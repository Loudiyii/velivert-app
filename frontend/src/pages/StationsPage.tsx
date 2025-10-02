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

  // Top 5 stations by available bikes
  const topStations = stations
    .filter(station => station.is_renting && station.num_bikes_available > 0)
    .sort((a, b) => b.num_bikes_available - a.num_bikes_available)
    .slice(0, 5)

  // Bottom 5 stations by available bikes (need potential rebalancing)
  const bottomStations = stations
    .filter(station => station.is_renting)
    .sort((a, b) => a.num_bikes_available - b.num_bikes_available)
    .slice(0, 5)

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
            <>
              <StationMap stations={stations} onStationClick={handleStationClick} />

              {/* Top 5 Stations - Only show in map mode */}
              {topStations.length > 0 && (
                <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border border-yellow-200 rounded-lg p-4 mt-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                    🏆 Top 5 Stations - Plus de vélos disponibles
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                    {topStations.map((station, index) => (
                      <div
                        key={station.station_id}
                        className="bg-white rounded-lg p-3 shadow-sm border hover:shadow-md transition-shadow cursor-pointer"
                        onClick={() => handleStationClick(station)}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-2xl font-bold text-yellow-600">#{index + 1}</span>
                          <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full">
                            {station.num_bikes_available} vélos
                          </span>
                        </div>
                        <h4 className="font-medium text-gray-800 text-sm leading-tight">
                          {station.name}
                        </h4>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Bottom 5 Stations - Need potential rebalancing */}
              {bottomStations.length > 0 && (
                <div className="bg-gradient-to-r from-red-50 to-orange-50 border border-red-200 rounded-lg p-4 mt-4">
                  <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
                    ⚠️ Stations nécessitant une requillibration potentielle
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                    {bottomStations.map((station, index) => (
                      <div
                        key={station.station_id}
                        className="bg-white rounded-lg p-3 shadow-sm border hover:shadow-md transition-shadow cursor-pointer"
                        onClick={() => handleStationClick(station)}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-2xl font-bold text-red-600">#{index + 1}</span>
                          <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded-full">
                            {station.num_bikes_available} vélos
                          </span>
                        </div>
                        <h4 className="font-medium text-gray-800 text-sm leading-tight">
                          {station.name}
                        </h4>
                        <p className="text-xs text-red-600 mt-1">
                          Faible disponibilité
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
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