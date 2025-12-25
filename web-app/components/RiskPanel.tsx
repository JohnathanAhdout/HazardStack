'use client'

import { AlertTriangle, Droplets, Waves, Activity, Info, HelpCircle } from 'lucide-react'
import { useState } from 'react'

interface RiskPanelProps {
  location: { lat: number, lon: number }
  riskData: any
  loading: boolean
}

export default function RiskPanel({ location, riskData, loading }: RiskPanelProps) {
  const [showInfo, setShowInfo] = useState(false)

  const getRiskClass = (level: string) => {
    switch (level) {
      case 'LOW': return 'bg-green-500'
      case 'MODERATE': return 'bg-yellow-500'
      case 'HIGH': return 'bg-orange-500'
      case 'EXTREME': return 'bg-red-700'
      default: return 'bg-gray-500'
    }
  }

  const getRiskDescription = (level: string) => {
    switch (level) {
      case 'LOW': return 'Minimal hazard risk. Normal activities can proceed.'
      case 'MODERATE': return 'Moderate risk. Monitor conditions and prepare precautions.'
      case 'HIGH': return 'Significant risk. Take protective actions immediately.'
      case 'EXTREME': return 'Severe risk. Evacuate if advised by authorities.'
      default: return 'Risk level unknown.'
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-8 bg-gray-200 rounded"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          <div className="text-center py-4">
            <p className="text-sm text-gray-600">Analyzing risk data for selected location...</p>
          </div>
        </div>
      </div>
    )
  }

  const mainCell = riskData?.cells?.[0]
  const risk6h = mainCell?.risk?.['6h']
  const components = mainCell?.components

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900 flex items-center">
          <AlertTriangle className="w-5 h-5 mr-2 text-orange-500" />
          Risk Assessment
        </h2>
        <button
          onClick={() => setShowInfo(!showInfo)}
          className="p-1 hover:bg-gray-100 rounded-full transition"
          title="Toggle information"
        >
          <HelpCircle className="w-5 h-5 text-gray-600" />
        </button>
      </div>

      {showInfo && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
          <p className="text-sm text-gray-800">
            <strong className="text-gray-900">What is this?</strong> This panel shows the predicted risk level for the next 6 hours at the selected location.
            Risk scores are calculated using machine learning models trained on historical hazard data.
          </p>
        </div>
      )}

      <div className="space-y-4">
        {/* Current Risk Level */}
        <div className="text-center p-4 rounded-lg bg-gray-50">
          <p className="text-sm text-gray-700 mb-2">6-Hour Risk Forecast</p>
          <div className={`inline-block px-6 py-2 rounded-full text-white font-bold text-lg ${getRiskClass(risk6h?.level || 'LOW')}`}>
            {risk6h?.level || 'LOW'}
          </div>
          <p className="text-sm text-gray-700 mt-2">
            Probability: {((risk6h?.score || 0) * 100).toFixed(1)}%
          </p>
          <p className="text-xs text-gray-600 mt-2 italic">
            {getRiskDescription(risk6h?.level || 'LOW')}
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
            <p className="font-semibold mb-2 text-sm text-gray-900">Individual Hazard Risks:</p>
            <p className="text-xs text-gray-600 mb-3">
              Each hazard type is analyzed separately. Higher percentages indicate greater risk.
            </p>
            <div className="space-y-2">
              {components.rain_extreme_6h !== undefined && (
                <RiskComponent
                  icon={<Droplets className="w-4 h-4" />}
                  label="Extreme Rainfall"
                  value={components.rain_extreme_6h}
                  color="text-blue-600"
                  description="Probability of >100mm rainfall in 6 hours"
                />
              )}
              {components.flood_12h !== undefined && (
                <RiskComponent
                  icon={<Waves className="w-4 h-4" />}
                  label="Flooding Risk"
                  value={components.flood_12h}
                  color="text-cyan-600"
                  description="Probability of flood exceedance in 12 hours"
                />
              )}
              {components.mmi_mean !== undefined && (
                <RiskComponent
                  icon={<Activity className="w-4 h-4" />}
                  label="Earthquake Shaking"
                  value={components.mmi_mean / 10}
                  color="text-red-600"
                  description="Modified Mercalli Intensity (MMI) level"
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

function RiskComponent({ icon, label, value, color, description }: any) {
  const [showTooltip, setShowTooltip] = useState(false)

  return (
    <div className="relative">
      <div className="flex items-center justify-between p-2 bg-gray-50 rounded hover:bg-gray-100 transition">
        <div className="flex items-center space-x-2">
          <span className={color}>{icon}</span>
          <div className="flex items-center gap-1">
            <span className="text-sm text-gray-900">{label}</span>
            <button
              onMouseEnter={() => setShowTooltip(true)}
              onMouseLeave={() => setShowTooltip(false)}
              onClick={() => setShowTooltip(!showTooltip)}
              className="p-0.5 hover:bg-gray-200 rounded-full transition"
            >
              <Info className="w-3 h-3 text-gray-500" />
            </button>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-24 bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full ${color.replace('text-', 'bg-')}`}
              style={{ width: `${Math.min(value * 100, 100)}%` }}
            ></div>
          </div>
          <span className="text-sm font-semibold w-12 text-right text-gray-900">
            {(value * 100).toFixed(0)}%
          </span>
        </div>
      </div>
      {showTooltip && description && (
        <div className="absolute z-10 left-0 right-0 mt-1 bg-gray-900 text-white text-xs p-2 rounded shadow-lg">
          {description}
        </div>
      )}
    </div>
  )
}
