export interface CarPark {
  id: string
  name: string
  nameZh: string | null
  address: string | null
  addressZh: string | null
  totalSpaces: number
  availableSpaces: number
  latitude: number | null
  longitude: number | null
  lastUpdated: string
  status: 'available' | 'limited' | 'full'
  occupancyRate: number
}

export interface CarParkStats {
  totalCarParks: number
  totalSpaces: number
  availableSpaces: number
  occupancyRate: number
  statusBreakdown: {
    available: number
    limited: number
    full: number
  }
}

export interface CarParkListResponse {
  success: boolean
  data: CarPark[]
  total: number
}

export interface CarParkRefreshResponse {
  success: boolean
  message: string
  data: CarPark[]
}

export interface CarParkStatsResponse {
  success: boolean
  data: CarParkStats
}

export type SortOption = 'available' | 'name' | 'total'
