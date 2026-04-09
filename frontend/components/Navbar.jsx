import Link from 'next/link'
import { useRouter } from 'next/router'
import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'

const navLinks = [
  { href: '/',          label: 'Home' },
  { href: '/predict',   label: 'Predictor' },
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/trends',    label: 'Trends' },
]

function MoonIcon() {
  return (
    <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <path d="M21 12.79A9 9 0 1111.21 3a7 7 0 109.79 9.79z" strokeLinecap="round"/>
    </svg>
  )
}

function SunIcon() {
  return (
    <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="5"/>
      <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" strokeLinecap="round"/>
    </svg>
  )
}

export default function Navbar() {
  const router    = useRouter()
  const { user, logout } = useAuth()
  const { theme, toggle, isDark } = useTheme()
  const [scrolled, setScrolled]   = useState(false)
  const [menuOpen, setMenuOpen]   = useState(false)
  const [userMenu, setUserMenu]   = useState(false)
  const userMenuRef = useRef(null)

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', handler)
    return () => window.removeEventListener('scroll', handler)
  }, [])

  useEffect(() => {
    const handler = (e) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target)) {
        setUserMenu(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const navBg = scrolled
    ? isDark
      ? 'rgba(12,12,14,0.92)'
      : 'rgba(245,242,236,0.92)'
    : 'transparent'

  return (
    <nav
      style={{
        background:    navBg,
        backdropFilter: scrolled ? 'blur(20px)' : 'none',
        borderBottom:  scrolled ? '1px solid var(--border)' : '1px solid transparent',
        transition:    'all 0.3s ease',
        position:      'fixed',
        top: 0, left: 0, right: 0,
        zIndex: 100,
      }}
    >
      <div style={{ maxWidth: 1280, margin: '0 auto', padding: '0 24px', height: 64, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>

        {/* Logo */}
        <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none' }}>
          <div style={{
            width: 34, height: 34,
            background: 'var(--gold)',
            borderRadius: 8,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <span style={{ fontFamily: 'Playfair Display, serif', fontWeight: 700, fontSize: 18, color: '#0C0C0E' }}>C</span>
          </div>
          <span style={{ fontFamily: 'Playfair Display, serif', fontWeight: 700, fontSize: 20, color: 'var(--text-1)', letterSpacing: '-0.5px' }}>
            CarLens<span style={{ color: 'var(--gold)' }}>LK</span>
          </span>
        </Link>

        {/* Desktop Nav */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }} className="hidden md:flex">
          {navLinks.map(link => (
            <Link key={link.href} href={link.href}
              className={`nav-link ${router.pathname === link.href ? 'active' : ''}`}>
              {link.label}
            </Link>
          ))}
        </div>

        {/* Right actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {/* Theme toggle */}
          <button onClick={toggle} style={{
            width: 36, height: 36,
            borderRadius: 8,
            border: '1px solid var(--border)',
            background: 'var(--bg-card2)',
            color: 'var(--text-2)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
          onMouseEnter={e => e.currentTarget.style.color = 'var(--gold)'}
          onMouseLeave={e => e.currentTarget.style.color = 'var(--text-2)'}
          >
            {isDark ? <SunIcon /> : <MoonIcon />}
          </button>

          {/* Auth */}
          {user ? (
            <div ref={userMenuRef} style={{ position: 'relative' }}>
              <button
                onClick={() => setUserMenu(!userMenu)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 8,
                  background: 'var(--bg-card2)',
                  border: '1px solid var(--border)',
                  borderRadius: 10,
                  padding: '6px 12px',
                  cursor: 'pointer',
                  color: 'var(--text-1)',
                  fontSize: 14,
                  fontWeight: 500,
                }}
              >
                <div style={{
                  width: 26, height: 26, borderRadius: '50%',
                  background: 'var(--gold)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 11, fontWeight: 700, color: '#0C0C0E',
                }}>
                  {user.name?.charAt(0).toUpperCase()}
                </div>
                <span className="hidden md:block">{user.name?.split(' ')[0]}</span>
                <svg width="12" height="12" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path d="M6 9l6 6 6-6" strokeLinecap="round"/>
                </svg>
              </button>

              {userMenu && (
                <div style={{
                  position: 'absolute', top: '100%', right: 0, marginTop: 8,
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border)',
                  borderRadius: 12,
                  padding: 8,
                  minWidth: 180,
                  boxShadow: 'var(--shadow)',
                  zIndex: 200,
                }}>
                  <div style={{ padding: '8px 12px', fontSize: 12, color: 'var(--text-3)', borderBottom: '1px solid var(--border)', marginBottom: 8 }}>
                    {user.email}
                  </div>
                  <Link href="/predict" onClick={() => setUserMenu(false)} style={{
                    display: 'block', padding: '10px 12px', fontSize: 14,
                    color: 'var(--text-1)', borderRadius: 8,
                    textDecoration: 'none',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                  >
                    Price Predictor
                  </Link>
                  <button onClick={() => { setUserMenu(false); logout() }} style={{
                    display: 'block', width: '100%', textAlign: 'left',
                    padding: '10px 12px', fontSize: 14,
                    color: '#EF4444', background: 'transparent',
                    border: 'none', borderRadius: 8, cursor: 'pointer',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(239,68,68,0.08)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                  >
                    Sign out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="hidden md:flex items-center gap-2">
              <Link href="/login" className="btn-ghost" style={{ padding: '8px 18px', fontSize: 13 }}>
                Sign in
              </Link>
              <Link href="/signup" className="btn-gold" style={{ padding: '8px 18px', fontSize: 13 }}>
                Get started
              </Link>
            </div>
          )}

          {/* Mobile hamburger */}
          <button className="md:hidden" onClick={() => setMenuOpen(!menuOpen)} style={{
            background: 'none', border: 'none', color: 'var(--text-2)', cursor: 'pointer', padding: 4,
          }}>
            <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
              {menuOpen
                ? <path d="M6 6l12 12M6 18L18 6" strokeLinecap="round"/>
                : <path d="M3 6h18M3 12h18M3 18h18" strokeLinecap="round"/>}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div style={{
          background: isDark ? 'rgba(12,12,14,0.98)' : 'rgba(245,242,236,0.98)',
          borderBottom: '1px solid var(--border)',
          padding: '12px 24px 20px',
        }}>
          {navLinks.map(link => (
            <Link key={link.href} href={link.href}
              onClick={() => setMenuOpen(false)}
              className={`block py-3 nav-link ${router.pathname === link.href ? 'active' : ''}`}>
              {link.label}
            </Link>
          ))}
          <div style={{ borderTop: '1px solid var(--border)', paddingTop: 16, marginTop: 8, display: 'flex', gap: 8 }}>
            {user ? (
              <button onClick={logout} className="btn-ghost" style={{ fontSize: 13 }}>Sign out</button>
            ) : (
              <>
                <Link href="/login" className="btn-ghost" style={{ fontSize: 13 }}>Sign in</Link>
                <Link href="/signup" className="btn-gold" style={{ fontSize: 13 }}>Get started</Link>
              </>
            )}
          </div>
        </div>
      )}
    </nav>
  )
}
