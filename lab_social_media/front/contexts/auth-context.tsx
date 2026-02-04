"use client"

import { createContext, useContext, useState, useEffect, type ReactNode } from "react"

export interface User {
  id: string
  username: string
  createdAt: string
}

interface AuthContextType {
  user: User | null
  isLoading: boolean
  login: (username: string, password: string) => Promise<boolean>
  register: (username: string, password: string) => Promise<boolean>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check for existing session
    const storedUser = localStorage.getItem("ssa_user")
    if (storedUser) {
      setUser(JSON.parse(storedUser))
    }
    setIsLoading(false)
  }, [])

  const login = async (username: string, password: string): Promise<boolean> => {
    // Get stored users
    const storedUsers = localStorage.getItem("ssa_users")
    const users: Record<string, { password: string; id: string; createdAt: string }> = storedUsers 
      ? JSON.parse(storedUsers) 
      : {}

    // Check if user exists and password matches
    if (users[username] && users[username].password === password) {
      const loggedUser: User = {
        id: users[username].id,
        username,
        createdAt: users[username].createdAt,
      }
      setUser(loggedUser)
      localStorage.setItem("ssa_user", JSON.stringify(loggedUser))
      return true
    }
    
    return false
  }

  const register = async (username: string, password: string): Promise<boolean> => {
    // Get stored users
    const storedUsers = localStorage.getItem("ssa_users")
    const users: Record<string, { password: string; id: string; createdAt: string }> = storedUsers 
      ? JSON.parse(storedUsers) 
      : {}

    // Check if user already exists
    if (users[username]) {
      return false
    }

    // Create new user
    const newUser = {
      password,
      id: crypto.randomUUID(),
      createdAt: new Date().toISOString(),
    }
    
    users[username] = newUser
    localStorage.setItem("ssa_users", JSON.stringify(users))

    // Auto login after register
    const loggedUser: User = {
      id: newUser.id,
      username,
      createdAt: newUser.createdAt,
    }
    setUser(loggedUser)
    localStorage.setItem("ssa_user", JSON.stringify(loggedUser))
    
    return true
  }

  const logout = () => {
    setUser(null)
    localStorage.removeItem("ssa_user")
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
