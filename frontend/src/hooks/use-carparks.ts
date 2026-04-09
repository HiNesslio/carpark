import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import type { 
  CarParkListResponse, 
  CarParkRefreshResponse, 
  CarParkStatsResponse,
  SortOption 
} from '@/types/carpark'

export function useCarParks(sortBy: SortOption = 'available') {
  return useQuery({
    queryKey: ['carparks', sortBy],
    queryFn: async () => {
      const { data } = await apiClient.get<CarParkListResponse>('/carparks')
      return data
    },
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Auto refresh every 60 seconds
  })
}

export function useCarParkStats() {
  return useQuery({
    queryKey: ['carparks', 'stats'],
    queryFn: async () => {
      const { data } = await apiClient.get<CarParkStatsResponse>('/carparks/stats')
      return data
    },
    staleTime: 30000,
    refetchInterval: 60000,
  })
}

export function useRefreshCarParks() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post<CarParkRefreshResponse>('/carparks/refresh')
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['carparks'] })
    },
  })
}

export function useSortCarParks(carparks: CarParkListResponse['data'] | undefined, sortBy: SortOption) {
  if (!carparks) return []
  
  const sorted = [...carparks]
  
  switch (sortBy) {
    case 'available':
      return sorted.sort((a, b) => b.availableSpaces - a.availableSpaces)
    case 'name':
      return sorted.sort((a, b) => a.name.localeCompare(b.name))
    case 'total':
      return sorted.sort((a, b) => b.totalSpaces - a.totalSpaces)
    default:
      return sorted
  }
}
