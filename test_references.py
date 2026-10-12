
from pathlib import Path

from src.scigenx_core import extract_pdf_text, extract_references


# Folder containing research PDFs
PDF_FOLDER = Path("papers")


class LocalPDF:
    """Make local PDF files compatible with extract_pdf_text()."""

    def __init__(self, path):
        self.name = path.name
        self.path = path

    def getvalue(self):
        return self.path.read_bytes()


def main():
    # Find PDF files
    pdf_paths = sorted(PDF_FOLDER.glob("*.pdf"))

    if not pdf_paths:
        print(f"No PDF files found in: {PDF_FOLDER.resolve()}")
        print("Please check that your PDFs are inside the papers folder.")
        return

    print("=" * 70)
    print("SciGenX - Reference Extraction and Quality Check")
    print("=" * 70)

    # Load PDF documents
    uploaded_pdfs = [LocalPDF(path) for path in pdf_paths]
    documents = extract_pdf_text(uploaded_pdfs)

    # Extract reference entries
    references = extract_references(documents)

    print(f"\nPDF files found: {len(pdf_paths)}")
    print(f"Pages with text: {len(documents)}")
    print(f"Extracted reference entries: {len(references)}")

    # Display references grouped by PDF
    print("\n" + "=" * 70)
    print("EXTRACTED REFERENCES")
    print("=" * 70)

    for source in sorted({ref["source"] for ref in references}):
        source_refs = [
            ref for ref in references
            if ref["source"] == source
        ]

        print(f"\nPDF: {source}")
        print("-" * 70)

        for ref in source_refs:
            print(
                f"[{ref['number']}] {ref['text']}\n"
                f"    Page: {ref['page']}"
            )

    # Basic quality checks
    print("\n" + "=" * 70)
    print("REFERENCE QUALITY CHECK")
    print("=" * 70)

    short_entries = []
    number_only_entries = []
    possible_duplicates = []
    seen_entries = set()

    for ref in references:
        entry_text = ref["text"].strip()

        # Find unusually short entries
        if len(entry_text) < 40:
            short_entries.append(ref)

        # Find entries containing only numbers
        if entry_text.isdigit():
            number_only_entries.append(ref)

        # Identify repeated text within the extracted references
        normalized_text = " ".join(entry_text.lower().split())

        if normalized_text in seen_entries:
            possible_duplicates.append(ref)
        else:
            seen_entries.add(normalized_text)

    print(f"\nShort entries to review: {len(short_entries)}")
    for ref in short_entries:
        print(
            f"  CHECK [{ref['number']}] {ref['text']}"
            f" | {ref['source']} | Page {ref['page']}"
        )

    print(f"\nNumber-only entries to review: {len(number_only_entries)}")
    for ref in number_only_entries:
        print(
            f"  CHECK [{ref['number']}] {ref['text']}"
            f" | {ref['source']} | Page {ref['page']}"
        )

    print(f"\nPossible duplicate entries: {len(possible_duplicates)}")
    for ref in possible_duplicates:
        print(
            f"  REVIEW [{ref['number']}] {ref['text']}"
            f" | {ref['source']} | Page {ref['page']}"
        )

    # Show a quick preview
    print("\n" + "=" * 70)
    print("FIRST 10 REFERENCES - PREVIEW")
    print("=" * 70)

    for ref in references[:10]:
        print(
            f"[{ref['number']}] {ref['text']}\n"
            f"    Source: {ref['source']} | Page: {ref['page']}\n"
        )

    # Save extracted entries to a text report
    output_path = Path("reference_extraction_report.txt")

    with output_path.open("w", encoding="utf-8") as file:
        file.write("SciGenX Reference Extraction Report\n")
        file.write("=" * 70 + "\n\n")
        file.write(f"PDF files: {len(pdf_paths)}\n")
        file.write(f"Pages with text: {len(documents)}\n")
        file.write(f"Extracted reference entries: {len(references)}\n\n")

        for ref in references:
            file.write(
                f"[{ref['number']}] {ref['text']}\n"
                f"Source: {ref['source']}\n"
                f"Page: {ref['page']}\n\n"
            )

        file.write("\nQUALITY CHECK SUMMARY\n")
        file.write(f"Short entries: {len(short_entries)}\n")
        file.write(f"Number-only entries: {len(number_only_entries)}\n")
        file.write(f"Possible duplicates: {len(possible_duplicates)}\n")

    print("\n" + "=" * 70)
    print(f"Report saved to: {output_path.resolve()}")
    print("Reference extraction test completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()