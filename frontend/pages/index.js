import Head from 'next/head'
import Link from 'next/link'
import { useState, useEffect } from 'react'

const stats = [
  { value: '9,617', label: 'Cars analysed' },
  { value: '92.5%', label: 'Model accuracy' },
  { value: '4', label: 'Economic factors' },
  { value: 'Live', label: 'Market data' },
]

const features = [
  {
    icon: (
      <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    ),
    title: 'AI price prediction',
    desc: 'Random Forest model trained on Sri Lanka\'s used car market. Enter your car details and get an instant market valuation.',
    href: '/predict',
    cta: 'Try predictor',
  },
  {
    icon: (
      <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    ),
    title: 'Market dashboard',
    desc: 'Live economic indicators — USD/LKR rate, inflation, fuel prices, CSE index — and how each affects car prices right now.',
    href: '/dashboard',
    cta: 'View dashboard',
  },
  {
    icon: (
      <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4v16" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    ),
    title: 'Brand trends',
    desc: 'Price trend forecasts for Toyota, Honda, Suzuki, BMW and more. Know whether prices are rising before you buy or sell.',
    href: '/trends',
    cta: 'Explore trends',
  },
]

export default function Home() {
  const [mounted, setMounted] = useState(false)
  useEffect(() => { setMounted(true) }, [])

  return (
    <>
      <Head>
        <title>CarLensLK — Sri Lanka Car Price Intelligence</title>
        <meta name="description" content="AI-powered car price prediction and market intelligence for Sri Lanka's used car market." />
      </Head>

      <main style={{ minHeight: '100vh' }}>
        {/* Hero */}
        <section
          style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            position: 'relative',
            overflow: 'hidden',
            paddingTop: 80,
          }}
        >
          {/* Background grid */}
          <div
            style={{
              position: 'absolute',
              inset: 0,
              backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(255,255,255,0.04) 1px, transparent 0)',
              backgroundSize: '32px 32px',
              pointerEvents: 'none',
            }}
          />
          {/* Gold glow */}
          <div
            style={{
              position: 'absolute',
              top: '20%',
              right: '-10%',
              width: 600,
              height: 600,
              background: 'radial-gradient(circle, rgba(244,162,39,0.08) 0%, transparent 70%)',
              pointerEvents: 'none',
            }}
          />
          <div
            style={{
              position: 'absolute',
              bottom: '10%',
              left: '-5%',
              width: 400,
              height: 400,
              background: 'radial-gradient(circle, rgba(16,185,129,0.06) 0%, transparent 70%)',
              pointerEvents: 'none',
            }}
          />

          <div className="max-w-7xl mx-auto px-6 w-full">
            <div className="max-w-3xl">
              {/* Badge */}
              <div
                className={`inline-flex items-center gap-2 mb-8 ${mounted ? 'animate-fade-up' : 'opacity-0'}`}
                style={{ animationDelay: '0.1s' }}
              >
                <span className="badge badge-amber">
                  <span
                    style={{
                      width: 6,
                      height: 6,
                      borderRadius: '50%',
                      background: '#F4A227',
                      animation: 'pulse 2s infinite',
                    }}
                  />
                  Live market data
                </span>
              </div>

              {/* Headline */}
              <h1
                className={mounted ? 'animate-fade-up' : 'opacity-0'}
                style={{
                  fontFamily: 'Syne, sans-serif',
                  fontSize: 'clamp(40px, 6vw, 72px)',
                  fontWeight: 800,
                  lineHeight: 1.05,
                  color: '#F1F5F9',
                  letterSpacing: '-2px',
                  marginBottom: 24,
                  animationDelay: '0.2s',
                }}
              >
                Know exactly what your{' '}
                <span className="gradient-text">car is worth</span>{' '}
                in Sri Lanka
              </h1>

              <p
                className={mounted ? 'animate-fade-up' : 'opacity-0'}
                style={{
                  fontSize: 18,
                  color: '#64748B',
                  lineHeight: 1.7,
                  marginBottom: 40,
                  maxWidth: 540,
                  animationDelay: '0.3s',
                }}
              >
                AI-powered price predictions trained on 9,617 local listings.
                Factor in exchange rates, inflation, and fuel prices to get the
                true market value — not just a guess.
              </p>

              {/* CTAs */}
              <div
                className={`flex flex-wrap gap-4 ${mounted ? 'animate-fade-up' : 'opacity-0'}`}
                style={{ animationDelay: '0.4s' }}
              >
                <Link href="/predict" className="btn-primary text-base px-7 py-3.5 inline-block">
                  Predict my car's price
                </Link>
                <Link
                  href="/dashboard"
                  style={{
                    display: 'inline-block',
                    fontSize: 16,
                    fontWeight: 500,
                    color: '#94A3B8',
                    padding: '14px 28px',
                    border: '1px solid rgba(255,255,255,0.08)',
                    borderRadius: 10,
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.borderColor = 'rgba(255,255,255,0.2)'
                    e.currentTarget.style.color = '#F1F5F9'
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'
                    e.currentTarget.style.color = '#94A3B8'
                  }}
                >
                  View market data →
                </Link>
              </div>
            </div>

            {/* Stats row */}
            <div
              className={`grid grid-cols-2 md:grid-cols-4 gap-4 mt-20 ${mounted ? 'animate-fade-up' : 'opacity-0'}`}
              style={{ animationDelay: '0.5s' }}
            >
              {stats.map((stat) => (
                <div
                  key={stat.label}
                  className="card p-5"
                  style={{ borderColor: 'rgba(255,255,255,0.06)' }}
                >
                  <div
                    style={{
                      fontFamily: 'JetBrains Mono, monospace',
                      fontSize: 30,
                      fontWeight: 600,
                      color: '#F4A227',
                      lineHeight: 1,
                      marginBottom: 6,
                    }}
                  >
                    {stat.value}
                  </div>
                  <div style={{ fontSize: 13, color: '#3D5068' }}>{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Features section */}
        <section style={{ padding: '100px 0', position: 'relative' }}>
          <div className="max-w-7xl mx-auto px-6">
            <div className="mb-16">
              <div className="gold-accent" />
              <h2
                style={{
                  fontFamily: 'Syne, sans-serif',
                  fontSize: 'clamp(28px, 4vw, 44px)',
                  fontWeight: 700,
                  color: '#F1F5F9',
                  letterSpacing: '-1px',
                  marginBottom: 16,
                }}
              >
                Three tools. One platform.
              </h2>
              <p style={{ fontSize: 17, color: '#64748B', maxWidth: 500 }}>
                Everything you need to make a confident car buying or selling decision in Sri Lanka.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-6">
              {features.map((f) => (
                <div
                  key={f.title}
                  className="card p-7 flex flex-col group"
                  style={{
                    transition: 'transform 0.25s, border-color 0.25s',
                    cursor: 'pointer',
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.transform = 'translateY(-4px)'
                    e.currentTarget.style.borderColor = 'rgba(244,162,39,0.25)'
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.transform = 'translateY(0)'
                    e.currentTarget.style.borderColor = 'rgba(255,255,255,0.07)'
                  }}
                >
                  <div
                    style={{
                      width: 44,
                      height: 44,
                      borderRadius: 10,
                      background: 'rgba(244,162,39,0.1)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#F4A227',
                      marginBottom: 20,
                    }}
                  >
                    {f.icon}
                  </div>
                  <h3
                    style={{
                      fontFamily: 'Syne, sans-serif',
                      fontSize: 20,
                      fontWeight: 700,
                      color: '#F1F5F9',
                      marginBottom: 12,
                    }}
                  >
                    {f.title}
                  </h3>
                  <p style={{ fontSize: 14, color: '#64748B', lineHeight: 1.7, flex: 1 }}>{f.desc}</p>
                  <Link
                    href={f.href}
                    style={{
                      marginTop: 24,
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 6,
                      fontSize: 14,
                      fontWeight: 500,
                      color: '#F4A227',
                    }}
                  >
                    {f.cta}
                    <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M5 3l6 4-6 4" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </Link>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer
          style={{
            borderTop: '1px solid rgba(255,255,255,0.06)',
            padding: '32px 0',
            color: '#3D5068',
            fontSize: 14,
          }}
        >
          <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between gap-4">
            <span style={{ fontFamily: 'Syne, sans-serif', fontWeight: 700, color: '#1E293B' }}>
              CarLensLK
            </span>
            <span>Trained on Sri Lanka used car listings · Random Forest · R² 92.5%</span>
          </div>
        </footer>
      </main>
    </>
  )
}
