
import { useState, useEffect } from "react";
import "./App.css";

const API = import.meta.env.VITE_API_URL || "/api";

function Icon({ children }) {
  return <span className="icon" aria-hidden="true">{children}</span>;
}

function App() {
  const [page, setPage] = useState("overview");

  const [backendStatus, setBackendStatus] = useState("checking"); // "connected" | "disconnected" | "checking"

  const [searchQuery, setSearchQuery] = useState("");
  const [papers, setPapers] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState("");

  const [question, setQuestion] = useState("");
  const [files, setFiles] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisError, setAnalysisError] = useState("");

  useEffect(() => {
    let isMounted = true;
    async function checkBackend() {
      try {
        const res = await fetch(`${API}/health`);
        if (res.ok && isMounted) {
          setBackendStatus("connected");
        } else if (isMounted) {
          setBackendStatus("disconnected");
        }
      } catch {
        if (isMounted) setBackendStatus("disconnected");
      }
    }

    checkBackend();
    const interval = setInterval(checkBackend, 5000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  async function searchPapers(event) {
    event.preventDefault();

    const query = searchQuery.trim();
    if (query.length < 2) {
      setSearchError("Enter a research topic to search.");
      return;
    }

    setSearchLoading(true);
    setSearchError("");
    setPapers([]);

    try {
      const response = await fetch(
        `${API}/search?q=${encodeURIComponent(query)}`
      );
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || "Search failed.");
      }

      setPapers(data.papers || []);
      if (!data.papers?.length) {
        setSearchError("No papers found. Try a different search phrase.");
      }
    } catch (error) {
      setSearchError(
        error.message || "Could not connect to the SciGenX API."
      );
    } finally {
      setSearchLoading(false);
    }
  }

  async function analyzePapers(event) {
    event.preventDefault();

    if (!question.trim()) {
      setAnalysisError("Enter your research question.");
      return;
    }

    if (!files.length) {
      setAnalysisError("Upload at least one research PDF.");
      return;
    }

    setAnalysisLoading(true);
    setAnalysisError("");
    setAnalysis(null);

    try {
      const formData = new FormData();
      formData.append("question", question.trim());

      for (const file of files) {
        formData.append("papers", file);
      }

      const response = await fetch(`${API}/analyze`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || "Analysis failed.");
      }

      setAnalysis(data);
      setPage("analysis");
    } catch (error) {
      setAnalysisError(
        error.message || "Could not connect to the SciGenX API."
      );
    } finally {
      setAnalysisLoading(false);
    }
  }

  function clearAnalysis() {
    setQuestion("");
    setFiles([]);
    setAnalysis(null);
    setAnalysisError("");

    const fileInput = document.getElementById("pdf-upload");
    if (fileInput) fileInput.value = "";
  }

  const navigation = [
    { id: "overview", icon: "⌂", label: "Overview" },
    { id: "search", icon: "⌕", label: "Search Papers" },
    { id: "analyze", icon: "✳", label: "Analyze Research" },
    { id: "analysis", icon: "▤", label: "Evidence & Results" },
  ];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <button className="brand" onClick={() => setPage("overview")}>
          <span className="brand-mark">S<span>✳</span></span>
          <span>SciGenX<small>AI RESEARCH STUDIO</small></span>
        </button>

        <div className="nav-caption">WORKSPACE</div>

        <nav className="side-nav">
          {navigation.map((item) => (
            <button
              key={item.id}
              className={`nav-link ${page === item.id ? "active" : ""}`}
              onClick={() => setPage(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
              {item.id === "analysis" && analysis && (
                <span className="nav-dot" />
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="local-ai-card">
            <span className="online-dot" />
            <div>
              <strong>Research engine</strong>
              <small>Local AI workflow</small>
            </div>
          </div>
          <p className="sidebar-note">
            Built for evidence-based discovery.
          </p>
          <div className="sidebar-version">SCIGENX · RESEARCH EDITION</div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div>
            <div className="breadcrumb">SciGenX <span>/</span> Workspace</div>
            <div className="topbar-title">
              {navigation.find((item) => item.id === page)?.label ||
                "Research Workspace"}
            </div>
          </div>

          <div className="topbar-right">
            <span
              className="system-status"
              style={{
                color:
                  backendStatus === "connected"
                    ? "#10b981"
                    : backendStatus === "checking"
                    ? "#f59e0b"
                    : "#ef4444",
                borderColor:
                  backendStatus === "connected"
                    ? "rgba(16, 185, 129, 0.2)"
                    : backendStatus === "checking"
                    ? "rgba(245, 158, 11, 0.2)"
                    : "rgba(239, 68, 68, 0.2)",
              }}
            >
              <span
                className="online-dot"
                style={{
                  background:
                    backendStatus === "connected"
                      ? "#10b981"
                      : backendStatus === "checking"
                      ? "#f59e0b"
                      : "#ef4444",
                  boxShadow:
                    backendStatus === "connected"
                      ? "0 0 8px #10b981"
                      : "none",
                }}
              />{" "}
              {backendStatus === "connected"
                ? "Backend Connected"
                : backendStatus === "checking"
                ? "Checking Backend..."
                : "Backend Disconnected"}
            </span>
            <div className="avatar">SX</div>
          </div>
        </header>

        {page === "overview" && (
          <section className="page-content">
            <div className="welcome-hero">
              <div className="hero-copy">
                <div className="eyebrow">
                  <span className="eyebrow-star">✦</span>
                  YOUR AI RESEARCH COMPANION
                </div>
                <h1>Turn research into<br /><span>real discoveries.</span></h1>
                <p>
                  Search academic literature, explore your PDFs, and
                  generate evidence-backed research insights in one workspace.
                </p>
                <div className="hero-actions">
                  <button className="button-primary" onClick={() => setPage("search")}>
                    <Icon>⌕</Icon> Search research papers <span>→</span>
                  </button>
                  <button className="button-secondary" onClick={() => setPage("analyze")}>
                    Analyze your PDFs
                  </button>
                </div>
              </div>

              <div className="science-visual" aria-label="Abstract scientific illustration">
                <div className="orbit orbit-one" />
                <div className="orbit orbit-two" />
                <div className="orbit orbit-three" />
                <div className="visual-core">✳</div>
                <div className="floating-chip chip-paper">▤ <span>Research</span></div>
                <div className="floating-chip chip-ai">✦ <span>AI insights</span></div>
                <div className="floating-chip chip-data">⌁ <span>Evidence</span></div>
                <div className="visual-spark spark-one">✦</div>
                <div className="visual-spark spark-two">·</div>
              </div>
              <div className="hero-decoration decoration-one" />
              <div className="hero-decoration decoration-two" />
            </div>

            <div className="section-heading">
              <div>
                <h2>Your research toolkit</h2>
                <p>Everything you need to move from a question to evidence.</p>
              </div>
            </div>

            <div className="tool-grid">
              <button className="tool-card" onClick={() => setPage("search")}>
                <div className="tool-icon purple">⌕</div>
                <div className="tool-arrow">↗</div>
                <h3>Discover literature</h3>
                <p>Search academic publication records by topic and explore DOI links.</p>
                <span className="tool-link">Explore papers <b>→</b></span>
              </button>

              <button className="tool-card" onClick={() => setPage("analyze")}>
                <div className="tool-icon blue">▤</div>
                <div className="tool-arrow">↗</div>
                <h3>Analyze research PDFs</h3>
                <p>Ask questions about uploaded papers and retrieve relevant evidence.</p>
                <span className="tool-link">Start analysis <b>→</b></span>
              </button>

              <button
                className="tool-card"
                onClick={() => setPage("analysis")}
              >
                <div className="tool-icon green">✓</div>
                <div className="tool-arrow">↗</div>
                <h3>Review evidence</h3>
                <p>Inspect retrieved sources and citation verification results.</p>
                <span className="tool-link">View results <b>→</b></span>
              </button>
            </div>

            <div className="bottom-note">
              <span className="note-icon">✦</span>
              <div>
                <strong>Research with traceability</strong>
                <p>
                  SciGenX links generated answers to retrieved evidence.
                  Citation matching supports traceability; it does not
                  independently prove that every scientific claim is true.
                </p>
              </div>
            </div>
          </section>
        )}

        {page === "search" && (
          <section className="page-content">
            <div className="page-heading">
              <div className="eyebrow">ACADEMIC DISCOVERY</div>
              <h1>Find your next <span>research insight.</span></h1>
              <p>Search academic publication metadata by keyword or research topic.</p>
            </div>

            <form className="search-panel" onSubmit={searchPapers}>
              <label htmlFor="search-query">What are you researching?</label>
              <div className="search-input-row">
                <span className="search-symbol">⌕</span>
                <input
                  id="search-query"
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                  placeholder="e.g. deep learning for plant disease detection"
                />
                <button className="button-primary" type="submit" disabled={searchLoading}>
                  {searchLoading ? "Searching..." : "Search papers →"}
                </button>
              </div>
              <div className="search-hint">
                <span>Try:</span>
                {["RAG for scientific research", "Plant disease detection", "Large language models"].map((term) => (
                  <button
                    key={term}
                    type="button"
                    className="topic-chip"
                    onClick={() => setSearchQuery(term)}
                  >
                    {term}
                  </button>
                ))}
              </div>
            </form>

            {searchError && <div className="message-error">{searchError}</div>}

            {papers.length > 0 && (
              <div className="results-heading">
                <div>
                  <h2>Search results</h2>
                  <p>{papers.length} publication records returned</p>
                </div>
                <span className="results-tag">CROSSREF METADATA</span>
              </div>
            )}

            <div className="paper-list">
              {papers.map((paper, index) => (
                <article className="paper-card" key={paper.doi || `${paper.title}-${index}`}>
                  <div className="paper-type-icon">▤</div>
                  <div className="paper-info">
                    <div className="paper-meta">
                      <span>PUBLICATION</span>
                      {paper.year && <span>{paper.year}</span>}
                      {paper.journal && <span>{paper.journal}</span>}
                    </div>
                    <h3>{paper.title}</h3>
                    <p className="paper-authors">
                      {paper.authors?.join(", ") || "Author details unavailable"}
                      {paper.authors?.length === 5 ? " et al." : ""}
                    </p>
                    {paper.publisher && <p className="publisher">Publisher: {paper.publisher}</p>}
                    <div className="paper-actions">
                      {paper.doi && <span className="doi-label">DOI: {paper.doi}</span>}
                      {paper.url && (
                        <a href={paper.url} target="_blank" rel="noreferrer">
                          Open publication ↗
                        </a>
                      )}
                    </div>
                  </div>
                </article>
              ))}
            </div>

            {!searchLoading && papers.length === 0 && !searchError && (
              <div className="empty-state">
                <div className="empty-illustration">⌕</div>
                <h3>Your next paper starts with a search</h3>
                <p>Enter a topic above to find academic publication records.</p>
              </div>
            )}
          </section>
        )}

        {page === "analyze" && (
          <section className="page-content">
            <div className="page-heading">
              <div className="eyebrow">EVIDENCE-BASED ANALYSIS</div>
              <h1>Ask better <span>research questions.</span></h1>
              <p>Upload papers and let SciGenX retrieve relevant evidence for your question.</p>
            </div>

            <div className="analysis-layout">
              <form className="analysis-panel" onSubmit={analyzePapers}>
                <div className="panel-title-row">
                  <div className="tool-icon blue">✳</div>
                  <div>
                    <h2>Research workspace</h2>
                    <p>Provide a question and your source documents.</p>
                  </div>
                </div>

                <label htmlFor="research-question">Your research question</label>
                <textarea
                  id="research-question"
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  placeholder="How does deep learning improve early detection of plant leaf diseases compared to traditional machine learning methods?"
                  rows={5}
                />

                <div className="label-row">
                  <label htmlFor="pdf-upload">Research papers (PDF)</label>
                  <span>MAXIMUM 50 MB TOTAL</span>
                </div>
                <label className="upload-zone" htmlFor="pdf-upload">
                  <span className="upload-icon">↑</span>
                  <strong>Drop your papers into the workspace</strong>
                  <span>or click to browse PDF files</span>
                  <small>PDF documents only</small>
                  <input
                    id="pdf-upload"
                    type="file"
                    accept=".pdf,application/pdf"
                    multiple
                    onChange={(event) => setFiles(Array.from(event.target.files || []))}
                  />
                </label>

                {files.length > 0 && (
                  <div className="selected-files">
                    <div className="selected-files-heading">
                      <strong>{files.length} file(s) selected</strong>
                      <button type="button" onClick={() => {
                        setFiles([]);
                        const input = document.getElementById("pdf-upload");
                        if (input) input.value = "";
                      }}>Remove all</button>
                    </div>
                    {files.map((file) => (
                      <div className="selected-file" key={`${file.name}-${file.size}`}>
                        <span className="pdf-badge">PDF</span>
                        <span className="filename">{file.name}</span>
                        <span className="filesize">{(file.size / (1024 * 1024)).toFixed(2)} MB</span>
                      </div>
                    ))}
                  </div>
                )}

                {analysisError && <div className="message-error">{analysisError}</div>}

                <div className="form-actions">
                  <button
                    type="button"
                    className="button-secondary"
                    onClick={clearAnalysis}
                  >
                    Clear
                  </button>
                  <button
                    type="submit"
                    className="button-primary"
                    disabled={analysisLoading}
                  >
                    {analysisLoading ? "Analyzing papers..." : "✦ Analyze research"}
                  </button>
                </div>
                {analysisLoading && (
                  <div className="progress-track">
                    <div className="progress-bar" />
                    <p>Extracting, retrieving and analyzing evidence. This can take a little while.</p>
                  </div>
                )}
              </form>

              <aside className="workflow-panel">
                <div className="workflow-heading">
                  <span className="tool-icon purple">✧</span>
                  <div>
                    <h3>How it works</h3>
                    <p>From source papers to insights</p>
                  </div>
                </div>
                {[
                  ["01", "Extract documents", "Read text and page content from your PDFs."],
                  ["02", "Retrieve evidence", "Find relevant chunks using semantic retrieval."],
                  ["03", "Generate analysis", "Use the local language model to answer."],
                  ["04", "Check citations", "Match citations against retrieved evidence."],
                ].map(([number, title, description]) => (
                  <div className="workflow-step" key={number}>
                    <span className="step-number">{number}</span>
                    <div><strong>{title}</strong><p>{description}</p></div>
                  </div>
                ))}
                <div className="workflow-footnote">
                  <span className="online-dot" />
                  Existing SciGenX research core
                </div>
              </aside>
            </div>
          </section>
        )}

        {page === "analysis" && (
          <section className="page-content">
            <div className="page-heading">
              <div className="eyebrow">RESEARCH OUTPUT</div>
              <h1>Your evidence <span>workspace.</span></h1>
              <p>Review the latest analysis, retrieved sources and citation checks.</p>
            </div>

            {!analysis ? (
              <div className="empty-state">
                <div className="empty-illustration">▤</div>
                <h3>No analysis to display yet</h3>
                <p>Upload research PDFs and run an analysis to see the evidence here.</p>
                <button className="button-primary" onClick={() => setPage("analyze")}>
                  Start an analysis →
                </button>
              </div>
            ) : (
              <>
                <div className="summary-grid">
                  <div className="summary-card">
                    <span className="summary-icon">▤</span>
                    <span className="summary-value">{analysis.total_pages_with_text ?? 0}</span>
                    <span className="summary-label">Pages with text</span>
                  </div>
                  <div className="summary-card">
                    <span className="summary-icon">⌘</span>
                    <span className="summary-value">{analysis.total_chunks ?? 0}</span>
                    <span className="summary-label">Text chunks</span>
                  </div>
                  <div className="summary-card">
                    <span className="summary-icon">⌕</span>
                    <span className="summary-value">{analysis.sources?.length ?? 0}</span>
                    <span className="summary-label">Evidence sources</span>
                  </div>
                </div>

                <article className="answer-panel">
                  <div className="panel-title-row">
                    <div className="tool-icon blue">✦</div>
                    <div>
                      <h2>AI research answer</h2>
                      <p>Generated from your uploaded documents</p>
                    </div>
                  </div>
                  <div className="question-quote">
                    <strong>RESEARCH QUESTION</strong>
                    <p>{analysis.question}</p>
                  </div>
                  <div className="answer-body">
                    {analysis.answer || "No answer was returned by the research engine."}
                  </div>
                </article>

                <article className="answer-panel">
                  <div className="panel-title-row">
                    <div className="tool-icon green">✓</div>
                    <div>
                      <h2>Citation verification</h2>
                      <p>Traceability check against retrieved evidence</p>
                    </div>
                  </div>
                  {analysis.citation_verification ? (
                    <>
                      <div className="verification-status">
                        <span className="status-dot" />
                        {analysis.citation_verification.status || "Verification completed"}
                      </div>
                      <p>{analysis.citation_verification.message || "Verification details returned by SciGenX."}</p>
                      <div className="verification-grid">
                        <div><strong>{analysis.citation_verification.total_citations ?? 0}</strong><span>Total citations</span></div>
                        <div><strong>{analysis.citation_verification.matched_citations ?? 0}</strong><span>Matched citations</span></div>
                        <div><strong>{analysis.citation_verification.unmatched_citations ?? 0}</strong><span>Unmatched citations</span></div>
                      </div>
                    </>
                  ) : (
                    <p>No citation verification details were returned.</p>
                  )}
                  <p className="disclaimer">
                    Citation matching checks traceability to retrieved evidence; it is not a guarantee of factual accuracy.
                  </p>
                </article>

                <article className="answer-panel">
                  <div className="panel-title-row">
                    <div className="tool-icon purple">▤</div>
                    <div>
                      <h2>Retrieved evidence</h2>
                      <p>Sources supplied to the research answer</p>
                    </div>
                  </div>
                  {analysis.sources?.length ? (
                    analysis.sources.map((source, index) => (
                      <div className="evidence-item" key={index}>
                        <div className="evidence-number">{String(index + 1).padStart(2, "0")}</div>
                        <div>
                          <strong>
                            {source.source || source.filename || source.file || `Evidence source ${index + 1}`}
                          </strong>
                          {source.page != null && <span className="page-label">Page {source.page}</span>}
                          <p>{source.text || source.content || source.chunk || "Evidence text unavailable."}</p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p>No evidence sources were returned for this answer.</p>
                  )}
                </article>

                <button className="button-secondary" onClick={() => setPage("analyze")}>
                  ← Run another analysis
                </button>
              </>
            )}
          </section>
        )}

        <footer className="app-footer">
          <span>© SciGenX · AI Research Workspace</span>
          <span>Evidence first. Insights next.</span>
        </footer>
      </main>
    </div>
  );
}

export default App;
