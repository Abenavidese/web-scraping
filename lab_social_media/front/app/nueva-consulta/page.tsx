"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Calendar, Globe, Languages, Sliders, AlertTriangle, Check, Loader2, X } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Checkbox } from "@/components/ui/checkbox"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { sentimentLLM, currentUserPlan, type SocialNetwork } from "@/lib/mock-data"
import { useAuth } from "@/contexts/auth-context"
import { api } from "@/lib/api"
import { useToast } from "@/components/ui/use-toast"

const networks: { id: SocialNetwork; name: string; icon: string; color: string }[] = [
  { id: "facebook", name: "Facebook", icon: "f", color: "#1877F2" },
  { id: "instagram", name: "Instagram", icon: "ig", color: "#E4405F" },
  { id: "x", name: "X (Twitter)", icon: "X", color: "#000000" },
  { id: "linkedin", name: "LinkedIn", icon: "in", color: "#0A66C2" },
]

const networkLLMMapping = {
  facebook: "OpenAI",
  instagram: "Gemini",
  x: "Grok",
  linkedin: "DeepSeek",
}

interface AnalysisStep {
  id: string
  name: string
  status: "pending" | "running" | "done" | "error"
  progress: number
  network?: SocialNetwork
}

export default function NuevaConsultaPage() {
  const router = useRouter()
  const [query, setQuery] = useState("")
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [language, setLanguage] = useState("ES")
  const [country, setCountry] = useState("global")
  const [maxResults, setMaxResults] = useState([50])
  const [includeComments, setIncludeComments] = useState(true)
  const [includePosts, setIncludePosts] = useState(true)
  const [cleaningLevel, setCleaningLevel] = useState("normal")
  const [selectedNetworks, setSelectedNetworks] = useState<SocialNetwork[]>(["facebook", "instagram", "x", "linkedin"])
  const [isCustomLimits, setIsCustomLimits] = useState(false)
  const [networkLimits, setNetworkLimits] = useState<Record<string, number>>({})

  const { user } = useAuth()
  const { toast } = useToast()

  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisSteps, setAnalysisSteps] = useState<AnalysisStep[]>([])

  // Estimated words calculation
  const estimatedWords = selectedNetworks.length * maxResults[0] * 12 // ~12 words per comment average
  const isOverBudget = currentUserPlan.wordsUsed + estimatedWords > currentUserPlan.wordsLimit

  // DeepSeek pricing calculation
  // Input: $0.14 per 1M tokens, Output: $0.28 per 1M tokens
  // Assuming ~1.3 tokens per word (average for English/Spanish)
  const estimatedInputTokens = estimatedWords * 1.3
  const estimatedOutputTokens = estimatedWords * 0.3 // Output is ~30% of input for sentiment analysis
  const estimatedCost = (estimatedInputTokens / 1_000_000 * 0.14) + (estimatedOutputTokens / 1_000_000 * 0.28)

  const toggleNetwork = (networkId: SocialNetwork) => {
    setSelectedNetworks(prev =>
      prev.includes(networkId)
        ? prev.filter(n => n !== networkId)
        : [...prev, networkId]
    )
  }

  const startAnalysis = async () => {
    if (!query.trim() || selectedNetworks.length === 0) return

    if (!user) {
      toast({
        title: "Error de autenticación",
        description: "Debes iniciar sesión para realizar consultas",
        variant: "destructive",
      })
      return
    }

    setIsAnalyzing(true)

    // Initialize steps
    const initialSteps: AnalysisStep[] = [
      { id: "request", name: "Iniciando solicitud", status: "running", progress: 0 },
      ...selectedNetworks.map(network => ({
        id: `extract-${network}`,
        name: `Extraccion ${networks.find(n => n.id === network)?.name}`,
        status: "pending" as const,
        progress: 0,
        network,
      })),
      { id: "processing", name: "Procesando resultados", status: "pending", progress: 0 },
    ]

    setAnalysisSteps(initialSteps)

    try {
      // Send request to API
      const result = await api.scrape({
        networks: selectedNetworks,
        query: query,
        num_posts: maxResults[0],
        num_comments: includeComments ? 10 : 0, // Default to 10 comments if checked
        user_id: user.id,
        limits: isCustomLimits ? networkLimits : undefined
      })

      // On success (the API currently waits for completion, so this blocks until done)
      // If we want real-time updates we need sockets, but for now we simulate or just valid

      setAnalysisSteps(prev => prev.map(s => ({ ...s, status: "done", progress: 100 })))

      toast({
        title: "Análisis completado",
        description: `Se han procesado ${result.successful} redes exitosamente.`,
      })

      // Redirect to results
      await new Promise(resolve => setTimeout(resolve, 800))
      router.push("/resultados")

    } catch (error) {
      console.error(error)
      setAnalysisSteps(prev => prev.map(s => ({ ...s, status: "error" })))
      toast({
        title: "Error en el análisis",
        description: error instanceof Error ? error.message : "Error desconocido",
        variant: "destructive",
      })
      setTimeout(() => setIsAnalyzing(false), 2000)
    }
  }

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Nueva consulta</h1>
          <p className="text-muted-foreground">
            Configura los parametros de tu analisis de sentimiento
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Main Form */}
          <div className="lg:col-span-2 space-y-6">
            {/* Query Block */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sliders className="h-5 w-5" />
                  Configuracion de busqueda
                </CardTitle>
                <CardDescription>
                  Define tu consulta y los filtros de extraccion
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Main Query */}
                <div className="space-y-2">
                  <Label htmlFor="query">Consulta principal</Label>
                  <Input
                    id="query"
                    placeholder="Ej: 'iPhone 15 bateria', 'Tesla Model 3 opinion'"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    className="text-lg h-12"
                  />
                  <p className="text-xs text-muted-foreground">
                    Escribe palabras clave o frases para buscar en las redes sociales
                  </p>
                </div>

                {/* Max Results Slider */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <Label>Maximo de resultados por red</Label>
                    <span className="text-sm font-medium">{maxResults[0]} resultados</span>
                  </div>
                  <Slider
                    value={maxResults}
                    onValueChange={setMaxResults}
                    min={10}
                    max={100}
                    step={10}
                    className="w-full"
                  />
                  <p className="text-xs text-muted-foreground">
                    Cantidad maxima de comentarios/publicaciones a extraer de cada red social
                  </p>

                  <div className="flex items-center space-x-2 pt-2">
                    <Checkbox
                      id="custom-limits"
                      checked={isCustomLimits}
                      onCheckedChange={(checked) => setIsCustomLimits(!!checked)}
                    />
                    <Label htmlFor="custom-limits">Personalizar límites por red</Label>
                  </div>

                  {isCustomLimits && (
                    <div className="grid grid-cols-2 gap-4 pt-2 p-4 bg-muted/20 rounded-lg border">
                      {selectedNetworks.map(netId => {
                        const net = networks.find(n => n.id === netId)
                        return (
                          <div key={netId} className="space-y-1">
                            <Label className="text-xs">{net?.name}</Label>
                            <Input
                              type="number"
                              min={1}
                              max={100}
                              value={networkLimits[netId] || maxResults[0]}
                              onChange={(e) => {
                                const val = parseInt(e.target.value) || 0
                                setNetworkLimits(prev => ({ ...prev, [netId]: val }))
                              }}
                              className="h-8"
                            />
                          </div>
                        )
                      })}
                      {selectedNetworks.length === 0 && (
                        <div className="col-span-2 text-xs text-muted-foreground">Selecciona redes para customizar sus límites</div>
                      )}
                    </div>
                  )}
                </div>

                {/* Content Type */}
                <div className="space-y-3">
                  <Label>Tipo de contenido</Label>
                  <div className="flex flex-wrap gap-4">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="comments"
                        checked={includeComments}
                        onCheckedChange={(checked) => setIncludeComments(checked as boolean)}
                      />
                      <label htmlFor="comments" className="text-sm cursor-pointer">
                        Incluir comentarios
                      </label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="posts"
                        checked={includePosts}
                        onCheckedChange={(checked) => setIncludePosts(checked as boolean)}
                      />
                      <label htmlFor="posts" className="text-sm cursor-pointer">
                        Incluir publicaciones
                      </label>
                    </div>
                  </div>
                </div>


              </CardContent>
            </Card>

            {/* Networks Block */}
            <Card>
              <CardHeader>
                <CardTitle>Redes sociales</CardTitle>
                <CardDescription>
                  Selecciona las plataformas a analizar
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* LLM Info Banner */}
                <div className="mb-4 flex items-center gap-3 rounded-lg border border-primary/20 bg-primary/5 p-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground text-xs font-bold">
                    DS
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium">Motor de analisis: {sentimentLLM}</p>
                    <p className="text-xs text-muted-foreground">
                      Todas las redes son procesadas con el mismo modelo para consistencia
                    </p>
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  {networks.map((network) => (
                    <div
                      key={network.id}
                      className={`relative flex items-center gap-4 rounded-lg border p-4 cursor-pointer transition-colors ${selectedNetworks.includes(network.id)
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-muted-foreground/50"
                        }`}
                      onClick={() => toggleNetwork(network.id)}
                    >
                      <div
                        className="flex h-10 w-10 items-center justify-center rounded-lg text-white font-bold text-sm"
                        style={{ backgroundColor: network.color }}
                      >
                        {network.icon}
                      </div>
                      <div className="flex-1">
                        <p className="font-medium">{network.name}</p>
                      </div>
                      <Checkbox
                        checked={selectedNetworks.includes(network.id)}
                        className="pointer-events-none"
                      />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar - Budget & Action */}
          <div className="space-y-6">
            {/* Budget Card */}
            <Card>
              <CardHeader>
                <CardTitle>Presupuesto de consumo</CardTitle>
                <CardDescription>
                  Estimacion basada en tu consulta
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Palabras estimadas</span>
                    <span className="font-medium">{estimatedWords.toLocaleString()}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Costo estimado</span>
                    <span className="font-medium text-primary">
                      ${estimatedCost < 0.01 ? '<0.01' : estimatedCost.toFixed(2)} USD
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Cupo disponible</span>
                    <span className="font-medium">
                      {(currentUserPlan.wordsLimit - currentUserPlan.wordsUsed).toLocaleString()}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Cupo despues</span>
                    <span className={`font-medium ${isOverBudget ? "text-destructive" : ""}`}>
                      {(currentUserPlan.wordsLimit - currentUserPlan.wordsUsed - estimatedWords).toLocaleString()}
                    </span>
                  </div>
                </div>

                <Progress
                  value={((currentUserPlan.wordsUsed + estimatedWords) / currentUserPlan.wordsLimit) * 100}
                  className="h-2"
                />

                {isOverBudget && (
                  <div className="flex items-start gap-2 rounded-lg bg-destructive/10 p-3">
                    <AlertTriangle className="h-4 w-4 text-destructive mt-0.5" />
                    <div className="text-sm">
                      <p className="font-medium text-destructive">Excede tu cupo</p>
                      <p className="text-muted-foreground">
                        Reduce resultados o actualiza tu plan.
                      </p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Action Card */}
            <Card>
              <CardContent className="pt-6">
                <Button
                  className="w-full h-12 text-base"
                  disabled={!query.trim() || selectedNetworks.length === 0 || isOverBudget}
                  onClick={startAnalysis}
                >
                  Ejecutar analisis
                </Button>
                <p className="text-xs text-muted-foreground text-center mt-3">
                  {selectedNetworks.length} {selectedNetworks.length === 1 ? 'red' : 'redes'} seleccionadas
                </p>
              </CardContent>
            </Card>

            {/* Info Card */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Como funciona</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-muted-foreground">
                <div className="flex gap-3">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs">1</span>
                  <p>Extraccion concurrente de contenido de las redes seleccionadas</p>
                </div>
                <div className="flex gap-3">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs">2</span>
                  <p>Preprocesamiento NLP: limpieza, tokenizacion, stopwords</p>
                </div>
                <div className="flex gap-3">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs">3</span>
                  <p>Clasificacion de sentimiento con {sentimentLLM}</p>
                </div>
                <div className="flex gap-3">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs">4</span>
                  <p>Consolidacion y generacion de insights</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Analysis Modal */}
        <Dialog open={isAnalyzing} onOpenChange={setIsAnalyzing}>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle>Ejecutando analisis</DialogTitle>
              <DialogDescription>
                Procesando consulta: &quot;{query}&quot;
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              {analysisSteps.map((step) => (
                <div key={step.id} className="flex items-center gap-4">
                  <div className="flex h-8 w-8 items-center justify-center">
                    {step.status === "pending" && (
                      <div className="h-4 w-4 rounded-full border-2 border-muted" />
                    )}
                    {step.status === "running" && (
                      <Loader2 className="h-4 w-4 animate-spin text-primary" />
                    )}
                    {step.status === "done" && (
                      <div className="flex h-5 w-5 items-center justify-center rounded-full bg-success">
                        <Check className="h-3 w-3 text-success-foreground" />
                      </div>
                    )}
                    {step.status === "error" && (
                      <div className="flex h-5 w-5 items-center justify-center rounded-full bg-destructive">
                        <X className="h-3 w-3 text-destructive-foreground" />
                      </div>
                    )}
                  </div>
                  <div className="flex-1">
                    <p className={`text-sm ${step.status === "running" ? "font-medium" : ""}`}>
                      {step.name}
                    </p>
                    {step.status === "running" && (
                      <Progress value={step.progress} className="h-1 mt-1" />
                    )}
                  </div>
                  {step.status === "done" && (
                    <span className="text-xs text-muted-foreground">
                      {(Math.random() * 2 + 1).toFixed(1)}s
                    </span>
                  )}
                </div>
              ))}
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </TooltipProvider >
  )
}
