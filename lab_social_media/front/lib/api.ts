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
    },

    /**
     * Get global stats for a user
     */
    getStats: async (userId: string) => {
        const response = await fetch(`${API_BASE_URL}/stats?user_id=${userId}`)

        if (!response.ok) {
            throw new Error("Failed to fetch stats")
        }

        return response.json()
    },

    /**
     * Get query history for a user
     */
    getQueries: async (userId: string) => {
        const response = await fetch(`${API_BASE_URL}/queries?user_id=${userId}`)

        if (!response.ok) {
            throw new Error("Failed to fetch queries")
        }

        return response.json()
    },

    /**
     * Get posts for a user
     */
    getPosts: async (userId: string) => {
        const response = await fetch(`${API_BASE_URL}/posts?user_id=${userId}`)

        if (!response.ok) {
            throw new Error("Failed to fetch posts")
        }

        return response.json()
    },

    /**
     * Download cleaned CSV data
     */
    downloadCSV: async (userId: string, cleaningLevel: 'basico' | 'normal' | 'agresivo', network: string = 'all') => {
        const response = await fetch(`${API_BASE_URL}/download-csv`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                user_id: userId,
                cleaning_level: cleaningLevel,
                network: network
            }),
        })

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}))
            throw new Error(errorData.error || "Error descargando CSV")
        }

        // Get filename from response headers or use default
        const contentDisposition = response.headers.get('content-disposition')
        let filename = `datos_${cleaningLevel}.csv`
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?(.+)"?/)
            if (filenameMatch) {
                filename = filenameMatch[1]
            }
        }

        // Download file
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
    }
}
