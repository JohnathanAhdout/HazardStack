'use client'

import { useState, useEffect } from 'react'
import Header from '@/components/Header'
import { fetchRecentEvents, fetchRiskData } from '@/lib/api'
import { BarChart3, TrendingUp, Activity, AlertTriangle, MapPin, TrendingDown, Minus, Info } from 'lucide-react'

export default function Analytics() {
  const [events, setEvents] = useState<any[]>([])
  const [riskData, setRiskData] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [eventsData, risk] = await Promise.all([
        fetchRecentEvents(168, 2.0), // Last week, mag 2.0+
        fetchRiskData(20.5, 78.9, 50, ['6h']) // Central India, wider area
      ])
      setEvents(eventsData)
      setRiskData(risk)
    } catch (error) {
      console.error('Error loading analytics data:', error)
    } finally {
      setLoading(false)
    }
  }

  // Calculate analytics
  const earthquakeEvents = events.filter(e => e.type === 'earthquake')
  const floodEvents = events.filter(e => e.type === 'flood')

  const magnitudeDistribution = {
    'M2-3': earthquakeEvents.filter(e => e.magnitude >= 2 && e.magnitude < 3).length,
    'M3-4': earthquakeEvents.filter(e => e.magnitude >= 3 && e.magnitude < 4).length,
    'M4-5': earthquakeEvents.filter(e => e.magnitude >= 4 && e.magnitude < 5).length,
    'M5-6': earthquakeEvents.filter(e => e.magnitude >= 5 && e.magnitude < 6).length,
    'M6+': earthquakeEvents.filter(e => e.magnitude >= 6).length,
  }

  const depthDistribution = {
    'Shallow (0-70km)': earthquakeEvents.filter(e => e.depth >= 0 && e.depth < 70).length,
    'Intermediate (70-300km)': earthquakeEvents.filter(e => e.depth >= 70 && e.depth < 300).length,
    'Deep (300km+)': earthquakeEvents.filter(e => e.depth >= 300).length,
  }

  const riskDistribution = {
    'LOW': riskData?.cells?.filter((c: any) => c.risk['6h']?.level === 'LOW').length || 0,
    'MODERATE': riskData?.cells?.filter((c: any) => c.risk['6h']?.level === 'MODERATE').length || 0,
    'HIGH': riskData?.cells?.filter((c: any) => c.risk['6h']?.level === 'HIGH').length || 0,
    'EXTREME': riskData?.cells?.filter((c: any) => c.risk['6h']?.level === 'EXTREME').length || 0,
  }

  const avgMagnitude = earthquakeEvents.length > 0
    ? earthquakeEvents.reduce((sum, e) => sum + e.magnitude, 0) / earthquakeEvents.length
    : 0

  const avgDepth = earthquakeEvents.length > 0
    ? earthquakeEvents.reduce((sum, e) => sum + e.depth, 0) / earthquakeEvents.length
    : 0

  const avgRiskScore = riskData?.cells?.length > 0
    ? riskData.cells.reduce((sum: number, c: any) => sum + (c.risk['6h']?.score || 0), 0) / riskData.cells.length
    : 0

  const significantEvents = earthquakeEvents.filter(e => e.magnitude >= 5.0).length
  const maxMagnitude = earthquakeEvents.length > 0
    ? Math.max(...earthquakeEvents.map(e => e.magnitude))
    : 0

  const avgMMI = riskData?.cells?.length > 0
    ? riskData.cells.reduce((sum: number, c: any) => sum + (c.components?.mmi_mean || 0), 0) / riskData.cells.length
    : 0

  const highRiskCells = riskData?.cells?.filter((c: any) =>
    c.risk['6h']?.level === 'HIGH' || c.risk['6h']?.level === 'EXTREME'
  ).length || 0

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="container mx-auto px-4 py-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Analytics Dashboard</h1>
          <p className="text-gray-600">Statistical analysis of hazard events and risk assessments</p>
        </div>

        {loading && (
          <div className="text-center py-12">
            <Activity className="w-12 h-12 mx-auto text-blue-500 animate-spin mb-4" />
            <p className="text-gray-600">Loading analytics data...</p>
          </div>
        )}

        {!loading && (
          <>
            {/* Summary Cards - Enhanced */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg shadow-md p-5 border border-orange-200">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <p className="text-xs font-medium text-orange-700 uppercase tracking-wide">Total Events</p>
                    <p className="text-sm text-orange-600">Last 7 days</p>
                  </div>
                  <AlertTriangle className="w-10 h-10 text-orange-500 opacity-80" />
                </div>
                <p className="text-4xl font-bold text-orange-900">{events.length}</p>
                <div className="mt-2 text-xs text-orange-600">
                  {earthquakeEvents.length} earthquakes · {floodEvents.length} floods
                </div>
              </div>

              <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-lg shadow-md p-5 border border-yellow-200">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <p className="text-xs font-medium text-yellow-700 uppercase tracking-wide">Avg Magnitude</p>
                    <p className="text-sm text-yellow-600">Earthquake events</p>
                  </div>
                  <TrendingUp className="w-10 h-10 text-yellow-500 opacity-80" />
                </div>
                <p className="text-4xl font-bold text-yellow-900">{avgMagnitude > 0 ? avgMagnitude.toFixed(1) : 'N/A'}</p>
                <div className="mt-2 text-xs text-yellow-600">
                  Max: M{maxMagnitude.toFixed(1)} · {significantEvents} significant (M5.0+)
                </div>
              </div>

              <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg shadow-md p-5 border border-blue-200">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <p className="text-xs font-medium text-blue-700 uppercase tracking-wide">Avg Depth</p>
                    <p className="text-sm text-blue-600">Hypocenter depth</p>
                  </div>
                  <MapPin className="w-10 h-10 text-blue-500 opacity-80" />
                </div>
                <p className="text-4xl font-bold text-blue-900">{avgDepth > 0 ? avgDepth.toFixed(0) : 'N/A'}</p>
                <div className="mt-2 text-xs text-blue-600">
                  {avgDepth > 0 ? (avgDepth < 70 ? 'Shallow focus' : avgDepth < 300 ? 'Intermediate' : 'Deep focus') : 'No data'} earthquakes
                </div>
              </div>

              <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg shadow-md p-5 border border-purple-200">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <p className="text-xs font-medium text-purple-700 uppercase tracking-wide">Avg Risk Score</p>
                    <p className="text-sm text-purple-600">6-hour forecast</p>
                  </div>
                  <Activity className="w-10 h-10 text-purple-500 opacity-80" />
                </div>
                <p className="text-4xl font-bold text-purple-900">{(avgRiskScore * 100).toFixed(0)}%</p>
                <div className="mt-2 text-xs text-purple-600">
                  {highRiskCells} cells in HIGH/EXTREME zones
                </div>
              </div>
            </div>

            {/* Additional Insights Row */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
              <div className="bg-white rounded-lg shadow p-4 border-l-4 border-green-500">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-600 uppercase tracking-wide">Avg Shaking Intensity</p>
                    <p className="text-2xl font-bold text-gray-900">MMI {avgMMI.toFixed(1)}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {avgMMI < 2 ? 'Not felt' : avgMMI < 3 ? 'Weak' : avgMMI < 4 ? 'Light' : avgMMI < 5 ? 'Moderate' : 'Strong'}
                    </p>
                  </div>
                  <Activity className="w-8 h-8 text-green-500" />
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-4 border-l-4 border-red-500">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-600 uppercase tracking-wide">Significant Events</p>
                    <p className="text-2xl font-bold text-gray-900">{significantEvents}</p>
                    <p className="text-xs text-gray-500 mt-1">Magnitude 5.0 or higher</p>
                  </div>
                  <AlertTriangle className="w-8 h-8 text-red-500" />
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-600 uppercase tracking-wide">Monitored Cells</p>
                    <p className="text-2xl font-bold text-gray-900">{riskData?.cells?.length || 0}</p>
                    <p className="text-xs text-gray-500 mt-1">Active risk zones (H3)</p>
                  </div>
                  <MapPin className="w-8 h-8 text-blue-500" />
                </div>
              </div>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Magnitude Distribution */}
              <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
                <div className="flex items-center justify-between mb-5">
                  <h2 className="text-lg font-bold flex items-center text-gray-900">
                    <BarChart3 className="w-5 h-5 mr-2 text-blue-600" />
                    Magnitude Distribution
                  </h2>
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full font-semibold">
                    Last 7 days
                  </span>
                </div>
                <div className="space-y-4">
                  {Object.entries(magnitudeDistribution).map(([range, count]) => {
                    const percentage = earthquakeEvents.length > 0 ? (count / earthquakeEvents.length) * 100 : 0
                    const getBarColor = (r: string) => {
                      if (r === 'M6+') return 'bg-gradient-to-r from-red-500 to-red-600'
                      if (r === 'M5-6') return 'bg-gradient-to-r from-orange-500 to-orange-600'
                      if (r === 'M4-5') return 'bg-gradient-to-r from-yellow-500 to-yellow-600'
                      if (r === 'M3-4') return 'bg-gradient-to-r from-green-500 to-green-600'
                      return 'bg-gradient-to-r from-blue-500 to-blue-600'
                    }

                    return (
                      <div key={range} className="group">
                        <div className="flex justify-between items-center text-sm mb-2">
                          <span className="font-semibold text-gray-700">{range}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-gray-900 font-bold">{count}</span>
                            <span className="text-gray-500 text-xs">({percentage.toFixed(0)}%)</span>
                          </div>
                        </div>
                        <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
                          <div
                            className={`${getBarColor(range)} h-3 rounded-full transition-all duration-500 shadow-sm`}
                            style={{ width: `${Math.max(percentage, 2)}%` }}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
                <div className="mt-4 pt-4 border-t border-gray-200 text-xs text-gray-600 flex items-center">
                  <Info className="w-3 h-3 mr-1" />
                  Distribution based on {earthquakeEvents.length} earthquake events
                </div>
              </div>

              {/* Depth Distribution */}
              <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
                <div className="flex items-center justify-between mb-5">
                  <h2 className="text-lg font-bold flex items-center text-gray-900">
                    <MapPin className="w-5 h-5 mr-2 text-blue-600" />
                    Depth Distribution
                  </h2>
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full font-semibold">
                    Hypocenter
                  </span>
                </div>
                <div className="space-y-4">
                  {Object.entries(depthDistribution).map(([range, count]) => {
                    const percentage = earthquakeEvents.length > 0 ? (count / earthquakeEvents.length) * 100 : 0
                    const getBarColor = (r: string) => {
                      if (r.includes('Shallow')) return 'bg-gradient-to-r from-red-500 to-orange-500'
                      if (r.includes('Intermediate')) return 'bg-gradient-to-r from-yellow-500 to-green-500'
                      return 'bg-gradient-to-r from-blue-500 to-purple-500'
                    }

                    return (
                      <div key={range} className="group">
                        <div className="flex justify-between items-center text-sm mb-2">
                          <span className="font-semibold text-gray-700">{range}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-gray-900 font-bold">{count}</span>
                            <span className="text-gray-500 text-xs">({percentage.toFixed(0)}%)</span>
                          </div>
                        </div>
                        <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
                          <div
                            className={`${getBarColor(range)} h-3 rounded-full transition-all duration-500 shadow-sm`}
                            style={{ width: `${Math.max(percentage, 2)}%` }}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
                <div className="mt-4 pt-4 border-t border-gray-200 text-xs text-gray-600 flex items-center">
                  <Info className="w-3 h-3 mr-1" />
                  Shallow events typically more damaging
                </div>
              </div>

              {/* Risk Level Distribution */}
              <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
                <div className="flex items-center justify-between mb-5">
                  <h2 className="text-lg font-bold flex items-center text-gray-900">
                    <Activity className="w-5 h-5 mr-2 text-purple-600" />
                    Risk Level Distribution
                  </h2>
                  <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded-full font-semibold">
                    6h Horizon
                  </span>
                </div>
                <div className="space-y-4">
                  {Object.entries(riskDistribution).map(([level, count]) => {
                    const colors: any = {
                      'LOW': 'bg-gradient-to-r from-green-500 to-green-600',
                      'MODERATE': 'bg-gradient-to-r from-yellow-500 to-yellow-600',
                      'HIGH': 'bg-gradient-to-r from-orange-500 to-orange-600',
                      'EXTREME': 'bg-gradient-to-r from-red-500 to-red-600',
                    }
                    const total = Object.values(riskDistribution).reduce((a: any, b: any) => a + b, 0)
                    const percentage = total > 0 ? ((count as number) / total) * 100 : 0

                    return (
                      <div key={level} className="group">
                        <div className="flex justify-between items-center text-sm mb-2">
                          <span className="font-semibold text-gray-700">{level}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-gray-900 font-bold">{count}</span>
                            <span className="text-gray-500 text-xs">({percentage.toFixed(0)}%)</span>
                          </div>
                        </div>
                        <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
                          <div
                            className={`${colors[level]} h-3 rounded-full transition-all duration-500 shadow-sm`}
                            style={{ width: `${Math.max(percentage, 2)}%` }}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
                <div className="mt-4 pt-4 border-t border-gray-200 text-xs text-gray-600 flex items-center">
                  <Info className="w-3 h-3 mr-1" />
                  Risk levels calculated from real seismic data
                </div>
              </div>

              {/* Event Timeline */}
              <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200 lg:col-span-2">
                <div className="flex items-center justify-between mb-5">
                  <h2 className="text-lg font-bold flex items-center text-gray-900">
                    <TrendingUp className="w-5 h-5 mr-2 text-blue-600" />
                    Recent Event Timeline
                  </h2>
                  <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded-full font-semibold">
                    Top 10 Events
                  </span>
                </div>
                <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
                  {earthquakeEvents.length === 0 ? (
                    <p className="text-center text-gray-500 py-8">No earthquake events in the last 7 days</p>
                  ) : (
                    earthquakeEvents.slice(0, 10).map((event, idx) => {
                      const getMagColor = (mag: number) => {
                        if (mag >= 6) return 'border-red-500 bg-red-50'
                        if (mag >= 5) return 'border-orange-500 bg-orange-50'
                        if (mag >= 4) return 'border-yellow-500 bg-yellow-50'
                        return 'border-blue-500 bg-blue-50'
                      }

                      return (
                        <div key={idx} className={`border-l-4 ${getMagColor(event.magnitude)} pl-4 py-3 rounded-r-lg transition-all hover:shadow-md`}>
                          <div className="flex justify-between items-start mb-1">
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-lg text-gray-900">M{event.magnitude?.toFixed(1)}</span>
                              <span className="text-xs bg-white px-2 py-1 rounded border border-gray-300 text-gray-700">
                                #{idx + 1}
                              </span>
                            </div>
                            <span className="text-xs text-gray-600 font-medium">
                              {event.time ? new Date(event.time).toLocaleString('en-US', {
                                month: 'short',
                                day: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                              }) : 'N/A'}
                            </span>
                          </div>
                          <p className="text-sm font-medium text-gray-800 mb-1">{event.place}</p>
                          <div className="flex gap-3 text-xs text-gray-600">
                            <span>Depth: {event.depth?.toFixed(1)} km</span>
                            <span>•</span>
                            <span>Source: {event.source || 'N/A'}</span>
                          </div>
                        </div>
                      )
                    })
                  )}
                </div>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
