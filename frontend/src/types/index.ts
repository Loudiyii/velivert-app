// Station types
export interface Station {
  id: string
  name: string
  lat: number
  lon: number
  address?: string
  capacity: number
  region_id?: string
  rental_methods?: string[]
  is_virtual_station: boolean
  created_at: string
  updated_at: string
}

export interface StationStatus {
  station_id: string
  name: string
  lat: number
  lon: number
  capacity: number
  num_bikes_available: number
  num_bikes_disabled: number
  num_docks_available: number
  num_docks_disabled: number
  is_installed: boolean
  is_renting: boolean
  is_returning: boolean
  last_reported: string
  occupancy_rate?: number
}

// Bike types
export interface Bike {
  bike_id: string
  vehicle_type_id?: string
  current_station_id?: string
  lat?: number
  lon?: number
  is_reserved: boolean
  is_disabled: boolean
  current_range_meters?: number
  last_reported?: string
  created_at: string
  updated_at: string
}

// Intervention types
export type InterventionType = 'repair' | 'relocation' | 'battery_swap' | 'other'
export type InterventionPriority = 'low' | 'medium' | 'high' | 'urgent'
export type InterventionStatus = 'pending' | 'in_progress' | 'completed' | 'cancelled'

export interface Intervention {
  id: string
  bike_id?: string
  station_id?: string
  technician_id?: string
  intervention_type: InterventionType
  priority: InterventionPriority
  status: InterventionStatus
  description?: string
  scheduled_at?: string
  started_at?: string
  completed_at?: string
  notes?: string
  created_at: string
  updated_at: string
}

// Route types
export interface Waypoint {
  intervention_id: string
  order: number
  lat: number
  lon: number
  estimated_arrival?: string
  completed: boolean
}

export interface OptimizedRoute {
  id: string
  technician_id: string
  date: string
  waypoints: Waypoint[]
  total_distance_meters?: number
  estimated_duration_minutes?: number
  status: string
  optimization_algorithm?: string
  created_at: string
  updated_at: string
}