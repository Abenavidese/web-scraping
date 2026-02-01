import os
import time
from openai import OpenAI
import config

class LLMAnalyzer:
    def __init__(self):
        # Initialize Clients
        
        # Grok (xAI)
        self.grok_client = None
        if config.GROK_API_KEY:
            self.grok_client = OpenAI(
                api_key=config.GROK_API_KEY,
                base_url="https://api.x.ai/v1",
            )
        
        # OpenAI
        self.openai_client = None
        if config.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
            
        # DeepSeek
        self.deepseek_client = None
        if config.DEEPSEEK_API_KEY:
            self.deepseek_client = OpenAI(
                api_key=config.DEEPSEEK_API_KEY, 
                base_url="https://api.deepseek.com/v1"
            )
            
        # Gemini
        if config.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=config.GEMINI_API_KEY)
                self.gemini_model = genai.GenerativeModel('gemini-pro')
            except ImportError:
                self.gemini_model = None
        else:
            self.gemini_model = None

    def _get_prompt(self, text, network):
        return f"""
        Analiza el siguiente texto extraído de {network}.
        
        Texto: "{text}"
        
        Tareas:
        1. Clasifica el sentimiento (Positivo, Negativo, Neutro).
        2. Explica brevemente POR QUÉ clasificaste así el sentimiento.
        
        Formato de respuesta esperado (fijo):
        Sentimiento: [CLASIFICACIÓN]
        Explicación: [BREVE EXPLICACIÓN]
        """

    def analyze(self, text, network, llm_provider):
        """
        Enruta el análisis al LLM correspondiente.
        """
        if not text or len(text) < 5:
            return "Neutro", "Texto insuficiente para analizar."

        prompt = self._get_prompt(text, network)
        
        try:
            if llm_provider == 'grok':
                return self._analyze_with_grok(prompt)
            elif llm_provider == 'openai':
                return self._analyze_with_openai(prompt)
            elif llm_provider == 'gemini':
                return self._analyze_with_gemini(prompt)
            elif llm_provider == 'deepseek':
                return self._analyze_with_deepseek(prompt)
            else:
                return "Error", "Proveedor de LLM desconocido"
        except Exception as e:
            return "Error", f"Fallo en análisis con {llm_provider}: {str(e)}"

    def _analyze_with_grok(self, prompt):
        if not self.grok_client:
            return "N/A", "API Key de Grok no configurada."
        
        # Lista de modelos a probar (según reporte de usuario y docs recientes)
        models_to_try = ["grok-2-latest", "grok-beta", "grok-2", "grok-1"]
        
        # El usuario mencionó "grok 4", así que lo añadimos al principio por si acaso es un alias nuevo
        models_to_try.insert(0, "grok-4")

        last_error = None
        
        for model in models_to_try:
            try:
                # print(f"   [Debug] Intentando con modelo: {model}...") 
                completion = self.grok_client.chat.completions.create(
                    model=model, 
                    messages=[
                        {"role": "system", "content": "Eres un experto en análisis de sentimiento. Responde con: 'Sentimiento: [Positivo/Negativo/Neutro] \\n Explicación: [Breve razón]'."},
                        {"role": "user", "content": prompt}
                    ]
                )
                return self._parse_response(completion.choices[0].message.content)
            except Exception as e:
                last_error = e
                # print(f"   [Debug] Falló {model}: {e}")
                continue
        
        return "Error", f"Todos los modelos Grok fallaron. Último error: {str(last_error)}"

    def _analyze_with_openai(self, prompt):
        if not self.openai_client:
            # Simulación si no hay Key (para cumplir la práctica si el usuario solo tiene Grok)
            return "Simulado (OpenAI)", "No se proporcionó API Key. Se asume Neutro."
        
        completion = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return self._parse_response(completion.choices[0].message.content)

    def _analyze_with_deepseek(self, prompt):
        if not self.deepseek_client:
             return "Simulado (DeepSeek)", "No se proporcionó API Key. Se asume Neutro."
        
        completion = self.deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}]
        )
        return self._parse_response(completion.choices[0].message.content)

    def _analyze_with_gemini(self, prompt):
        if not self.gemini_model:
             return "Simulado (Gemini)", "No se proporcionó API Key. Se asume Neutro."
        
        response = self.gemini_model.generate_content(prompt)
        return self._parse_response(response.text)

    def _parse_response(self, response_text):
        """
        Parsea la respuesta para separar sentimiento y explicación.
        Busca 'Sentimiento:' y 'Explicación:'.
        """
        sentiment = "Indeterminado"
        explanation = response_text
        
        lines = response_text.split('\n')
        for line in lines:
            if "Sentimiento:" in line:
                sentiment = line.split("Sentimiento:")[1].strip()
            elif "Explicación:" in line:
                explanation = line.split("Explicación:")[1].strip()
        
        # Si no se encontró el formato exacto, devolvemos todo en explicación
        if sentiment == "Indeterminado":
             # Intento flexible
             if "positivo" in response_text.lower(): sentiment = "Positivo"
             elif "negativo" in response_text.lower(): sentiment = "Negativo"
             else: sentiment = "Neutro"

        return sentiment, explanation
