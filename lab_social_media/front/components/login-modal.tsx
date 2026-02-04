"use client"

import React from "react"

import { useState } from "react"
import { Loader2, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useAuth } from "@/contexts/auth-context"

export function LoginModal() {
  const { user, isLoading, login, register } = useAuth()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState("login")

  // Login form state
  const [loginUsername, setLoginUsername] = useState("")
  const [loginPassword, setLoginPassword] = useState("")

  // Register form state
  const [registerUsername, setRegisterUsername] = useState("")
  const [registerPassword, setRegisterPassword] = useState("")
  const [registerConfirmPassword, setRegisterConfirmPassword] = useState("")

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)

    if (!loginUsername.trim() || !loginPassword.trim()) {
      setError("Por favor completa todos los campos")
      setIsSubmitting(false)
      return
    }

    const success = await login(loginUsername.trim(), loginPassword)
    
    if (!success) {
      setError("Usuario o contrasena incorrectos")
    }
    
    setIsSubmitting(false)
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)

    if (!registerUsername.trim() || !registerPassword.trim() || !registerConfirmPassword.trim()) {
      setError("Por favor completa todos los campos")
      setIsSubmitting(false)
      return
    }

    if (registerUsername.trim().length < 3) {
      setError("El usuario debe tener al menos 3 caracteres")
      setIsSubmitting(false)
      return
    }

    if (registerPassword.length < 4) {
      setError("La contrasena debe tener al menos 4 caracteres")
      setIsSubmitting(false)
      return
    }

    if (registerPassword !== registerConfirmPassword) {
      setError("Las contrasenas no coinciden")
      setIsSubmitting(false)
      return
    }

    const success = await register(registerUsername.trim(), registerPassword)
    
    if (!success) {
      setError("Este usuario ya existe. Intenta con otro nombre.")
    }
    
    setIsSubmitting(false)
  }

  // Don't show modal while checking for existing session
  if (isLoading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-muted-foreground">Cargando...</p>
        </div>
      </div>
    )
  }

  // Don't show modal if user is logged in
  if (user) {
    return null
  }

  return (
    <Dialog open={true}>
      <DialogContent className="sm:max-w-md" onPointerDownOutside={(e) => e.preventDefault()}>
        <DialogHeader className="text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-primary text-primary-foreground font-bold text-xl">
            SSA
          </div>
          <DialogTitle className="text-xl">Sentiment Social Analyzer</DialogTitle>
          <DialogDescription>
            Analiza el sentimiento en redes sociales con inteligencia artificial
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-4">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="login">Iniciar sesion</TabsTrigger>
            <TabsTrigger value="register">Registrarse</TabsTrigger>
          </TabsList>

          <TabsContent value="login" className="mt-4">
            <form onSubmit={handleLogin} className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
              
              <div className="space-y-2">
                <Label htmlFor="login-username">Usuario</Label>
                <Input
                  id="login-username"
                  type="text"
                  placeholder="Tu nombre de usuario"
                  value={loginUsername}
                  onChange={(e) => setLoginUsername(e.target.value)}
                  disabled={isSubmitting}
                  autoComplete="username"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="login-password">Contrasena</Label>
                <Input
                  id="login-password"
                  type="password"
                  placeholder="Tu contrasena"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  disabled={isSubmitting}
                  autoComplete="current-password"
                />
              </div>

              <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Iniciando sesion...
                  </>
                ) : (
                  "Iniciar sesion"
                )}
              </Button>
            </form>
          </TabsContent>

          <TabsContent value="register" className="mt-4">
            <form onSubmit={handleRegister} className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
              
              <div className="space-y-2">
                <Label htmlFor="register-username">Usuario</Label>
                <Input
                  id="register-username"
                  type="text"
                  placeholder="Elige un nombre de usuario"
                  value={registerUsername}
                  onChange={(e) => setRegisterUsername(e.target.value)}
                  disabled={isSubmitting}
                  autoComplete="username"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="register-password">Contrasena</Label>
                <Input
                  id="register-password"
                  type="password"
                  placeholder="Crea una contrasena"
                  value={registerPassword}
                  onChange={(e) => setRegisterPassword(e.target.value)}
                  disabled={isSubmitting}
                  autoComplete="new-password"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="register-confirm-password">Confirmar contrasena</Label>
                <Input
                  id="register-confirm-password"
                  type="password"
                  placeholder="Repite la contrasena"
                  value={registerConfirmPassword}
                  onChange={(e) => setRegisterConfirmPassword(e.target.value)}
                  disabled={isSubmitting}
                  autoComplete="new-password"
                />
              </div>

              <Button type="submit" className="w-full" disabled={isSubmitting}>
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creando cuenta...
                  </>
                ) : (
                  "Crear cuenta"
                )}
              </Button>
            </form>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
