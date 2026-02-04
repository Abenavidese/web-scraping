"use client"

import { Download, FileText, Search, BarChart3, GitCompare, Lightbulb, Target, TrendingUp, CheckCircle2 } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { currentAnalysis, networkConfig, sentimentLLM } from "@/lib/mock-data"

export default function StorytellingPage() {
  const positivePercent = Math.round((currentAnalysis.totalPositive / currentAnalysis.totalComments) * 100)
  const neutralPercent = Math.round((currentAnalysis.totalNeutral / currentAnalysis.totalComments) * 100)
  const negativePercent = Math.round((currentAnalysis.totalNegative / currentAnalysis.totalComments) * 100)

  // Find best and worst performing networks
  const networkStats = currentAnalysis.networks.map(n => ({
    ...n,
    positivePercent: Math.round((n.positive / n.totalComments) * 100)
  })).sort((a, b) => b.positivePercent - a.positivePercent)

  const bestNetwork = networkStats[0]
  const worstNetwork = networkStats[networkStats.length - 1]

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Storytelling</h1>
          <p className="text-muted-foreground">
            Reporte narrativo del analisis de sentimiento
          </p>
        </div>
        <Button>
          <Download className="h-4 w-4 mr-2" />
          Exportar reporte
        </Button>
      </div>

      {/* Report Container */}
      <div className="space-y-8">
        {/* Section 1: What was queried */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="h-5 w-5 text-primary" />
              Que se consulto
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-4">
              <div className="flex-1 min-w-[200px]">
                <p className="text-sm text-muted-foreground mb-1">Consulta principal</p>
                <p className="text-lg font-medium">&quot;{currentAnalysis.query}&quot;</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-1">Fecha de analisis</p>
                <p className="font-medium">{new Date(currentAnalysis.createdAt).toLocaleDateString("es-ES", { 
                  year: 'numeric', 
                  month: 'long', 
                  day: 'numeric' 
                })}</p>
              </div>
            </div>

            <Separator />

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <p className="text-sm text-muted-foreground">Rango de fechas</p>
                <p className="font-medium">
                  {currentAnalysis.filters.dateRange.from} - {currentAnalysis.filters.dateRange.to}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Idioma</p>
                <p className="font-medium">{currentAnalysis.filters.language === "ES" ? "Espanol" : "English"}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Region</p>
                <p className="font-medium">{currentAnalysis.filters.country}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Nivel de limpieza</p>
                <p className="font-medium capitalize">{currentAnalysis.filters.cleaningLevel}</p>
              </div>
            </div>

            <div className="flex flex-wrap gap-2 pt-2">
              {currentAnalysis.networks.map(n => (
                <Badge key={n.network} variant="secondary">
                  {networkConfig[n.network].name}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Section 2: What was found */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-primary" />
              Que se encontro
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="text-center p-4 rounded-lg bg-muted/50">
                <p className="text-3xl font-bold">{currentAnalysis.totalComments}</p>
                <p className="text-sm text-muted-foreground">Comentarios totales</p>
              </div>
              <div className="text-center p-4 rounded-lg bg-muted/50">
                <p className="text-3xl font-bold">{currentAnalysis.totalWordsProcessed.toLocaleString()}</p>
                <p className="text-sm text-muted-foreground">Palabras procesadas</p>
              </div>
              <div className="text-center p-4 rounded-lg bg-muted/50">
                <p className="text-3xl font-bold">{currentAnalysis.totalExecutionTime.toFixed(1)}s</p>
                <p className="text-sm text-muted-foreground">Tiempo de ejecucion</p>
              </div>
            </div>

            <Separator />

            <div>
              <h4 className="font-medium mb-4">Resumen por red social</h4>
              <div className="space-y-4">
                {currentAnalysis.networks.map(n => (
                  <div key={n.network} className="flex items-center gap-4 p-3 rounded-lg border">
                    <div 
                      className="h-10 w-10 rounded-lg flex items-center justify-center text-white font-bold text-sm"
                      style={{ backgroundColor: networkConfig[n.network].color }}
                    >
                      {n.network[0].toUpperCase()}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium">{networkConfig[n.network].name}</p>
                      <p className="text-sm text-muted-foreground">
                        {n.totalComments} comentarios · {n.wordsProcessed.toLocaleString()} palabras
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium text-success">{Math.round((n.positive / n.totalComments) * 100)}% positivo</p>
                      <p className="text-xs text-muted-foreground">via {sentimentLLM}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Section 3: Sentiment Patterns */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-primary" />
              Patrones de sentimiento
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="p-4 rounded-lg bg-success/10 border border-success/20">
              <h4 className="font-medium text-success mb-2">Sentimiento global: Positivo</h4>
              <p className="text-sm text-muted-foreground">
                El {positivePercent}% de los comentarios analizados expresan opiniones positivas sobre 
                &quot;{currentAnalysis.query}&quot;. Este es un indicador favorable de la percepcion publica.
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <div className="p-4 rounded-lg border text-center">
                <p className="text-2xl font-bold text-success">{positivePercent}%</p>
                <p className="text-sm text-muted-foreground">Positivo</p>
                <p className="text-xs text-muted-foreground mt-1">{currentAnalysis.totalPositive} comentarios</p>
              </div>
              <div className="p-4 rounded-lg border text-center">
                <p className="text-2xl font-bold text-warning">{neutralPercent}%</p>
                <p className="text-sm text-muted-foreground">Neutral</p>
                <p className="text-xs text-muted-foreground mt-1">{currentAnalysis.totalNeutral} comentarios</p>
              </div>
              <div className="p-4 rounded-lg border text-center">
                <p className="text-2xl font-bold text-destructive">{negativePercent}%</p>
                <p className="text-sm text-muted-foreground">Negativo</p>
                <p className="text-xs text-muted-foreground mt-1">{currentAnalysis.totalNegative} comentarios</p>
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="font-medium">Insights clave</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-success mt-0.5 flex-shrink-0" />
                  <span>La mayoria de comentarios positivos mencionan calidad, rendimiento y satisfaccion general.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-success mt-0.5 flex-shrink-0" />
                  <span>Los comentarios neutrales tienden a ser comparativos con productos de la competencia.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-4 w-4 text-success mt-0.5 flex-shrink-0" />
                  <span>Las opiniones negativas se concentran principalmente en aspectos de precio y disponibilidad.</span>
                </li>
              </ul>
            </div>
          </CardContent>
        </Card>

        {/* Section 4: Network Comparison */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <GitCompare className="h-5 w-5 text-primary" />
              Comparacion entre redes
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="p-4 rounded-lg bg-success/10 border border-success/20">
                <p className="text-sm text-muted-foreground mb-1">Mejor rendimiento</p>
                <p className="font-medium">{networkConfig[bestNetwork.network].name}</p>
                <p className="text-2xl font-bold text-success">{bestNetwork.positivePercent}% positivo</p>
              </div>
              <div className="p-4 rounded-lg bg-muted border">
                <p className="text-sm text-muted-foreground mb-1">Menor rendimiento</p>
                <p className="font-medium">{networkConfig[worstNetwork.network].name}</p>
                <p className="text-2xl font-bold">{worstNetwork.positivePercent}% positivo</p>
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="font-medium">Por que difieren los resultados?</h4>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Las diferencias entre redes sociales pueden atribuirse a varios factores:
              </p>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <span className="font-medium text-foreground">Demografica:</span>
                  <span>Cada plataforma tiene audiencias con perfiles distintos y expectativas diferentes.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="font-medium text-foreground">Formato:</span>
                  <span>Instagram favorece contenido visual, mientras que X permite expresiones mas directas y polarizadas.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="font-medium text-foreground">Contexto:</span>
                  <span>LinkedIn tiende a tener un tono mas profesional y medido en las opiniones.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="font-medium text-foreground">Analisis:</span>
                  <span>El modelo {sentimentLLM} proporciona consistencia en la clasificacion de sentimiento a traves de todas las plataformas.</span>
                </li>
              </ul>
            </div>
          </CardContent>
        </Card>

        {/* Section 5: Recommendations */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5 text-primary" />
              Recomendaciones
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start gap-4 p-4 rounded-lg border">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium">
                  1
                </div>
                <div>
                  <p className="font-medium">Capitalizar el sentimiento positivo</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Aprovechar los comentarios positivos como testimonios en campanas de marketing, 
                    especialmente en {networkConfig[bestNetwork.network].name} donde el sentimiento es mas favorable.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4 p-4 rounded-lg border">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium">
                  2
                </div>
                <div>
                  <p className="font-medium">Atender las preocupaciones negativas</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Identificar los temas recurrentes en comentarios negativos y desarrollar respuestas 
                    proactivas o mejoras de producto/servicio.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4 p-4 rounded-lg border">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium">
                  3
                </div>
                <div>
                  <p className="font-medium">Optimizar presencia por plataforma</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Adaptar el mensaje y tono segun la plataforma. Contenido mas visual para Instagram, 
                    mas profesional para LinkedIn, y mas conversacional para X.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4 p-4 rounded-lg border">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium">
                  4
                </div>
                <div>
                  <p className="font-medium">Monitoreo continuo</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Establecer analisis periodicos para detectar cambios en la percepcion publica 
                    y responder rapidamente a tendencias emergentes.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4 p-4 rounded-lg border">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium">
                  5
                </div>
                <div>
                  <p className="font-medium">Engagement estrategico</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Responder activamente a comentarios, especialmente los neutrales que pueden 
                    convertirse en promotores con la interaccion adecuada.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4 p-4 rounded-lg border">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium">
                  6
                </div>
                <div>
                  <p className="font-medium">Analisis competitivo</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Realizar consultas similares sobre competidores para comparar la percepcion 
                    del mercado y identificar ventajas competitivas.
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <FileText className="h-8 w-8 text-muted-foreground" />
                <div>
                  <p className="font-medium">Reporte generado automaticamente</p>
                  <p className="text-sm text-muted-foreground">
                    Sentiment Social Analyzer · {new Date().toLocaleDateString("es-ES")}
                  </p>
                </div>
              </div>
              <Button>
                <Download className="h-4 w-4 mr-2" />
                Exportar reporte PDF
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
