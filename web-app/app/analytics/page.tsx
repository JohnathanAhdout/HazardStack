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

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="container mx-auto px-4 py-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Analytics Dashboard</h1>
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
            {/* Summary Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Total Events (7d)</p>
                    <p className="text-2xl font-bold text-gray-900">{events.length}</p>
                  </div>
                  <AlertTriangle className="w-8 h-8 text-orange-500" />
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Avg Magnitude</p>
                    <p className="text-2xl font-bold text-gray-900">{avgMagnitude.toFixed(2)}</p>
                  </div>
                  <TrendingUp className="w-8 h-8 text-green-500" />
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Avg Depth</p>
                    <p className="text-2xl font-bold text-gray-900">{avgDepth.toFixed(1)} km</p>
                  </div>
                  <MapPin className="w-8 h-8 text-blue-500" />
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Avg Risk Score</p>
                    <p className="text-2xl font-bold text-gray-900">{(avgRiskScore * 100).toFixed(1)}%</p>
                  </div>
                  <Activity className="w-8 h-8 text-purple-500" />
                </div>
              </div>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Magnitude Distribution */}
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                  <BarChart3 className="w-5 h-5 mr-2" />
                  Magnitude Distribution (7d)
                </h2>
                <div className="space-y-3">
                  {Object.entries(magnitudeDistribution).map(([range, count]) => (
                    <div key={range}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="font-medium text-gray-900">{range}</span>
                        <span className="text-gray-600">{count} events</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{
                            width: `${earthquakeEvents.length > 0 ? (count / earthquakeEvents.length) * 100 : 0}%`
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Risk Level Distribution */}
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                  <BarChart3 className="w-5 h-5 mr-2" />
                  Risk Level Distribution
                </h2>
                <div className="space-y-3">
                  {Object.entries(riskDistribution).map(([level, count]) => {
                    const colors: any = {
                      'LOW': 'bg-green-500',
                      'MODERATE': 'bg-yellow-500',
                      'HIGH': 'bg-orange-500',
                      'EXTREME': 'bg-red-500',
                    }
                    const total = Object.values(riskDistribution).reduce((a: any, b: any) => a + b, 0)

                    return (
                      <div key={level}>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="font-medium text-gray-900">{level}</span>
                          <span className="text-gray-600">{count} cells</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={`${colors[level]} h-2 rounded-full`}
                            style={{
                              width: `${total > 0 ? ((count as number) / total) * 100 : 0}%`
                            }}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Event Timeline */}
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Event Timeline</h2>
                <div className="space-y-3 max-h-80 overflow-y-auto">
                  {earthquakeEvents.slice(0, 10).map((event, idx) => (
                    <div key={idx} className="border-l-4 border-blue-500 pl-4 py-2">
                      <div className="flex justify-between">
                        <span className="font-semibold text-gray-900">M {event.magnitude?.toFixed(1)}</span>
                        <span className="text-xs text-gray-500">
                          {event.time ? new Date(event.time).toLocaleDateString() : 'N/A'}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600">{event.place}</p>
                      <p className="text-xs text-gray-500">Depth: {event.depth?.toFixed(1)} km</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Event Types */}
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">Event Type Breakdown</h2>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
                    <div>
                      <p className="font-semibold text-gray-900">Earthquakes</p>
                      <p className="text-sm text-gray-600">Seismic events detected</p>
                    </div>
                    <div className="text-2xl font-bold text-blue-600">{earthquakeEvents.length}</div>
                  </div>
                  <div className="flex items-center justify-between p-4 bg-cyan-50 rounded-lg">
                    <div>
                      <p className="font-semibold text-gray-900">Flood Alerts</p>
                      <p className="text-sm text-gray-600">Basin warnings issued</p>
                    </div>
                    <div className="text-2xl font-bold text-cyan-600">{floodEvents.length}</div>
                  </div>
                  <div className="flex items-center justify-between p-4 bg-purple-50 rounded-lg">
                    <div>
                      <p className="font-semibold text-gray-900">Risk Cells Monitored</p>
                      <p className="text-sm text-gray-600">Active monitoring zones</p>
                    </div>
                    <div className="text-2xl font-bold text-purple-600">{riskData?.cells?.length || 0}</div>
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
