import { useState } from 'react'
import { Car } from 'lucide-react'
import { useCarParks, useCarParkStats, useRefreshCarParks, useSortCarParks } from '@/hooks/use-carparks'
import { CarParkCard, RefreshButton, SortControl, StatsOverview } from '@/components/carpark'
import { SortOption } from '@/types/carpark'
import { FadeIn, Stagger, StaggerChild } from '@/components/MotionPrimitives'

export default function Index() {
  const [sortBy, setSortBy] = useState<SortOption>('available')
  const { data: carParksResponse, isLoading: isLoadingParks, data } = useCarParks(sortBy)
  const { data: statsResponse, isLoading: isLoadingStats } = useCarParkStats()
  const refreshMutation = useRefreshCarParks()

  const sortedCarParks = useSortCarParks(carParksResponse?.data, sortBy)
  const lastCarPark = sortedCarParks[0]

  const handleRefresh = () => {
    refreshMutation.mutate()
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-card border-b shadow-sm">
        <div className="container max-w-6xl py-4">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Car className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h1 className="font-bold" style={{ fontSize: 'var(--font-size-headline)' }}>
                  澳門停車場即時空位
                </h1>
                <p className="text-sm text-muted-foreground">
                  即時查詢各停車場空位狀況
                </p>
              </div>
            </div>
            <RefreshButton
              onRefresh={handleRefresh}
              isLoading={refreshMutation.isPending}
              lastUpdated={lastCarPark?.lastUpdated}
            />
          </div>
        </div>
      </header>

      <main className="container max-w-6xl py-6">
        {/* Stats Overview */}
        <section className="mb-6">
          <FadeIn>
            <StatsOverview 
              stats={statsResponse?.data} 
              isLoading={isLoadingStats} 
            />
          </FadeIn>
        </section>

        {/* Sort Controls */}
        <section className="mb-6">
          <FadeIn delay={0.1}>
            <SortControl value={sortBy} onChange={setSortBy} />
          </FadeIn>
        </section>

        {/* Car Park Grid */}
        <section>
          {isLoadingParks ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[...Array(9)].map((_, i) => (
                <div 
                  key={i} 
                  className="bg-card rounded-lg h-48 animate-pulse"
                />
              ))}
            </div>
          ) : sortedCarParks.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              暫無停車場資料
            </div>
          ) : (
            <Stagger className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {sortedCarParks.map((carpark) => (
                <StaggerChild key={carpark.id}>
                  <CarParkCard carpark={carpark} />
                </StaggerChild>
              ))}
            </Stagger>
          )}
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t py-4 mt-8">
        <div className="container max-w-6xl text-center text-sm text-muted-foreground">
          數據來源: 澳門交通事務局 | 每 60 秒自動更新
        </div>
      </footer>
    </div>
  )
}
