interface IdleBike {
  bike_id: string
  lat: number | null
  lon: number | null
  last_reported: string
  hours_idle: number | null
  current_station_id: string | null
}

interface IdleBikesTableProps {
  bikes: IdleBike[]
}

export default function IdleBikesTable({ bikes }: IdleBikesTableProps) {
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-xl font-semibold text-gray-700 mb-4">Vélos Immobiles</h3>

      {bikes.length === 0 ? (
        <p className="text-gray-500 text-center py-8">Aucun vélo immobile détecté</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ID Vélo
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Station
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Localisation
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Temps d'inactivité
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Dernière activité
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {bikes.map((bike) => (
                <tr key={bike.bike_id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {bike.bike_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {bike.current_station_id || 'En free-floating'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {bike.lat && bike.lon ? `${bike.lat.toFixed(4)}, ${bike.lon.toFixed(4)}` : 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={`px-2 py-1 rounded-full ${
                      (bike.hours_idle || 0) > 48 ? 'bg-red-100 text-red-800' :
                      (bike.hours_idle || 0) > 24 ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {bike.hours_idle ? `${bike.hours_idle.toFixed(1)}h` : 'N/A'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(bike.last_reported).toLocaleString('fr-FR')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {bikes.length > 0 && (
        <div className="mt-4 text-sm text-gray-600">
          {bikes.length} vélo(s) immobile(s) détecté(s)
        </div>
      )}
    </div>
  )
}