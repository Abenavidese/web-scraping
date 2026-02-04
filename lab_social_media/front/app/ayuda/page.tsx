"use client"

import { BookOpen, MessageCircle, FileQuestion, Zap, Database, Brain, Search, ExternalLink } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"

const faqs = [
  {
    question: "Como funciona el analisis de sentimiento?",
    answer: "Nuestro sistema extrae comentarios y publicaciones de las redes sociales seleccionadas de forma concurrente. Luego, el texto pasa por un proceso de preprocesamiento NLP (limpieza, tokenizacion, eliminacion de stopwords) antes de ser clasificado por un modelo de lenguaje (LLM) especializado para cada red social."
  },
  {
    question: "Por que se usa un LLM diferente para cada red?",
    answer: "Cada modelo tiene fortalezas distintas en la interpretacion del lenguaje segun la plataforma. OpenAI (GPT-4) destaca en el contenido de Facebook, Google Gemini en Instagram, xAI Grok en X (Twitter), y DeepSeek en LinkedIn. Esta diversificacion mejora la precision global del analisis."
  },
  {
    question: "Como se calcula el consumo de palabras?",
    answer: "El consumo se calcula sumando el total de palabras en el texto extraido de las redes sociales mas las palabras de tu consulta. Antes de ejecutar el analisis, te mostramos una estimacion basada en el numero de resultados solicitados por red."
  },
  {
    question: "Que significa el nivel de limpieza?",
    answer: "El nivel de limpieza determina que tan agresivo es el preprocesamiento del texto: Basico solo elimina caracteres especiales; Normal anade tokenizacion y eliminacion de stopwords; Agresivo incluye stemming/lematizacion completa. Niveles mas altos pueden perder contexto pero reducen ruido."
  },
  {
    question: "Puedo usar mis propias API keys?",
    answer: "Si, en la seccion de Configuracion puedes ingresar tus propias claves de API para cada proveedor de LLM. Esto es util si tienes cuentas empresariales o quieres usar cuotas personalizadas."
  },
  {
    question: "Que pasa si mi consulta excede el cupo del plan?",
    answer: "El sistema te alertara antes de ejecutar el analisis si la estimacion de palabras excede tu cupo disponible. Puedes reducir el numero de resultados por red o actualizar tu plan para continuar."
  },
  {
    question: "Puedo exportar los resultados?",
    answer: "Si, en la seccion de Resultados puedes descargar los datos en formato CSV o JSON. Ademas, en Storytelling puedes exportar el reporte narrativo completo en PDF (disponible segun tu plan)."
  },
  {
    question: "Cuanto tiempo se guardan mis analisis?",
    answer: "Depende de tu plan: Free no tiene historial, Student guarda 30 dias, Pro tiene historial ilimitado, y Enterprise tambien es ilimitado con backups adicionales."
  }
]

const guides = [
  {
    title: "Primeros pasos",
    description: "Aprende a crear tu primera consulta de analisis",
    icon: Zap,
  },
  {
    title: "Interpretar resultados",
    description: "Guia para entender los graficos y metricas",
    icon: Brain,
  },
  {
    title: "Optimizar consultas",
    description: "Tips para obtener mejores resultados",
    icon: Search,
  },
  {
    title: "Gestion de datos",
    description: "Como exportar y organizar tus analisis",
    icon: Database,
  },
]

export default function AyudaPage() {
  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Centro de ayuda</h1>
        <p className="text-muted-foreground">
          Documentacion, guias y preguntas frecuentes
        </p>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Buscar en la documentacion..."
              className="pl-9 h-12 text-base"
            />
          </div>
        </CardContent>
      </Card>

      {/* Quick Links */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {guides.map((guide) => (
          <Card key={guide.title} className="cursor-pointer hover:border-primary/50 transition-colors">
            <CardContent className="pt-6">
              <div className="flex flex-col items-center text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 mb-4">
                  <guide.icon className="h-6 w-6 text-primary" />
                </div>
                <p className="font-medium">{guide.title}</p>
                <p className="text-sm text-muted-foreground mt-1">{guide.description}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* FAQs */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileQuestion className="h-5 w-5" />
            Preguntas frecuentes
          </CardTitle>
          <CardDescription>
            Respuestas a las dudas mas comunes
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Accordion type="single" collapsible className="w-full">
            {faqs.map((faq, index) => (
              <AccordionItem key={index} value={`item-${index}`}>
                <AccordionTrigger className="text-left">
                  {faq.question}
                </AccordionTrigger>
                <AccordionContent className="text-muted-foreground">
                  {faq.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </CardContent>
      </Card>

      {/* Documentation */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="h-5 w-5" />
            Documentacion tecnica
          </CardTitle>
          <CardDescription>
            Recursos avanzados para desarrolladores
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="flex items-start gap-4 p-4 rounded-lg border">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                <FileQuestion className="h-5 w-5" />
              </div>
              <div>
                <p className="font-medium">API Reference</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Documentacion completa de endpoints
                </p>
                <Button variant="link" className="px-0 mt-2">
                  Ver documentacion <ExternalLink className="h-3 w-3 ml-1" />
                </Button>
              </div>
            </div>
            <div className="flex items-start gap-4 p-4 rounded-lg border">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                <Database className="h-5 w-5" />
              </div>
              <div>
                <p className="font-medium">Webhooks</p>
                <p className="text-sm text-muted-foreground mt-1">
                  Integra notificaciones en tiempo real
                </p>
                <Button variant="link" className="px-0 mt-2">
                  Configurar webhooks <ExternalLink className="h-3 w-3 ml-1" />
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Contact Support */}
      <Card>
        <CardContent className="py-8">
          <div className="flex flex-col items-center text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary/10 mb-4">
              <MessageCircle className="h-7 w-7 text-primary" />
            </div>
            <h3 className="text-lg font-medium">No encuentras lo que buscas?</h3>
            <p className="text-muted-foreground mt-2 max-w-md">
              Nuestro equipo de soporte esta disponible para ayudarte con cualquier 
              duda o problema que tengas.
            </p>
            <div className="flex gap-4 mt-6">
              <Button variant="outline">
                Ver tutoriales
              </Button>
              <Button>
                Contactar soporte
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
