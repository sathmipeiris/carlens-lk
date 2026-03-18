import axios from 'axios'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

export async function predictPrice(formData) {
  const { data } = await api.post('/predict', formData)
  return data
}

export async function getEconomicIndicators() {
  const { data } = await api.get('/api/dashboard/economic-indicators')
  return data
}

export async function getMarketHealth() {
  const { data } = await api.get('/api/dashboard/market-health')
  return data
}

export async function getBrandTrends() {
  const { data } = await api.get('/api/dashboard/brand-trends')
  return data
}

export async function checkHealth() {
  const { data } = await api.get('/health')
  return data
}
