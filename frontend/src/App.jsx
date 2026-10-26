import { useCallback, useEffect, useMemo, useState } from 'react'
import './App.css'

const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')
const SAMPLE_TITLE = 'Hydration serum launch · Instagram'
const SAMPLE_CONTENT =
  'Meet your new daily hydration serum. It gives you guaranteed results in 3 days. It is 100% risk-free and proven to cure all diseases.'

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...options.headers,
    },
  })
  if (!response.ok) {
    const problem = await response.json().catch(() => ({}))
    throw new Error(problem.detail || `Request failed (${response.status})`)
  }
  return response.json()
}

function Icon({ name, size = 18 }) {
  const paths = {
    grid: <><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" /></>,
    plus: <><path d="M12 5v14M5 12h14" /></>,
    book: <><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21z" /><path d="M4 5.5v13A2.5 2.5 0 0 1 6.5 16H20" /></>,
    clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
    arrow: <><path d="M7 17 17 7M7 7h10v10" /></>,
    check: <><path d="m5 12 4 4L19 6" /></>,
    alert: <><path d="M12 3 2.8 19h18.4L12 3Z" /><path d="M12 9v4m0 3h.01" /></>,
    sparkle: <><path d="m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z" /><path d="m19 14 .9 2.1L22 17l-2.1.9L19 20l-.9-2.1L16 17l2.1-.9L19 14Z" /></>,
    shield: <><path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Z" /><path d="m9 12 2 2 4-4" /></>,
  }
  return (
    <svg aria-hidden="true" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      {paths[name]}
    </svg>
  )
}

function StatusPill({ status }) {
  const labels = {
    needs_review: 'Awaiting decision',
    approved: 'Approved',
    changes_requested: 'Changes requested',
  }
  return <span className={`status-pill status-${status}`}>{labels[status] || status}</span>
}

function IssueCard({ finding, index }) {
  return (
    <article className="issue-card">
      <div className="issue-topline">
        <span className={`severity severity-${finding.severity}`}>
          <Icon name={finding.severity === 'high' ? 'alert' : 'sparkle'} size={14} />
          {finding.severity === 'high' ? 'High priority' : 'Needs verification'}
        </span>
        <span className="issue-number">ISSUE {String(index + 1).padStart(2, '0')}</span>
      </div>
      <h3>{finding.category}</h3>
      <blockquote>“{finding.matched_text}”</blockquote>
      <p className="issue-reason">{finding.reason}</p>
      <div className="citation">
        <span className="citation-label"><Icon name="book" size={14} /> SOURCE · {finding.source_id}</span>
        <p>{finding.source_text}</p>
      </div>
      <div className="suggestion">
        <span>Suggested next step</span>
        <p>{finding.suggestion}</p>
      </div>
    </article>
  )
}

function App() {
  const [page, setPage] = useState('review')
  const [title, setTitle] = useState(SAMPLE_TITLE)
  const [content, setContent] = useState(SAMPLE_CONTENT)
  const [policy, setPolicy] = useState({ rules: [], facts: [] })
  const [reviews, setReviews] = useState([])
  const [activeReview, setActiveReview] = useState(null)
  const [loading, setLoading] = useState(true)
  const [checking, setChecking] = useState(false)
  const [savingDecision, setSavingDecision] = useState(false)
  const [error, setError] = useState('')
  const [ruleInput, setRuleInput] = useState('')
  const [factInput, setFactInput] = useState('')
  const [policyMessage, setPolicyMessage] = useState('')
  const [decisionNote, setDecisionNote] = useState('')

  const loadWorkspace = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [nextPolicy, history] = await Promise.all([
        api('/api/policy'),
        api('/api/reviews'),
      ])
      setPolicy(nextPolicy)
      setReviews(history.reviews)
    } catch (loadError) {
      setError(loadError.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let active = true
    async function loadInitialWorkspace() {
      try {
        const [nextPolicy, history] = await Promise.all([
          api('/api/policy'),
          api('/api/reviews'),
        ])
        if (active) {
          setPolicy(nextPolicy)
          setReviews(history.reviews)
        }
      } catch (loadError) {
        if (active) setError(loadError.message)
      } finally {
        if (active) setLoading(false)
      }
    }
    loadInitialWorkspace()
    return () => { active = false }
  }, [])

  const totals = useMemo(() => ({
    reviews: reviews.length,
    issues: reviews.reduce((sum, review) => sum + review.total_issues, 0),
    waiting: reviews.filter((review) => review.status === 'needs_review').length,
  }), [reviews])

  function startNewReview() {
    setPage('review')
    setTitle('')
    setContent('')
    setActiveReview(null)
    setDecisionNote('')
    setError('')
  }

  async function runReview(event) {
    event.preventDefault()
    setChecking(true)
    setError('')
    setActiveReview(null)
    try {
      const review = await api('/api/reviews', {
        method: 'POST',
        body: JSON.stringify({ title, content }),
      })
      setActiveReview(review)
      setTitle(review.title)
      setDecisionNote('')
      await loadWorkspace()
    } catch (reviewError) {
      setError(reviewError.message)
    } finally {
      setChecking(false)
    }
  }

  async function openReview(reviewId) {
    setError('')
    try {
      const review = await api(`/api/reviews/${reviewId}`)
      setActiveReview(review)
      setTitle(review.title)
      setContent(review.content)
      setDecisionNote(review.reviewer_note || '')
      setPage('review')
    } catch (reviewError) {
      setError(reviewError.message)
    }
  }

  async function submitDecision(decision) {
    if (!activeReview) return
    setSavingDecision(true)
    setError('')
    try {
      const review = await api(`/api/reviews/${activeReview.id}/decision`, {
        method: 'PATCH',
        body: JSON.stringify({ decision, note: decisionNote }),
      })
      setActiveReview(review)
      await loadWorkspace()
    } catch (decisionError) {
      setError(decisionError.message)
    } finally {
      setSavingDecision(false)
    }
  }

  async function addPolicyItem(event, kind) {
    event.preventDefault()
    setError('')
    setPolicyMessage('')
    try {
      if (kind === 'rule') {
        await api('/api/policy/rules', {
          method: 'POST',
          body: JSON.stringify({ term: ruleInput }),
        })
        setRuleInput('')
        setPolicyMessage('Banned term added. It will be checked in the next review.')
      } else {
        await api('/api/policy/facts', {
          method: 'POST',
          body: JSON.stringify({ text: factInput }),
        })
        setFactInput('')
        setPolicyMessage('Approved fact added to your brand register.')
      }
      await loadWorkspace()
    } catch (policyError) {
      setError(policyError.message)
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#" onClick={(event) => { event.preventDefault(); setPage('review') }}>
          <span className="brand-mark"><Icon name="shield" size={21} /></span>
          <span className="brand-name">brand<span>lens</span><small>BRAND GOVERNANCE</small></span>
        </a>
        <div className="workspace-switcher">
          <span className="workspace-avatar">S</span>
          <span><strong>Studio workspace</strong><small>Free demo workspace</small></span>
          <span className="chevron">⌄</span>
        </div>
        <div className="nav-label">WORKSPACE</div>
        <nav className="main-nav" aria-label="Main navigation">
          <button className={page === 'review' ? 'nav-item active' : 'nav-item'} onClick={() => setPage('review')}>
            <Icon name="grid" /> Overview
          </button>
          <button className="nav-item" onClick={startNewReview}>
            <Icon name="plus" /> New review
          </button>
          <button className={page === 'policy' ? 'nav-item active' : 'nav-item'} onClick={() => { setPage('policy'); setPolicyMessage('') }}>
            <Icon name="book" /> Brand policy
            <span className="nav-count">{policy.rules.length + policy.facts.length}</span>
          </button>
          <button className={page === 'history' ? 'nav-item active' : 'nav-item'} onClick={() => setPage('history')}>
            <Icon name="clock" /> Review history
          </button>
        </nav>
        <div className="sidebar-bottom">
          <div className="privacy-note">
            <span className="privacy-icon"><Icon name="shield" size={17} /></span>
            <strong>Human-led by design</strong>
            <p>Checks suggest. Your team makes every final call.</p>
          </div>
          <div className="profile">
            <span className="profile-avatar">Y</span>
            <span><strong>Yuvraj Sonkar</strong><small>Workspace owner</small></span>
            <span className="more">···</span>
          </div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumbs"><span>Studio workspace</span><b>/</b><strong>{page === 'policy' ? 'Brand policy' : page === 'history' ? 'Review history' : 'Overview'}</strong></div>
          <div className="topbar-right"><span className="secure-label"><span /> Demo environment</span><span className="top-avatar">Y</span></div>
        </header>

        <div className="content-wrap">
          {error && <div className="error-banner" role="alert"><Icon name="alert" size={17} />{error}<button onClick={() => setError('')} aria-label="Dismiss error">×</button></div>}

          {page === 'review' && (
            <>
              <section className="page-heading">
                <div>
                  <div className="eyebrow">BRAND GOVERNANCE <span>·</span> WORKSPACE</div>
                  <h1>Review workspace</h1>
                  <p>Make every draft feel like it came from one brand.</p>
                </div>
                <button className="button button-primary" onClick={startNewReview}><Icon name="plus" size={17} /> New review</button>
              </section>

              <section className="metrics-row" aria-label="Workspace summary">
                <article className="metric-card"><span className="metric-icon lilac"><Icon name="grid" /></span><div><span>Drafts reviewed</span><strong>{totals.reviews}</strong></div><small className="metric-caption">Saved to this workspace</small></article>
                <article className="metric-card"><span className="metric-icon peach"><Icon name="alert" /></span><div><span>Findings to review</span><strong>{totals.issues}</strong></div><small className="metric-caption">Across recent reviews</small></article>
                <article className="metric-card"><span className="metric-icon mint"><Icon name="clock" /></span><div><span>Awaiting your call</span><strong>{totals.waiting}</strong></div><small className="metric-caption">Human decision required</small></article>
              </section>

              <div className="section-title-row"><div><h2>Content review</h2><p>Check a draft against your active brand rules and approved facts.</p></div><span className="engine-badge"><span /> RULE-BASED CHECKS</span></div>
              <div className="review-layout">
                <section className="panel editor-panel">
                  <div className="panel-heading"><div><span className="panel-icon"><Icon name="plus" size={17} /></span><div><h2>Draft content</h2><p>Paste in the text you want to review.</p></div></div><span className="channel-tag">TEXT REVIEW</span></div>
                  <form onSubmit={runReview}>
                    <label className="field-label" htmlFor="draft-title">DRAFT NAME</label>
                    <input id="draft-title" className="text-input" value={title} onChange={(event) => setTitle(event.target.value)} maxLength={120} placeholder="e.g. Summer campaign · Instagram" />
                    <div className="textarea-label"><label className="field-label" htmlFor="draft-content">CONTENT</label><span>{content.length.toLocaleString()} / 20,000</span></div>
                    <textarea id="draft-content" className="draft-textarea" value={content} onChange={(event) => setContent(event.target.value)} maxLength={20000} required placeholder="Paste your marketing copy here. BrandLens will check it against your policy..." />
                    <div className="editor-footer"><span><Icon name="shield" size={15} /> Your draft stays in this demo workspace.</span><button className="button button-primary check-button" disabled={checking || loading || !content.trim()} type="submit">{checking ? <span className="spinner" /> : <Icon name="sparkle" size={17} />}{checking ? 'Checking draft…' : 'Check my draft'}</button></div>
                  </form>
                  <div className="editor-tip"><span className="tip-bulb">✳</span><p><strong>New here?</strong> We’ve added a sample draft with a few issues. Run the check to see how findings are explained.</p><button onClick={() => { setTitle(SAMPLE_TITLE); setContent(SAMPLE_CONTENT); setActiveReview(null) }}>Load sample</button></div>
                </section>

                <section className="panel findings-panel">
                  <div className="panel-heading findings-heading"><div><span className="panel-icon findings-icon"><Icon name="sparkle" size={17} /></span><div><h2>Review findings</h2><p>Evidence first. A person always decides.</p></div></div>{activeReview && <StatusPill status={activeReview.status} />}</div>
                  {loading && !activeReview ? <div className="empty-findings"><span className="empty-symbol"><span className="spinner" /></span><strong>Connecting to your workspace</strong><p>Loading brand policy and recent reviews…</p></div> : !activeReview ? (
                    <div className="empty-findings"><span className="empty-symbol"><Icon name="shield" size={23} /></span><strong>Your findings will show up here</strong><p>Run a check to see exact quotes, the relevant policy source, and a clear next step.</p><span className="empty-hint"><Icon name="arrow" size={14} /> Start with the sample draft on the left</span></div>
                  ) : (
                    <>
                      <div className="findings-summary"><span className={activeReview.total_issues ? 'summary-dot has-issues' : 'summary-dot'} /><strong>{activeReview.total_issues ? `${activeReview.total_issues} ${activeReview.total_issues === 1 ? 'finding' : 'findings'} need attention` : 'No issues found'}</strong><span>{activeReview.total_issues ? 'Review each before you decide.' : 'This draft passed the active checks.'}</span></div>
                      {activeReview.findings.length ? <div className="issue-list">{activeReview.findings.map((finding, index) => <IssueCard key={`${finding.rule_id}-${index}`} finding={finding} index={index} />)}</div> : <div className="clean-result"><span><Icon name="check" size={23} /></span><strong>Looking good so far</strong><p>No active rule or claim checks were triggered. Your team still makes the final approval decision.</p></div>}
                      <div className="decision-box">
                        <div className="decision-title"><Icon name="shield" size={17} /><div><strong>Your decision</strong><span>Automated checks never approve or publish content.</span></div></div>
                        {activeReview.reviewer_note && activeReview.status !== 'needs_review' && <div className="saved-note"><strong>Reviewer note</strong><p>{activeReview.reviewer_note}</p></div>}
                        <label className="field-label" htmlFor="decision-note">OPTIONAL REVIEWER NOTE</label>
                        <textarea id="decision-note" className="note-input" value={decisionNote} onChange={(event) => setDecisionNote(event.target.value)} maxLength={1000} placeholder="Add context for the content creator…" />
                        <div className="decision-actions"><button className="button button-outline" onClick={() => submitDecision('changes_requested')} disabled={savingDecision}>{savingDecision ? 'Saving…' : 'Request changes'}</button><button className="button button-approve" onClick={() => submitDecision('approved')} disabled={savingDecision}><Icon name="check" size={16} />{savingDecision ? 'Saving…' : 'Approve draft'}</button></div>
                      </div>
                      {activeReview.audit_log?.length > 0 && <div className="audit-line"><Icon name="clock" size={14} /> Activity recorded · {activeReview.audit_log.length} event{activeReview.audit_log.length === 1 ? '' : 's'}</div>}
                    </>
                  )}
                </section>
              </div>
              <div className="disclaimer"><Icon name="shield" size={15} /><span><strong>Human review matters.</strong> These deterministic checks are an assistant, not legal or compliance advice. Verify every claim and make the final call yourself.</span></div>
            </>
          )}

          {page === 'policy' && (
            <>
              <section className="page-heading">
                <div><div className="eyebrow">WORKSPACE <span>·</span> CONFIGURATION</div><h1>Brand policy</h1><p>Give every review a shared source of truth.</p></div>
                <span className="policy-count"><Icon name="shield" size={16} /> {policy.rules.length + policy.facts.length} active checks</span>
              </section>
              {policyMessage && <div className="success-banner"><Icon name="check" size={17} />{policyMessage}<button onClick={() => setPolicyMessage('')} aria-label="Dismiss message">×</button></div>}
              <div className="policy-grid">
                <section className="panel policy-panel">
                  <div className="policy-panel-heading"><span className="metric-icon peach"><Icon name="alert" /></span><div><h2>Banned terms</h2><p>Phrases your content should never use.</p></div></div>
                  <form className="add-policy-form" onSubmit={(event) => addPolicyItem(event, 'rule')}><label className="field-label" htmlFor="new-rule">ADD A BANNED PHRASE</label><div className="inline-form"><input id="new-rule" className="text-input" value={ruleInput} onChange={(event) => setRuleInput(event.target.value)} minLength={2} maxLength={120} required placeholder="e.g. risk-free results" /><button className="button button-primary" type="submit">Add term</button></div></form>
                  <div className="policy-list">{policy.rules.map((rule) => <div className="policy-row" key={rule.rule_id}><span className="rule-dot" /><span>{rule.term}</span><code>{rule.rule_id}</code></div>)}</div>
                </section>
                <section className="panel policy-panel">
                  <div className="policy-panel-heading"><span className="metric-icon mint"><Icon name="check" /></span><div><h2>Approved facts</h2><p>Statements your team has verified.</p></div></div>
                  <form className="add-policy-form" onSubmit={(event) => addPolicyItem(event, 'fact')}><label className="field-label" htmlFor="new-fact">ADD AN APPROVED FACT</label><div className="inline-form"><input id="new-fact" className="text-input" value={factInput} onChange={(event) => setFactInput(event.target.value)} minLength={8} maxLength={500} required placeholder="e.g. Delivery takes 3-5 business days" /><button className="button button-primary" type="submit">Add fact</button></div></form>
                  <div className="policy-list">{policy.facts.map((fact) => <div className="policy-row fact-row" key={fact.fact_id}><span className="fact-check"><Icon name="check" size={13} /></span><span>{fact.text}</span><code>{fact.fact_id}</code></div>)}</div>
                </section>
              </div>
              <div className="policy-footnote"><Icon name="sparkle" size={16} /><span><strong>How checks work:</strong> Exact phrase matches cite their policy ID. Numeric and absolute claims are flagged when no exact approved fact is present. Findings are deterministic suggestions, not AI-generated legal judgments.</span></div>
            </>
          )}

          {page === 'history' && (
            <>
              <section className="page-heading"><div><div className="eyebrow">WORKSPACE <span>·</span> ACTIVITY</div><h1>Review history</h1><p>Every submitted draft and human decision, in one place.</p></div><button className="button button-primary" onClick={startNewReview}><Icon name="plus" size={17} /> New review</button></section>
              <section className="panel history-panel"><div className="history-heading"><div><h2>Recent reviews</h2><p>{reviews.length} saved {reviews.length === 1 ? 'review' : 'reviews'}</p></div><span className="history-retention">Latest 30</span></div>
                {loading ? <div className="history-empty">Loading review history…</div> : reviews.length === 0 ? <div className="history-empty"><span className="empty-symbol"><Icon name="clock" /></span><strong>No reviews yet</strong><p>Run a draft through BrandLens to start your review history.</p><button className="button button-primary" onClick={startNewReview}>Start a review</button></div> : <div className="history-table-wrap"><table className="history-table"><thead><tr><th>DRAFT</th><th>STATUS</th><th>FINDINGS</th><th>LAST UPDATED</th><th /></tr></thead><tbody>{reviews.map((review) => <tr key={review.id}><td><strong>{review.title}</strong><span>Review #{review.id}</span></td><td><StatusPill status={review.status} /></td><td><span className="finding-count">{review.total_issues}</span></td><td>{new Date(review.updated_at).toLocaleString()}</td><td><button className="open-review" onClick={() => openReview(review.id)}>Open <Icon name="arrow" size={14} /></button></td></tr>)}</tbody></table></div>}
              </section>
            </>
          )}
          <footer className="app-footer"><span>BRANDLENS <span className="footer-dot">·</span> ROUND 2 BUILD</span><span>Evidence-first checks. Human-led decisions.</span></footer>
        </div>
      </main>
    </div>
  )
}

export default App
