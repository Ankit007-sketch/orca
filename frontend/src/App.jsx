import { useCallback, useState } from 'react'
import Header from './components/Header.jsx'
import QuerySection from './components/QuerySection.jsx'
import AgentCards from './components/AgentCards.jsx'
import RecommendationCard from './components/RecommendationCard.jsx'
import EvidenceCards from './components/EvidenceCards.jsx'
import MapSection from './components/MapSection.jsx'
import ExplanationSection from './components/ExplanationSection.jsx'
import {
  DEFAULT_DATETIME,
  DEFAULT_LOCATION,
  DEFAULT_QUERY,
  initialDemoResponse,
} from './data/mockData.js'
import {
  getProcessingSnapshot,
  runMockAnalysis,
} from './services/mockAnalysisService.js'
import { runRealAnalysis } from './services/orcaApiService.js'
import './App.css'

export default function App() {
  const [query, setQuery] = useState(DEFAULT_QUERY)
  const [location, setLocation] = useState(DEFAULT_LOCATION)
  const [datetime, setDatetime] = useState(DEFAULT_DATETIME)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisData, setAnalysisData] = useState(initialDemoResponse)
  const [hasAnalyzed, setHasAnalyzed] = useState(false)

  const handleAnalyze = useCallback(async () => {
    if (!query.trim() || isAnalyzing) return

    setIsAnalyzing(true)
    setAnalysisData(getProcessingSnapshot())

    try {
      // Try the real ORCA backend first; if it's unreachable (not running,
      // network error, etc.) fall back to the mock service so the demo
      // still works.
      let result
      try {
        result = await runRealAnalysis({ query, location, datetime })
      } catch (err) {
        console.warn('ORCA backend unavailable, falling back to mock data:', err)
        result = await runMockAnalysis({ query, location, datetime })
      }
      setAnalysisData(result)
      setHasAnalyzed(true)
    } finally {
      setIsAnalyzing(false)
    }
  }, [query, location, datetime, isAnalyzing])

  const showResults = hasAnalyzed || !isAnalyzing

  return (
    <div className="orca-app">
      <Header />

      <main className="orca-main">
        <QuerySection
          query={query}
          location={location}
          datetime={datetime}
          isAnalyzing={isAnalyzing}
          onQueryChange={setQuery}
          onLocationChange={setLocation}
          onDatetimeChange={setDatetime}
          onAnalyze={handleAnalyze}
        />

        <AgentCards agents={analysisData.agents} />

        <RecommendationCard
          recommendation={isAnalyzing ? null : analysisData.recommendation}
          isAnalyzing={isAnalyzing}
        />

        {!isAnalyzing && showResults && (
          <>
            <EvidenceCards evidence={analysisData.evidence} isAnalyzing={false} />
            <MapSection mapData={analysisData.map} isAnalyzing={false} />
            <ExplanationSection explanation={analysisData.explanation} isAnalyzing={false} />
          </>
        )}

        {isAnalyzing && (
          <>
            <EvidenceCards evidence={[]} isAnalyzing />
            <MapSection mapData={analysisData.map} isAnalyzing />
          </>
        )}
      </main>

      <footer className="orca-footer">
        <p>
          ORCA · Marine Ecosystem Reasoning with Collaborative Agents · Live backend when
          available, demo data otherwise
        </p>
      </footer>
    </div>
  )
}
