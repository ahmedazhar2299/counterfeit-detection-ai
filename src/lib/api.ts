import axios from 'axios'

import type { AnalysisResponse, ListingInput, ListingWithAnalysis, MetricsPayload } from '@/types'

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  headers: { 'Content-Type': 'application/json' }
})

export const analyzeListing = async (payload: ListingInput) => {
  const { data } = await api.post<AnalysisResponse>('/api/analyze', payload)
  return data
}

export const getListings = async (limit = 50) => {
  const { data } = await api.get<ListingWithAnalysis[]>(`/api/listings?limit=${limit}`)
  return data
}

export const getListing = async (id: number) => {
  const { data } = await api.get<ListingWithAnalysis>(`/api/listings/${id}`)
  return data
}

export const sendFeedback = async (payload: { analysis_id: number; label: string; notes?: string }) => {
  const { data } = await api.post('/api/feedback', payload)
  return data
}

export const getMetrics = async () => {
  const { data } = await api.get<MetricsPayload>('/api/metrics')
  return data
}
