export default function Header() {
  return (
    <header className="orca-header">
      <div className="orca-header__brand">
        <div className="orca-header__logo" aria-hidden="true">
          <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="24" cy="24" r="22" stroke="currentColor" strokeWidth="2" />
            <path
              d="M8 28c6-4 12-4 18 0s12 4 18 0"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
            <path
              d="M10 22c5-3 10-3 15 0s10 3 15 0"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              opacity="0.6"
            />
            <circle cx="24" cy="16" r="3" fill="currentColor" opacity="0.85" />
          </svg>
        </div>
        <div>
          <h1 className="orca-header__title">ORCA</h1>
          <p className="orca-header__tagline">
            Marine Ecosystem Reasoning with Collaborative Agents
          </p>
        </div>
      </div>
      <div className="orca-header__badge">
        <span className="orca-header__badge-dot" />
        SIH Demo · Marine Intelligence
      </div>
    </header>
  )
}
