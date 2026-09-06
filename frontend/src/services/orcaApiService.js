/**
 * Real ORCA backend integration.
 *
 * Talks to the FastAPI backend built in backend/ (see backend/main.py,
 * backend/api/routes.py) and converts its UnifiedResponse payload into the
 * exact shape the existing UI components already render (see
 * frontend/src/data/mockData.js for the reference shape). App.jsx tries this
 * first and falls back to mockAnalysisService.js if the backend can't be
 * reached, so the demo keeps working even if the server isn't running.
 */

import { AGENT_STATUS, MAP_CENTER, RISK_LEVELS } from '../data/mockData.js'

export const API_BASE_URL =
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) ||
  'http://localhost:8000'

// A handful of well-known Indian coastal locations so the free-text
// "Location" field can be turned into coordinates for the backend, which
// requires WGS84 lat/lon. Falls back to the Mangalore demo point (matches
// MAP_CENTER) for anything not recognized -- extend this list as needed.
const KNOWN_LOCATIONS = {
  mangalore: [12.9141, 74.856],
  chennai: [13.08, 80.27],
  mumbai: [18.96, 72.82],
  kochi: [9.93, 76.26],
  cochin: [9.93, 76.26],
  visakhapatnam: [17.68, 83.22],
  vizag: [17.68, 83.22],
  lakshadweep: [10.57, 72.64],
  andaman: [11.62, 92.73],
  goa: [15.3, 73.82],
  kolkata: [22.57, 88.36],
  puducherry: [11.94, 79.81],
  thiruvananthapuram: [8.52, 76.94],
  trivandrum: [8.52, 76.94],
}

function resolveCoordinates(locationText) {
  const normalized = (locationText || '').toLowerCase()
  const match = Object.keys(KNOWN_LOCATIONS).find((key) => normalized.includes(key))
  if (match) return KNOWN_LOCATIONS[match]
  return MAP_CENTER
}

function getSessionId() {
  const key = 'orca_session_id'
  let sessionId = sessionStorage.getItem(key)
  if (!sessionId) {
    sessionId = `orca-web-${Math.random().toString(36).slice(2, 10)}`
    sessionStorage.setItem(key, sessionId)
  }
  return sessionId
}

const RISK_LEVEL_MAP = {
  SAFE: RISK_LEVELS.LOW,
  CAUTION: RISK_LEVELS.MODERATE,
  UNSAFE: RISK_LEVELS.HIGH,
}

const RECOMMENDATION_TITLE = {
  SAFE: 'Safe for fishing',
  CAUTION: 'Fishing with caution',
  UNSAFE: 'Avoid fishing',
}

function agentStatusFromResult(result) {
  if (!result) return AGENT_STATUS.UNAVAILABLE
  if (result.status === 'partial_error' || result.errors?.length) {
    return AGENT_STATUS.UNAVAILABLE
  }
  return AGENT_STATUS.COMPLETED
}

function factorSentiment(severity) {
  if (severity === 'critical' || severity === 'high') return 'negative'
  if (severity === 'moderate') return 'neutral'
  return 'positive'
}

function factorIcon(factorName = '') {
  const name = factorName.toLowerCase()
  if (name.includes('wind')) return '💨'
  if (name.includes('wave')) return '🌊'
  if (name.includes('current')) return '🔄'
  if (name.includes('mpa')) return '🚫'
  if (name.includes('imbl') || name.includes('boundary')) return '🚧'
  if (name.includes('cyclone')) return '🌀'
  return '📊'
}

/**
 * Converts a backend UnifiedResponse (see backend/models/response.py) into
 * the { agents, recommendation, evidence, explanation, map } shape that
 * AgentCards / RecommendationCard / EvidenceCards / ExplanationSection /
 * MapSection already know how to render.
 */
export function mapUnifiedResponseToUI(unified, { lat, lon, locationLabel }) {
  const weather = unified.agent_assessments?.weather_agent
  const ocean = unified.agent_assessments?.ocean_agent
  const marine = unified.agent_assessments?.marine_agent

  const wData = weather?.data || {}
  const oData = ocean?.data || {}
  const mData = marine?.data || {}

  const backendRiskLevel = unified.risk?.level || 'CAUTION'
  const riskLevel = RISK_LEVEL_MAP[backendRiskLevel] || RISK_LEVELS.MODERATE

  const agents = {
    weather: { name: 'Weather Agent', status: agentStatusFromResult(weather) },
    ocean: { name: 'Ocean Agent', status: agentStatusFromResult(ocean) },
    marine: { name: 'Marine Agent', status: agentStatusFromResult(marine) },
  }

  const recommendation = {
    riskLevel,
    title: RECOMMENDATION_TITLE[backendRiskLevel] || 'Analysis complete',
    reason: unified.recommendation,
    confidence: Math.round((unified.risk?.confidence ?? 0.9) * 100),
  }

  const evidence = [
    {
      id: 'wind',
      label: 'Wind',
      value: wData.wind_speed_kmh ?? '—',
      unit: 'km/h',
      description: weather?.assessment?.summary || 'Wind conditions',
      source: 'IMD',
    },
    {
      id: 'waveHeight',
      label: 'Wave Height',
      value: oData.wave_height_m ?? '—',
      unit: 'm',
      description: ocean?.assessment?.summary || 'Sea state',
      source: 'INCOIS',
    },
    {
      id: 'sst',
      label: 'SST',
      value: oData.sea_surface_temperature_c ?? '—',
      unit: '°C',
      description: 'Sea surface temperature',
      source: 'INCOIS',
    },
    {
      id: 'chlorophyll',
      label: 'Chlorophyll',
      value: mData.chlorophyll_mg_m3 ?? '—',
      unit: 'mg/m³',
      description: marine?.assessment?.summary || 'Ocean colour reading',
      source: 'IRS P4 OCM',
    },
    {
      id: 'pfz',
      label: 'PFZ',
      value: mData.pfz_detected ? 'Favorable' : 'Not detected',
      unit: '',
      description: mData.mpa_violation
        ? `Inside ${mData.mpa_name || 'a Marine Protected Area'}`
        : 'Potential fishing zone status',
      source: 'INCOIS',
    },
    {
      id: 'warnings',
      label: 'Warnings',
      value: unified.risk?.primary_hazard || 'No major warning',
      unit: '',
      description: mData.mpa_violation
        ? 'Marine Protected Area restriction active'
        : 'Active alerts, if any',
      source: 'IMD / Coast Guard',
    },
  ]

  const serverFactors = (unified.risk?.contributing_factors || []).map((f, i) => ({
    id: `factor-${i}`,
    text: f.description,
    sentiment: factorSentiment(f.severity),
    icon: factorIcon(f.factor_name),
  }))

  if (mData.pfz_detected) {
    serverFactors.push({
      id: 'pfz-factor',
      text: 'Potential Fishing Zone detected',
      sentiment: 'positive',
      icon: '📍',
    })
  }

  const explanation = { factors: serverFactors }

  const riskZoneColor =
    backendRiskLevel === 'UNSAFE' ? 'HIGH' : backendRiskLevel === 'CAUTION' ? 'MODERATE' : 'LOW'

  const map = {
    center: [lat, lon],
    zoom: 10,
    userLocation: { lat, lng: lon, label: `Query Location — ${locationLabel}` },
    pfzZone: mData.pfz_detected
      ? { center: [lat + 0.03, lon - 0.05], radius: 8000, label: 'Potential Fishing Zone (PFZ)' }
      : null,
    riskZones: [
      {
        id: 'zone-1',
        level: riskZoneColor,
        center: [lat, lon],
        radius: 6000,
        label: `${backendRiskLevel} — ${unified.risk?.primary_hazard || 'overall assessment'}`,
      },
    ],
    warnings: mData.mpa_violation
      ? [{ id: 'warn-mpa', lat, lng: lon, message: `Inside ${mData.mpa_name || 'a Marine Protected Area'}` }]
      : [],
  }

  return { agents, recommendation, evidence, explanation, map }
}

/**
 * Calls the real backend. Throws on any network/HTTP failure so the caller
 * (App.jsx) can fall back to the mock service.
 */
export async function runRealAnalysis({ query, location, datetime }) {
  const [lat, lon] = resolveCoordinates(location)

  const response = await fetch(`${API_BASE_URL}/api/v1/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: getSessionId(),
      user_query: query,
      latitude: lat,
      longitude: lon,
      language_code: 'en',
      timestamp: datetime ? new Date(datetime).toISOString() : undefined,
    }),
  })

  if (!response.ok) {
    throw new Error(`ORCA backend returned ${response.status}`)
  }

  const unified = await response.json()
  return mapUnifiedResponseToUI(unified, { lat, lon, locationLabel: location || 'Selected location' })
}
