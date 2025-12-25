'use client'

import { useState, useEffect } from 'react'
import Header from '@/components/Header'
import MapView from '@/components/MapView'
import RiskPanel from '@/components/RiskPanel'
import AlertsList from '@/components/AlertsList'
import StatsOverview from '@/components/StatsOverview'
import { fetchRiskData, fetchRecentEvents } from '@/lib/api'

export default function Dashboard() {
  const [selectedLocation, setSelectedLocation] = useState<{lat: number, lon: number} | null>(null)
  const [riskData, setRiskData] = useState<any>(null)
  const [recentEvents, setRecentEvents] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  // Default to Mumbai coordinates
  const defaultLocation = { lat: 19.07, lon: 72.88 }

  useEffect(() => {
    // Fetch initial data for default location
    loadData(defaultLocation)
    loadRecentEvents()
  }, [])

  const loadData = async (location: {lat: number, lon: number}) => {
    setLoading(true)
    try {
      const data = await fetchRiskData(location.lat, location.lon, 10, ['1h', '6h', '24h'])
      setRiskData(data)
      setSelectedLocation(location)
    } catch (error) {
      console.error('Error fetching risk data:', error)
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
    }
  }

  const handleLocationSelect = (lat: number, lon: number) => {
    loadData({ lat, lon })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="container mx-auto px-4 py-6">
        {/* Stats Overview */}
        <StatsOverview riskData={riskData} recentEvents={recentEvents} />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
          {/* Map View - Takes 2 columns on large screens */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-lg p-4 h-[600px]">
              <h2 className="text-xl font-bold mb-4">Risk Map</h2>
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
      </main>
    </div>
  )
}
