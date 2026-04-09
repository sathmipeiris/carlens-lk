import Head from 'next/head'
import Link from 'next/link'
import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'

// High-quality car images from Unsplash (free to use)
const CARS = [
  {
    url: 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=1600&q=80',
    name: 'Porsche 911',
    tag: 'Sports',
  },
  {
    url: 'https://images.unsplash.com/photo-1555215695-3004980ad54e?w=1600&q=80',
    name: 'BMW M Series',
    tag: 'Luxury',
  },
  {
    url: 'https://images.unsplash.com/photo-1544636331-e26879cd4d9b?w=1600&q=80',
    name: 'Mercedes-Benz',
    tag: 'Executive',
  },
  {
    url: 'https://images.unsplash.com/photo-1493238792000-8113da705763?w=1600&q=80',
    name: 'Audi RS',
    tag: 'Performance',
  },
  {
    url: 'https://images.unsplash.com/photo-1612544448445-b8232cff3b6c?w=1600&q=80',
    name: 'Lamborghini',
    tag: 'Supercar',
  },
]

const STATS = [
  { value: '9,788', label: 'Listings analysed' },
  { value: '92.5%', label: 'Model accuracy' },
  { value: '4',     label: 'Live economic factors' },
  { value: '3',     label: 'Forecasted brands' },
]

const FEATURES = [
  {
    icon: (
      <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
        <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    ),
    title: 'AI Price Predictor',
    desc: 'Random Forest model trained on 9,788 real Sri Lankan listings. Adjusted for live exchange rates, inflation, and import restrictions.',
    href: '/predict',
  },
  {
    icon: (
      <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
        <path d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    ),
    title: 'Market Dashboard',
    desc: 'Live USD/LKR, CCPI inflation, petrol prices, and CSE ASPI — all showing their real impact on second-hand car prices.',
    href: '/dashboard',
  },
  {
    icon: (
      <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
        <path d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4v16" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    ),
    title: 'Brand Trends',
    desc: 'Price movement forecasts for Toyota, Honda, Suzuki, BMW and more. Know if now is the right time to buy.',
    href: '/trends',
  },
]

function CarCarousel() {
  const [current, setCurrent] = useState(0)
  const [loaded, setLoaded]   = useState({})
  const timerRef = useRef(null)

  const go = (idx) => {
    setCurrent((idx + CARS.length) % CARS.length)
  }

  useEffect(() => {
    timerRef.current = setInterval(() => go(current + 1), 5000)
    return () => clearInterval(timerRef.current)
  }, [current])

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden', borderRadius: 24 }}>
      {/* Images */}
      {CARS.map((car, i) => (
        <div
          key={i}
          style={{
            position:   'absolute',
            inset:       0,
            opacity:     i === current ? 1 : 0,
            transition:  'opacity 0.8s cubic-bezier(0.4,0,0.2,1)',
            zIndex:      i === current ? 1 : 0,
          }}
        >
          <img
            src={car.url}
            alt={car.name}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            onLoad={() => setLoaded(p => ({ ...p, [i]: true }))}
          />
          {/* Gradient overlay */}
          <div style={{
            position: 'absolute', inset: 0,
            background: 'linear-gradient(to right, rgba(12,12,14,0.7) 0%, rgba(12,12,14,0.2) 60%, transparent 100%)',
          }}/>
          {/* Car label */}
          <div style={{
            position: 'absolute', bottom: 24, right: 24,
            background: 'rgba(12,12,14,0.6)',
            backdropFilter: 'blur(12px)',
            border: '1px solid rgba(201,168,76,0.3)',
            borderRadius: 10,
            padding: '8px 14px',
            display: 'flex', flexDirection: 'column', alignItems: 'flex-end',
          }}>
            <span style={{ fontFamily: 'Playfair Display, serif', fontSize: 15, fontWeight: 600, color: '#F0EDE8' }}>{car.name}</span>
            <span style={{ fontSize: 11, color: 'var(--gold)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>{car.tag}</span>
          </div>
        </div>
      ))}

      {/* Dots */}
      <div style={{
        position: 'absolute', bottom: 24, left: '50%', transform: 'translateX(-50%)',
        display: 'flex', gap: 6, zIndex: 10,
      }}>
        {CARS.map((_, i) => (
          <button key={i} onClick={() => go(i)} style={{
            width: i === current ? 24 : 6,
            height: 6,
            borderRadius: 3,
            background: i === current ? 'var(--gold)' : 'rgba(255,255,255,0.3)',
            border: 'none', cursor: 'pointer',
            transition: 'all 0.3s ease',
            padding: 0,
          }}/>
        ))}
      </div>

      {/* Arrows */}
      {[
        { dir: -1, side: { left: 16 } },
        { dir:  1, side: { right: 16 } },
      ].map(({ dir, side }) => (
        <button key={dir} onClick={() => go(current + dir)} style={{
          position: 'absolute', top: '50%', transform: 'translateY(-50%)',
          ...side,
          width: 36, height: 36,
          borderRadius: '50%',
          background: 'rgba(12,12,14,0.5)',
          backdropFilter: 'blur(8px)',
          border: '1px solid rgba(255,255,255,0.1)',
          color: '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          cursor: 'pointer',
          zIndex: 10,
          transition: 'background 0.2s',
        }}
        onMouseEnter={e => e.currentTarget.style.background = 'rgba(201,168,76,0.4)'}
        onMouseLeave={e => e.currentTarget.style.background = 'rgba(12,12,14,0.5)'}
        >
          <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2">
            {dir === -1
              ? <path d="M15 18l-6-6 6-6" strokeLinecap="round"/>
              : <path d="M9 18l6-6-6-6" strokeLinecap="round"/>}
          </svg>
        </button>
      ))}
    </div>
  )
}

export default function Home() {
  const { user } = useAuth()
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])

  return (
    <>
      <Head>
        <title>CarLensLK — Sri Lanka Car Price Intelligence</title>
        <meta name="description" content="AI-powered used car price prediction for Sri Lanka. Live economic adjustments, brand trends, market dashboard."/>
      </Head>

      <main>
        {/* ── Hero ────────────────────────────────── */}
        <section style={{
          minHeight: '100vh',
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 0,
          paddingTop: 64,
          position: 'relative',
          overflow: 'hidden',
        }} className="flex flex-col lg:grid">

          {/* Left — text */}
          <div style={{
            display: 'flex', flexDirection: 'column', justifyContent: 'center',
            padding: 'clamp(40px,8vw,100px) clamp(24px,6vw,80px)',
          }}>
            {/* Live badge */}
            <div className={`badge badge-gold ${mounted ? 'fade-up delay-1' : 'opacity-0'}`}
              style={{ width: 'fit-content', marginBottom: 28 }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--gold)', animation: 'pulse 2s infinite' }}/>
              Live market data
            </div>

            <h1
              className={mounted ? 'fade-up delay-2' : 'opacity-0'}
              style={{
                fontFamily: 'Playfair Display, serif',
                fontSize: 'clamp(36px,5vw,68px)',
                fontWeight: 800,
                lineHeight: 1.08,
                letterSpacing: '-1.5px',
                color: 'var(--text-1)',
                marginBottom: 24,
              }}
            >
              Know your car's
              true{' '}
              <span className="gradient-text">market value</span>
              {' '}in Sri Lanka
            </h1>

            <p
              className={mounted ? 'fade-up delay-3' : 'opacity-0'}
              style={{
                fontSize: 17, color: 'var(--text-2)', lineHeight: 1.75,
                maxWidth: 480, marginBottom: 40,
              }}
            >
              AI predictions trained on 9,788 local listings — adjusted in real time
              for exchange rates, inflation, fuel costs, and Sri Lanka's import restrictions.
            </p>

            <div
              className={`flex flex-wrap gap-3 ${mounted ? 'fade-up delay-4' : 'opacity-0'}`}
              style={{ marginBottom: 56 }}
            >
              <Link href="/predict" className="btn-gold" style={{ fontSize: 15, padding: '14px 32px' }}>
                Predict my car's price
              </Link>
              {!user && (
                <Link href="/signup" className="btn-ghost" style={{ fontSize: 15, padding: '14px 32px' }}>
                  Create free account
                </Link>
              )}
            </div>

            {/* Stats */}
            <div
              className={`grid grid-cols-2 gap-4 ${mounted ? 'fade-up delay-5' : 'opacity-0'}`}
              style={{ maxWidth: 420 }}
            >
              {STATS.map(s => (
                <div key={s.label} style={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border)',
                  borderRadius: 12,
                  padding: '16px 20px',
                }}>
                  <div style={{
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: 26, fontWeight: 700,
                    color: 'var(--gold)', lineHeight: 1, marginBottom: 4,
                  }}>{s.value}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-3)' }}>{s.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Right — carousel */}
          <div style={{
            position: 'relative',
            minHeight: 500,
            padding: '40px 40px 40px 0',
          }} className="hidden lg:block">
            <CarCarousel />
          </div>
        </section>

        {/* ── Mobile carousel ──────────────────────── */}
        <div className="lg:hidden" style={{ height: 280, margin: '0 24px 48px', borderRadius: 16, overflow: 'hidden' }}>
          <CarCarousel />
        </div>

        {/* ── Features ─────────────────────────────── */}
        <section style={{ padding: '100px 0', background: 'var(--bg-card2)' }}>
          <div style={{ maxWidth: 1280, margin: '0 auto', padding: '0 clamp(24px,6vw,80px)' }}>
            <div style={{ marginBottom: 64 }}>
              <div className="gold-line"/>
              <h2 style={{
                fontFamily: 'Playfair Display, serif',
                fontSize: 'clamp(28px,4vw,48px)',
                fontWeight: 700, color: 'var(--text-1)',
                letterSpacing: '-1px', marginBottom: 16,
              }}>
                Three tools. One platform.
              </h2>
              <p style={{ fontSize: 17, color: 'var(--text-2)', maxWidth: 480 }}>
                Everything you need to make a confident car buying or selling decision.
              </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px,1fr))', gap: 24 }}>
              {FEATURES.map(f => (
                <Link key={f.title} href={f.href} style={{ textDecoration: 'none' }}>
                  <div className="card" style={{
                    padding: '32px 28px',
                    cursor: 'pointer', height: '100%',
                    display: 'flex', flexDirection: 'column', gap: 16,
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.transform = 'translateY(-6px)'
                    e.currentTarget.style.borderColor = 'var(--gold-border)'
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.transform = 'translateY(0)'
                    e.currentTarget.style.borderColor = 'var(--border)'
                  }}
                  >
                    <div style={{
                      width: 48, height: 48, borderRadius: 12,
                      background: 'var(--gold-dim)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      color: 'var(--gold)',
                    }}>
                      {f.icon}
                    </div>
                    <h3 style={{
                      fontFamily: 'Playfair Display, serif',
                      fontSize: 22, fontWeight: 700,
                      color: 'var(--text-1)',
                    }}>{f.title}</h3>
                    <p style={{ fontSize: 14, color: 'var(--text-2)', lineHeight: 1.7, flex: 1 }}>
                      {f.desc}
                    </p>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--gold)', fontSize: 14, fontWeight: 600 }}>
                      Explore →
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>

        {/* ── CTA Banner ───────────────────────────── */}
        <section style={{
          padding: '80px clamp(24px,6vw,80px)',
          maxWidth: 1280, margin: '0 auto',
        }}>
          <div style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--gold-border)',
            borderRadius: 24,
            padding: 'clamp(40px,6vw,72px)',
            display: 'flex', flexDirection: 'column', alignItems: 'center',
            textAlign: 'center', gap: 24,
            position: 'relative', overflow: 'hidden',
          }}>
            {/* Background shimmer */}
            <div style={{
              position: 'absolute', top: -100, right: -100,
              width: 400, height: 400,
              background: 'radial-gradient(circle, rgba(201,168,76,0.08) 0%, transparent 70%)',
              pointerEvents: 'none',
            }}/>
            <div className="badge badge-gold">Free to use</div>
            <h2 style={{
              fontFamily: 'Playfair Display, serif',
              fontSize: 'clamp(28px,4vw,48px)',
              fontWeight: 800, color: 'var(--text-1)',
              letterSpacing: '-1px', maxWidth: 600,
            }}>
              Start predicting smarter today
            </h2>
            <p style={{ fontSize: 16, color: 'var(--text-2)', maxWidth: 480 }}>
              Create a free account to save your predictions, track brands, and get price alerts.
            </p>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', justifyContent: 'center' }}>
              <Link href="/signup" className="btn-gold" style={{ fontSize: 15, padding: '14px 36px' }}>
                Create free account
              </Link>
              <Link href="/predict" className="btn-ghost" style={{ fontSize: 15, padding: '14px 36px' }}>
                Try without signing up
              </Link>
            </div>
          </div>
        </section>

        {/* ── Footer ───────────────────────────────── */}
        <footer style={{
          borderTop: '1px solid var(--border)',
          padding: '32px clamp(24px,6vw,80px)',
        }}>
          <div style={{ maxWidth: 1280, margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
            <span style={{ fontFamily: 'Playfair Display, serif', fontWeight: 700, fontSize: 18, color: 'var(--text-1)' }}>
              CarLens<span style={{ color: 'var(--gold)' }}>LK</span>
            </span>
            <span style={{ fontSize: 13, color: 'var(--text-3)' }}>
              Random Forest · R² 92.5% · 9,788 Sri Lankan listings
            </span>
          </div>
        </footer>
      </main>
    </>
  )
}
