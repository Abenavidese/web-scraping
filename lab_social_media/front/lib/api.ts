export const API_BASE_URL = "http://localhost:5000/api"

export interface ScrapeRequest {
    networks: string[]
    query: string
    num_posts: number
    num_comments: number
    user_id?: string
    limits?: Record<string, number>
}

export interface ChatRequest {
    user_id: string
    message: string
}

export const api = {
    /**
     * Run the scrapers
     */
    scrape: async (data: ScrapeRequest) => {
        const response = await fetch(`${API_BASE_URL}/scrape`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(data),
        })

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}))
            throw new Error(errorData.error || "Error al ejecutar scrapers")
        }

        return response.json()
    },

    /**
     * Get analytics data
     */
    getAnalytics: async (userId: string) => {
        const response = await fetch(`${API_BASE_URL}/analytics?user_id=${userId}`)

        if (!response.ok) {
            throw new Error("Error obteniendo analiticas")
        }

        return response.json()
    },

    /**
     * Get sentiment distribution
     */
    getSentiments: async (userId: string) => {
        const response = await fetch(`${API_BASE_URL}/sentiments?user_id=${userId}`)

        if (!response.ok) {
            throw new Error("Error obteniendo sentimientos")
        }

        return response.json()
    },

    /**
     * Chat with data
     */
    chat: async (data: ChatRequest) => {
        const response = await fetch(`${API_BASE_URL}/chat-with-data`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(data),
        })

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}))
            throw new Error(errorData.error || "Error en el chat")
        }

        return response.json()
    }
}
