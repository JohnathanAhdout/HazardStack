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
    return response.data.events || []
  } catch (error) {
    console.error('Error fetching recent events:', error)
    // Return mock data if API is unavailable
    return getMockEvents()
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
  return {
    query: { lat, lon, radius_km: 10 },
    generated_at: new Date().toISOString(),
    cells: [
      {
        h3_id: '852a1073fffffff',
        centroid: [lat, lon],
        risk: {
          '1h': { level: 'LOW', score: 0.23 },
          '6h': { level: 'MODERATE', score: 0.43 },
          '24h': { level: 'HIGH', score: 0.71 },
        },
        components: {
          rain_extreme_6h: 0.68,
          flood_12h: 0.22,
          mmi_mean: 1.2,
          aftershock_24h: 0.03,
        },
        explain: [
          { feature: 'R_acc_3h', impact: 0.19 },
          { feature: 'API_3d', impact: 0.12 },
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
