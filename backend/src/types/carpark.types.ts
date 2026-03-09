import { z } from 'zod'

export const carParkSchema = z.object({
  id: z.string(),
  name: z.string(),
  nameZh: z.string().nullable(),
  address: z.string().nullable(),
  addressZh: z.string().nullable(),
  totalSpaces: z.number(),
  availableSpaces: z.number(),
  latitude: z.number().nullable(),
  longitude: z.number().nullable(),
  lastUpdated: z.date(),
})

export const carParkResponseSchema = z.object({
  id: z.string(),
  name: z.string(),
  nameZh: z.string().nullable(),
  address: z.string().nullable(),
  addressZh: z.string().nullable(),
  totalSpaces: z.number(),
  availableSpaces: z.number(),
  latitude: z.number().nullable(),
  longitude: z.number().nullable(),
  lastUpdated: z.string(),
  status: z.enum(['available', 'limited', 'full']),
  occupancyRate: z.number(),
})

export type CarPark = z.infer<typeof carParkSchema>
export type CarParkResponse = z.infer<typeof carParkResponseSchema>
