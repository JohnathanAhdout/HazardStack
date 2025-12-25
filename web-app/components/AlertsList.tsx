'use client'

import { AlertCircle, MapPin, Clock } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

interface AlertsListProps {
  events: any[]
}

export default function AlertsList({ events }: AlertsListProps) {
  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
        <AlertCircle className="w-5 h-5 mr-2 text-red-500" />
        Recent Events
      </h2>

      <div className="space-y-3 max-h-96 overflow-y-auto">
        {events.length === 0 ? (
          <p className="text-gray-500 text-sm text-center py-4">No recent events</p>
        ) : (
          events.map((event, idx) => (
            <EventCard key={idx} event={event} />
          ))
        )}
      </div>
    </div>
  )
}

function EventCard({ event }: { event: any }) {
  const getMagnitudeColor = (mag: number) => {
    if (mag >= 7) return 'text-red-700 bg-red-50'
    if (mag >= 6) return 'text-orange-700 bg-orange-50'
    if (mag >= 5) return 'text-yellow-700 bg-yellow-50'
    return 'text-green-700 bg-green-50'
  }

  const getRiskLevelColor = (level: string) => {
    if (level === 'EXTREME' || level === 'HIGH') return 'text-red-700 bg-red-50'
    if (level === 'MODERATE') return 'text-yellow-700 bg-yellow-50'
    return 'text-green-700 bg-green-50'
  }

  // Handle flood events
  if (event.type === 'flood') {
    return (
      <div className="border border-gray-200 rounded-lg p-3 hover:shadow-md transition">
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center space-x-2">
            <div className={`px-2 py-1 rounded font-bold text-sm ${getRiskLevelColor(event.risk_level)}`}>
              {event.risk_level}
            </div>
            <span className="text-sm font-semibold text-gray-700">
              {event.basin || 'Flood Alert'}
            </span>
          </div>
        </div>
        <div className="space-y-1 text-xs text-gray-600">
          <p>{event.message}</p>
          <div className="flex items-center">
            <Clock className="w-3 h-3 mr-1" />
            <span>
              {event.time ? formatDistanceToNow(new Date(event.time), { addSuffix: true }) : 'Unknown time'}
            </span>
          </div>
        </div>
      </div>
    )
  }

  // Handle earthquake events
  return (
    <div className="border border-gray-200 rounded-lg p-3 hover:shadow-md transition">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center space-x-2">
          <div className={`px-2 py-1 rounded font-bold text-sm ${getMagnitudeColor(event.magnitude)}`}>
            M {event.magnitude?.toFixed(1) || 'N/A'}
          </div>
          <span className="text-sm font-semibold text-gray-700">
            {event.place || 'Unknown Location'}
          </span>
        </div>
      </div>

      <div className="space-y-1 text-xs text-gray-600">
        <div className="flex items-center">
          <MapPin className="w-3 h-3 mr-1" />
          <span>
            {event.coordinates?.[1]?.toFixed(2)}°N, {event.coordinates?.[0]?.toFixed(2)}°E
          </span>
          <span className="mx-2">•</span>
          <span>Depth: {event.depth?.toFixed(1)} km</span>
        </div>

        <div className="flex items-center">
          <Clock className="w-3 h-3 mr-1" />
          <span>
            {event.time ? formatDistanceToNow(new Date(event.time), { addSuffix: true }) : 'Unknown time'}
          </span>
          {event.source && (
            <>
              <span className="mx-2">•</span>
              <span>Source: {event.source}</span>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
