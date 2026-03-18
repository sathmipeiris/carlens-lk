import Head from 'next/head'
import { useState, useEffect } from 'react'
import { getEconomicIndicators, getMarketHealth } from '../lib/api'
import StatCard from '../components/StatCard'

function ImpactBadge({ level }) {
  const map = {
    High: 'badge-red',
    Moderate: 'badge-amber',
    Medium: 'badge-amber',
    Low: 'badge-green',
    Positive: 'badge-green',
  }
  return <span className={`badge ${map[level] || 'badge-amber'}`}>{level}</span>
}

function IndicatorCard({ title, value, impact, description, loading }) {
  if (loading) {
    return (
      <div className="card p-6">
        <div className="skeleton h-3 w-24 mb-4" />
        <div className="skeleton h-8 w-28 mb-3" />
        <div className="skeleton h-3 w-full mb-2" />
        <div className="skeleton h-3 w-3/4" />
      </div>
    )
  }
  return (
    <div className="card p-6 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-4">
        <span style={{ fontSize: 13, color: '#64748B', fontWeight: 500 }}>{title}</span>
        {impact && <ImpactBadge level={impact} />}
      </div>
      <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 28, fontWeight: 600, color: '#F1F5F9' }}>
        {value}
      </div>
      <p style={{ fontSize: 13, color: '#3D5068', lineHeight: 1.6 }}>{description}</p>
    </div>
  )
}

function HealthGauge({ score, status, loading }) {
  if (loading) {
    return (
      <div className="card p-8 flex flex-col items-center gap-4">
        <div className="skeleton h-5 w-32 mb-2" />
        <div className="skeleton" style={{ width: 160, height: 160, borderRadius: '50%' }} />
        <div className="skeleton h-4 w-24" />
      </div>
    )
  }

  const color = score >= 70 ? '#10B981' : score >= 40 ? '#F4A227' : '#F43F5E'
  const circumference = 2 * Math.PI * 54
  const offset = circumference - (score / 100) * circumference

  return (
    <div className="card p-8 flex flex-col items-center">
      <div style={{ fontSize: 13, color: '#64748B', fontWeight: 500, marginBottom: 24, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
        Market health
      </div>
      <div style={{ position: 'relative', width: 140, height: 140 }}>
        <svg width="140" height="140" viewBox="0 0 140 140">
          <circle cx="70" cy="70" r="54" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="10" />
          <circle
            cx="70" cy="70" r="54"
            fill="none"
            stroke={color}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            transform="rotate(-90 70 70)"
            style={{ transition: 'stroke-dashoffset 1s ease' }}
          />
        </svg>
        <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 28, fontWeight: 700, color, lineHeight: 1 }}>{score}</span>
          <span style={{ fontSize: 11, color: '#3D5068', marginTop: 2 }}>/ 100</span>
        </div>
      </div>
      <div style={{ marginTop: 20, fontSize: 18, fontFamily: 'Syne, sans-serif', fontWeight: 700, color }}>
        {status}
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const [indicators, setIndicators] = useState(null)
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [ind, h] = await Promise.all([getEconomicIndicators(), getMarketHealth()])
      setIndicators(ind)
      setHealth(h)
      setLastUpdated(new Date())
    } catch (e) {
      setError('Cannot connect to backend. Start your Flask API on port 5000.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchData() }, [])

  const ind = indicators?.indicators || {}
  const impact = indicators?.impact_analysis || {}

  const mainStats = [
    {
      label: 'USD / LKR rate',
      value: ind.usd_lkr_rate ? ind.usd_lkr_rate.toFixed(1) : '—',
      impact: impact.usd_lkr?.impact,
      description: impact.usd_lkr?.description || 'Affects import car prices',
    },
    {
      label: 'Inflation rate',
      value: ind.inflation_rate ? `${ind.inflation_rate.toFixed(1)}%` : '—',
      impact: impact.inflation?.impact,
      description: impact.inflation?.description || 'Affects purchasing power and depreciation',
    },
    {
      label: 'Petrol (92) price',
      value: ind.petrol_price ? `Rs. ${ind.petrol_price}` : '—',
      impact: impact.fuel_price?.impact,
      description: impact.fuel_price?.description || 'Higher fuel costs increase hybrid premiums',
    },
    {
      label: 'CSE ASPI',
      value: ind.cse_aspi ? ind.cse_aspi.toLocaleString() : '—',
      impact: impact.stock_market?.impact,
      description: impact.stock_market?.description || 'Correlates with consumer confidence',
    },
  ]

  return (
    <>
      <Head>
        <title>Market Dashboard — CarLensLK</title>
      </Head>
      <main style={{ minHeight: '100vh', paddingTop: 96, paddingBottom: 80 }}>
        <div className="max-w-7xl mx-auto px-6">
          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
            <div>
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
                Market Dashboard
              </h1>
              <p style={{ color: '#64748B', fontSize: 16 }}>
                Live Sri Lankan economic indicators and their impact on car prices.
              </p>
            </div>
            <div className="flex items-center gap-4">
              {lastUpdated && (
                <span style={{ fontSize: 13, color: '#3D5068', fontFamily: 'JetBrains Mono, monospace' }}>
                  Updated {lastUpdated.toLocaleTimeString()}
                </span>
              )}
              <button
                onClick={fetchData}
                disabled={loading}
                style={{
                  background: 'rgba(244,162,39,0.1)',
                  border: '1px solid rgba(244,162,39,0.2)',
                  borderRadius: 10,
                  color: '#F4A227',
                  padding: '10px 20px',
                  fontSize: 14,
                  fontWeight: 500,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  opacity: loading ? 0.6 : 1,
                  transition: 'all 0.2s',
                }}
              >
                <svg className={loading ? 'animate-spin' : ''} width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path d="M4 4v5h5M20 20v-5h-5M4 9a9 9 0 0115 0M20 15a9 9 0 01-15 0" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                Refresh
              </button>
            </div>
          </div>

          {error && (
            <div
              className="card p-6 mb-8"
              style={{ border: '1px solid rgba(244,63,94,0.2)', background: 'rgba(244,63,94,0.05)' }}
            >
              <div style={{ fontSize: 14, color: '#FB7185', fontWeight: 500, marginBottom: 6 }}>Backend not connected</div>
              <div style={{ fontSize: 13, color: '#64748B' }}>{error}</div>
            </div>
          )}

          <div className="grid lg:grid-cols-4 gap-6 mb-8">
            {/* Health gauge spans 1 col */}
            <HealthGauge
              score={health?.health_score ?? 0}
              status={health?.health_status ?? '—'}
              loading={loading}
            />

            {/* 3 stat cards */}
            <div className="lg:col-span-3 grid sm:grid-cols-3 gap-6">
              <StatCard
                label="Market recommendation"
                value={health?.recommendation || '—'}
                loading={loading}
                accent={health?.health_score >= 60 ? '#34D399' : '#FB7185'}
              />
              <StatCard
                label="Health score"
                value={health?.health_score ? `${health.health_score}/100` : '—'}
                loading={loading}
              />
              <StatCard
                label="Key driver"
                value={ind.usd_lkr_rate > 350 ? 'Exchange rate' : 'Inflation'}
                loading={loading}
              />
            </div>
          </div>

          {/* Indicator cards */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-12">
            {mainStats.map((s) => (
              <IndicatorCard key={s.label} {...s} loading={loading} />
            ))}
          </div>

          {/* Impact table */}
          <div className="card p-8">
            <h2 style={{ fontFamily: 'Syne, sans-serif', fontSize: 20, fontWeight: 700, color: '#F1F5F9', marginBottom: 24 }}>
              How economic factors affect your car's price
            </h2>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: '0 8px' }}>
                <thead>
                  <tr>
                    {['Indicator', 'Current value', 'Impact level', 'Effect on prices'].map((h) => (
                      <th key={h} style={{ textAlign: 'left', padding: '4px 16px', fontSize: 12, color: '#3D5068', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {mainStats.map((s) => (
                    <tr key={s.label}>
                      <td style={{ padding: '12px 16px', fontSize: 14, color: '#94A3B8', background: 'rgba(255,255,255,0.02)', borderRadius: '8px 0 0 8px' }}>{s.label}</td>
                      <td style={{ padding: '12px 16px', fontSize: 14, color: '#F1F5F9', fontFamily: 'JetBrains Mono, monospace', background: 'rgba(255,255,255,0.02)' }}>{s.value}</td>
                      <td style={{ padding: '12px 16px', background: 'rgba(255,255,255,0.02)' }}>
                        {loading ? <div className="skeleton h-5 w-16" /> : <ImpactBadge level={s.impact || 'Low'} />}
                      </td>
                      <td style={{ padding: '12px 16px', fontSize: 13, color: '#64748B', background: 'rgba(255,255,255,0.02)', borderRadius: '0 8px 8px 0' }}>{s.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
    </>
  )
}
