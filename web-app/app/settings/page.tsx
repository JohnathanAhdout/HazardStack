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
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4 flex items-center">
              <Bell className="w-5 h-5 mr-2" />
              Notifications
            </h2>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium">Earthquake Alerts</label>
                <input
                  type="checkbox"
                  checked={settings.notifications.earthquakes}
                  onChange={(e) => updateNotificationSetting('earthquakes', e.target.checked)}
                  className="w-5 h-5"
                />
              </div>

              <div className="flex items-center justify-between">
                <label className="text-sm font-medium">Flood Alerts</label>
                <input
                  type="checkbox"
                  checked={settings.notifications.floods}
                  onChange={(e) => updateNotificationSetting('floods', e.target.checked)}
                  className="w-5 h-5"
                />
              </div>

              <div>
                <label className="text-sm font-medium block mb-2">
                  Minimum Magnitude: {settings.notifications.minMagnitude}
                </label>
                <input
                  type="range"
                  min="2.0"
                  max="7.0"
                  step="0.5"
                  value={settings.notifications.minMagnitude}
                  onChange={(e) => updateNotificationSetting('minMagnitude', parseFloat(e.target.value))}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>2.0</span>
                  <span>7.0+</span>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <label className="text-sm font-medium">Email Alerts</label>
                <input
                  type="checkbox"
                  checked={settings.notifications.emailAlerts}
                  onChange={(e) => updateNotificationSetting('emailAlerts', e.target.checked)}
                  className="w-5 h-5"
                />
              </div>

              <div className="flex items-center justify-between">
                <label className="text-sm font-medium">Push Notifications</label>
                <input
                  type="checkbox"
                  checked={settings.notifications.pushNotifications}
                  onChange={(e) => updateNotificationSetting('pushNotifications', e.target.checked)}
                  className="w-5 h-5"
                />
              </div>
            </div>
          </div>

          {/* Map Settings */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4 flex items-center">
              <MapPin className="w-5 h-5 mr-2" />
              Map Preferences
            </h2>

            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium block mb-2">Default Location</label>
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
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option>Mumbai</option>
                  <option>Delhi</option>
                  <option>Kolkata</option>
                  <option>Chennai</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium block mb-2">
                  Default Zoom: {settings.map.defaultZoom}
                </label>
                <input
                  type="range"
                  min="4"
                  max="12"
                  value={settings.map.defaultZoom}
                  onChange={(e) => updateMapSetting('defaultZoom', parseInt(e.target.value))}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>Country</span>
                  <span>City</span>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <label className="text-sm font-medium">Show Risk Circles</label>
                <input
                  type="checkbox"
                  checked={settings.map.showRiskCircles}
                  onChange={(e) => updateMapSetting('showRiskCircles', e.target.checked)}
                  className="w-5 h-5"
                />
              </div>

              <div>
                <label className="text-sm font-medium block mb-2">Map Style</label>
                <select
                  value={settings.map.mapStyle}
                  onChange={(e) => updateMapSetting('mapStyle', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="standard">Standard</option>
                  <option value="satellite">Satellite</option>
                  <option value="terrain">Terrain</option>
                </select>
              </div>
            </div>
          </div>

          {/* Display Settings */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4 flex items-center">
              <Eye className="w-5 h-5 mr-2" />
              Display
            </h2>

            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium block mb-2">Theme</label>
                <select
                  value={settings.display.theme}
                  onChange={(e) => updateDisplaySetting('theme', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                  <option value="auto">Auto</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium block mb-2">Time Format</label>
                <select
                  value={settings.display.timeFormat}
                  onChange={(e) => updateDisplaySetting('timeFormat', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="12h">12-hour</option>
                  <option value="24h">24-hour</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium block mb-2">Units</label>
                <select
                  value={settings.display.units}
                  onChange={(e) => updateDisplaySetting('units', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="metric">Metric (km, °C)</option>
                  <option value="imperial">Imperial (mi, °F)</option>
                </select>
              </div>

              <div className="flex items-center justify-between">
                <label className="text-sm font-medium">Auto Refresh</label>
                <input
                  type="checkbox"
                  checked={settings.display.autoRefresh}
                  onChange={(e) => updateDisplaySetting('autoRefresh', e.target.checked)}
                  className="w-5 h-5"
                />
              </div>

              {settings.display.autoRefresh && (
                <div>
                  <label className="text-sm font-medium block mb-2">
                    Refresh Interval: {settings.display.refreshInterval} min
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="30"
                    value={settings.display.refreshInterval}
                    onChange={(e) => updateDisplaySetting('refreshInterval', parseInt(e.target.value))}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>1 min</span>
                    <span>30 min</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="mt-6 flex justify-end">
          <button
            onClick={handleSave}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2"
          >
            <Save className="w-5 h-5" />
            Save Settings
          </button>
        </div>

        {/* Additional Info */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-800">
            <strong>Note:</strong> Settings are saved locally in your browser. Some features may require
            an active API connection to function properly.
          </p>
        </div>
      </main>
    </div>
  )
}
