
import streamlit as st

from src.scigenx_core import (
    analyze_research,
    verify_answer_citations,
)


# Page configuration
st.set_page_config(
    page_title="SciGenX",
    page_icon="🔬",
    layout="wide"
)

# Title
st.title("🔬 SciGenX")
st.subheader("Agentic RAG Scientific Research Assistant")

st.write(
    "Upload research papers, ask research questions, "
    "retrieve evidence, compare papers, and discover potential research gaps."
)

st.divider()


# Sidebar
with st.sidebar:
    st.header("📚 Research Papers")

    uploaded_files = st.file_uploader(
        "Upload PDF research papers",
        type=["pdf"],
        accept_multiple_files=True
    )


# Main section
st.header("🔎 Research Question")

question = st.text_area(
    "Enter your research question",
    placeholder=(
        "Example: What are the limitations of deep learning "
        "approaches for plant disease detection?"
    )
)


# Analyze button
if st.button("🚀 Analyze Research", use_container_width=True):

    if not uploaded_files:
        st.warning("Please upload at least one research paper.")

    elif not question.strip():
        st.warning("Please enter your research question.")

    else:
        st.write("### 📄 Uploaded Papers")

        for file in uploaded_files:
            st.write(f"• {file.name}")

        st.write("### ❓ Research Question")
        st.info(question)

        try:
            with st.spinner(
                "Extracting PDF text, retrieving evidence, "
                "and generating your research answer..."
            ):
                result = analyze_research(
                    pdf_files=uploaded_files,
                    question=question
                )

            st.success("Research analysis completed!")

            # Research answer
            st.header("🧠 Research Answer")
            st.markdown(result["answer"])

            # Citation verification
            st.divider()
            st.header("🔍 Citation Verification")

            verification = verify_answer_citations(
                answer=result["answer"],
                evidence=result["sources"]
            )

            status = verification["status"]

            if status == "TRACEABLE":
                st.success("✅ Citations match retrieved source pages.")

            elif status == "REVIEW_REQUIRED":
                st.warning(
                    "⚠️ Some citations could not be matched "
                    "to the retrieved evidence."
                )

            elif status == "NO_RECOGNIZED_CITATIONS":
                st.info(
                    "No citations in the expected format were found. "
                    "The answer may need clearer source citations."
                )

            else:
                st.info(verification["message"])

            st.write(verification["message"])

            st.metric(
                "Recognized citations",
                verification["total_citations"]
            )

            with st.expander("✅ Matched citations"):
                if verification["matched_citations"]:
                    for citation in verification["matched_citations"]:
                        pages = ", ".join(
                            str(page) for page in citation["pages"]
                        )
                        st.write(
                            f"- {citation['source']} — PDF page(s): {pages}"
                        )
                else:
                    st.write("No matched citations.")

            with st.expander("⚠️ Citations requiring review"):
                if verification["unmatched_citations"]:
                    for citation in verification["unmatched_citations"]:
                        pages = ", ".join(
                            str(page) for page in citation["pages"]
                        )
                        st.write(
                            f"- {citation['source']} — PDF page(s): {pages}"
                        )
                else:
                    st.write("No unmatched citations detected.")

            st.caption(
                "Note: This check verifies whether cited filenames and "
                "page numbers occur in the retrieved evidence. It does "
                "not independently prove that each passage supports "
                "the associated scientific claim."
            )

            # Retrieved evidence
            st.divider()
            st.header("📚 Retrieved Evidence")

            st.write(
                f"Pages with text: {result['total_pages_with_text']} | "
                f"Text chunks: {result['total_chunks']}"
            )

            for i, source in enumerate(result["sources"], start=1):
                with st.expander(
                    f"Evidence {i}: {source['source']} — "
                    f"Page {source['page']}"
                ):
                    st.write(source["text"])
                    st.caption(
                        f"Similarity score: {source['similarity']:.3f}"
                    )

        except Exception as e:
            st.error(
                "Research analysis failed. Please check the error below."
            )
            st.exception(e)