import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet'
import { Icon, DivIcon } from 'leaflet'
import { StationStatus } from '../../types'
import 'leaflet/dist/leaflet.css'

interface StationMapProps {
  stations: StationStatus[]
  onStationClick?: (station: StationStatus) => void
}

export default function StationMap({ stations, onStationClick }: StationMapProps) {
  // Center on Saint-Étienne
  const center: [number, number] = [45.4397, 4.3872]

  const createCustomIcon = (station: StationStatus) => {
    const bikesAvailable = station.num_bikes_available
    const isActive = station.is_renting && station.is_installed

    // Color based on bike availability
    let bgColor = 'bg-gray-400' // No bikes or inactive
    if (!isActive) {
      bgColor = 'bg-red-500'
    } else if (bikesAvailable === 0) {
      bgColor = 'bg-orange-500'
    } else if (bikesAvailable < 5) {
      bgColor = 'bg-yellow-500'
    } else {
      bgColor = 'bg-green-500'
    }

    return new DivIcon({
      className: 'custom-marker',
      html: `
        <div class="flex flex-col items-center transform -translate-x-1/2 -translate-y-full">
          <div class="${bgColor} rounded-full w-12 h-12 flex items-center justify-center shadow-lg border-2 border-white">
            <span class="text-white font-bold text-sm">${bikesAvailable}</span>
          </div>
          <div class="w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-t-[8px] border-t-white -mt-1"></div>
        </div>
      `,
      iconSize: [48, 56],
      iconAnchor: [24, 56],
      popupAnchor: [0, -56],
    })
  }

  return (
    <div className="relative w-full h-[600px] rounded-lg overflow-hidden shadow-lg">
      <MapContainer
        center={center}
        zoom={13}
        className="w-full h-full"
        zoomControl={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {stations.map((station) => {
          if (!station.lat || !station.lon) return null

          return (
            <Marker
              key={station.station_id}
              position={[station.lat, station.lon]}
              icon={createCustomIcon(station)}
              eventHandlers={{
                click: () => onStationClick?.(station),
              }}
            >
              <Popup>
                <div className="min-w-[200px] p-2">
                  <h3 className="font-bold text-lg mb-2 text-gray-800">{station.name}</h3>

                  <div className="space-y-2">
                    {/* Status */}
                    {!station.is_renting && (
                      <div className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded-full text-center">
                        Hors service
                      </div>
                    )}

                    {/* Bikes Available */}
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">🚲 Vélos disponibles:</span>
                      <span className={`font-bold ${station.num_bikes_available > 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {station.num_bikes_available}
                      </span>
                    </div>

                    {/* Docks Available */}
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">🅿 Places libres:</span>
                      <span className="font-bold text-blue-600">{station.num_docks_available}</span>
                    </div>

                    {/* Capacity */}
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Capacité totale:</span>
                      <span className="font-bold text-gray-700">{station.capacity}</span>
                    </div>

                    {/* Occupancy Bar */}
                    {station.occupancy_rate !== undefined && (
                      <div className="mt-3">
                        <div className="flex justify-between text-xs text-gray-600 mb-1">
                          <span>Taux d'occupation</span>
                          <span className="font-semibold">{(station.occupancy_rate * 100).toFixed(0)}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2.5">
                          <div
                            className={`h-2.5 rounded-full ${
                              station.occupancy_rate > 0.7
                                ? 'bg-green-500'
                                : station.occupancy_rate > 0.3
                                ? 'bg-yellow-500'
                                : 'bg-red-500'
                            }`}
                            style={{ width: `${station.occupancy_rate * 100}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </Popup>
            </Marker>
          )
        })}
      </MapContainer>

      {/* Legend */}
      <div className="absolute bottom-4 right-4 bg-white rounded-lg shadow-lg p-4 z-[1000]">
        <h4 className="font-semibold text-sm text-gray-800 mb-2">Légende</h4>
        <div className="space-y-1.5 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-green-500"></div>
            <span className="text-gray-700">≥5 vélos disponibles</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-yellow-500"></div>
            <span className="text-gray-700">1-4 vélos disponibles</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-orange-500"></div>
            <span className="text-gray-700">Aucun vélo disponible</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-red-500"></div>
            <span className="text-gray-700">Station hors service</span>
          </div>
        </div>
      </div>
    </div>
  )
}
