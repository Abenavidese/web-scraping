// Mock data for Sentiment Social Analyzer

export type SocialNetwork = "facebook" | "instagram" | "x" | "linkedin"
export type Sentiment = "positive" | "neutral" | "negative"
export type AnalysisStatus = "pending" | "running" | "done" | "error"

export interface Comment {
  id: string
  network: SocialNetwork
  text: string
  author: string
  date: string
  url: string
  sentiment: Sentiment
  score: number
  llm: string
  tokens?: string[]
  cleanedText?: string
  explanation?: string
}

export interface NetworkResult {
  network: SocialNetwork
  llm: string
  status: AnalysisStatus
  comments: Comment[]
  totalComments: number
  positive: number
  neutral: number
  negative: number
  executionTime: number
  wordsProcessed: number
}

export interface AnalysisResult {
  id: string
  query: string
  createdAt: string
  status: AnalysisStatus
  filters: {
    dateRange: { from: string; to: string }
    language: string
    country: string
    maxResults: number
    includeComments: boolean
    cleaningLevel: string
  }
  networks: NetworkResult[]
  totalComments: number
  totalPositive: number
  totalNeutral: number
  totalNegative: number
  totalWordsProcessed: number
  totalExecutionTime: number
}

export interface HistoryItem {
  id: string
  query: string
  createdAt: string
  networks: SocialNetwork[]
  totalComments: number
  sentimentGlobal: Sentiment
  wordsProcessed: number
  status: AnalysisStatus
}

export interface Plan {
  id: string
  name: string
  price: number
  wordsPerMonth: number
  maxNetworks: number
  features: string[]
  popular?: boolean
}

export interface UserPlan {
  planId: string
  wordsUsed: number
  wordsLimit: number
  daysRemaining: number
  renewalDate: string
}

// LLM for sentiment analysis (unified across all networks)
export const sentimentLLM = "DeepSeek"

// LLM mapping per network (all use DeepSeek)
export const networkLLMMapping: Record<SocialNetwork, string> = {
  facebook: "DeepSeek",
  instagram: "DeepSeek",
  x: "DeepSeek",
  linkedin: "DeepSeek"
}

// Network icons and colors
export const networkConfig: Record<SocialNetwork, { name: string; color: string }> = {
  facebook: { name: "Facebook", color: "#1877F2" },
  instagram: { name: "Instagram", color: "#E4405F" },
  x: { name: "X (Twitter)", color: "#000000" },
  linkedin: { name: "LinkedIn", color: "#0A66C2" }
}

// Plans
export const plans: Plan[] = [
  {
    id: "free",
    name: "Free",
    price: 0,
    wordsPerMonth: 5000,
    maxNetworks: 2,
    features: [
      "5,000 palabras/mes",
      "2 redes sociales",
      "Resultados basicos",
      "Sin exportacion"
    ]
  },
  {
    id: "student",
    name: "Student",
    price: 9,
    wordsPerMonth: 50000,
    maxNetworks: 4,
    features: [
      "50,000 palabras/mes",
      "4 redes sociales",
      "Storytelling completo",
      "Historial 30 dias",
      "Exportar reportes"
    ],
    popular: true
  },
  {
    id: "pro",
    name: "Pro",
    price: 29,
    wordsPerMonth: 250000,
    maxNetworks: 4,
    features: [
      "250,000 palabras/mes",
      "4 redes sociales",
      "Storytelling completo",
      "Historial ilimitado",
      "Exportar reportes",
      "Prioridad en analisis"
    ]
  },
  {
    id: "enterprise",
    name: "Enterprise",
    price: 99,
    wordsPerMonth: -1, // unlimited
    maxNetworks: 4,
    features: [
      "Palabras ilimitadas",
      "4 redes sociales",
      "Todas las funciones",
      "Soporte prioritario",
      "API access",
      "Custom integrations"
    ]
  }
]

// Current user plan
export const currentUserPlan: UserPlan = {
  planId: "student",
  wordsUsed: 28500,
  wordsLimit: 50000,
  daysRemaining: 18,
  renewalDate: "2026-02-21"
}

// Generate mock comments
function generateComments(network: SocialNetwork, count: number): Comment[] {
  const llm = networkLLMMapping[network]
  const sampleTexts = {
    positive: [
      "Excelente producto, me encanta la calidad!",
      "La mejor compra que he hecho este ano",
      "Super recomendado, funciona perfectamente",
      "Increible servicio al cliente, muy rapidos",
      "Totalmente satisfecho con mi compra",
      "Superó mis expectativas, muy feliz!",
      "Lo mejor del mercado sin duda",
      "Calidad premium a buen precio"
    ],
    neutral: [
      "El producto está bien, cumple su funcion",
      "Normal, nada especial pero tampoco malo",
      "Es lo que esperaba, ni mas ni menos",
      "Producto estándar, sin sorpresas",
      "Hace lo que promete, nada más",
      "Cumple con lo basico"
    ],
    negative: [
      "Muy decepcionado, no funciona como esperaba",
      "Mala calidad, no lo recomiendo",
      "Tuve problemas desde el primer dia",
      "El envío tardó demasiado",
      "No vale la pena el precio",
      "Servicio terrible, nunca más"
    ]
  }

  const authors = ["@usuario1", "@maria_g", "@tech_lover", "@reviewer_pro", "@consumidor_smart", "@opinion_real", "@social_user", "@feedback_master"]
  
  const comments: Comment[] = []
  
  for (let i = 0; i < count; i++) {
    const rand = Math.random()
    let sentiment: Sentiment
    let texts: string[]
    
    if (rand < 0.45) {
      sentiment = "positive"
      texts = sampleTexts.positive
    } else if (rand < 0.75) {
      sentiment = "neutral"
      texts = sampleTexts.neutral
    } else {
      sentiment = "negative"
      texts = sampleTexts.negative
    }
    
    const text = texts[Math.floor(Math.random() * texts.length)]
    const score = sentiment === "positive" 
      ? 0.7 + Math.random() * 0.3 
      : sentiment === "neutral" 
        ? 0.4 + Math.random() * 0.2 
        : 0.1 + Math.random() * 0.3
    
    comments.push({
      id: `${network}-${i + 1}`,
      network,
      text,
      author: authors[Math.floor(Math.random() * authors.length)],
      date: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
      url: `https://${network}.com/post/${Math.random().toString(36).substr(2, 9)}`,
      sentiment,
      score: Math.round(score * 100) / 100,
      llm,
      tokens: text.toLowerCase().split(/\s+/),
      cleanedText: text.toLowerCase().replace(/[!?.,]/g, ""),
      explanation: sentiment === "positive" 
        ? "El comentario expresa satisfaccion clara con palabras como 'excelente', 'encanta', 'recomendado'."
        : sentiment === "negative"
          ? "El comentario muestra insatisfaccion con terminos negativos como 'decepcionado', 'mala', 'problemas'."
          : "El comentario es descriptivo sin expresar emociones fuertes, usando terminos neutrales."
    })
  }
  
  return comments
}

// Generate network results
function generateNetworkResult(network: SocialNetwork): NetworkResult {
  const commentCount = 25 + Math.floor(Math.random() * 25)
  const comments = generateComments(network, commentCount)
  
  const positive = comments.filter(c => c.sentiment === "positive").length
  const neutral = comments.filter(c => c.sentiment === "neutral").length
  const negative = comments.filter(c => c.sentiment === "negative").length
  
  return {
    network,
    llm: networkLLMMapping[network],
    status: "done",
    comments,
    totalComments: commentCount,
    positive,
    neutral,
    negative,
    executionTime: 2 + Math.random() * 5,
    wordsProcessed: comments.reduce((acc, c) => acc + c.text.split(/\s+/).length, 0)
  }
}

// Current analysis result
export const currentAnalysis: AnalysisResult = (() => {
  const networks = (["facebook", "instagram", "x", "linkedin"] as SocialNetwork[]).map(generateNetworkResult)
  
  const totalComments = networks.reduce((acc, n) => acc + n.totalComments, 0)
  const totalPositive = networks.reduce((acc, n) => acc + n.positive, 0)
  const totalNeutral = networks.reduce((acc, n) => acc + n.neutral, 0)
  const totalNegative = networks.reduce((acc, n) => acc + n.negative, 0)
  const totalWordsProcessed = networks.reduce((acc, n) => acc + n.wordsProcessed, 0)
  const totalExecutionTime = networks.reduce((acc, n) => acc + n.executionTime, 0)
  
  return {
    id: "analysis-001",
    query: "iPhone 15 bateria",
    createdAt: new Date().toISOString(),
    status: "done",
    filters: {
      dateRange: { from: "2026-01-01", to: "2026-02-03" },
      language: "ES",
      country: "Global",
      maxResults: 50,
      includeComments: true,
      cleaningLevel: "normal"
    },
    networks,
    totalComments,
    totalPositive,
    totalNeutral,
    totalNegative,
    totalWordsProcessed,
    totalExecutionTime
  }
})()

// History items
export const historyItems: HistoryItem[] = [
  {
    id: "hist-001",
    query: "iPhone 15 bateria",
    createdAt: "2026-02-03T10:30:00Z",
    networks: ["facebook", "instagram", "x", "linkedin"],
    totalComments: 156,
    sentimentGlobal: "positive",
    wordsProcessed: 4520,
    status: "done"
  },
  {
    id: "hist-002",
    query: "Samsung Galaxy S24",
    createdAt: "2026-02-02T14:15:00Z",
    networks: ["facebook", "instagram", "x"],
    totalComments: 98,
    sentimentGlobal: "neutral",
    wordsProcessed: 2890,
    status: "done"
  },
  {
    id: "hist-003",
    query: "MacBook Pro M3",
    createdAt: "2026-02-01T09:00:00Z",
    networks: ["linkedin", "x"],
    totalComments: 67,
    sentimentGlobal: "positive",
    wordsProcessed: 1950,
    status: "done"
  },
  {
    id: "hist-004",
    query: "Tesla Model 3",
    createdAt: "2026-01-30T16:45:00Z",
    networks: ["facebook", "instagram", "x", "linkedin"],
    totalComments: 234,
    sentimentGlobal: "positive",
    wordsProcessed: 6780,
    status: "done"
  },
  {
    id: "hist-005",
    query: "Netflix precio suscripcion",
    createdAt: "2026-01-28T11:20:00Z",
    networks: ["facebook", "x"],
    totalComments: 189,
    sentimentGlobal: "negative",
    wordsProcessed: 5430,
    status: "done"
  },
  {
    id: "hist-006",
    query: "Spotify vs Apple Music",
    createdAt: "2026-01-25T08:30:00Z",
    networks: ["instagram", "x", "linkedin"],
    totalComments: 145,
    sentimentGlobal: "neutral",
    wordsProcessed: 4120,
    status: "done"
  },
  {
    id: "hist-007",
    query: "ChatGPT experiencia",
    createdAt: "2026-01-22T13:00:00Z",
    networks: ["facebook", "instagram", "x", "linkedin"],
    totalComments: 312,
    sentimentGlobal: "positive",
    wordsProcessed: 8950,
    status: "done"
  },
  {
    id: "hist-008",
    query: "Amazon Prime Day",
    createdAt: "2026-01-20T10:00:00Z",
    networks: ["facebook", "instagram"],
    totalComments: 78,
    sentimentGlobal: "positive",
    wordsProcessed: 2340,
    status: "done"
  },
  {
    id: "hist-009",
    query: "PlayStation 5 disponibilidad",
    createdAt: "2026-01-18T15:30:00Z",
    networks: ["x", "facebook"],
    totalComments: 156,
    sentimentGlobal: "negative",
    wordsProcessed: 4560,
    status: "error"
  },
  {
    id: "hist-010",
    query: "Uber Eats servicio",
    createdAt: "2026-01-15T12:00:00Z",
    networks: ["facebook", "instagram", "x"],
    totalComments: 203,
    sentimentGlobal: "neutral",
    wordsProcessed: 5890,
    status: "done"
  },
  {
    id: "hist-011",
    query: "Nike Air Max 2026",
    createdAt: "2026-01-12T09:45:00Z",
    networks: ["instagram", "facebook"],
    totalComments: 89,
    sentimentGlobal: "positive",
    wordsProcessed: 2670,
    status: "done"
  },
  {
    id: "hist-012",
    query: "Starbucks nuevos productos",
    createdAt: "2026-01-10T14:00:00Z",
    networks: ["instagram", "x"],
    totalComments: 134,
    sentimentGlobal: "positive",
    wordsProcessed: 3890,
    status: "done"
  }
]

// User data
export const currentUser = {
  name: "Ana Martinez",
  email: "ana.martinez@example.com",
  avatar: null,
  plan: currentUserPlan
}
