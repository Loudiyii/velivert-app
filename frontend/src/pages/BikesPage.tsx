import { useEffect, useState } from 'react'
import { bikesApi } from '../services/api'
import RefreshIndicator from '../components/RefreshIndicator'

interface Bike {
  bike_id: string
  vehicle_type_id: string
  current_station_id: string | null
  lat: string | number
  lon: string | number
  is_reserved: boolean
  is_disabled: boolean
  current_range_meters: number | null
  last_reported: string
}

export default function BikesPage() {
  const [bikes, setBikes] = useState<Bike[]>([])
  const [loading, setLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastRefresh, setLastRefresh] = useState<Date>()
  const [filterStatus, setFilterStatus] = useState<'all' | 'available' | 'disabled' | 'in_circulation'>('all')
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    const fetchBikes = async (isAutoRefresh = false) => {
      try {
        if (isAutoRefresh) {
          setIsRefreshing(true)
        } else {
          setLoading(true)
        }
        const response = await bikesApi.getCurrentStatus()
        setBikes(response.data)
        setLastRefresh(new Date())
      } catch (error) {
        console.error('Failed to fetch bikes:', error)
      } finally {
        setLoading(false)
        setIsRefreshing(false)
      }
    }

    fetchBikes(false)
    // Refresh every 30 seconds
    const interval = setInterval(() => fetchBikes(true), 30000)
    return () => clearInterval(interval)
  }, [])

  const filteredBikes = bikes.filter(bike => {
    // Status filter
    if (filterStatus === 'available' && (bike.is_disabled || bike.is_reserved)) return false
    if (filterStatus === 'disabled' && !bike.is_disabled) return false
    if (filterStatus === 'in_circulation' && (bike.current_station_id !== null && bike.current_station_id !== '')) return false

    // Search filter
    if (searchTerm && !bike.bike_id.toLowerCase().includes(searchTerm.toLowerCase())) return false

    return true
  })

  const availableBikes = bikes.filter(b => !b.is_disabled && !b.is_reserved).length
  const disabledBikes = bikes.filter(b => b.is_disabled).length
  const reservedBikes = bikes.filter(b => b.is_reserved).length
  const inCirculationBikes = bikes.filter(b => !b.current_station_id || b.current_station_id === '').length

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Vélos</h1>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Total Vélos</h3>
          <p className="text-3xl font-bold text-blue-600">{bikes.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Disponibles</h3>
          <p className="text-3xl font-bold text-green-600">{availableBikes}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-1">En Circulation</h3>
          <p className="text-3xl font-bold text-purple-600">{inCirculationBikes}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Désactivés</h3>
          <p className="text-3xl font-bold text-red-600">{disabledBikes}</p>
        </div>
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-1">Réservés</h3>
          <p className="text-3xl font-bold text-orange-600">{reservedBikes}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-6">
        <div className="flex gap-4">
          <input
            type="text"
            placeholder="Rechercher un vélo..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <select
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 text-gray-900 bg-white"
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as any)}
          >
            <option value="all">Tous</option>
            <option value="available">Disponibles</option>
            <option value="in_circulation">En Circulation</option>
            <option value="disabled">Désactivés</option>
          </select>
        </div>
        <div className="mt-2 text-sm text-gray-600">
          {filteredBikes.length} vélo(s) affiché(s)
        </div>
      </div>

      {/* Bikes List */}
      <div className="bg-white rounded-lg shadow-md p-6">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <p className="text-gray-500">Chargement des vélos...</p>
          </div>
        ) : filteredBikes.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Aucun vélo trouvé</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Station</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Position</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Autonomie</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Statut</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredBikes.map((bike) => (
                  <tr key={bike.bike_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                      {bike.bike_id.substring(0, 8)}...
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      Type {bike.vehicle_type_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {bike.current_station_id ? (
                        <span className="text-blue-600">{bike.current_station_id.substring(0, 12)}...</span>
                      ) : (
                        <span className="text-gray-400">En circulation</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {Number(bike.lat).toFixed(4)}, {Number(bike.lon).toFixed(4)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {bike.current_range_meters
                        ? `${(bike.current_range_meters / 1000).toFixed(1)} km`
                        : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {bike.is_disabled ? (
                        <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800">
                          Désactivé
                        </span>
                      ) : bike.is_reserved ? (
                        <span className="px-2 py-1 text-xs rounded-full bg-orange-100 text-orange-800">
                          Réservé
                        </span>
                      ) : (
                        <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">
                          Disponible
                        </span>
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