import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet'
import { Icon, LatLngExpression } from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { StationStatus, Bike } from '../../types'

// Fix Leaflet default icon issue with Vite
import icon from 'leaflet/dist/images/marker-icon.png'
import iconShadow from 'leaflet/dist/images/marker-shadow.png'

let DefaultIcon = new Icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41]
})

interface RealtimeMapProps {
  stations: StationStatus[]
  bikes: Bike[]
  center?: LatLngExpression
  zoom?: number
}

export default function RealtimeMap({
  stations,
  bikes,
  center = [45.44, 4.39], // Saint-Étienne coordinates
  zoom = 13
}: RealtimeMapProps) {
  const [selectedStation, setSelectedStation] = useState<StationStatus | null>(null)

  const getStationColor = (station: StationStatus): string => {
    if (!station.is_renting || !station.is_installed) return '#gray'

    const occupancy = station.num_bikes_available / station.capacity
    if (occupancy > 0.5) return '#22c55e' // green
    if (occupancy > 0.2) return '#eab308' // yellow
    return '#ef4444' // red
  }

  const getStationRadius = (capacity: number): number => {
    // Scale radius based on station capacity
    return Math.min(Math.max(capacity * 2, 30), 80)
  }

  return (
    <MapContainer
      center={center}
      zoom={zoom}
      style={{ height: '100%', width: '100%', minHeight: '500px' }}
      className="rounded-lg shadow-lg"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {/* Render stations as circles */}
      {stations.map((station) => (
        <Circle
          key={station.station_id}
          center={[station.lat, station.lon]}
          radius={getStationRadius(station.capacity)}
          pathOptions={{
            fillColor: getStationColor(station),
            fillOpacity: 0.6,
            color: getStationColor(station),
            weight: 2
          }}
          eventHandlers={{
            click: () => setSelectedStation(station)
          }}
        >
          <Popup>
            <div className="p-2">
              <h3 className="font-bold text-lg mb-2">{station.name}</h3>
              <div className="space-y-1 text-sm">
                <p>
                  <span className="font-semibold">Vélos disponibles:</span>{' '}
                  <span className={station.num_bikes_available > 0 ? 'text-green-600' : 'text-red-600'}>
                    {station.num_bikes_available}
                  </span>
                </p>
                <p>
                  <span className="font-semibold">Places disponibles:</span>{' '}
                  {station.num_docks_available}
                </p>
                <p>
                  <span className="font-semibold">Capacité totale:</span> {station.capacity}
                </p>
                <p>
                  <span className="font-semibold">Taux d'occupation:</span>{' '}
                  {station.occupancy_rate
                    ? `${(station.occupancy_rate * 100).toFixed(0)}%`
                    : 'N/A'}
                </p>
                {!station.is_renting && (
                  <p className="text-red-600 font-semibold">⚠️ Hors service</p>
                )}
              </div>
            </div>
          </Popup>
        </Circle>
      ))}

      {/* Render bikes as markers */}
      {bikes.map((bike) => (
        <Marker
          key={bike.bike_id}
          position={[bike.lat || 0, bike.lon || 0]}
          icon={DefaultIcon}
        >
          <Popup>
            <div className="p-2">
              <h3 className="font-bold mb-1">🚲 Vélo {bike.bike_id}</h3>
              <div className="text-sm">
                {bike.is_disabled && <p className="text-red-600">❌ Désactivé</p>}
                {bike.is_reserved && <p className="text-orange-600">🔒 Réservé</p>}
                {bike.current_range_meters && (
                  <p>Autonomie: {(bike.current_range_meters / 1000).toFixed(1)} km</p>
                )}
              </div>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  )
}