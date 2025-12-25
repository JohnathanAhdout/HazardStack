'use client'

import { useState, useEffect } from 'react'
import Header from '@/components/Header'
import MapView from '@/components/MapView'
import RiskPanel from '@/components/RiskPanel'
import AlertsList from '@/components/AlertsList'
import StatsOverview from '@/components/StatsOverview'
import { fetchRiskData, fetchRecentEvents } from '@/lib/api'
import { Info, HelpCircle } from 'lucide-react'

export default function Dashboard() {
  const [selectedLocation, setSelectedLocation] = useState<{lat: number, lon: number} | null>(null)
  const [riskData, setRiskData] = useState<any>(null)
  const [recentEvents, setRecentEvents] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showHelp, setShowHelp] = useState(false)

  // Default to Mumbai coordinates
  const defaultLocation = { lat: 19.07, lon: 72.88 }

  useEffect(() => {
    // Fetch initial data for default location
    loadData(defaultLocation)
    loadRecentEvents()
  }, [])

  const loadData = async (location: {lat: number, lon: number}) => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchRiskData(location.lat, location.lon, 10, ['1h', '6h', '24h'])
      setRiskData(data)
      setSelectedLocation(location)
    } catch (error) {
      console.error('Error fetching risk data:', error)
      setError('Unable to fetch risk data. Using fallback data for demonstration.')
    } finally {
      setLoading(false)
    }
  }

  const loadRecentEvents = async () => {
    try {
      const events = await fetchRecentEvents(24, 3.0)
      setRecentEvents(events)
    } catch (error) {
      console.error('Error fetching recent events:', error)
      setError('Unable to fetch recent events. Using fallback data for demonstration.')
    }
  }

  const handleLocationSelect = (lat: number, lon: number) => {
    loadData({ lat, lon })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="container mx-auto px-4 py-6">
        {/* Welcome Banner with Instructions */}
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h1 className="text-2xl font-bold mb-2">Multi-Hazard Risk Dashboard</h1>
              <p className="text-blue-100 mb-3">
                Real-time monitoring and prediction of earthquakes, floods, and extreme weather events across South Asia.
              </p>
              <div className="flex items-center gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <Info className="w-4 h-4" />
                  <span>Click anywhere on the map to view risk for that location</span>
                </div>
              </div>
            </div>
            <button
              onClick={() => setShowHelp(!showHelp)}
              className="ml-4 p-2 hover:bg-blue-400 rounded-full transition"
              title="Toggle help"
            >
              <HelpCircle className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Help Section */}
        {showHelp && (
          <div className="bg-white border-l-4 border-blue-500 rounded-lg shadow p-6 mb-6">
            <h3 className="font-bold text-lg text-gray-900 mb-3">How to Use This Dashboard</h3>
            <div className="space-y-3 text-gray-700">
              <div>
                <p className="font-semibold text-gray-900">📊 Statistics Overview (Top Cards):</p>
                <p className="text-sm">Shows real-time metrics including active monitoring zones, high-risk areas, rainfall warnings, and model confidence levels.</p>
              </div>
              <div>
                <p className="font-semibold text-gray-900">🗺️ Interactive Map (Center):</p>
                <p className="text-sm">Click anywhere on the map to select a location. Risk data will update to show predictions for that area. Color-coded circles indicate risk levels (Green=Low, Yellow=Moderate, Orange=High, Red=Extreme).</p>
              </div>
              <div>
                <p className="font-semibold text-gray-900">⚠️ Risk Panel (Right Sidebar):</p>
                <p className="text-sm">Displays detailed risk assessment for the selected location, including probability scores for rainfall, flooding, and earthquake shaking.</p>
              </div>
              <div>
                <p className="font-semibold text-gray-900">🚨 Recent Events (Bottom Right):</p>
                <p className="text-sm">Lists real earthquakes detected by USGS seismic networks and active flood warnings from monitoring agencies.</p>
              </div>
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-yellow-50 border-l-4 border-yellow-400 text-yellow-800 rounded-lg shadow p-4 mb-6">
            <div className="flex items-center">
              <Info className="w-5 h-5 mr-2" />
              <p className="text-sm">{error}</p>
            </div>
          </div>
        )}

        {/* Stats Overview */}
        <StatsOverview riskData={riskData} recentEvents={recentEvents} />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
          {/* Map View - Takes 2 columns on large screens */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-lg p-4 h-[600px]">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-900">Interactive Risk Map</h2>
                <div className="text-xs text-gray-600 bg-gray-100 px-3 py-1 rounded-full">
                  💡 Tip: Click anywhere to update risk data
                </div>
              </div>
              <MapView
                onLocationSelect={handleLocationSelect}
                selectedLocation={selectedLocation || defaultLocation}
                riskData={riskData}
              />
            </div>
          </div>

          {/* Sidebar - Risk Panel and Alerts */}
          <div className="space-y-6">
            <RiskPanel
              location={selectedLocation || defaultLocation}
              riskData={riskData}
              loading={loading}
            />

            <AlertsList events={recentEvents} />
          </div>
        </div>

        {/* Footer Info */}
        <div className="mt-6 bg-gray-100 rounded-lg p-4 text-center">
          <p className="text-sm text-gray-700">
            <strong className="text-gray-900">Data Sources:</strong> USGS Earthquake Catalog, ERA5 Weather Data, INSAT-3D Satellite Imagery
          </p>
          <p className="text-xs text-gray-600 mt-1">
            Last updated: {riskData?.generated_at ? new Date(riskData.generated_at).toLocaleString() : 'Loading...'}
          </p>
        </div>
      </main>
    </div>
  )
}
