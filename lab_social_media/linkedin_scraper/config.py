# CONFIGURACIÓN DE CREDENCIALES
import os
from dotenv import load_dotenv

load_dotenv()

# API KEYS LLMs
GROK_API_KEY = os.getenv("GROK_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# MÉTODO DE COOKIE (MÁS SEGURO Y ESTABLE)
# 1. Ve a linkedin.com en tu navegador y logueate.
# 2. Presiona F12 -> Pestaña "Application" (o Almacenamiento) -> Cookies -> https://www.linkedin.com
# 3. Busca la cookie llamada "li_at". Copia su valor y pégalo abajo.

LINKEDIN_LI_AT_COOKIE = "AQEDAWOWvO8B72WTAAABm9wiQ14AAAGc5OuMO00Av7QeurQAGKAnilrDo0-PMsOFNBQ7SJGYx7Tq7jhX2172OmVKNjvDaBRIc0sijZvAz_6u-95NYuR5sBvf7027ajFmq9ja0DzTY7Oylnnk8eARj8ij"

# Configuración de consultas por defecto (opcional)
DEFAULT_QUERY = "Desarrollador Python Senior"
DEFAULT_LIMIT = 5
