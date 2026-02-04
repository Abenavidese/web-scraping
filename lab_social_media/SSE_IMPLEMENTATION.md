# Implementación de Server-Sent Events (SSE) para Progreso en Tiempo Real

## Descripción General
Se implementó un sistema de streaming en tiempo real utilizando Server-Sent Events (SSE) para mostrar el progreso real de los scrapers en el modal de análisis.

## Arquitectura

### Backend (Flask API)

#### 1. **progress_tracker.py** - Sistema de Eventos
- **ProgressTracker**: Clase thread-safe que gestiona eventos por sesión
- Métodos principales:
  - `emit(session_id, event_type, data)`: Emite un evento
  - `subscribe(session_id, callback)`: Registra callbacks para una sesión
  - `clear_session(session_id)`: Limpia eventos de una sesión

#### 2. **app.py** - Endpoints SSE

##### POST `/api/scrape/stream`
- Inicia el scraping en un thread de fondo
- Retorna `session_id` único para tracking
- Crea una cola de eventos para la sesión

##### GET `/api/scrape/events/<session_id>`
- Endpoint SSE que transmite eventos en tiempo real
- Formato: `data: {json}\n\n`
- Envía heartbeats cada segundo si no hay eventos

#### 3. **scraper_manager.py** - Emisión de Eventos

Eventos emitidos durante el scraping:

1. **launch**: Cuando se lanzan todos los scrapers
   ```json
   {"type": "launch", "networks": ["instagram", "x"]}
   ```

2. **network_start**: Cuando inicia un scraper específico
   ```json
   {"type": "network_start", "network": "instagram", "name": "Instagram Scraper", "pid": 12345}
   ```

3. **network_complete**: Cuando termina un scraper
   ```json
   {"type": "network_complete", "network": "instagram", "status": "success", "execution_time": 45.2}
   ```

4. **import_start**: Cuando inicia la importación de datos
   ```json
   {"type": "import_start", "network": "instagram"}
   ```

5. **import_done**: Cuando termina la importación
   ```json
   {"type": "import_done", "network": "instagram"}
   ```

6. **complete**: Cuando todo el proceso termina
   ```json
   {"type": "complete", "result": {...}}
   ```

7. **error**: Si ocurre un error
   ```json
   {"type": "error", "error": "Mensaje de error"}
   ```

### Frontend (React/Next.js)

#### nueva-consulta/page.tsx - Conexión SSE

**Flujo de conexión:**

1. Usuario hace clic en "Iniciar Análisis"
2. Se hace POST a `/api/scrape/stream` para obtener `session_id`
3. Se crea `EventSource` conectado a `/api/scrape/events/{session_id}`
4. Se escuchan eventos y se actualiza el estado del modal

**Manejo de eventos:**

```typescript
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data)
  
  switch (data.type) {
    case 'start': // Marca request como completo
    case 'launch': // Inicia primera red
    case 'network_start': // Marca red como running
    case 'network_complete': // Marca red como done/error
    case 'import_start': // Inicia procesamiento
    case 'import_done': // Incrementa progreso
    case 'complete': // Redirige a resultados
    case 'error': // Muestra error
  }
}
```

## Ventajas de SSE vs Polling

✅ **Menor latencia**: Eventos en tiempo real sin esperas
✅ **Menos recursos**: Una conexión persistente vs múltiples requests
✅ **Orden garantizado**: Los eventos llegan en secuencia
✅ **Reconexión automática**: EventSource reconecta automáticamente
✅ **Simple**: No requiere WebSockets, funciona sobre HTTP

## Flujo Completo

```
Usuario → Inicia Análisis
    ↓
Frontend → POST /api/scrape/stream
    ↓
Backend → Crea session_id y thread de scraping
    ↓
Backend → Retorna session_id
    ↓
Frontend → EventSource(/api/scrape/events/session_id)
    ↓
Backend → Ejecuta scrapers en paralelo
    ↓
Backend → Emite eventos: launch → network_start → network_complete
    ↓
Backend → Importa datos y emite: import_start → import_done
    ↓
Backend → Emite complete
    ↓
Frontend → Recibe complete y redirige a /resultados
```

## Testing

Para probar la implementación:

1. Iniciar backend: `python api/app.py`
2. Iniciar frontend: `cd front && npm run dev`
3. Ir a "Nueva Consulta"
4. Seleccionar redes y query
5. Click "Iniciar Análisis"
6. Observar modal actualizándose con progreso real
7. Verificar logs del backend mostrando ejecución paralela

## Logs del Backend

Los logs muestran claramente el progreso:
```
🚀 Launching parallel scrapers...
   ▶️ Started Instagram Scraper (PID: 12345)
   ▶️ Started X Scraper (PID: 12346)
   ✅ Finished Instagram Scraper in 45.2s
   ✅ Finished X Scraper in 67.3s
📥 Importing data for instagram...
📥 Importing data for x...
```

Estos logs ahora se reflejan en tiempo real en el frontend.

## Manejo de Errores

- **Conexión perdida**: EventSource.onerror reconecta automáticamente
- **Sesión inválida**: SSE endpoint retorna error y cierra
- **Error de scraper**: Se emite evento 'error' y se marca red como error
- **Timeout**: Heartbeats previenen timeout de conexión

## Limpieza de Recursos

- Sesiones se limpian al completar o en error
- EventSource se cierra al recibir 'complete' o 'error'
- Threads de scraping son daemon para evitar bloqueos
