import { RISK_LEVELS } from '../data/mockData.js'

const RISK_CONFIG = {
  [RISK_LEVELS.LOW]: { emoji: '🟢', className: 'risk-low', label: 'LOW RISK' },
  [RISK_LEVELS.MODERATE]: {
    emoji: '🟡',
    className: 'risk-moderate',
    label: 'MODERATE RISK',
  },
  [RISK_LEVELS.HIGH]: { emoji: '🔴', className: 'risk-high', label: 'HIGH RISK' },
}

export default function RecommendationCard({ recommendation, isAnalyzing }) {
  if (isAnalyzing) {
    return (
      <section className="orca-section">
        <div className="recommendation-card recommendation-card--loading">
          <div className="recommendation-skeleton">
            <span className="spinner spinner--lg" />
            <p>Synthesizing multi-agent recommendation…</p>
          </div>
        </div>
      </section>
    )
  }

  if (!recommendation) return null

  const config = RISK_CONFIG[recommendation.riskLevel] ?? RISK_CONFIG[RISK_LEVELS.MODERATE]

  return (
    <section className="orca-section">
      <div className={`recommendation-card ${config.className}`}>
        <div className="recommendation-card__header">
          <span className="recommendation-card__risk">
            {config.emoji} {config.label}
          </span>
          {recommendation.confidence != null && (
            <span className="recommendation-card__confidence">
              Confidence: {recommendation.confidence}%
            </span>
          )}
        </div>
        <h2 className="recommendation-card__title">{recommendation.title}</h2>
        <div className="recommendation-card__reason">
          <strong>Reason:</strong> {recommendation.reason}
        </div>
      </div>
    </section>
  )
}
