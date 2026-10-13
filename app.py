import streamlit as st
from datetime import datetime
import html

from src.scigenx_core import (
    analyze_research,
    verify_answer_citations,
)

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="SciGenX | Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# PROFESSIONAL WHITE THEME + ANIMATIONS
# --------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --primary: #4263eb;
        --primary-dark: #304fc4;
        --text: #172033;
        --muted: #64748b;
        --border: #e5eaf2;
        --surface: #ffffff;
        --background: #f6f8fc;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: var(--background);
        color: var(--text);
    }

    [data-testid="stHeader"] {
        background: rgba(246,248,252,.92);
    }

    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.4rem;
    }

    .block-container {
        max-width: 1320px;
        padding-top: 1.8rem;
        padding-bottom: 3rem;
        animation: fadeIn .65s ease-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes cardEnter {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes gentleFloat {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-4px); }
    }

    .brand-row {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 25px;
    }

    .brand-icon {
        min-width: 48px;
        height: 48px;
        border-radius: 15px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        font-size: 25px;
        font-weight: 800;
        background: linear-gradient(135deg, #4263eb, #7950d9);
        box-shadow: 0 7px 18px rgba(66,99,235,.23);
    }

    .brand-name {
        font-size: 24px;
        font-weight: 800;
        letter-spacing: -1px;
        color: #172033;
        margin: 0;
    }

    .brand-caption {
        color: #718096;
        font-size: 10px;
        letter-spacing: 1.4px;
        text-transform: uppercase;
        margin: 1px 0 0;
    }

    .hero {
        position: relative;
        overflow: hidden;
        background: linear-gradient(115deg, #ffffff 5%, #edf3ff 70%, #f2edff 100%);
        border: 1px solid #dce6fb;
        border-radius: 24px;
        padding: 35px;
        margin-bottom: 27px;
        animation: cardEnter .65s ease-out;
    }

    .hero::after {
        content: "";
        position: absolute;
        right: -55px;
        top: -95px;
        width: 240px;
        height: 240px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(99,102,241,.16), transparent 70%);
        pointer-events: none;
    }

    .hero-label {
        display: inline-block;
        color: #4056c7;
        background: #e7edff;
        padding: 7px 12px;
        border-radius: 30px;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 1.3px;
        margin-bottom: 15px;
    }

    .hero h1 {
        font-size: clamp(30px, 4vw, 43px);
        line-height: 1.18;
        font-weight: 800;
        letter-spacing: -1.7px;
        color: #172d55;
        margin: 0 0 13px;
    }

    .hero p {
        color: #52647c;
        font-size: 14px;
        line-height: 1.9;
        max-width: 760px;
        margin: 0;
    }

    .section-heading {
        font-size: 21px;
        font-weight: 750;
        color: #1b2b49;
        letter-spacing: -.5px;
        margin: 12px 0 5px;
    }

    .section-caption {
        font-size: 13px;
        color: #718096;
        margin-bottom: 18px;
    }

    .feature-card {
        background: #fff;
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 19px;
        min-height: 140px;
        transition: transform .25s ease, box-shadow .25s ease;
        animation: cardEnter .6s ease-out;
    }

    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 26px rgba(31,41,55,.07);
    }

    .feature-icon {
        width: 38px;
        height: 38px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 12px;
        color: #4056c7;
        background: #edf1ff;
        font-size: 19px;
        margin-bottom: 12px;
    }

    .feature-title {
        color: #243451;
        font-size: 14px;
        font-weight: 750;
        margin-bottom: 5px;
    }

    .feature-description {
        color: #718096;
        font-size: 12px;
        line-height: 1.7;
    }

    .metric-note {
        color: #718096;
        font-size: 12px;
        margin-top: 5px;
    }

    div[data-testid="stMetric"] {
        background: #fff;
        border: 1px solid var(--border);
        border-radius: 15px;
        padding: 17px;
        box-shadow: 0 3px 10px rgba(15,23,42,.015);
        animation: cardEnter .55s ease-out;
        transition: transform .2s ease, box-shadow .2s ease;
    }

    div[data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 9px 22px rgba(31,41,55,.06);
    }

    div[data-testid="stMetricLabel"] {
        color: #718096;
    }

    div[data-testid="stMetricValue"] {
        color: #20365c;
        font-weight: 800;
    }

    .result-banner {
        background: linear-gradient(110deg, #ffffff, #f0f4ff);
        border: 1px solid #dce6fb;
        border-radius: 16px;
        padding: 19px 22px;
        margin: 18px 0;
        animation: cardEnter .5s ease-out;
    }

    .result-banner-title {
        color: #243b6b;
        font-size: 18px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .result-banner-text {
        color: #718096;
        font-size: 12px;
        line-height: 1.7;
    }

    .evidence-card {
        background: #fff;
        border: 1px solid #e3e9f3;
        border-left: 4px solid #6578e8;
        border-radius: 12px;
        padding: 16px 18px;
        margin: 9px 0;
        transition: transform .22s ease, box-shadow .22s ease;
        animation: cardEnter .45s ease-out;
    }

    .evidence-card:hover {
        transform: translateX(3px);
        box-shadow: 0 7px 18px rgba(15,23,42,.05);
    }

    .evidence-source {
        color: #4056c7;
        font-size: 13px;
        font-weight: 750;
        margin-bottom: 6px;
        overflow-wrap: anywhere;
    }

    .evidence-meta {
        color: #8290a5;
        font-size: 11px;
        margin-bottom: 10px;
    }

    .evidence-text {
        color: #35445b;
        font-size: 13px;
        line-height: 1.8;
        white-space: pre-wrap;
        overflow-wrap: anywhere;
    }

    .footer-note {
        text-align: center;
        color: #98a2b3;
        font-size: 11px;
        padding-top: 8px;
    }

    .stButton > button,
    .stDownloadButton > button,
    .stFormSubmitButton > button {
        border-radius: 10px;
        min-height: 43px;
        font-weight: 650;
        transition: transform .2s ease, box-shadow .2s ease;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover,
    .stFormSubmitButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(66,99,235,.15);
    }

    .stTextArea textarea,
    .stTextInput input {
        background: #fff;
        border-radius: 11px;
        border-color: #dce3ee;
    }

    [data-testid="stFileUploader"] {
        background: #fbfcff;
        border: 1px dashed #bac8ef;
        border-radius: 15px;
        padding: 10px;
    }

    [data-testid="stExpander"] {
        border-color: #e2e8f0;
        border-radius: 12px;
        background: #fff;
    }

    h2, h3 {
        color: #243b6b;
    }

    hr {
        border-color: #e6eaf1;
    }

    @media (max-width: 700px) {
        .hero { padding: 23px; }
        .hero h1 { letter-spacing: -1px; }
    }

    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation-duration: .01ms !important;
            transition-duration: .01ms !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="brand-row">
            <div class="brand-icon">S</div>
            <div>
                <p class="brand-name">SciGenX</p>
                <p class="brand-caption">Research Intelligence</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 📚 Research Workspace")
    st.caption("Explore your research papers and supporting evidence.")

    uploaded_files = st.file_uploader(
        "Upload research papers",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload one or more scientific research papers in PDF format.",
    )

    if uploaded_files:
        st.success(f"{len(uploaded_files)} PDF(s) selected.")

        with st.expander("📄 View uploaded papers"):
            for file in uploaded_files:
                st.write(f"📄 {file.name}")

    st.divider()

    st.markdown("**Your research workflow**")
    st.caption("01 · Upload papers")
    st.caption("02 · Ask a question")
    st.caption("03 · Analyze evidence")
    st.caption("04 · Review citations")

    st.divider()
    st.caption("SciGenX · Academic Research Assistant")

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <span class="hero-label">✦ AI-POWERED RESEARCH WORKSPACE</span>
        <h1>Discover insights.<br>Accelerate research.</h1>
        <p>
            Analyze scientific literature, retrieve relevant evidence,
            review citation traceability, and export your findings —
            all from one research workspace.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# RESEARCH INPUT
# --------------------------------------------------
st.markdown(
    '<div class="section-heading">Research workspace</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="section-caption">Upload your papers in the sidebar, then enter a research question below.</div>',
    unsafe_allow_html=True,
)

with st.form("research_form", clear_on_submit=False):
    question = st.text_area(
        "Research question",
        placeholder=(
            "Example: Compare the methods, datasets, evaluation metrics, "
            "main findings, and limitations of these research papers."
        ),
        height=120,
    )

    analyze_clicked = st.form_submit_button(
        "🔍  Analyze Research",
        use_container_width=True,
        type="primary",
    )

# --------------------------------------------------
# ANALYSIS
# --------------------------------------------------
if analyze_clicked:
    if not uploaded_files:
        st.warning("Please upload at least one research paper in the sidebar.")

    elif not question.strip():
        st.warning("Please enter a research question.")

    else:
        try:
            with st.spinner(
                "Reading papers, retrieving evidence, and preparing your analysis..."
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
                answer = result.get("answer", "No answer was returned.")
                sources = result.get("sources", [])
                total_pages = result.get("total_pages_with_text", 0)
                total_chunks = result.get("total_chunks", 0)

                verification = verify_answer_citations(
                    answer=answer,
                    evidence=sources,
                )

                # Preserve the latest result across Streamlit reruns.
                st.session_state["scigenx_result"] = {
                    "question": question.strip(),
                    "answer": answer,
                    "sources": sources,
                    "total_pages_with_text": total_pages,
                    "total_chunks": total_chunks,
                    "citation_verification": verification,
                    "pdf_count": len(uploaded_files),
                }

                st.success("Research analysis completed successfully.")

        except Exception as error:
            st.error("Research analysis failed.")
            st.exception(error)

# --------------------------------------------------
# DISPLAY RESULTS
# --------------------------------------------------
result = st.session_state.get("scigenx_result")

if result:
    st.markdown(
        """
        <div class="result-banner">
            <div class="result-banner-title">✨ Your research insights</div>
            <div class="result-banner-text">
                Review the generated answer, inspect the supporting evidence,
                and check citation traceability before using the findings.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    answer = result.get("answer", "")
    sources = result.get("sources", [])
    verification = result.get("citation_verification", {})
    total_pages = result.get("total_pages_with_text", 0)
    total_chunks = result.get("total_chunks", 0)

    matched = verification.get("matched_citations", [])
    unmatched = verification.get("unmatched_citations", [])

    matched_count = len(matched) if isinstance(matched, list) else 0
    unmatched_count = len(unmatched) if isinstance(unmatched, list) else 0

    # Overview metrics
    st.markdown(
        '<div class="section-heading">Research overview</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("PDFs Uploaded", result.get("pdf_count", 0))
    col2.metric("Pages with Text", total_pages)
    col3.metric("Evidence Sources", len(sources))
    col4.metric("Text Chunks", total_chunks)

    # Research answer
    st.divider()
    st.markdown(
        '<div class="section-heading">🧠 Research analysis</div>',
        unsafe_allow_html=True,
    )

    st.markdown(answer)

    # Citation verification
    st.divider()
    st.markdown(
        '<div class="section-heading">✓ Citation verification</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-caption">Review how citations correspond to the retrieved evidence.</div>',
        unsafe_allow_html=True,
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

    citation_col1, citation_col2, citation_col3 = st.columns(3)

    citation_col1.metric(
        "Recognized Citations",
        verification.get("total_citations", 0),
    )
    citation_col2.metric("Matched Citations", matched_count)
    citation_col3.metric("Citations to Review", unmatched_count)

    with st.expander("📗 Matched citations", expanded=False):
        if isinstance(matched, list) and matched:
            for citation in matched:
                if isinstance(citation, dict):
                    st.write(
                        f"- {citation.get('source', 'Unknown source')} "
                        f"| Pages: {citation.get('pages', [])}"
                    )
                else:
                    st.write(f"- {citation}")
        else:
            st.write("No matched citations.")

    with st.expander("📙 Citations requiring review", expanded=False):
        if isinstance(unmatched, list) and unmatched:
            for citation in unmatched:
                if isinstance(citation, dict):
                    st.write(
                        f"- {citation.get('source', 'Unknown source')} "
                        f"| Pages: {citation.get('pages', [])}"
                    )
                else:
                    st.write(f"- {citation}")
        else:
            st.write("No unmatched citations detected.")

    st.caption(
        "Citation traceability checks whether citations match retrieved "
        "evidence. It does not independently prove that every citation "
        "supports the scientific claim."
    )

    # Evidence sources
    st.divider()
    st.markdown(
        '<div class="section-heading">📑 Retrieved evidence</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-caption">Inspect the source, page, text, and similarity score for each retrieved passage.</div>',
        unsafe_allow_html=True,
    )

    if sources:
        for index, source in enumerate(sources, start=1):
            source_name = str(source.get("source", "Unknown source"))
            page_number = source.get("page", "N/A")
            similarity = source.get("similarity")
            evidence_text = str(source.get("text", "No evidence text."))

            meta = f"Page {page_number}"
            if isinstance(similarity, (int, float)):
                meta += f"  ·  Similarity score: {similarity:.3f}"

            # Escape source text before placing it inside HTML.
            safe_name = html.escape(source_name)
            safe_meta = html.escape(meta)
            safe_text = html.escape(evidence_text)

            with st.expander(
                f"Evidence {index}  ·  {source_name}  ·  Page {page_number}",
                expanded=(index == 1),
            ):
                st.markdown(
                    f"""
                    <div class="evidence-card">
                        <div class="evidence-source">{safe_name}</div>
                        <div class="evidence-meta">{safe_meta}</div>
                        <div class="evidence-text">{safe_text}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.info("No evidence sources were returned.")

    # Markdown report
    st.divider()
    st.markdown(
        '<div class="section-heading">📥 Export research report</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-caption">Download the research question, answer, citation status, and retrieved evidence as a Markdown file.</div>',
        unsafe_allow_html=True,
    )

    report_lines = [
        "# SciGenX Research Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Research Question",
        result.get("question", ""),
        "",
        "## Research Answer",
        str(answer),
        "",
        "## Citation Verification",
        f"**Status:** {status}",
        str(message),
        f"**Recognized citations:** {verification.get('total_citations', 0)}",
        f"**Matched citations:** {matched_count}",
        f"**Citations requiring review:** {unmatched_count}",
        "",
        "## Retrieved Evidence",
    ]

    for index, source in enumerate(sources, start=1):
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

# --------------------------------------------------
# FEATURE CARDS
# --------------------------------------------------
st.divider()
st.markdown(
    '<div class="section-heading">Built for better research</div>',
    unsafe_allow_html=True,
)

feature1, feature2, feature3 = st.columns(3)

with feature1:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">📄</div>
            <div class="feature-title">Research paper analysis</div>
            <div class="feature-description">
                Ask questions about your uploaded scientific literature.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with feature2:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">🔎</div>
            <div class="feature-title">Evidence retrieval</div>
            <div class="feature-description">
                Inspect relevant text passages and source page references.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with feature3:
    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">✓</div>
            <div class="feature-title">Citation traceability</div>
            <div class="feature-description">
                Review recognized, matched, and unmatched citations.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.divider()
st.markdown(
    """
    <div class="footer-note">
        SciGenX · Evidence-assisted scientific research<br>
        Always review the original papers before relying on scientific conclusions.
    </div>
    """,
    unsafe_allow_html=True,
)