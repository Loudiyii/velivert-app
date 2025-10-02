import { useEffect, useState } from 'react'
import axios from 'axios'
import OccupancyChart from '../components/Analytics/OccupancyChart'
import IdleBikesTable from '../components/Analytics/IdleBikesTable'
import RefreshIndicator from '../components/RefreshIndicator'

interface AnalyticsOverview {
  period_hours: number
  average_occupancy_rate: number
  idle_bikes_count: number
  daily_bike_rotations: number
  occupancy_timeseries: Array<{
    timestamp: string
    occupancy_rate: number
    average_bikes_available: number
  }>
}

export default function AnalyticsPage() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null)
  const [idleBikes, setIdleBikes] = useState([])
  const [loading, setLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastRefresh, setLastRefresh] = useState<Date>()
  const [timeWindow, setTimeWindow] = useState(24)

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  useEffect(() => {
    const fetchAnalytics = async (isAutoRefresh = false) => {
      try {
        if (isAutoRefresh) {
          setIsRefreshing(true)
        } else {
          setLoading(true)
        }

        console.log('[Analytics] Fetching data for', timeWindow, 'hours...')

        const token = localStorage.getItem('auth_token')
        const headers = token ? { 'Authorization': `Bearer ${token}` } : {}

        // Fetch overview data
        const overviewResponse = await axios.get(
          `${API_BASE_URL}/api/analytics/overview?hours=${timeWindow}`,
          { headers }
        )
        setOverview(overviewResponse.data)

        // Fetch idle bikes
        const idleResponse = await axios.get(
          `${API_BASE_URL}/api/analytics/bikes/idle-detection?threshold_hours=${timeWindow}`,
          { headers }
        )
        setIdleBikes(idleResponse.data)

        setLastRefresh(new Date())
        console.log('[Analytics] Data updated:', overviewResponse.data)

      } catch (error) {
        console.error('[Analytics] Failed to fetch analytics:', error)
      } finally {
        setLoading(false)
        setIsRefreshing(false)
      }
    }

    fetchAnalytics(false)

    // Auto-refresh every 60 seconds
    const interval = setInterval(() => fetchAnalytics(true), 60000)
    return () => clearInterval(interval)
  }, [timeWindow])

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">Analytics</h1>
      </div>

      {/* Message de maintenance */}
      <div className="bg-yellow-50 border-2 border-yellow-300 rounded-lg p-8 text-center">
        <div className="text-6xl mb-4">🚧</div>
        <h2 className="text-2xl font-bold text-gray-800 mb-3">Onglet Temporairement Hors Service</h2>
        <p className="text-gray-700 text-lg mb-2">
          Cet onglet nécessite davantage de données historiques pour fonctionner correctement.
        </p>
        <p className="text-gray-600">
          Les analytics seront disponibles après avoir collecté suffisamment de snapshots de stations sur plusieurs jours.
        </p>
        <div className="mt-6 inline-flex items-center gap-2 bg-blue-100 text-blue-800 px-4 py-2 rounded-lg">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="font-medium">Collecte de données en cours...</span>
        </div>
      </div>

      {/* Ancien contenu masqué */}
      <div className="hidden">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className={`bg-white rounded-lg shadow-md p-6 transition-all duration-300 ${isRefreshing ? 'opacity-70' : ''}`}>
          <h3 className="text-sm font-medium text-gray-500 mb-1">Taux d'Occupation Moyen</h3>
          <p className="text-3xl font-bold text-blue-600">
            {loading ? '...' : `${Math.round((overview?.average_occupancy_rate || 0) * 100)}%`}
          </p>
          <p className="text-sm text-gray-500 mt-1">Dernières {timeWindow}h</p>
        </div>
        <div className={`bg-white rounded-lg shadow-md p-6 transition-all duration-300 ${isRefreshing ? 'opacity-70' : ''}`}>
          <h3 className="text-sm font-medium text-gray-500 mb-1">Vélos Immobiles</h3>
          <p className="text-3xl font-bold text-orange-600">
            {loading ? '...' : (overview?.idle_bikes_count || 0)}
          </p>
          <p className="text-sm text-gray-500 mt-1">Nécessitant attention</p>
        </div>
        <div className={`bg-white rounded-lg shadow-md p-6 transition-all duration-300 ${isRefreshing ? 'opacity-70' : ''}`}>
          <h3 className="text-sm font-medium text-gray-500 mb-1">Rotations Journalières</h3>
          <p className="text-3xl font-bold text-green-600">
            {loading ? '...' : (overview?.daily_bike_rotations || 0)}
          </p>
          <p className="text-sm text-gray-500 mt-1">Moyenne par vélo</p>
        </div>
      </div>

      <div className="mb-6">
        <OccupancyChart
          data={overview?.occupancy_timeseries || []}
          stationName="Toutes les stations"
        />
      </div>

      <div>
        {loading ? (
          <div className="flex items-center justify-center h-64 bg-white rounded-lg shadow-md">
            <p className="text-gray-500">Chargement des données...</p>
          </div>
        ) : (
          <IdleBikesTable bikes={idleBikes} />
        )}
      </div>

      {/* Debug info */}
      {!loading && overview && (
        <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm">
          <p className="font-semibold text-blue-800 mb-2">📊 État des données Analytics :</p>
          <ul className="space-y-1 text-blue-700">
            <li>✓ Taux d'occupation : {Math.round((overview.average_occupancy_rate || 0) * 100)}%</li>
            <li>✓ Vélos immobiles : {overview.idle_bikes_count}</li>
            <li>✓ Rotations journalières : {overview.daily_bike_rotations}</li>
            <li>✓ Points de données graphique : {overview.occupancy_timeseries?.length || 0}</li>
          </ul>
        </div>
      )}

      <RefreshIndicator isRefreshing={isRefreshing} lastRefresh={lastRefresh} />
      </div>
      {/* Fin ancien contenu masqué */}
    </div>
  )
}