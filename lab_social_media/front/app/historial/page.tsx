"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Calendar, Search, Eye, RotateCcw, Trash2, MoreHorizontal, AlertCircle, FileText, MessageSquare, CheckCircle2, XCircle, Loader2 } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { networkConfig } from "@/lib/mock-data"
import { useAuth } from "@/contexts/auth-context"
import { api } from "@/lib/api"

interface HistoryItem {
  id: number
  query_text: string
  network: string
  created_at: string
  status: string
}

function SentimentBadge({ sentiment }: { sentiment: string }) {
  return (
    <Badge
      variant={sentiment === "positive" ? "default" : sentiment === "negative" ? "destructive" : "secondary"}
      className={sentiment === "positive" ? "bg-success text-success-foreground hover:bg-success/80" : ""}
    >
      {sentiment === "positive" ? "Positivo" : sentiment === "negative" ? "Negativo" : "Neutral"}
    </Badge>
  )
}

function StatusBadge({ status }: { status: string }) {
  if (status === "done") {
    return (
      <Badge variant="outline" className="text-success border-success/50">
        <CheckCircle2 className="h-3 w-3 mr-1" />
        Completado
      </Badge>
    )
  }
  if (status === "error") {
    return (
      <Badge variant="outline" className="text-destructive border-destructive/50">
        <XCircle className="h-3 w-3 mr-1" />
        Error
      </Badge>
    )
  }
  return (
    <Badge variant="outline">
      {status}
    </Badge>
  )
}

export default function HistorialPage() {
  const { user } = useAuth()
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState("")
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [selectedItem, setSelectedItem] = useState<HistoryItem | null>(null)
  const [deleteItem, setDeleteItem] = useState<HistoryItem | null>(null)
  const [items, setItems] = useState<HistoryItem[]>([])
  const [posts, setPosts] = useState<any[]>([])

  useEffect(() => {
    if (!user) {
      setLoading(false)
      return
    }

    const loadHistory = async () => {
      try {
        const [queriesData, postsData, statsData] = await Promise.all([
          api.getQueries(user.id),
          api.getPosts(user.id),
          api.getStats(user.id)
        ])

        console.log('History data loaded:', { queriesData, postsData, statsData })

        setItems(queriesData.queries || [])
        setPosts(postsData.posts || [])
        
        // Store total comments from stats for accurate count
        const commentsCount = statsData.total_comments || 0
        console.log('Total comments from stats:', commentsCount)
        
      } catch (error) {
        console.error('Error loading history:', error)
      } finally {
        setLoading(false)
      }
    }

    loadHistory()
  }, [user])

  // Group posts by query and network
  const getQueryStats = (query: string, network: string) => {
    const queryPosts = posts.filter(p => 
      p.query === query && p.network === network
    )
    
    const totalComments = queryPosts.reduce((sum, p) => sum + (p.num_comments || 0), 0)
    const totalWords = queryPosts.reduce((sum, p) => {
      const text = p.text || ''
      return sum + text.split(/\s+/).filter(w => w.length > 0).length
    }, 0)
    
    // Calculate dominant sentiment
    const sentiments = queryPosts.map(p => p.sentiment?.toLowerCase() || 'neutral')
    const sentimentCounts = {
      positive: sentiments.filter(s => s.includes('positiv')).length,
      negative: sentiments.filter(s => s.includes('negativ')).length,
      neutral: sentiments.length - sentiments.filter(s => s.includes('positiv') || s.includes('negativ')).length
    }
    
    let dominantSentiment = 'neutral'
    if (sentimentCounts.positive > sentimentCounts.negative && sentimentCounts.positive > sentimentCounts.neutral) {
      dominantSentiment = 'positive'
    } else if (sentimentCounts.negative > sentimentCounts.positive && sentimentCounts.negative > sentimentCounts.neutral) {
      dominantSentiment = 'negative'
    }

    return {
      totalComments,
      totalWords,
      sentiment: dominantSentiment,
      postsCount: queryPosts.length
    }
  }

  const filteredItems = items.filter(item => {
    if (searchTerm && !item.query_text.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false
    }
    if (dateFrom) {
      const itemDate = new Date(item.created_at)
      const fromDate = new Date(dateFrom)
      if (itemDate < fromDate) return false
    }
    if (dateTo) {
      const itemDate = new Date(item.created_at)
      const toDate = new Date(dateTo)
      if (itemDate > toDate) return false
    }
    return true
  })

  const handleDelete = (item: HistoryItem) => {
    setItems(prev => prev.filter(i => i.id !== item.id))
    setDeleteItem(null)
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-96">
        <Loader2 className="animate-spin h-8 w-8 text-primary" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Historial</h1>
        <p className="text-muted-foreground">
          Consultas de {user?.username || "usuario"} - resultados guardados
        </p>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Buscar por consulta..."
                className="pl-9"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <div className="flex gap-2">
              <div className="relative">
                <Calendar className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  type="date"
                  className="pl-9 w-[160px]"
                  placeholder="Desde"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                />
              </div>
              <div className="relative">
                <Calendar className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  type="date"
                  className="pl-9 w-[160px]"
                  placeholder="Hasta"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results Count */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {filteredItems.length} de {items.length} consultas
        </p>
      </div>

      {/* History Table */}
      {filteredItems.length > 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Consulta</TableHead>
                    <TableHead>Fecha</TableHead>
                    <TableHead>Redes</TableHead>
                    <TableHead>Posts</TableHead>
                    <TableHead>Sentimiento</TableHead>
                    <TableHead>Palabras</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredItems.map((item) => {
                    const stats = getQueryStats(item.query_text, item.network)
                    
                    return (
                      <TableRow key={item.id}>
                        <TableCell>
                          <p className="font-medium">{item.query_text}</p>
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {new Date(item.created_at).toLocaleDateString("es-ES", {
                            day: "2-digit",
                            month: "short",
                            year: "numeric"
                          })}
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-1">
                            <div
                              className="h-6 w-6 rounded flex items-center justify-center text-white text-xs font-bold"
                              style={{ backgroundColor: networkConfig[item.network]?.color || '#666' }}
                              title={networkConfig[item.network]?.name || item.network}
                            >
                              {item.network[0].toUpperCase()}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>{stats.postsCount}</TableCell>
                        <TableCell>
                          <SentimentBadge sentiment={stats.sentiment} />
                        </TableCell>
                        <TableCell>{stats.totalWords.toLocaleString()}</TableCell>
                        <TableCell>
                          <StatusBadge status={item.status} />
                        </TableCell>
                        <TableCell className="text-right">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon">
                                <MoreHorizontal className="h-4 w-4" />
                                <span className="sr-only">Acciones</span>
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => setSelectedItem(item)}>
                                <Eye className="h-4 w-4 mr-2" />
                                Ver resultados
                              </DropdownMenuItem>
                              <DropdownMenuItem asChild>
                                <Link href={`/nueva-consulta?query=${encodeURIComponent(item.query_text)}`}>
                                  <RotateCcw className="h-4 w-4 mr-2" />
                                  Repetir consulta
                                </Link>
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem 
                                className="text-destructive focus:text-destructive"
                                onClick={() => setDeleteItem(item)}
                              >
                                <Trash2 className="h-4 w-4 mr-2" />
                                Eliminar
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-muted">
                <FileText className="h-6 w-6 text-muted-foreground" />
              </div>
              <h3 className="mt-4 text-lg font-medium">Sin resultados</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                No se encontraron consultas que coincidan con tu busqueda.
              </p>
              <Button className="mt-4 bg-transparent" variant="outline" onClick={() => {
                setSearchTerm("")
                setDateFrom("")
                setDateTo("")
              }}>
                Limpiar filtros
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Detail Dialog */}
      <Dialog open={!!selectedItem} onOpenChange={() => setSelectedItem(null)}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Detalle de consulta</DialogTitle>
            <DialogDescription>
              Resumen de los resultados guardados
            </DialogDescription>
          </DialogHeader>
          {selectedItem && (() => {
            const stats = getQueryStats(selectedItem.query_text, selectedItem.network)
            return (
              <div className="space-y-4">
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">Consulta</p>
                  <p className="font-medium">&quot;{selectedItem.query_text}&quot;</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Fecha</p>
                    <p className="font-medium">
                      {new Date(selectedItem.created_at).toLocaleDateString("es-ES", {
                        day: "numeric",
                        month: "long",
                        year: "numeric"
                      })}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Estado</p>
                    <StatusBadge status={selectedItem.status} />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 p-4 rounded-lg bg-muted">
                  <div className="text-center">
                    <p className="text-2xl font-bold">{stats.postsCount}</p>
                    <p className="text-xs text-muted-foreground">Posts</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold">{stats.totalWords.toLocaleString()}</p>
                    <p className="text-xs text-muted-foreground">Palabras</p>
                  </div>
                  <div className="text-center">
                    <SentimentBadge sentiment={stats.sentiment} />
                    <p className="text-xs text-muted-foreground mt-1">Sentimiento</p>
                  </div>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground mb-2">Red analizada</p>
                  <Badge variant="secondary">
                    {networkConfig[selectedItem.network]?.name || selectedItem.network}
                  </Badge>
                </div>
              </div>
            )
          })()}
          <DialogFooter>
            <Button variant="outline" onClick={() => setSelectedItem(null)}>
              Cerrar
            </Button>
            <Button asChild>
              <Link href="/resultados">Ver resultados completos</Link>
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={!!deleteItem} onOpenChange={() => setDeleteItem(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Eliminar consulta</AlertDialogTitle>
            <AlertDialogDescription>
              Esta seguro que desea eliminar la consulta &quot;{deleteItem?.query_text}&quot;? 
              Esta accion no se puede deshacer.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              onClick={() => deleteItem && handleDelete(deleteItem)}
            >
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
