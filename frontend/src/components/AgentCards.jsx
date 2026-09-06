import { AGENT_META, AGENT_STATUS } from '../data/mockData.js'

const STATUS_CONFIG = {
  [AGENT_STATUS.IDLE]: { icon: '○', label: 'Ready', className: 'status-idle' },
  [AGENT_STATUS.PROCESSING]: { icon: '⏳', label: 'Processing', className: 'status-processing' },
  [AGENT_STATUS.COMPLETED]: { icon: '✓', label: 'Completed', className: 'status-completed' },
  [AGENT_STATUS.UNAVAILABLE]: {
    icon: '⚠',
    label: 'Data unavailable',
    className: 'status-unavailable',
  },
}

export default function AgentCards({ agents }) {
  const agentKeys = ['weather', 'ocean', 'marine']

  return (
    <section className="orca-section">
      <div className="section-heading">
        <h2>Multi-Agent Analysis</h2>
        <p>Collaborative agents assess weather, ocean, and marine conditions</p>
      </div>

      <div className="agent-grid">
        {agentKeys.map((key) => {
          const meta = AGENT_META[key]
          const agent = agents?.[key]
          const status = agent?.status ?? AGENT_STATUS.IDLE
          const config = STATUS_CONFIG[status] ?? STATUS_CONFIG[AGENT_STATUS.IDLE]

          return (
            <article key={key} className={`agent-card agent-card--${key}`}>
              <div className="agent-card__icon">{meta.icon}</div>
              <div className="agent-card__body">
                <h3>{agent?.name ?? meta.label}</h3>
                <span className={`agent-status ${config.className}`}>
                  <span aria-hidden="true">{config.icon}</span>
                  {config.label}
                </span>
              </div>
            </article>
          )
        })}
      </div>
    </section>
  )
}
