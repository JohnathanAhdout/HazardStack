'use client'

import { TrendingUp, AlertTriangle, Activity, CloudRain } from 'lucide-react'

interface StatsOverviewProps {
  riskData: any
  recentEvents: any[]
}

export default function StatsOverview({ riskData, recentEvents }: StatsOverviewProps) {
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
      label: 'Recent Events',
      value: recentEvents.length || 0,
      unit: '24h',
      color: 'bg-orange-500',
    },
    {
      icon: <CloudRain className="w-6 h-6" />,
      label: 'Gravity Wave Features',
      value: '24',
      unit: 'active',
      color: 'bg-cyan-500',
    },
    {
      icon: <TrendingUp className="w-6 h-6" />,
      label: 'Model Accuracy',
      value: '94.5',
      unit: '% R²',
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
