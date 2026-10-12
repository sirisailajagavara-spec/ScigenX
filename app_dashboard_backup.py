
import streamlit as st
from pathlib import Path
from datetime import datetime

from src.scigenx_core import (
    analyze_research,
    verify_answer_citations,
)

st.set_page_config(
    page_title="SciGenX | Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Professional white theme ----------
st.markdown(
    """
    <style>
    .stApp {
        background: #f7f9fc;
        color: #172033;
    }
    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e5eaf2;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1250px;
    }
    .hero {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        padding: 28px 30px;
        margin-bottom: 24px;
    }
    .hero h1 {
        color: #183b70;
        font-size: 2.25rem;
        margin-bottom: 8px;
    }
    .hero p {
        color: #53647c;
        font-size: 1rem;
        margin-bottom: 0;
    }
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
    }
    div.stButton > button {
        background: #2457a7;
        color: white;
        border: 0;
        border-radius: 9px;
        min-height: 44px;
        font-weight: 600;
    }
    div.stButton > button:hover {
        background: #183f80;
        color: white;
        border: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Header ----------
st.markdown(
    """
    <div class="hero">
        <h1>🔬 SciGenX</h1>
        <p>
            AI-powered scientific research assistant for literature analysis,
            evidence retrieval, citation verification, and research discovery.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- Sidebar ----------
with st.sidebar:
    st.title("📚 Research Workspace")
    st.caption("Build your analysis from research papers.")

    uploaded_files = st.file_uploader(
        "Upload research papers (PDF)",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload one or more research papers.",
    )

    if uploaded_files:
        st.success(f"{len(uploaded_files)} PDF file(s) selected.")
        with st.expander("View uploaded files"):
            for file in uploaded_files:
                st.write(f"📄 {file.name}")

    st.divider()
    st.caption("SciGenX · Academic Research Assistant")

# ---------- Research input ----------
st.subheader("Research Question")
st.write(
    "Ask a focused question about the uploaded papers. "
    "SciGenX will retrieve relevant evidence for analysis."
)

question = st.text_area(
    "Enter your research question",
    placeholder=(
        "Example: What are the limitations of deep learning "
        "approaches for plant disease detection?"
    ),
    height=120,
)

analyze_clicked = st.button(
    "🔍 Analyze Research",
    use_container_width=True,
)

# ---------- Analysis ----------
if analyze_clicked:
    if not uploaded_files:
        st.warning("Please upload at least one research paper.")
    elif not question.strip():
        st.warning("Please enter a research question.")
    else:
        try:
            with st.spinner(
                "Reading papers and retrieving relevant evidence..."
            ):
                result = analyze_research(
                    pdf_files=uploaded_files,
                    question=question.strip(),
                )

            if not isinstance(result, dict):
                st.error(
                    "The analysis function did not return the expected "
                    "dictionary result. Check src/scigenx_core.py."
                )
            else:
                answer = result.get("answer", "No answer was returned.")
                sources = result.get("sources", [])
                total_pages = result.get("total_pages_with_text", 0)
                total_chunks = result.get("total_chunks", 0)

                st.divider()
                st.subheader("Research Analysis")

                col1, col2, col3 = st.columns(3)
                col1.metric("PDFs uploaded", len(uploaded_files))
                col2.metric("Pages with text", total_pages)
                col3.metric("Retrieved evidence", len(sources))

                st.markdown("#### Research Answer")
                st.markdown(answer)

                # Citation verification
                st.divider()
                st.subheader("Citation Verification")

                verification = verify_answer_citations(
                    answer=answer,
                    evidence=sources,
                )

                status = verification.get("status", "UNKNOWN")
                message = verification.get("message", status)

                if status == "TRACEABLE":
                    st.success(message)
                elif status == "REVIEW_REQUIRED":
                    st.warning(message)
                elif status == "NO_RECOGNIZED_CITATIONS":
                    st.info(message)
                else:
                    st.info(message)

                st.metric(
                    "Recognized citations",
                    verification.get("total_citations", 0),
                )

                with st.expander("Matched citations"):
                    matched = verification.get("matched_citations", [])
                    if matched:
                        for citation in matched:
                            pages = ", ".join(
                                str(page)
                                for page in citation.get("pages", [])
                            )
                            st.write(
                                f"- {citation.get('source', 'Unknown source')} "
                                f"— PDF page(s): {pages}"
                            )
                    else:
                        st.write("No matched citations.")

                with st.expander("Citations requiring review"):
                    unmatched = verification.get("unmatched_citations", [])
                    if unmatched:
                        for citation in unmatched:
                            pages = ", ".join(
                                str(page)
                                for page in citation.get("pages", [])
                            )
                            st.write(
                                f"- {citation.get('source', 'Unknown source')} "
                                f"— PDF page(s): {pages}"
                            )
                    else:
                        st.write("No unmatched citations detected.")

                st.caption(
                    "Citation traceability checks whether cited sources and "
                    "pages match retrieved evidence. It does not independently "
                    "prove that every citation supports the scientific claim."
                )

                # Retrieved evidence
                st.divider()
                st.subheader("Retrieved Evidence")
                st.caption(f"Total text chunks: {total_chunks}")

                if sources:
                    for index, source in enumerate(sources, start=1):
                        source_name = source.get("source", "Unknown source")
                        page = source.get("page", "N/A")
                        similarity = source.get("similarity")

                        with st.expander(
                            f"Evidence {index} · {source_name} · Page {page}"
                        ):
                            st.write(source.get("text", "No evidence text."))
                            if isinstance(similarity, (int, float)):
                                st.caption(
                                    f"Similarity score: {similarity:.3f}"
                                )
                else:
                    st.info("No evidence sources were returned.")

                # Markdown report download
                st.divider()
                st.subheader("Export Research Report")

                report_lines = [
                    "# SciGenX Research Report",
                    "",
                    f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    "",
                    "## Research Question",
                    question.strip(),
                    "",
                    "## Research Answer",
                    str(answer),
                    "",
                    "## Citation Verification",
                    f"**Status:** {status}",
                    str(message),
                    "",
                    "## Retrieved Evidence",
                ]

                for index, source in enumerate(sources, start=1):
                    report_lines.extend([
                        "",
                        f"### Evidence {index}",
                        f"- **Source:** {source.get('source', 'Unknown source')}",
                        f"- **Page:** {source.get('page', 'N/A')}",
                        f"- **Similarity:** {source.get('similarity', 'N/A')}",
                        "",
                        str(source.get("text", "")),
                    ])

                report_text = "\n".join(report_lines)

                st.download_button(
                    label="⬇️ Download Markdown Report",
                    data=report_text,
                    file_name="scigenx_research_report.md",
                    mime="text/markdown",
                    use_container_width=True,
                )

        except Exception as error:
            st.error("Research analysis failed.")
            st.exception(error)
