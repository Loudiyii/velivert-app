import { useEffect, useState } from 'react'
import axios from 'axios'

interface DataRefreshStatusProps {
  lastRefresh?: Date
  isRefreshing?: boolean
  className?: string
}

interface SystemStats {
  total_bikes: number
  bikes_available: number
  bikes_disabled: number
  bikes_in_circulation: number
  total_stations: number
  last_data_update: string
  data_freshness_seconds: number
}

export default function DataRefreshStatus({
  lastRefresh,
  isRefreshing = false,
  className = ''
}: DataRefreshStatusProps) {
  const [stats, setStats] = useState<SystemStats | null>(null)
  const [isOpen, setIsOpen] = useState(false)

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const token = localStorage.getItem('auth_token')
        const headers = token ? { 'Authorization': `Bearer ${token}` } : {}

        const [bikesRes, stationsRes] = await Promise.all([
          axios.get(`${API_BASE_URL}/api/bikes/current`, { headers }),
          axios.get(`${API_BASE_URL}/api/stations/current`, { headers })
        ])

        const bikes = bikesRes.data
        const stations = stationsRes.data

        // Calculer les statistiques
        const bikesDisabled = bikes.filter((b: any) => b.is_disabled).length
        const bikesInCirculation = bikes.filter((b: any) => !b.current_station_id || b.current_station_id === '').length
        const bikesAvailable = bikes.length - bikesDisabled

        // Utiliser lastRefresh si fourni, sinon utiliser last_reported des vélos
        let lastUpdate: Date
        let freshnessSeconds: number

        if (lastRefresh) {
          // Utiliser le timestamp du dernier refresh manuel
          lastUpdate = lastRefresh
          freshnessSeconds = Math.floor((new Date().getTime() - lastRefresh.getTime()) / 1000)
        } else {
          // Sinon, trouver la dernière mise à jour dans les données
          const bikeLastUpdate = bikes.reduce((latest: Date | null, bike: any) => {
            if (!bike.last_reported) return latest
            const bikeDate = new Date(bike.last_reported)
            return !latest || bikeDate > latest ? bikeDate : latest
          }, null)

          lastUpdate = bikeLastUpdate || new Date()
          freshnessSeconds = bikeLastUpdate
            ? Math.floor((new Date().getTime() - bikeLastUpdate.getTime()) / 1000)
            : 0
        }

        setStats({
          total_bikes: bikes.length,
          bikes_available: bikesAvailable,
          bikes_disabled: bikesDisabled,
          bikes_in_circulation: bikesInCirculation,
          total_stations: stations.length,
          last_data_update: lastUpdate.toISOString(),
          data_freshness_seconds: freshnessSeconds
        })
      } catch (error) {
        console.error('Failed to fetch system stats:', error)
      }
    }

    fetchStats()
    const interval = setInterval(fetchStats, 5000) // Refresh every 5s to update countdown
    return () => clearInterval(interval)
  }, [lastRefresh])

  const formatTimeAgo = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}min`
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}min`
  }

  const formatDateTime = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const getFreshnessColor = (seconds: number) => {
    if (seconds < 60) return 'text-green-600'
    if (seconds < 300) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getFreshnessBg = (seconds: number) => {
    if (seconds < 60) return 'bg-green-50 border-green-200'
    if (seconds < 300) return 'bg-yellow-50 border-yellow-200'
    return 'bg-red-50 border-red-200'
  }

  return (
    <div className={`relative ${className}`}>
      {/* Status indicator button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-2 px-3 py-2 rounded-lg border transition-all ${
          isRefreshing
            ? 'bg-blue-50 border-blue-200 animate-pulse'
            : stats
            ? getFreshnessBg(stats.data_freshness_seconds)
            : 'bg-gray-50 border-gray-200'
        }`}
      >
        {isRefreshing ? (
          <>
            <svg className="animate-spin h-4 w-4 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span className="text-sm font-medium text-blue-600">Actualisation...</span>
          </>
        ) : stats ? (
          <>
            <div className={`w-2 h-2 rounded-full ${stats.data_freshness_seconds < 60 ? 'bg-green-500' : stats.data_freshness_seconds < 300 ? 'bg-yellow-500' : 'bg-red-500'}`}></div>
            <span className={`text-sm font-medium ${getFreshnessColor(stats.data_freshness_seconds)}`}>
              Mise à jour: {formatTimeAgo(stats.data_freshness_seconds)}
            </span>
          </>
        ) : (
          <span className="text-sm text-gray-500">Chargement...</span>
        )}
        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Expanded details panel */}
      {isOpen && stats && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-xl border border-gray-200 z-50 p-4">
          <div className="flex justify-between items-start mb-3">
            <h3 className="text-sm font-semibold text-gray-800">📊 État du Système</h3>
            <button
              onClick={() => setIsOpen(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          {/* Freshness indicator */}
          <div className={`mb-3 p-3 rounded-lg border ${getFreshnessBg(stats.data_freshness_seconds)}`}>
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-gray-600">Fraîcheur des données</span>
              <span className={`text-sm font-bold ${getFreshnessColor(stats.data_freshness_seconds)}`}>
                {formatTimeAgo(stats.data_freshness_seconds)}
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Dernière actualisation: {formatDateTime(stats.last_data_update)}
            </div>
          </div>

          {/* Stats grid */}
          <div className="space-y-2">
            <div className="flex justify-between items-center p-2 bg-gray-50 rounded">
              <span className="text-xs text-gray-600">🚲 Total Vélos</span>
              <span className="text-sm font-bold text-gray-900">{stats.total_bikes}</span>
            </div>

            <div className="flex justify-between items-center p-2 bg-green-50 rounded">
              <span className="text-xs text-gray-600">✅ Disponibles</span>
              <span className="text-sm font-bold text-green-700">{stats.bikes_available}</span>
            </div>

            <div className="flex justify-between items-center p-2 bg-red-50 rounded">
              <span className="text-xs text-gray-600">❌ Désactivés</span>
              <span className="text-sm font-bold text-red-700">{stats.bikes_disabled}</span>
            </div>

            <div className="flex justify-between items-center p-2 bg-purple-50 rounded">
              <span className="text-xs text-gray-600">🔄 En Circulation</span>
              <span className="text-sm font-bold text-purple-700">{stats.bikes_in_circulation}</span>
            </div>

            <div className="flex justify-between items-center p-2 bg-blue-50 rounded">
              <span className="text-xs text-gray-600">🏢 Stations</span>
              <span className="text-sm font-bold text-blue-700">{stats.total_stations}</span>
            </div>
          </div>

          {/* Footer */}
          <div className="mt-3 pt-3 border-t border-gray-200">
            <div className="text-xs text-gray-500 text-center">
              {lastRefresh && (
                <>Dernière synchro: {lastRefresh.toLocaleTimeString('fr-FR')}</>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
