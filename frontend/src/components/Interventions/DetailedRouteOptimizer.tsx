import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet'
import L from 'leaflet'
import axios from 'axios'
import 'leaflet/dist/leaflet.css'

// Fix leaflet default icon issue
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

interface Station {
  station_id: string
  name: string
  lat: number
  lon: number
  capacity: number
  disabled_bikes_count: number
}

interface DetailedInstruction {
  step: number
  action: string
  location: string
  bike_id?: string
  priority?: string
  description: string
}

interface OptimalRoute {
  waypoints: any[]
  total_distance_meters: number
  estimated_duration_minutes: number
  total_bikes: number
  route_type: string
  start_location?: string
  detailed_instructions?: DetailedInstruction[]
}

interface DetailedRouteOptimizerProps {
  routeType: 'disabled_bikes' | 'pending_interventions' | 'low_battery'
}

export default function DetailedRouteOptimizer({ routeType }: DetailedRouteOptimizerProps) {
  const [stations, setStations] = useState<Station[]>([])
  const [selectedStation, setSelectedStation] = useState<string>('')
  const [route, setRoute] = useState<OptimalRoute | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  // Charger les stations avec vélos hors service
  useEffect(() => {
    const fetchStations = async () => {
      try {
        const token = localStorage.getItem('auth_token')
        const headers = token ? { 'Authorization': `Bearer ${token}` } : {}

        const response = await axios.get(
          `${API_BASE_URL}/api/route-optimization/stations-with-disabled-bikes`,
          { headers }
        )

        console.log('Stations loaded:', response.data)
        const loadedStations = response.data.stations || []
        setStations(loadedStations)

        // Auto-sélectionner la station avec le plus de vélos défectueux (temps record)
        if (loadedStations.length > 0) {
          const optimalStation = loadedStations.reduce((max, station) =>
            station.disabled_bikes_count > max.disabled_bikes_count ? station : max
          )
          setSelectedStation(optimalStation.station_id)
          console.log('🚀 Station optimale sélectionnée:', optimalStation.name,
                      `(${optimalStation.disabled_bikes_count} vélos)`)
        }
      } catch (err: any) {
        console.error('Failed to fetch stations:', err)
        console.error('Error details:', err.response?.data)
        // Essayer sans authentification si erreur 401/403
        if (err.response?.status === 401 || err.response?.status === 403) {
          try {
            const response = await axios.get(
              `${API_BASE_URL}/api/route-optimization/stations-with-disabled-bikes`
            )
            const loadedStations = response.data.stations || []
            setStations(loadedStations)

            if (loadedStations.length > 0) {
              const optimalStation = loadedStations.reduce((max, station) =>
                station.disabled_bikes_count > max.disabled_bikes_count ? station : max
              )
              setSelectedStation(optimalStation.station_id)
            }
          } catch (retryErr) {
            console.error('Retry failed:', retryErr)
          }
        }
      }
    }

    fetchStations()
  }, [routeType])

  const fetchRoute = async () => {
    try {
      setLoading(true)
      setError(null)

      const token = localStorage.getItem('auth_token')
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {}

      const params: any = { route_type: routeType }
      if (selectedStation) {
        params.start_station_id = selectedStation
      }

      const response = await axios.get(
        `${API_BASE_URL}/api/route-optimization/optimize/detailed-route`,
        { headers, params }
      )

      setRoute(response.data)
    } catch (err: any) {
      console.error('Failed to fetch optimal route:', err)
      setError(err.response?.data?.detail || 'Erreur lors du calcul du trajet')
    } finally {
      setLoading(false)
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return '#DC2626'
      case 'high': return '#F59E0B'
      case 'medium': return '#3B82F6'
      case 'low': return '#10B981'
      default: return '#6B7280'
    }
  }

  const createNumberedIcon = (number: number, priority: string) => {
    const color = getPriorityColor(priority)
    return L.divIcon({
      html: `
        <div style="
          background-color: ${color};
          width: 30px;
          height: 30px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: bold;
          font-size: 14px;
          border: 2px solid white;
          box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        ">
          ${number}
        </div>
      `,
      className: '',
      iconSize: [30, 30],
      iconAnchor: [15, 15],
    })
  }

  const routeTypeLabels = {
    disabled_bikes: 'Vélos Désactivés',
    low_battery: 'Batteries Faibles',
    pending_interventions: 'Interventions en Attente'
  }

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">
          🛣️ Optimisation de Trajet - {routeTypeLabels[routeType]}
        </h3>

        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Station de Départ (Optionnel)
            </label>
            <select
              value={selectedStation}
              onChange={(e) => setSelectedStation(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
            >
              <option value="" className="text-gray-900">🏢 Centre de Saint-Étienne (Par défaut)</option>
              {stations.map((station) => (
                <option key={station.station_id} value={station.station_id} className="text-gray-900">
                  {station.name} ({station.disabled_bikes_count} vélo{station.disabled_bikes_count > 1 ? 's' : ''} hors service)
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={fetchRoute}
              disabled={loading}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? '⏳ Calcul...' : '🗺️ Calculer le Trajet'}
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {route && route.waypoints.length === 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800">Aucun trajet à optimiser pour le moment</p>
        </div>
      )}

      {route && route.waypoints.length > 0 && (
        <>
          {/* Route Stats */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div className="bg-white rounded-lg shadow-md p-4">
              <h3 className="text-sm font-medium text-gray-500 mb-1">📍 Points d'Arrêt</h3>
              <p className="text-2xl font-bold text-blue-600">{route.waypoints.length}</p>
            </div>
            <div className="bg-white rounded-lg shadow-md p-4">
              <h3 className="text-sm font-medium text-gray-500 mb-1">📏 Distance</h3>
              <p className="text-2xl font-bold text-green-600">
                {(route.total_distance_meters / 1000).toFixed(1)} km
              </p>
            </div>
            <div className="bg-white rounded-lg shadow-md p-4">
              <h3 className="text-sm font-medium text-gray-500 mb-1">⏱️ Durée Estimée</h3>
              <p className="text-2xl font-bold text-orange-600">
                {Math.floor(route.estimated_duration_minutes / 60)}h{route.estimated_duration_minutes % 60}min
              </p>
            </div>
            <div className="bg-white rounded-lg shadow-md p-4">
              <h3 className="text-sm font-medium text-gray-500 mb-1">🚲 Vélos</h3>
              <p className="text-2xl font-bold text-purple-600">{route.total_bikes}</p>
            </div>
            <div className="bg-white rounded-lg shadow-md p-4">
              <h3 className="text-sm font-medium text-gray-500 mb-1">🚀 Départ</h3>
              <p className="text-sm font-semibold text-indigo-600 line-clamp-2">
                {route.start_location || 'Centre ville'}
              </p>
            </div>
          </div>

          {/* Narrative Description - Texte détaillé de récupération */}
          {route.detailed_instructions && route.detailed_instructions.length > 0 && (
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg shadow-md p-6 border border-blue-200">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">
                📝 Instructions de Collecte Détaillées
              </h3>
              <div className="prose prose-sm text-gray-700 space-y-3">
                <p className="leading-relaxed">
                  <strong>Commencez</strong> votre tournée depuis <span className="text-blue-700 font-semibold">{route.start_location || 'le centre ville'}</span>.
                </p>

                {/* Génération du texte détaillé pour chaque vélo */}
                {route.detailed_instructions
                  .filter(inst => inst.action === 'collect')
                  .map((instruction, idx) => {
                    const bikeIdShort = instruction.bike_id?.substring(0, 8) || 'N/A'
                    const isLast = idx === route.detailed_instructions.filter(i => i.action === 'collect').length - 1

                    return (
                      <p key={instruction.step} className="leading-relaxed border-l-4 border-blue-400 pl-3 py-1">
                        <span className="font-semibold text-blue-900">Arrêt #{idx + 1}:</span> Récupérez le vélo <span className="font-mono text-purple-700">{bikeIdShort}</span> à la station{' '}
                        <span className="text-indigo-700 font-semibold">{instruction.location}</span>
                        {instruction.priority === 'urgent' && <span className="ml-2 text-red-600 font-bold">(🔴 URGENT)</span>}
                        {instruction.priority === 'high' && <span className="ml-2 text-orange-600 font-bold">(🟠 Prioritaire)</span>}
                        {!isLast ? <span className="text-gray-500">, puis</span> : <span className="text-green-600 font-semibold">.</span>}
                      </p>
                    )
                  })}

                <p className="leading-relaxed mt-4 pt-3 border-t border-blue-200">
                  <strong>🏁 Finalisation:</strong> Après avoir collecté les <span className="text-purple-700 font-bold">{route.total_bikes} vélo{route.total_bikes > 1 ? 's' : ''}</span>,
                  retournez au dépôt pour traitement. Distance totale: <span className="text-green-700 font-bold">{(route.total_distance_meters / 1000).toFixed(1)} km</span>,
                  durée estimée: <span className="text-orange-700 font-bold">{Math.floor(route.estimated_duration_minutes / 60)}h{route.estimated_duration_minutes % 60}min</span>.
                </p>
              </div>
            </div>
          )}

          {/* Detailed Instructions */}
          {route.detailed_instructions && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                📋 Instructions Étape par Étape
              </h3>
              <div className="space-y-2">
                {route.detailed_instructions.map((instruction) => (
                  <div
                    key={instruction.step}
                    className={`flex items-center gap-3 p-3 rounded-lg ${
                      instruction.action === 'start'
                        ? 'bg-green-50 border border-green-200'
                        : instruction.action === 'finish'
                        ? 'bg-blue-50 border border-blue-200'
                        : 'bg-gray-50 border border-gray-200'
                    }`}
                  >
                    <div
                      className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-bold text-white ${
                        instruction.action === 'start'
                          ? 'bg-green-600'
                          : instruction.action === 'finish'
                          ? 'bg-blue-600'
                          : 'bg-gray-600'
                      }`}
                    >
                      {instruction.step}
                    </div>
                    <p className="text-sm font-medium text-gray-800">
                      {instruction.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Map */}
          <div className="h-[500px] rounded-lg overflow-hidden shadow-md">
            <MapContainer
              center={route.waypoints[0] ? [route.waypoints[0].lat, route.waypoints[0].lon] : [45.439695, 4.387178]}
              zoom={13}
              style={{ height: '100%', width: '100%' }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />

              {/* Route line */}
              <Polyline
                positions={route.waypoints.map(wp => [wp.lat, wp.lon] as [number, number])}
                pathOptions={{
                  color: '#3B82F6',
                  weight: 3,
                  opacity: 0.7,
                  dashArray: '10, 10'
                }}
              />

              {/* Waypoint markers */}
              {route.waypoints.map((waypoint, index) => (
                <Marker
                  key={waypoint.intervention_id}
                  position={[waypoint.lat, waypoint.lon]}
                  icon={createNumberedIcon(index + 1, waypoint.priority)}
                >
                  <Popup>
                    <div className="text-sm">
                      <p className="font-bold text-gray-900">Arrêt #{index + 1}</p>
                      <p className="text-xs text-gray-600 mb-2">
                        {waypoint.bike_id ? waypoint.bike_id.substring(0, 8) + '...' : 'N/A'}
                      </p>
                      <p>
                        <span className="font-medium">Priorité:</span>{' '}
                        <span className={`
                          ${waypoint.priority === 'urgent' ? 'text-red-600' : ''}
                          ${waypoint.priority === 'high' ? 'text-orange-600' : ''}
                          ${waypoint.priority === 'medium' ? 'text-blue-600' : ''}
                          ${waypoint.priority === 'low' ? 'text-green-600' : ''}
                          font-semibold
                        `}>
                          {waypoint.priority}
                        </span>
                      </p>
                      {waypoint.station_id && (
                        <p className="text-xs text-gray-600 mt-1">
                          Station: {waypoint.station_id.substring(0, 12)}...
                        </p>
                      )}
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>

          {/* Legend */}
          <div className="bg-white rounded-lg shadow-md p-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Légende des Priorités</h3>
            <div className="flex flex-wrap gap-4 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded-full bg-red-600"></div>
                <span className="text-gray-800">Urgent</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded-full bg-orange-600"></div>
                <span className="text-gray-800">Haute</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded-full bg-blue-600"></div>
                <span className="text-gray-800">Moyenne</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded-full bg-green-600"></div>
                <span className="text-gray-800">Basse</span>
              </div>
            </div>
            <p className="text-xs text-gray-700 mt-2">
              La ligne en pointillés montre le trajet optimal calculé avec l'algorithme du plus proche voisin.
            </p>
          </div>
        </>
      )}
    </div>
  )
}
