// frontend/context/AuthContext.js
import { createContext, useContext, useState, useEffect } from 'react'
import { useRouter } from 'next/router'

const AuthContext = createContext(null)

// Simple users store in localStorage
// To upgrade to a real DB: replace these functions with API calls
const USERS_KEY = 'carlens_users'
const SESSION_KEY = 'carlens_session'

function getUsers() {
  if (typeof window === 'undefined') return []
  try { return JSON.parse(localStorage.getItem(USERS_KEY) || '[]') } catch { return [] }
}

function saveUsers(users) {
  localStorage.setItem(USERS_KEY, JSON.stringify(users))
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    // Restore session on mount
    try {
      const session = JSON.parse(localStorage.getItem(SESSION_KEY) || 'null')
      if (session?.email) setUser(session)
    } catch {}
    setLoading(false)
  }, [])

  const signup = async ({ name, email, password }) => {
    const users = getUsers()
    if (users.find(u => u.email === email)) {
      throw new Error('An account with this email already exists')
    }
    const newUser = {
      id:        Date.now().toString(),
      name,
      email,
      password,  // In production: hash this with bcrypt via API
      createdAt: new Date().toISOString(),
    }
    saveUsers([...users, newUser])
    const session = { id: newUser.id, name, email }
    localStorage.setItem(SESSION_KEY, JSON.stringify(session))
    setUser(session)
    return session
  }

  const login = async ({ email, password }) => {
    const users = getUsers()
    const found = users.find(u => u.email === email && u.password === password)
    if (!found) throw new Error('Invalid email or password')
    const session = { id: found.id, name: found.name, email: found.email }
    localStorage.setItem(SESSION_KEY, JSON.stringify(session))
    setUser(session)
    return session
  }

  const logout = () => {
    localStorage.removeItem(SESSION_KEY)
    setUser(null)
    router.push('/')
  }

  return (
    <AuthContext.Provider value={{ user, loading, signup, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
