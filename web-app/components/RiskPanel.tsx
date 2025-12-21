'use client'

import { AlertTriangle, Droplets, Waves, Activity } from 'lucide-react'

interface RiskPanelProps {
  location: { lat: number, lon: number }
  riskData: any
  loading: boolean
}

export default function RiskPanel({ location, riskData, loading }: RiskPanelProps) {
  const getRiskClass = (level: string) => {
    switch (level) {
      case 'LOW': return 'bg-green-500'
      case 'MODERATE': return 'bg-yellow-500'
      case 'HIGH': return 'bg-orange-500'
      case 'EXTREME': return 'bg-red-700'
      default: return 'bg-gray-500'
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-8 bg-gray-200 rounded"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    )
  }

  const mainCell = riskData?.cells?.[0]
  const risk6h = mainCell?.risk?.['6h']
  const components = mainCell?.components

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-xl font-bold mb-4 flex items-center">
        <AlertTriangle className="w-5 h-5 mr-2 text-orange-500" />
        Risk Assessment
      </h2>

      <div className="space-y-4">
        {/* Current Risk Level */}
        <div className="text-center p-4 rounded-lg bg-gray-50">
          <p className="text-sm text-gray-600 mb-2">Current Risk Level (6h)</p>
          <div className={`inline-block px-6 py-2 rounded-full text-white font-bold text-lg ${getRiskClass(risk6h?.level || 'LOW')}`}>
            {risk6h?.level || 'LOW'}
          </div>
          <p className="text-sm text-gray-600 mt-2">
            Score: {((risk6h?.score || 0) * 100).toFixed(1)}%
          </p>
        </div>

        {/* Location Info */}
        <div className="text-sm text-gray-600 border-t pt-4">
          <p className="font-semibold mb-1">Location:</p>
          <p>{location.lat.toFixed(4)}°N, {location.lon.toFixed(4)}°E</p>
        </div>

        {/* Component Risks */}
        {components && (
          <div className="border-t pt-4">
            <p className="font-semibold mb-3 text-sm">Hazard Components:</p>
            <div className="space-y-2">
              {components.rain_extreme_6h && (
                <RiskComponent
                  icon={<Droplets className="w-4 h-4" />}
                  label="Extreme Rain (6h)"
                  value={components.rain_extreme_6h}
                  color="text-blue-600"
                />
              )}
              {components.flood_12h && (
                <RiskComponent
                  icon={<Waves className="w-4 h-4" />}
                  label="Flood (12h)"
                  value={components.flood_12h}
                  color="text-cyan-600"
                />
              )}
              {components.mmi_mean && (
                <RiskComponent
                  icon={<Activity className="w-4 h-4" />}
                  label="Earthquake MMI"
                  value={components.mmi_mean / 10}
                  color="text-red-600"
                />
              )}
            </div>
          </div>
        )}

        {/* Last Updated */}
        <div className="text-xs text-gray-500 border-t pt-4 text-center">
          Last updated: {riskData?.generated_at ? new Date(riskData.generated_at).toLocaleString() : 'N/A'}
        </div>
      </div>
    </div>
  )
}

function RiskComponent({ icon, label, value, color }: any) {
  return (
    <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
      <div className="flex items-center space-x-2">
        <span className={color}>{icon}</span>
        <span className="text-sm">{label}</span>
      </div>
      <div className="flex items-center space-x-2">
        <div className="w-24 bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full ${color.replace('text-', 'bg-')}`}
            style={{ width: `${Math.min(value * 100, 100)}%` }}
          ></div>
        </div>
        <span className="text-sm font-semibold w-12 text-right">
          {(value * 100).toFixed(0)}%
        </span>
      </div>
    </div>
  )
}
