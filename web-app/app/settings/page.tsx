'use client'

import { useState } from 'react'
import Header from '@/components/Header'
import { Settings, Bell, MapPin, Eye, Save } from 'lucide-react'

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    notifications: {
      earthquakes: true,
      floods: true,
      minMagnitude: 4.0,
      emailAlerts: false,
      pushNotifications: true,
    },
    map: {
      defaultLocation: { lat: 19.07, lon: 72.88, name: 'Mumbai' },
      defaultZoom: 8,
      showRiskCircles: true,
      mapStyle: 'standard',
    },
    display: {
      theme: 'light',
      timeFormat: '24h',
      units: 'metric',
      autoRefresh: true,
      refreshInterval: 5,
    },
  })

  const [saved, setSaved] = useState(false)

  const handleSave = () => {
    // In a real app, this would save to backend/localStorage
    localStorage.setItem('spiral_settings', JSON.stringify(settings))
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  const updateNotificationSetting = (key: string, value: any) => {
    setSettings({
      ...settings,
      notifications: { ...settings.notifications, [key]: value }
    })
  }

  const updateMapSetting = (key: string, value: any) => {
    setSettings({
      ...settings,
      map: { ...settings.map, [key]: value }
    })
  }

  const updateDisplaySetting = (key: string, value: any) => {
    setSettings({
      ...settings,
      display: { ...settings.display, [key]: value }
    })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="container mx-auto px-4 py-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2 flex items-center">
            <Settings className="w-8 h-8 mr-3" />
            Settings
          </h1>
          <p className="text-gray-600">Customize your SPIRAL experience</p>
        </div>

        {saved && (
          <div className="mb-6 bg-green-50 border border-green-200 text-green-800 rounded-lg p-4">
            Settings saved successfully!
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Notification Settings */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 hover:shadow-xl transition-shadow">
            <div className="mb-6">
              <h2 className="text-xl font-bold mb-2 flex items-center">
                <div className="p-2 bg-blue-100 rounded-lg mr-3">
                  <Bell className="w-5 h-5 text-blue-600" />
                </div>
                Notifications
              </h2>
              <p className="text-sm text-gray-600">Configure alert preferences and thresholds</p>
            </div>

            <div className="space-y-5">
              <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex items-center justify-between mb-1">
                  <label className="text-sm font-semibold text-gray-800">Earthquake Alerts</label>
                  <input
                    type="checkbox"
                    checked={settings.notifications.earthquakes}
                    onChange={(e) => updateNotificationSetting('earthquakes', e.target.checked)}
                    className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <p className="text-xs text-gray-600">Receive notifications for seismic events</p>
              </div>

              <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex items-center justify-between mb-1">
                  <label className="text-sm font-semibold text-gray-800">Flood Alerts</label>
                  <input
                    type="checkbox"
                    checked={settings.notifications.floods}
                    onChange={(e) => updateNotificationSetting('floods', e.target.checked)}
                    className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <p className="text-xs text-gray-600">Get alerts for flood warnings and risks</p>
              </div>

              <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                <label className="text-sm font-semibold text-gray-800 block mb-3">
                  Minimum Magnitude: <span className="text-blue-600">{settings.notifications.minMagnitude}</span>
                </label>
                <p className="text-xs text-gray-600 mb-3">Only alert for earthquakes above this magnitude</p>
                <div className="relative">
                  <input
                    type="range"
                    min="2.0"
                    max="7.0"
                    step="0.5"
                    value={settings.notifications.minMagnitude}
                    onChange={(e) => updateNotificationSetting('minMagnitude', parseFloat(e.target.value))}
                    className="w-full h-2 bg-gradient-to-r from-green-200 via-yellow-200 to-red-300 rounded-lg appearance-none cursor-pointer"
                    style={{
                      background: `linear-gradient(to right, #86efac, #fde047, #fca5a5)`
                    }}
                  />
                </div>
                <div className="flex justify-between text-xs text-gray-600 mt-2 font-medium">
                  <span>Minor (2.0)</span>
                  <span>Major (7.0+)</span>
                </div>
              </div>

              <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex items-center justify-between mb-1">
                  <label className="text-sm font-semibold text-gray-800">Email Alerts</label>
                  <input
                    type="checkbox"
                    checked={settings.notifications.emailAlerts}
                    onChange={(e) => updateNotificationSetting('emailAlerts', e.target.checked)}
                    className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <p className="text-xs text-gray-600">Send alerts to your email address</p>
              </div>

              <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex items-center justify-between mb-1">
                  <label className="text-sm font-semibold text-gray-800">Push Notifications</label>
                  <input
                    type="checkbox"
                    checked={settings.notifications.pushNotifications}
                    onChange={(e) => updateNotificationSetting('pushNotifications', e.target.checked)}
                    className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <p className="text-xs text-gray-600">Enable browser push notifications</p>
              </div>
            </div>
          </div>

          {/* Map Settings */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 hover:shadow-xl transition-shadow">
            <div className="mb-6">
              <h2 className="text-xl font-bold mb-2 flex items-center">
                <div className="p-2 bg-green-100 rounded-lg mr-3">
                  <MapPin className="w-5 h-5 text-green-600" />
                </div>
                Map Preferences
              </h2>
              <p className="text-sm text-gray-600">Customize map display and default location</p>
            </div>

            <div className="space-y-5">
              <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                <label className="text-sm font-semibold text-gray-800 block mb-2">Default Location</label>
                <p className="text-xs text-gray-600 mb-3">Choose your starting map location</p>
                <select
                  value={settings.map.defaultLocation.name}
                  onChange={(e) => {
                    const locations: any = {
                      'Mumbai': { lat: 19.07, lon: 72.88, name: 'Mumbai' },
                      'Delhi': { lat: 28.6, lon: 77.2, name: 'Delhi' },
                      'Kolkata': { lat: 22.57, lon: 88.36, name: 'Kolkata' },
                      'Chennai': { lat: 13.08, lon: 80.27, name: 'Chennai' },
                    }
                    updateMapSetting('defaultLocation', locations[e.target.value])
                  }}
                  className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg text-gray-800 font-medium focus:border-green-500 focus:ring-2 focus:ring-green-200 transition"
                >
                  <option>Mumbai</option>
                  <option>Delhi</option>
                  <option>Kolkata</option>
                  <option>Chennai</option>
                </select>
              </div>

              <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                <label className="text-sm font-semibold text-gray-800 block mb-3">
                  Default Zoom: <span className="text-green-600">{settings.map.defaultZoom}</span>
                </label>
                <p className="text-xs text-gray-600 mb-3">Set initial map zoom level</p>
                <div className="relative">
                  <input
                    type="range"
                    min="4"
                    max="12"
                    value={settings.map.defaultZoom}
                    onChange={(e) => updateMapSetting('defaultZoom', parseInt(e.target.value))}
                    className="w-full h-2 bg-gradient-to-r from-blue-200 to-green-300 rounded-lg appearance-none cursor-pointer"
                  />
                </div>
                <div className="flex justify-between text-xs text-gray-600 mt-2 font-medium">
                  <span>Wide (Country)</span>
                  <span>Close (City)</span>
                </div>
              </div>

              <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex items-center justify-between mb-1">
                  <label className="text-sm font-semibold text-gray-800">Show Risk Circles</label>
                  <input
                    type="checkbox"
                    checked={settings.map.showRiskCircles}
                    onChange={(e) => updateMapSetting('showRiskCircles', e.target.checked)}
                    className="w-5 h-5 text-green-600 rounded focus:ring-2 focus:ring-green-500"
                  />
                </div>
                <p className="text-xs text-gray-600">Display risk zones around hazard locations</p>
              </div>

              <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                <label className="text-sm font-semibold text-gray-800 block mb-2">Map Style</label>
                <p className="text-xs text-gray-600 mb-3">Select map visualization style</p>
                <select
                  value={settings.map.mapStyle}
                  onChange={(e) => updateMapSetting('mapStyle', e.target.value)}
                  className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg text-gray-800 font-medium focus:border-green-500 focus:ring-2 focus:ring-green-200 transition"
                >
                  <option value="standard">Standard</option>
                  <option value="satellite">Satellite</option>
                  <option value="terrain">Terrain</option>
                </select>
              </div>
            </div>
          </div>

          {/* Display Settings */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 hover:shadow-xl transition-shadow">
            <div className="mb-6">
              <h2 className="text-xl font-bold mb-2 flex items-center">
                <div className="p-2 bg-purple-100 rounded-lg mr-3">
                  <Eye className="w-5 h-5 text-purple-600" />
                </div>
                Display
              </h2>
              <p className="text-sm text-gray-600">Adjust visual preferences and refresh settings</p>
            </div>

            <div className="space-y-5">
              <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                <label className="text-sm font-semibold text-gray-800 block mb-2">Theme</label>
                <p className="text-xs text-gray-600 mb-3">Choose your preferred color scheme</p>
                <select
                  value={settings.display.theme}
                  onChange={(e) => updateDisplaySetting('theme', e.target.value)}
                  className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg text-gray-800 font-medium focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition"
                >
                  <option value="light">☀️ Light</option>
                  <option value="dark">🌙 Dark</option>
                  <option value="auto">🔄 Auto (System)</option>
                </select>
              </div>

              <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                <label className="text-sm font-semibold text-gray-800 block mb-2">Time Format</label>
                <p className="text-xs text-gray-600 mb-3">Select time display format</p>
                <select
                  value={settings.display.timeFormat}
                  onChange={(e) => updateDisplaySetting('timeFormat', e.target.value)}
                  className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg text-gray-800 font-medium focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition"
                >
                  <option value="12h">12-hour (AM/PM)</option>
                  <option value="24h">24-hour (Military)</option>
                </select>
              </div>

              <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                <label className="text-sm font-semibold text-gray-800 block mb-2">Units</label>
                <p className="text-xs text-gray-600 mb-3">Measurement system preference</p>
                <select
                  value={settings.display.units}
                  onChange={(e) => updateDisplaySetting('units', e.target.value)}
                  className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg text-gray-800 font-medium focus:border-purple-500 focus:ring-2 focus:ring-purple-200 transition"
                >
                  <option value="metric">📏 Metric (km, °C)</option>
                  <option value="imperial">📐 Imperial (mi, °F)</option>
                </select>
              </div>

              <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex items-center justify-between mb-1">
                  <label className="text-sm font-semibold text-gray-800">Auto Refresh</label>
                  <input
                    type="checkbox"
                    checked={settings.display.autoRefresh}
                    onChange={(e) => updateDisplaySetting('autoRefresh', e.target.checked)}
                    className="w-5 h-5 text-purple-600 rounded focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <p className="text-xs text-gray-600">Automatically refresh data periodically</p>
              </div>

              {settings.display.autoRefresh && (
                <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <label className="text-sm font-semibold text-gray-800 block mb-3">
                    Refresh Interval: <span className="text-purple-600">{settings.display.refreshInterval} min</span>
                  </label>
                  <p className="text-xs text-gray-600 mb-3">How often to update hazard data</p>
                  <div className="relative">
                    <input
                      type="range"
                      min="1"
                      max="30"
                      value={settings.display.refreshInterval}
                      onChange={(e) => updateDisplaySetting('refreshInterval', parseInt(e.target.value))}
                      className="w-full h-2 bg-gradient-to-r from-purple-200 to-pink-300 rounded-lg appearance-none cursor-pointer"
                    />
                  </div>
                  <div className="flex justify-between text-xs text-gray-600 mt-2 font-medium">
                    <span>Fast (1 min)</span>
                    <span>Slow (30 min)</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="mt-8 flex justify-end">
          <button
            onClick={handleSave}
            className="px-8 py-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl hover:from-blue-700 hover:to-blue-800 transition-all shadow-lg hover:shadow-xl transform hover:scale-105 flex items-center gap-3 font-semibold text-lg"
          >
            <Save className="w-6 h-6" />
            Save All Settings
          </button>
        </div>

        {/* Additional Info */}
        <div className="mt-8 bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-xl p-5 shadow-sm">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Settings className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm font-semibold text-blue-900 mb-1">Settings Information</p>
              <p className="text-sm text-blue-800">
                Your settings are saved locally in your browser storage. Some features may require an active API connection to function properly. For the best experience, ensure your backend server is running and accessible.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
