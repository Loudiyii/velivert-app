import { useEffect, useState } from 'react'
import { stationsApi } from '../services/api'
import { StationStatus } from '../types'
import StationList from '../components/Stations/StationList'
import StationMap from '../components/Stations/StationMap'
import RefreshIndicator from '../components/RefreshIndicator'

type ViewMode = 'map' | 'list'

export default function StationsPage() {
  const [stations, setStations] = useState<StationStatus[]>([])
  const [loading, setLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastRefresh, setLastRefresh] = useState<Date>()
  const [viewMode, setViewMode] = useState<ViewMode>('map')

  useEffect(() => {
    const fetchStations = async (isAutoRefresh = false) => {
      try {
        if (isAutoRefresh) {
          setIsRefreshing(true)
        } else {
          setLoading(true)
        }
        const response = await stationsApi.getCurrentStatus()
        setStations(response.data)
        setLastRefresh(new Date())
      } catch (error) {
        console.error('Failed to fetch stations:', error)
      } finally {
        setLoading(false)
        setIsRefreshing(false)
      }
    }

    fetchStations(false)
    // Refresh stations every 30 seconds
    const interval = setInterval(() => fetchStations(true), 30000)
    return () => clearInterval(interval)
  }, [])

  const handleStationClick = (station: StationStatus) => {
    console.log('Station clicked:', station)
    // TODO: Show station details modal or navigate to station detail page
  }

  return (
    <div>
      {/* Header with view toggle */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Stations</h1>
          <p className="text-gray-600 mt-1">{stations.length} station(s) trouvée(s)</p>
        </div>

        {/* View Mode Toggle */}
        <div className="flex gap-2 bg-white rounded-lg shadow-md p-1">
          <button
            onClick={() => setViewMode('map')}
            className={`px-4 py-2 rounded-md transition-colors ${
              viewMode === 'map'
                ? 'bg-blue-600 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            🗺️ Carte
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`px-4 py-2 rounded-md transition-colors ${
              viewMode === 'list'
                ? 'bg-blue-600 text-white'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            📋 Liste
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-500">Chargement des stations...</p>
        </div>
      ) : (
        <>
          {viewMode === 'map' && (
            <StationMap stations={stations} onStationClick={handleStationClick} />
          )}
          {viewMode === 'list' && (
            <StationList stations={stations} onStationClick={handleStationClick} />
          )}
        </>
      )}

      <RefreshIndicator isRefreshing={isRefreshing} lastRefresh={lastRefresh} />
    </div>
  )
}