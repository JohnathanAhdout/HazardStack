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

  const earthquakeCount = events.filter(e => e.type === 'earthquake').length
  const floodCount = events.filter(e => e.type === 'flood').length
  const avgMagnitude = earthquakeCount > 0
    ? events.filter(e => e.type === 'earthquake').reduce((sum, e) => sum + (e.magnitude || 0), 0) / earthquakeCount
    : 0
  const significantEvents = events.filter(e => e.type === 'earthquake' && e.magnitude >= 5.0).length

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="container mx-auto px-4 py-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Recent Alerts & Events</h1>
          <p className="text-gray-600">Real-time monitoring of seismic activity and flood warnings</p>
        </div>

        {/* Summary Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Events</p>
                <p className="text-2xl font-bold text-gray-900">{events.length}</p>
              </div>
              <AlertCircle className="w-8 h-8 text-blue-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Earthquakes</p>
                <p className="text-2xl font-bold text-orange-600">{earthquakeCount}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-orange-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg Magnitude</p>
                <p className="text-2xl font-bold text-yellow-600">{avgMagnitude > 0 ? avgMagnitude.toFixed(1) : 'N/A'}</p>
              </div>
              <MapPin className="w-8 h-8 text-yellow-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Significant (M5.0+)</p>
                <p className="text-2xl font-bold text-red-600">{significantEvents}</p>
              </div>
              <AlertCircle className="w-8 h-8 text-red-500" />
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex gap-4 flex-wrap items-end">
            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Clock className="w-4 h-4 inline mr-1" />
                Time Range
              </label>
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-black focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={6}>Last 6 hours</option>
                <option value={12}>Last 12 hours</option>
                <option value={24}>Last 24 hours</option>
                <option value={48}>Last 48 hours</option>
                <option value={168}>Last week</option>
              </select>
            </div>

            <div className="flex-1 min-w-[200px]">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <TrendingUp className="w-4 h-4 inline mr-1" />
                Minimum Magnitude
              </label>
              <select
                value={minMagnitude}
                onChange={(e) => setMinMagnitude(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-black focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={2.0}>2.0+ (Minor)</option>
                <option value={3.0}>3.0+ (Light)</option>
                <option value={4.0}>4.0+ (Moderate)</option>
                <option value={5.0}>5.0+ (Strong)</option>
                <option value={6.0}>6.0+ (Major)</option>
              </select>
            </div>

            <button
              onClick={loadEvents}
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {loading ? 'Loading...' : 'Refresh'}
            </button>
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
    if (mag >= 5) return 'bg-yellow-600 text-white border-yellow-700'
    if (mag >= 4) return 'bg-yellow-500 text-white border-yellow-600'
    return 'bg-green-600 text-white border-green-700'
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
    if (level === 'MODERATE') return 'bg-yellow-600 text-white border-yellow-700'
    return 'bg-green-600 text-white border-green-700'
  }

  if (event.type === 'flood') {
    return (
      <div
        onClick={onClick}
        className={`border-2 rounded-lg p-4 hover:shadow-lg transition-all cursor-pointer ${
          isSelected ? 'border-blue-500 bg-blue-50 shadow-md' : 'border-gray-200 hover:border-gray-300'
        }`}
      >
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className={`px-3 py-1 rounded-md font-bold text-sm border ${getRiskLevelColor(event.risk_level)}`}>
              {event.risk_level}
            </div>
            <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded">FLOOD</span>
          </div>
          <Clock className="w-4 h-4 text-gray-400" />
        </div>
        <h4 className="font-bold text-base mb-2 text-gray-900">{event.basin}</h4>
        <p className="text-sm text-gray-700 leading-relaxed">{event.message}</p>
        <div className="mt-3 text-xs text-gray-500">
          {event.time ? formatDistanceToNow(new Date(event.time), { addSuffix: true }) : 'Unknown time'}
        </div>
      </div>
    )
  }

  return (
    <div
      onClick={onClick}
      className={`border-2 rounded-lg p-4 hover:shadow-lg transition-all cursor-pointer ${
        isSelected ? 'border-blue-500 bg-blue-50 shadow-md' : 'border-gray-200 hover:border-gray-300'
      }`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className={`px-3 py-1 rounded-md font-bold text-sm border ${getMagnitudeColor(event.magnitude)}`}>
            M{event.magnitude?.toFixed(1)}
          </div>
          <span className="px-2 py-1 bg-orange-100 text-orange-800 text-xs font-semibold rounded">
            {getMagnitudeLabel(event.magnitude)}
          </span>
        </div>
        <Clock className="w-4 h-4 text-gray-400" />
      </div>
      <h4 className="font-bold text-base mb-2 text-gray-900">{event.place}</h4>
      <div className="grid grid-cols-2 gap-2 text-sm mb-2">
        <div>
          <span className="text-gray-500 text-xs">Depth:</span>
          <span className="font-semibold ml-1 text-gray-900">{event.depth?.toFixed(1)} km</span>
        </div>
        <div>
          <span className="text-gray-500 text-xs">Source:</span>
          <span className="font-semibold ml-1 text-gray-900">{event.source || 'N/A'}</span>
        </div>
      </div>
      <div className="text-xs text-gray-500 mt-3">
        {event.time ? formatDistanceToNow(new Date(event.time), { addSuffix: true }) : 'Unknown time'}
      </div>
    </div>
  )
}

function EarthquakeDetails({ event, details }: any) {
  const getMagnitudeColor = (mag: number) => {
    if (mag >= 7) return 'bg-red-600 text-white'
    if (mag >= 6) return 'bg-orange-600 text-white'
    if (mag >= 5) return 'bg-yellow-600 text-white'
    if (mag >= 4) return 'bg-yellow-500 text-white'
    return 'bg-green-600 text-white'
  }

  return (
    <div className="space-y-5">
      <div>
        <div className="flex items-center gap-3 mb-4">
          <div className={`px-4 py-2 rounded-lg font-bold text-lg ${getMagnitudeColor(event.magnitude)}`}>
            M{event.magnitude?.toFixed(1)}
          </div>
          <h3 className="font-bold text-xl text-gray-900">{event.place}</h3>
        </div>

        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <h4 className="font-semibold text-sm text-gray-700 mb-3">Event Information</h4>
          <div className="grid grid-cols-2 gap-x-4 gap-y-3">
            <div className="flex flex-col">
              <span className="text-xs text-gray-500 uppercase tracking-wide">Magnitude</span>
              <span className="font-bold text-base text-gray-900">{event.magnitude?.toFixed(1)}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-xs text-gray-500 uppercase tracking-wide">Depth</span>
              <span className="font-bold text-base text-gray-900">{event.depth?.toFixed(1)} km</span>
            </div>
            <div className="flex flex-col">
              <span className="text-xs text-gray-500 uppercase tracking-wide">Latitude</span>
              <span className="font-mono text-sm text-gray-900">{event.coordinates?.[1]?.toFixed(4)}°</span>
            </div>
            <div className="flex flex-col">
              <span className="text-xs text-gray-500 uppercase tracking-wide">Longitude</span>
              <span className="font-mono text-sm text-gray-900">{event.coordinates?.[0]?.toFixed(4)}°</span>
            </div>
            <div className="flex flex-col">
              <span className="text-xs text-gray-500 uppercase tracking-wide">Source</span>
              <span className="font-semibold text-sm text-gray-900">{event.source || 'N/A'}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-xs text-gray-500 uppercase tracking-wide">Time</span>
              <span className="font-semibold text-sm text-gray-900">
                {event.time ? formatDistanceToNow(new Date(event.time), { addSuffix: true }) : 'N/A'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {details?.aftershock_forecast && (
        <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border-l-4 border-orange-500 rounded-lg p-4">
          <h4 className="font-bold text-base mb-3 flex items-center text-gray-900">
            <TrendingUp className="w-5 h-5 mr-2 text-orange-600" />
            Aftershock Forecast (Next 24h)
          </h4>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Probability</span>
              <div className="flex items-center gap-2">
                <div className="bg-white rounded-full px-3 py-1 border border-orange-300">
                  <span className="font-bold text-orange-700">
                    {(details.aftershock_forecast.probability_24h * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">Expected Count</span>
              <div className="bg-white rounded-full px-3 py-1 border border-orange-300">
                <span className="font-bold text-orange-700">
                  ~{details.aftershock_forecast.expected_count_24h}
                </span>
              </div>
            </div>
            {details.aftershock_forecast.magnitude_range && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-700">Expected Magnitude Range</span>
                <div className="bg-white rounded-full px-3 py-1 border border-orange-300">
                  <span className="font-bold text-orange-700">
                    M{details.aftershock_forecast.magnitude_range[0].toFixed(1)} - M{details.aftershock_forecast.magnitude_range[1].toFixed(1)}
                  </span>
                </div>
              </div>
            )}
            <p className="text-xs text-gray-600 italic mt-2 pt-2 border-t border-orange-200">
              {details.aftershock_forecast.note}
            </p>
          </div>
        </div>
      )}

      {details?.impact_assessment && (
        <div className="bg-blue-50 border-l-4 border-blue-500 rounded-lg p-4">
          <h4 className="font-bold text-base mb-3 text-gray-900">Impact Assessment</h4>
          <div className="space-y-2">
            {details.impact_assessment.alert_level && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-700">Alert Level</span>
                <span className="font-bold text-sm uppercase px-3 py-1 bg-white rounded border border-blue-300 text-blue-700">
                  {details.impact_assessment.alert_level}
                </span>
              </div>
            )}
            {details.impact_assessment.felt_reports && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-700">Felt Reports</span>
                <span className="font-bold text-sm px-3 py-1 bg-white rounded border border-blue-300 text-blue-700">
                  {details.impact_assessment.felt_reports}
                </span>
              </div>
            )}
            {details.impact_assessment.intensity && (
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-700">Intensity (MMI)</span>
                <span className="font-bold text-sm px-3 py-1 bg-white rounded border border-blue-300 text-blue-700">
                  {details.impact_assessment.intensity}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function FloodDetails({ event }: any) {
  const getRiskColor = (level: string) => {
    if (level === 'EXTREME') return 'bg-red-600 text-white'
    if (level === 'HIGH') return 'bg-orange-600 text-white'
    if (level === 'MODERATE') return 'bg-yellow-600 text-white'
    return 'bg-green-600 text-white'
  }

  return (
    <div className="space-y-5">
      <div>
        <div className="flex items-center gap-3 mb-4">
          <div className={`px-4 py-2 rounded-lg font-bold text-base ${getRiskColor(event.risk_level)}`}>
            {event.risk_level}
          </div>
          <h3 className="font-bold text-xl text-gray-900">{event.basin}</h3>
        </div>

        <div className="bg-gradient-to-r from-blue-50 to-cyan-50 border-l-4 border-blue-500 rounded-lg p-4">
          <h4 className="font-bold text-base mb-3 text-gray-900">Flood Alert Details</h4>
          <p className="text-sm text-gray-700 leading-relaxed mb-4">{event.message}</p>

          <div className="grid grid-cols-2 gap-3 bg-white rounded-lg p-3 border border-blue-200">
            <div className="flex flex-col">
              <span className="text-xs text-gray-500 uppercase tracking-wide">Risk Level</span>
              <span className="font-bold text-base text-gray-900">{event.risk_level}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-xs text-gray-500 uppercase tracking-wide">Basin</span>
              <span className="font-semibold text-base text-gray-900">{event.basin}</span>
            </div>
            <div className="flex flex-col col-span-2">
              <span className="text-xs text-gray-500 uppercase tracking-wide">Issued</span>
              <span className="font-semibold text-sm text-gray-900">
                {event.time ? formatDistanceToNow(new Date(event.time), { addSuffix: true }) : 'N/A'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
