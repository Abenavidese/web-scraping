"use client"

import { useState } from "react"
import { Bell, Globe, Save } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useAuth } from "@/contexts/auth-context"

export default function ConfiguracionPage() {
  const { user } = useAuth()
  const [notifications, setNotifications] = useState({
    email: true,
    analysis: true,
    marketing: false,
    weekly: true,
  })

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Configuracion</h1>
        <p className="text-muted-foreground">
          Preferencias de la aplicacion para {user?.username || "usuario"}
        </p>
      </div>

      <Tabs defaultValue="notificaciones" className="space-y-6">
        <TabsList>
          <TabsTrigger value="notificaciones">Notificaciones</TabsTrigger>
          <TabsTrigger value="preferencias">Preferencias</TabsTrigger>
        </TabsList>

        {/* Notifications Tab */}
        <TabsContent value="notificaciones" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5" />
                Notificaciones
              </CardTitle>
              <CardDescription>
                Configura como quieres recibir actualizaciones
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Notificaciones por email</p>
                  <p className="text-sm text-muted-foreground">
                    Recibe un resumen de tus actividades por correo
                  </p>
                </div>
                <Switch
                  checked={notifications.email}
                  onCheckedChange={(checked) =>
                    setNotifications(prev => ({ ...prev, email: checked }))
                  }
                />
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Analisis completados</p>
                  <p className="text-sm text-muted-foreground">
                    Notificacion cuando un analisis termine
                  </p>
                </div>
                <Switch
                  checked={notifications.analysis}
                  onCheckedChange={(checked) =>
                    setNotifications(prev => ({ ...prev, analysis: checked }))
                  }
                />
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Reporte semanal</p>
                  <p className="text-sm text-muted-foreground">
                    Resumen semanal de tu consumo y actividad
                  </p>
                </div>
                <Switch
                  checked={notifications.weekly}
                  onCheckedChange={(checked) =>
                    setNotifications(prev => ({ ...prev, weekly: checked }))
                  }
                />
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Novedades y promociones</p>
                  <p className="text-sm text-muted-foreground">
                    Informacion sobre nuevas funciones y ofertas
                  </p>
                </div>
                <Switch
                  checked={notifications.marketing}
                  onCheckedChange={(checked) =>
                    setNotifications(prev => ({ ...prev, marketing: checked }))
                  }
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Preferences Tab */}
        <TabsContent value="preferencias" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="h-5 w-5" />
                Preferencias generales
              </CardTitle>
              <CardDescription>
                Personaliza tu experiencia en la plataforma
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label>Idioma de la interfaz</Label>
                  <Select defaultValue="es">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="es">Espanol</SelectItem>
                      <SelectItem value="en">English</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Zona horaria</Label>
                  <Select defaultValue="madrid">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="madrid">Madrid (UTC+1)</SelectItem>
                      <SelectItem value="mexico">Mexico City (UTC-6)</SelectItem>
                      <SelectItem value="bogota">Bogota (UTC-5)</SelectItem>
                      <SelectItem value="buenos_aires">Buenos Aires (UTC-3)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Separator />

              <div className="space-y-2">
                <Label>Idioma predeterminado para analisis</Label>
                <Select defaultValue="ES">
                  <SelectTrigger className="w-full sm:w-[200px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ES">Espanol</SelectItem>
                    <SelectItem value="EN">English</SelectItem>
                    <SelectItem value="AUTO">Auto-detectar</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  Este sera el idioma seleccionado por defecto en nuevas consultas
                </p>
              </div>

              <Separator />

              <div className="space-y-2">
                <Label>Nivel de limpieza predeterminado</Label>
                <Select defaultValue="normal">
                  <SelectTrigger className="w-full sm:w-[200px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="basico">Basico</SelectItem>
                    <SelectItem value="normal">Normal</SelectItem>
                    <SelectItem value="agresivo">Agresivo</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  Nivel de preprocesamiento NLP por defecto
                </p>
              </div>

              <div className="flex justify-end">
                <Button>
                  <Save className="h-4 w-4 mr-2" />
                  Guardar preferencias
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card className="border-destructive/50">
            <CardHeader>
              <CardTitle className="text-destructive">Zona de peligro</CardTitle>
              <CardDescription>
                Acciones irreversibles
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Eliminar todos los datos</p>
                  <p className="text-sm text-muted-foreground">
                    Borra todo tu historial de consultas y resultados
                  </p>
                </div>
                <Button variant="outline" className="text-destructive border-destructive/50 hover:bg-destructive/10 bg-transparent">
                  Eliminar datos
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
