import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'

interface OccupancyData {
  timestamp?: string
  time?: string
  occupancy_rate?: number
  average_bikes_available?: number
  avg_bikes_available?: number
  min_bikes_available?: number
  max_bikes_available?: number
}

interface OccupancyChartProps {
  data: OccupancyData[]
  stationName?: string
}

export default function OccupancyChart({ data, stationName }: OccupancyChartProps) {
  // Transform data to ensure consistent format
  const chartData = data.map(item => ({
    time: item.timestamp || item.time || '',
    occupancy_rate: (item.occupancy_rate || 0) * 100, // Convert to percentage
    avg_bikes_available: item.average_bikes_available || item.avg_bikes_available || 0,
    min_bikes_available: item.min_bikes_available,
    max_bikes_available: item.max_bikes_available
  }))

  console.log('[OccupancyChart] Data points:', chartData.length, 'Sample:', chartData[0])

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xl font-semibold text-gray-700">
          {stationName ? `Occupation - ${stationName}` : 'Taux d\'Occupation des Stations'}
        </h3>
        <span className="text-sm text-gray-500">
          {chartData.length} points de données
        </span>
      </div>

      {chartData.length === 0 ? (
        <div className="flex items-center justify-center h-64 bg-gray-50 rounded text-gray-500">
          ⚠️ Aucune donnée disponible pour la période sélectionnée
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="time"
              tickFormatter={(value) => new Date(value).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
            />
            <YAxis
              yAxisId="left"
              label={{ value: 'Taux d\'occupation (%)', angle: -90, position: 'insideLeft' }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              label={{ value: 'Vélos disponibles', angle: 90, position: 'insideRight' }}
            />
            <Tooltip
              labelFormatter={(value) => new Date(value).toLocaleString('fr-FR')}
              formatter={(value: number, name: string) => {
                if (name === 'Taux d\'occupation') return [`${value.toFixed(1)}%`, name]
                return [`${value.toFixed(1)} vélos`, name]
              }}
            />
            <Legend />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="occupancy_rate"
              stroke="#8b5cf6"
              name="Taux d'occupation"
              strokeWidth={2}
              dot={false}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="avg_bikes_available"
              stroke="#3b82f6"
              name="Vélos disponibles"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}