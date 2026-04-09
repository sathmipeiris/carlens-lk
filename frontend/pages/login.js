import Head from 'next/head'
import Link from 'next/link'
import { useState } from 'react'
import { useRouter } from 'next/router'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const { login } = useAuth()
  const router    = useRouter()
  const [form, setForm]     = useState({ email: '', password: '' })
  const [error, setError]   = useState('')
  const [loading, setLoading] = useState(false)

  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(form)
      router.push(router.query.next || '/')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Head><title>Sign in — CarLensLK</title></Head>
      <main style={{
        minHeight: '100vh', paddingTop: 64,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '80px 24px',
        background: 'var(--bg)',
      }}>
        {/* Background glow */}
        <div style={{
          position: 'fixed', top: '30%', left: '50%', transform: 'translate(-50%,-50%)',
          width: 600, height: 600, borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(201,168,76,0.06) 0%, transparent 70%)',
          pointerEvents: 'none',
        }}/>

        <div className="auth-card fade-up">
          {/* Logo */}
          <div style={{ textAlign: 'center', marginBottom: 36 }}>
            <div style={{
              width: 48, height: 48, borderRadius: 12,
              background: 'var(--gold)',
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
              marginBottom: 16,
            }}>
              <span style={{ fontFamily: 'Playfair Display, serif', fontWeight: 800, fontSize: 24, color: '#0C0C0E' }}>C</span>
            </div>
            <h1 style={{
              fontFamily: 'Playfair Display, serif',
              fontSize: 28, fontWeight: 700,
              color: 'var(--text-1)', marginBottom: 8,
            }}>
              Welcome back
            </h1>
            <p style={{ fontSize: 14, color: 'var(--text-2)' }}>
              Sign in to your CarLensLK account
            </p>
          </div>

          {error && (
            <div style={{
              background: 'rgba(239,68,68,0.08)',
              border: '1px solid rgba(239,68,68,0.2)',
              borderRadius: 10, padding: '12px 16px',
              fontSize: 14, color: '#EF4444',
              marginBottom: 20,
            }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div>
              <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-2)', display: 'block', marginBottom: 6 }}>
                Email address
              </label>
              <input
                type="email"
                className="input"
                placeholder="you@example.com"
                value={form.email}
                onChange={set('email')}
                required
                autoComplete="email"
              />
            </div>

            <div>
              <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-2)', display: 'block', marginBottom: 6 }}>
                Password
              </label>
              <input
                type="password"
                className="input"
                placeholder="Your password"
                value={form.password}
                onChange={set('password')}
                required
                autoComplete="current-password"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-gold"
              style={{ width: '100%', marginTop: 8, padding: '14px', fontSize: 15, opacity: loading ? 0.7 : 1 }}
            >
              {loading ? (
                <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <svg style={{ animation: 'spin 1s linear infinite' }} width="16" height="16" fill="none" viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" strokeOpacity="0.25"/>
                    <path fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                  </svg>
                  Signing in...
                </span>
              ) : 'Sign in'}
            </button>
          </form>

          <div className="divider">or</div>

          <p style={{ textAlign: 'center', fontSize: 14, color: 'var(--text-2)' }}>
            Don't have an account?{' '}
            <Link href="/signup" style={{ color: 'var(--gold)', fontWeight: 600, textDecoration: 'none' }}>
              Create one free
            </Link>
          </p>
        </div>
      </main>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </>
  )
}
