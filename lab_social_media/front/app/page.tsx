"use client"

import { useEffect, useState } from "react"
import { ArrowUpRight, MessageSquare, TrendingUp, FileText, Plus, Loader2 } from "lucide-react"
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
import { useAuth } from "@/contexts/auth-context"
import { api } from "@/lib/api"
import { currentUserPlan, plans } from "@/lib/mock-data"

const sentimentColors = {
  positive: "#22c55e",
  neutral: "#eab308",
  negative: "#ef4444"
}

export default function DashboardPage() {
  const { user } = useAuth()
  const [loading, setLoading] = useState(true)
  const [analytics, setAnalytics] = useState<any[]>([])
  const [sentiments, setSentiments] = useState<any>(null)
  const [stats, setStats] = useState<any>(null)
  const [queries, setQueries] = useState<any[]>([])

  useEffect(() => {
    if (!user) {
      setLoading(false)
      return
    }

    const loadDashboardData = async () => {
      try {
        const [analyticsData, sentimentsData, statsData, queriesData] = await Promise.all([
          api.getAnalytics(user.id),
          api.getSentiments(user.id),
          api.getStats(user.id),
          api.getQueries(user.id)
        ])

        console.log('Dashboard data loaded:', {
          analytics: analyticsData,
          sentiments: sentimentsData,
          stats: statsData,
          queries: queriesData
        })

        setAnalytics(analyticsData.analytics || [])
        setSentiments(sentimentsData)
        setStats(statsData)
        setQueries(queriesData.queries || [])
      } catch (error) {
        console.error('Error loading dashboard:', error)
      } finally {
        setLoading(false)
      }
    }

    loadDashboardData()
  }, [user])

  // Calculate metrics from real data
  const totalComments = stats?.total_comments || 0
  const totalPosts = stats?.total_posts || 0
  const totalWords = stats?.total_words || 0

  const globalSentiment = sentiments?.global || { positive: 0, neutral: 0, negative: 0, mixed: 0, total: 1 }
  const positivePercent = globalSentiment.total > 0 
    ? Math.round((globalSentiment.positive / globalSentiment.total) * 100) 
    : 0

  console.log('Global sentiment:', globalSentiment, 'Positive %:', positivePercent)

  const pieData = [
    { name: "Positivo", value: globalSentiment.positive, color: sentimentColors.positive },
    { name: "Neutral", value: globalSentiment.neutral, color: sentimentColors.neutral },
    { name: "Negativo", value: globalSentiment.negative, color: sentimentColors.negative },
  ].filter(item => item.value > 0)

  console.log('Pie data:', pieData)

  const barData = analytics.map(net => ({
    name: net.network.charAt(0).toUpperCase() + net.network.slice(1),
    positivo: sentiments?.summary?.[net.network]?.positive || 0,
    neutral: sentiments?.summary?.[net.network]?.neutral || 0,
    negativo: sentiments?.summary?.[net.network]?.negative || 0,
  }))

  console.log('Bar data:', barData)

  const recentQueries = queries.slice(0, 5)
  const currentPlan = plans.find(p => p.id === currentUserPlan.planId)
  const usagePercent = (currentUserPlan.wordsUsed / currentUserPlan.wordsLimit) * 100

  if (loading) {
    return (
      <div className="flex justify-center items-center h-96">
        <Loader2 className="animate-spin h-8 w-8 text-primary" />
      </div>
    )
  }

  if (!user || totalPosts === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <h2 className="text-2xl font-bold">No hay datos aún</h2>
        <p className="text-muted-foreground">Realiza tu primera consulta para ver el dashboard</p>
        <Button asChild>
          <Link href="/nueva-consulta">
            <Plus className="mr-2 h-4 w-4" />
            Nueva Consulta
          </Link>
        </Button>
      </div>
    )
  }

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
            <div className="text-2xl font-bold">{totalComments.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              Total de comentarios analizados
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
              {globalSentiment.positive} positivos de {globalSentiment.total}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Posts Analizados</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalPosts.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              {analytics.length} {analytics.length === 1 ? 'red social' : 'redes sociales'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Palabras Procesadas</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalWords.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              Palabras procesadas en total
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
            <CardDescription>
              {analytics.length > 0 ? `${analytics.length} ${analytics.length === 1 ? 'red' : 'redes'} analizadas` : 'Sin datos'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[280px]">
              {pieData.length > 0 ? (
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
                      label
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
              ) : (
                <div className="flex items-center justify-center h-full text-muted-foreground">
                  <p>No hay datos de sentimiento disponibles</p>
                </div>
              )}
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
              {recentQueries.length > 0 ? (
                recentQueries.map((query: any) => (
                  <div key={query.id} className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                        <MessageSquare className="h-5 w-5 text-muted-foreground" />
                      </div>
                      <div>
                        <p className="text-sm font-medium leading-none">{query.query_text || 'Sin título'}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {new Date(query.created_at).toLocaleDateString("es-ES")} · {query.network || 'Todas las redes'}
                        </p>
                      </div>
                    </div>
                    <Badge variant="secondary">
                      {query.status || 'Completado'}
                    </Badge>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground text-center py-4">
                  No hay consultas recientes
                </p>
              )}
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
