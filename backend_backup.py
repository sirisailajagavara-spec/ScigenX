
import io
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

from src.scigenx_core import (
    analyze_research,
    verify_answer_citations,
)

app = Flask(__name__)
CORS(app)

app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024


@app.get("/api/health")
def health():
    return jsonify({
        "status": "success",
        "message": "SciGenX API is running"
    })


@app.post("/api/analyze")
def analyze():
    if "papers" not in request.files:
        return jsonify({
            "status": "error",
            "message": "Please upload at least one PDF."
        }), 400

    question = request.form.get("question", "").strip()

    uploaded_files = [
        file
        for file in request.files.getlist("papers")
        if file and file.filename
    ]

    if not question:
        return jsonify({
            "status": "error",
            "message": "Please enter a research question."
        }), 400

    if not uploaded_files:
        return jsonify({
            "status": "error",
            "message": "Please upload at least one PDF."
        }), 400

    if any(
        Path(file.filename).suffix.lower() != ".pdf"
        for file in uploaded_files
    ):
        return jsonify({
            "status": "error",
            "message": "Only PDF files are supported."
        }), 400

    try:
        # Convert uploaded PDFs into in-memory file objects.
        pdf_files = []

        for uploaded_file in uploaded_files:
            safe_name = secure_filename(uploaded_file.filename)

            pdf_buffer = io.BytesIO(uploaded_file.read())
            pdf_buffer.name = safe_name

            pdf_files.append(pdf_buffer)

        # Run the existing SciGenX research engine.
        result = analyze_research(
            pdf_files=pdf_files,
            question=question
        )

        answer = result["answer"]
        sources = result["sources"]

        # Verify citations without failing the entire analysis.
        try:
            citations = verify_answer_citations(
                answer=answer,
                evidence=sources
            )
        except Exception:
            app.logger.exception("Citation verification failed")
            citations = {
                "status": "unavailable",
                "message": "Citation verification could not be completed."
            }

        return jsonify({
            "status": "success",
            "question": question,
            "answer": answer,
            "sources": sources,
            "total_pages_with_text": result["total_pages_with_text"],
            "total_chunks": result["total_chunks"],
            "citation_verification": citations
        })

    except ValueError as error:
        return jsonify({
            "status": "error",
            "message": str(error)
        }), 400

    except Exception:
        app.logger.exception("SciGenX analysis failed")
        return jsonify({
            "status": "error",
            "message": "Analysis failed. Check the backend terminal."
        }), 500


@app.errorhandler(413)
def file_too_large(_error):
    return jsonify({
        "status": "error",
        "message": "The total upload size must not exceed 50 MB."
    }), 413


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
