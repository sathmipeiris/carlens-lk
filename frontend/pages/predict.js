// frontend/pages/predict.js
import Head from 'next/head'
import { useState } from 'react'
import PriceBreakdown from '../components/PriceBreakdown'
import { predictPrice } from '../lib/api'
import axios from 'axios'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'

const BRANDS     = ['TOYOTA','HONDA','SUZUKI','BMW','MERCEDES-BENZ','AUDI',
                    'NISSAN','MITSUBISHI','HYUNDAI','KIA','MAZDA','FORD',
                    'LAND ROVER','LEXUS','SUBARU','VOLKSWAGEN']
const FUEL_TYPES = ['Petrol','Diesel','Hybrid','Plug-in Hybrid','Electric','Gas']
const GEAR_TYPES = ['Automatic','Manual','Semi-Automatic','CVT']
const LEASING    = ['No Leasing','Leasing Available','Fully Leased']
const CONDITIONS = ['USED','RECONDITIONED','BRAND NEW']

const INITIAL = {
  brand:'TOYOTA', model:'Corolla', yom:2018, engine_cc:1800,
  mileage:60000, gear:'Automatic', fuel_type:'Petrol',
  town:'Colombo', leasing:'No Leasing', condition:'USED',
  air_condition:1, power_steering:1, power_mirror:1, power_window:1,
}

function Field({ label, children, hint }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label style={{ fontSize:13, color:'#64748B', fontWeight:500 }}>{label}</label>
      {children}
      {hint && <span style={{ fontSize:12, color:'#2D3F58' }}>{hint}</span>}
    </div>
  )
}

function Toggle({ label, value, onChange }) {
  return (
    <div className="flex items-center justify-between p-4 rounded-xl"
      style={{ background:'rgba(255,255,255,0.03)', border:'1px solid rgba(255,255,255,0.06)' }}>
      <span style={{ fontSize:14, color:'#94A3B8' }}>{label}</span>
      <button type="button" onClick={() => onChange(value ? 0 : 1)}
        style={{
          width:36, height:20, borderRadius:10,
          background: value ? '#F4A227' : '#2D3F58',
          position:'relative', transition:'background 0.2s',
          border:'none', cursor:'pointer', flexShrink:0,
        }}>
        <span style={{
          position:'absolute', top:2, left: value ? 18 : 2,
          width:16, height:16, borderRadius:8,
          background:'#fff', transition:'left 0.2s',
        }}/>
      </button>
    </div>
  )
}

// Import ban warning
function ImportBanWarning({ yom }) {
  const y = parseInt(yom)
  if (y >= 2020 && y <= 2023) return (
    <div style={{
      padding:'12px 16px', borderRadius:10, marginTop:8,
      background:'rgba(244,162,39,0.08)',
      border:'1px solid rgba(244,162,39,0.2)',
      fontSize:13, color:'#F4A227', lineHeight:1.6,
    }}>
      ⚠ YOM {y} falls within Sri Lanka's import restriction period (2020–2023).
      This car commands a scarcity premium — expect prices 6–10% above comparable older models.
    </div>
  )
  if (y >= 2024) return (
    <div style={{
      padding:'12px 16px', borderRadius:10, marginTop:8,
      background:'rgba(16,185,129,0.06)',
      border:'1px solid rgba(16,185,129,0.15)',
      fontSize:13, color:'#34D399', lineHeight:1.6,
    }}>
      ✓ YOM {y} is post-ban. Import restrictions lifted — normal supply levels.
    </div>
  )
  return null
}

export default function PredictPage() {
  const [form, setForm]               = useState(INITIAL)
  const [baseResult, setBaseResult]   = useState(null)
  const [econResult, setEconResult]   = useState(null)
  const [loading, setLoading]         = useState(false)
  const [error, setError]             = useState(null)
  const [activeTab, setActiveTab]     = useState('adjusted') // 'base' | 'adjusted'

  const set = (key) => (e) =>
    setForm(f => ({ ...f, [key]: e.target ? e.target.value : e }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setBaseResult(null)
    setEconResult(null)

    const payload = {
      ...form,
      yom:       parseInt(form.yom),
      engine_cc: parseFloat(form.engine_cc),
      mileage:   parseFloat(form.mileage),
    }

    try {
      // Fire both requests in parallel
      const [base, econ] = await Promise.all([
        axios.post(`${API_BASE}/predict`, payload)
          .then(r => r.data).catch(() => null),
        axios.post(`${API_BASE}/predict-with-economics`, payload)
          .then(r => r.data).catch(() => null),
      ])

      setBaseResult(base)
      setEconResult(econ)

      if (!base && !econ) {
        throw new Error('Both endpoints failed. Is your Flask backend running on port 5000?')
      }
    } catch (err) {
      setError(err.message || 'Could not connect to backend.')
    } finally {
      setLoading(false)
    }
  }

  const carAge = new Date().getFullYear() - parseInt(form.yom || 2018)

  return (
    <>
      <Head><title>Price Predictor — CarLensLK</title></Head>
      <main style={{ minHeight:'100vh', paddingTop:96, paddingBottom:80 }}>
        <div className="max-w-6xl mx-auto px-6">

          {/* Header */}
          <div className="mb-12">
            <div className="gold-accent" />
            <h1 style={{
              fontFamily:'Syne, sans-serif',
              fontSize:'clamp(28px,4vw,48px)',
              fontWeight:800, color:'#F1F5F9',
              letterSpacing:'-1.5px', lineHeight:1.1, marginBottom:12,
            }}>
              Price Predictor
            </h1>
            <p style={{ color:'#64748B', fontSize:16, maxWidth:520 }}>
              Get your car's market value — adjusted for live exchange rates,
              inflation, fuel prices and Sri Lanka's import restrictions.
            </p>
          </div>

          <div className="grid lg:grid-cols-3 gap-8">

            {/* ── Form ── */}
            <form onSubmit={handleSubmit} className="lg:col-span-2 flex flex-col gap-8">

              {/* Identity */}
              <section>
                <h2 style={{ fontFamily:'Syne, sans-serif', fontSize:14, fontWeight:600,
                  color:'#F4A227', marginBottom:20, textTransform:'uppercase', letterSpacing:'0.06em' }}>
                  Vehicle identity
                </h2>
                <div className="grid sm:grid-cols-2 gap-5">
                  <Field label="Brand">
                    <select className="input-field px-4 py-3 text-sm"
                      value={form.brand} onChange={set('brand')}>
                      {BRANDS.map(b => <option key={b}>{b}</option>)}
                    </select>
                  </Field>
                  <Field label="Model name">
                    <input className="input-field px-4 py-3 text-sm"
                      value={form.model} onChange={set('model')}
                      placeholder="e.g. Corolla, Civic" />
                  </Field>
                  <Field label="Year of manufacture" hint={`Car age: ${carAge} year${carAge !== 1 ? 's' : ''}`}>
                    <input className="input-field px-4 py-3 text-sm font-mono"
                      type="number" min="1990" max="2025"
                      value={form.yom} onChange={set('yom')} />
                    <ImportBanWarning yom={form.yom} />
                  </Field>
                  <Field label="Town / City">
                    <input className="input-field px-4 py-3 text-sm"
                      value={form.town} onChange={set('town')}
                      placeholder="e.g. Colombo" />
                  </Field>
                </div>
              </section>

              {/* Specs */}
              <section>
                <h2 style={{ fontFamily:'Syne, sans-serif', fontSize:14, fontWeight:600,
                  color:'#F4A227', marginBottom:20, textTransform:'uppercase', letterSpacing:'0.06em' }}>
                  Specifications
                </h2>
                <div className="grid sm:grid-cols-2 gap-5">
                  <Field label="Engine (cc)">
                    <input className="input-field px-4 py-3 text-sm font-mono"
                      type="number" min="500" max="6000" step="100"
                      value={form.engine_cc} onChange={set('engine_cc')} />
                  </Field>
                  <Field label="Mileage (km)">
                    <input className="input-field px-4 py-3 text-sm font-mono"
                      type="number" min="0" max="500000" step="1000"
                      value={form.mileage} onChange={set('mileage')} />
                  </Field>
                  <Field label="Gear type">
                    <select className="input-field px-4 py-3 text-sm"
                      value={form.gear} onChange={set('gear')}>
                      {GEAR_TYPES.map(g => <option key={g}>{g}</option>)}
                    </select>
                  </Field>
                  <Field label="Fuel type">
                    <select className="input-field px-4 py-3 text-sm"
                      value={form.fuel_type} onChange={set('fuel_type')}>
                      {FUEL_TYPES.map(f => <option key={f}>{f}</option>)}
                    </select>
                  </Field>
                  <Field label="Condition">
                    <select className="input-field px-4 py-3 text-sm"
                      value={form.condition} onChange={set('condition')}>
                      {CONDITIONS.map(c => <option key={c}>{c}</option>)}
                    </select>
                  </Field>
                  <Field label="Leasing">
                    <select className="input-field px-4 py-3 text-sm"
                      value={form.leasing} onChange={set('leasing')}>
                      {LEASING.map(l => <option key={l}>{l}</option>)}
                    </select>
                  </Field>
                </div>
              </section>

              {/* Equipment */}
              <section>
                <h2 style={{ fontFamily:'Syne, sans-serif', fontSize:14, fontWeight:600,
                  color:'#F4A227', marginBottom:20, textTransform:'uppercase', letterSpacing:'0.06em' }}>
                  Equipment
                </h2>
                <div className="grid sm:grid-cols-2 gap-3">
                  <Toggle label="Air conditioning" value={form.air_condition}   onChange={set('air_condition')} />
                  <Toggle label="Power steering"   value={form.power_steering}  onChange={set('power_steering')} />
                  <Toggle label="Power mirrors"    value={form.power_mirror}    onChange={set('power_mirror')} />
                  <Toggle label="Power windows"    value={form.power_window}    onChange={set('power_window')} />
                </div>
              </section>

              <button type="submit" disabled={loading}
                className="btn-primary py-4 text-base w-full"
                style={{ opacity: loading ? 0.7 : 1 }}>
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin" width="18" height="18" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                    </svg>
                    Calculating with live economic data...
                  </span>
                ) : 'Get economically adjusted price'}
              </button>
            </form>

            {/* ── Results panel ── */}
            <div className="flex flex-col gap-4">

              {error && (
                <div className="card p-6" style={{
                  background:'rgba(244,63,94,0.05)',
                  border:'1px solid rgba(244,63,94,0.2)', borderRadius:16 }}>
                  <div style={{ fontSize:14, color:'#FB7185', fontWeight:500, marginBottom:8 }}>
                    Connection error
                  </div>
                  <div style={{ fontSize:13, color:'#64748B', lineHeight:1.6 }}>{error}</div>
                </div>
              )}

              {(baseResult || econResult) && (
                <>
                  {/* Tab switcher */}
                  <div style={{
                    display:'flex', background:'rgba(255,255,255,0.03)',
                    borderRadius:10, padding:4,
                    border:'1px solid rgba(255,255,255,0.06)',
                  }}>
                    {[
                      { key:'adjusted', label:'Adjusted price' },
                      { key:'base',     label:'Base model' },
                    ].map(({ key, label }) => (
                      <button key={key} type="button"
                        onClick={() => setActiveTab(key)}
                        style={{
                          flex:1, padding:'8px 0', borderRadius:8,
                          fontSize:13, fontWeight:500, border:'none',
                          cursor:'pointer', transition:'all 0.2s',
                          background: activeTab === key
                            ? '#F4A227' : 'transparent',
                          color: activeTab === key ? '#0A0F1E' : '#64748B',
                        }}>
                        {label}
                      </button>
                    ))}
                  </div>

                  {/* Adjusted price breakdown */}
                  {activeTab === 'adjusted' && (
                    <PriceBreakdown result={econResult} loading={loading} />
                  )}

                  {/* Base prediction */}
                  {activeTab === 'base' && baseResult && (
                    <div className="card p-7"
                      style={{ border:'1px solid rgba(255,255,255,0.08)' }}>
                      <div style={{ fontSize:12, color:'#64748B', fontWeight:600,
                        textTransform:'uppercase', letterSpacing:'0.08em', marginBottom:16 }}>
                        Raw model output
                      </div>
                      <div style={{
                        fontFamily:'JetBrains Mono, monospace',
                        fontSize:40, fontWeight:700, color:'#94A3B8',
                        lineHeight:1, marginBottom:8,
                      }}>
                        Rs. {baseResult.predicted_price?.toFixed(1)}L
                      </div>
                      <div style={{ fontSize:13, color:'#3D5068', marginBottom:20 }}>
                        Before economic adjustments
                      </div>
                      <div style={{
                        padding:'12px 14px', borderRadius:8,
                        background:'rgba(255,255,255,0.03)',
                        border:'1px solid rgba(255,255,255,0.05)',
                        fontSize:13, color:'#64748B', lineHeight:1.6,
                      }}>
                        This is the Random Forest model's raw prediction based
                        on car specifications only. Switch to "Adjusted price"
                        to see the market-realistic value with live economic factors applied.
                      </div>
                    </div>
                  )}
                </>
              )}

              {/* Tips — shown when no result yet */}
              {!baseResult && !econResult && !loading && (
                <div className="card p-6">
                  <div style={{ fontSize:13, fontWeight:600, color:'#94A3B8',
                    marginBottom:16, textTransform:'uppercase', letterSpacing:'0.06em' }}>
                    What gets adjusted
                  </div>
                  {[
                    { icon:'💱', text:'USD/LKR rate — weak rupee raises all import-related costs' },
                    { icon:'📈', text:'Inflation — older cars depreciate faster in high-inflation periods' },
                    { icon:'⛽', text:'Fuel price — hybrids worth more when petrol is expensive' },
                    { icon:'🚗', text:'Import ban (2020–2023) — scarcity premium on ban-era cars' },
                  ].map(({ icon, text }) => (
                    <div key={text} className="flex gap-3 mb-4">
                      <span style={{ fontSize:16, flexShrink:0 }}>{icon}</span>
                      <span style={{ fontSize:13, color:'#64748B', lineHeight:1.5 }}>{text}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </>
  )
}
