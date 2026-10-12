
from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback

from src.scigenx_core import (
    analyze_research,
    verify_answer_citations,
)

app = Flask(__name__)
CORS(app)


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "success",
        "message": "SciGenX API is running"
    }), 200


@app.route("/api/search", methods=["GET"])
def search_papers():
    """
    Search research papers using the existing search module.
    """
    query = request.args.get("q", "").strip()

    if not query:
        return jsonify({
            "status": "error",
            "message": "Please enter a search query."
        }), 400

    try:
        from src.scigenx_core import search_research_papers

        papers = search_research_papers(query)

        return jsonify({
            "status": "success",
            "query": query,
            "papers": papers
        }), 200

    except ImportError:
        return jsonify({
            "status": "error",
            "message": (
                "Paper search is not connected to this API yet. "
                "Please preserve your existing working search function."
            )
        }), 501

    except Exception as exc:
        app.logger.exception("Paper search failed")
        return jsonify({
            "status": "error",
            "message": str(exc)
        }), 500


@app.route("/api/analyze", methods=["POST"])
def analyze_papers():
    """
    Receive uploaded research PDFs and a research question,
    analyze them using the existing SciGenX core, and return
    evidence and citation-verification results to React.
    """
    question = request.form.get("question", "").strip()
    papers = request.files.getlist("papers")

    if not question:
        return jsonify({
            "status": "error",
            "message": "Please enter a research question."
        }), 400

    if not papers or not any(p.filename for p in papers):
        return jsonify({
            "status": "error",
            "message": "Please upload at least one research PDF."
        }), 400

    valid_papers = [
        paper for paper in papers
        if paper.filename and paper.filename.lower().endswith(".pdf")
    ]

    if not valid_papers:
        return jsonify({
            "status": "error",
            "message": "Please upload valid PDF files."
        }), 400

    try:
        # Preserve the existing core analysis implementation.
        result = analyze_research(valid_papers, question)

        if not isinstance(result, dict):
            return jsonify({
                "status": "error",
                "message": "The analysis core returned an unexpected result."
            }), 500

        answer = result.get("answer", "")
        sources = result.get("sources", [])

        # Verify citations against the retrieved evidence.
        citation_verification = verify_answer_citations(
            answer,
            sources
        )

        response = {
            "status": "success",
            "question": question,
            "answer": answer,
            "sources": sources,
            "total_pages_with_text": result.get(
                "total_pages_with_text", 0
            ),
            "total_chunks": result.get("total_chunks", 0),
            "citation_verification": citation_verification
        }

        return jsonify(response), 200

    except Exception as exc:
        app.logger.exception("Research analysis failed")
        return jsonify({
            "status": "error",
            "message": str(exc)
        }), 500


@app.errorhandler(404)
def not_found(_error):
    return jsonify({
        "status": "error",
        "message": "API endpoint not found."
    }), 404


@app.errorhandler(405)
def method_not_allowed(_error):
    return jsonify({
        "status": "error",
        "message": "HTTP method not allowed for this endpoint."
    }), 405


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
