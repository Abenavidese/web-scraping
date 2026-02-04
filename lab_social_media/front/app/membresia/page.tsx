"use client"

import { Check, CreditCard, Calendar, TrendingUp, Zap, Info } from "lucide-react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { plans, currentUserPlan } from "@/lib/mock-data"

export default function MembresiaPage() {
  const currentPlan = plans.find(p => p.id === currentUserPlan.planId)
  const usagePercent = (currentUserPlan.wordsUsed / currentUserPlan.wordsLimit) * 100

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Membresia</h1>
          <p className="text-muted-foreground">
            Gestiona tu plan y consumo mensual
          </p>
        </div>

        {/* Current Plan Status */}
        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Plan actual</CardTitle>
                  <CardDescription>Tu suscripcion activa</CardDescription>
                </div>
                <Badge className="bg-primary">{currentPlan?.name}</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Usage Bar */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Consumo de palabras</span>
                  <span className="text-sm text-muted-foreground">
                    {currentUserPlan.wordsUsed.toLocaleString()} / {currentUserPlan.wordsLimit.toLocaleString()}
                  </span>
                </div>
                <Progress value={usagePercent} className="h-3" />
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>{Math.round(usagePercent)}% utilizado</span>
                  <span>{(currentUserPlan.wordsLimit - currentUserPlan.wordsUsed).toLocaleString()} palabras disponibles</span>
                </div>
              </div>

              <Separator />

              {/* Plan Details */}
              <div className="grid gap-4 sm:grid-cols-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <TrendingUp className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Palabras/mes</p>
                    <p className="font-medium">{currentPlan?.wordsPerMonth.toLocaleString()}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <Zap className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Redes sociales</p>
                    <p className="font-medium">{currentPlan?.maxNetworks} redes</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <Calendar className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Renovacion</p>
                    <p className="font-medium">{currentUserPlan.daysRemaining} dias</p>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Features */}
              <div>
                <p className="text-sm font-medium mb-3">Incluido en tu plan</p>
                <div className="grid gap-2 sm:grid-cols-2">
                  {currentPlan?.features.map((feature, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm">
                      <Check className="h-4 w-4 text-success" />
                      <span>{feature}</span>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
            <CardFooter className="flex gap-4">
              <Button variant="outline" className="flex-1 bg-transparent">
                <CreditCard className="h-4 w-4 mr-2" />
                Gestionar pago
              </Button>
              <Button className="flex-1">
                Actualizar plan
              </Button>
            </CardFooter>
          </Card>

          {/* Usage Rules */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Reglas de consumo</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3 text-sm">
                <div className="flex items-start gap-2">
                  <Info className="h-4 w-4 text-muted-foreground mt-0.5" />
                  <p className="text-muted-foreground">
                    Se descuenta por <span className="text-foreground font-medium">palabras procesadas</span> 
                    (texto extraido + query).
                  </p>
                </div>
                <div className="flex items-start gap-2">
                  <Info className="h-4 w-4 text-muted-foreground mt-0.5" />
                  <p className="text-muted-foreground">
                    El conteo es aproximado y se calcula antes de ejecutar el analisis.
                  </p>
                </div>
                <div className="flex items-start gap-2">
                  <Info className="h-4 w-4 text-muted-foreground mt-0.5" />
                  <p className="text-muted-foreground">
                    El cupo no utilizado <span className="text-foreground font-medium">no se acumula</span> al siguiente mes.
                  </p>
                </div>
              </div>

              <Separator />

              <div>
                <p className="text-sm font-medium mb-2">Tu ciclo actual</p>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Inicio</span>
                    <span>22 Ene 2026</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Fin</span>
                    <span>{new Date(currentUserPlan.renewalDate).toLocaleDateString("es-ES", {
                      day: "numeric",
                      month: "short",
                      year: "numeric"
                    })}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Dias restantes</span>
                    <span className="font-medium">{currentUserPlan.daysRemaining}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Plans */}
        <div>
          <h2 className="text-lg font-semibold mb-4">Planes disponibles</h2>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {plans.map((plan) => {
              const isCurrent = plan.id === currentUserPlan.planId
              return (
                <Card 
                  key={plan.id} 
                  className={`relative ${plan.popular ? "border-primary shadow-lg" : ""} ${isCurrent ? "bg-primary/5" : ""}`}
                >
                  {plan.popular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <Badge className="bg-primary">Mas popular</Badge>
                    </div>
                  )}
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      {plan.name}
                      {isCurrent && <Badge variant="outline">Actual</Badge>}
                    </CardTitle>
                    <CardDescription>
                      <span className="text-3xl font-bold text-foreground">
                        ${plan.price}
                      </span>
                      <span className="text-muted-foreground">/mes</span>
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      {plan.features.map((feature, i) => (
                        <div key={i} className="flex items-center gap-2 text-sm">
                          <Check className="h-4 w-4 text-success flex-shrink-0" />
                          <span>{feature}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                  <CardFooter>
                    <Button 
                      className="w-full" 
                      variant={isCurrent ? "outline" : plan.popular ? "default" : "outline"}
                      disabled={isCurrent}
                    >
                      {isCurrent ? "Plan actual" : plan.price === 0 ? "Empezar gratis" : "Seleccionar"}
                    </Button>
                  </CardFooter>
                </Card>
              )
            })}
          </div>
        </div>

        {/* Comparison Note */}
        <Card>
          <CardContent className="py-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <p className="font-medium">Necesitas un plan personalizado?</p>
                <p className="text-sm text-muted-foreground">
                  Contactanos para soluciones empresariales con volumenes mayores y soporte dedicado.
                </p>
              </div>
              <Button variant="outline">
                Contactar ventas
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </TooltipProvider>
  )
}
