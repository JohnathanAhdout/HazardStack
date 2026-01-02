'use client'

import { useState, useEffect } from 'react'
import Header from '@/components/Header'
import { fetchRecentEvents, fetchRiskData } from '@/lib/api'
import { BarChart3, TrendingUp, Activity, AlertTriangle, MapPin } from 'lucide-react'

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

  const totalRiskCells = riskData?.cells?.length || 0
  const highRiskCells = riskDistribution.HIGH + riskDistribution.EXTREME

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="container mx-auto px-4 py-6">
        {/* Header Section */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Analytics Dashboard</h1>
          <p className="text-gray-600">Comprehensive statistical analysis of hazard events and risk assessments across South Asia</p>
        </div>

        {/* Info Banner */}
        <div className="bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-xl font-bold mb-2">7-Day Event Analysis</h2>
          <p className="text-purple-100 text-sm">
            Analyzing {events.length} total events including {earthquakeEvents.length} seismic events and {floodEvents.length} flood warnings.
            Risk assessment covers {totalRiskCells} geographic cells with {highRiskCells} in high-risk status.
          </p>
        </div>

        {loading && (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <Activity className="w-12 h-12 mx-auto text-blue-500 animate-spin mb-4" />
            <p className="text-gray-600 font-medium">Loading analytics data...</p>
            <p className="text-gray-500 text-sm mt-2">Aggregating event data and computing risk statistics</p>
          </div>
        )}

        {!loading && (
          <>
            {/* Enhanced Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
              <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl shadow-lg p-6 border-2 border-orange-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-orange-700 mb-1">Total Events (7d)</p>
                    <p className="text-3xl font-bold text-orange-900">{events.length}</p>
                    <p className="text-xs text-orange-600 mt-1">
                      {earthquakeEvents.length} seismic, {floodEvents.length} flood
                    </p>
                  </div>
                  <AlertTriangle className="w-10 h-10 text-orange-500" />
                </div>
              </div>

              <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl shadow-lg p-6 border-2 border-green-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-green-700 mb-1">Avg Magnitude</p>
                    <p className="text-3xl font-bold text-green-900">
                      {earthquakeEvents.length > 0 ? avgMagnitude.toFixed(2) : 'N/A'}
                    </p>
                    <p className="text-xs text-green-600 mt-1">
                      {earthquakeEvents.length > 0 ? `Based on ${earthquakeEvents.length} events` : 'No seismic data'}
                    </p>
                  </div>
                  <TrendingUp className="w-10 h-10 text-green-500" />
                </div>
              </div>

              <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl shadow-lg p-6 border-2 border-blue-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-blue-700 mb-1">Avg Depth</p>
                    <p className="text-3xl font-bold text-blue-900">
                      {earthquakeEvents.length > 0 ? `${avgDepth.toFixed(1)}` : 'N/A'}
                      <span className="text-lg ml-1">km</span>
                    </p>
                    <p className="text-xs text-blue-600 mt-1">
                      Hypocenter depth
                    </p>
                  </div>
                  <MapPin className="w-10 h-10 text-blue-500" />
                </div>
              </div>

              <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl shadow-lg p-6 border-2 border-purple-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-purple-700 mb-1">Avg Risk Score</p>
                    <p className="text-3xl font-bold text-purple-900">
                      {totalRiskCells > 0 ? `${(avgRiskScore * 100).toFixed(1)}%` : 'N/A'}
                    </p>
                    <p className="text-xs text-purple-600 mt-1">
                      Composite hazard index
                    </p>
                  </div>
                  <Activity className="w-10 h-10 text-purple-500" />
                </div>
              </div>
            </div>

            {/* Enhanced Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Magnitude Distribution */}
              <div className="bg-white rounded-xl shadow-lg p-6 border-t-4 border-blue-500">
                <h2 className="text-xl font-bold mb-2 flex items-center text-gray-900">
                  <BarChart3 className="w-6 h-6 mr-2 text-blue-500" />
                  Magnitude Distribution (7d)
                </h2>
                <p className="text-sm text-gray-600 mb-4">Distribution of seismic events by magnitude range</p>
                {earthquakeEvents.length > 0 ? (
                  <div className="space-y-4">
                    {Object.entries(magnitudeDistribution).map(([range, count]) => {
                      const percentage = earthquakeEvents.length > 0 ? ((count as number) / earthquakeEvents.length * 100).toFixed(1) : '0.0'
                      const colors: any = {
                        'M2-3': 'bg-green-500',
                        'M3-4': 'bg-blue-500',
                        'M4-5': 'bg-yellow-500',
                        'M5-6': 'bg-orange-500',
                        'M6+': 'bg-red-500',
                      }
                      return (
                        <div key={range}>
                          <div className="flex justify-between items-center text-sm mb-2">
                            <span className="font-semibold text-gray-700">{range}</span>
                            <div className="flex items-center gap-2">
                              <span className="text-gray-600">{count} events</span>
                              <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded">
                                {percentage}%
                              </span>
                            </div>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-3 shadow-inner">
                            <div
                              className={`${colors[range]} h-3 rounded-full transition-all duration-500 shadow-sm`}
                              style={{
                                width: `${earthquakeEvents.length > 0 ? (count / earthquakeEvents.length) * 100 : 0}%`
                              }}
                            />
                          </div>
                        </div>
                      )
                    })}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <BarChart3 className="w-12 h-12 mx-auto mb-2 opacity-30" />
                    <p>No seismic event data available for this period</p>
                  </div>
                )}
              </div>

              {/* Risk Level Distribution */}
              <div className="bg-white rounded-xl shadow-lg p-6 border-t-4 border-purple-500">
                <h2 className="text-xl font-bold mb-2 flex items-center text-gray-900">
                  <BarChart3 className="w-6 h-6 mr-2 text-purple-500" />
                  Risk Level Distribution
                </h2>
                <p className="text-sm text-gray-600 mb-4">Geographic cells grouped by 6-hour risk assessment level</p>
                {totalRiskCells > 0 ? (
                  <div className="space-y-4">
                    {Object.entries(riskDistribution).map(([level, count]) => {
                      const colors: any = {
                        'LOW': 'bg-green-500',
                        'MODERATE': 'bg-yellow-500',
                        'HIGH': 'bg-orange-500',
                        'EXTREME': 'bg-red-500',
                      }
                      const textColors: any = {
                        'LOW': 'text-green-700',
                        'MODERATE': 'text-yellow-700',
                        'HIGH': 'text-orange-700',
                        'EXTREME': 'text-red-700',
                      }
                      const total = Object.values(riskDistribution).reduce((a: any, b: any) => a + b, 0)
                      const percentage = total > 0 ? ((count as number) / total * 100).toFixed(1) : '0.0'

                      return (
                        <div key={level}>
                          <div className="flex justify-between items-center text-sm mb-2">
                            <span className={`font-semibold ${textColors[level]}`}>{level}</span>
                            <div className="flex items-center gap-2">
                              <span className="text-gray-600">{count} cells</span>
                              <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded">
                                {percentage}%
                              </span>
                            </div>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-3 shadow-inner">
                            <div
                              className={`${colors[level]} h-3 rounded-full transition-all duration-500 shadow-sm`}
                              style={{
                                width: `${total > 0 ? ((count as number) / total) * 100 : 0}%`
                              }}
                            />
                          </div>
                        </div>
                      )
                    })}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <Activity className="w-12 h-12 mx-auto mb-2 opacity-30" />
                    <p>No risk assessment data available</p>
                  </div>
                )}
              </div>

              {/* Event Timeline */}
              <div className="bg-white rounded-xl shadow-lg p-6 border-t-4 border-orange-500">
                <h2 className="text-xl font-bold mb-2 flex items-center text-gray-900">
                  <TrendingUp className="w-6 h-6 mr-2 text-orange-500" />
                  Recent Event Timeline
                </h2>
                <p className="text-sm text-gray-600 mb-4">Most recent seismic events (newest first)</p>
                {earthquakeEvents.length > 0 ? (
                  <div className="space-y-3 max-h-80 overflow-y-auto pr-2 custom-scrollbar">
                    {earthquakeEvents.slice(0, 10).map((event, idx) => {
                      const magnitudeColor = event.magnitude >= 5 ? 'border-red-500' : event.magnitude >= 4 ? 'border-orange-500' : 'border-blue-500'
                      return (
                        <div key={idx} className={`border-l-4 ${magnitudeColor} bg-gray-50 pl-4 py-3 rounded-r-lg hover:bg-gray-100 transition`}>
                          <div className="flex justify-between items-start mb-1">
                            <span className="font-bold text-gray-900">M {event.magnitude?.toFixed(1)}</span>
                            <span className="text-xs text-gray-500 bg-white px-2 py-1 rounded shadow-sm">
                              {event.time ? new Date(event.time).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'N/A'}
                            </span>
                          </div>
                          <p className="text-sm font-medium text-gray-700">{event.place}</p>
                          <p className="text-xs text-gray-500 mt-1">Depth: {event.depth?.toFixed(1)} km</p>
                        </div>
                      )
                    })}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <TrendingUp className="w-12 h-12 mx-auto mb-2 opacity-30" />
                    <p>No seismic events recorded in this period</p>
                  </div>
                )}
              </div>

              {/* Event Types */}
              <div className="bg-white rounded-xl shadow-lg p-6 border-t-4 border-green-500">
                <h2 className="text-xl font-bold mb-2 flex items-center text-gray-900">
                  <Activity className="w-6 h-6 mr-2 text-green-500" />
                  Event Type Breakdown
                </h2>
                <p className="text-sm text-gray-600 mb-4">Summary of all monitored hazard categories</p>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-5 bg-gradient-to-r from-blue-50 to-blue-100 rounded-xl border-2 border-blue-200 hover:shadow-md transition">
                    <div>
                      <p className="font-bold text-blue-900 text-lg">Earthquakes</p>
                      <p className="text-sm text-blue-700">Seismic events detected</p>
                    </div>
                    <div className="text-3xl font-bold text-blue-600">{earthquakeEvents.length}</div>
                  </div>
                  <div className="flex items-center justify-between p-5 bg-gradient-to-r from-cyan-50 to-cyan-100 rounded-xl border-2 border-cyan-200 hover:shadow-md transition">
                    <div>
                      <p className="font-bold text-cyan-900 text-lg">Flood Alerts</p>
                      <p className="text-sm text-cyan-700">Basin warnings issued</p>
                    </div>
                    <div className="text-3xl font-bold text-cyan-600">{floodEvents.length}</div>
                  </div>
                  <div className="flex items-center justify-between p-5 bg-gradient-to-r from-purple-50 to-purple-100 rounded-xl border-2 border-purple-200 hover:shadow-md transition">
                    <div>
                      <p className="font-bold text-purple-900 text-lg">Risk Cells Monitored</p>
                      <p className="text-sm text-purple-700">Active monitoring zones</p>
                    </div>
                    <div className="text-3xl font-bold text-purple-600">{riskData?.cells?.length || 0}</div>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
