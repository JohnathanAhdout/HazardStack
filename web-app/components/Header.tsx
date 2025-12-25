'use client'

import { Activity, Bell, Settings } from 'lucide-react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

export default function Header() {
  const pathname = usePathname()

  const isActive = (path: string) => {
    return pathname === path || pathname?.startsWith(path)
  }

  return (
    <header className="bg-gradient-to-r from-blue-600 to-blue-800 text-white shadow-lg">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Link href="/dashboard" className="flex items-center space-x-3 hover:opacity-90 transition">
            <Activity className="w-8 h-8" />
            <div>
              <h1 className="text-2xl font-bold">SPIRAL</h1>
              <p className="text-xs text-blue-100">Multi-Hazard Prediction System</p>
            </div>
          </Link>

          <nav className="hidden md:flex items-center space-x-6">
            <Link
              href="/dashboard"
              className={`hover:text-blue-200 transition ${isActive('/dashboard') ? 'font-bold border-b-2 border-white' : ''}`}
            >
              Dashboard
            </Link>
            <Link
              href="/alerts"
              className={`hover:text-blue-200 transition ${isActive('/alerts') ? 'font-bold border-b-2 border-white' : ''}`}
            >
              Alerts
            </Link>
            <Link
              href="/analytics"
              className={`hover:text-blue-200 transition ${isActive('/analytics') ? 'font-bold border-b-2 border-white' : ''}`}
            >
              Analytics
            </Link>
            <Link
              href="/about"
              className={`hover:text-blue-200 transition ${isActive('/about') ? 'font-bold border-b-2 border-white' : ''}`}
            >
              About
            </Link>
          </nav>

          <div className="flex items-center space-x-4">
            <Link href="/notifications" className="relative p-2 hover:bg-blue-700 rounded-full transition">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </Link>
            <Link href="/settings" className="p-2 hover:bg-blue-700 rounded-full transition">
              <Settings className="w-5 h-5" />
            </Link>
          </div>
        </div>
      </div>
    </header>
  )
}
