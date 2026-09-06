import {
  AGENT_STATUS,
  analysisResponse,
  highRiskResponse,
  initialDemoResponse,
} from '../data/mockData.js'

const ANALYSIS_DELAY_MS = 2200

/**
 * Simulates backend analysis. Replace this module with real API calls.
 * @param {{ query: string, location: string, datetime: string }} params
 * @returns {Promise<object>}
 */
export function runMockAnalysis({ query, location, datetime }) {
  const normalized = `${query} ${location} ${datetime}`.toLowerCase()

  const useHighRisk =
    normalized.includes('unsafe') ||
    normalized.includes('storm') ||
    normalized.includes('danger')

  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(useHighRisk ? highRiskResponse : analysisResponse)
    }, ANALYSIS_DELAY_MS)
  })
}

/**
 * Returns processing-state snapshot while agents work.
 */
export function getProcessingSnapshot() {
  const processing = { name: '', status: AGENT_STATUS.PROCESSING }
  return {
    ...initialDemoResponse,
    agents: {
      weather: { ...processing, name: 'Weather Agent' },
      ocean: { ...processing, name: 'Ocean Agent' },
      marine: { ...processing, name: 'Marine Agent' },
    },
    recommendation: null,
    evidence: [],
    explanation: { factors: [] },
  }
}
