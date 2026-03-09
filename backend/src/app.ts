import express, { Application } from 'express'
import cors from 'cors'
import compression from 'compression'
import 'express-async-errors'
import { env } from './config/env'
import { errorHandler } from './middleware/errorHandler'
import { httpLogger } from './middleware/logger'
import { systemRouter } from './modules/system'
import { carParkRouter, syncCarParkData } from './modules/carpark'

export const createApp = (): Application => {
  const app = express()

  // HTTP request logging
  app.use(httpLogger)

  app.use(
    cors({
      origin: env.CORS_ORIGIN === '*' ? '*' : env.CORS_ORIGIN,
      credentials: env.CORS_ORIGIN !== '*',
    })
  )

  // Body parsing and compression
  app.use(express.json())
  app.use(express.urlencoded({ extended: true }))
  app.use(compression())

  // API routes - System & Health
  app.use(env.API_PREFIX, systemRouter)

  // Car Park routes
  app.use(`${env.API_PREFIX}/carparks`, carParkRouter)

  // Error handling
  app.use(errorHandler)

  return app
}

// Auto-sync on startup
let syncInterval: NodeJS.Timeout | null = null

export async function startAutoSync() {
  // Initial sync
  try {
    console.log('Starting initial car park data sync...')
    await syncCarParkData()
    console.log('Initial sync completed')
  } catch (error) {
    console.error('Initial sync failed:', error)
  }

  // Sync every 60 seconds
  syncInterval = setInterval(async () => {
    try {
      await syncCarParkData()
    } catch (error) {
      console.error('Auto-sync failed:', error)
    }
  }, 60000)
}

export function stopAutoSync() {
  if (syncInterval) {
    clearInterval(syncInterval)
    syncInterval = null
  }
}
