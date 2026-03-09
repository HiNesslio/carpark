import { Router, Request, Response } from 'express'
import { PrismaClient } from '@prisma/client'
import axios from 'axios'
import * as xml2js from 'xml2js'

const router = Router()
const prisma = new PrismaClient()

const CAR_PARK_API_URL = 'https://dsat.apigateway.data.gov.mo/car_park_maintance'
const API_AUTHORIZATION = 'APPCODE 09d43a591fba407fb862412970667de4'

// Calculate parking status based on available spaces
function getStatus(available: number, total: number): 'available' | 'limited' | 'full' {
  if (available === 0) return 'full'
  if (total === 0) return 'available'
  const rate = available / total
  if (rate <= 0.2) return 'limited'
  return 'available'
}

// Fetch and parse XML data from Macau API
async function fetchCarParkData() {
  const response = await axios.get(CAR_PARK_API_URL, {
    headers: {
      Authorization: API_AUTHORIZATION,
    },
    responseType: 'text',
  })

  const parser = new xml2js.Parser({ 
    explicitArray: false,
    mergeAttrs: true,
  })
  const result = await parser.parseStringPromise(response.data)

  // XML structure: <CarPark><Car_park_info ID="..." name="..." ... />
  const carParks = result.CarPark?.Car_park_info || []
  return Array.isArray(carParks) ? carParks : [carParks]
}

// Sync data from API to database
async function syncCarParkData() {
  try {
    const carParks = await fetchCarParkData()
    let savedCount = 0

    for (const cp of carParks) {
      const id = cp.ID
      const name = cp.name || ''
      const nameEn = cp.CP_EName || ''
      
      // Car_CNT is available car spaces, MB_CNT is available motorcycle spaces
      const carAvailable = parseInt(cp.Car_CNT || '0', 10) || 0
      const motoAvailable = parseInt(cp.MB_CNT || '0', 10) || 0
      const totalSpaces = carAvailable + motoAvailable
      const availableSpaces = carAvailable
      
      const lastUpdatedStr = cp.Time || new Date().toISOString()
      let lastUpdated: Date
      try {
        // Parse time format: "3/9/2026 5:05:18 PM"
        lastUpdated = new Date(lastUpdatedStr)
        if (isNaN(lastUpdated.getTime())) {
          lastUpdated = new Date()
        }
      } catch {
        lastUpdated = new Date()
      }

      if (id && name) {
        await prisma.carPark.upsert({
          where: { id: String(id) },
          update: {
            name: nameEn || name,
            nameZh: name,
            totalSpaces,
            availableSpaces,
            lastUpdated,
          },
          create: {
            id: String(id),
            name: nameEn || name,
            nameZh: name,
            totalSpaces,
            availableSpaces,
            lastUpdated,
          },
        })
        savedCount++
      }
    }

    console.log(`Synced ${savedCount} car parks`)
    return { success: true, count: savedCount }
  } catch (error) {
    console.error('Failed to sync car park data:', error)
    throw error
  }
}

// GET /api/carparks - Get all car parks
router.get('/', async (req: Request, res: Response) => {
  try {
    const carParks = await prisma.carPark.findMany({
      orderBy: { availableSpaces: 'desc' },
    })

    const response = carParks.map(cp => ({
      id: cp.id,
      name: cp.name,
      nameZh: cp.nameZh,
      address: cp.address,
      addressZh: cp.addressZh,
      totalSpaces: cp.totalSpaces,
      availableSpaces: cp.availableSpaces,
      latitude: cp.latitude,
      longitude: cp.longitude,
      lastUpdated: cp.lastUpdated.toISOString(),
      status: getStatus(cp.availableSpaces, cp.totalSpaces),
      occupancyRate: cp.totalSpaces > 0 
        ? Math.round((cp.availableSpaces / cp.totalSpaces) * 100) 
        : 0,
    }))

    res.json({
      success: true,
      data: response,
      total: response.length,
    })
  } catch (error) {
    console.error('Error fetching car parks:', error)
    res.status(500).json({
      success: false,
      error: 'Failed to fetch car park data',
    })
  }
})

// POST /api/carparks/refresh - Refresh data from API
router.post('/refresh', async (req: Request, res: Response) => {
  try {
    const result = await syncCarParkData()
    
    // Return updated data
    const carParks = await prisma.carPark.findMany({
      orderBy: { availableSpaces: 'desc' },
    })

    const response = carParks.map(cp => ({
      id: cp.id,
      name: cp.name,
      nameZh: cp.nameZh,
      address: cp.address,
      addressZh: cp.addressZh,
      totalSpaces: cp.totalSpaces,
      availableSpaces: cp.availableSpaces,
      latitude: cp.latitude,
      longitude: cp.longitude,
      lastUpdated: cp.lastUpdated.toISOString(),
      status: getStatus(cp.availableSpaces, cp.totalSpaces),
      occupancyRate: cp.totalSpaces > 0 
        ? Math.round((cp.availableSpaces / cp.totalSpaces) * 100) 
        : 0,
    }))

    res.json({
      success: true,
      message: `Synced ${result.count} car parks`,
      data: response,
    })
  } catch (error) {
    console.error('Error refreshing car park data:', error)
    res.status(500).json({
      success: false,
      error: 'Failed to refresh car park data',
    })
  }
})

// GET /api/carparks/stats - Get statistics
router.get('/stats', async (req: Request, res: Response) => {
  try {
    const carParks = await prisma.carPark.findMany()
    
    const totalSpaces = carParks.reduce((sum, cp) => sum + cp.totalSpaces, 0)
    const availableSpaces = carParks.reduce((sum, cp) => sum + cp.availableSpaces, 0)
    const fullCount = carParks.filter(cp => cp.availableSpaces === 0).length
    const limitedCount = carParks.filter(cp => {
      if (cp.totalSpaces === 0) return false
      const rate = cp.availableSpaces / cp.totalSpaces
      return rate > 0 && rate <= 0.2
    }).length

    res.json({
      success: true,
      data: {
        totalCarParks: carParks.length,
        totalSpaces,
        availableSpaces,
        occupancyRate: totalSpaces > 0 
          ? Math.round(((totalSpaces - availableSpaces) / totalSpaces) * 100) 
          : 0,
        statusBreakdown: {
          available: carParks.length - fullCount - limitedCount,
          limited: limitedCount,
          full: fullCount,
        },
      },
    })
  } catch (error) {
    console.error('Error fetching stats:', error)
    res.status(500).json({
      success: false,
      error: 'Failed to fetch statistics',
    })
  }
})

export { router as carParkRouter, syncCarParkData }
