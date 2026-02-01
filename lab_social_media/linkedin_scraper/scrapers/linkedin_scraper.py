import asyncio
import os
import random
import re
from typing import List, Dict
from playwright.async_api import async_playwright, Page, BrowserContext
from .base_scraper import SocialScraper


class LinkedInScraper(SocialScraper):

    def __init__(self, li_at_cookie: str, headless: bool = False):
        self.li_at_cookie = li_at_cookie
        self.headless = headless
        self.base_url = "https://www.linkedin.com"

    def _is_spanish(self, text: str) -> bool:
        """
        Detección estricta de español basada en puntaje.
        Penaliza fuertemente palabras exclusivas de inglés y portugués.
        """
        text = text.lower()
        tokens = set(text.split())
        
        # Palabras exclusivas (o casi) de cada idioma
        es_signs = {'y', 'el', 'la', 'en', 'que', 'los', 'del', 'las', 'por', 'para', 'con', 'una', 'su', 'al', 'lo', 'como', 'más', 'pero', 'sus', 'le', 'ya', 'o', 'fue'}
        
        # Penalizadores Fuertes (Si aparecen estas, probablemente NO es español puro)
        en_signs = {'the', 'and', 'start', 'end', 'to', 'of', 'in', 'is', 'for', 'you', 'that', 'with', 'on', 'are', 'this', 'from', 'be', 'at', 'have', 'as', 'it', 'not', 'we', 'will', 'can', 'top', 'new', 'time', 'like'}
        pt_signs = {'e', 'em', 'um', 'uma', 'com', 'os', 'as', 'do', 'da', 'no', 'na', 'por', 'para', 'mais', 'como', 'foi', 'que', 'muito', 'são', 'não', 'você'}
        
        score = 0
        
        # Conteo de Puntos
        for t in tokens:
            if t in es_signs:
                score += 1
            if t in en_signs:
                score -= 5 # Penalización agresiva para INGLÉS
            if t in pt_signs and t not in es_signs: # Cuidado con intersecciones como 'para', 'que', 'com'(no)
                 if t not in ['para', 'que', 'como', 'por']: # Palabras compartidas neutras
                    score -= 2 # Penalización moderada para PORTUGUÉS
        
        # Regla de veto directo: Si hay demasiadas palabras en inglés, adiós.
        en_count = sum(1 for t in tokens if t in en_signs)
        if en_count >= 2:
            return False

        return score >= 2 # Necesitamos al menos 2 palabras netamente españolas y saldo positivo

    async def _human_delay(self, min_ms: int = 500, max_ms: int = 2000, chance: float = 1.0):
        """
        Pausa aleatoria para simular comportamiento humano.
        chance: Probabilidad de ejecutar el delay (0.0 a 1.0).
        """
        if random.random() > chance:
            return

        delay = random.randint(min_ms, max_ms)
        await asyncio.sleep(delay / 1000)

    async def _scroll_page(self, page: Page):
        """Scroll suave hacia abajo (Optimizado)."""
        # Menos pasos, más rápido
        for _ in range(random.randint(2, 4)):
            await page.mouse.wheel(0, random.randint(400, 900))
            await asyncio.sleep(random.uniform(0.2, 0.8))

    async def _extract_comments(self, page, item_locator, max_qty):
        comments = []
        try:
            # --- ESTRATEGIA ROBUSTA BASADA EN TEXTO ---
            # En lugar de clases CSS que cambian, buscamos lo que ve el usuario.
            
            # 1. BUSCAR INDICADOR DE COMENTARIOS (ej: "5 comentarios")
            # Usamos Regex para buscar texto dinámico dentro del item
            comment_indicator = item_locator.locator("button, a, span").filter(has_text=re.compile(r"\d+\s+(coment|comment)", re.IGNORECASE)).first
            
            should_have_comments = False
            if await comment_indicator.count() > 0 and await comment_indicator.is_visible():
                should_have_comments = True
                # print(f"   [DEBUG] Indicador Visual: {await comment_indicator.inner_text()}")
                try:
                    # Intento 1: Clic directo en el texto "X comentarios"
                    await comment_indicator.click(force=True)
                    await asyncio.sleep(3)
                except: pass
            
            # 2. INTENTO GENÉRICO: BOTÓN DE ACCIÓN "COMENTAR"
            # Si no clickeamos arriba o falló, buscamos el botón de acción principal
            # Suele tener aria-label="Comentar" o texto "Comentar"
            action_btn = item_locator.locator("button").filter(has_text=re.compile(r"^(comentar|comment)$", re.IGNORECASE)).first
            if await action_btn.count() == 0:
                 action_btn = item_locator.locator("button[aria-label*='comentar'], button[aria-label*='comment']").first
            
            if await action_btn.is_visible():
                # print("   [DEBUG] Click en botón Acción Comentar")
                try:
                    await action_btn.click(force=True)
                    await asyncio.sleep(3)
                except: pass

            # 3. EXTRAER CONTENIDO
            # Ahora buscamos cualquier bloque que parezca un comentario
            # Clases comunes 2024/2025
            potential_blocks = [
                "article.comments-comment-entity",  # <--- HITO: Clase confirmada en debug 2026
                "article.comments-comment-item",
                "div.comments-comment-item",
                "div.feed-shared-comment-item",
                "li.comments-comments-list__comment-item",
                "div.comments-comments-list__comment-item-content" 
            ]
            
            # Determinar contenedor (Modal vs Inline)
            modal = page.locator("div.artdeco-modal[role='dialog']")
            container = item_locator
            if await modal.is_visible():
                container = modal
            
            # PEQUEÑO SCROLL PARA FORZAR RENDER (Lazy Loading)
            # A veces los comentarios no cargan hasta que scrolleas un poco el contenedor
            try:
                await container.dispatch_event("wheel", {"deltaY": 500})
                await asyncio.sleep(1)
            except: pass

            found_loc = None
            for sel in potential_blocks:
                loc = container.locator(sel)
                if await loc.count() > 0:
                    found_loc = loc
                    break
            
            if found_loc:
                count = await found_loc.count()
                take = min(count, max_qty)
                for i in range(take):
                    c = found_loc.nth(i)
                    # Extraer texto: Priorizamos el span con dirección de texto
                    text_loc = c.locator("span[dir='ltr']").first
                    if await text_loc.count() == 0:
                        text_loc = c.locator("div.feed-shared-text, div.update-components-text").first
                        
                    if await text_loc.count() == 0:
                         # Intento final: tomar todo el texto del item
                         text_loc = c
                    
                    if await text_loc.count() > 0:
                        t = await text_loc.inner_text()
                        cleaned = t.replace('\n', ' ').strip()
                        if cleaned:
                            comments.append(cleaned)
            
            # --- DEBUGGING FINAL: GUARDAR HTML SI FALLA ---
            # Solo guardamos si TENIAMOS un indicador visual (ej "5 comentarios") pero sacamos 0.
            # if should_have_comments and len(comments) == 0:
            #     print(f"   [WARN] El post decía tener comentarios pero no se extrajeron. Guardando debug...")
            #     debug_file = f"output/debug_fail_{random.randint(1000,9999)}.html"
            #     os.makedirs('output', exist_ok=True)
            #     html_content = await item_locator.inner_html()
            #     with open(debug_file, "w", encoding="utf-8") as f:
            #          f.write(f"<!-- DUMP DEL POST -->\n{html_content}")
            #     print(f"   [DEBUG] HTML guardado en {debug_file}")

            # Limpieza (Cerrar modal)
            if await modal.is_visible():
                await page.keyboard.press("Escape")
                
        except Exception as e:
            # print(f"   [Error Extracción]: {e}")
            pass
            
        return comments

    async def extract(self, query: str, limit: int = 10, max_comments: int = 0) -> List[Dict]:
        results = []
        seen_hashes = set()
        
        async with async_playwright() as p:
            # 1. Lanzar navegador
            browser = await p.chromium.launch(headless=self.headless, slow_mo=50)
            
            # 2. Configurar contexto
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 800}
            )
            
            if self.li_at_cookie:
                print(f"[{self.__class__.__name__}] Inyectando cookie de sesión...")
                await context.add_cookies([{
                    'name': 'li_at',
                    'value': self.li_at_cookie,
                    'domain': '.linkedin.com',
                    'path': '/'
                }])
            
            page = await context.new_page()

            # --- NITRO MODE: BLOQUEO DE RECURSOS PESADOS ---
            # Bloqueamos imágenes, fuentes y multimedia para acelerar la carga.
            await page.route("**/*", lambda route: route.abort() 
                if route.request.resource_type in ["image", "media", "font"] 
                else route.continue_()
            )

            try:
                print(f"[{self.__class__.__name__}] Buscando '{query}' en LinkedIn...")
                # Búsqueda optimizada
                enhanced_query = f"{query} AND (el OR la OR en OR que)"
                encoded_query = enhanced_query.replace(" ", "%20")
                search_url = f"https://www.linkedin.com/search/results/content/?keywords={encoded_query}&origin=SWITCH_SEARCH_VERTICAL"
                
                try:
                    await page.goto(search_url, timeout=60000)
                    await self._human_delay(1000, 2000)  # Reducido de 2000-4000
                except Exception as e:
                    if "ERR_TOO_MANY_REDIRECTS" in str(e):
                        print("\n[!] ERROR: Cookie expirada (Redirección en bucle). Actualiza 'li_at' en config.py.")
                        return []
                    raise e
                
                # Check login
                if "login" in page.url or "signup" in page.url:
                     print(f"[{self.__class__.__name__}] ⚠️ ERROR: Login requerido. La cookie puede ser inválida.")
                     return []

                # --- BUCLE PRINCIPAL DE EXTRACCIÓN ---
                no_new_data_counter = 0
                max_retries_no_data = 10  # Reducido de 30 a 10 para ser más rápido
                
                print(f"[{self.__class__.__name__}] Iniciando extracción. Meta: {limit} posts.")
                
                while len(results) < limit:
                    # Buscar items en el DOM actual
                    post_items = await page.locator(".search-results-container .artdeco-card, div.feed-shared-update-v2").all()
                    
                    new_in_this_pass = 0
                    
                    # [..LOOP CONTENTS..]
                    
                    for item in post_items:
                        if len(results) >= limit:
                            break
                        
                        try:
                            # Obtener texto para hash (deduplicación)
                            text_el = item.locator("div.update-components-text, div.feed-shared-update-v2__description-wrapper").first
                            if await text_el.count() == 0:
                                continue
                                
                            raw_text = await text_el.inner_text()
                            post_hash = hash(raw_text[:100])
                            
                            if post_hash in seen_hashes:
                                continue # Ya procesado
                            
                            # Filtro Idioma RELAJADO - solo verificar que tenga algo de contenido
                            # Removemos el filtro estricto de español para no perder posts
                            if len(raw_text.strip()) < 10:  # Solo verificar que tenga contenido mínimo
                                continue

                            # Marcar visto
                            seen_hashes.add(post_hash)
                            
                            # Expandir 'ver más' (sin delay)
                            try:
                                see_more = item.locator("button.feed-shared-inline-show-more-text__see-more-less-toggle").first
                                if await see_more.is_visible():
                                    await see_more.click()
                                    await asyncio.sleep(0.3)  # Reducido de 0.5
                            except: pass
                            
                            # Re-leer texto completo
                            post_text = await text_el.inner_text()
                            
                            # Autor
                            author = "Desconocido"
                            author_el = item.locator(".update-components-actor__name span[aria-hidden='true'], .update-components-actor__title span[aria-hidden='true']").first
                            if await author_el.count() > 0:
                                author = await author_el.inner_text()

                            # Comentarios (OPCIONAL - solo si se pide)
                            comments_list = []
                            if max_comments > 0:
                                comments_list = await self._extract_comments(page, item, max_comments)

                            # Guardar
                            results.append({
                                "source": "LinkedIn Post",
                                "title": f"Post de {author}",
                                "content": post_text,
                                "comments": comments_list
                            })
                            new_in_this_pass += 1
                            print(f"   [{len(results)}/{limit}] Post de {author} | Comentarios: {len(comments_list)}")
                            
                        except Exception as e:
                            continue
                            
                    # Verificar progreso
                    if len(results) >= limit:
                        print(f"   [!] Meta alcanzada ({len(results)}/{limit}).")
                        break
                        
                    if new_in_this_pass == 0:
                        no_new_data_counter += 1
                        print(f"   ...scrolleando (Intento {no_new_data_counter}/{max_retries_no_data} sin nuevos posts)...")
                        
                        # Wiggle Strategy: Subir un poco y volver a bajar (solo cada 2 intentos)
                        if no_new_data_counter % 2 == 0:
                            await page.mouse.wheel(0, -400)  # Reducido
                            await asyncio.sleep(0.5)  # Reducido
                            await page.mouse.wheel(0, 600)  # Reducido
                        
                        if no_new_data_counter >= max_retries_no_data:
                            print("   [!] No aparecen más resultados nuevos. Terminando.")
                            break
                    else:
                        no_new_data_counter = 0
                        print(f"   ...scrolleando para buscar más...")

                    # Scroll MÁS RÁPIDO
                    await self._scroll_page(page)
                    # Delay mínimo entre scrolls
                    await self._human_delay(500, 1000, chance=0.5)  # Reducido significativamente

            except Exception as e:
                print(f"Error crítico en scraper: {e}")
            finally:
                print("Cerrando navegador automáticamente...")
                await context.close()
                await browser.close()
                
        return results
