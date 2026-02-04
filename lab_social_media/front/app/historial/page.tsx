"use client"

import { useState } from "react"
import Link from "next/link"
import { Calendar, Search, Eye, RotateCcw, Trash2, MoreHorizontal, AlertCircle, FileText, MessageSquare, CheckCircle2, XCircle } from "lucide-react"
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
import { historyItems, networkConfig, type HistoryItem } from "@/lib/mock-data"
import { useAuth } from "@/contexts/auth-context"

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
  const [searchTerm, setSearchTerm] = useState("")
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [selectedItem, setSelectedItem] = useState<HistoryItem | null>(null)
  const [deleteItem, setDeleteItem] = useState<HistoryItem | null>(null)
  const [items, setItems] = useState(historyItems)

  const filteredItems = items.filter(item => {
    if (searchTerm && !item.query.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false
    }
    if (dateFrom) {
      const itemDate = new Date(item.createdAt)
      const fromDate = new Date(dateFrom)
      if (itemDate < fromDate) return false
    }
    if (dateTo) {
      const itemDate = new Date(item.createdAt)
      const toDate = new Date(dateTo)
      if (itemDate > toDate) return false
    }
    return true
  })

  const handleDelete = (item: HistoryItem) => {
    setItems(prev => prev.filter(i => i.id !== item.id))
    setDeleteItem(null)
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
                    <TableHead>Comentarios</TableHead>
                    <TableHead>Sentimiento</TableHead>
                    <TableHead>Palabras</TableHead>
                    <TableHead>Estado</TableHead>
                    <TableHead className="text-right">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredItems.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell>
                        <p className="font-medium">{item.query}</p>
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {new Date(item.createdAt).toLocaleDateString("es-ES", {
                          day: "2-digit",
                          month: "short",
                          year: "numeric"
                        })}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          {item.networks.map(network => (
                            <div
                              key={network}
                              className="h-6 w-6 rounded flex items-center justify-center text-white text-xs font-bold"
                              style={{ backgroundColor: networkConfig[network].color }}
                              title={networkConfig[network].name}
                            >
                              {network[0].toUpperCase()}
                            </div>
                          ))}
                        </div>
                      </TableCell>
                      <TableCell>{item.totalComments}</TableCell>
                      <TableCell>
                        <SentimentBadge sentiment={item.sentimentGlobal} />
                      </TableCell>
                      <TableCell>{item.wordsProcessed.toLocaleString()}</TableCell>
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
                              <Link href={`/nueva-consulta?query=${encodeURIComponent(item.query)}`}>
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
                  ))}
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
          {selectedItem && (
            <div className="space-y-4">
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">Consulta</p>
                <p className="font-medium">&quot;{selectedItem.query}&quot;</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Fecha</p>
                  <p className="font-medium">
                    {new Date(selectedItem.createdAt).toLocaleDateString("es-ES", {
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
                  <p className="text-2xl font-bold">{selectedItem.totalComments}</p>
                  <p className="text-xs text-muted-foreground">Comentarios</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold">{selectedItem.wordsProcessed.toLocaleString()}</p>
                  <p className="text-xs text-muted-foreground">Palabras</p>
                </div>
                <div className="text-center">
                  <SentimentBadge sentiment={selectedItem.sentimentGlobal} />
                  <p className="text-xs text-muted-foreground mt-1">Sentimiento</p>
                </div>
              </div>

              <div>
                <p className="text-sm text-muted-foreground mb-2">Redes analizadas</p>
                <div className="flex flex-wrap gap-2">
                  {selectedItem.networks.map(network => (
                    <Badge key={network} variant="secondary">
                      {networkConfig[network].name}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          )}
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
              Esta seguro que desea eliminar la consulta &quot;{deleteItem?.query}&quot;? 
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
