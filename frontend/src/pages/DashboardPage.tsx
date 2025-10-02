import { useEffect, useState, useCallback } from 'react'
import { stationsApi, bikesApi } from '../services/api'
import { StationStatus, Bike } from '../types'
import { useWebSocket } from '../hooks/useWebSocket'
import { useDataPolling } from '../hooks/useDataPolling'
import RefreshIndicator from '../components/RefreshIndicator'
import DataRefreshStatus from '../components/DataRefreshStatus'
import ManualRefreshButton from '../components/ManualRefreshButton'

export default function DashboardPage() {
  const [stations, setStations] = useState<StationStatus[]>([])
  const [bikes, setBikes] = useState<Bike[]>([])
  const [loading, setLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastRefresh, setLastRefresh] = useState<Date>()
  const [showRefreshToast, setShowRefreshToast] = useState(false)
  const [stats, setStats] = useState({
    activeStations: 0,
    totalBikes: 0,
    availableBikes: 0,
    bikesInStations: 0,
    bikesInCirculation: 0,
    pendingInterventions: 0
  })

  // WebSocket connection for real-time updates
  const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
  const { isConnected, lastMessage } = useWebSocket(`${wsUrl}/ws/realtime`)

  // Fetch data function
  const fetchData = useCallback(async () => {
    try {
      setIsRefreshing(true)
      console.log('[Dashboard] Fetching fresh data from API...')

      const [stationsRes, bikesRes] = await Promise.all([
        stationsApi.getCurrentStatus(),
        bikesApi.getCurrentStatus()
      ])

      console.log('[Dashboard] Data received - Stations:', stationsRes.data.length, 'Bikes:', bikesRes.data.length)

      setStations(stationsRes.data)
      setBikes(bikesRes.data)

      // Calculate stats from bikes data (more accurate)
      const activeStations = stationsRes.data.filter((s: StationStatus) => s.is_renting).length
      const totalBikes = bikesRes.data.length
      const availableBikes = bikesRes.data.filter(
        (b: any) => !b.is_disabled && !b.is_reserved
      ).length
      const bikesInStations = bikesRes.data.filter(
        (b: any) => b.current_station_id !== null && b.current_station_id !== ''
      ).length
      const bikesInCirculation = totalBikes - bikesInStations

      const newStats = {
        activeStations,
        totalBikes,
        availableBikes,
        bikesInStations,
        bikesInCirculation,
        pendingInterventions: 0 // TODO: fetch from API
      }

      console.log('[Dashboard] Stats calculated:', newStats)

      setStats(newStats)
      const refreshTime = new Date()
      setLastRefresh(refreshTime)
      console.log('[Dashboard] UI updated at:', refreshTime.toLocaleTimeString())

      // Afficher le toast de confirmation
      setShowRefreshToast(true)
      setTimeout(() => setShowRefreshToast(false), 3000)

      setLoading(false)
    } catch (error) {
      console.error('[Dashboard] Failed to fetch dashboard data:', error)
      setLoading(false)
    } finally {
      setIsRefreshing(false)
    }
  }, [])

  // Initial load
  useEffect(() => {
    setLoading(true)
    fetchData()
  }, [fetchData])

  // Polling toutes les 4 minutes pour near real-time
  const { isPolling, minutesUntilNextPoll } = useDataPolling({
    enabled: true,
    intervalMinutes: 4,
    onPoll: fetchData
  })

  // Handle WebSocket updates
  useEffect(() => {
    if (lastMessage) {
      console.log('WebSocket message:', lastMessage)
      // TODO: Update stations/bikes based on WebSocket messages
    }
  }, [lastMessage])

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold text-gray-800">
          Dashboard Vélivert Saint-Étienne
        </h1>
        <div className="flex items-center space-x-4">
          <DataRefreshStatus lastRefresh={lastRefresh} isRefreshing={isRefreshing} />
          <ManualRefreshButton onRefreshComplete={fetchData} />
          <div className="flex items-center space-x-2">
            <span
              className={`inline-block w-3 h-3 rounded-full ${
                isConnected ? 'bg-green-500' : 'bg-red-500'
              }`}
            />
            <span className="text-sm text-gray-600">
              {isConnected ? 'Temps réel actif' : 'Hors ligne'}
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className={`bg-white rounded-lg shadow-md p-6 transition-all duration-500 ${isRefreshing ? 'ring-2 ring-blue-400 scale-105' : ''}`}>
          <h2 className="text-xl font-semibold text-gray-700 mb-2">Total Vélos</h2>
          <p className={`text-4xl font-bold text-blue-600 transition-all duration-300 ${isRefreshing ? 'opacity-50' : 'opacity-100'}`}>
            {loading ? '...' : stats.totalBikes}
          </p>
          <p className="text-sm text-gray-500 mt-2">Dans le système</p>
          {lastRefresh && (
            <p className="text-xs text-green-600 mt-1">✓ Màj: {lastRefresh.toLocaleTimeString()}</p>
          )}
        </div>
        <div className={`bg-white rounded-lg shadow-md p-6 transition-all duration-500 ${isRefreshing ? 'ring-2 ring-green-400 scale-105' : ''}`}>
          <h2 className="text-xl font-semibold text-gray-700 mb-2">Vélos Disponibles</h2>
          <p className={`text-4xl font-bold text-green-600 transition-all duration-300 ${isRefreshing ? 'opacity-50' : 'opacity-100'}`}>
            {loading ? '...' : stats.availableBikes}
          </p>
          <p className="text-sm text-gray-500 mt-2">Prêts à l'utilisation</p>
          {lastRefresh && (
            <p className="text-xs text-green-600 mt-1">✓ Màj: {lastRefresh.toLocaleTimeString()}</p>
          )}
        </div>
        <div className={`bg-white rounded-lg shadow-md p-6 transition-all duration-500 ${isRefreshing ? 'ring-2 ring-purple-400 scale-105' : ''}`}>
          <h2 className="text-xl font-semibold text-gray-700 mb-2">Vélos en Circulation</h2>
          <p className={`text-4xl font-bold text-purple-600 transition-all duration-300 ${isRefreshing ? 'opacity-50' : 'opacity-100'}`}>
            {loading ? '...' : stats.bikesInCirculation}
          </p>
          <p className="text-sm text-gray-500 mt-2">Hors des stations</p>
          {lastRefresh && (
            <p className="text-xs text-green-600 mt-1">✓ Màj: {lastRefresh.toLocaleTimeString()}</p>
          )}
        </div>
        <div className={`bg-white rounded-lg shadow-md p-6 transition-all duration-500 ${isRefreshing ? 'ring-2 ring-cyan-400 scale-105' : ''}`}>
          <h2 className="text-xl font-semibold text-gray-700 mb-2">Stations Actives</h2>
          <p className={`text-4xl font-bold text-cyan-600 transition-all duration-300 ${isRefreshing ? 'opacity-50' : 'opacity-100'}`}>
            {loading ? '...' : stats.activeStations}
          </p>
          <p className="text-sm text-gray-500 mt-2">Opérationnelles</p>
          {lastRefresh && (
            <p className="text-xs text-green-600 mt-1">✓ Màj: {lastRefresh.toLocaleTimeString()}</p>
          )}
        </div>
      </div>

      {/* Stats détaillées */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-700">🚲 Vélos</h3>
            <a href="/bikes" className="text-blue-600 hover:text-blue-700 text-sm font-medium">
              Voir tout →
            </a>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center pb-2 border-b">
              <span className="text-gray-600">En station</span>
              <span className="font-bold text-blue-600">{stats.bikesInStations}</span>
            </div>
            <div className="flex justify-between items-center pb-2 border-b">
              <span className="text-gray-600">En circulation</span>
              <span className="font-bold text-purple-600">{stats.bikesInCirculation}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Disponibles</span>
              <span className="font-bold text-green-600">{stats.availableBikes}</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-700">🏢 Stations</h3>
            <a href="/stations" className="text-blue-600 hover:text-blue-700 text-sm font-medium">
              Voir carte →
            </a>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center pb-2 border-b">
              <span className="text-gray-600">Total stations</span>
              <span className="font-bold text-cyan-600">{stations.length}</span>
            </div>
            <div className="flex justify-between items-center pb-2 border-b">
              <span className="text-gray-600">Actives</span>
              <span className="font-bold text-green-600">{stats.activeStations}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Taux d'activité</span>
              <span className="font-bold text-blue-600">
                {stations.length > 0 ? Math.round((stats.activeStations / stations.length) * 100) : 0}%
              </span>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg shadow-md p-6 text-white">
          <h3 className="text-lg font-semibold mb-4">🗺️ Visualisation</h3>
          <p className="text-sm opacity-90 mb-4">
            Explorez la carte interactive pour voir l'état en temps réel de toutes les stations et vélos.
          </p>
          <a
            href="/stations"
            className="inline-block bg-white text-blue-600 font-semibold px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            Ouvrir la Carte Complète
          </a>
        </div>
      </div>

      {/* Quick links */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <a
          href="/interventions"
          className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow border-l-4 border-orange-500"
        >
          <div className="flex items-center gap-3">
            <span className="text-3xl">🔧</span>
            <div>
              <h4 className="font-semibold text-gray-800">Interventions</h4>
              <p className="text-sm text-gray-600">Gérer les maintenances</p>
            </div>
          </div>
        </a>

        <a
          href="/bike-flows"
          className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow border-l-4 border-purple-500"
        >
          <div className="flex items-center gap-3">
            <span className="text-3xl">📊</span>
            <div>
              <h4 className="font-semibold text-gray-800">Flux de Vélos</h4>
              <p className="text-sm text-gray-600">Analyser les mouvements</p>
            </div>
          </div>
        </a>

        <a
          href="/analytics"
          className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow border-l-4 border-green-500"
        >
          <div className="flex items-center gap-3">
            <span className="text-3xl">📈</span>
            <div>
              <h4 className="font-semibold text-gray-800">Analytics</h4>
              <p className="text-sm text-gray-600">Voir les statistiques</p>
            </div>
          </div>
        </a>
      </div>

      <RefreshIndicator isRefreshing={isRefreshing} lastRefresh={lastRefresh} />

      {/* Toast notification pour refresh */}
      {showRefreshToast && (
        <div className="fixed bottom-4 right-4 bg-green-500 text-white px-6 py-4 rounded-lg shadow-xl flex items-center gap-3 animate-slide-up z-50">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          <div>
            <p className="font-semibold">Données actualisées !</p>
            <p className="text-sm opacity-90">{stats.totalBikes} vélos • {stats.activeStations} stations</p>
          </div>
        </div>
      )}
    </div>
  )
}