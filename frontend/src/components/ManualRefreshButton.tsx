import { useState, useEffect, useRef } from 'react'
import axios from 'axios'

interface ManualRefreshButtonProps {
  onRefreshComplete?: () => void
  autoRefreshInterval?: number // en secondes, par défaut 60 (1min)
}

// Global timer shared across all instances
let globalSecondsRemaining = 60
let globalLastRefreshTime = Date.now()

export default function ManualRefreshButton({
  onRefreshComplete,
  autoRefreshInterval = 60  // 1 minute par défaut
}: ManualRefreshButtonProps) {
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [secondsUntilRefresh, setSecondsUntilRefresh] = useState(() => {
    // Initialize from global timer
    const elapsed = Math.floor((Date.now() - globalLastRefreshTime) / 1000)
    const remaining = Math.max(1, autoRefreshInterval - elapsed)
    return remaining
  })

  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const onRefreshCompleteRef = useRef(onRefreshComplete)

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  // Keep ref updated without triggering re-renders
  useEffect(() => {
    onRefreshCompleteRef.current = onRefreshComplete
  }, [onRefreshComplete])

  const handleRefresh = async () => {
    try {
      setIsRefreshing(true)
      setError(null)

      const token = localStorage.getItem('auth_token')
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {}

      console.log('[ManualRefresh] Starting data refresh...')

      // Appel à l'endpoint de refresh manuel
      const response = await axios.post(
        `${API_BASE_URL}/api/data/manual-refresh`,
        {},
        { headers }
      )

      const refreshTime = new Date()
      setLastRefresh(refreshTime)

      // Reset global timer
      globalSecondsRemaining = autoRefreshInterval
      globalLastRefreshTime = Date.now()
      setSecondsUntilRefresh(autoRefreshInterval)

      console.log('[ManualRefresh] Refresh completed:', response.data)
      console.log('[ManualRefresh] Movements detected by backend:', response.data.stats?.movements_detected)
      console.log('[ManualRefresh] Last refresh:', refreshTime.toLocaleTimeString())

      // Attendre que la base de données finalise les écritures et que le backend détecte les mouvements
      await new Promise(resolve => setTimeout(resolve, 1500))

      // Appeler le callback si fourni pour mettre à jour les données dans la page
      if (onRefreshCompleteRef.current) {
        console.log('[ManualRefresh] Calling onRefreshComplete callback to update UI...')
        await onRefreshCompleteRef.current()
      }
    } catch (err: any) {
      console.error('[ManualRefresh] Refresh failed:', err)
      setError(err.response?.data?.detail || 'Erreur lors du rafraîchissement')
    } finally {
      setIsRefreshing(false)
    }
  }

  // Auto-refresh timer + countdown
  useEffect(() => {
    // Clear existing interval if any
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
    }

    intervalRef.current = setInterval(() => {
      // Update global timer
      globalSecondsRemaining = Math.max(0, globalSecondsRemaining - 1)

      if (globalSecondsRemaining <= 0) {
        // Trigger refresh
        console.log('[ManualRefresh] Auto-refresh triggered!')
        handleRefresh()
        globalSecondsRemaining = autoRefreshInterval
        globalLastRefreshTime = Date.now()
      }

      // Update local state from global timer
      setSecondsUntilRefresh(globalSecondsRemaining)
    }, 1000)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [autoRefreshInterval]) // Only depend on autoRefreshInterval, not handleRefresh

  const formatCountdown = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="relative group">
      <button
        onClick={handleRefresh}
        disabled={isRefreshing}
        className={`
          flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all relative
          ${isRefreshing
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-green-600 hover:bg-green-700 active:scale-95'
          }
          text-white shadow-md
        `}
        title={`Actualiser les données maintenant (auto-refresh dans ${formatCountdown(secondsUntilRefresh)})`}
      >
        <svg
          className={`w-5 h-5 ${isRefreshing ? 'animate-spin' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
          />
        </svg>
        <span>{isRefreshing ? 'Actualisation...' : 'Actualiser'}</span>

        {/* Countdown badge */}
        {!isRefreshing && (
          <span className="ml-1 bg-green-800 bg-opacity-50 px-2 py-0.5 rounded-full text-xs font-mono">
            {formatCountdown(secondsUntilRefresh)}
          </span>
        )}
      </button>

      {/* Hover tooltip */}
      <div className="absolute bottom-full mb-2 right-0 hidden group-hover:block bg-gray-900 text-white text-xs rounded px-3 py-2 whitespace-nowrap z-10">
        <div className="text-center">
          <div className="font-semibold">🔄 Actualisation automatique</div>
          <div className="mt-1">Prochain refresh dans: <span className="font-mono font-bold text-green-400">{formatCountdown(secondsUntilRefresh)}</span></div>
          <div className="text-gray-400 mt-1">Cliquez pour actualiser maintenant</div>
        </div>
        {/* Arrow */}
        <div className="absolute top-full right-4 -mt-1 border-4 border-transparent border-t-gray-900"></div>
      </div>

      {lastRefresh && !isRefreshing && (
        <div className="absolute top-full mt-1 right-0 text-xs text-gray-600 whitespace-nowrap">
          ✅ Dernière màj: {lastRefresh.toLocaleTimeString()}
        </div>
      )}

      {error && (
        <div className="absolute top-full mt-1 right-0 bg-red-100 border border-red-300 text-red-700 px-3 py-1 rounded text-xs whitespace-nowrap z-20">
          ❌ {error}
        </div>
      )}
    </div>
  )
}
