import { useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, Polyline, Marker } from 'react-leaflet'
import axios from 'axios'
import L from 'leaflet'

interface TechnicianAssignment {
  technician_id: number
  technician_name: string
  num_interventions: number
  urgent_count: number
  route: {
    waypoints: any[]
    total_distance_meters: number
    estimated_duration_minutes: number
  }
  start_location: {
    lat: number
    lon: number
    name: string
  }
  estimated_duration_minutes: number
  total_distance_km: number
  priority_score: number
}

interface AssignmentResult {
  technician_assignments: TechnicianAssignment[]
  total_technicians: number
  total_interventions: number
  total_distance_km: number
  max_duration_minutes: number
  optimization_algorithm: string
  summary: {
    most_loaded_technician: string
    avg_interventions_per_tech: number
    load_balance_score: number
  }
}

export default function MultiTechnicianAssignment() {
  const [numTechnicians, setNumTechnicians] = useState(3)
  const [technicianNames, setTechnicianNames] = useState('')
  const [routeType, setRouteType] = useState('disabled_bikes')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AssignmentResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selectedTechnicianId, setSelectedTechnicianId] = useState<number | null>(null)

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  const handleAssign = async () => {
    try {
      setLoading(true)
      setError(null)

      const token = localStorage.getItem('auth_token')
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {}

      const names = technicianNames
        .split(',')
        .map(n => n.trim())
        .filter(n => n.length > 0)

      const response = await axios.post(
        `${API_BASE_URL}/api/multi-technician/assign-technicians`,
        {
          num_technicians: numTechnicians,
          technician_names: names.length > 0 ? names : null,
          route_type: routeType
        },
        { headers }
      )

      setResult(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erreur lors de l\'assignation')
    } finally {
      setLoading(false)
    }
  }

  const getTechnicianColor = (index: number) => {
    const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6', '#F97316']
    return colors[index % colors.length]
  }

  const createNumberedIcon = (number: number, color: string) => {
    return L.divIcon({
      html: `
        <div style="
          background-color: ${color};
          width: 32px;
          height: 32px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: bold;
          font-size: 14px;
          border: 3px solid white;
          box-shadow: 0 2px 6px rgba(0,0,0,0.4);
        ">
          T${number}
        </div>
      `,
      className: '',
      iconSize: [32, 32],
      iconAnchor: [16, 16],
    })
  }

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">
          👥 Répartition Multi-Techniciens
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Nombre de techniciens
            </label>
            <input
              type="number"
              min="1"
              max="10"
              value={numTechnicians}
              onChange={(e) => setNumTechnicians(Number(e.target.value))}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Type de mission
            </label>
            <select
              value={routeType}
              onChange={(e) => setRouteType(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
            >
              <option value="disabled_bikes">Vélos désactivés</option>
              <option value="low_battery">Batteries faibles</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Noms techniciens (optionnel, séparés par virgule)
            </label>
            <input
              type="text"
              value={technicianNames}
              onChange={(e) => setTechnicianNames(e.target.value)}
              placeholder="Marc, Julie, Thomas..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900"
            />
          </div>
        </div>

        <button
          onClick={handleAssign}
          disabled={loading}
          className="w-full md:w-auto px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? '⏳ Calcul en cours...' : '🚀 Répartir les interventions'}
        </button>

        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-600">{error}</p>
          </div>
        )}
      </div>

      {/* Results Summary */}
      {result && result.technician_assignments.length > 0 && (
        <>
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg shadow-md p-6 border border-blue-200">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">📊 Résumé de la répartition</h3>

            <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-4">
              <div className="text-center">
                <p className="text-sm text-gray-600">Techniciens</p>
                <p className="text-2xl font-bold text-blue-600">{result.total_technicians}</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600">Interventions totales</p>
                <p className="text-2xl font-bold text-purple-600">{result.total_interventions}</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600">Distance totale</p>
                <p className="text-2xl font-bold text-green-600">{result.total_distance_km} km</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600">Durée max</p>
                <p className="text-2xl font-bold text-orange-600">
                  {Math.floor(result.max_duration_minutes / 60)}h{result.max_duration_minutes % 60}min
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600">Équilibrage</p>
                <p className="text-2xl font-bold text-indigo-600">{result.summary.load_balance_score}%</p>
              </div>
            </div>

            <div className="text-sm text-gray-700 space-y-1">
              <p><strong>Algorithme:</strong> {result.optimization_algorithm}</p>
              <p><strong>Technicien le plus chargé:</strong> {result.summary.most_loaded_technician}</p>
              <p><strong>Moyenne interventions/tech:</strong> {result.summary.avg_interventions_per_tech}</p>
            </div>
          </div>

          {/* Technician Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {result.technician_assignments.map((assignment, idx) => (
              <div
                key={assignment.technician_id}
                className={`bg-white rounded-lg shadow-md p-5 border-l-4 cursor-pointer transition-all hover:shadow-lg ${
                  selectedTechnicianId === assignment.technician_id ? 'ring-2 ring-blue-500 shadow-xl' : ''
                }`}
                style={{ borderLeftColor: getTechnicianColor(idx) }}
                onClick={() => setSelectedTechnicianId(
                  selectedTechnicianId === assignment.technician_id ? null : assignment.technician_id
                )}
              >
                <div className="flex items-center gap-3 mb-3">
                  <div
                    className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold"
                    style={{ backgroundColor: getTechnicianColor(idx) }}
                  >
                    T{idx + 1}
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-800">{assignment.technician_name}</h4>
                    <p className="text-xs text-gray-500">{assignment.start_location.name}</p>
                  </div>
                  <div className="text-blue-600 text-sm">
                    {selectedTechnicianId === assignment.technician_id ? '👁️ Détails' : '👆 Cliquer'}
                  </div>
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Interventions:</span>
                    <span className="font-semibold text-gray-900">{assignment.num_interventions}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Urgents:</span>
                    <span className="font-semibold text-red-600">{assignment.urgent_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Distance:</span>
                    <span className="font-semibold text-green-600">{assignment.total_distance_km} km</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Durée:</span>
                    <span className="font-semibold text-orange-600">
                      {Math.floor(assignment.estimated_duration_minutes / 60)}h{assignment.estimated_duration_minutes % 60}min
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Score priorité:</span>
                    <span className="font-semibold text-indigo-600">{Math.round(assignment.priority_score)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Détails du technicien sélectionné */}
          {selectedTechnicianId !== null && result.technician_assignments.find(a => a.technician_id === selectedTechnicianId) && (
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg shadow-md p-6 border-2 border-blue-300">
              {(() => {
                const selectedAssignment = result.technician_assignments.find(a => a.technician_id === selectedTechnicianId)!
                const techIdx = result.technician_assignments.findIndex(a => a.technician_id === selectedTechnicianId)

                return (
                  <>
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div
                          className="w-12 h-12 rounded-full flex items-center justify-center text-white font-bold text-lg"
                          style={{ backgroundColor: getTechnicianColor(techIdx) }}
                        >
                          T{techIdx + 1}
                        </div>
                        <div>
                          <h3 className="text-xl font-bold text-gray-800">
                            Trajet détaillé - {selectedAssignment.technician_name}
                          </h3>
                          <p className="text-sm text-gray-600">
                            {selectedAssignment.num_interventions} intervention(s) • {selectedAssignment.total_distance_km} km • {Math.floor(selectedAssignment.estimated_duration_minutes / 60)}h{selectedAssignment.estimated_duration_minutes % 60}min
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setSelectedTechnicianId(null)
                        }}
                        className="text-gray-500 hover:text-gray-700 text-xl font-bold"
                      >
                        ✕
                      </button>
                    </div>

                    <div className="prose prose-sm text-gray-700 space-y-3 max-w-none">
                      <p className="leading-relaxed">
                        <strong>🚀 Départ:</strong> Commencez votre tournée depuis{' '}
                        <span className="text-blue-700 font-semibold">{selectedAssignment.start_location.name}</span>.
                      </p>

                      {/* Instructions étape par étape */}
                      {selectedAssignment.route.waypoints.map((waypoint, wpIdx) => {
                        const bikeIdShort = waypoint.bike_id?.substring(0, 8) || 'N/A'
                        const isLast = wpIdx === selectedAssignment.route.waypoints.length - 1
                        const priorityEmoji = waypoint.priority === 'urgent' ? '🔴' : waypoint.priority === 'high' ? '🟠' : '🟡'

                        return (
                          <p key={wpIdx} className="leading-relaxed border-l-4 pl-3 py-1" style={{ borderLeftColor: getTechnicianColor(techIdx) }}>
                            <span className="font-semibold text-blue-900">Arrêt #{wpIdx + 1}:</span> Récupérez le vélo{' '}
                            <span className="font-mono text-purple-700 bg-purple-50 px-1 rounded">{bikeIdShort}</span>
                            {waypoint.station_id && <span className="text-gray-600"> (station {waypoint.station_id.substring(0, 8)}...)</span>}
                            {waypoint.priority === 'urgent' && <span className="ml-2 font-bold text-red-600">{priorityEmoji} URGENT</span>}
                            {waypoint.priority === 'high' && <span className="ml-2 font-bold text-orange-600">{priorityEmoji} Prioritaire</span>}
                            {!isLast ? <span className="text-gray-500">, puis</span> : <span className="text-green-600 font-semibold">.</span>}
                          </p>
                        )
                      })}

                      <p className="leading-relaxed mt-4 pt-3 border-t-2 border-blue-200">
                        <strong>🏁 Finalisation:</strong> Après avoir collecté les{' '}
                        <span className="text-purple-700 font-bold">{selectedAssignment.num_interventions} vélo(s)</span>, retournez au dépôt pour traitement.
                        <br />
                        <span className="text-sm text-gray-600">
                          Distance totale: <span className="text-green-700 font-bold">{selectedAssignment.total_distance_km} km</span> •
                          Durée estimée: <span className="text-orange-700 font-bold">{Math.floor(selectedAssignment.estimated_duration_minutes / 60)}h{selectedAssignment.estimated_duration_minutes % 60}min</span>
                        </span>
                      </p>
                    </div>
                  </>
                )
              })()}
            </div>
          )}

          {/* Map */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">🗺️ Carte des assignations</h3>

            <div className="h-[600px] rounded-lg overflow-hidden">
              <MapContainer
                center={[45.439695, 4.387178]}
                zoom={12}
                style={{ height: '100%', width: '100%' }}
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                {result.technician_assignments.map((assignment, techIdx) => {
                  const color = getTechnicianColor(techIdx)

                  return (
                    <div key={assignment.technician_id}>
                      {/* Start location marker */}
                      <Marker
                        position={[assignment.start_location.lat, assignment.start_location.lon]}
                        icon={createNumberedIcon(techIdx + 1, color)}
                      >
                        <Popup>
                          <div className="text-sm">
                            <p className="font-bold text-gray-900">{assignment.technician_name}</p>
                            <p className="text-xs text-gray-600 mb-2">{assignment.start_location.name}</p>
                            <p><span className="font-medium">Interventions:</span> {assignment.num_interventions}</p>
                            <p><span className="font-medium">Distance:</span> {assignment.total_distance_km} km</p>
                          </div>
                        </Popup>
                      </Marker>

                      {/* Route waypoints */}
                      {assignment.route.waypoints.map((waypoint, wpIdx) => (
                        <CircleMarker
                          key={`${assignment.technician_id}-${wpIdx}`}
                          center={[waypoint.lat, waypoint.lon]}
                          radius={6}
                          pathOptions={{
                            fillColor: color,
                            fillOpacity: 0.7,
                            color: '#fff',
                            weight: 2
                          }}
                        >
                          <Popup>
                            <div className="text-xs">
                              <p className="font-semibold">{assignment.technician_name} - Arrêt {wpIdx + 1}</p>
                              <p className="text-gray-600">{waypoint.bike_id || 'Vélo'}</p>
                            </div>
                          </Popup>
                        </CircleMarker>
                      ))}

                      {/* Route line */}
                      {assignment.route.waypoints.length > 0 && (
                        <Polyline
                          positions={assignment.route.waypoints.map(wp => [wp.lat, wp.lon])}
                          pathOptions={{
                            color: color,
                            weight: 3,
                            opacity: 0.6,
                            dashArray: '5, 10'
                          }}
                        />
                      )}
                    </div>
                  )
                })}
              </MapContainer>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
