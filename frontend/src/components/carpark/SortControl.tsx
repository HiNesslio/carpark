import { SortOption } from '@/types/carpark'
import { ArrowUpDown, Car, Hash, Building } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SortControlProps {
  value: SortOption
  onChange: (value: SortOption) => void
}

const sortOptions: { value: SortOption; label: string; icon: React.ReactNode }[] = [
  { value: 'available', label: '按剩餘車位', icon: <Car className="w-4 h-4" /> },
  { value: 'total', label: '按總車位', icon: <Hash className="w-4 h-4" /> },
  { value: 'name', label: '按名稱', icon: <Building className="w-4 h-4" /> },
]

export function SortControl({ value, onChange }: SortControlProps) {
  return (
    <div className="flex items-center gap-2">
      <ArrowUpDown className="w-4 h-4 text-muted-foreground" />
      <div className="flex gap-1">
        {sortOptions.map((option) => (
          <button
            key={option.value}
            onClick={() => onChange(option.value)}
            className={cn(
              'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium',
              'transition-colors duration-200',
              value === option.value
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-muted-foreground hover:bg-muted/80'
            )}
          >
            {option.icon}
            {option.label}
          </button>
        ))}
      </div>
    </div>
  )
}
