"use client"

import { ArrowUpRight, ArrowDownRight, MessageSquare, TrendingUp, Clock, FileText, Plus } from "lucide-react"
import Link from "next/link"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from "recharts"
import { currentAnalysis, historyItems, currentUserPlan, plans, networkConfig } from "@/lib/mock-data"

const sentimentColors = {
  positive: "#22c55e",
  neutral: "#eab308",
  negative: "#ef4444"
}

const pieData = [
  { name: "Positivo", value: currentAnalysis.totalPositive, color: sentimentColors.positive },
  { name: "Neutral", value: currentAnalysis.totalNeutral, color: sentimentColors.neutral },
  { name: "Negativo", value: currentAnalysis.totalNegative, color: sentimentColors.negative },
]

const barData = currentAnalysis.networks.map(n => ({
  name: networkConfig[n.network].name.split(" ")[0],
  positivo: n.positive,
  neutral: n.neutral,
  negativo: n.negative,
}))

export default function DashboardPage() {
  const currentPlan = plans.find(p => p.id === currentUserPlan.planId)
  const usagePercent = (currentUserPlan.wordsUsed / currentUserPlan.wordsLimit) * 100
  const recentHistory = historyItems.slice(0, 5)
  
  const positivePercent = Math.round((currentAnalysis.totalPositive / currentAnalysis.totalComments) * 100)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Bienvenido de vuelta. Aqui tienes un resumen de tu actividad.
          </p>
        </div>
        <Button asChild>
          <Link href="/nueva-consulta">
            <Plus className="mr-2 h-4 w-4" />
            Nueva consulta
          </Link>
        </Button>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Comentarios</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{currentAnalysis.totalComments.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-success flex items-center gap-1">
                <ArrowUpRight className="h-3 w-3" />
                +12% vs ultima consulta
              </span>
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Sentimiento Global</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-success">{positivePercent}% Positivo</div>
            <p className="text-xs text-muted-foreground">
              {currentAnalysis.totalPositive} positivos de {currentAnalysis.totalComments}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tiempo Ejecucion</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{currentAnalysis.totalExecutionTime.toFixed(1)}s</div>
            <p className="text-xs text-muted-foreground">
              <span className="text-success flex items-center gap-1">
                <ArrowDownRight className="h-3 w-3" />
                -8% mas rapido
              </span>
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Palabras Procesadas</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{currentAnalysis.totalWordsProcessed.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              Hoy: {Math.round(currentAnalysis.totalWordsProcessed * 0.3).toLocaleString()} palabras
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Section */}
      <div className="grid gap-4 lg:grid-cols-7">
        {/* Pie Chart */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Distribucion de Sentimientos</CardTitle>
            <CardDescription>Ultima consulta: &quot;{currentAnalysis.query}&quot;</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px'
                    }}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Bar Chart */}
        <Card className="lg:col-span-4">
          <CardHeader>
            <CardTitle>Comparacion por Red Social</CardTitle>
            <CardDescription>Sentimientos desglosados por plataforma</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={barData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px'
                    }}
                  />
                  <Bar dataKey="positivo" fill={sentimentColors.positive} radius={[4, 4, 0, 0]} />
                  <Bar dataKey="neutral" fill={sentimentColors.neutral} radius={[4, 4, 0, 0]} />
                  <Bar dataKey="negativo" fill={sentimentColors.negative} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Bottom Section */}
      <div className="grid gap-4 lg:grid-cols-7">
        {/* Recent History */}
        <Card className="lg:col-span-4">
          <CardHeader>
            <CardTitle>Historial Reciente</CardTitle>
            <CardDescription>Tus ultimas consultas de analisis</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentHistory.map((item) => (
                <div key={item.id} className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                      <MessageSquare className="h-5 w-5 text-muted-foreground" />
                    </div>
                    <div>
                      <p className="text-sm font-medium leading-none">{item.query}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {new Date(item.createdAt).toLocaleDateString("es-ES")} · {item.totalComments} comentarios
                      </p>
                    </div>
                  </div>
                  <Badge
                    variant={
                      item.sentimentGlobal === "positive"
                        ? "default"
                        : item.sentimentGlobal === "negative"
                          ? "destructive"
                          : "secondary"
                    }
                    className={item.sentimentGlobal === "positive" ? "bg-success text-success-foreground" : ""}
                  >
                    {item.sentimentGlobal === "positive" ? "Positivo" : item.sentimentGlobal === "negative" ? "Negativo" : "Neutral"}
                  </Badge>
                </div>
              ))}
            </div>
            <Button variant="outline" className="w-full mt-4 bg-transparent" asChild>
              <Link href="/historial">Ver todo el historial</Link>
            </Button>
          </CardContent>
        </Card>

        {/* Usage Card */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Consumo del Plan</CardTitle>
            <CardDescription>Plan {currentPlan?.name} · {currentUserPlan.daysRemaining} dias restantes</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-muted-foreground">Palabras usadas</span>
                <span className="text-sm font-medium">
                  {currentUserPlan.wordsUsed.toLocaleString()} / {currentUserPlan.wordsLimit.toLocaleString()}
                </span>
              </div>
              <Progress value={usagePercent} className="h-2" />
              <p className="text-xs text-muted-foreground mt-2">
                {Math.round(100 - usagePercent)}% disponible este mes
              </p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Redes disponibles</span>
                <span className="font-medium">{currentPlan?.maxNetworks} redes</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Consultas hoy</span>
                <span className="font-medium">3 consultas</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Renovacion</span>
                <span className="font-medium">{new Date(currentUserPlan.renewalDate).toLocaleDateString("es-ES")}</span>
              </div>
            </div>

            <Button className="w-full bg-transparent" variant="outline" asChild>
              <Link href="/membresia">Actualizar plan</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
