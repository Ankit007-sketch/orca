export default function EvidenceCards({ evidence, isAnalyzing }) {
  if (isAnalyzing) {
    return (
      <section className="orca-section">
        <div className="section-heading">
          <h2>Evidence &amp; Data</h2>
          <p>Collecting observational data from IMD and INCOIS sources</p>
        </div>
        <div className="evidence-grid evidence-grid--loading">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="evidence-card evidence-card--skeleton" />
          ))}
        </div>
      </section>
    )
  }

  if (!evidence?.length) return null

  return (
    <section className="orca-section">
      <div className="section-heading">
        <h2>Evidence &amp; Data</h2>
        <p>Key indicators supporting the ORCA recommendation</p>
      </div>

      <div className="evidence-grid">
        {evidence.map((item) => (
          <article key={item.id} className="evidence-card">
            <h3>{item.label}</h3>
            <p className="evidence-card__value">
              {item.value}
              {item.unit && <span className="evidence-card__unit"> {item.unit}</span>}
            </p>
            <p className="evidence-card__desc">{item.description}</p>
            <p className="evidence-card__source">Source: {item.source}</p>
          </article>
        ))}
      </div>
    </section>
  )
}
