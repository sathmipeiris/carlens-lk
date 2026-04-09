import Head from 'next/head'
import { useState } from 'react'
import { predictPrice } from '../lib/api'

const BRANDS = ['TOYOTA', 'HONDA', 'SUZUKI', 'BMW', 'MERCEDES-BENZ', 'AUDI', 'NISSAN', 'MITSUBISHI', 'HYUNDAI', 'KIA', 'MAZDA', 'FORD', 'LAND ROVER', 'LEXUS', 'SUBARU', 'VOLKSWAGEN']
const FUEL_TYPES = ['Petrol', 'Diesel', 'Hybrid', 'Electric', 'Gas']
const GEAR_TYPES = ['Automatic', 'Manual', 'Semi-Automatic', 'CVT']
const LEASING = ['No Leasing', 'Leasing Available', 'Fully Leased']
const CONDITIONS = ['USED', 'RECONDITIONED', 'BRAND NEW']

const INITIAL = {
  brand: 'TOYOTA', model: 'Corolla', yom: 2018, engine_cc: 1800,
  mileage: 60000, gear: 'Automatic', fuel_type: 'Petrol',
  town: 'Colombo', leasing: 'No Leasing', condition: 'USED',
  air_condition: 1, power_steering: 1, power_mirror: 1, power_window: 1,
}

function Field({ label, children, hint }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label style={{ fontSize: 13, color: '#64748B', fontWeight: 500 }}>{label}</label>
      {children}
      {hint && <span style={{ fontSize: 12, color: '#2D3F58' }}>{hint}</span>}
    </div>
  )
}

function Toggle({ label, value, onChange }) {
  return (
    <div className="flex items-center justify-between p-4 rounded-xl" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
      <span style={{ fontSize: 14, color: '#94A3B8' }}>{label}</span>
      <button
        type="button"
        onClick={() => onChange(value ? 0 : 1)}
        style={{
          width: 44,
          height: 24,
          borderRadius: 12,
          background: value ? '#F4A227' : '#2D3F58',
          position: 'relative',
          transition: 'background 0.2s',
          border: 'none',
          cursor: 'pointer',
        }}
      >
        <span
          style={{
            position: 'absolute',
            top: 2,
            left: value ? 22 : 2,
            width: 20,
            height: 20,
            borderRadius: 10,
            background: '#fff',
            transition: 'left 0.2s',
          }}
        />
      </button>
    </div>
  )
}

export default function PredictPage() {
  const [form, setForm] = useState(INITIAL)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const set = (key) => (e) =>
    setForm((f) => ({ ...f, [key]: e.target ? e.target.value : e }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const payload = {
        ...form,
        yom: parseInt(form.yom),
        engine_cc: parseFloat(form.engine_cc),
        mileage: parseFloat(form.mileage),
      }
      const res = await predictPrice(payload)
      setResult(res)
    } catch (err) {
      setError(err.response?.data?.error || 'Could not connect to the API. Make sure your Flask backend is running on port 5000.')
    } finally {
      setLoading(false)
    }
  }

  const carAge = new Date().getFullYear() - parseInt(form.yom || 2018)

  return (
    <>
      <Head>
        <title>Price Predictor — CarLensLK</title>
      </Head>
      <main style={{ minHeight: '100vh', paddingTop: 96, paddingBottom: 80 }}>
        <div className="max-w-6xl mx-auto px-6">
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
              Price Predictor
            </h1>
            <p style={{ color: '#64748B', fontSize: 16 }}>
              Fill in your car details and our model will estimate its Sri Lankan market value.
            </p>
          </div>

          <div className="grid lg:grid-cols-3 gap-8">
            {/* Form */}
            <form onSubmit={handleSubmit} className="lg:col-span-2 flex flex-col gap-8">
              {/* Identity */}
              <section>
                <h2 style={{ fontFamily: 'Syne, sans-serif', fontSize: 16, fontWeight: 600, color: '#F4A227', marginBottom: 20, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  Vehicle identity
                </h2>
                <div className="grid sm:grid-cols-2 gap-5">
                  <Field label="Brand">
                    <select className="input-field px-4 py-3 text-sm" value={form.brand} onChange={set('brand')}>
                      {BRANDS.map(b => <option key={b}>{b}</option>)}
                    </select>
                  </Field>
                  <Field label="Model name">
                    <input className="input-field px-4 py-3 text-sm" value={form.model} onChange={set('model')} placeholder="e.g. Corolla, Civic" />
                  </Field>
                  <Field label="Year of manufacture" hint={`Car age: ${carAge} years`}>
                    <input className="input-field px-4 py-3 text-sm font-mono" type="number" min="1990" max="2025" value={form.yom} onChange={set('yom')} />
                  </Field>
                  <Field label="Town / City">
                    <input className="input-field px-4 py-3 text-sm" value={form.town} onChange={set('town')} placeholder="e.g. Colombo" />
                  </Field>
                </div>
              </section>

              {/* Specs */}
              <section>
                <h2 style={{ fontFamily: 'Syne, sans-serif', fontSize: 16, fontWeight: 600, color: '#F4A227', marginBottom: 20, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  Specifications
                </h2>
                <div className="grid sm:grid-cols-2 gap-5">
                  <Field label="Engine (cc)">
                    <input className="input-field px-4 py-3 text-sm font-mono" type="number" min="500" max="6000" step="100" value={form.engine_cc} onChange={set('engine_cc')} />
                  </Field>
                  <Field label="Mileage (km)">
                    <input className="input-field px-4 py-3 text-sm font-mono" type="number" min="0" max="500000" step="1000" value={form.mileage} onChange={set('mileage')} />
                  </Field>
                  <Field label="Gear type">
                    <select className="input-field px-4 py-3 text-sm" value={form.gear} onChange={set('gear')}>
                      {GEAR_TYPES.map(g => <option key={g}>{g}</option>)}
                    </select>
                  </Field>
                  <Field label="Fuel type">
                    <select className="input-field px-4 py-3 text-sm" value={form.fuel_type} onChange={set('fuel_type')}>
                      {FUEL_TYPES.map(f => <option key={f}>{f}</option>)}
                    </select>
                  </Field>
                  <Field label="Condition">
                    <select className="input-field px-4 py-3 text-sm" value={form.condition} onChange={set('condition')}>
                      {CONDITIONS.map(c => <option key={c}>{c}</option>)}
                    </select>
                  </Field>
                  <Field label="Leasing">
                    <select className="input-field px-4 py-3 text-sm" value={form.leasing} onChange={set('leasing')}>
                      {LEASING.map(l => <option key={l}>{l}</option>)}
                    </select>
                  </Field>
                </div>
              </section>

              {/* Equipment */}
              <section>
                <h2 style={{ fontFamily: 'Syne, sans-serif', fontSize: 16, fontWeight: 600, color: '#F4A227', marginBottom: 20, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  Equipment
                </h2>
                <div className="grid sm:grid-cols-2 gap-3">
                  <Toggle label="Air conditioning" value={form.air_condition} onChange={set('air_condition')} />
                  <Toggle label="Power steering" value={form.power_steering} onChange={set('power_steering')} />
                  <Toggle label="Power mirrors" value={form.power_mirror} onChange={set('power_mirror')} />
                  <Toggle label="Power windows" value={form.power_window} onChange={set('power_window')} />
                </div>
              </section>

              <button
                type="submit"
                disabled={loading}
                className="btn-primary py-4 text-base w-full"
                style={{ opacity: loading ? 0.7 : 1 }}
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin" width="18" height="18" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                    </svg>
                    Calculating...
                  </span>
                ) : 'Get price estimate'}
              </button>
            </form>

            {/* Result panel */}
            <div className="flex flex-col gap-4">
              {/* Result */}
              {result && (
                <div
                  className="card p-8"
                  style={{ border: '1px solid rgba(244,162,39,0.3)', background: 'rgba(244,162,39,0.04)' }}
                >
                  <div style={{ fontSize: 12, color: '#F4A227', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 16 }}>
                    Estimated market value
                  </div>
                  <div
                    style={{
                      fontFamily: 'JetBrains Mono, monospace',
                      fontSize: 42,
                      fontWeight: 700,
                      color: '#F4A227',
                      lineHeight: 1,
                      marginBottom: 8,
                    }}
                  >
                    Rs. {result.predicted_price?.toFixed(1)}L
                  </div>
                  <div style={{ fontSize: 14, color: '#3D5068', marginBottom: 24 }}>
                    LKR Lakhs · {result.confidence || 'R² 92.5%'}
                  </div>
                  <div
                    style={{
                      borderTop: '1px solid rgba(255,255,255,0.06)',
                      paddingTop: 20,
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 12,
                    }}
                  >
                    {[
                      { k: 'Brand', v: form.brand },
                      { k: 'Year', v: form.yom },
                      { k: 'Mileage', v: `${parseInt(form.mileage).toLocaleString()} km` },
                      { k: 'Fuel', v: form.fuel_type },
                    ].map(({ k, v }) => (
                      <div key={k} className="flex justify-between">
                        <span style={{ fontSize: 13, color: '#3D5068' }}>{k}</span>
                        <span style={{ fontSize: 13, color: '#94A3B8', fontFamily: 'JetBrains Mono, monospace' }}>{v}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {error && (
                <div className="card p-6 badge-red" style={{ background: 'rgba(244,63,94,0.05)', border: '1px solid rgba(244,63,94,0.2)', borderRadius: 16 }}>
                  <div style={{ fontSize: 14, color: '#FB7185', fontWeight: 500, marginBottom: 8 }}>Connection error</div>
                  <div style={{ fontSize: 13, color: '#64748B', lineHeight: 1.6 }}>{error}</div>
                </div>
              )}

              {/* Tips */}
              <div className="card p-6">
                <div style={{ fontSize: 13, fontWeight: 600, color: '#94A3B8', marginBottom: 16, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  Tips for accuracy
                </div>
                {[
                  'Use the exact registered brand name',
                  'Enter mileage from the odometer',
                  'Reconditioned cars are typically priced higher',
                  'Hybrid premium increases with fuel prices',
                ].map((tip) => (
                  <div key={tip} className="flex gap-3 mb-3">
                    <span style={{ color: '#F4A227', fontSize: 16 }}>›</span>
                    <span style={{ fontSize: 13, color: '#64748B', lineHeight: 1.5 }}>{tip}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    </>
  )
}
