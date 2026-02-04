"use client"

import { useState, useRef, useEffect } from "react"
import { useAuth } from "@/contexts/auth-context"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Send, Bot, User, Loader2, Sparkles } from "lucide-react"

interface Message {
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

export default function StorytellingPage() {
  const { user } = useAuth()
  const [input, setInput] = useState("")
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Hola, soy tu asistente de datos. Pregúntame sobre los resultados de tu último análisis.", timestamp: new Date() }
  ])
  const [isLoading, setIsLoading] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || !user) return

    const userMsg: Message = { role: "user", content: input, timestamp: new Date() }
    setMessages(prev => [...prev, userMsg])
    setInput("")
    setIsLoading(true)

    try {
      const response = await api.chat({
        user_id: user.id,
        message: userMsg.content
      })

      const botMsg: Message = {
        role: "assistant",
        content: response.response,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, botMsg])

    } catch (error) {
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "Lo siento, hubo un error al consultar tus datos. Intenta nuevamente.",
        timestamp: new Date()
      }])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="h-[calc(100vh-120px)] flex flex-col gap-4">
      <div>
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <Sparkles className="text-primary" /> Storytelling AI
        </h1>
        <p className="text-muted-foreground">
          Interpretación inteligente de tus resultados con DeepSeek
        </p>
      </div>

      <Card className="flex-1 flex flex-col overflow-hidden border-primary/20">
        <ScrollArea className="flex-1 p-4" ref={scrollRef}>
          <div className="space-y-4">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"
                  }`}
              >
                <Avatar className="h-8 w-8">
                  {msg.role === "assistant" ? (
                    <AvatarFallback className="bg-primary text-primary-foreground"><Bot size={16} /></AvatarFallback>
                  ) : (
                    <AvatarFallback className="bg-muted"><User size={16} /></AvatarFallback>
                  )}
                </Avatar>

                <div
                  className={`rounded-lg p-3 max-w-[80%] text-sm ${msg.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted"
                    }`}
                >
                  {msg.content}
                  <span className="text-[10px] opacity-50 block mt-1 text-right">
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex gap-3">
                <Avatar className="h-8 w-8">
                  <AvatarFallback className="bg-primary text-primary-foreground"><Bot size={16} /></AvatarFallback>
                </Avatar>
                <div className="bg-muted rounded-lg p-3 flex items-center">
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  <span className="text-xs text-muted-foreground">Analizando datos...</span>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        <div className="p-4 bg-background border-t">
          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
          >
            <Input
              placeholder="Ej: ¿Cuáles son las principales quejas en los comentarios negativos?"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
            />
            <Button type="submit" size="icon" disabled={isLoading || !input.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>
      </Card>
    </div>
  )
}
