
from src.scigenx_core import verify_answer_citations


# Sample evidence matching the format returned by SciGenX
evidence = [
    {
        "source": "plant_desease.pdf",
        "page": 35,
        "text": (
            "Deep learning and convolutional neural networks "
            "have been explored for plant disease recognition."
        ),
    },
    {
        "source": "compherencive_review.pdf",
        "page": 17,
        "text": (
            "The reviewed studies discuss deep learning approaches "
            "for plant disease classification."
        ),
    },
]

# Test answer containing citations in the expected format
answer = """
CNN-based approaches have been explored for plant disease recognition.
[Source: plant_desease.pdf, PDF page: 35]

Several studies discuss deep learning classification methods.
[Source: compherencive_review.pdf, PDF page: 17]

This claim uses a page that is not in the retrieved evidence.
[Source: plant_desease.pdf, PDF page: 99]
"""

result = verify_answer_citations(answer, evidence)

print("Verification status:", result["status"])
print("Recognized citations:", result["total_citations"])
print("\nMatched citations:")

for citation in result["matched_citations"]:
    print(citation)

print("\nCitations requiring review:")

for citation in result["unmatched_citations"]:
    print(citation)

print("\nMessage:", result["message"])