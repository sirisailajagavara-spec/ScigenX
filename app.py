
import streamlit as st
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

# ---------- Professional White Theme ----------
st.markdown(
    """
    <style>
    .stApp {
        background: #f5f7fb;
        color: #172033;
    }

    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e5eaf2;
    }

    .block-container {
        max-width: 1250px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .hero {
        background: linear-gradient(120deg, #ffffff, #edf4ff);
        border: 1px solid #dce6f5;
        border-radius: 20px;
        padding: 30px;
        margin-bottom: 25px;
    }

    .hero h1 {
        color: #173c73;
        font-size: 2.5rem;
        margin-bottom: 8px;
    }

    .hero p {
        color: #52647c;
        font-size: 1.05rem;
        margin-bottom: 0;
    }

    .section-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 16px;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
    }

    div.stButton > button,
    div.stDownloadButton > button {
        background: #2457a7;
        color: white;
        border: none;
        border-radius: 9px;
        min-height: 44px;
        font-weight: 600;
    }

    div.stButton > button:hover,
    div.stDownloadButton > button:hover {
        background: #183f80;
        color: white;
        border: none;
    }

    h2, h3 {
        color: #183b70;
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
            evidence retrieval, citation verification and research discovery.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- Sidebar ----------
with st.sidebar:
    st.title("📚 Research Workspace")
    st.caption("Explore your research papers and evidence.")

    uploaded_files = st.file_uploader(
        "Upload research papers",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload one or more research papers in PDF format.",
    )

    if uploaded_files:
        st.success(f"{len(uploaded_files)} PDF(s) selected.")

        with st.expander("View uploaded papers"):
            for file in uploaded_files:
                st.write(f"📄 {file.name}")

    st.divider()
    st.caption("SciGenX · Academic Research Assistant")

# ---------- Research Input ----------
st.subheader("Research Workspace")
st.write(
    "Enter a research question to retrieve relevant evidence "
    "from your uploaded scientific papers."
)

question = st.text_area(
    "Research question",
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
                    "Unexpected result from analyze_research(). "
                    "Please check src/scigenx_core.py."
                )

            else:
                answer = result.get(
                    "answer", "No answer was returned."
                )
                sources = result.get("sources", [])
                total_pages = result.get(
                    "total_pages_with_text", 0
                )
                total_chunks = result.get("total_chunks", 0)

                st.divider()
                st.subheader("Research Overview")

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "PDFs Uploaded", len(uploaded_files)
                )
                col2.metric(
                    "Pages with Text", total_pages
                )
                col3.metric(
                    "Evidence Retrieved", len(sources)
                )

                # Research answer
                st.divider()
                st.subheader("Research Analysis")
                st.markdown(answer)

                # Citation verification
                st.divider()
                st.subheader("Citation Verification")

                verification = verify_answer_citations(
                    answer=answer,
                    evidence=sources,
                )

                status = verification.get(
                    "status", "UNKNOWN"
                )
                message = verification.get(
                    "message", status
                )

                if status == "TRACEABLE":
                    st.success(message)
                elif status == "REVIEW_REQUIRED":
                    st.warning(message)
                elif status == "NO_RECOGNIZED_CITATIONS":
                    st.info(message)
                else:
                    st.info(message)

                st.metric(
                    "Recognized Citations",
                    verification.get("total_citations", 0),
                )

                with st.expander("Matched Citations"):
                    matched = verification.get(
                        "matched_citations", []
                    )

                    if matched:
                        for citation in matched:
                            st.write(
                                f"- {citation.get('source', 'Unknown source')} "
                                f"| Pages: {citation.get('pages', [])}"
                            )
                    else:
                        st.write("No matched citations.")

                with st.expander("Citations Requiring Review"):
                    unmatched = verification.get(
                        "unmatched_citations", []
                    )

                    if unmatched:
                        for citation in unmatched:
                            st.write(
                                f"- {citation.get('source', 'Unknown source')} "
                                f"| Pages: {citation.get('pages', [])}"
                            )
                    else:
                        st.write("No unmatched citations detected.")

                st.caption(
                    "Citation traceability checks whether citations "
                    "match retrieved evidence. It does not independently "
                    "prove that every citation supports the scientific claim."
                )

                # Retrieved evidence
                st.divider()
                st.subheader("Retrieved Evidence")
                st.caption(f"Total text chunks: {total_chunks}")

                if sources:
                    for index, source in enumerate(
                        sources, start=1
                    ):
                        source_name = source.get(
                            "source", "Unknown source"
                        )
                        page = source.get("page", "N/A")
                        similarity = source.get("similarity")

                        with st.expander(
                            f"Evidence {index} · {source_name} · Page {page}"
                        ):
                            st.write(
                                source.get(
                                    "text", "No evidence text."
                                )
                            )

                            if isinstance(
                                similarity, (int, float)
                            ):
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

                for index, source in enumerate(
                    sources, start=1
                ):
                    report_lines.extend(
                        [
                            "",
                            f"### Evidence {index}",
                            f"- **Source:** {source.get('source', 'Unknown source')}",
                            f"- **Page:** {source.get('page', 'N/A')}",
                            f"- **Similarity:** {source.get('similarity', 'N/A')}",
                            "",
                            str(source.get("text", "")),
                        ]
                    )

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

# ---------- Footer ----------
st.divider()
st.caption(
    "SciGenX | Evidence-assisted research. "
    "Always review source papers before relying on scientific conclusions."
)
