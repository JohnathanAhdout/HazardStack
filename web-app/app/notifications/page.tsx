'use client'

import { useState, useEffect } from 'react'
import Header from '@/components/Header'
import { fetchRecentEvents } from '@/lib/api'
import { Bell, AlertCircle, CheckCircle, XCircle, Clock } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

interface Notification {
  id: string
  type: 'earthquake' | 'flood' | 'warning' | 'info'
  severity: 'low' | 'medium' | 'high' | 'critical'
  title: string
  message: string
  timestamp: Date
  read: boolean
  event?: any
}

export default function Notifications() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [filter, setFilter] = useState<'all' | 'unread' | 'earthquake' | 'flood'>('all')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadNotifications()
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadNotifications, 30000)
    return () => clearInterval(interval)
  }, [])

  const loadNotifications = async () => {
    setLoading(true)
    try {
      const events = await fetchRecentEvents(72, 2.5) // Last 3 days

      // Convert events to notifications
      const newNotifications: Notification[] = events.map((event, idx) => {
        if (event.type === 'earthquake') {
          const severity = event.magnitude >= 6 ? 'critical' :
                          event.magnitude >= 5 ? 'high' :
                          event.magnitude >= 4 ? 'medium' : 'low'

          return {
            id: event.event_id || `eq-${idx}`,
            type: 'earthquake' as const,
            severity,
            title: `M${event.magnitude?.toFixed(1)} Earthquake`,
            message: `${event.place} - Depth: ${event.depth?.toFixed(1)}km`,
            timestamp: new Date(event.time),
            read: false,
            event,
          }
        } else {
          const severity = event.risk_level === 'EXTREME' ? 'critical' :
                          event.risk_level === 'HIGH' ? 'high' :
                          event.risk_level === 'MODERATE' ? 'medium' : 'low'

          return {
            id: `flood-${idx}`,
            type: 'flood' as const,
            severity,
            title: `Flood Alert - ${event.risk_level}`,
            message: event.message || event.basin,
            timestamp: new Date(event.time),
            read: false,
            event,
          }
        }
      })

      setNotifications(newNotifications.sort((a, b) =>
        b.timestamp.getTime() - a.timestamp.getTime()
      ))
    } catch (error) {
      console.error('Error loading notifications:', error)
    } finally {
      setLoading(false)
    }
  }

  const markAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    )
  }

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })))
  }

  const deleteNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }

  const filteredNotifications = notifications.filter(n => {
    if (filter === 'all') return true
    if (filter === 'unread') return !n.read
    return n.type === filter
  })

  const unreadCount = notifications.filter(n => !n.read).length

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="container mx-auto px-4 py-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2 flex items-center">
              <Bell className="w-8 h-8 mr-3" />
              Notifications
              {unreadCount > 0 && (
                <span className="ml-3 px-3 py-1 bg-red-500 text-white text-sm rounded-full">
                  {unreadCount} new
                </span>
              )}
            </h1>
            <p className="text-gray-600">Stay informed about recent hazard events and system alerts</p>
          </div>
          <button
            onClick={markAllAsRead}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Mark all as read
          </button>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-2 rounded-md ${filter === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
            >
              All ({notifications.length})
            </button>
            <button
              onClick={() => setFilter('unread')}
              className={`px-4 py-2 rounded-md ${filter === 'unread' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
            >
              Unread ({unreadCount})
            </button>
            <button
              onClick={() => setFilter('earthquake')}
              className={`px-4 py-2 rounded-md ${filter === 'earthquake' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
            >
              Earthquakes ({notifications.filter(n => n.type === 'earthquake').length})
            </button>
            <button
              onClick={() => setFilter('flood')}
              className={`px-4 py-2 rounded-md ${filter === 'flood' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
            >
              Floods ({notifications.filter(n => n.type === 'flood').length})
            </button>
          </div>
        </div>

        {/* Notifications List */}
        <div className="space-y-3">
          {loading ? (
            <div className="text-center py-12">
              <Bell className="w-12 h-12 mx-auto text-gray-400 animate-pulse mb-4" />
              <p className="text-gray-600">Loading notifications...</p>
            </div>
          ) : filteredNotifications.length === 0 ? (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <CheckCircle className="w-16 h-16 mx-auto text-green-500 mb-4" />
              <p className="text-xl font-semibold mb-2">All caught up!</p>
              <p className="text-gray-600">No {filter === 'all' ? '' : filter} notifications to show</p>
            </div>
          ) : (
            filteredNotifications.map(notification => (
              <NotificationCard
                key={notification.id}
                notification={notification}
                onRead={markAsRead}
                onDelete={deleteNotification}
              />
            ))
          )}
        </div>
      </main>
    </div>
  )
}

function NotificationCard({ notification, onRead, onDelete }: any) {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'border-red-500 bg-red-50'
      case 'high': return 'border-orange-500 bg-orange-50'
      case 'medium': return 'border-yellow-500 bg-yellow-50'
      case 'low': return 'border-green-500 bg-green-50'
      default: return 'border-gray-300 bg-white'
    }
  }

  const getIcon = () => {
    switch (notification.type) {
      case 'earthquake':
        return <AlertCircle className="w-6 h-6 text-red-600" />
      case 'flood':
        return <AlertCircle className="w-6 h-6 text-blue-600" />
      default:
        return <Bell className="w-6 h-6 text-gray-600" />
    }
  }

  return (
    <div
      className={`border-l-4 rounded-lg shadow p-4 transition ${getSeverityColor(notification.severity)} ${
        notification.read ? 'opacity-60' : ''
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3 flex-1">
          <div className="mt-1">{getIcon()}</div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-bold text-lg">{notification.title}</h3>
              {!notification.read && (
                <span className="px-2 py-0.5 bg-blue-500 text-white text-xs rounded-full">NEW</span>
              )}
            </div>
            <p className="text-gray-700 mb-2">{notification.message}</p>
            <div className="flex items-center gap-4 text-xs text-gray-600">
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {formatDistanceToNow(notification.timestamp, { addSuffix: true })}
              </span>
              <span className="px-2 py-0.5 bg-gray-200 rounded uppercase font-medium">
                {notification.severity}
              </span>
            </div>
          </div>
        </div>
        <div className="flex gap-2 ml-4">
          {!notification.read && (
            <button
              onClick={() => onRead(notification.id)}
              className="p-2 hover:bg-gray-200 rounded transition"
              title="Mark as read"
            >
              <CheckCircle className="w-5 h-5 text-green-600" />
            </button>
          )}
          <button
            onClick={() => onDelete(notification.id)}
            className="p-2 hover:bg-gray-200 rounded transition"
            title="Delete"
          >
            <XCircle className="w-5 h-5 text-red-600" />
          </button>
        </div>
      </div>
    </div>
  )
}
