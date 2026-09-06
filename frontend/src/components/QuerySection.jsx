import { DEFAULT_LOCATION } from '../data/mockData.js'

export default function QuerySection({
  query,
  location,
  datetime,
  isAnalyzing,
  onQueryChange,
  onLocationChange,
  onDatetimeChange,
  onAnalyze,
}) {
  return (
    <section className="orca-section query-section">
      <div className="section-heading">
        <h2>Ask ORCA</h2>
        <p>Query marine conditions and get multi-agent fishing intelligence</p>
      </div>

      <div className="query-form">
        <label className="field-label" htmlFor="orca-query">
          Your question
        </label>
        <textarea
          id="orca-query"
          className="query-input"
          rows={3}
          placeholder="e.g. Is it safe to fish tomorrow morning near Mangalore?"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          disabled={isAnalyzing}
        />

        <div className="query-form__meta">
          <div className="field-group">
            <label className="field-label" htmlFor="orca-location">
              Location <span className="optional">(optional)</span>
            </label>
            <input
              id="orca-location"
              type="text"
              className="field-input"
              placeholder={DEFAULT_LOCATION}
              value={location}
              onChange={(e) => onLocationChange(e.target.value)}
              disabled={isAnalyzing}
            />
          </div>

          <div className="field-group">
            <label className="field-label" htmlFor="orca-datetime">
              Date &amp; time <span className="optional">(optional)</span>
            </label>
            <input
              id="orca-datetime"
              type="datetime-local"
              className="field-input"
              value={datetime}
              onChange={(e) => onDatetimeChange(e.target.value)}
              disabled={isAnalyzing}
            />
          </div>
        </div>

        <button
          type="button"
          className="analyze-btn"
          onClick={onAnalyze}
          disabled={isAnalyzing || !query.trim()}
        >
          {isAnalyzing ? (
            <>
              <span className="spinner" aria-hidden="true" />
              Analyzing…
            </>
          ) : (
            'Analyze'
          )}
        </button>
      </div>
    </section>
  )
}
