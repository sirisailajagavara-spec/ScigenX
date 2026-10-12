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
        re.IGNORECASE | re.MULTILINE
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
                reference_entries.append(
                    current_reference.copy()
                )

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
        raise ValueError(
            "chunk_size must be greater than zero."
        )

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be non-negative and smaller than "
            "chunk_size."
        )

    chunks = []

    for document in documents:
        text = document["text"]
        start = 0

        while start < len(text):
            end = min(
                start + chunk_size,
                len(text)
            )

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
        raise ValueError(
            "Cannot build an index without document chunks."
        )

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    embeddings = embedding_model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    embeddings = np.asarray(
        embeddings,
        dtype="float32"
    )

    index = faiss.IndexFlatIP(
        embeddings.shape[1]
    )

    index.add(embeddings)

    return index, embeddings


# --------------------------------------------------
# EVIDENCE RETRIEVAL
# --------------------------------------------------

def retrieve_evidence(
    question,
    chunks,
    index,
    top_k=5
):
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

    k = min(
        top_k,
        len(chunks),
        index.ntotal
    )

    scores, indices = index.search(
        question_embedding,
        k
    )

    evidence = []

    for score, idx in zip(
        scores[0],
        indices[0]
    ):
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
    r"PDF\s+page:\s*(\d+)"
    r"(?:\s*[-–]\s*(\d+))?\s*\]",
    re.IGNORECASE
)


# --------------------------------------------------
# FALLBACK CITATION LIST
# --------------------------------------------------

def _append_evidence_citations(
    answer,
    evidence
):
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
        source = str(
            item["source"]
        ).strip()

        page = str(
            item["page"]
        ).strip()

        key = (
            source.lower(),
            page
        )

        if key not in seen:
            seen.add(key)
            unique_evidence.append(
                (source, page)
            )

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
            "passages retrieved for this answer. Check each "
            "passage before attributing a specific claim to it."
        ),
        ""
    ]

    for source, page in unique_evidence:
        citation_lines.append(
            f"- [Source: {source}, PDF page: {page}]"
        )

    return (
        answer.rstrip()
        + "\n"
        + "\n".join(citation_lines)
    )


# --------------------------------------------------
# RESEARCH ANSWER GENERATION
# --------------------------------------------------

def generate_research_answer(
    question,
    evidence
):
    """
    Generate an evidence-grounded research answer using Ollama.

    The answer:
    - Uses only retrieved evidence
    - Produces inline source/page citations
    - Supports model comparison tables
    - Avoids inventing numerical values
    - Clearly reports missing evidence
    """

    if not evidence:
        return (
            "Insufficient evidence: no relevant text was "
            "retrieved from the uploaded research papers."
        )

    # --------------------------------------------------
    # Build evidence context
    # --------------------------------------------------

    context_parts = []

    for i, item in enumerate(
        evidence,
        start=1
    ):
        context_parts.append(
            f"[Evidence E{i}]\n"
            f"Source file: {item['source']}\n"
            f"PDF page: {item['page']}\n"
            f"Similarity score: "
            f"{item.get('similarity', 'N/A')}\n"
            f"Retrieved text:\n"
            f"{item['text']}"
        )

    context = "\n\n".join(
        context_parts
    )

    # --------------------------------------------------
    # Scientific research prompt
    # --------------------------------------------------

    prompt = f"""
You are SciGenX, an evidence-grounded scientific research assistant.

Your task is to answer the research question using ONLY the supplied
retrieved evidence from the uploaded research papers.

RESEARCH QUESTION:
{question}

RETRIEVED EVIDENCE:
{context}


==================================================
STRICT SCIENTIFIC RULES
==================================================

1. EVIDENCE-ONLY ANSWERING

- Use only information explicitly present in the retrieved evidence.
- Never invent facts, numerical values, accuracy percentages,
  computational times, FLOPs, model sizes, datasets, authors,
  publication years, or references.
- Do not use outside knowledge to fill missing information.
- If the evidence does not contain information required to answer
  part of the question, explicitly write:

  "Not reported in the retrieved evidence."

- Clearly distinguish evidence-supported findings from interpretation.


==================================================
2. INLINE CITATIONS ARE MANDATORY
==================================================

Every substantive factual claim MUST have an inline citation.

Place the citation immediately after the claim it supports.

Use EXACTLY this citation format:

[Source: filename.pdf, PDF page: 12]

Examples:

CNN-based approaches were used for plant disease classification.
[Source: compherencive_review.pdf, PDF page: 2]

Vision Transformers were identified as an underexplored area in
agricultural pathology.
[Source: compherencive_review.pdf, PDF page: 17]

IMPORTANT:

- Copy the filename exactly from the evidence.
- Copy the PDF page number exactly from the evidence.
- Never invent a filename.
- Never invent a page number.
- Do not cite a source merely because it is related to the topic.
- The cited evidence must actually support the claim.
- If multiple passages support a claim, multiple citations may be used.


==================================================
3. MODEL COMPARISON
==================================================

If the research question asks to compare different models,
methods, or approaches, provide a concise comparison table.

Use this structure when appropriate:

| Model | Reported Performance | Computational Efficiency | Major Limitation |
|---|---|---|---|

Rules:

- Include only models supported by the retrieved evidence.
- Do not invent performance values.
- Do not estimate accuracy.
- Do not estimate computational cost.
- Do not assume that one model is computationally better than another.
- If accuracy is not reported, write:

  "Not reported in the retrieved evidence."

- If computational efficiency is not reported, write:

  "Not reported in the retrieved evidence."

- Add citations to factual table entries whenever possible.


==================================================
4. ACCURACY AND COMPUTATIONAL EFFICIENCY
==================================================

If the research question asks about:

- accuracy
- precision
- recall
- F1-score
- inference time
- computational cost
- FLOPs
- memory
- model size
- training time
- computational efficiency

then follow these rules:

- Report numerical values ONLY when explicitly present in the evidence.
- Never invent numerical values.
- Never estimate missing values.
- Never infer computational efficiency without evidence.
- Never claim a model is faster, slower, cheaper, or more expensive
  unless the retrieved evidence explicitly supports that claim.

If the retrieved evidence does not contain enough information for a
numerical comparison, clearly state:

"The retrieved evidence does not provide enough information for a
direct numerical comparison."

Then use:

"Not reported in the retrieved evidence."

where appropriate.


==================================================
5. LIMITATIONS
==================================================

Identify only limitations directly supported by the retrieved evidence.

For every limitation:

- Explain it briefly.
- Add the supporting source/page citation.

Do NOT present general AI/ML knowledge as if it came from the papers.

For example, if the evidence states that poor image quality can reduce
disease detection performance, report that limitation and cite the
corresponding evidence.

Do not add unrelated limitations.


==================================================
6. RESEARCH GAPS
==================================================

Identify potential research gaps only from the retrieved evidence.

Use this exact label:

"Potential research gap:"

Do NOT claim that a topic has "never been researched" unless the
retrieved evidence explicitly establishes this.

If the evidence suggests that a topic is underexplored, write carefully.

For example:

"Potential research gap: The retrieved evidence identifies limited
investigation of Vision Transformers in agricultural pathology.
[Source: compherencive_review.pdf, PDF page: 17]

A broader literature review is required to determine whether this
represents a genuinely underexplored research area."


==================================================
7. EVIDENCE LIMITATIONS
==================================================

At the end of the answer, explain what cannot be established from the
retrieved evidence.

Possible evidence limitations include:

- insufficient numerical comparisons
- insufficient computational-efficiency information
- limited number of retrieved passages
- lack of experimental details
- incomplete dataset information
- incomplete model implementation details

Only mention limitations that are actually relevant to the retrieved
evidence.

Do not invent evidence limitations.


==================================================
ANSWER STRUCTURE
==================================================

A. Summary

Provide a concise evidence-grounded summary of the answer.

Every substantive factual statement must have an inline citation.


B. Main Methods and Findings

Explain the models, methods, and findings supported by the evidence.

If the research question asks for model comparison, include a comparison
table.

Every substantive factual statement must have an inline citation.


C. Limitations Supported by Evidence

List the limitations that are directly supported by the retrieved
evidence.

Each limitation should have a citation.


D. Potential Research Gaps

List potential research gaps supported by the evidence.

Clearly distinguish potential gaps from confirmed findings.

Use:

"Potential research gap:"


E. Evidence Limitations and Conclusion

Explain what cannot be concluded from the retrieved evidence.

Pay special attention to missing numerical accuracy or computational
efficiency information.

Then provide a concise scientific conclusion.


==================================================
FINAL QUALITY CHECK
==================================================

Before returning the answer, verify all of the following:

1. Every substantive factual claim has an inline citation.

2. Every citation uses the exact source filename and PDF page from the
   retrieved evidence.

3. No unsupported numerical value has been invented.

4. No unsupported model comparison has been invented.

5. Missing information is explicitly labelled:

   "Not reported in the retrieved evidence."

6. Potential research gaps are clearly labelled.

7. The answer does not claim that a topic has never been researched
   unless the evidence explicitly proves it.

8. The answer clearly distinguishes:
   - evidence-supported findings
   - interpretation
   - potential research gaps

9. The answer is scientifically cautious.

10. The answer uses ONLY the retrieved evidence.

Return ONLY the final research answer in Markdown.
"""

    # --------------------------------------------------
    # Call Ollama
    # --------------------------------------------------

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

    answer = response[
        "message"
    ][
        "content"
    ].strip()

    # --------------------------------------------------
    # Fallback evidence citations
    # --------------------------------------------------

    answer = _append_evidence_citations(
        answer,
        evidence
    )

    return answer


# --------------------------------------------------
# COMPLETE RESEARCH ANALYSIS PIPELINE
# --------------------------------------------------

def analyze_research(
    pdf_files,
    question
):
    """
    Run the complete SciGenX research analysis pipeline.

    Steps:
        1. Extract PDF text
        2. Create document chunks
        3. Build FAISS vector index
        4. Retrieve relevant evidence
        5. Generate research answer

    Returns:
        Dictionary containing:
        - answer
        - sources
        - total_pages_with_text
        - total_chunks
    """

    # --------------------------------------------------
    # Validate input
    # --------------------------------------------------

    if not pdf_files:
        raise ValueError(
            "Please upload at least one research paper."
        )

    if (
        not isinstance(question, str)
        or not question.strip()
    ):
        raise ValueError(
            "Please enter a research question."
        )

    # --------------------------------------------------
    # Step 1: Extract text from PDFs
    # --------------------------------------------------

    documents = extract_pdf_text(
        pdf_files
    )

    # --------------------------------------------------
    # Step 2: Create overlapping chunks
    # --------------------------------------------------

    chunks = chunk_documents(
        documents,
        chunk_size=700,
        overlap=100
    )

    if not chunks:
        raise ValueError(
            "No usable text chunks were created."
        )

    # --------------------------------------------------
    # Step 3: Build FAISS vector index
    # --------------------------------------------------

    index, _ = build_faiss_index(
        chunks
    )

    # --------------------------------------------------
    # Step 4: Retrieve relevant evidence
    # --------------------------------------------------

    sources = retrieve_evidence(
        question=question.strip(),
        chunks=chunks,
        index=index,
        top_k=5
    )

    # --------------------------------------------------
    # Step 5: Generate research answer
    # --------------------------------------------------

    answer = generate_research_answer(
        question=question.strip(),
        evidence=sources
    )

    # --------------------------------------------------
    # Step 6: Return result
    # --------------------------------------------------

    return {
        "answer": answer,
        "sources": sources,
        "total_pages_with_text": len(documents),
        "total_chunks": len(chunks)
    }


# --------------------------------------------------
# CITATION VERIFICATION
# --------------------------------------------------

def verify_answer_citations(
    answer,
    evidence
):
    """
    Check whether cited filenames and PDF pages occur
    in retrieved evidence.

    This checks traceability, not whether a passage proves
    a scientific claim.
    """

    if not evidence:
        return {
            "status": "NO_EVIDENCE",
            "total_citations": 0,
            "matched_citations": [],
            "unmatched_citations": [],
            "message": (
                "No retrieved evidence is available "
                "for verification."
            )
        }

    # --------------------------------------------------
    # Build valid source/page combinations
    # --------------------------------------------------

    valid_sources = set()

    for item in evidence:
        source = str(
            item["source"]
        ).strip().casefold()

        page = str(
            item["page"]
        ).strip()

        valid_sources.add(
            (source, page)
        )

    # --------------------------------------------------
    # Find citations in generated answer
    # --------------------------------------------------

    matches = list(
        CITATION_PATTERN.finditer(
            answer or ""
        )
    )

    matched_citations = []
    unmatched_citations = []

    # --------------------------------------------------
    # Validate every citation
    # --------------------------------------------------

    for match in matches:

        source = match.group(
            1
        ).strip()

        start_page = int(
            match.group(2)
        )

        end_page = int(
            match.group(3)
            or start_page
        )

        # Reject reversed or excessively large ranges
        if (
            end_page < start_page
            or end_page - start_page > 100
        ):
            unmatched_citations.append({
                "source": source,
                "pages": (
                    list(
                        range(
                            start_page,
                            end_page + 1
                        )
                    )
                    if (
                        end_page >= start_page
                        and end_page - start_page <= 100
                    )
                    else [
                        start_page,
                        end_page
                    ]
                )
            })

            continue

        pages = list(
            range(
                start_page,
                end_page + 1
            )
        )

        citation = {
            "source": source,
            "pages": pages
        }

        all_pages_found = all(
            (
                source.casefold(),
                str(page)
            ) in valid_sources
            for page in pages
        )

        if all_pages_found:
            matched_citations.append(
                citation
            )
        else:
            unmatched_citations.append(
                citation
            )

    # --------------------------------------------------
    # Determine verification status
    # --------------------------------------------------

    if not matches:

        status = (
            "NO_RECOGNIZED_CITATIONS"
        )

        message = (
            "No citations in the expected format "
            "were found. Check the answer's citation "
            "format."
        )

    elif unmatched_citations:

        status = (
            "REVIEW_REQUIRED"
        )

        message = (
            "Some citations do not match the retrieved "
            "source/page combinations. Review the "
            "unmatched citations."
        )

    else:

        status = "TRACEABLE"

        message = (
            "All recognized citations match retrieved "
            "source/page combinations. This does not "
            "independently verify that each passage "
            "supports its associated scientific claim."
        )

    # --------------------------------------------------
    # Return verification result
    # --------------------------------------------------

    return {
        "status": status,
        "total_citations": len(matches),
        "matched_citations": matched_citations,
        "unmatched_citations": unmatched_citations,
        "message": message
    }