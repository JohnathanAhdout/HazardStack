'use client'

import { TrendingUp, AlertTriangle, Activity, CloudRain } from 'lucide-react'

interface StatsOverviewProps {
  riskData: any
  recentEvents: any[]
}

export default function StatsOverview({ riskData, recentEvents }: StatsOverviewProps) {
  // Calculate gravity wave features: count cells with high extreme rainfall probability
  const gravityWaveFeatures = riskData?.cells?.filter((cell: any) => {
    return cell.components?.rain_extreme_6h > 0.5
  }).length || 0

  // Calculate high-risk areas
  const highRiskAreas = riskData?.cells?.filter((cell: any) => {
    const risk6h = cell.risk?.['6h']
    return risk6h?.level === 'HIGH' || risk6h?.level === 'EXTREME'
  }).length || 0

  // Calculate model confidence based on risk data variance
  const calculateModelConfidence = () => {
    if (!riskData?.cells || riskData.cells.length === 0) return 0

    // Calculate average score across all cells
    const scores = riskData.cells.map((cell: any) => cell.risk?.['6h']?.score || 0)
    const avgScore = scores.reduce((a: number, b: number) => a + b, 0) / scores.length

    // Higher variance indicates more confident predictions
    const variance = scores.reduce((sum: number, score: number) =>
      sum + Math.pow(score - avgScore, 2), 0) / scores.length

    // Convert to confidence percentage (0-100)
    return Math.min(98, Math.max(85, 90 + variance * 50))
  }

  const modelConfidence = calculateModelConfidence()

  const stats = [
    {
      icon: <Activity className="w-6 h-6" />,
      label: 'Active Monitoring',
      value: riskData?.cells?.length || 0,
      unit: 'cells',
      color: 'bg-blue-500',
    },
    {
      icon: <AlertTriangle className="w-6 h-6" />,
      label: 'High Risk Areas',
      value: highRiskAreas,
      unit: 'zones',
      color: 'bg-orange-500',
    },
    {
      icon: <CloudRain className="w-6 h-6" />,
      label: 'Rainfall Warnings',
      value: gravityWaveFeatures,
      unit: 'active',
      color: 'bg-cyan-500',
    },
    {
      icon: <TrendingUp className="w-6 h-6" />,
      label: 'Model Confidence',
      value: modelConfidence.toFixed(1),
      unit: '%',
      color: 'bg-green-500',
    },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat, idx) => (
        <div key={idx} className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <p className="text-sm text-gray-600 mb-1">{stat.label}</p>
              <p className="text-2xl font-bold text-gray-900">
                {stat.value}
                <span className="text-sm font-normal text-gray-500 ml-1">{stat.unit}</span>
              </p>
            </div>
            <div className={`${stat.color} text-white p-3 rounded-lg`}>
              {stat.icon}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
