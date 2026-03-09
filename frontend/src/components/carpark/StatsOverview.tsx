import { Car, AlertCircle, CheckCircle } from 'lucide-react'
import type { CarParkStats } from '@/types/carpark'

interface StatsOverviewProps {
  stats: CarParkStats | undefined
  isLoading: boolean
}

export function StatsOverview({ stats, isLoading }: StatsOverviewProps) {
  if (isLoading || !stats) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-card rounded-lg p-4 animate-pulse">
            <div className="h-4 bg-muted rounded w-20 mb-2" />
            <div className="h-8 bg-muted rounded w-16" />
          </div>
        ))}
      </div>
    )
  }

  const statItems = [
    {
      icon: <Car className="w-5 h-5 text-primary" />,
      label: '停車場總數',
      value: stats.totalCarParks,
    },
    {
      icon: <CheckCircle className="w-5 h-5 text-parking-available" />,
      label: '空位充足',
      value: stats.statusBreakdown.available,
    },
    {
      icon: <AlertCircle className="w-5 h-5 text-parking-limited" />,
      label: '空位緊張',
      value: stats.statusBreakdown.limited,
    },
    {
      icon: <AlertCircle className="w-5 h-5 text-parking-full" />,
      label: '已滿',
      value: stats.statusBreakdown.full,
    },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {statItems.map((item, index) => (
        <div 
          key={index} 
          className="bg-card rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow"
        >
          <div className="flex items-center gap-2 mb-2">
            {item.icon}
            <span className="text-sm text-muted-foreground">{item.label}</span>
          </div>
          <div className="font-bold text-2xl tabular-nums">{item.value}</div>
        </div>
      ))}
    </div>
  )
}
