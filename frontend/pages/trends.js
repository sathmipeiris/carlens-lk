import Head from 'next/head'
import { useState, useEffect } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Area, AreaChart,
} from 'recharts'
import { getBrandTrends } from '../lib/api'

const BRAND_COLORS = {
  TOYOTA: '#F4A227',
  HONDA: '#10B981',
  SUZUKI: '#3B82F6',
  BMW: '#8B5CF6',
}

const MOCK_HISTORY = {
  TOYOTA: [52, 53, 51, 54, 55, 53, 56, 57, 56, 58, 59, 58],
  HONDA:  [44, 45, 43, 46, 45, 47, 48, 47, 49, 50, 50, 51],
  SUZUKI: [38, 37, 39, 38, 40, 41, 40, 42, 43, 42, 44, 45],
  BMW:    [120, 122, 119, 125, 128, 124, 130, 132, 129, 135, 138, 136],
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

function TrendBadge({ trend }) {
  if (trend === 'increasing') return <span className="badge badge-red">↑ Rising</span>
  if (trend === 'decreasing') return <span className="badge badge-green">↓ Falling</span>
  return <span className="badge" style={{ background: 'rgba(100,116,139,0.12)', color: '#94A3B8' }}>→ Stable</span>
}

function BrandCard({ brand, data, selected, onClick, loading }) {
  const color = BRAND_COLORS[brand]
  if (loading) {
    return (
      <div className="card p-5 cursor-pointer">
        <div className="skeleton h-4 w-20 mb-3" />
        <div className="skeleton h-8 w-28 mb-2" />
        <div className="skeleton h-4 w-16" />
      </div>
    )
  }

  return (
    <div
      className="card p-5 cursor-pointer"
      style={{
        border: selected ? `1px solid ${color}40` : undefined,
        background: selected ? `${color}08` : undefined,
        transition: 'all 0.2s',
      }}
      onClick={onClick}
      onMouseEnter={e => { if (!selected) e.currentTarget.style.borderColor = `${color}30` }}
      onMouseLeave={e => { if (!selected) e.currentTarget.style.borderColor = 'rgba(255,255,255,0.07)' }}
    >
      <div className="flex items-center justify-between mb-3">
        <span style={{ fontFamily: 'Syne, sans-serif', fontWeight: 700, fontSize: 15, color: '#F1F5F9' }}>
          {brand}
        </span>
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: color }} />
      </div>
      <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 24, fontWeight: 600, color, lineHeight: 1, marginBottom: 8 }}>
        Rs. {data?.current_price?.toFixed(1) ?? '—'}L
      </div>
      <div className="flex items-center justify-between">
        <TrendBadge trend={data?.trend} />
        <span style={{ fontSize: 12, color: '#3D5068' }}>
          {data?.confidence ? `${(data.confidence * 100).toFixed(0)}% conf.` : ''}
        </span>
      </div>
    </div>
  )
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: '#1E293B', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10, padding: '10px 14px' }}>
      <div style={{ fontSize: 12, color: '#64748B', marginBottom: 8 }}>{label}</div>
      {payload.map((p) => (
        <div key={p.name} style={{ fontSize: 14, fontFamily: 'JetBrains Mono, monospace', color: p.color, fontWeight: 500 }}>
          {p.name}: Rs. {p.value}L
        </div>
      ))}
    </div>
  )
}

export default function TrendsPage() {
  const [trends, setTrends] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedBrand, setSelectedBrand] = useState('TOYOTA')

  useEffect(() => {
    getBrandTrends()
      .then(setTrends)
      .catch(() => setError('Backend not connected — showing illustrative data.'))
      .finally(() => setLoading(false))
  }, [])

  const brands = ['TOYOTA', 'HONDA', 'SUZUKI', 'BMW']

  // Build chart data (history + forecast)
  const historyData = MONTHS.map((month, i) => {
    const row = { month }
    brands.forEach((b) => { row[b] = MOCK_HISTORY[b][i] })
    return row
  })

  // Forecast 3 months
  const forecastData = [0, 1, 2].map((i) => {
    const row = { month: ['Next', '+2mo', '+3mo'][i] }
    brands.forEach((b) => {
      const base = MOCK_HISTORY[b][11]
      const trend = trends[b]?.trend
      const slope = trend === 'increasing' ? 1.5 : trend === 'decreasing' ? -1 : 0.3
      row[b] = parseFloat((base + slope * (i + 1)).toFixed(1))
      row[`${b}_forecast`] = true
    })
    return row
  })

  const chartData = [...historyData, ...forecastData]
  const selectedColor = BRAND_COLORS[selectedBrand]

  return (
    <>
      <Head>
        <title>Brand Trends — CarLensLK</title>
      </Head>
      <main style={{ minHeight: '100vh', paddingTop: 96, paddingBottom: 80 }}>
        <div className="max-w-7xl mx-auto px-6">
          {/* Header */}
          <div className="mb-12">
            <div className="gold-accent" />
            <h1
              style={{
                fontFamily: 'Syne, sans-serif',
                fontSize: 'clamp(28px, 4vw, 48px)',
                fontWeight: 800,
                color: '#F1F5F9',
                letterSpacing: '-1.5px',
                lineHeight: 1.1,
                marginBottom: 12,
              }}
            >
              Brand Trends
            </h1>
            <p style={{ color: '#64748B', fontSize: 16 }}>
              Price movement forecasts for top brands in the Sri Lankan market.
            </p>
          </div>

          {error && (
            <div className="card p-5 mb-8 flex items-center gap-4" style={{ border: '1px solid rgba(244,162,39,0.2)', background: 'rgba(244,162,39,0.04)' }}>
              <svg width="18" height="18" fill="none" stroke="#F4A227" strokeWidth="2" viewBox="0 0 24 24">
                <path d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" strokeLinecap="round"/>
              </svg>
              <span style={{ fontSize: 14, color: '#F4A227' }}>{error} Chart shows illustrative historical data.</span>
            </div>
          )}

          {/* Brand cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {brands.map((b) => (
              <BrandCard
                key={b}
                brand={b}
                data={trends[b]}
                selected={selectedBrand === b}
                onClick={() => setSelectedBrand(b)}
                loading={loading}
              />
            ))}
          </div>

          {/* Main chart */}
          <div className="card p-8 mb-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
              <div>
                <h2 style={{ fontFamily: 'Syne, sans-serif', fontSize: 20, fontWeight: 700, color: '#F1F5F9', marginBottom: 4 }}>
                  {selectedBrand} — 12-month history + 3-month forecast
                </h2>
                <p style={{ fontSize: 13, color: '#3D5068' }}>
                  Average price in LKR Lakhs · Dashed section = forecast
                </p>
              </div>
              <TrendBadge trend={trends[selectedBrand]?.trend ?? 'stable'} />
            </div>

            <div style={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 5, right: 10, bottom: 0, left: 0 }}>
                  <defs>
                    <linearGradient id={`grad-${selectedBrand}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={selectedColor} stopOpacity={0.15} />
                      <stop offset="95%" stopColor={selectedColor} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
                  <XAxis
                    dataKey="month"
                    tick={{ fill: '#3D5068', fontSize: 12, fontFamily: 'JetBrains Mono' }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: '#3D5068', fontSize: 12, fontFamily: 'JetBrains Mono' }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(v) => `${v}L`}
                    width={48}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Area
                    type="monotone"
                    dataKey={selectedBrand}
                    stroke={selectedColor}
                    strokeWidth={2.5}
                    fill={`url(#grad-${selectedBrand})`}
                    dot={false}
                    activeDot={{ r: 5, fill: selectedColor, strokeWidth: 0 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Multi-brand comparison */}
          <div className="card p-8">
            <h2 style={{ fontFamily: 'Syne, sans-serif', fontSize: 20, fontWeight: 700, color: '#F1F5F9', marginBottom: 8 }}>
              All brands comparison
            </h2>
            <p style={{ fontSize: 13, color: '#3D5068', marginBottom: 24 }}>Price trends across all tracked brands.</p>

            {/* Legend */}
            <div className="flex flex-wrap gap-6 mb-6">
              {brands.map((b) => (
                <div key={b} className="flex items-center gap-2">
                  <div style={{ width: 24, height: 2.5, borderRadius: 2, background: BRAND_COLORS[b] }} />
                  <span style={{ fontSize: 13, color: '#64748B', fontWeight: 500 }}>{b}</span>
                </div>
              ))}
            </div>

            <div style={{ height: 280 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={historyData} margin={{ top: 5, right: 10, bottom: 0, left: 0 }}>
                  <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
                  <XAxis dataKey="month" tick={{ fill: '#3D5068', fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#3D5068', fontSize: 12 }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v}L`} width={48} />
                  <Tooltip content={<CustomTooltip />} />
                  {brands.map((b) => (
                    <Line
                      key={b}
                      type="monotone"
                      dataKey={b}
                      stroke={BRAND_COLORS[b]}
                      strokeWidth={selectedBrand === b ? 2.5 : 1.5}
                      dot={false}
                      opacity={selectedBrand === b ? 1 : 0.4}
                      activeDot={{ r: 4, strokeWidth: 0 }}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </main>
    </>
  )
}
