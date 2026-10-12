
import re
from collections import defaultdict

import faiss
import numpy as np
import ollama
import pymupdf
from sentence_transformers import SentenceTransformer


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
LLM_MODEL = "llama3.2:latest"

# Load the embedding model once.
embedding_model = SentenceTransformer(EMBEDDING_MODEL)


# --------------------------------------------------
# PDF TEXT EXTRACTION
# --------------------------------------------------

def extract_pdf_text(pdf_files):
    """Extract readable text from uploaded PDF files."""

    documents = []

    for pdf_file in pdf_files:
        pdf_bytes = pdf_file.getvalue()

        with pymupdf.open(
            stream=pdf_bytes,
            filetype="pdf"
        ) as pdf:

            for page_number, page in enumerate(pdf, start=1):
                text = page.get_text("text").strip()

                if text:
                    documents.append({
                        "text": text,
                        "source": pdf_file.name,
                        "page": page_number
                    })

    if not documents:
        raise ValueError(
            "No readable text found. The PDFs may be scanned "
            "documents or contain no extractable text."
        )

    return documents


# --------------------------------------------------
# REFERENCE EXTRACTION
# --------------------------------------------------

def extract_references(documents):
    """Extract numbered entries from identified reference sections."""

    reference_entries = []

    reference_heading = re.compile(
        r"^\s*(?:references|bibliography|works cited|"
        r"literature\s+cited)\s*:?\s*$",
        re.IGNORECASE | re.MULTILINE
    )

    end_heading = re.compile(
        r"^\s*(?:appendix|acknowledgements?|author contributions|"
        r"conflict of interest|funding|supplementary materials?)"
        r"\s*:?\s*$",
        re.IGNORECASE
    )

    numbered_reference = re.compile(
        r"^\s*(?:\[(\d{1,4})\]|(\d{1,4})[.)])\s+(.+)$"
    )

    documents_by_source = defaultdict(list)

    for document in documents:
        documents_by_source[document["source"]].append(document)

    for source, source_documents in documents_by_source.items():
        source_documents.sort(key=lambda doc: doc["page"])

        in_reference_section = False
        current_reference = None

        def save_current_reference():
            if (
                current_reference
                and len(current_reference["text"]) >= 25
            ):
                reference_entries.append(current_reference.copy())

        for document in source_documents:
            page_text = document["text"]

            if reference_heading.search(page_text):
                in_reference_section = True
                save_current_reference()
                current_reference = None

            if not in_reference_section:
                continue

            for line in page_text.splitlines():
                line = line.strip()

                if not line:
                    continue

                if reference_heading.fullmatch(line):
                    continue

                if end_heading.fullmatch(line):
                    save_current_reference()
                    current_reference = None
                    in_reference_section = False
                    break

                match = numbered_reference.match(line)

                if match:
                    save_current_reference()

                    number = match.group(1) or match.group(2)

                    current_reference = {
                        "number": number,
                        "text": match.group(3).strip(),
                        "source": source,
                        "page": document["page"],
                        "reference_section_detected": True
                    }

                elif current_reference:
                    current_reference["text"] += " " + line

        save_current_reference()

    return reference_entries


# --------------------------------------------------
# DOCUMENT CHUNKING
# --------------------------------------------------

def chunk_documents(documents, chunk_size=700, overlap=100):
    """Split page text into overlapping chunks."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be non-negative and smaller than chunk_size."
        )

    chunks = []

    for document in documents:
        text = document["text"]
        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "source": document["source"],
                    "page": document["page"]
                })

            if end == len(text):
                break

            start = end - overlap

    return chunks


# --------------------------------------------------
# FAISS INDEX
# --------------------------------------------------

def build_faiss_index(chunks):
    """Create normalized embeddings and a FAISS index."""

    if not chunks:
        raise ValueError("Cannot build an index without document chunks.")

    texts = [chunk["text"] for chunk in chunks]

    embeddings = embedding_model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    embeddings = np.asarray(embeddings, dtype="float32")

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    return index, embeddings


# --------------------------------------------------
# EVIDENCE RETRIEVAL
# --------------------------------------------------

def retrieve_evidence(question, chunks, index, top_k=5):
    """Retrieve the most relevant chunks for a research question."""

    if not chunks or index.ntotal == 0:
        return []

    if top_k <= 0:
        return []

    question_embedding = embedding_model.encode(
        [question],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    question_embedding = np.asarray(
        question_embedding,
        dtype="float32"
    )

    k = min(top_k, len(chunks), index.ntotal)

    scores, indices = index.search(question_embedding, k)

    evidence = []

    for score, idx in zip(scores[0], indices[0]):
        if 0 <= idx < len(chunks):
            evidence.append({
                **chunks[int(idx)],
                "similarity": float(score)
            })

    return evidence


# --------------------------------------------------
# CITATION FORMAT
# --------------------------------------------------

CITATION_PATTERN = re.compile(
    r"\[\s*Source:\s*([^,\]]+?)\s*,\s*"
    r"PDF\s+page:\s*(\d+)(?:\s*[-–]\s*(\d+))?\s*\]",
    re.IGNORECASE
)


def _append_evidence_citations(answer, evidence):
    """
    Add an explicit evidence list only if the generated answer
    contains no citations in SciGenX's expected format.

    These citations identify retrieved passages. They do not
    independently establish claim-level scientific support.
    """

    if CITATION_PATTERN.search(answer):
        return answer

    unique_evidence = []
    seen = set()

    for item in evidence:
        source = str(item["source"]).strip()
        page = str(item["page"]).strip()

        key = (source.lower(), page)

        if key not in seen:
            seen.add(key)
            unique_evidence.append((source, page))

    if not unique_evidence:
        return answer

    citation_lines = [
        "",
        "",
        "### Retrieved evidence citations",
        "",
        (
            "The answer did not contain inline citations in the "
            "required format. The following citations identify "
            "passages retrieved for this answer. Check each passage "
            "before attributing a specific claim to it."
        ),
        ""
    ]

    for source, page in unique_evidence:
        citation_lines.append(
            f"- [Source: {source}, PDF page: {page}]"
        )

    return answer.rstrip() + "\n" + "\n".join(citation_lines)


# --------------------------------------------------
# RESEARCH ANSWER GENERATION
# --------------------------------------------------

def generate_research_answer(question, evidence):
    """Generate an evidence-grounded research answer using Ollama."""

    if not evidence:
        return (
            "Insufficient evidence: no relevant text was retrieved "
            "from the uploaded research papers."
        )

    context_parts = []

    for i, item in enumerate(evidence, start=1):
        context_parts.append(
            f"[Evidence E{i}]\n"
            f"Source file: {item['source']}\n"
            f"PDF page: {item['page']}\n"
            f"Retrieved text:\n{item['text']}"
        )

    context = "\n\n".join(context_parts)

    prompt = f"""
You are SciGenX, a scientific research assistant.

Answer the research question using ONLY the supplied evidence.

RESEARCH QUESTION:
{question}

RETRIEVED EVIDENCE:
{context}

STRICT RULES:

1. Evidence discipline:
   - Do not invent facts, statistics, experiments, authors,
     publication years, or references.
   - If evidence is insufficient, state that clearly.
   - Distinguish evidence-supported findings from interpretation.

2. Citations:
   - Cite every substantive factual claim using the exact
     filename and page of its supporting retrieved evidence.
   - Use exactly this format:
     [Source: paper.pdf, PDF page: 12]
   - Copy filenames and page numbers exactly from the evidence.
   - Never invent filenames, page numbers, or references.
   - Use multiple citations when multiple passages support a claim.
   - Do not cite a source that does not support the claim.

3. Research gaps:
   - Identify only limitations supported by the evidence.
   - Label reasonable deductions as "Potential research gap".
   - Do not claim that a topic has never been researched based
     only on a few retrieved passages.
   - State when a broader literature review is needed.

4. Answer structure:
   A. Summary
   B. Main methods and findings
   C. Limitations supported by evidence
   D. Potential research gaps
   E. Evidence limitations and conclusion

5. Keep the answer clear, scientific, and specific.
   Do not invent information to fill a section.

Return the answer in Markdown.
"""

    response = ollama.chat(
        model=LLM_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": 0.1
        }
    )

    answer = response["message"]["content"].strip()

    # Fallback: make retrieved source/page references visible
    # when the model omits the expected citation format.
    answer = _append_evidence_citations(answer, evidence)

    return answer


# --------------------------------------------------
# CITATION VERIFICATION
# --------------------------------------------------

def verify_answer_citations(answer, evidence):
    """
    Check whether cited filenames and PDF pages occur in retrieved
    evidence.

    This checks traceability, not whether a passage proves a claim.
    """

    if not evidence:
        return {
            "status": "NO_EVIDENCE",
            "total_citations": 0,
            "matched_citations": [],
            "unmatched_citations": [],
            "message": (
                "No retrieved evidence is available for verification."
            )
        }

    valid_sources = set()

    for item in evidence:
        source = str(item["source"]).strip().casefold()
        page = str(item["page"]).strip()
        valid_sources.add((source, page))

    matches = list(CITATION_PATTERN.finditer(answer or ""))

    matched_citations = []
    unmatched_citations = []

    for match in matches:
        source = match.group(1).strip()
        start_page = int(match.group(2))
        end_page = int(match.group(3) or start_page)

        # Reject reversed or excessively large page ranges.
        if end_page < start_page or end_page - start_page > 100:
            unmatched_citations.append({
                "source": source,
                "pages": list(range(start_page, end_page + 1))
                if end_page >= start_page
                and end_page - start_page <= 100
                else [start_page, end_page]
            })
            continue

        pages = list(range(start_page, end_page + 1))

        citation = {
            "source": source,
            "pages": pages
        }

        all_pages_found = all(
            (source.casefold(), str(page)) in valid_sources
            for page in pages
        )

        if all_pages_found:
            matched_citations.append(citation)
        else:
            unmatched_citations.append(citation)

    if not matches:
        status = "NO_RECOGNIZED_CITATIONS"
        message = (
            "No citations in the expected format were found. "
            "Check the answer's citation format."
        )

    elif unmatched_citations:
        status = "REVIEW_REQUIRED"
        message = (
            "Some citations do not match the retrieved source/page "
            "combinations. Review the unmatched citations."
        )

    else:
        status = "TRACEABLE"
        message = (
            "All recognized citations match retrieved source/page "
            "combinations. This does not independently verify that "
            "each passage supports its associated scientific claim."
        )

    return {
        "status": status,
        "total_citations": len(matches),
        "matched_citations": matched_citations,
        "unmatched_citations": unmatched_citations,
        "message": message
    }