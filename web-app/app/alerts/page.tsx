'use client'

import { useState, useEffect } from 'react'
import Header from '@/components/Header'
import { fetchRecentEvents, fetchEventDetails } from '@/lib/api'
import { AlertCircle, MapPin, Clock, TrendingUp } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

export default function Alerts() {
  const [events, setEvents] = useState<any[]>([])
  const [selectedEvent, setSelectedEvent] = useState<any>(null)
  const [eventDetails, setEventDetails] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [timeRange, setTimeRange] = useState(24)
  const [minMagnitude, setMinMagnitude] = useState(3.0)

  useEffect(() => {
    loadEvents()
  }, [timeRange, minMagnitude])

  const loadEvents = async () => {
    setLoading(true)
    try {
      const data = await fetchRecentEvents(timeRange, minMagnitude)
      setEvents(data)
    } catch (error) {
      console.error('Error fetching events:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleEventClick = async (event: any) => {
    setSelectedEvent(event)
    if (event.event_id) {
      const details = await fetchEventDetails(event.event_id)
      setEventDetails(details)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="container mx-auto px-4 py-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Recent Alerts & Events</h1>
          <p className="text-gray-600">Real-time monitoring of seismic activity and flood warnings</p>
        </div>

        {/* Info Banner */}
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-xl font-bold mb-2">Live Hazard Event Monitoring</h2>
          <p className="text-blue-100 text-sm">
            Real-time tracking of seismic events from USGS and flood warnings from basin monitoring systems.
            Events are automatically updated and filtered by severity and time range.
          </p>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <AlertCircle className="w-5 h-5 mr-2 text-blue-500" />
            Filter Events
          </h3>
          <div className="flex gap-4 flex-wrap items-end">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Time Range
                <span className="text-xs text-gray-500 ml-2">({events.length} events found)</span>
              </label>
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(Number(e.target.value))}
                className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg text-black font-medium hover:border-blue-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition"
              >
                <option value={6}>Last 6 hours</option>
                <option value={12}>Last 12 hours</option>
                <option value={24}>Last 24 hours</option>
                <option value={48}>Last 48 hours</option>
                <option value={168}>Last 7 days</option>
              </select>
            </div>

            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Minimum Magnitude
                <span className="text-xs text-gray-500 ml-2">(seismic events only)</span>
              </label>
              <select
                value={minMagnitude}
                onChange={(e) => setMinMagnitude(Number(e.target.value))}
                className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg text-black font-medium hover:border-blue-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition"
              >
                <option value={2.0}>2.0+ (All recorded events)</option>
                <option value={3.0}>3.0+ (Light earthquakes)</option>
                <option value={4.0}>4.0+ (Moderate earthquakes)</option>
                <option value={5.0}>5.0+ (Strong earthquakes)</option>
                <option value={6.0}>6.0+ (Major earthquakes)</option>
              </select>
            </div>

            <div className="flex gap-2">
              <button
                onClick={loadEvents}
                className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium shadow-md hover:shadow-lg transition flex items-center gap-2"
              >
                <AlertCircle className="w-4 h-4" />
                Refresh Data
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Events List */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4 flex items-center">
              <AlertCircle className="w-5 h-5 mr-2 text-red-500" />
              Events ({events.length})
            </h2>

            <div className="space-y-3 max-h-[700px] overflow-y-auto">
              {loading ? (
                <p className="text-gray-500 text-center py-8">Loading events...</p>
              ) : events.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No events found</p>
              ) : (
                events.map((event, idx) => (
                  <EventCard
                    key={idx}
                    event={event}
                    onClick={() => handleEventClick(event)}
                    isSelected={selectedEvent === event}
                  />
                ))
              )}
            </div>
          </div>

          {/* Event Details */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Event Details</h2>

            {!selectedEvent ? (
              <p className="text-gray-500 text-center py-8">Select an event to view details</p>
            ) : (
              <div className="space-y-4">
                {selectedEvent.type === 'earthquake' ? (
                  <EarthquakeDetails event={selectedEvent} details={eventDetails} />
                ) : (
                  <FloodDetails event={selectedEvent} />
                )}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

function EventCard({ event, onClick, isSelected }: any) {
  const getMagnitudeColor = (mag: number) => {
    if (mag >= 7) return 'bg-red-600 text-white border-red-700'
    if (mag >= 6) return 'bg-orange-600 text-white border-orange-700'
    if (mag >= 5) return 'bg-yellow-500 text-white border-yellow-600'
    if (mag >= 4) return 'bg-blue-500 text-white border-blue-600'
    return 'bg-green-500 text-white border-green-600'
  }

  const getMagnitudeLabel = (mag: number) => {
    if (mag >= 7) return 'Major'
    if (mag >= 6) return 'Strong'
    if (mag >= 5) return 'Moderate'
    if (mag >= 4) return 'Light'
    return 'Minor'
  }

  const getRiskLevelColor = (level: string) => {
    if (level === 'EXTREME') return 'bg-red-600 text-white border-red-700'
    if (level === 'HIGH') return 'bg-orange-600 text-white border-orange-700'
    if (level === 'MODERATE') return 'bg-yellow-500 text-white border-yellow-600'
    return 'bg-green-500 text-white border-green-600'
  }

  if (event.type === 'flood') {
    return (
      <div
        onClick={onClick}
        className={`border-2 rounded-xl p-4 hover:shadow-xl transition-all cursor-pointer ${
          isSelected ? 'border-blue-500 bg-blue-50 shadow-lg' : 'border-gray-200 bg-white hover:border-blue-300'
        }`}
      >
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className={`px-3 py-1.5 rounded-lg font-bold text-sm shadow-sm border-2 ${getRiskLevelColor(event.risk_level)}`}>
              {event.risk_level}
            </div>
          </div>
          <div className="bg-blue-100 text-blue-700 px-2 py-1 rounded-md text-xs font-semibold">
            FLOOD WARNING
          </div>
        </div>
        <h4 className="font-bold text-gray-900 mb-2 text-base">{event.basin}</h4>
        <p className="text-sm text-gray-700 leading-relaxed">{event.message}</p>
      </div>
    )
  }

  return (
    <div
      onClick={onClick}
      className={`border-2 rounded-xl p-4 hover:shadow-xl transition-all cursor-pointer ${
        isSelected ? 'border-blue-500 bg-blue-50 shadow-lg' : 'border-gray-200 bg-white hover:border-blue-300'
      }`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className={`px-3 py-1.5 rounded-lg font-bold text-sm shadow-sm border-2 ${getMagnitudeColor(event.magnitude)}`}>
            M {event.magnitude?.toFixed(1)}
          </div>
          <span className="text-xs font-semibold text-gray-600 bg-gray-100 px-2 py-1 rounded">
            {getMagnitudeLabel(event.magnitude)}
          </span>
        </div>
        <div className="bg-orange-100 text-orange-700 px-2 py-1 rounded-md text-xs font-semibold">
          EARTHQUAKE
        </div>
      </div>
      <h4 className="font-bold text-gray-900 mb-2 text-base">{event.place}</h4>
      <div className="flex items-center gap-3 text-sm text-gray-600">
        <div className="flex items-center gap-1">
          <Clock className="w-4 h-4" />
          <span>{event.time ? formatDistanceToNow(new Date(event.time), { addSuffix: true }) : 'Unknown'}</span>
        </div>
        {event.depth && (
          <div className="flex items-center gap-1">
            <MapPin className="w-4 h-4" />
            <span>{event.depth.toFixed(1)} km depth</span>
          </div>
        )}
      </div>
    </div>
  )
}

function EarthquakeDetails({ event, details }: any) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="font-bold text-lg mb-2">{event.place}</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Magnitude:</span>
            <span className="font-semibold ml-2">{event.magnitude?.toFixed(1)}</span>
          </div>
          <div>
            <span className="text-gray-600">Depth:</span>
            <span className="font-semibold ml-2">{event.depth?.toFixed(1)} km</span>
          </div>
          <div>
            <span className="text-gray-600">Latitude:</span>
            <span className="font-semibold ml-2">{event.coordinates?.[1]?.toFixed(4)}°</span>
          </div>
          <div>
            <span className="text-gray-600">Longitude:</span>
            <span className="font-semibold ml-2">{event.coordinates?.[0]?.toFixed(4)}°</span>
          </div>
          <div>
            <span className="text-gray-600">Source:</span>
            <span className="font-semibold ml-2">{event.source || 'N/A'}</span>
          </div>
          <div>
            <span className="text-gray-600">Time:</span>
            <span className="font-semibold ml-2">
              {event.time ? formatDistanceToNow(new Date(event.time), { addSuffix: true }) : 'N/A'}
            </span>
          </div>
        </div>
      </div>

      {details?.aftershock_forecast && (
        <div className="border-t pt-4">
          <h4 className="font-bold mb-2 flex items-center">
            <TrendingUp className="w-4 h-4 mr-2" />
            Aftershock Forecast
          </h4>
          <div className="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm">
            <p className="mb-2">
              <span className="font-semibold">24h Probability:</span>{' '}
              {(details.aftershock_forecast.probability_24h * 100).toFixed(0)}%
            </p>
            <p className="mb-2">
              <span className="font-semibold">Expected Count:</span>{' '}
              ~{details.aftershock_forecast.expected_count_24h} aftershocks
            </p>
            <p className="text-xs text-gray-600">{details.aftershock_forecast.note}</p>
          </div>
        </div>
      )}

      {details?.impact_assessment && (
        <div className="border-t pt-4">
          <h4 className="font-bold mb-2">Impact Assessment</h4>
          <div className="space-y-2 text-sm">
            {details.impact_assessment.alert_level && (
              <div>
                <span className="text-gray-600">Alert Level:</span>
                <span className="font-semibold ml-2 uppercase">{details.impact_assessment.alert_level}</span>
              </div>
            )}
            {details.impact_assessment.felt_reports && (
              <div>
                <span className="text-gray-600">Felt Reports:</span>
                <span className="font-semibold ml-2">{details.impact_assessment.felt_reports}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function FloodDetails({ event }: any) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="font-bold text-lg mb-2">{event.basin}</h3>
        <div className="bg-blue-50 border border-blue-200 rounded p-4">
          <div className="mb-3">
            <span className="text-sm text-gray-600">Risk Level:</span>
            <span className={`ml-2 px-2 py-1 rounded font-bold text-sm ${
              event.risk_level === 'HIGH' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'
            }`}>
              {event.risk_level}
            </span>
          </div>
          <p className="text-sm">{event.message}</p>
        </div>
      </div>
    </div>
  )
}
