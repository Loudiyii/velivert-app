import { useEffect, useState, useCallback } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, Polyline, useMap } from 'react-leaflet'
import axios from 'axios'
import { useDataPolling } from '../hooks/useDataPolling'
import RefreshIndicator from '../components/RefreshIndicator'
import DataRefreshStatus from '../components/DataRefreshStatus'
import ManualRefreshButton from '../components/ManualRefreshButton'
import BikeMovementToast from '../components/BikeMovementToast'
import 'leaflet/dist/leaflet.css'

interface StationFlow {
  station_id: string
  name: string
  lat: number
  lon: number
  capacity: number
  bikes_arrived: number
  bikes_departed: number
  net_flow: number
  total_activity: number
  is_hub: boolean
}

interface BikeInCirculation {
  bike_id: string
  lat: number
  lon: number
  range_km: number
  is_reserved: boolean
  is_disabled: boolean
}

interface MovementSummary {
  total_movements: number
  pickups: number
  dropoffs: number
  relocations: number
  in_transit: number
  total_distance_km: number
  unique_bikes: number
}

interface BikeMovement {
  id: string
  bike_id: string
  from_station_id: string | null
  from_lat: number | null
  from_lon: number | null
  to_station_id: string | null
  to_lat: number
  to_lon: number
  movement_type: string
  distance_meters: number | null
  detected_at: string
}

export default function BikeFlowsPage() {
  const [stationFlows, setStationFlows] = useState<StationFlow[]>([])
  const [bikesInCirculation, setBikesInCirculation] = useState<BikeInCirculation[]>([])
  const [movementSummary, setMovementSummary] = useState<MovementSummary | null>(null)
  const [bikeMovements, setBikeMovements] = useState<BikeMovement[]>([])
  const [loading, setLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastRefresh, setLastRefresh] = useState<Date>()
  const [timeRange, setTimeRange] = useState(24)
  const [showMovementLines, setShowMovementLines] = useState(true)

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  const fetchData = useCallback(async () => {
    try {
      setIsRefreshing(true)

      const token = localStorage.getItem('auth_token')
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {}

      console.log('[BikeFlows] Fetching data for last', timeRange, 'hours...')

      const [flowsRes, circulationRes, movementsRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/bike-flows/flows/station-movements`, {
          params: { hours: timeRange, min_flow: 0 },
          headers
        }),
        axios.get(`${API_BASE_URL}/api/bike-flows/flows/current-circulation`, { headers }),
        axios.get(`${API_BASE_URL}/api/bike-flows/movements/history`, {
          params: { hours: timeRange, limit: 5000 },  // Augmenté de 500 à 5000
          headers
        })
      ])

      console.log('[BikeFlows] Movement summary received:', movementsRes.data.summary)
      console.log('[BikeFlows] Total movements:', movementsRes.data.movements?.length)

      setStationFlows(flowsRes.data.stations || [])
      setBikesInCirculation(circulationRes.data.bikes_in_circulation || [])
      setMovementSummary(movementsRes.data.summary || null)
      setBikeMovements(movementsRes.data.movements || [])
      setLastRefresh(new Date())
      setLoading(false)
    } catch (error) {
      console.error('[BikeFlows] Failed to fetch bike flows:', error)
      setLoading(false)
    } finally {
      setIsRefreshing(false)
    }
  }, [timeRange])

  // Initial load
  useEffect(() => {
    setLoading(true)
    fetchData()
  }, [fetchData])

  // Polling toutes les 5 minutes pour near real-time analysis
  useDataPolling({
    enabled: true,
    intervalMinutes: 5,
    onPoll: fetchData
  })

  const getStationColor = (station: StationFlow) => {
    if (station.is_hub) return '#8B5CF6' // Purple for hubs
    if (station.net_flow > 10) return '#10B981' // Green for net arrivals
    if (station.net_flow < -10) return '#EF4444' // Red for net departures
    return '#3B82F6' // Blue for balanced
  }

  const getStationRadius = (station: StationFlow) => {
    const baseRadius = 8
    const activityFactor = Math.min(station.total_activity / 50, 3)
    return baseRadius + (activityFactor * 3)
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-800">Flux de Vélos</h1>
          <p className="text-gray-600 mt-1">Analyse des mouvements entre stations</p>
        </div>

        <div className="flex items-center gap-4">
          <DataRefreshStatus lastRefresh={lastRefresh} isRefreshing={isRefreshing} />
          <ManualRefreshButton onRefreshComplete={fetchData} />
          <select
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
            value={timeRange}
            onChange={(e) => setTimeRange(Number(e.target.value))}
          >
            <option value={6}>Dernières 6h</option>
            <option value={12}>Dernières 12h</option>
            <option value={24}>Dernières 24h</option>
            <option value={48}>Dernières 48h</option>
            <option value={168}>Dernière semaine</option>
          </select>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Vélos en Circulation</h3>
          <p className="text-3xl font-bold text-purple-600">{bikesInCirculation.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Stations Actives</h3>
          <p className="text-3xl font-bold text-blue-600">{stationFlows.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Stations Hubs</h3>
          <p className="text-3xl font-bold text-indigo-600">
            {stationFlows.filter(s => s.is_hub).length}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Total Mouvements</h3>
          <p className="text-3xl font-bold text-green-600">
            {movementSummary?.total_movements || 0}
          </p>
          <p className="text-xs text-gray-500 mt-1">Détection individuelle</p>
        </div>
      </div>

      {/* Real Movement Tracking Stats */}
      {movementSummary && movementSummary.total_movements > 0 && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg shadow-md p-6 mb-6 border border-blue-200">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">
            📊 Mouvements Détectés en Temps Réel
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
            <div className="text-center">
              <p className="text-sm text-gray-600">Total</p>
              <p className="text-2xl font-bold text-blue-600">{movementSummary.total_movements}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Prises 🚴</p>
              <p className="text-2xl font-bold text-green-600">{movementSummary.pickups}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Dépôts 🅿️</p>
              <p className="text-2xl font-bold text-orange-600">{movementSummary.dropoffs}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Relocations 🚚</p>
              <p className="text-2xl font-bold text-purple-600">{movementSummary.relocations}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">En Transit 🔄</p>
              <p className="text-2xl font-bold text-indigo-600">{movementSummary.in_transit}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Distance 📍</p>
              <p className="text-2xl font-bold text-red-600">{movementSummary.total_distance_km} km</p>
            </div>
          </div>
          <p className="text-xs text-gray-600 mt-3 text-center">
            ✨ Système de tracking en temps réel basé sur la détection automatique des mouvements
          </p>
        </div>
      )}

      {/* Map */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-700 mb-4">Carte des Flux</h2>

        {/* Legend and Controls */}
        <div className="mb-4 space-y-3">
          {/* Stations Legend */}
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <h4 className="text-sm font-bold text-gray-700 mb-2">🏢 Stations</h4>
            <div className="flex flex-wrap gap-6">
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-full bg-purple-500 border-2 border-purple-700 shadow-sm"></div>
                <span className="text-gray-800 font-semibold text-base">Hubs</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-full bg-green-500 border-2 border-green-700 shadow-sm"></div>
                <span className="text-gray-800 font-semibold text-base">Arrivées (+10)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-full bg-red-500 border-2 border-red-700 shadow-sm"></div>
                <span className="text-gray-800 font-semibold text-base">Départs (-10)</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-full bg-blue-500 border-2 border-blue-700 shadow-sm"></div>
                <span className="text-gray-800 font-semibold text-base">Équilibrée</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded-full bg-orange-500 border-2 border-orange-700 shadow-sm"></div>
                <span className="text-gray-800 font-semibold text-base">Vélo en circulation</span>
              </div>
            </div>
          </div>

          {/* Movement Lines Legend */}
          {showMovementLines && bikeMovements.length > 0 && (
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
              <h4 className="text-sm font-bold text-blue-800 mb-2">🔄 Mouvements de vélos</h4>
              <div className="flex flex-wrap gap-6">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-1 bg-blue-600 rounded"></div>
                  <span className="text-gray-800 font-semibold text-sm">🚴 Pickup</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-1 bg-green-600 rounded"></div>
                  <span className="text-gray-800 font-semibold text-sm">📍 Dropoff</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-1 bg-purple-600 rounded"></div>
                  <span className="text-gray-800 font-semibold text-sm">🔄 Relocation</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-1 bg-orange-600 rounded"></div>
                  <span className="text-gray-800 font-semibold text-sm">🚲 En transit</span>
                </div>
              </div>
            </div>
          )}

          {/* Controls */}
          <div className="flex justify-between items-center">
            <label className="flex items-center gap-3 cursor-pointer bg-white px-4 py-3 rounded-lg border-2 border-gray-300 hover:border-blue-500 transition-colors shadow-sm">
              <input
                type="checkbox"
                checked={showMovementLines}
                onChange={(e) => {
                  console.log('Toggle movement lines:', e.target.checked, 'Movements count:', bikeMovements.length)
                  setShowMovementLines(e.target.checked)
                }}
                className="w-5 h-5 text-blue-600 rounded"
              />
              <span className="text-gray-800 font-bold text-base">
                {showMovementLines ? '✓ Liaisons actives' : 'Afficher les liaisons'} {bikeMovements.length > 0 && `(${bikeMovements.length})`}
              </span>
            </label>

            {showMovementLines && bikeMovements.length > 0 && (
              <div className="text-sm text-gray-600 bg-white px-4 py-2 rounded-lg border border-gray-200">
                Affichage : <span className="font-bold text-blue-600">{Math.min(100, bikeMovements.filter(m => m.from_lat && m.from_lon).length)}</span> mouvements récents
              </div>
            )}
          </div>
        </div>

        {loading ? (
          <div className="h-96 flex items-center justify-center bg-gray-100 rounded">
            <p className="text-gray-500">Chargement de la carte...</p>
          </div>
        ) : (
          <div className="h-[600px] rounded-lg overflow-hidden">
            <MapContainer
              center={[45.439695, 4.387178]}
              zoom={13}
              style={{ height: '100%', width: '100%' }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />

              {/* Station Flows */}
              {stationFlows.map((station) => (
                <CircleMarker
                  key={station.station_id}
                  center={[station.lat, station.lon]}
                  radius={getStationRadius(station)}
                  pathOptions={{
                    fillColor: getStationColor(station),
                    fillOpacity: 0.7,
                    color: '#fff',
                    weight: 2
                  }}
                >
                  <Popup>
                    <div className="text-sm">
                      <p className="font-bold text-gray-900">{station.name}</p>
                      {station.is_hub && (
                        <p className="text-purple-600 font-semibold">⭐ Station Hub</p>
                      )}
                      <p className="mt-2">
                        <span className="font-medium">Capacité:</span> {station.capacity}
                      </p>
                      <p>
                        <span className="font-medium">Arrivées:</span>{' '}
                        <span className="text-green-600">+{station.bikes_arrived}</span>
                      </p>
                      <p>
                        <span className="font-medium">Départs:</span>{' '}
                        <span className="text-red-600">-{station.bikes_departed}</span>
                      </p>
                      <p className="mt-1">
                        <span className="font-medium">Flux net:</span>{' '}
                        <span className={station.net_flow > 0 ? 'text-green-600' : 'text-red-600'}>
                          {station.net_flow > 0 ? '+' : ''}{station.net_flow}
                        </span>
                      </p>
                      <p>
                        <span className="font-medium">Activité totale:</span> {station.total_activity}
                      </p>
                    </div>
                  </Popup>
                </CircleMarker>
              ))}

              {/* Bikes in Circulation */}
              {bikesInCirculation.map((bike) => (
                <CircleMarker
                  key={bike.bike_id}
                  center={[bike.lat, bike.lon]}
                  radius={5}
                  pathOptions={{
                    fillColor: bike.is_disabled ? '#DC2626' : bike.is_reserved ? '#F59E0B' : '#FF6B6B',
                    fillOpacity: 0.8,
                    color: '#fff',
                    weight: 1
                  }}
                >
                  <Popup>
                    <div className="text-sm">
                      <p className="font-bold text-gray-900">Vélo en circulation</p>
                      <p className="text-xs text-gray-600">{bike.bike_id.substring(0, 8)}...</p>
                      <p className="mt-1">
                        <span className="font-medium">Autonomie:</span> {bike.range_km} km
                      </p>
                      <p>
                        <span className="font-medium">Statut:</span>{' '}
                        {bike.is_disabled ? 'Désactivé' : bike.is_reserved ? 'Réservé' : 'En utilisation'}
                      </p>
                    </div>
                  </Popup>
                </CircleMarker>
              ))}

              {/* Movement Lines - Connexions entre déplacements */}
              {showMovementLines && bikeMovements.length > 0 && bikeMovements
                .filter(m => m.from_lat && m.from_lon && m.to_lat && m.to_lon)
                .slice(0, 100) // Afficher jusqu'à 100 lignes
                .map((movement, idx) => {
                  const getMovementColor = (type: string) => {
                    switch (type) {
                      case 'pickup': return '#2563EB' // Blue vif
                      case 'dropoff': return '#059669' // Green vif
                      case 'relocation': return '#7C3AED' // Purple vif
                      case 'in_transit': return '#EA580C' // Orange vif
                      default: return '#DC2626' // Red vif
                    }
                  }

                  // Les mouvements récents sont plus opaques
                  const opacity = Math.max(0.4, 1 - (idx / 100))

                  return (
                    <Polyline
                      key={movement.id}
                      positions={[
                        [movement.from_lat!, movement.from_lon!],
                        [movement.to_lat, movement.to_lon]
                      ]}
                      pathOptions={{
                        color: getMovementColor(movement.movement_type),
                        weight: 4, // Plus épais
                        opacity: opacity, // Opacité variable selon l'âge
                        lineCap: 'round',
                        lineJoin: 'round'
                      }}
                    >
                      <Popup>
                        <div className="text-sm">
                          <p className="font-bold text-gray-900">Mouvement de Vélo</p>
                          <p className="text-xs text-gray-600 mb-1">{movement.bike_id.substring(0, 8)}...</p>
                          <p>
                            <span className="font-medium">Type:</span>{' '}
                            {movement.movement_type === 'pickup' ? '🚴 Pickup' :
                             movement.movement_type === 'dropoff' ? '📍 Dropoff' :
                             movement.movement_type === 'relocation' ? '🔄 Relocation' : '🚲 En transit'}
                          </p>
                          {movement.distance_meters && (
                            <p>
                              <span className="font-medium">Distance:</span> {(movement.distance_meters / 1000).toFixed(2)} km
                            </p>
                          )}
                          <p className="text-xs text-gray-500 mt-1">
                            {new Date(movement.detected_at).toLocaleString()}
                          </p>
                        </div>
                      </Popup>
                    </Polyline>
                  )
                })}
            </MapContainer>
          </div>
        )}

        {/* Info message when no movements */}
        {!loading && bikeMovements.length === 0 && (
          <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
            <p className="text-blue-800 font-medium">
              ℹ️ Aucun mouvement de vélo détecté dans les dernières {timeRange}h
            </p>
            <p className="text-blue-600 text-sm mt-1">
              Les liaisons s'afficheront automatiquement dès qu'un vélo sera déplacé
            </p>
          </div>
        )}
      </div>

      {/* Top Stations Table */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-700 mb-4">Stations les Plus Actives</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Station</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Arrivées</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Départs</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Flux Net</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Activité</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {stationFlows
                .sort((a, b) => b.total_activity - a.total_activity)
                .slice(0, 10)
                .map((station) => (
                  <tr key={station.station_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {station.name}
                      {station.is_hub && <span className="ml-2">⭐</span>}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {station.is_hub ? (
                        <span className="px-2 py-1 text-xs rounded-full bg-purple-100 text-purple-800">
                          Hub
                        </span>
                      ) : station.net_flow > 10 ? (
                        <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">
                          Arrivée
                        </span>
                      ) : station.net_flow < -10 ? (
                        <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800">
                          Départ
                        </span>
                      ) : (
                        <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                          Équilibré
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600 font-medium">
                      +{station.bikes_arrived}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600 font-medium">
                      -{station.bikes_departed}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <span className={station.net_flow > 0 ? 'text-green-600' : station.net_flow < 0 ? 'text-red-600' : 'text-gray-600'}>
                        {station.net_flow > 0 ? '+' : ''}{station.net_flow}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-bold">
                      {station.total_activity}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>

      <RefreshIndicator isRefreshing={isRefreshing} lastRefresh={lastRefresh} />

      {/* Toast Notifications pour les nouveaux mouvements */}
      <BikeMovementToast movements={bikeMovements} />
    </div>
  )
}
