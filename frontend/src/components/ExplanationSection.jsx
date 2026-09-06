export default function ExplanationSection({ explanation, isAnalyzing }) {
  if (isAnalyzing) return null

  const factors = explanation?.factors ?? []
  if (!factors.length) return null

  return (
    <section className="orca-section">
      <div className="section-heading">
        <h2>Why did ORCA make this recommendation?</h2>
        <p>Major factors from collaborative agent reasoning</p>
      </div>

      <div className="factors-grid">
        {factors.map((factor, index) => (
          <div key={factor.id} className="factor-card">
            <div className="factor-card__step">{index + 1}</div>
            <div className="factor-card__icon" aria-hidden="true">
              {factor.icon}
            </div>
            <p className={`factor-card__text factor-card__text--${factor.sentiment}`}>
              {factor.text}
            </p>
          </div>
        ))}
      </div>
    </section>
  )
}
