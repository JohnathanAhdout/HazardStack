import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface RiskParams {
  lat: number
  lon: number
  radius_km: number
  horizons: string[]
}

export async function fetchRiskData(
  lat: number,
  lon: number,
  radius_km: number = 10,
  horizons: string[] = ['1h', '6h', '24h']
): Promise<any> {
  try {
    const response = await api.get('/api/v1/risk', {
      params: {
        lat,
        lon,
        radius_km,
        horizons: horizons.join(','),
      },
    })
    return response.data
  } catch (error) {
    console.error('Error fetching risk data:', error)
    // Return mock data if API is unavailable
    return getMockRiskData(lat, lon)
  }
}

export async function fetchRecentEvents(
  hours: number = 24,
  min_magnitude: number = 3.0
): Promise<any[]> {
  try {
    const response = await api.get('/api/v1/events/recent', {
      params: {
        hours,
        min_magnitude,
      },
    })
    // Combine earthquakes and flood bulletins into a single events array
    const earthquakes = (response.data.earthquakes || []).map((eq: any) => ({
      type: 'earthquake',
      magnitude: eq.magnitude,
      place: eq.location,
      coordinates: [eq.longitude, eq.latitude],
      depth: eq.depth_km,
      time: eq.time,
      event_id: eq.event_id,
      source: eq.source,
    }))
    const floods = (response.data.flood_bulletins || []).map((fb: any) => ({
      type: 'flood',
      basin: fb.basin_name,
      risk_level: fb.risk_level,
      message: fb.message,
      time: fb.issued_at,
    }))
    return [...earthquakes, ...floods]
  } catch (error) {
    console.error('Error fetching recent events:', error)
    // Return mock data if API is unavailable
    return getMockEvents()
  }
}

export async function fetchEventDetails(event_id: string): Promise<any> {
  try {
    const response = await api.get(`/api/v1/events/earthquake/${event_id}`)
    return response.data
  } catch (error) {
    console.error('Error fetching event details:', error)
    return null
  }
}

export async function fetchHealthCheck(): Promise<any> {
  try {
    const response = await api.get('/api/v1/health')
    return response.data
  } catch (error) {
    console.error('Error checking API health:', error)
    return { status: 'unavailable' }
  }
}

// Mock data for development/demo
function getMockRiskData(lat: number, lon: number): any {
  // Generate pseudo-random but deterministic values based on lat/lon
  // This ensures different locations show different risk levels
  const seed = Math.abs(Math.sin(lat * 100) * Math.cos(lon * 100))

  // Generate varying risk scores based on location
  const score1h = 0.1 + (seed * 0.4)  // Range: 0.1 - 0.5
  const score6h = 0.3 + (seed * 0.5)  // Range: 0.3 - 0.8
  const score24h = 0.4 + (seed * 0.6) // Range: 0.4 - 1.0

  // Convert scores to risk levels
  const getRiskLevel = (score: number): string => {
    if (score >= 0.75) return 'EXTREME'
    if (score >= 0.6) return 'HIGH'
    if (score >= 0.4) return 'MODERATE'
    return 'LOW'
  }

  // Generate component risks with variation
  const rainExtreme = 0.2 + (Math.abs(Math.sin(lat * 50)) * 0.7)
  const flood = 0.1 + (Math.abs(Math.cos(lon * 50)) * 0.6)
  const mmi = 0.5 + (Math.abs(Math.sin(lat + lon)) * 3.5)
  const aftershock = 0.01 + (Math.abs(Math.cos(lat - lon)) * 0.15)

  return {
    query: { lat, lon, radius_km: 10 },
    generated_at: new Date().toISOString(),
    cells: [
      {
        h3_id: '852a1073fffffff',
        centroid: [lat, lon],
        risk: {
          '1h': { level: getRiskLevel(score1h), score: parseFloat(score1h.toFixed(2)) },
          '6h': { level: getRiskLevel(score6h), score: parseFloat(score6h.toFixed(2)) },
          '24h': { level: getRiskLevel(score24h), score: parseFloat(score24h.toFixed(2)) },
        },
        components: {
          rain_extreme_6h: parseFloat(rainExtreme.toFixed(2)),
          flood_12h: parseFloat(flood.toFixed(2)),
          mmi_mean: parseFloat(mmi.toFixed(1)),
          aftershock_24h: parseFloat(aftershock.toFixed(3)),
        },
        explain: [
          { feature: 'R_acc_3h', impact: parseFloat((0.1 + seed * 0.2).toFixed(2)) },
          { feature: 'API_3d', impact: parseFloat((0.05 + seed * 0.15).toFixed(2)) },
        ],
      },
    ],
  }
}

function getMockEvents(): any[] {
  return [
    {
      magnitude: 4.5,
      place: 'Northern India',
      coordinates: [77.2, 28.7],
      depth: 10.0,
      time: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    },
    {
      magnitude: 3.8,
      place: 'Gujarat',
      coordinates: [72.5, 23.0],
      depth: 5.2,
      time: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
    },
    {
      magnitude: 5.2,
      place: 'Northeast India',
      coordinates: [91.7, 26.2],
      depth: 35.0,
      time: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
    },
  ]
}

export default api
