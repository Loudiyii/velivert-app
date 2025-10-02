import { useEffect, useState } from 'react'
import { interventionsApi, bikesApi } from '../services/api'
import RefreshIndicator from '../components/RefreshIndicator'
import DataRefreshStatus from '../components/DataRefreshStatus'
import OptimalRouteMap from '../components/Interventions/OptimalRouteMap'
import DetailedRouteOptimizer from '../components/Interventions/DetailedRouteOptimizer'
import MultiTechnicianAssignment from '../components/Interventions/MultiTechnicianAssignment'

interface Intervention {
  id: string
  bike_id: string | null
  station_id: string | null
  intervention_type: string
  priority: string
  status: string
  description: string | null
  scheduled_at: string | null
  started_at: string | null
  completed_at: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

interface SuspectBike {
  bike_id: string
  reason: string
  priority: 'urgent' | 'high' | 'medium'
  is_disabled: boolean
  current_range_meters: number | null
  current_station_id: string | null
}

export default function InterventionsPage() {
  const [interventions, setInterventions] = useState<Intervention[]>([])
  const [suspectBikes, setSuspectBikes] = useState<SuspectBike[]>([])
  const [loading, setLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastRefresh, setLastRefresh] = useState<Date>()
  const [showForm, setShowForm] = useState(false)
  const [showAlerts, setShowAlerts] = useState(true)
  const [showOptimalRoute, setShowOptimalRoute] = useState(false)
  const [useDetailedOptimizer, setUseDetailedOptimizer] = useState(true)
  const [routeType, setRouteType] = useState<'disabled_bikes' | 'pending_interventions' | 'low_battery'>('disabled_bikes')
  const [formData, setFormData] = useState({
    bike_id: '',
    station_id: '',
    intervention_type: 'repair',
    priority: 'medium',
    description: '',
    scheduled_at: ''
  })

  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [filterPriority, setFilterPriority] = useState<string>('all')

  useEffect(() => {
    const loadData = async (isAutoRefresh = false) => {
      if (isAutoRefresh) {
        setIsRefreshing(true)
      }
      await Promise.all([fetchInterventions(), detectSuspectBikes()])
      setLastRefresh(new Date())
      setIsRefreshing(false)
    }

    loadData(false)

    // Auto-refresh every 30 seconds
    const interval = setInterval(() => loadData(true), 30000)

    return () => clearInterval(interval)
  }, [filterStatus, filterPriority])

  const detectSuspectBikes = async () => {
    try {
      const response = await bikesApi.getCurrentStatus()
      const bikes = response.data

      const suspects: SuspectBike[] = []

      bikes.forEach((bike: any) => {
        // Critère 1: Vélo désactivé
        if (bike.is_disabled) {
          suspects.push({
            bike_id: bike.bike_id,
            reason: 'Vélo désactivé - nécessite inspection',
            priority: 'high',
            is_disabled: bike.is_disabled,
            current_range_meters: bike.current_range_meters,
            current_station_id: bike.current_station_id
          })
        }
        // Critère 2: Autonomie critique (< 5 km)
        else if (bike.current_range_meters && bike.current_range_meters < 5000) {
          suspects.push({
            bike_id: bike.bike_id,
            reason: `Autonomie critique: ${(bike.current_range_meters / 1000).toFixed(1)} km`,
            priority: 'high',
            is_disabled: bike.is_disabled,
            current_range_meters: bike.current_range_meters,
            current_station_id: bike.current_station_id
          })
        }
        // Critère 3: Batterie vide
        else if (bike.current_range_meters === 0) {
          suspects.push({
            bike_id: bike.bike_id,
            reason: 'Batterie vide - recharge nécessaire',
            priority: 'urgent',
            is_disabled: bike.is_disabled,
            current_range_meters: bike.current_range_meters,
            current_station_id: bike.current_station_id
          })
        }
      })

      // Trier par priorité
      suspects.sort((a, b) => {
        const priorityOrder = { urgent: 0, high: 1, medium: 2 }
        return priorityOrder[a.priority] - priorityOrder[b.priority]
      })

      setSuspectBikes(suspects)
    } catch (error) {
      console.error('Failed to detect suspect bikes:', error)
    }
  }

  const fetchInterventions = async () => {
    try {
      setLoading(true)
      const params: any = {}
      if (filterStatus !== 'all') params.status = filterStatus
      if (filterPriority !== 'all') params.priority = filterPriority

      const response = await interventionsApi.getAll(params)
      setInterventions(response.data)
    } catch (error) {
      console.error('Failed to fetch interventions:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      // Ensure at least bike_id or station_id is provided
      if (!formData.bike_id && !formData.station_id) {
        alert('Veuillez fournir un ID de vélo ou de station')
        return
      }

      const payload: any = {
        intervention_type: formData.intervention_type,
        priority: formData.priority,
        description: formData.description || undefined,
        scheduled_at: formData.scheduled_at || undefined
      }

      if (formData.bike_id) payload.bike_id = formData.bike_id
      if (formData.station_id) payload.station_id = formData.station_id

      await interventionsApi.create(payload)
      setShowForm(false)
      setFormData({
        bike_id: '',
        station_id: '',
        intervention_type: 'repair',
        priority: 'medium',
        description: '',
        scheduled_at: ''
      })
      fetchInterventions()
    } catch (error) {
      console.error('Failed to create intervention:', error)
      alert('Erreur lors de la création de l\'intervention')
    }
  }

  const updateStatus = async (id: string, newStatus: string) => {
    try {
      await interventionsApi.update(id, { status: newStatus })
      fetchInterventions()
    } catch (error) {
      console.error('Failed to update intervention:', error)
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'bg-red-100 text-red-800'
      case 'high': return 'bg-orange-100 text-orange-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'low': return 'bg-green-100 text-green-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800'
      case 'in_progress': return 'bg-blue-100 text-blue-800'
      case 'pending': return 'bg-gray-100 text-gray-800'
      case 'cancelled': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const createInterventionFromAlert = (bike: SuspectBike) => {
    setFormData({
      bike_id: bike.bike_id,
      station_id: bike.current_station_id || '',
      intervention_type: bike.current_range_meters === 0 ? 'battery_swap' : 'repair',
      priority: bike.priority,
      description: bike.reason,
      scheduled_at: ''
    })
    setShowForm(true)
    setShowAlerts(false)
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">Interventions de Maintenance</h1>
        <div className="flex gap-4 items-center">
          <DataRefreshStatus lastRefresh={lastRefresh} isRefreshing={isRefreshing} />
          <button
            onClick={() => setShowOptimalRoute(!showOptimalRoute)}
            className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg"
          >
            {showOptimalRoute ? 'Masquer' : '🗺️ Optimisation'}
          </button>
        </div>
      </div>

      {/* Optimisation Multi-Techniciens */}
      {showOptimalRoute && (
        <div className="mb-6">
          <MultiTechnicianAssignment />
        </div>
      )}

      {/* Alertes Vélos Suspects */}
      {showAlerts && suspectBikes.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-700">
                🚨 Alertes: Vélos Nécessitant une Intervention
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                {suspectBikes.length} vélo(s) suspect(s) détecté(s) automatiquement
              </p>
            </div>
            <button
              onClick={() => setShowAlerts(false)}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>

          <div className="space-y-3">
            {suspectBikes.slice(0, 10).map((bike) => (
              <div
                key={bike.bike_id}
                className={`border-l-4 p-4 rounded-r-lg ${
                  bike.priority === 'urgent'
                    ? 'bg-red-50 border-red-500'
                    : bike.priority === 'high'
                    ? 'bg-orange-50 border-orange-500'
                    : 'bg-yellow-50 border-yellow-500'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-semibold text-gray-800">
                        {bike.bike_id.substring(0, 12)}...
                      </span>
                      <span
                        className={`px-2 py-1 text-xs rounded-full ${
                          bike.priority === 'urgent'
                            ? 'bg-red-100 text-red-800'
                            : bike.priority === 'high'
                            ? 'bg-orange-100 text-orange-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}
                      >
                        {bike.priority === 'urgent' ? 'URGENT' : bike.priority === 'high' ? 'HAUTE' : 'MOYENNE'}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 mt-1">{bike.reason}</p>
                    {bike.current_station_id && (
                      <p className="text-xs text-gray-500 mt-1">
                        📍 Station: {bike.current_station_id.substring(0, 15)}...
                      </p>
                    )}
                  </div>
                  <button
                    onClick={() => createInterventionFromAlert(bike)}
                    className="ml-4 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                  >
                    Créer Intervention
                  </button>
                </div>
              </div>
            ))}
            {suspectBikes.length > 10 && (
              <p className="text-sm text-gray-500 text-center pt-2">
                ... et {suspectBikes.length - 10} autre(s) vélo(s)
              </p>
            )}
          </div>
        </div>
      )}

      {/* Create Form */}
      {showForm && (
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-700 mb-4">Créer une Intervention</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ID Vélo (optionnel si station fournie)
                </label>
                <input
                  type="text"
                  value={formData.bike_id}
                  onChange={(e) => setFormData({ ...formData, bike_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white"
                  placeholder="BIKE001"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ID Station (optionnel si vélo fourni)
                </label>
                <input
                  type="text"
                  value={formData.station_id}
                  onChange={(e) => setFormData({ ...formData, station_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white"
                  placeholder="SE001"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                <select
                  value={formData.intervention_type}
                  onChange={(e) => setFormData({ ...formData, intervention_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white"
                >
                  <option value="repair">Réparation</option>
                  <option value="relocation">Relocalisation</option>
                  <option value="battery_swap">Changement de batterie</option>
                  <option value="maintenance">Maintenance</option>
                  <option value="cleaning">Nettoyage</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Priorité</label>
                <select
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white"
                >
                  <option value="low">Basse</option>
                  <option value="medium">Moyenne</option>
                  <option value="high">Haute</option>
                  <option value="urgent">Urgente</option>
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white"
                  rows={3}
                  placeholder="Description de l'intervention..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Planification</label>
                <input
                  type="datetime-local"
                  value={formData.scheduled_at}
                  onChange={(e) => setFormData({ ...formData, scheduled_at: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white"
                />
              </div>
            </div>
            <div className="flex justify-end">
              <button
                type="submit"
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg"
              >
                Créer l'intervention
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="flex gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Statut</label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white"
            >
              <option value="all">Tous</option>
              <option value="pending">En attente</option>
              <option value="in_progress">En cours</option>
              <option value="completed">Terminé</option>
              <option value="cancelled">Annulé</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Priorité</label>
            <select
              value={filterPriority}
              onChange={(e) => setFilterPriority(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white"
            >
              <option value="all">Toutes</option>
              <option value="urgent">Urgente</option>
              <option value="high">Haute</option>
              <option value="medium">Moyenne</option>
              <option value="low">Basse</option>
            </select>
          </div>
        </div>
      </div>

      {/* Interventions List */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-700 mb-4">
          Liste des Interventions ({interventions.length})
        </h2>

        {loading ? (
          <div className="text-center py-8">
            <p className="text-gray-500">Chargement...</p>
          </div>
        ) : interventions.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500">Aucune intervention trouvée</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Cible</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Priorité</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Statut</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Planification</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {interventions.map((intervention) => (
                  <tr key={intervention.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {intervention.id.substring(0, 8)}...
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {intervention.bike_id && `🚲 ${intervention.bike_id}`}
                      {intervention.station_id && `🅿 ${intervention.station_id}`}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {intervention.intervention_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full ${getPriorityColor(intervention.priority)}`}>
                        {intervention.priority}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(intervention.status)}`}>
                        {intervention.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {intervention.scheduled_at ? new Date(intervention.scheduled_at).toLocaleDateString('fr-FR') : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {intervention.status === 'pending' && (
                        <button
                          onClick={() => updateStatus(intervention.id, 'in_progress')}
                          className="text-blue-600 hover:text-blue-800 mr-2"
                        >
                          Démarrer
                        </button>
                      )}
                      {intervention.status === 'in_progress' && (
                        <button
                          onClick={() => updateStatus(intervention.id, 'completed')}
                          className="text-green-600 hover:text-green-800 mr-2"
                        >
                          Terminer
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <RefreshIndicator isRefreshing={isRefreshing} lastRefresh={lastRefresh} />
    </div>
  )
}