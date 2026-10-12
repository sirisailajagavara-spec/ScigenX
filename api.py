
import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

from src.scigenx_core import (
    analyze_research,
    verify_answer_citations,
)

app = Flask(__name__)
CORS(app)

app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

CROSSREF_API = "https://api.crossref.org/works"


class UploadedPDF:
    """Adapt Flask uploads to the interface expected by the existing core."""

    def __init__(self, storage):
        self.name = storage.filename
        self._content = storage.read()

    def getvalue(self):
        return self._content


@app.get("/api/health")
def health():
    return jsonify({
        "status": "success",
        "message": "SciGenX API is running"
    })


@app.get("/api/search")
def search_papers():
    """Search academic publication metadata using Crossref."""

    query = request.args.get("q", "").strip()

    if len(query) < 2:
        return jsonify({
            "status": "error",
            "message": "Enter a research topic with at least 2 characters."
        }), 400

    try:
        response = requests.get(
            CROSSREF_API,
            params={
                "query": query,
                "rows": 10,
                "select": (
                    "title,author,published,created,DOI,"
                    "URL,publisher,container-title,type"
                ),
            },
            headers={
                "User-Agent": "SciGenX/1.0 (academic research project)"
            },
            timeout=20,
        )
        response.raise_for_status()

        items = response.json().get("message", {}).get("items", [])
        papers = []

        for item in items:
            titles = item.get("title") or []
            title = titles[0].strip() if titles else "Untitled paper"

            authors = []
            for author in item.get("author", [])[:5]:
                given = author.get("given", "")
                family = author.get("family", "")
                name = f"{given} {family}".strip()
                if name:
                    authors.append(name)

            published = item.get("published", {}).get("date-parts", [])
            year = (
                published[0][0]
                if published and published[0]
                else None
            )

            doi = item.get("DOI")
            doi_url = f"https://doi.org/{doi}" if doi else item.get("URL")

            journals = item.get("container-title") or []

            papers.append({
                "title": title,
                "authors": authors,
                "year": year,
                "doi": doi,
                "url": doi_url,
                "publisher": item.get("publisher", ""),
                "journal": journals[0] if journals else "",
                "type": item.get("type", ""),
            })

        return jsonify({
            "status": "success",
            "query": query,
            "count": len(papers),
            "papers": papers,
        })

    except requests.RequestException as exc:
        app.logger.warning("Crossref search failed: %s", exc)
        return jsonify({
            "status": "error",
            "message": (
                "Could not reach the academic search service. "
                "Check your internet connection and try again."
            )
        }), 502

    except (ValueError, TypeError) as exc:
        app.logger.exception("Invalid Crossref response")
        return jsonify({
            "status": "error",
            "message": "The search service returned an invalid response."
        }), 502


@app.post("/api/analyze")
def analyze_papers():
    """Analyze uploaded PDFs with the existing SciGenX core."""

    question = request.form.get("question", "").strip()
    uploaded_files = request.files.getlist("papers")

    if not question:
        return jsonify({
            "status": "error",
            "message": "Enter a research question."
        }), 400

    pdf_files = [
        file for file in uploaded_files
        if file and file.filename
    ]

    if not pdf_files:
        return jsonify({
            "status": "error",
            "message": "Upload at least one PDF research paper."
        }), 400

    for file in pdf_files:
        if not file.filename.lower().endswith(".pdf"):
            return jsonify({
                "status": "error",
                "message": "Only PDF files are supported."
            }), 400

    try:
        adapted_files = [UploadedPDF(file) for file in pdf_files]

        result = analyze_research(adapted_files, question)

        answer = result.get("answer", "")
        sources = result.get("sources", [])

        verification = verify_answer_citations(answer, sources)

        return jsonify({
            "status": "success",
            "question": question,
            "answer": answer,
            "sources": sources,
            "total_pages_with_text": result.get(
                "total_pages_with_text", 0
            ),
            "total_chunks": result.get("total_chunks", 0),
            "citation_verification": verification,
        })

    except Exception:
        app.logger.exception("Research analysis failed")
        return jsonify({
            "status": "error",
            "message": (
                "Research analysis failed. Check the API terminal "
                "for the detailed error."
            )
        }), 500


@app.errorhandler(413)
def request_too_large(_error):
    return jsonify({
        "status": "error",
        "message": "The uploaded files exceed the 50 MB limit."
    }), 413


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
