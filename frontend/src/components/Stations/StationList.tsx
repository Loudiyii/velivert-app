import { useState } from 'react'
import { StationStatus } from '../../types'

interface StationListProps {
  stations: StationStatus[]
  onStationClick?: (station: StationStatus) => void
}

export default function StationList({ stations, onStationClick }: StationListProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all')
  const [sortBy, setSortBy] = useState<'name' | 'bikes' | 'occupancy'>('name')

  const filteredStations = stations
    .filter((station) => {
      // Search filter
      const matchesSearch = station.name.toLowerCase().includes(searchTerm.toLowerCase())

      // Status filter
      const matchesStatus =
        statusFilter === 'all' ||
        (statusFilter === 'active' && station.is_renting) ||
        (statusFilter === 'inactive' && !station.is_renting)

      return matchesSearch && matchesStatus
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name)
        case 'bikes':
          return b.num_bikes_available - a.num_bikes_available
        case 'occupancy':
          const occA = a.occupancy_rate || 0
          const occB = b.occupancy_rate || 0
          return occB - occA
        default:
          return 0
      }
    })

  const getOccupancyColor = (rate?: number): string => {
    if (!rate) return 'bg-gray-500'
    if (rate > 0.7) return 'bg-green-500'
    if (rate > 0.3) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow-md space-y-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <input
              type="text"
              placeholder="Rechercher une station..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          {/* Status Filter */}
          <select
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
          >
            <option value="all">Toutes les stations</option>
            <option value="active">Actives</option>
            <option value="inactive">Inactives</option>
          </select>

          {/* Sort */}
          <select
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
          >
            <option value="name">Trier par nom</option>
            <option value="bikes">Trier par vélos disponibles</option>
            <option value="occupancy">Trier par occupation</option>
          </select>
        </div>

        <div className="text-sm text-gray-600">
          {filteredStations.length} station(s) trouvée(s)
        </div>
      </div>

      {/* Station List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredStations.map((station) => (
          <div
            key={station.station_id}
            className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow cursor-pointer"
            onClick={() => onStationClick?.(station)}
          >
            <div className="flex items-start justify-between mb-3">
              <h3 className="font-semibold text-lg text-gray-800">{station.name}</h3>
              {!station.is_renting && (
                <span className="px-2 py-1 bg-red-100 text-red-600 text-xs rounded-full">
                  Hors service
                </span>
              )}
            </div>

            <div className="space-y-2">
              {/* Bikes Available */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Vélos disponibles</span>
                <span className={`font-bold ${station.num_bikes_available > 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {station.num_bikes_available}
                </span>
              </div>

              {/* Docks Available */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Places disponibles</span>
                <span className="font-bold text-gray-800">{station.num_docks_available}</span>
              </div>

              {/* Capacity */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Capacité totale</span>
                <span className="font-bold text-gray-800">{station.capacity}</span>
              </div>

              {/* Occupancy Bar */}
              {station.occupancy_rate !== undefined && (
                <div>
                  <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                    <span>Occupation</span>
                    <span>{(station.occupancy_rate * 100).toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${getOccupancyColor(station.occupancy_rate)}`}
                      style={{ width: `${station.occupancy_rate * 100}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {filteredStations.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          Aucune station trouvée
        </div>
      )}
    </div>
  )
}