/**
 * ORCA mock data — replace with backend API responses later.
 * Shape mirrors expected API contract for easy swap.
 */

export const DEFAULT_QUERY =
  'Is it safe to fish tomorrow morning near Mangalore?'

export const DEFAULT_LOCATION = 'Mangalore, Karnataka'
export const DEFAULT_DATETIME = '2026-09-02T06:00'

/** Mangalore coastal area center */
export const MAP_CENTER = [12.9141, 74.856]

export const AGENT_META = {
  weather: { id: 'weather', icon: '🌦️', label: 'Weather Agent' },
  ocean: { id: 'ocean', icon: '🌊', label: 'Ocean Agent' },
  marine: { id: 'marine', icon: '🐟', label: 'Marine Agent' },
}

export const AGENT_STATUS = {
  IDLE: 'idle',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  UNAVAILABLE: 'unavailable',
}

export const RISK_LEVELS = {
  LOW: 'LOW',
  MODERATE: 'MODERATE',
  HIGH: 'HIGH',
}

/** Initial demo state shown before first analysis */
export const initialDemoResponse = {
  agents: {
    weather: { name: 'Weather Agent', status: AGENT_STATUS.IDLE },
    ocean: { name: 'Ocean Agent', status: AGENT_STATUS.IDLE },
    marine: { name: 'Marine Agent', status: AGENT_STATUS.IDLE },
  },
  recommendation: {
    riskLevel: RISK_LEVELS.MODERATE,
    title: 'Fishing with caution',
    reason:
      'Moderate wave conditions and wind, while marine indicators are favorable.',
    confidence: 78,
  },
  evidence: [
    {
      id: 'wind',
      label: 'Wind',
      value: '18',
      unit: 'km/h',
      description: 'Moderate onshore breeze',
      source: 'IMD',
    },
    {
      id: 'waveHeight',
      label: 'Wave Height',
      value: '1.8',
      unit: 'm',
      description: 'Moderate swell near coast',
      source: 'INCOIS',
    },
    {
      id: 'sst',
      label: 'SST',
      value: '28.4',
      unit: '°C',
      description: 'Within optimal range',
      source: 'INCOIS',
    },
    {
      id: 'chlorophyll',
      label: 'Chlorophyll',
      value: '0.42',
      unit: 'mg/m³',
      description: 'Productive waters detected',
      source: 'INCOIS',
    },
    {
      id: 'pfz',
      label: 'PFZ',
      value: 'Favorable',
      unit: '',
      description: 'Potential fishing zone identified',
      source: 'INCOIS',
    },
    {
      id: 'warnings',
      label: 'Warnings',
      value: 'No major warning',
      unit: '',
      description: 'No active IMD marine alerts',
      source: 'IMD',
    },
  ],
  explanation: {
    factors: [
      { id: 'wave', text: 'Moderate wave height', sentiment: 'neutral', icon: '🌊' },
      { id: 'wind', text: 'Moderate wind conditions', sentiment: 'neutral', icon: '💨' },
      { id: 'sst', text: 'Favorable SST', sentiment: 'positive', icon: '🌡️' },
      {
        id: 'chlorophyll',
        text: 'Favorable chlorophyll concentration',
        sentiment: 'positive',
        icon: '🌿',
      },
      { id: 'pfz', text: 'PFZ detected', sentiment: 'positive', icon: '📍' },
      {
        id: 'warning',
        text: 'No major marine warning',
        sentiment: 'positive',
        icon: '✅',
      },
    ],
  },
  map: {
    center: MAP_CENTER,
    zoom: 10,
    userLocation: {
      lat: 12.9141,
      lng: 74.856,
      label: 'Query Location — Mangalore',
    },
    pfzZone: {
      center: [12.95, 74.82],
      radius: 8000,
      label: 'Potential Fishing Zone (PFZ)',
    },
    riskZones: [
      {
        id: 'safe-1',
        level: 'LOW',
        center: [12.88, 74.78],
        radius: 5000,
        label: 'Safe — sheltered nearshore',
      },
      {
        id: 'moderate-1',
        level: 'MODERATE',
        center: [12.93, 74.87],
        radius: 6000,
        label: 'Moderate risk — open shelf',
      },
      {
        id: 'high-1',
        level: 'HIGH',
        center: [13.02, 74.92],
        radius: 4000,
        label: 'High risk — rough swell band',
      },
    ],
    warnings: [
      {
        id: 'warn-1',
        lat: 13.0,
        lng: 74.9,
        message: 'Moderate swell advisory — exercise caution offshore',
      },
    ],
  },
}

/** Full analysis result returned after mock API delay */
export const analysisResponse = {
  ...initialDemoResponse,
  agents: {
    weather: { name: 'Weather Agent', status: AGENT_STATUS.COMPLETED },
    ocean: { name: 'Ocean Agent', status: AGENT_STATUS.COMPLETED },
    marine: { name: 'Marine Agent', status: AGENT_STATUS.COMPLETED },
  },
}

/** Alternate scenario for different queries (demo variety) */
export const highRiskResponse = {
  ...initialDemoResponse,
  agents: {
    weather: { name: 'Weather Agent', status: AGENT_STATUS.COMPLETED },
    ocean: { name: 'Ocean Agent', status: AGENT_STATUS.COMPLETED },
    marine: { name: 'Marine Agent', status: AGENT_STATUS.UNAVAILABLE },
  },
  recommendation: {
    riskLevel: RISK_LEVELS.HIGH,
    title: 'Avoid fishing',
    reason:
      'Strong winds and high swell detected. Marine agent data partially unavailable.',
    confidence: 85,
  },
  evidence: initialDemoResponse.evidence.map((item) =>
    item.id === 'wind'
      ? { ...item, value: '42', description: 'Strong gusts expected' }
      : item.id === 'waveHeight'
        ? { ...item, value: '3.2', description: 'High swell — unsafe for small craft' }
        : item.id === 'warnings'
          ? {
              ...item,
              value: 'High swell warning',
              description: 'IMD marine warning active',
            }
          : item,
  ),
  explanation: {
    factors: [
      { id: 'wave', text: 'High wave height', sentiment: 'negative', icon: '🌊' },
      { id: 'wind', text: 'Strong wind conditions', sentiment: 'negative', icon: '💨' },
      { id: 'warning', text: 'Active marine warning', sentiment: 'negative', icon: '⚠️' },
      { id: 'marine', text: 'Marine data partially unavailable', sentiment: 'negative', icon: '🐟' },
    ],
  },
}
