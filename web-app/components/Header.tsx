'use client'

import { Activity, Bell, Settings } from 'lucide-react'

export default function Header() {
  return (
    <header className="bg-gradient-to-r from-blue-600 to-blue-800 text-white shadow-lg">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Activity className="w-8 h-8" />
            <div>
              <h1 className="text-2xl font-bold">SPIRAL</h1>
              <p className="text-xs text-blue-100">Multi-Hazard Prediction System</p>
            </div>
          </div>

          <nav className="hidden md:flex items-center space-x-6">
            <a href="#dashboard" className="hover:text-blue-200 transition">Dashboard</a>
            <a href="#alerts" className="hover:text-blue-200 transition">Alerts</a>
            <a href="#analytics" className="hover:text-blue-200 transition">Analytics</a>
            <a href="#about" className="hover:text-blue-200 transition">About</a>
          </nav>

          <div className="flex items-center space-x-4">
            <button className="relative p-2 hover:bg-blue-700 rounded-full transition">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>
            <button className="p-2 hover:bg-blue-700 rounded-full transition">
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}
