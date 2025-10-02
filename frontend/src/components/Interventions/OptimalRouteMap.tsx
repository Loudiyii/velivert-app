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

interface Waypoint {
  intervention_id: string
  order: number
  lat: number
  lon: number
  priority: string
  bike_id?: string
  station_id?: string
}

interface OptimalRoute {
  waypoints: Waypoint[]
  total_distance_meters: number
  estimated_duration_minutes: number
  total_bikes: number
  route_type: string
}

interface OptimalRouteMapProps {
  routeType: 'disabled_bikes' | 'pending_interventions' | 'low_battery'
}

export default function OptimalRouteMap({ routeType }: OptimalRouteMapProps) {
  const [route, setRoute] = useState<OptimalRoute | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  useEffect(() => {
    const fetchRoute = async () => {
      try {
        setLoading(true)
        setError(null)

        const token = localStorage.getItem('auth_token')
        const headers = token ? { 'Authorization': `Bearer ${token}` } : {}

        let endpoint = ''
        switch (routeType) {
          case 'disabled_bikes':
            endpoint = '/api/route-optimization/optimize/disabled-bikes'
            break
          case 'pending_interventions':
            endpoint = '/api/route-optimization/optimize/pending-interventions'
            break
          case 'low_battery':
            endpoint = '/api/route-optimization/optimize/low-battery-bikes'
            break
        }

        const response = await axios.get(`${API_BASE_URL}${endpoint}`, { headers })
        setRoute(response.data)
      } catch (err: any) {
        console.error('Failed to fetch optimal route:', err)
        setError(err.response?.data?.detail || 'Erreur lors du chargement du trajet')
      } finally {
        setLoading(false)
      }
    }

    fetchRoute()
  }, [routeType])

  if (loading) {
    return (
      <div className="h-96 flex items-center justify-center bg-gray-100 rounded-lg">
        <p className="text-gray-500">Calcul du trajet optimal...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="h-96 flex items-center justify-center bg-red-50 rounded-lg">
        <p className="text-red-600">{error}</p>
      </div>
    )
  }

  if (!route || route.waypoints.length === 0) {
    return (
      <div className="h-96 flex items-center justify-center bg-gray-100 rounded-lg">
        <p className="text-gray-500">Aucun trajet à optimiser pour le moment</p>
      </div>
    )
  }

  // Créer la ligne du trajet
  const routeLine = route.waypoints.map(wp => [wp.lat, wp.lon] as [number, number])

  // Couleur selon la priorité
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return '#DC2626'
      case 'high': return '#F59E0B'
      case 'medium': return '#3B82F6'
      case 'low': return '#10B981'
      default: return '#6B7280'
    }
  }

  // Créer des icônes numérotées
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

  const center: [number, number] = route.waypoints.length > 0
    ? [route.waypoints[0].lat, route.waypoints[0].lon]
    : [45.439695, 4.387178]

  return (
    <div>
      {/* Route Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
        <div className="bg-white rounded-lg shadow-md p-4">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Points d'Arrêt</h3>
          <p className="text-2xl font-bold text-blue-600">{route.waypoints.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-4">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Distance Totale</h3>
          <p className="text-2xl font-bold text-green-600">
            {(route.total_distance_meters / 1000).toFixed(1)} km
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-4">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Temps Estimé</h3>
          <p className="text-2xl font-bold text-orange-600">
            {Math.floor(route.estimated_duration_minutes / 60)}h{route.estimated_duration_minutes % 60}min
          </p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-4">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Vélos à Collecter</h3>
          <p className="text-2xl font-bold text-purple-600">{route.total_bikes}</p>
        </div>
      </div>

      {/* Map */}
      <div className="h-[500px] rounded-lg overflow-hidden mb-4">
        <MapContainer center={center} zoom={13} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Route line */}
          <Polyline
            positions={routeLine}
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
            <span>Urgent</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-orange-600"></div>
            <span>Haute</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-blue-600"></div>
            <span>Moyenne</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-green-600"></div>
            <span>Basse</span>
          </div>
        </div>
        <p className="text-xs text-gray-600 mt-2">
          La ligne en pointillés montre le trajet optimal calculé avec l'algorithme du plus proche voisin.
        </p>
      </div>
    </div>
  )
}
