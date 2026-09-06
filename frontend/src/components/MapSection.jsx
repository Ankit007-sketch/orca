import { useEffect } from 'react'
import { MapContainer, TileLayer, Circle, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const RISK_COLORS = {
  LOW: { fill: '#22c55e', stroke: '#16a34a' },
  MODERATE: { fill: '#eab308', stroke: '#ca8a04' },
  HIGH: { fill: '#ef4444', stroke: '#dc2626' },
}

const PFZ_COLOR = { fill: '#0ea5e9', stroke: '#0284c7' }

function createIcon(color, symbol) {
  return L.divIcon({
    className: 'orca-map-icon',
    html: `<div style="background:${color};width:28px;height:28px;border-radius:50%;border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.3);display:flex;align-items:center;justify-content:center;font-size:14px;">${symbol}</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  })
}

const userIcon = createIcon('#0369a1', '📍')
const warningIcon = createIcon('#f97316', '⚠')

function MapUpdater({ center, zoom }) {
  const map = useMap()
  useEffect(() => {
    map.setView(center, zoom, { animate: true })
  }, [map, center, zoom])
  return null
}

function MapLegend() {
  return (
    <div className="map-legend">
      <span className="map-legend__title">Legend</span>
      <div className="map-legend__item">
        <span className="map-legend__swatch map-legend__swatch--safe" />
        Safe area
      </div>
      <div className="map-legend__item">
        <span className="map-legend__swatch map-legend__swatch--moderate" />
        Moderate risk
      </div>
      <div className="map-legend__item">
        <span className="map-legend__swatch map-legend__swatch--high" />
        High risk
      </div>
      <div className="map-legend__item">
        <span className="map-legend__swatch map-legend__swatch--pfz" />
        PFZ
      </div>
    </div>
  )
}

export default function MapSection({ mapData, isAnalyzing }) {
  if (!mapData) return null

  const { center, zoom, userLocation, pfzZone, riskZones, warnings } = mapData

  return (
    <section className="orca-section">
      <div className="section-heading">
        <h2>Interactive Map</h2>
        <p>Coastal intelligence overlay — Mangalore region</p>
      </div>

      <div className={`map-wrapper ${isAnalyzing ? 'map-wrapper--loading' : ''}`}>
        {isAnalyzing && (
          <div className="map-overlay">
            <span className="spinner spinner--lg" />
            <span>Updating map layers…</span>
          </div>
        )}

        <MapContainer
          center={center}
          zoom={zoom}
          scrollWheelZoom
          className="orca-map"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <MapUpdater center={center} zoom={zoom} />

          {riskZones?.map((zone) => {
            const colors = RISK_COLORS[zone.level] ?? RISK_COLORS.MODERATE
            return (
              <Circle
                key={zone.id}
                center={zone.center}
                radius={zone.radius}
                pathOptions={{
                  color: colors.stroke,
                  fillColor: colors.fill,
                  fillOpacity: 0.25,
                  weight: 2,
                }}
              >
                <Popup>
                  <strong>{zone.level} Risk</strong>
                  <br />
                  {zone.label}
                </Popup>
              </Circle>
            )
          })}

          {pfzZone && (
            <Circle
              center={pfzZone.center}
              radius={pfzZone.radius}
              pathOptions={{
                color: PFZ_COLOR.stroke,
                fillColor: PFZ_COLOR.fill,
                fillOpacity: 0.2,
                weight: 2,
                dashArray: '6 4',
              }}
            >
              <Popup>
                <strong>{pfzZone.label}</strong>
              </Popup>
            </Circle>
          )}

          {userLocation && (
            <Marker
              position={[userLocation.lat, userLocation.lng]}
              icon={userIcon}
            >
              <Popup>
                <strong>{userLocation.label}</strong>
              </Popup>
            </Marker>
          )}

          {warnings?.map((w) => (
            <Marker key={w.id} position={[w.lat, w.lng]} icon={warningIcon}>
              <Popup>
                <strong>Marine Warning</strong>
                <br />
                {w.message}
              </Popup>
            </Marker>
          ))}
        </MapContainer>

        <MapLegend />
      </div>
    </section>
  )
}
