import asyncio
import os
import random
import re
from typing import List, Dict
from datetime import datetime
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
        """
        Extrae comentarios de un post de LinkedIn.
        Estrategia mejorada con múltiples intentos y debugging.
        """
        comments = []
        try:
            # --- PASO 1: BUSCAR INDICADOR DE COMENTARIOS ---
            # Buscar texto que indique cantidad de comentarios (ej: "5 comentarios", "10 comments")
            comment_indicator = item_locator.locator("button, a, span").filter(
                has_text=re.compile(r"\d+\s+(coment|comment)", re.IGNORECASE)
            ).first
            
            should_have_comments = False
            if await comment_indicator.count() > 0:
                try:
                    if await comment_indicator.is_visible():
                        should_have_comments = True
                        indicator_text = await comment_indicator.inner_text()
                        print(f"   [DEBUG] Post tiene comentarios: {indicator_text}")
                        
                        # Clic en el indicador para abrir/expandir comentarios
                        await comment_indicator.scroll_into_view_if_needed()
                        await asyncio.sleep(0.5)
                        await comment_indicator.click(force=True, timeout=5000)
                        print(f"   [DEBUG] Click en indicador de comentarios exitoso")
                        
                        # Esperar a que carguen los comentarios
                        await asyncio.sleep(3)
                except Exception as e:
                    print(f"   [DEBUG] Error en click de indicador: {e}")
            
            # --- PASO 2: SI NO HAY INDICADOR, BUSCAR SECCIÓN DE COMENTARIOS ---
            # LinkedIn puede mostrar comentarios inline sin que haya un contador visible
            if not should_have_comments:
                # Buscar la sección de comentarios por su estructura
                comments_section = item_locator.locator(".comments-comments-list, .social-details-social-activity").first
                if await comments_section.count() > 0:
                    should_have_comments = True
                    print(f"   [DEBUG] Sección de comentarios encontrada inline")
            
            # --- PASO 3: DETERMINAR CONTENEDOR (Modal vs Inline) ---
            modal = page.locator("div.artdeco-modal[role='dialog']").first
            container = item_locator
            
            # Esperar a que aparezca el modal o los comentarios inline
            try:
                await modal.wait_for(state="visible", timeout=4000)
                if await modal.is_visible():
                    container = modal
                    print(f"   [DEBUG] Modal de comentarios detectado")
                    
                    # IMPORTANTE: Esperar a que carguen los comentarios dentro del modal
                    # LinkedIn carga los comentarios de forma progresiva
                    await asyncio.sleep(2)
                    
                    # Hacer scroll dentro del modal para cargar más comentarios (lazy loading)
                    try:
                        await container.evaluate("el => el.scrollTop = el.scrollHeight / 2")
                        await asyncio.sleep(1)
                        await container.evaluate("el => el.scrollTop = el.scrollHeight")
                        await asyncio.sleep(1.5)
                        print(f"   [DEBUG] Scroll en modal para cargar comentarios lazy")
                    except Exception as e:
                        print(f"   [DEBUG] Error en scroll de modal: {e}")
                        
            except Exception as e:
                print(f"   [DEBUG] No se detectó modal, buscando comentarios inline: {e}")
            
            # Si no hay modal, buscar comentarios inline en el post
            if container == item_locator:
                # Scroll pequeño para forzar lazy loading inline
                try:
                    await item_locator.dispatch_event("wheel", {"deltaY": 300})
                    await asyncio.sleep(1)
                except: 
                    pass

            # --- PASO 4: BUSCAR ELEMENTOS DE COMENTARIOS ---
            # Lista completa de selectores actualizados para LinkedIn 2025/2026
            potential_selectors = [
                # Selectores más específicos primero (dentro de modal)
                "article.comments-comment-item",
                "li.comments-comment-item", 
                "div.comments-comment-item",
                
                # Contenedor de lista completa
                ".comments-comments-list > ul > li",
                ".comments-comments-list article",
                
                # Fallbacks genéricos
                ".social-details-social-activity article",
                "article[data-id]",
                ".feed-shared-comment",
            ]
            
            found_loc = None
            found_selector = None
            
            for selector in potential_selectors:
                loc = container.locator(selector)
                count = await loc.count()
                if count > 0:
                    found_loc = loc
                    found_selector = selector
                    print(f"   [DEBUG] ✓ Encontrados {count} elementos con selector: {selector}")
                    break
            
            # --- PASO 5: EXTRAER TEXTO DE COMENTARIOS ---
            if found_loc:
                count = await found_loc.count()
                take = min(count, max_qty)
                print(f"   [DEBUG] Extrayendo hasta {take} de {count} comentarios encontrados...")
                
                seen_comment_texts = set()  # Para evitar duplicados
                
                for i in range(count):  # Iterar sobre TODOS, no solo 'take'
                    if len(comments) >= max_qty:
                        break
                        
                    try:
                        comment_element = found_loc.nth(i)
                        
                        # Asegurarse de que el elemento esté visible
                        try:
                            await comment_element.scroll_into_view_if_needed(timeout=2000)
                            await asyncio.sleep(0.3)
                        except:
                            pass
                        
                        # Estrategia de extracción de texto por prioridad
                        text = None
                        
                        # 1. Buscar específicamente el contenedor del cuerpo del comentario
                        # Este es el selector más confiable para el TEXTO del comentario
                        text_selectors = [
                            ".comments-comment-item-content-body",  # Principal
                            ".comments-comment-item__main-content",
                            "span[dir='ltr']",  # Formato de texto de LinkedIn
                            ".feed-shared-inline-show-more-text",
                            ".comments-comment-item__inline-show-more-text",
                        ]
                        
                        for sel in text_selectors:
                            text_loc = comment_element.locator(sel).first
                            if await text_loc.count() > 0:
                                try:
                                    text = await text_loc.inner_text()
                                    if text and len(text.strip()) > 10:
                                        print(f"   [DEBUG]     Texto encontrado con selector: {sel}")
                                        break
                                except:
                                    continue
                        
                        # Fallback: tomar todo el texto del elemento (menos confiable)
                        if not text or len(text.strip()) <= 10:
                            try:
                                full_text = await comment_element.inner_text()
                                # Intentar extraer solo la parte del comentario, no botones
                                lines = full_text.split('\n')
                                # Filtrar líneas que parecen ser el comentario (más de 10 caracteres)
                                content_lines = [l.strip() for l in lines if len(l.strip()) > 10]
                                if content_lines:
                                    text = content_lines[0]  # Tomar la primera línea con contenido
                            except:
                                pass
                        
                        # Limpiar y validar
                        if text:
                            cleaned = text.replace('\n', ' ').strip()
                            
                            # Filtrar elementos no deseados
                            skip_patterns = [
                                'me gusta', 'like', 'comentar', 'compartir', 'reply', 'share',
                                'recomendar', 'recommend', 'ver más', 'see more', 'menos', 'less',
                                'responder', 'answer', 'útil', 'helpful'
                            ]
                            
                            should_skip = False
                            for pattern in skip_patterns:
                                if cleaned.lower() == pattern or len(cleaned) < 15:
                                    should_skip = True
                                    break
                            
                            # Verificar que no sea duplicado
                            comment_hash = cleaned[:50]  # Usar primeros 50 chars para hash
                            if should_skip or comment_hash in seen_comment_texts:
                                continue
                            
                            seen_comment_texts.add(comment_hash)
                            comments.append(cleaned)
                            print(f"   [DEBUG]   ✓ Comentario {len(comments)}: {cleaned[:100]}...")
                    
                    except Exception as e:
                        print(f"   [DEBUG]   ✗ Error extrayendo comentario {i+1}: {e}")
                        continue
                
                print(f"   [DEBUG] Total extraído: {len(comments)} comentarios únicos")
            
            # --- PASO 6: GUARDAR HTML PARA DEBUGGING SI FALLA ---
            if should_have_comments and len(comments) == 0:
                print(f"   [WARN] ❌ El post indica tener comentarios pero no se extrajeron")
                print(f"   [WARN] Guardando HTML para análisis...")
                
                debug_dir = os.path.join("output", "debug")
                os.makedirs(debug_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                debug_file = os.path.join(debug_dir, f"fail_{timestamp}_{random.randint(1000,9999)}.html")
                
                try:
                    html_content = await container.inner_html()
                    with open(debug_file, "w", encoding="utf-8") as f:
                        f.write(f"<!-- DUMP DEL CONTENEDOR DE COMENTARIOS -->\n")
                        f.write(f"<!-- Timestamp: {timestamp} -->\n")
                        f.write(f"<!-- Selectores probados: {', '.join(potential_selectors)} -->\n\n")
                        f.write(html_content)
                    print(f"   [DEBUG] HTML guardado en: {debug_file}")
                except Exception as e:
                    print(f"   [DEBUG] Error guardando HTML: {e}")
            
            # --- PASO 7: CERRAR MODAL SI EXISTE ---
            try:
                if await modal.first.is_visible():
                    await page.keyboard.press("Escape")
                    await asyncio.sleep(0.5)
                    print(f"   [DEBUG] Modal cerrado")
            except:
                pass
                
        except Exception as e:
            print(f"   [ERROR] Error crítico en _extract_comments: {e}")
            import traceback
            traceback.print_exc()
            
        return comments
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
                indicator_text = await comment_indicator.inner_text()
                print(f"   [DEBUG] Indicador Visual: {indicator_text}")
                try:
                    # Intento 1: Clic directo en el texto "X comentarios"
                    await comment_indicator.click(force=True, timeout=5000)
                    await asyncio.sleep(2)
                    print(f"   [DEBUG] Click exitoso en indicador de comentarios")
                except Exception as e:
                    print(f"   [DEBUG] Error en click de indicador: {e}")
                    pass
            
            # 2. INTENTO GENÉRICO: BOTÓN DE ACCIÓN "COMENTAR"
            # Si no clickeamos arriba o falló, buscamos el botón de acción principal
            # Suele tener aria-label="Comentar" o texto "Comentar"
            if not should_have_comments:
                action_btn = item_locator.locator("button").filter(has_text=re.compile(r"^(comentar|comment)$", re.IGNORECASE)).first
                if await action_btn.count() == 0:
                     action_btn = item_locator.locator("button[aria-label*='comentar'], button[aria-label*='comment']").first
                
                if await action_btn.count() > 0 and await action_btn.is_visible():
                    print(f"   [DEBUG] Click en botón Acción Comentar")
                    try:
                        await action_btn.click(force=True, timeout=5000)
                        await asyncio.sleep(2)
                    except Exception as e:
                        print(f"   [DEBUG] Error en click de botón comentar: {e}")
                        pass

            # 3. EXTRAER CONTENIDO
            # Ahora buscamos cualquier bloque que parezca un comentario
            # Clases comunes 2024/2025 + Fallbacks
            potential_blocks = [
                "article.comments-comment-entity",
                "article.comments-comment-item",
                "div.comments-comment-item",
                "div.feed-shared-comment-item",
                "li.comments-comments-list__comment-item",
                "div.comments-comments-list__comment-item-content",
                "article[data-id]", # Generic article in comment section
                "div.comments-post-meta__profile-info-wrapper", # Inside comment header
                ".comments-comment-item__main-content", # Nuevo selector
                ".comments-comment-texteditor", # Para ver el input de comentarios
            ]
            
            # Determinar contenedor (Modal vs Inline)
            modal = page.locator("div.artdeco-modal[role='dialog']")
            container = item_locator
            if await modal.is_visible():
                container = modal
                print(f"   [DEBUG] Modal de comentarios abierto")
            else:
                print(f"   [DEBUG] Buscando comentarios inline")
            
            # PEQUEÑO SCROLL PARA FORZAR RENDER (Lazy Loading)
            try:
                await container.dispatch_event("wheel", {"deltaY": 500})
                await asyncio.sleep(1.5)
            except: pass

            found_loc = None
            for sel in potential_blocks:
                loc = container.locator(sel)
                count = await loc.count()
                if count > 0:
                    found_loc = loc
                    print(f"   [DEBUG] Found {count} comments using selector: {sel}")
                    break
            
            if found_loc:
                count = await found_loc.count()
                take = min(count, max_qty)
                print(f"   [DEBUG] Extrayendo {take} de {count} comentarios")
                for i in range(take):
                    c = found_loc.nth(i)
                    # Extraer texto: Priorizamos el span con dirección de texto
                    text_loc = c.locator("span[dir='ltr']").first
                    if await text_loc.count() == 0:
                        text_loc = c.locator("div.feed-shared-text, div.update-components-text, .comments-comment-item__main-content").first
                        
                    if await text_loc.count() == 0:
                         # Intento final: tomar todo el texto del item
                         text_loc = c
                    
                    if await text_loc.count() > 0:
                        t = await text_loc.inner_text()
                        cleaned = t.replace('\n', ' ').strip()
                        if cleaned and len(cleaned) > 5:
                            comments.append(cleaned)
                            print(f"   [DEBUG] Comentario {i+1}: {cleaned[:80]}...")
            
            # --- DEBUGGING FINAL: GUARDAR HTML SI FALLA ---
            if should_have_comments and len(comments) == 0:
                print(f"   [WARN] El post decía tener comentarios pero no se extrajeron. (Posible selector desactualizado)")
                debug_file = f"output/debug_fail_{random.randint(1000,9999)}.html"
                os.makedirs('output', exist_ok=True)
                html_content = await container.inner_html()
                with open(debug_file, "w", encoding="utf-8") as f:
                     f.write(f"<!-- DUMP DEL POST -->\n{html_content}")
                print(f"   [DEBUG] HTML guardado en {debug_file} para análisis")

            # Limpieza (Cerrar modal)
            if await modal.is_visible():
                await page.keyboard.press("Escape")
                await asyncio.sleep(0.5)
                
        except Exception as e:
            print(f"   [Error Extracción Comentarios]: {e}")
            import traceback
            traceback.print_exc()
            
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
                # Búsqueda exacta como pide el usuario
                encoded_query = query.replace(" ", "%20")
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

                print(f"[{self.__class__.__name__}] Debug: URL reached -> {page.url}")
                await page.screenshot(path="linkedin_search_debug.jpg")
                
                html_content = await page.content()
                with open("debug.html", "w", encoding="utf-8") as f:
                    f.write(html_content)

                # --- BUCLE PRINCIPAL DE EXTRACCIÓN ---
                no_new_data_counter = 0
                max_retries_no_data = 10  # Reducido de 30 a 10 para ser más rápido
                
                print(f"[{self.__class__.__name__}] Iniciando extracción. Meta: {limit} posts.")
                
                while len(results) < limit:
                    # Buscar items en el DOM actual
                    # Actualizamos selectores según la estructura obtenida
                    # [data-view-name="feed-full-update"] es el nuevo contenedor principal
                    post_items = await page.locator(".search-results-container .artdeco-card, div.feed-shared-update-v2, div[data-view-name='feed-full-update']").all()

                    new_in_this_pass = 0
                    for item in post_items:
                        if len(results) >= limit:
                            break

                        try:
                            # Extraer URN del contenedor o enlaces internos
                            post_urn = await item.get_attribute("data-urn")
                            if not post_urn:
                                # Intentar extraer URN de enlaces internos si no lo tiene en la raíz
                                urn_links = await item.locator("a[href*='urn:li:activity']").all()
                                if urn_links:
                                    href = await urn_links[0].get_attribute("href")
                                    import re
                                    match = re.search(r"urn:li:activity:\d+", href)
                                    if match:
                                        post_urn = match.group(0)

                            if post_urn and post_urn in seen_hashes:
                                continue  # Ya extraído

                            # Extraer texto principal
                            post_text_loc = item.locator(".feed-shared-update-v2__description-wrapper, .update-components-text, span.break-words, span.update-components-text, [data-view-name='feed-commentary']").first
                            post_text = ""
                            if await post_text_loc.count() > 0:
                                post_text = await post_text_loc.inner_text()
                            else:
                                # Fallback si no encuentra selector exacto
                                post_text = (await item.inner_text()).split('\n')[0] 

                            if not post_text.strip() or len(post_text.strip()) < 10:
                                continue

                            # Marcar visto
                            seen_hashes.add(post_urn if post_urn else hash(post_text[:100])) 
                            
                            # Expandir 'ver más' (sin delay largo)
                            try:
                                see_more = item.locator("button.feed-shared-inline-show-more-text__see-more-less-toggle").first
                                if await see_more.is_visible():
                                    await see_more.click()
                                    await asyncio.sleep(0.3)
                            except: pass
                            
                            # Re-leer texto completo después de posible clic en "ver más"
                            if await post_text_loc.count() > 0:
                                post_text = await post_text_loc.inner_text()
                            
                            # Autor
                            author = "Desconocido"
                            author_el = item.locator(".update-components-actor__name span[aria-hidden='true'], .update-components-actor__title span[aria-hidden='true'], span.update-components-actor__name, span.feed-shared-actor__name").first
                            if await author_el.count() > 0:
                                author = await author_el.inner_text()

                            # Comentarios (OPCIONAL)
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
                            
                    # Verificar progreso después de procesar todos los posts en pantalla
                    if len(results) >= limit:
                        print(f"   [!] Meta alcanzada ({len(results)}/{limit}).")
                        break
                        
                    if new_in_this_pass == 0:
                        no_new_data_counter += 1
                        print(f"   ...scrolleando (Intento {no_new_data_counter}/{max_retries_no_data} sin nuevos posts)...")
                        
                        # Aggressive scrolling to force load
                        try:
                            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            await asyncio.sleep(1)
                            await page.keyboard.press("PageDown")
                            await asyncio.sleep(1)
                        except: pass
                        
                        if no_new_data_counter >= max_retries_no_data:
                            print("   [!] No aparecen más resultados nuevos. Terminando.")
                            break
                    else:
                        no_new_data_counter = 0
                        print(f"   ...scrolleando para buscar más...")
                        # Scroll para cargar siguientes resultados
                        try:
                            await page.evaluate("window.scrollBy(0, 800)")
                            await asyncio.sleep(0.5)
                        except: pass

            except Exception as e:
                print(f"Error crítico en scraper: {e}")
            finally:
                print("Cerrando navegador automáticamente...")
                await context.close()
                await browser.close()
                
        return results
