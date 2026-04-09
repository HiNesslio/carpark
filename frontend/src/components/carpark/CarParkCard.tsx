import { cva, type VariantProps } from 'class-variance-authorority'
import type { CarPark } from '@/types/carpark'

const statusVariants = cva(
  'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium',
  {
    variants: {
      status: {
        available: 'text-parking-available',
        limited: 'text-parking-limited',
        full: 'text-parking-full',
      },
    },
    defaultVariants: {
      status: 'available',
    },
  }
)

const indicatorVariants = cva(
  'w-2 h-2 rounded-full',
  {
    variants: {
      status: {
        available: 'bg-parking-available animate-pulse',
        limited: 'bg-parking-limited',
        full: 'bg-parking-full',
      },
    },
  }
)

interface CarParkCardProps {
  carpark: CarPark
}

const statusLabels = {
  available: '空位充足',
  limited: '空位緊張',
  full: '已滿',
}

const statusBgColors = {
  available: 'rgba(72, 187, 120, 0.15)',
  limited: 'rgba(237, 137, 54, 0.15)',
  full: 'rgba(229, 62, 62, 0.15)',
}

function formatTime(isoString: string) {
  const date = new Date(isoString)
  return date.toLocaleTimeString('zh-MO', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function CarParkCard({ carpark }: CarParkCardProps) {
  const displayName = carpark.nameZh || carpark.name
  const displayAddress = carpark.addressZh || carpark.address
  const statusColor = `var(--parking-${carpark.status})`

  return (
    <div 
      className="relative bg-card rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-200"
      style={{ paddingLeft: 'var(--spacing-sm)' }}
    >
      <div 
        className="absolute left-0 top-0 bottom-0 w-1 rounded-l-lg"
        style={{ backgroundColor: statusColor }}
      />
      
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <h3 className="font-semibold text-foreground" style={{ fontSize: 'var(--font-size-title)' }}>
            {displayName}
          </h3>
          <span 
            className={statusVariants({ status: carpark.status })}
            style={{ backgroundColor: statusBgColors[carpark.status] }}
          >
            <span className={indicatorVariants({ status: carpark.status })} />
            {statusLabels[carpark.status]}
          </span>
        </div>

        {/* Address */}
        {displayAddress && (
          <p className="text-muted-foreground text-sm mb-4 line-clamp-2">
            {displayAddress}
          </p>
        )}

        {/* Stats */}
        <div className="grid grid-cols-2 gap-3 mb-3">
          <div className="bg-muted/50 rounded-md p-2">
            <div className="text-muted-foreground text-xs mb-0.5">剩餘車位</div>
            <div 
              className="font-bold tabular-nums" 
              style={{ fontSize: 'var(--font-size-headline)', color: statusColor }}
            >
              {carpark.availableSpaces}
            </div>
          </div>
          <div className="bg-muted/50 rounded-md p-2">
            <div className="text-muted-foreground text-xs mb-0.5">總車位</div>
            <div className="font-bold tabular-nums text-foreground" style={{ fontSize: 'var(--font-size-headline)' }}>
              {carpark.totalSpaces}
            </div>
          </div>
        </div>

        {/* Progress bar */}
        <div className="mb-2">
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div 
              className="h-full rounded-full transition-all duration-500"
              style={{ 
                width: `${carpark.occupancyRate}%`,
                backgroundColor: statusColor
              }}
            />
          </div>
          <div className="flex justify-between mt-1 text-xs text-muted-foreground">
            <span>使用率</span>
            <span className="tabular-nums">{carpark.occupancyRate}%</span>
          </div>
        </div>

        {/* Last updated */}
        <div className="text-xs text-muted-foreground text-right">
          更新時間: {formatTime(carpark.lastUpdated)}
        </div>
      </div>
    </div>
  )
}

export type { CarParkCardProps }
