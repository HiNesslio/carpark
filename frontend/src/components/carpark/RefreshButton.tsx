import { RefreshCw } from 'lucide-react'
import { cn } from '@/lib/utils'

interface RefreshButtonProps {
  onRefresh: () => void
  isLoading: boolean
  lastUpdated?: string
}

function formatLastUpdated(isoString?: string) {
  if (!isoString) return '--:--'
  const date = new Date(isoString)
  return date.toLocaleTimeString('zh-MO', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

export function RefreshButton({ onRefresh, isLoading, lastUpdated }: RefreshButtonProps) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-muted-foreground">
        最後更新: {formatLastUpdated(lastUpdated)}
      </span>
      <button
        onClick={onRefresh}
        disabled={isLoading}
        className={cn(
          'inline-flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm',
          'bg-primary text-primary-foreground',
          'hover:bg-primary/90 active:scale-95',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          'transition-all duration-200'
        )}
      >
        <RefreshCw className={cn('w-4 h-4', isLoading && 'animate-spin')} />
        {isLoading ? '更新中...' : '立即更新'}
      </button>
    </div>
  )
}
