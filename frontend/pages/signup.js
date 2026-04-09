import Head from 'next/head'
import Link from 'next/link'
import { useState } from 'react'
import { useRouter } from 'next/router'
import { useAuth } from '../context/AuthContext'

export default function SignupPage() {
  const { signup } = useAuth()
  const router     = useRouter()
  const [form, setForm]     = useState({ name: '', email: '', password: '', confirm: '' })
  const [error, setError]   = useState('')
  const [loading, setLoading] = useState(false)

  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (form.password !== form.confirm) {
      setError('Passwords do not match')
      return
    }
    if (form.password.length < 6) {
      setError('Password must be at least 6 characters')
      return
    }
    setLoading(true)
    try {
      await signup({ name: form.name, email: form.email, password: form.password })
      router.push('/')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const strength = form.password.length === 0 ? 0
    : form.password.length < 6 ? 1
    : form.password.length < 10 ? 2 : 3

  const strengthLabel = ['', 'Weak', 'Good', 'Strong']
  const strengthColor = ['', '#EF4444', '#F59E0B', '#10B981']

  return (
    <>
      <Head><title>Create account — CarLensLK</title></Head>
      <main style={{
        minHeight: '100vh', paddingTop: 64,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '80px 24px',
        background: 'var(--bg)',
      }}>
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
              Create your account
            </h1>
            <p style={{ fontSize: 14, color: 'var(--text-2)' }}>
              Free forever. No credit card required.
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
                Full name
              </label>
              <input
                type="text"
                className="input"
                placeholder="Sathmi Peiris"
                value={form.name}
                onChange={set('name')}
                required
              />
            </div>

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
                placeholder="At least 6 characters"
                value={form.password}
                onChange={set('password')}
                required
                autoComplete="new-password"
              />
              {form.password.length > 0 && (
                <div style={{ marginTop: 8, display: 'flex', gap: 4, alignItems: 'center' }}>
                  {[1,2,3].map(i => (
                    <div key={i} style={{
                      height: 3, flex: 1, borderRadius: 2,
                      background: i <= strength ? strengthColor[strength] : 'var(--border)',
                      transition: 'background 0.2s',
                    }}/>
                  ))}
                  <span style={{ fontSize: 11, color: strengthColor[strength], marginLeft: 4, fontWeight: 600 }}>
                    {strengthLabel[strength]}
                  </span>
                </div>
              )}
            </div>

            <div>
              <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-2)', display: 'block', marginBottom: 6 }}>
                Confirm password
              </label>
              <input
                type="password"
                className="input"
                placeholder="Repeat your password"
                value={form.confirm}
                onChange={set('confirm')}
                required
                autoComplete="new-password"
              />
              {form.confirm && form.password !== form.confirm && (
                <p style={{ fontSize: 12, color: '#EF4444', marginTop: 6 }}>Passwords don't match</p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-gold"
              style={{ width: '100%', marginTop: 8, padding: '14px', fontSize: 15, opacity: loading ? 0.7 : 1 }}
            >
              {loading ? (
                <span style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'center' }}>
                  <svg style={{ animation: 'spin 1s linear infinite' }} width="16" height="16" fill="none" viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" strokeOpacity="0.25"/>
                    <path fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                  </svg>
                  Creating account...
                </span>
              ) : 'Create free account'}
            </button>
          </form>

          <div className="divider">already have an account?</div>

          <Link href="/login" className="btn-ghost" style={{ display: 'block', textAlign: 'center', textDecoration: 'none', padding: '12px' }}>
            Sign in instead
          </Link>
        </div>
      </main>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </>
  )
}
