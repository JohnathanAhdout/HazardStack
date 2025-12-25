'use client'

import { useEffect } from 'react'
import dynamic from 'next/dynamic'
import { MapPin } from 'lucide-react'

// Dynamic import to avoid SSR issues with Leaflet
const MapContainer = dynamic(
  () => import('react-leaflet').then((mod) => mod.MapContainer),
  { ssr: false }
)
const TileLayer = dynamic(
  () => import('react-leaflet').then((mod) => mod.TileLayer),
  { ssr: false }
)
const Marker = dynamic(
  () => import('react-leaflet').then((mod) => mod.Marker),
  { ssr: false }
)
const Popup = dynamic(
  () => import('react-leaflet').then((mod) => mod.Popup),
  { ssr: false }
)
const Circle = dynamic(
  () => import('react-leaflet').then((mod) => mod.Circle),
  { ssr: false }
)

interface MapViewProps {
  onLocationSelect: (lat: number, lon: number) => void
  selectedLocation: { lat: number, lon: number }
  riskData: any
}

// Component to handle map click events
function MapClickHandler({ onLocationSelect }: { onLocationSelect: (lat: number, lon: number) => void }) {
  if (typeof window === 'undefined') return null

  const { useMapEvents } = require('react-leaflet')

  useMapEvents({
    click: (e: any) => {
      onLocationSelect(e.latlng.lat, e.latlng.lng)
    },
  })

  return null
}

export default function MapView({ onLocationSelect, selectedLocation, riskData }: MapViewProps) {
  useEffect(() => {
    // Import Leaflet CSS on client side only
    if (typeof window !== 'undefined') {
      require('leaflet/dist/leaflet.css')
    }
  }, [])

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'LOW': return '#22C55E'
      case 'MODERATE': return '#F59E0B'
      case 'HIGH': return '#EF4444'
      case 'EXTREME': return '#7C2D12'
      default: return '#6B7280'
    }
  }

  if (typeof window === 'undefined') {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-100 rounded">
        <div className="text-center">
          <MapPin className="w-12 h-12 mx-auto text-gray-400 mb-2" />
          <p className="text-gray-600">Loading map...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full h-full rounded overflow-hidden">
      <MapContainer
        center={[selectedLocation.lat, selectedLocation.lon]}
        zoom={8}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
      >
        <MapClickHandler onLocationSelect={onLocationSelect} />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Risk circles for cells */}
        {riskData?.cells?.map((cell: any, idx: number) => (
          <Circle
            key={idx}
            center={[cell.centroid[0], cell.centroid[1]]}
            radius={5000}
            pathOptions={{
              fillColor: getRiskColor(cell.risk['6h']?.level || 'LOW'),
              fillOpacity: 0.5,
              color: getRiskColor(cell.risk['6h']?.level || 'LOW'),
              weight: 2
            }}
          >
            <Popup>
              <div className="text-sm">
                <p className="font-bold">Risk Level: {cell.risk['6h']?.level || 'N/A'}</p>
                <p>Score: {(cell.risk['6h']?.score * 100).toFixed(1)}%</p>
                <p className="text-xs text-gray-600 mt-1">
                  {cell.centroid[0].toFixed(4)}, {cell.centroid[1].toFixed(4)}
                </p>
              </div>
            </Popup>
          </Circle>
        ))}

        {/* Selected location marker */}
        <Marker position={[selectedLocation.lat, selectedLocation.lon]}>
          <Popup>
            <div className="text-sm">
              <p className="font-bold">Selected Location</p>
              <p className="text-xs">{selectedLocation.lat.toFixed(4)}, {selectedLocation.lon.toFixed(4)}</p>
            </div>
          </Popup>
        </Marker>
      </MapContainer>
    </div>
  )
}
