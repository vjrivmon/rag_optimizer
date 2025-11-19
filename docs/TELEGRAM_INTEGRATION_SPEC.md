# 📱 ESPECIFICACIÓN TÉCNICA: INTEGRACIÓN TELEGRAM + PERSISTENCIA CROSS-SESIÓN

---

## 📋 METADATA DEL DOCUMENTO

| Campo | Valor |
|-------|-------|
| **Título** | Especificación Técnica de Integración Telegram para Chatbot DNI con Persistencia Cross-Sesión |
| **Proyecto** | RAG Auto-Optimizer v4.0 - Chatbot DNI |
| **Autor** | Vicente |
| **Institución** | Universitat Politècnica de València |
| **Contexto Académico** | Trabajo Final de Máster (TFG) |
| **Versión Documento** | 1.0 |
| **Fecha Creación** | 2025-11-19 |
| **Última Actualización** | 2025-11-19 |
| **Estado** | 🚧 DRAFT - Fase de Diseño |
| **Sistema Base** | Chatbot DNI v3.3 (Web) |
| **Sistema Objetivo** | Chatbot DNI v4.0 (Telegram + WhatsApp) |

---

## 🎯 RESUMEN EJECUTIVO

### Objetivo del Proyecto

Extender el **Chatbot DNI v3.3** (actualmente web-only con sesiones efímeras) hacia plataformas de mensajería instantánea (**Telegram** primero, **WhatsApp** después) con **persistencia cross-sesión de largo plazo**.

### Requisito Crítico de Negocio

> **Caso de uso objetivo:**
> Un usuario de DNI habla con el bot un **lunes** preguntando sobre "Desayunos Solidarios".
> Vuelve el **viernes** y pregunta: *"¿A qué hora era?"*
> El bot debe **recordar automáticamente** que la conversación previa era sobre Desayunos y responder con el horario correcto (8:00 AM).

Este requisito es **imposible** en la versión web actual (sesión = pestaña del navegador), pero **crítico** para mensajería donde las conversaciones son persistentes por naturaleza.

### Alcance

**IN SCOPE:**
- ✅ Integración completa con Telegram Bot API
- ✅ Persistencia de conversaciones en PostgreSQL
- ✅ Gestión inteligente de contexto cross-sesión
- ✅ Context decay exponencial (3 días half-life)
- ✅ API REST para gestión de usuarios y conversaciones
- ✅ GDPR compliance (consentimiento, data deletion)
- ✅ Deployment con Docker Compose
- ✅ Testing completo (unit, integration, e2e)

**OUT OF SCOPE (futuro):**
- ❌ Integración WhatsApp (FASE 10, posterior a TFG)
- ❌ Multimodalidad (imágenes, audio, video)
- ❌ Multi-idioma (valenciano, inglés)
- ❌ Fine-tuning específico de gemma2 para DNI
- ❌ Escalabilidad horizontal (Kubernetes)

### Timeline Académico

| Fase | Duración | Actividades Principales |
|------|----------|-------------------------|
| **Mes 1** | Nov 2025 | Diseño técnico + PostgreSQL schema + Service layer |
| **Mes 2** | Dic 2025 | PersistentContextManager + Telegram bot + API REST |
| **Mes 3** | Ene 2026 | Testing + Deployment + Documentación TFG |

**Deadline TFG:** Enero 2026

---

## 📚 TABLA DE CONTENIDOS

1. [Análisis de Requisitos](#1-análisis-de-requisitos)
   - 1.1 Diferencias Web vs Telegram
   - 1.2 Casos de Uso Cross-Sesión
   - 1.3 Requisitos Funcionales
   - 1.4 Requisitos No Funcionales
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
   - 2.1 Vista General
   - 2.2 Comparación: Arquitectura Actual vs Propuesta
   - 2.3 Flujo de Datos End-to-End
3. Diseño de Base de Datos (PostgreSQL)
4. Gestión de Contexto Persistente
5. Capa de Servicios
6. Integración Telegram Bot
7. API REST
8. Deployment e Infraestructura
9. Privacidad y GDPR
10. Estrategia de Testing
11. Gestión de Riesgos
12. Timeline Detallado
13. **ANEXO: Diagramas Mermaid Detallados** ✨
    - 13.1 Arquitectura del Sistema (C4 Container)
    - 13.2 Diagrama Entidad-Relación (Mermaid)
    - 13.3 Flujos de Datos Completos (Registro, Mensaje, GDPR)
    - 13.4 Diagramas de Estado (Conversaciones, Usuarios, Procesamiento)
    - 13.5 Arquitectura de Deployment (Docker Compose)
    - 13.6 Diagrama de Decisión: Query Enrichment
    - 13.7 Diagrama de Componentes RAG Pipeline
    - 13.8 Timeline Visual del Proyecto (Gantt)
14. Conclusiones del Diseño

---

## 1. ANÁLISIS DE REQUISITOS

### 1.1 Diferencias Web vs Telegram

#### Chatbot Web Actual (v3.3)

| Aspecto | Comportamiento | Implicación |
|---------|----------------|-------------|
| **Sesión** | Ligada a pestaña del navegador | Cerrar pestaña = perder todo el contexto |
| **Persistencia** | ❌ Cero (solo en memoria) | Refresh = conversación nueva |
| **Identidad** | ❌ Anónimo (sin login) | No hay concepto de "usuario" |
| **Contexto** | Ventana deslizante 4 turnos | Solo durante sesión activa |
| **Storage** | JavaScript localStorage (opcional) | No se usa actualmente |
| **Infraestructura** | FastAPI + WebSocket | Stateless backend |

**Ventajas:**
- ✅ Simple y rápido de implementar
- ✅ No requiere DB (bajo costo infraestructura)
- ✅ GDPR friendly (no almacena datos personales)
- ✅ Ideal para sesiones cortas (1-5 preguntas)

**Limitaciones:**
- ❌ Imposible recordar entre sesiones
- ❌ No hay historial de conversaciones
- ❌ No puede aprender de interacciones previas
- ❌ Usuario pierde contexto si cambia de dispositivo

#### Chatbot Telegram Objetivo (v4.0)

| Aspecto | Comportamiento | Implicación |
|---------|----------------|-------------|
| **Sesión** | ❌ NO existe concepto de "sesión" | Conversación continua indefinida |
| **Persistencia** | ✅ Obligatoria (días/semanas/meses) | DB requerida |
| **Identidad** | ✅ telegram_user_id único | Usuario rastreable |
| **Contexto** | Cross-sesión con decay exponencial | Recordar conversaciones antiguas |
| **Storage** | PostgreSQL (usuarios, mensajes, contexto) | Infraestructura más compleja |
| **Infraestructura** | FastAPI + python-telegram-bot + DB | Stateful backend |

**Ventajas:**
- ✅ Experiencia conversacional natural (como hablar con humano)
- ✅ Recordar preferencias y contexto histórico
- ✅ Posibilidad de analytics y mejora continua
- ✅ Multi-dispositivo (mismo telegram_user_id)

**Desafíos:**
- ❌ Complejidad técnica mayor (DB, migrations, backups)
- ❌ Responsabilidad GDPR (datos personales)
- ❌ Gestión de contexto antiguo (evitar confusión)
- ❌ Costos de infraestructura (PostgreSQL, almacenamiento)

### 1.2 Casos de Uso Cross-Sesión

#### Caso de Uso 1: Contexto Temporal Simple

**Scenario:**
- **Lunes 10:00:** Usuario pregunta "¿Cuándo son los desayunos solidarios?"
- Bot responde: "Los Desayunos Solidarios son todos los sábados a las 8:00 AM..."
- **Viernes 18:00:** Usuario pregunta "¿A qué hora era?"

**Comportamiento Esperado:**
1. Sistema detecta pregunta ambigua ("¿A qué hora era?")
2. Consulta contexto histórico → encuentra "Desayunos Solidarios" (lunes)
3. Calcula relevancia con decay exponencial (5 días atrás)
4. Enriquece query: `[Contexto: Desayunos Solidarios] ¿A qué hora era?`
5. RAG devuelve: "Los Desayunos Solidarios son a las 8:00 AM..."

**Métricas de Éxito:**
- ✅ Context retrieval accuracy > 80%
- ✅ Response time < 3s (incluyendo DB lookup)
- ✅ Confianza del usuario (no necesita repetir contexto)

#### Caso de Uso 2: Multi-Proyecto con Cambio de Tema

**Scenario:**
- **Día 1:** Conversación sobre "Desayunos Solidarios" (5 preguntas)
- **Día 3:** Usuario pregunta sobre "Refuerzo Escolar COLES" (4 preguntas)
- **Día 5:** Usuario pregunta "¿Dónde quedamos para los desayunos?"

**Comportamiento Esperado:**
1. Sistema mantiene 2 contextos separados: Desayunos (día 1) + COLES (día 3)
2. Pregunta menciona explícitamente "desayunos" → prioriza contexto día 1
3. Aplica decay: día 1 (4 días) vs día 3 (2 días) → pesa ambos pero prioriza mención explícita
4. Responde con punto de encuentro de Desayunos: "Carrer de Sagunt, 177"

**Métricas de Éxito:**
- ✅ Correcta identificación del proyecto mencionado (100%)
- ✅ No mezclar información de proyectos diferentes
- ✅ Decay adecuado (más reciente = más peso, pero mención explícita gana)

#### Caso de Uso 3: Contexto Muy Antiguo (Edge Case)

**Scenario:**
- **15 días atrás:** Conversación sobre "Charlas con Abuelitos"
- **Hoy:** Usuario pregunta "¿Cuándo es lo de la residencia?"

**Comportamiento Esperado:**
1. Sistema busca contexto antiguo (15 días)
2. Decay exponencial (half-life 3 días) → peso muy bajo (~0.03)
3. Si confidence del match < 0.4 → pedir aclaración
4. Respuesta: "¿Te refieres a las Charlas con Abuelitos en la residencia L'Acollida? Hace tiempo hablamos de eso. Son los domingos de 10:30-12:30."

**Métricas de Éxito:**
- ✅ Reconoce contexto antiguo pero avisa al usuario
- ✅ No da respuesta incorrecta por decay excesivo
- ✅ Ofrece confirmación antes de asumir contexto

#### Caso de Uso 4: Nuevo Usuario (Sin Historial)

**Scenario:**
- Usuario nuevo abre conversación con el bot por primera vez
- Pregunta: "¿Qué es DNI?"

**Comportamiento Esperado:**
1. Sistema detecta `telegram_user_id` no existe en DB
2. Crea registro en tabla `users` con timestamp
3. No hay contexto previo → comportamiento idéntico a chatbot web actual
4. Responde con información general de DNI
5. Guarda mensaje en tabla `messages` para futuras referencias

**Métricas de Éxito:**
- ✅ Response time < 2s (sin overhead de contexto histórico)
- ✅ Usuario creado correctamente en DB
- ✅ Primera conversación registrada

### 1.3 Requisitos Funcionales

#### RF-01: Autenticación y Registro de Usuarios

**Prioridad:** ALTA
**Descripción:** El sistema debe identificar unívocamente a cada usuario de Telegram mediante `telegram_user_id` y registrarlo automáticamente en la base de datos la primera vez que interactúa.

**Criterios de Aceptación:**
- ✅ Cada `telegram_user_id` único corresponde a exactamente 1 registro en tabla `users`
- ✅ Campos obligatorios: `telegram_user_id`, `first_name`, `created_at`
- ✅ Campos opcionales: `last_name`, `username`, `language_code`
- ✅ Auto-registro transparente (sin comando `/start` obligatorio)
- ✅ Actualización de `last_interaction_at` en cada mensaje

#### RF-02: Persistencia de Mensajes

**Prioridad:** ALTA
**Descripción:** Todos los mensajes enviados y recibidos deben almacenarse en PostgreSQL con metadata completa.

**Criterios de Aceptación:**
- ✅ Tabla `messages` con campos: `id`, `conversation_id`, `role` (user/assistant/system), `content`, `created_at`
- ✅ Metadata adicional: `telegram_message_id`, `confidence_score`, `retrieval_sources`
- ✅ Almacenamiento de RAG metadata: chunks usados, scores, latencia
- ✅ Soporte para mensajes largos (hasta 4096 chars Telegram limit)

#### RF-03: Gestión de Conversaciones

**Prioridad:** ALTA
**Descripción:** Agrupar mensajes relacionados en conversaciones lógicas con detección automática de cambios de tema.

**Criterios de Aceptación:**
- ✅ Tabla `conversations` con `id`, `user_id`, `project_context` (enum), `created_at`, `updated_at`
- ✅ Nueva conversación si: (a) >7 días de inactividad, o (b) cambio de proyecto detectado
- ✅ Máximo 1 conversación activa por usuario simultáneamente
- ✅ Historico completo de conversaciones archivadas

#### RF-04: Context Tracking Cross-Sesión

**Prioridad:** CRÍTICA
**Descripción:** El sistema debe recordar y recuperar contexto relevante de conversaciones previas con decay temporal exponencial.

**Criterios de Aceptación:**
- ✅ Algoritmo decay: `weight = exp(-λ * days_ago)` con λ = ln(2)/3 (half-life 3 días)
- ✅ Retrieval de contexto: buscar en últimos 30 días, ordenar por relevancia * decay
- ✅ Detección de proyectos DNI en contexto histórico (6 proyectos)
- ✅ Query enrichment automático si pregunta ambigua + contexto relevante encontrado
- ✅ Snapshot de contexto cada 5 mensajes para optimizar queries

#### RF-05: Comandos Telegram Básicos

**Prioridad:** MEDIA
**Descripción:** Implementar comandos estándar de Telegram para gestión de conversación.

**Criterios de Aceptación:**
- ✅ `/start` - Mensaje de bienvenida + registro de usuario
- ✅ `/help` - Guía de uso del bot
- ✅ `/reset` - Borrar contexto actual (inicia conversación nueva)
- ✅ `/history` - Mostrar últimas 5 conversaciones
- ✅ `/delete_data` - Borrar TODOS los datos del usuario (GDPR)
- ✅ `/feedback` - Sistema de feedback (👍👎)

#### RF-06: Sugerencias de Preguntas Contextuales

**Prioridad:** BAJA
**Descripción:** Ofrecer 3 preguntas sugeridas relevantes al contexto actual usando inline keyboard.

**Criterios de Aceptación:**
- ✅ Reutilizar `QuestionSuggester` actual (69 preguntas)
- ✅ Inline keyboard con 3 botones (preguntas)
- ✅ Priorizar por proyecto detectado en contexto
- ✅ No mostrar si conversación >10 mensajes (molesto)

#### RF-07: Exportación de Conversaciones

**Prioridad:** BAJA
**Descripción:** Permitir al usuario exportar su historial de conversaciones en formato TXT/JSON.

**Criterios de Aceptación:**
- ✅ Comando `/export [format]` (txt o json)
- ✅ Formato TXT: Igual al actual del chatbot web
- ✅ Formato JSON: Metadata completa (timestamps, confidence, sources)
- ✅ Envío como archivo adjunto por Telegram (no mensaje largo)

### 1.4 Requisitos No Funcionales

#### RNF-01: Performance

| Métrica | Target | Crítico |
|---------|--------|---------|
| **Response time** (consulta simple) | < 2s | < 5s |
| **Response time** (con context lookup) | < 3s | < 6s |
| **DB query time** (context retrieval) | < 300ms | < 1s |
| **Throughput** | 10 usuarios concurrentes | 5 min |

**Justificación:** Telegram es síncrono (usuario espera respuesta inmediata), a diferencia de email.

#### RNF-02: Escalabilidad

- ✅ Soportar hasta **100 usuarios registrados** (MVP)
- ✅ Soportar hasta **1,000 mensajes/día** (asumiendo 10 msg/usuario/día promedio)
- ✅ DB growth: ~1 GB/año (estimado: 365k mensajes * 2 KB/mensaje promedio)

**Límites explícitos (fuera de MVP):**
- ❌ No optimizado para >500 usuarios concurrentes
- ❌ No soporta sharding de DB (single PostgreSQL instance)

#### RNF-03: Disponibilidad

- ✅ **Uptime objetivo:** 95% (permite ~36 horas downtime/mes)
- ✅ **Horario crítico:** Viernes-Sábado 6:00-12:00 (Desayunos Solidarios)
- ✅ Graceful degradation: Si DB cae → fallback a modo "stateless" (sin contexto histórico)

**No se requiere:**
- ❌ Alta disponibilidad 99.9% (no es servicio crítico)
- ❌ Disaster recovery automático
- ❌ Multi-region deployment

#### RNF-04: Seguridad y Privacidad

- ✅ **GDPR compliance:**
  - Consentimiento explícito al usar `/start` (mensaje de aviso)
  - Derecho al olvido con `/delete_data`
  - Data retention: 90 días (auto-borrado de conversaciones antiguas)
- ✅ **Encryption at rest:** PostgreSQL con `pgcrypto` para campos sensibles
- ✅ **Encryption in transit:** HTTPS para API, TLS para DB connections
- ✅ **Access control:** Telegram user_id como único identificador (no emails, no teléfonos)
- ✅ **Logging:** No loggear contenido de mensajes (solo metadata)

#### RNF-05: Mantenibilidad

- ✅ **Código documentado:** Docstrings en 100% de funciones públicas
- ✅ **Tests coverage:** >85% (unit + integration)
- ✅ **Type hints:** Python 3.12+ con mypy strict
- ✅ **Migrations:** Alembic para DB schema versioning
- ✅ **Monitoring:** Logs estructurados (JSON) + métricas básicas (Prometheus opcional)

#### RNF-06: Compatibilidad

- ✅ **Python:** 3.12+ (required)
- ✅ **PostgreSQL:** 14+ (required)
- ✅ **Telegram Bot API:** Latest stable (python-telegram-bot v20+)
- ✅ **Ollama server:** Compatible con API actual (gemma2:27b)
- ✅ **ChromaDB:** Reutilizar vector store actual (sin cambios)

---

## 2. ARQUITECTURA DEL SISTEMA

### 2.1 Vista General

```
┌─────────────────────────────────────────────────────────────────────┐
│                     USUARIO (Telegram Mobile App)                    │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                   ┌─────────▼─────────┐
                   │  Telegram Server   │ (API pública de Telegram)
                   │  (Bot API)         │
                   └─────────┬─────────┘
                             │ HTTPS Webhook (opcional) o Long Polling
                             │
          ┌──────────────────▼──────────────────┐
          │   python-telegram-bot Library       │
          │   • Handlers (CommandHandler, etc)  │
          │   • Update dispatcher               │
          │   • Error handling                  │
          └──────────────────┬──────────────────┘
                             │
          ┌──────────────────▼──────────────────────────────┐
          │         FastAPI Backend (Extended)              │
          │  ┌────────────────────────────────────────────┐ │
          │  │  TelegramBotService (NEW)                  │ │
          │  │  • Process incoming messages               │ │
          │  │  • Call ConversationalRAG                  │ │
          │  │  • Format responses for Telegram           │ │
          │  └──────────────────┬─────────────────────────┘ │
          │                     │                            │
          │  ┌──────────────────▼─────────────────────────┐ │
          │  │  PersistentContextManager (NEW)            │ │
          │  │  • Load context from DB                    │ │
          │  │  • Decay calculation                       │ │
          │  │  • Save context snapshots                  │ │
          │  └──────────────────┬─────────────────────────┘ │
          │                     │                            │
          │  ┌──────────────────▼─────────────────────────┐ │
          │  │  ConversationalRAG (REUSED)                │ │
          │  │  • ContextTracker (reused)                 │ │
          │  │  • Query enrichment                        │ │
          │  │  • question_id=0 forced                    │ │
          │  └──────────────────┬─────────────────────────┘ │
          │                     │                            │
          │  ┌──────────────────▼─────────────────────────┐ │
          │  │  EnhancedRAGEngineNew (REUSED)             │ │
          │  │  • Confidence dinámico                     │ │
          │  │  • Cross-encoder reranking                 │ │
          │  └──────────────────┬─────────────────────────┘ │
          └─────────────────────┼──────────────────────────┘
                                │
          ┌─────────────────────┴──────────────────────────┐
          │                                                 │
┌─────────▼──────────┐                          ┌──────────▼────────┐
│  PostgreSQL DB      │                          │  ChromaDB         │
│  • users            │                          │  (Vector Store)   │
│  • conversations    │                          │  • 263 chunks     │
│  • messages         │                          │  • REUSED         │
│  • context_snapshots│                          └───────────────────┘
│  • feedback         │
│  • (NEW TABLES)     │
└─────────┬──────────┘
          │
┌─────────▼──────────┐
│  Ollama UPV Server  │
│  gemma2:27b         │
│  (REUSED)           │
└─────────────────────┘
```

### 2.2 Comparación: Arquitectura Actual vs Propuesta

#### Stack Tecnológico

| Componente | Web Actual (v3.3) | Telegram Propuesto (v4.0) | Cambio |
|------------|-------------------|---------------------------|--------|
| **Frontend** | HTML + CSS + JS | Telegram App | Reemplazado |
| **Backend** | FastAPI + WebSocket | FastAPI + python-telegram-bot | Extendido |
| **Persistencia** | ❌ Ninguna (RAM) | ✅ PostgreSQL | **NUEVO** |
| **RAG Engine** | ConversationalRAG + EnhancedRAGEngineNew | Mismo | Reutilizado |
| **Vector Store** | ChromaDB (263 chunks) | Mismo | Reutilizado |
| **LLM** | gemma2:27b (Ollama UPV) | Mismo | Reutilizado |
| **Context Tracking** | ContextTracker (4 turnos) | PersistentContextManager (30 días) | **NUEVO** |
| **Deployment** | Python script | Docker Compose | Mejorado |

#### Flujo de Mensajes

**Web Actual (v3.3):**
```
User (Browser)
  → WebSocket
  → FastAPI endpoint
  → ConversationalRAG (in-memory context)
  → EnhancedRAGEngineNew
  → ChromaDB + Ollama
  → Response
  → WebSocket
  → User (Browser)
```

**Telegram Propuesto (v4.0):**
```
User (Telegram App)
  → Telegram Server
  → python-telegram-bot (long polling/webhook)
  → TelegramBotService
  → PersistentContextManager (DB lookup)
  → ConversationalRAG (enriched with DB context)
  → EnhancedRAGEngineNew
  → ChromaDB + Ollama
  → Response
  → PersistentContextManager (save to DB)
  → TelegramBotService
  → python-telegram-bot
  → Telegram Server
  → User (Telegram App)
```

**Diferencias clave:**
1. ✅ **DB lookup antes** de llamar a RAG (cargar contexto histórico)
2. ✅ **DB save después** de generar respuesta (guardar mensaje + contexto)
3. ✅ **No WebSocket** (Telegram usa polling o webhook)
4. ✅ **User identification** (telegram_user_id vs sesión anónima)

### 2.3 Flujo de Datos End-to-End

#### Flujo 1: Primer Mensaje de Usuario Nuevo

```mermaid
sequenceDiagram
    participant U as Usuario (Telegram)
    participant T as Telegram Server
    participant B as TelegramBotService
    participant DB as PostgreSQL
    participant P as PersistentContextManager
    participant R as ConversationalRAG
    participant E as EnhancedRAGEngineNew
    participant C as ChromaDB
    participant O as Ollama (gemma2)

    U->>T: "¿Qué es DNI?"
    T->>B: Update{telegram_user_id=123, text="¿Qué es DNI?"}

    B->>DB: SELECT * FROM users WHERE telegram_user_id=123
    DB-->>B: ❌ No existe

    B->>DB: INSERT INTO users (telegram_user_id, first_name, created_at)
    DB-->>B: ✅ User created (id=1)

    B->>DB: INSERT INTO conversations (user_id=1, project_context=NULL)
    DB-->>B: ✅ Conversation created (id=1)

    B->>P: load_context(user_id=1)
    P->>DB: SELECT * FROM context_snapshots WHERE user_id=1
    DB-->>P: [] (vacío)
    P-->>B: context=[] (sin historial)

    B->>R: generate_response(query="¿Qué es DNI?", context=[])
    R->>E: retrieve_with_rag(query="¿Qué es DNI?")
    E->>C: hybrid_search(query="¿Qué es DNI?", k=10)
    C-->>E: [chunk1, chunk2, ...] (10 chunks)
    E->>O: generate(prompt="...", chunks=[...])
    O-->>E: "DNI (Damos Nuestra Ilusión) es una asociación..."
    E-->>R: {answer, confidence=0.87, sources}
    R-->>B: {answer, confidence, sources}

    B->>DB: INSERT INTO messages (conversation_id=1, role='user', content='¿Qué es DNI?')
    B->>DB: INSERT INTO messages (conversation_id=1, role='assistant', content='...', confidence_score=0.87)

    B->>P: save_context_snapshot(user_id=1, detected_project='General')
    P->>DB: INSERT INTO context_snapshots (user_id=1, project_context='General', message_count=1)

    B->>T: sendMessage(chat_id=123, text="DNI (Damos Nuestra Ilusión)...")
    T->>U: "DNI (Damos Nuestra Ilusión)..."
```

#### Flujo 2: Usuario Vuelve Después de 5 Días (Cross-Sesión)

```mermaid
sequenceDiagram
    participant U as Usuario (Telegram)
    participant B as TelegramBotService
    participant DB as PostgreSQL
    participant P as PersistentContextManager
    participant R as ConversationalRAG

    Note over U,R: Día 1: Usuario preguntó sobre "Desayunos Solidarios"
    Note over U,R: Día 5: Usuario vuelve con pregunta ambigua

    U->>B: "¿A qué hora era?"

    B->>DB: SELECT * FROM users WHERE telegram_user_id=123
    DB-->>B: ✅ User exists (id=1, last_interaction=Día 1)

    B->>DB: UPDATE users SET last_interaction_at=NOW() WHERE id=1

    B->>P: load_context(user_id=1, max_days=30)
    P->>DB: SELECT cs.*, c.updated_at FROM context_snapshots cs JOIN conversations c ON cs.conversation_id=c.id WHERE cs.user_id=1 AND c.updated_at > NOW() - INTERVAL '30 days' ORDER BY c.updated_at DESC
    DB-->>P: [snapshot{project='Desayunos', updated_at=Día 1, message_count=5}]

    P->>P: calculate_decay(days_ago=4)
    Note over P: weight = exp(-ln(2)/3 * 4) = 0.40

    P-->>B: context=[{project='Desayunos', weight=0.40, messages=[...]}]

    B->>R: generate_response(query="¿A qué hora era?", historical_context=[...])

    Note over R: ContextTracker detecta proyecto "Desayunos" en contexto<br/>Query enrichment: "[Contexto: Desayunos Solidarios] ¿A qué hora era?"

    R->>R: EnhancedRAGEngineNew.retrieve(enriched_query)
    R-->>B: {answer="Los Desayunos Solidarios son a las 8:00 AM...", confidence=0.82}

    B->>DB: INSERT INTO messages (conversation_id=<existing>, role='user', content='¿A qué hora era?')
    B->>DB: INSERT INTO messages (conversation_id=<existing>, role='assistant', content='...', confidence=0.82)

    B->>P: save_context_snapshot(user_id=1, detected_project='Desayunos', message_count=7)
    P->>DB: UPDATE context_snapshots SET message_count=7, updated_at=NOW()

    B->>U: "Los Desayunos Solidarios son a las 8:00 AM..."
```

---

## 3. DISEÑO DE BASE DE DATOS (PostgreSQL)

### 3.1 Justificación de PostgreSQL

#### Comparación de Alternativas

| Criterio | PostgreSQL | MongoDB | SQLite | MySQL |
|----------|-----------|---------|--------|-------|
| **ACID Compliance** | ✅ Full | ⚠️ Eventual | ✅ Full | ✅ Full |
| **Relaciones complejas** | ✅ Excelente | ❌ Limitado | ✅ Bueno | ✅ Bueno |
| **JSON support** | ✅ Nativo (JSONB) | ✅ Nativo | ⚠️ Básico | ⚠️ Básico |
| **Full-text search** | ✅ Built-in (tsvector) | ✅ Text indexes | ❌ Limitado | ⚠️ Básico |
| **Concurrencia** | ✅ MVCC | ✅ Bueno | ❌ Locks | ✅ Bueno |
| **Escalabilidad** | ✅ Hasta TBs | ✅ Horizontal | ❌ Single file | ✅ Hasta TBs |
| **Licencia** | ✅ Open source | ✅ Open source | ✅ Public domain | ⚠️ GPL/Comercial |
| **Madurez** | ✅ 35+ años | ⚠️ 15 años | ✅ 20+ años | ✅ 25+ años |

**Decisión:** PostgreSQL seleccionado por:
1. ✅ Soporte nativo para JSONB (metadata flexible)
2. ✅ Full-text search integrado (búsqueda en historial de mensajes)
3. ✅ Robustez en relaciones complejas (users → conversations → messages)
4. ✅ MVCC para concurrencia sin locks (múltiples usuarios simultáneos)
5. ✅ Extensibilidad (pgcrypto para encryption, pg_trgm para fuzzy search)

### 3.2 Schema Completo

#### Diagrama Entidad-Relación

```
┌─────────────────────┐
│      users          │
│─────────────────────│
│ id (PK)             │◄──────┐
│ telegram_user_id    │       │
│ first_name          │       │
│ last_name           │       │
│ username            │       │
│ language_code       │       │
│ created_at          │       │
│ last_interaction_at │       │
│ is_active           │       │
└─────────────────────┘       │
                              │ 1:N
                              │
                    ┌─────────┴─────────────┐
                    │   conversations       │
                    │───────────────────────│
                    │ id (PK)               │◄──────┐
                    │ user_id (FK)          │       │
                    │ project_context       │       │
                    │ is_active             │       │
                    │ created_at            │       │
                    │ updated_at            │       │
                    └───────────────────────┘       │
                                                    │ 1:N
                    ┌───────────────────────────────┤
                    │                               │
          ┌─────────▼──────────┐        ┌──────────▼──────────┐
          │     messages       │        │  context_snapshots  │
          │────────────────────│        │─────────────────────│
          │ id (PK)            │        │ id (PK)             │
          │ conversation_id(FK)│        │ conversation_id (FK)│
          │ role               │        │ user_id (FK)        │
          │ content            │        │ project_context     │
          │ telegram_message_id│        │ detected_topics     │
          │ confidence_score   │        │ message_count       │
          │ retrieval_metadata │        │ last_user_query     │
          │ created_at         │        │ snapshot_data       │
          └────────────────────┘        │ created_at          │
                                        └─────────────────────┘

┌─────────────────────┐        ┌─────────────────────┐
│      feedback       │        │   user_consents     │
│─────────────────────│        │─────────────────────│
│ id (PK)             │        │ id (PK)             │
│ user_id (FK)        │        │ user_id (FK)        │
│ message_id (FK)     │        │ consent_type        │
│ rating              │        │ granted             │
│ comment             │        │ granted_at          │
│ created_at          │        │ revoked_at          │
└─────────────────────┘        └─────────────────────┘

┌─────────────────────┐
│  analytics_events   │
│─────────────────────│
│ id (PK)             │
│ user_id (FK)        │
│ event_type          │
│ event_data          │
│ created_at          │
└─────────────────────┘
```

### 3.3 Definición de Tablas

#### Tabla 1: `users`

**Propósito:** Almacenar información básica de cada usuario de Telegram que interactúa con el bot.

```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    telegram_user_id BIGINT NOT NULL UNIQUE,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255),
    username VARCHAR(255),
    language_code VARCHAR(10),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_interaction_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Constraints
    CONSTRAINT chk_telegram_user_id_positive CHECK (telegram_user_id > 0)
);

-- Índices
CREATE INDEX idx_users_telegram_user_id ON users(telegram_user_id);
CREATE INDEX idx_users_last_interaction ON users(last_interaction_at DESC)
    WHERE is_active = TRUE;
CREATE INDEX idx_users_created_at ON users(created_at DESC);

-- Comentarios (documentación en DB)
COMMENT ON TABLE users IS 'Usuarios de Telegram registrados en el sistema';
COMMENT ON COLUMN users.telegram_user_id IS 'ID único de Telegram (obtenido de update.effective_user.id)';
COMMENT ON COLUMN users.is_active IS 'FALSE si el usuario solicitó borrado de datos (GDPR)';
COMMENT ON COLUMN users.last_interaction_at IS 'Actualizado en cada mensaje para detectar usuarios inactivos';
```

**Justificación de Campos:**
- `telegram_user_id`: Identificador único proporcionado por Telegram, NO generado por nosotros. Es `BIGINT` porque Telegram usa IDs de 64-bit.
- `username`: Opcional (no todos los usuarios de Telegram tienen @username).
- `is_active`: Soft delete para GDPR compliance (mantener métricas sin exponer datos).
- `last_interaction_at`: Crítico para detectar usuarios inactivos (auto-borrado después de 90 días).

**Ejemplo de Datos:**
```sql
INSERT INTO users (telegram_user_id, first_name, last_name, username, language_code)
VALUES
    (123456789, 'María', 'García', 'maria_g', 'es'),
    (987654321, 'Carlos', NULL, NULL, 'es'),
    (555555555, 'Ana', 'López', 'ana_lopez', 'ca');
```

#### Tabla 2: `conversations`

**Propósito:** Agrupar mensajes en conversaciones lógicas basadas en contexto temporal y temático.

```sql
CREATE TYPE project_context_enum AS ENUM (
    'desayunos',      -- Desayunos Solidarios
    'resis',          -- Charlas con Abuelitos (residencia L'Acollida)
    'coles',          -- Refuerzo Escolar COLES
    'dana',           -- Rehabilitar Valencia (apoyo DANA - Horta Sud)
    'kayak',          -- Recogida de Plásticos
    'general',        -- Preguntas generales sobre DNI
    'unknown'         -- No detectado aún
);

CREATE TABLE conversations (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_context project_context_enum NOT NULL DEFAULT 'unknown',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_only_one_active_per_user
        EXCLUDE USING gist (user_id WITH =)
        WHERE (is_active = TRUE)
);

-- Índices
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_active ON conversations(user_id, is_active)
    WHERE is_active = TRUE;
CREATE INDEX idx_conversations_updated_at ON conversations(updated_at DESC);
CREATE INDEX idx_conversations_project ON conversations(project_context);

-- Trigger para auto-actualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE conversations IS 'Conversaciones agrupadas por tema/proyecto DNI';
COMMENT ON COLUMN conversations.is_active IS 'Solo 1 conversación activa por usuario (constraint)';
COMMENT ON COLUMN conversations.project_context IS 'Proyecto DNI detectado automáticamente por ContextTracker';
```

**Justificación de Diseño:**
- **ENUM para `project_context`:** Garantiza integridad referencial (no se pueden insertar valores inválidos como "desallunos").
- **Constraint `EXCLUDE USING gist`:** Garantiza que solo haya 1 conversación activa por usuario simultáneamente (previene race conditions).
- **Trigger `updated_at`:** Se actualiza automáticamente en cada INSERT de mensaje (via FK).

**Lógica de Negocio:**
- Nueva conversación si: (a) `updated_at` > 7 días de inactividad, o (b) cambio de proyecto detectado.
- Al crear nueva conversación: `UPDATE conversations SET is_active=FALSE WHERE user_id=X AND is_active=TRUE` (cierra la anterior).

**Ejemplo de Datos:**
```sql
INSERT INTO conversations (user_id, project_context, is_active)
VALUES
    (1, 'desayunos', TRUE),   -- María preguntando sobre desayunos (activa)
    (2, 'general', TRUE),     -- Carlos preguntando sobre DNI (activa)
    (1, 'coles', FALSE);      -- María preguntó sobre COLES hace 10 días (archivada)
```

#### Tabla 3: `messages`

**Propósito:** Almacenar todos los mensajes intercambiados (user ↔ assistant) con metadata completa de RAG.

```sql
CREATE TYPE message_role_enum AS ENUM ('user', 'assistant', 'system');

CREATE TABLE messages (
    id BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role message_role_enum NOT NULL,
    content TEXT NOT NULL,
    telegram_message_id BIGINT,
    confidence_score REAL,
    retrieval_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_content_not_empty CHECK (LENGTH(TRIM(content)) > 0),
    CONSTRAINT chk_confidence_range CHECK (confidence_score IS NULL OR
                                           (confidence_score >= 0.0 AND confidence_score <= 1.0)),
    CONSTRAINT chk_assistant_has_confidence CHECK (role != 'assistant' OR confidence_score IS NOT NULL),
    CONSTRAINT chk_telegram_message_id_positive CHECK (telegram_message_id IS NULL OR telegram_message_id > 0)
);

-- Índices
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id, created_at DESC);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX idx_messages_role ON messages(role) WHERE role = 'user';
CREATE INDEX idx_messages_confidence ON messages(confidence_score DESC NULLS LAST)
    WHERE role = 'assistant';

-- Índice GIN para búsqueda full-text en contenido
CREATE INDEX idx_messages_content_fts ON messages
    USING gin(to_tsvector('spanish', content));

-- Índice GIN para búsqueda en metadata JSON
CREATE INDEX idx_messages_metadata ON messages USING gin(retrieval_metadata);

COMMENT ON TABLE messages IS 'Mensajes de conversación con metadata de RAG';
COMMENT ON COLUMN messages.telegram_message_id IS 'ID del mensaje en Telegram (para editar/borrar)';
COMMENT ON COLUMN messages.confidence_score IS 'Score de confianza (0.0-1.0), obligatorio para role=assistant';
COMMENT ON COLUMN messages.retrieval_metadata IS 'JSON con chunks, scores, latencia, sources, etc.';
```

**Estructura del Campo `retrieval_metadata` (JSONB):**

```json
{
  "chunks_used": 12,
  "top_chunks": [
    {
      "chunk_id": "chunk_123",
      "score": 0.87,
      "source": "07_desayunos_logistica.txt"
    },
    {
      "chunk_id": "chunk_456",
      "score": 0.82,
      "source": "01_faq_dni.txt"
    }
  ],
  "confidence_breakdown": {
    "chunks_factor": 0.85,
    "length_factor": 0.92,
    "negative_factor": 1.0,
    "specificity_factor": 0.88,
    "overlap_factor": 0.73,
    "keyword_factor": 0.82
  },
  "latency_ms": 2340,
  "model_used": "gemma2:27b",
  "context_enriched": true,
  "historical_context_used": true
}
```

**Justificación de JSONB:**
- ✅ Esquema flexible (puede evolucionar sin migrations)
- ✅ Queryable (puede buscar por `retrieval_metadata->>'model_used'`)
- ✅ Indexable con GIN (búsquedas rápidas)
- ✅ Compresión automática (PostgreSQL comprime JSONB)

**Ejemplo de Datos:**
```sql
INSERT INTO messages (conversation_id, role, content, telegram_message_id, confidence_score, retrieval_metadata)
VALUES
    (1, 'user', '¿Cuándo son los desayunos?', 10001, NULL, NULL),
    (1, 'assistant', 'Los Desayunos Solidarios son todos los sábados a las 8:00 AM...',
     10002, 0.87,
     '{"chunks_used": 10, "latency_ms": 2100, "model_used": "gemma2:27b"}'::jsonb);
```

#### Tabla 4: `context_snapshots`

**Propósito:** Almacenar snapshots del contexto conversacional cada N mensajes para optimizar retrieval histórico.

```sql
CREATE TABLE context_snapshots (
    id BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_context project_context_enum NOT NULL,
    detected_topics TEXT[],
    message_count INTEGER NOT NULL DEFAULT 0,
    last_user_query TEXT,
    snapshot_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_message_count_positive CHECK (message_count >= 0)
);

-- Índices
CREATE INDEX idx_snapshots_conversation_id ON context_snapshots(conversation_id);
CREATE INDEX idx_snapshots_user_id ON context_snapshots(user_id, created_at DESC);
CREATE INDEX idx_snapshots_created_at ON context_snapshots(created_at DESC);
CREATE INDEX idx_snapshots_project ON context_snapshots(project_context);

-- Índice GIN para búsqueda en array de topics
CREATE INDEX idx_snapshots_topics ON context_snapshots USING gin(detected_topics);

COMMENT ON TABLE context_snapshots IS 'Snapshots periódicos del contexto conversacional (cada 5 mensajes)';
COMMENT ON COLUMN context_snapshots.detected_topics IS 'Array de temas detectados (ej: ["horarios", "ubicacion"])';
COMMENT ON COLUMN context_snapshots.message_count IS 'Número de mensajes en la conversación al momento del snapshot';
COMMENT ON COLUMN context_snapshots.snapshot_data IS 'JSON con estado completo del contexto';
```

**Estructura del Campo `snapshot_data` (JSONB):**

```json
{
  "project_confidence": 0.92,
  "topic_confidence": 0.85,
  "last_5_messages": [
    {"role": "user", "content": "¿Cuándo son los desayunos?", "timestamp": "2025-11-15T10:00:00Z"},
    {"role": "assistant", "content": "Los sábados a las 8 AM...", "timestamp": "2025-11-15T10:00:02Z"}
  ],
  "keywords": ["desayunos", "sábado", "8 AM", "Carrer de Sagunt"],
  "entities": ["Desayunos Solidarios", "Valencia"],
  "context_tracker_state": {
    "window_size": 4,
    "projects_detected": ["desayunos"],
    "decay_applied": false
  }
}
```

**Justificación de Diseño:**
- **Snapshots cada 5 mensajes:** Balance entre performance (menos DB queries) y granularidad.
- **Array de `detected_topics`:** Permite búsqueda eficiente con GIN index (`WHERE 'horarios' = ANY(detected_topics)`).
- **Redundancia `user_id`:** Optimiza queries cross-conversación (ej: "buscar todos los snapshots del usuario en últimos 30 días").

**Ejemplo de Datos:**
```sql
INSERT INTO context_snapshots (conversation_id, user_id, project_context, detected_topics, message_count, last_user_query, snapshot_data)
VALUES
    (1, 1, 'desayunos', ARRAY['horarios', 'ubicacion'], 5, '¿Dónde quedamos?',
     '{"project_confidence": 0.92, "keywords": ["desayunos", "sábado"]}'::jsonb);
```

#### Tabla 5: `feedback`

**Propósito:** Almacenar feedback de usuarios (👍/👎) para evaluar calidad de respuestas.

```sql
CREATE TYPE feedback_rating_enum AS ENUM ('positive', 'negative');

CREATE TABLE feedback (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message_id BIGINT NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    rating feedback_rating_enum NOT NULL,
    comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_feedback_unique UNIQUE (message_id),
    CONSTRAINT chk_comment_length CHECK (comment IS NULL OR LENGTH(comment) <= 500)
);

-- Índices
CREATE INDEX idx_feedback_user_id ON feedback(user_id);
CREATE INDEX idx_feedback_message_id ON feedback(message_id);
CREATE INDEX idx_feedback_rating ON feedback(rating);
CREATE INDEX idx_feedback_created_at ON feedback(created_at DESC);

COMMENT ON TABLE feedback IS 'Feedback de usuarios sobre respuestas del bot (👍👎)';
COMMENT ON COLUMN feedback.comment IS 'Comentario opcional del usuario (máx 500 chars)';
```

**Ejemplo de Datos:**
```sql
INSERT INTO feedback (user_id, message_id, rating, comment)
VALUES
    (1, 2, 'positive', 'Respuesta muy clara, gracias!'),
    (2, 4, 'negative', 'No respondió mi pregunta exacta');
```

#### Tabla 6: `user_consents`

**Propósito:** Rastrear consentimientos GDPR (data storage, analytics, etc.).

```sql
CREATE TYPE consent_type_enum AS ENUM (
    'data_storage',
    'analytics',
    'marketing'
);

CREATE TABLE user_consents (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    consent_type consent_type_enum NOT NULL,
    granted BOOLEAN NOT NULL DEFAULT FALSE,
    granted_at TIMESTAMP WITH TIME ZONE,
    revoked_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT chk_consents_unique UNIQUE (user_id, consent_type),
    CONSTRAINT chk_granted_logic CHECK (
        (granted = TRUE AND granted_at IS NOT NULL) OR
        (granted = FALSE AND revoked_at IS NOT NULL)
    )
);

-- Índices
CREATE INDEX idx_consents_user_id ON user_consents(user_id);
CREATE INDEX idx_consents_type ON user_consents(consent_type, granted);

COMMENT ON TABLE user_consents IS 'Gestión de consentimientos GDPR';
COMMENT ON COLUMN user_consents.granted IS 'TRUE si consentimiento activo, FALSE si revocado';
```

**Ejemplo de Datos:**
```sql
INSERT INTO user_consents (user_id, consent_type, granted, granted_at)
VALUES
    (1, 'data_storage', TRUE, NOW()),
    (1, 'analytics', TRUE, NOW());
```

#### Tabla 7: `analytics_events`

**Propósito:** Registrar eventos de uso para análisis (opcional, fuera de MVP).

```sql
CREATE TYPE event_type_enum AS ENUM (
    'bot_started',
    'command_used',
    'conversation_started',
    'conversation_ended',
    'context_retrieved',
    'error_occurred'
);

CREATE TABLE analytics_events (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    event_type event_type_enum NOT NULL,
    event_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_analytics_user_id ON analytics_events(user_id);
CREATE INDEX idx_analytics_type ON analytics_events(event_type);
CREATE INDEX idx_analytics_created_at ON analytics_events(created_at DESC);

-- Índice parcial para eventos recientes (últimos 30 días)
CREATE INDEX idx_analytics_recent ON analytics_events(created_at DESC)
    WHERE created_at > NOW() - INTERVAL '30 days';

COMMENT ON TABLE analytics_events IS 'Eventos de uso para analytics (opcional)';
```

### 3.4 Relaciones y Constraints

#### Cascade Rules

| Acción | Tabla Origen | Tabla Destino | Comportamiento |
|--------|--------------|---------------|----------------|
| DELETE user | users | conversations | CASCADE (borrar todas sus conversaciones) |
| DELETE user | users | messages | CASCADE (vía conversations) |
| DELETE user | users | context_snapshots | CASCADE |
| DELETE user | users | feedback | CASCADE |
| DELETE user | users | user_consents | CASCADE |
| DELETE user | users | analytics_events | SET NULL (preservar evento sin identificar) |
| DELETE conversation | conversations | messages | CASCADE |
| DELETE conversation | conversations | context_snapshots | CASCADE |

**Justificación:** Cumplimiento GDPR - cuando usuario solicita borrado (`/delete_data`), se elimina completamente de `users` y todas las tablas relacionadas en cascada.

#### Integrity Constraints Summary

```sql
-- Solo 1 conversación activa por usuario
ALTER TABLE conversations
    ADD CONSTRAINT chk_only_one_active_per_user
    EXCLUDE USING gist (user_id WITH =) WHERE (is_active = TRUE);

-- Mensajes de assistant DEBEN tener confidence_score
ALTER TABLE messages
    ADD CONSTRAINT chk_assistant_has_confidence
    CHECK (role != 'assistant' OR confidence_score IS NOT NULL);

-- Feedback único por mensaje
ALTER TABLE feedback
    ADD CONSTRAINT chk_feedback_unique UNIQUE (message_id);

-- Consentimiento único por tipo
ALTER TABLE user_consents
    ADD CONSTRAINT chk_consents_unique UNIQUE (user_id, consent_type);
```

### 3.5 Índices de Optimización

#### Análisis de Query Patterns

| Query Frecuente | Índice Requerido | Justificación |
|-----------------|------------------|---------------|
| "Buscar usuario por telegram_id" | `idx_users_telegram_user_id` | Lookup en CADA mensaje recibido |
| "Obtener conversación activa del usuario" | `idx_conversations_active` | Cada mensaje debe encontrar conversación activa |
| "Obtener últimos N mensajes de conversación" | `idx_messages_conversation_id` | Para construir historial en context window |
| "Buscar snapshots recientes del usuario" | `idx_snapshots_user_id` | Context retrieval cross-sesión |
| "Búsqueda full-text en mensajes" | `idx_messages_content_fts` | Feature futuro: buscar en historial |
| "Filtrar usuarios inactivos (>90 días)" | `idx_users_last_interaction` | Cleanup job mensual |

#### Performance Estimations

**Query 1: Buscar conversación activa**
```sql
SELECT c.*
FROM conversations c
WHERE c.user_id = 1 AND c.is_active = TRUE;
```
- **Sin índice:** O(N) - Full table scan
- **Con `idx_conversations_active`:** O(1) - Index-only scan
- **Improvement:** ~1000x para tabla con 10k conversaciones

**Query 2: Context retrieval cross-sesión**
```sql
SELECT cs.*
FROM context_snapshots cs
JOIN conversations c ON cs.conversation_id = c.id
WHERE cs.user_id = 1
  AND c.updated_at > NOW() - INTERVAL '30 days'
ORDER BY c.updated_at DESC
LIMIT 10;
```
- **Expected rows:** ~6 snapshots (1 usuario, 2 conversaciones, 3 snapshots c/u)
- **Execution time:** <50ms (con índices)
- **Without indexes:** ~500ms (tabla con 100k snapshots)

### 3.6 Data Retention y Archivado

#### Política de Retención (GDPR Compliance)

| Datos | Retention Period | Justificación | Acción Post-Retention |
|-------|------------------|---------------|----------------------|
| **Mensajes** | 90 días | Balance privacidad/utilidad | Borrado automático |
| **Context snapshots** | 90 días | Misma retention que mensajes | Borrado automático |
| **Conversaciones** | 90 días | Metadata sin contenido | Borrado automático |
| **Usuarios inactivos** | 90 días sin interacción | GDPR minimización de datos | Anonimizar (no borrar) |
| **Feedback** | Indefinido (anonimizado) | Mejora del sistema | Desvincular user_id |
| **Analytics** | 365 días | Análisis histórico | Borrado automático |

#### Cleanup Job (Cron Mensual)

```sql
-- Script: cleanup_old_data.sql
-- Frecuencia: Ejecutar el día 1 de cada mes a las 03:00 AM

BEGIN;

-- 1. Borrar mensajes >90 días (cascada a context_snapshots por FK)
DELETE FROM messages
WHERE created_at < NOW() - INTERVAL '90 days';

-- 2. Borrar conversaciones >90 días sin mensajes (huérfanas)
DELETE FROM conversations
WHERE updated_at < NOW() - INTERVAL '90 days'
  AND id NOT IN (SELECT DISTINCT conversation_id FROM messages);

-- 3. Anonimizar usuarios inactivos >90 días
UPDATE users
SET
    first_name = 'Usuario Inactivo',
    last_name = NULL,
    username = NULL,
    is_active = FALSE
WHERE last_interaction_at < NOW() - INTERVAL '90 days'
  AND is_active = TRUE;

-- 4. Desvincular feedback de usuarios borrados (preservar métricas)
UPDATE feedback
SET user_id = NULL
WHERE user_id IN (
    SELECT id FROM users WHERE is_active = FALSE
);

-- 5. Borrar analytics events >365 días
DELETE FROM analytics_events
WHERE created_at < NOW() - INTERVAL '365 days';

-- 6. Vacuum para recuperar espacio
VACUUM ANALYZE messages, conversations, context_snapshots, analytics_events;

COMMIT;
```

### 3.7 Migrations con Alembic

#### Configuración Inicial

```bash
# Instalar Alembic
pip install alembic psycopg2-binary

# Inicializar Alembic en el proyecto
cd /home/vicente/Practicas/rag_optimizer_complete/rag_optimizer
alembic init alembic

# Editar alembic.ini
# sqlalchemy.url = postgresql://user:password@localhost:5432/chatbot_dni_db
```

#### Primera Migration: Schema Inicial

**Archivo:** `alembic/versions/001_initial_schema.py`

```python
"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-11-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Crear ENUMs
    project_context = postgresql.ENUM(
        'desayunos', 'resis', 'coles', 'dana', 'kayak', 'general', 'unknown',
        name='project_context_enum'
    )
    project_context.create(op.get_bind())

    message_role = postgresql.ENUM('user', 'assistant', 'system', name='message_role_enum')
    message_role.create(op.get_bind())

    feedback_rating = postgresql.ENUM('positive', 'negative', name='feedback_rating_enum')
    feedback_rating.create(op.get_bind())

    consent_type = postgresql.ENUM('data_storage', 'analytics', 'marketing', name='consent_type_enum')
    consent_type.create(op.get_bind())

    event_type = postgresql.ENUM(
        'bot_started', 'command_used', 'conversation_started',
        'conversation_ended', 'context_retrieved', 'error_occurred',
        name='event_type_enum'
    )
    event_type.create(op.get_bind())

    # Tabla users
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('telegram_user_id', sa.BigInteger(), nullable=False),
        sa.Column('first_name', sa.String(255), nullable=False),
        sa.Column('last_name', sa.String(255), nullable=True),
        sa.Column('username', sa.String(255), nullable=True),
        sa.Column('language_code', sa.String(10), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('last_interaction_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='TRUE', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_user_id'),
        sa.CheckConstraint('telegram_user_id > 0', name='chk_telegram_user_id_positive')
    )

    # Índices users
    op.create_index('idx_users_telegram_user_id', 'users', ['telegram_user_id'])
    op.create_index('idx_users_last_interaction', 'users', [sa.text('last_interaction_at DESC')],
                    postgresql_where=sa.text('is_active = TRUE'))

    # Tabla conversations (definición completa similar...)
    # ... [continuar con resto de tablas] ...

def downgrade():
    # Orden inverso (por FKs)
    op.drop_table('analytics_events')
    op.drop_table('user_consents')
    op.drop_table('feedback')
    op.drop_table('context_snapshots')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('users')

    # Borrar ENUMs
    postgresql.ENUM(name='event_type_enum').drop(op.get_bind())
    postgresql.ENUM(name='consent_type_enum').drop(op.get_bind())
    postgresql.ENUM(name='feedback_rating_enum').drop(op.get_bind())
    postgresql.ENUM(name='message_role_enum').drop(op.get_bind())
    postgresql.ENUM(name='project_context_enum').drop(op.get_bind())
```

#### Aplicar Migrations

```bash
# Generar migration automática (detecta cambios en modelos)
alembic revision --autogenerate -m "Add new field to users"

# Aplicar todas las migrations pendientes
alembic upgrade head

# Rollback última migration
alembic downgrade -1

# Ver historial de migrations
alembic history

# Ver SQL sin ejecutar (dry-run)
alembic upgrade head --sql
```

### 3.8 Ejemplo Completo: Flujo de Datos en DB

#### Scenario: Usuario pregunta "¿Cuándo son los desayunos?" por primera vez

**Step 1: Usuario nuevo interactúa**
```sql
-- Bot recibe mensaje de telegram_user_id=123456789
-- Busca usuario
SELECT * FROM users WHERE telegram_user_id = 123456789;
-- Resultado: (vacío)

-- Crea usuario
INSERT INTO users (telegram_user_id, first_name, language_code)
VALUES (123456789, 'María', 'es')
RETURNING id;
-- Resultado: id = 1
```

**Step 2: Crear conversación**
```sql
-- Crear conversación (project_context=unknown inicialmente)
INSERT INTO conversations (user_id, project_context)
VALUES (1, 'unknown')
RETURNING id;
-- Resultado: id = 1
```

**Step 3: Guardar mensaje de usuario**
```sql
INSERT INTO messages (conversation_id, role, content, telegram_message_id)
VALUES (1, 'user', '¿Cuándo son los desayunos?', 50001);
```

**Step 4: Generar respuesta (RAG ejecuta)**
```sql
-- (RAG ejecuta en backend, no toca DB)
-- Resultado: "Los Desayunos Solidarios son todos los sábados a las 8:00 AM..."
-- Confidence: 0.87
-- Metadata: {...}
```

**Step 5: Guardar respuesta del bot**
```sql
INSERT INTO messages (conversation_id, role, content, telegram_message_id, confidence_score, retrieval_metadata)
VALUES (
    1,
    'assistant',
    'Los Desayunos Solidarios son todos los sábados a las 8:00 AM en Valencia...',
    50002,
    0.87,
    '{"chunks_used": 10, "latency_ms": 2100, "model_used": "gemma2:27b", "top_chunks": [...]}'::jsonb
);
```

**Step 6: Actualizar conversación con proyecto detectado**
```sql
UPDATE conversations
SET project_context = 'desayunos', updated_at = NOW()
WHERE id = 1;
```

**Step 7: Crear primer snapshot (después de 5 mensajes)**
```sql
-- (Asumiendo que ya hay 5 mensajes en la conversación)
INSERT INTO context_snapshots (
    conversation_id, user_id, project_context,
    detected_topics, message_count, last_user_query, snapshot_data
)
VALUES (
    1, 1, 'desayunos',
    ARRAY['horarios', 'ubicacion'],
    5,
    '¿Dónde quedamos para ir juntos?',
    '{
        "project_confidence": 0.92,
        "keywords": ["desayunos", "sábado", "8 AM", "Carrer de Sagunt"],
        "last_5_messages": [...]
    }'::jsonb
);
```

#### Scenario: Usuario vuelve 5 días después con "¿A qué hora era?"

**Step 1: Identificar usuario**
```sql
SELECT id, last_interaction_at
FROM users
WHERE telegram_user_id = 123456789;
-- Resultado: id=1, last_interaction_at=2025-11-15 10:00:00
```

**Step 2: Actualizar timestamp**
```sql
UPDATE users
SET last_interaction_at = NOW()
WHERE id = 1;
```

**Step 3: Obtener conversación activa**
```sql
SELECT *
FROM conversations
WHERE user_id = 1 AND is_active = TRUE;
-- Resultado: conversation_id=1, project_context='desayunos'
```

**Step 4: Recuperar contexto histórico (últimos 30 días)**
```sql
SELECT
    cs.*,
    c.updated_at,
    EXTRACT(EPOCH FROM (NOW() - c.updated_at)) / 86400 AS days_ago
FROM context_snapshots cs
JOIN conversations c ON cs.conversation_id = c.id
WHERE cs.user_id = 1
  AND c.updated_at > NOW() - INTERVAL '30 days'
ORDER BY c.updated_at DESC
LIMIT 10;
-- Resultado:
-- [snapshot{project='desayunos', days_ago=5, project_confidence=0.92, ...}]
```

**Step 5: Calcular decay weight (en backend Python)**
```python
import math
days_ago = 5
half_life = 3  # días
lambda_decay = math.log(2) / half_life
weight = math.exp(-lambda_decay * days_ago)
# weight = exp(-0.231 * 5) = 0.315
```

**Step 6: Enriquecer query con contexto**
```python
# Backend detecta proyecto "desayunos" con weight=0.315 (aún relevante)
enriched_query = "[Contexto: Desayunos Solidarios] ¿A qué hora era?"
```

**Step 7: Guardar nuevo mensaje + respuesta (similar a Step 3-5 anterior)**

---

## 4. GESTIÓN DE CONTEXTO PERSISTENTE

### 4.1 Fundamentos Teóricos: Context Decay

#### Motivación del Problema

En sistemas conversacionales con persistencia de largo plazo, surge un desafío fundamental: **¿cómo ponderar contexto antiguo vs contexto reciente?**

**Ejemplo crítico:**
- **Día 1:** Usuario pregunta sobre "Desayunos Solidarios" (5 mensajes)
- **Día 3:** Usuario pregunta sobre "Refuerzo Escolar COLES" (4 mensajes)
- **Día 10:** Usuario pregunta ambiguamente "¿A qué hora era?"

**Problema:** Si ponderamos todo el contexto por igual, el sistema podría confundir proyectos. Si solo miramos la última conversación, perdemos información relevante.

**Solución:** Context decay exponencial con half-life configurable.

#### Modelo Matemático: Exponential Decay

**Función de decay:**

```
weight(t) = exp(-λ * t)
```

Donde:
- `t`: Tiempo transcurrido en días desde la conversación
- `λ`: Constante de decay (lambda)
- `weight(t)`: Peso del contexto (0.0 - 1.0)

**Relación con half-life:**

El half-life (t₁/₂) es el tiempo necesario para que el peso se reduzca a la mitad:

```
weight(t₁/₂) = 0.5 = exp(-λ * t₁/₂)

Resolviendo para λ:
λ = ln(2) / t₁/₂
```

**Configuración para DNI:**
- Half-life: **3 días** (balance entre memoria corto/largo plazo)
- λ = ln(2) / 3 ≈ 0.231

**Tabla de pesos según días transcurridos:**

| Días atrás | Cálculo | Weight | Interpretación |
|-----------|---------|--------|----------------|
| 0 (hoy) | exp(-0.231 * 0) | 1.000 | Contexto completamente relevante |
| 1 | exp(-0.231 * 1) | 0.794 | Muy relevante |
| 2 | exp(-0.231 * 2) | 0.630 | Relevante |
| 3 (half-life) | exp(-0.231 * 3) | 0.500 | Moderadamente relevante |
| 5 | exp(-0.231 * 5) | 0.315 | Poco relevante |
| 7 | exp(-0.231 * 7) | 0.199 | Débilmente relevante |
| 10 | exp(-0.231 * 10) | 0.100 | Muy débilmente relevante |
| 14 | exp(-0.231 * 14) | 0.050 | Casi irrelevante |
| 30 | exp(-0.231 * 30) | 0.001 | Prácticamente irrelevante |

**Threshold de relevancia:**
- Weight < 0.1 (>10 días): Mostrar advertencia al usuario ("Hace tiempo hablamos de esto...")
- Weight < 0.01 (>30 días): Ignorar contexto (no usar para enrichment)

#### Justificación del Half-Life de 3 Días

**Alternativas consideradas:**

| Half-life | Pros | Contras | Caso de uso |
|-----------|------|---------|-------------|
| **1 día** | Memoria muy corta, contexto reciente dominante | Usuario debe repetir info si vuelve 2-3 días después | Chatbots transaccionales (banca, e-commerce) |
| **3 días** ✅ | Balance óptimo para DNI (voluntarios activos semanalmente) | - | Asociaciones de voluntarios |
| **7 días** | Memoria larga, recordar conversaciones semanales | Contexto antiguo podría confundir | Coaching personal, terapia |
| **14 días** | Memoria muy larga | Riesgo alto de mezclar contextos | CRM empresarial |

**Decisión para DNI:** 3 días porque:
1. ✅ Ciclo de actividad típico: Viernes (planificación) → Sábado (Desayunos) → Lunes (feedback)
2. ✅ Usuario que pregunta lunes y vuelve viernes tiene weight=0.63 (aún relevante)
3. ✅ Usuario que vuelve después de 2 semanas (weight=0.05) recibe advertencia

### 4.2 Algoritmo de Context Retrieval

#### Pseudocódigo de Alto Nivel

```python
def retrieve_context(user_id: int, current_query: str, max_days: int = 30) -> ContextData:
    """
    Recupera y pondera contexto histórico del usuario.

    Args:
        user_id: ID del usuario en DB
        current_query: Query actual del usuario
        max_days: Ventana temporal máxima (default 30 días)

    Returns:
        ContextData con proyectos detectados, pesos y mensajes relevantes
    """
    # 1. Recuperar snapshots de últimos max_days
    snapshots = db.query(
        """
        SELECT cs.*, c.updated_at,
               EXTRACT(EPOCH FROM (NOW() - c.updated_at)) / 86400 AS days_ago
        FROM context_snapshots cs
        JOIN conversations c ON cs.conversation_id = c.id
        WHERE cs.user_id = %s
          AND c.updated_at > NOW() - INTERVAL '%s days'
        ORDER BY c.updated_at DESC
        """,
        (user_id, max_days)
    )

    # 2. Calcular decay weights
    half_life = 3  # días
    lambda_decay = ln(2) / half_life

    for snapshot in snapshots:
        snapshot.weight = exp(-lambda_decay * snapshot.days_ago)

    # 3. Filtrar por threshold
    relevant_snapshots = [s for s in snapshots if s.weight >= 0.01]

    # 4. Agrupar por proyecto y sumar pesos
    project_weights = defaultdict(float)
    for snapshot in relevant_snapshots:
        project_weights[snapshot.project_context] += snapshot.weight

    # 5. Seleccionar proyecto dominante
    if project_weights:
        dominant_project = max(project_weights, key=project_weights.get)
        project_confidence = project_weights[dominant_project] / sum(project_weights.values())
    else:
        dominant_project = None
        project_confidence = 0.0

    # 6. Decidir si enriquecer query
    should_enrich = (
        project_confidence > 0.4 and          # Confianza mínima
        is_query_ambiguous(current_query) and # Query necesita contexto
        max(s.weight for s in relevant_snapshots) > 0.1  # Contexto no muy antiguo
    )

    return ContextData(
        dominant_project=dominant_project,
        project_confidence=project_confidence,
        should_enrich=should_enrich,
        snapshots=relevant_snapshots,
        max_weight=max(s.weight for s in relevant_snapshots) if relevant_snapshots else 0.0
    )
```

#### Detección de Queries Ambiguas

```python
def is_query_ambiguous(query: str) -> bool:
    """
    Detecta si una query es ambigua y se beneficiaría de contexto histórico.

    Queries ambiguas típicas:
    - "¿A qué hora era?"
    - "¿Dónde quedamos?"
    - "¿Quién organiza?"
    - "¿Cuándo es?"
    """
    ambiguous_patterns = [
        r'\b(a qué hora|qué hora|horario)\b',
        r'\b(dónde|donde|lugar|sitio|ubicación)\b',
        r'\b(quién|quien|responsable|contacto)\b',
        r'\b(cuándo|cuando|día|fecha)\b',
        r'\b(cómo|como|requisitos|condiciones)\b',
    ]

    # Query es ambigua si:
    # 1. Contiene pattern ambiguo
    # 2. NO menciona explícitamente un proyecto DNI

    query_lower = query.lower()

    has_ambiguous_pattern = any(
        re.search(pattern, query_lower) for pattern in ambiguous_patterns
    )

    dni_projects = ['desayunos', 'coles', 'resis', 'abuelitos', 'dana', 'kayak']
    mentions_project = any(project in query_lower for project in dni_projects)

    return has_ambiguous_pattern and not mentions_project
```

### 4.3 PersistentContextManager: Implementación Completa

**Archivo:** `src/core/persistent_context_manager.py`

```python
"""
Persistent Context Manager para Chatbot DNI con Telegram.

Gestiona persistencia cross-sesión de contexto conversacional usando PostgreSQL.
Implementa exponential decay con half-life de 3 días.

Author: Vicente
Date: 2025-11-19
"""

import math
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


@dataclass
class ContextSnapshot:
    """Representa un snapshot de contexto con su peso temporal."""
    id: int
    conversation_id: int
    user_id: int
    project_context: str
    detected_topics: List[str]
    message_count: int
    last_user_query: str
    snapshot_data: Dict[str, Any]
    created_at: datetime
    days_ago: float
    weight: float  # Calculado con exponential decay


@dataclass
class ContextData:
    """Resultado del context retrieval."""
    dominant_project: Optional[str]
    project_confidence: float
    should_enrich: bool
    snapshots: List[ContextSnapshot]
    max_weight: float
    warning_old_context: bool  # True si max_weight < 0.1


class PersistentContextManager:
    """
    Gestiona contexto persistente cross-sesión.

    Responsabilidades:
    1. Recuperar contexto histórico de DB con decay weights
    2. Decidir si enriquecer query con contexto
    3. Guardar snapshots periódicos
    4. Limpiar contexto antiguo
    """

    def __init__(
        self,
        db_connection_string: str,
        half_life_days: float = 3.0,
        max_context_days: int = 30,
        min_confidence_threshold: float = 0.4,
        min_weight_threshold: float = 0.01
    ):
        """
        Args:
            db_connection_string: PostgreSQL connection string
            half_life_days: Half-life para exponential decay (default 3 días)
            max_context_days: Ventana temporal máxima (default 30 días)
            min_confidence_threshold: Confianza mínima para enrichment (default 0.4)
            min_weight_threshold: Peso mínimo para considerar snapshot (default 0.01)
        """
        self.db_connection_string = db_connection_string
        self.half_life_days = half_life_days
        self.max_context_days = max_context_days
        self.min_confidence_threshold = min_confidence_threshold
        self.min_weight_threshold = min_weight_threshold

        # Calcular lambda para exponential decay
        self.lambda_decay = math.log(2) / self.half_life_days

        logger.info(
            f"PersistentContextManager initialized: "
            f"half_life={half_life_days}d, lambda={self.lambda_decay:.3f}, "
            f"max_days={max_context_days}"
        )

    def _get_connection(self):
        """Obtener conexión a PostgreSQL."""
        return psycopg2.connect(self.db_connection_string)

    def calculate_decay_weight(self, days_ago: float) -> float:
        """
        Calcula peso de decay exponencial.

        Formula: weight = exp(-λ * days_ago)

        Args:
            days_ago: Días transcurridos desde el snapshot

        Returns:
            Peso entre 0.0 (muy antiguo) y 1.0 (actual)
        """
        return math.exp(-self.lambda_decay * days_ago)

    def retrieve_context(
        self,
        user_id: int,
        current_query: str
    ) -> ContextData:
        """
        Recupera contexto histórico del usuario con decay weights.

        Args:
            user_id: ID del usuario en DB
            current_query: Query actual del usuario

        Returns:
            ContextData con proyectos detectados y decisión de enrichment
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Query optimizada con JOIN
                cur.execute(
                    """
                    SELECT
                        cs.id,
                        cs.conversation_id,
                        cs.user_id,
                        cs.project_context,
                        cs.detected_topics,
                        cs.message_count,
                        cs.last_user_query,
                        cs.snapshot_data,
                        cs.created_at,
                        c.updated_at,
                        EXTRACT(EPOCH FROM (NOW() - c.updated_at)) / 86400.0 AS days_ago
                    FROM context_snapshots cs
                    JOIN conversations c ON cs.conversation_id = c.id
                    WHERE cs.user_id = %s
                      AND c.updated_at > NOW() - INTERVAL '%s days'
                    ORDER BY c.updated_at DESC
                    LIMIT 20
                    """,
                    (user_id, self.max_context_days)
                )

                rows = cur.fetchall()
        finally:
            conn.close()

        # Convertir a ContextSnapshot con decay weights
        snapshots = []
        for row in rows:
            weight = self.calculate_decay_weight(row['days_ago'])

            # Filtrar por threshold
            if weight < self.min_weight_threshold:
                continue

            snapshot = ContextSnapshot(
                id=row['id'],
                conversation_id=row['conversation_id'],
                user_id=row['user_id'],
                project_context=row['project_context'],
                detected_topics=row['detected_topics'] or [],
                message_count=row['message_count'],
                last_user_query=row['last_user_query'],
                snapshot_data=row['snapshot_data'],
                created_at=row['created_at'],
                days_ago=row['days_ago'],
                weight=weight
            )
            snapshots.append(snapshot)

        logger.info(f"Retrieved {len(snapshots)} relevant snapshots for user {user_id}")

        # Si no hay contexto histórico
        if not snapshots:
            return ContextData(
                dominant_project=None,
                project_confidence=0.0,
                should_enrich=False,
                snapshots=[],
                max_weight=0.0,
                warning_old_context=False
            )

        # Agrupar por proyecto y sumar pesos
        project_weights = defaultdict(float)
        for snapshot in snapshots:
            if snapshot.project_context != 'unknown':
                project_weights[snapshot.project_context] += snapshot.weight

        # Seleccionar proyecto dominante
        if project_weights:
            dominant_project = max(project_weights, key=project_weights.get)
            total_weight = sum(project_weights.values())
            project_confidence = project_weights[dominant_project] / total_weight
        else:
            dominant_project = None
            project_confidence = 0.0

        max_weight = max(s.weight for s in snapshots)

        # Decidir si enriquecer query
        should_enrich = (
            project_confidence >= self.min_confidence_threshold and
            self._is_query_ambiguous(current_query) and
            max_weight >= 0.1  # No enriquecer con contexto muy antiguo
        )

        # Advertencia si contexto es antiguo pero aún relevante
        warning_old_context = (max_weight < 0.1 and should_enrich)

        logger.info(
            f"Context analysis: dominant_project={dominant_project}, "
            f"confidence={project_confidence:.3f}, max_weight={max_weight:.3f}, "
            f"should_enrich={should_enrich}"
        )

        return ContextData(
            dominant_project=dominant_project,
            project_confidence=project_confidence,
            should_enrich=should_enrich,
            snapshots=snapshots,
            max_weight=max_weight,
            warning_old_context=warning_old_context
        )

    def _is_query_ambiguous(self, query: str) -> bool:
        """
        Detecta si query es ambigua y necesita contexto.

        Args:
            query: Query del usuario

        Returns:
            True si query es ambigua
        """
        import re

        ambiguous_patterns = [
            r'\b(a qué hora|qué hora|horario)\b',
            r'\b(dónde|donde|lugar|sitio|ubicación|punto de encuentro)\b',
            r'\b(quién|quien|responsable|contacto|organizador)\b',
            r'\b(cuándo|cuando|día|fecha)\b',
            r'\b(cómo|como|requisitos|condiciones|necesito)\b',
            r'\b(qué era|a qué|de qué)\b',
        ]

        query_lower = query.lower()

        has_ambiguous = any(
            re.search(pattern, query_lower) for pattern in ambiguous_patterns
        )

        # Menciona proyecto explícitamente?
        dni_projects = [
            'desayunos', 'solidarios',
            'coles', 'refuerzo', 'escolar',
            'resis', 'abuelitos', 'residencia',
            'dana', 'horta sud',
            'kayak', 'plásticos'
        ]
        mentions_project = any(proj in query_lower for proj in dni_projects)

        return has_ambiguous and not mentions_project

    def save_snapshot(
        self,
        conversation_id: int,
        user_id: int,
        project_context: str,
        detected_topics: List[str],
        message_count: int,
        last_user_query: str,
        snapshot_data: Dict[str, Any]
    ) -> int:
        """
        Guarda un snapshot del contexto actual.

        Args:
            conversation_id: ID de la conversación
            user_id: ID del usuario
            project_context: Proyecto DNI detectado
            detected_topics: Lista de temas detectados
            message_count: Número de mensajes en la conversación
            last_user_query: Última pregunta del usuario
            snapshot_data: Diccionario con estado completo del contexto

        Returns:
            ID del snapshot creado
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO context_snapshots (
                        conversation_id, user_id, project_context,
                        detected_topics, message_count, last_user_query,
                        snapshot_data
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        conversation_id, user_id, project_context,
                        detected_topics, message_count, last_user_query,
                        psycopg2.extras.Json(snapshot_data)
                    )
                )
                snapshot_id = cur.fetchone()[0]
                conn.commit()

                logger.info(
                    f"Saved snapshot {snapshot_id}: conversation={conversation_id}, "
                    f"project={project_context}, msg_count={message_count}"
                )

                return snapshot_id
        finally:
            conn.close()

    def enrich_query_with_context(
        self,
        original_query: str,
        context: ContextData
    ) -> str:
        """
        Enriquece query con prefijo contextual si es necesario.

        Args:
            original_query: Query original del usuario
            context: ContextData recuperado

        Returns:
            Query enriquecida (o original si no debe enriquecer)
        """
        if not context.should_enrich or not context.dominant_project:
            return original_query

        # Mapeo de project_context a nombre legible
        project_names = {
            'desayunos': 'Desayunos Solidarios',
            'resis': 'Charlas con Abuelitos',
            'coles': 'Refuerzo Escolar COLES',
            'dana': 'Rehabilitar Valencia (DANA)',
            'kayak': 'Recogida de Plásticos',
            'general': 'DNI en general'
        }

        project_name = project_names.get(
            context.dominant_project,
            context.dominant_project
        )

        # Construir prefijo
        if context.warning_old_context:
            prefix = f"[Contexto antiguo: {project_name}] "
        else:
            prefix = f"[Contexto: {project_name}] "

        enriched = prefix + original_query

        logger.info(f"Enriched query: '{original_query}' → '{enriched}'")

        return enriched
```

### 4.4 Capa de Servicios (Service Layer Pattern)

#### Justificación Arquitectónica

**Service Layer Pattern** separa la lógica de negocio de la capa de persistencia (DB) y la capa de presentación (Telegram bot).

**Beneficios:**
1. ✅ **Testabilidad:** Servicios pueden mockearse fácilmente
2. ✅ **Reutilización:** Misma lógica para Telegram, WhatsApp, API REST
3. ✅ **Mantenibilidad:** Cambios en DB no afectan lógica de negocio
4. ✅ **Separación de concerns:** Cada servicio tiene responsabilidad única

**Arquitectura:**

```
┌─────────────────────────────────────────┐
│  Telegram Bot / API REST (Presentación) │
└───────────────┬─────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────┐
│        Service Layer (Lógica Negocio)     │
│  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │  User    │  │ Message  │  │ Context │ │
│  │ Service  │  │ Service  │  │ Service │ │
│  └──────────┘  └──────────┘  └─────────┘ │
│  ┌──────────────────────────────────────┐ │
│  │   Conversation Service               │ │
│  └──────────────────────────────────────┘ │
└───────────────┬───────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────┐
│   Data Access Layer (Repositories/DB)     │
└───────────────────────────────────────────┘
```

#### Service 1: UserService

**Responsabilidad:** Gestión de usuarios (CRUD + lógica GDPR).

**Archivo:** `src/services/user_service.py`

```python
"""
User Service - Gestión de usuarios del chatbot.

Author: Vicente
Date: 2025-11-19
"""

import logging
from typing import Optional
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class UserService:
    """Servicio para gestión de usuarios."""

    def __init__(self, db_connection_string: str):
        self.db_connection_string = db_connection_string

    def _get_connection(self):
        return psycopg2.connect(self.db_connection_string)

    def get_or_create_user(
        self,
        telegram_user_id: int,
        first_name: str,
        last_name: Optional[str] = None,
        username: Optional[str] = None,
        language_code: Optional[str] = 'es'
    ) -> dict:
        """
        Obtiene usuario existente o lo crea si no existe.

        Args:
            telegram_user_id: ID de Telegram del usuario
            first_name: Nombre del usuario
            last_name: Apellido (opcional)
            username: @username de Telegram (opcional)
            language_code: Código de idioma (default 'es')

        Returns:
            Diccionario con datos del usuario (incluyendo id interno)
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Intentar obtener usuario existente
                cur.execute(
                    """
                    SELECT * FROM users
                    WHERE telegram_user_id = %s
                    """,
                    (telegram_user_id,)
                )
                user = cur.fetchone()

                if user:
                    # Actualizar last_interaction_at
                    cur.execute(
                        """
                        UPDATE users
                        SET last_interaction_at = NOW()
                        WHERE id = %s
                        """,
                        (user['id'],)
                    )
                    conn.commit()
                    logger.info(f"User {user['id']} interaction updated")
                    return dict(user)

                # Crear nuevo usuario
                cur.execute(
                    """
                    INSERT INTO users (
                        telegram_user_id, first_name, last_name,
                        username, language_code
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (telegram_user_id, first_name, last_name, username, language_code)
                )
                new_user = cur.fetchone()
                conn.commit()

                logger.info(
                    f"Created new user {new_user['id']}: "
                    f"telegram_id={telegram_user_id}, name={first_name}"
                )

                return dict(new_user)
        finally:
            conn.close()

    def delete_user_data(self, user_id: int) -> bool:
        """
        Borra TODOS los datos del usuario (GDPR compliance).

        Utiliza CASCADE delete definido en schema.

        Args:
            user_id: ID interno del usuario

        Returns:
            True si se borró correctamente
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM users WHERE id = %s",
                    (user_id,)
                )
                deleted = cur.rowcount > 0
                conn.commit()

                if deleted:
                    logger.warning(
                        f"GDPR: Deleted all data for user {user_id}"
                    )

                return deleted
        finally:
            conn.close()
```

#### Service 2: ConversationService

**Responsabilidad:** Gestión de conversaciones (crear, obtener activa, archivar).

**Archivo:** `src/services/conversation_service.py`

```python
"""
Conversation Service - Gestión de conversaciones.

Author: Vicente
Date: 2025-11-19
"""

import logging
from typing import Optional
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class ConversationService:
    """Servicio para gestión de conversaciones."""

    def __init__(self, db_connection_string: str):
        self.db_connection_string = db_connection_string

    def _get_connection(self):
        return psycopg2.connect(self.db_connection_string)

    def get_active_conversation(self, user_id: int) -> Optional[dict]:
        """
        Obtiene la conversación activa del usuario.

        Args:
            user_id: ID interno del usuario

        Returns:
            Diccionario con datos de la conversación o None
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT * FROM conversations
                    WHERE user_id = %s AND is_active = TRUE
                    """,
                    (user_id,)
                )
                conv = cur.fetchone()
                return dict(conv) if conv else None
        finally:
            conn.close()

    def create_conversation(
        self,
        user_id: int,
        project_context: str = 'unknown'
    ) -> dict:
        """
        Crea nueva conversación y archiva la anterior si existe.

        Args:
            user_id: ID interno del usuario
            project_context: Proyecto DNI (default 'unknown')

        Returns:
            Diccionario con datos de la nueva conversación
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Archivar conversación activa previa
                cur.execute(
                    """
                    UPDATE conversations
                    SET is_active = FALSE
                    WHERE user_id = %s AND is_active = TRUE
                    """,
                    (user_id,)
                )

                # Crear nueva conversación
                cur.execute(
                    """
                    INSERT INTO conversations (user_id, project_context)
                    VALUES (%s, %s)
                    RETURNING *
                    """,
                    (user_id, project_context)
                )
                new_conv = cur.fetchone()
                conn.commit()

                logger.info(
                    f"Created conversation {new_conv['id']} for user {user_id}"
                )

                return dict(new_conv)
        finally:
            conn.close()

    def update_project_context(
        self,
        conversation_id: int,
        project_context: str
    ):
        """
        Actualiza el proyecto detectado de la conversación.

        Args:
            conversation_id: ID de la conversación
            project_context: Nuevo proyecto DNI
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE conversations
                    SET project_context = %s, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (project_context, conversation_id)
                )
                conn.commit()

                logger.info(
                    f"Updated conversation {conversation_id}: "
                    f"project={project_context}"
                )
        finally:
            conn.close()

    def should_create_new_conversation(
        self,
        current_conversation: Optional[dict],
        inactivity_days: int = 7
    ) -> bool:
        """
        Decide si crear nueva conversación basado en inactividad.

        Args:
            current_conversation: Conversación actual (o None)
            inactivity_days: Días de inactividad para nueva conversación

        Returns:
            True si debe crear nueva conversación
        """
        if not current_conversation:
            return True

        updated_at = current_conversation['updated_at']
        days_inactive = (datetime.now(updated_at.tzinfo) - updated_at).days

        return days_inactive > inactivity_days
```

#### Service 3: MessageService

**Responsabilidad:** Guardar mensajes con metadata completa.

**Archivo:** `src/services/message_service.py`

```python
"""
Message Service - Gestión de mensajes.

Author: Vicente
Date: 2025-11-19
"""

import logging
from typing import Optional, List, Dict, Any

import psycopg2
from psycopg2.extras import RealDictCursor, Json

logger = logging.getLogger(__name__)


class MessageService:
    """Servicio para gestión de mensajes."""

    def __init__(self, db_connection_string: str):
        self.db_connection_string = db_connection_string

    def _get_connection(self):
        return psycopg2.connect(self.db_connection_string)

    def save_user_message(
        self,
        conversation_id: int,
        content: str,
        telegram_message_id: Optional[int] = None
    ) -> int:
        """
        Guarda mensaje del usuario.

        Args:
            conversation_id: ID de la conversación
            content: Contenido del mensaje
            telegram_message_id: ID del mensaje en Telegram

        Returns:
            ID del mensaje guardado
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO messages (
                        conversation_id, role, content, telegram_message_id
                    )
                    VALUES (%s, 'user', %s, %s)
                    RETURNING id
                    """,
                    (conversation_id, content, telegram_message_id)
                )
                message_id = cur.fetchone()[0]
                conn.commit()

                logger.debug(f"Saved user message {message_id}")

                return message_id
        finally:
            conn.close()

    def save_assistant_message(
        self,
        conversation_id: int,
        content: str,
        confidence_score: float,
        retrieval_metadata: Dict[str, Any],
        telegram_message_id: Optional[int] = None
    ) -> int:
        """
        Guarda mensaje del asistente con metadata de RAG.

        Args:
            conversation_id: ID de la conversación
            content: Contenido de la respuesta
            confidence_score: Score de confianza (0.0-1.0)
            retrieval_metadata: Metadata de RAG (chunks, scores, etc.)
            telegram_message_id: ID del mensaje en Telegram

        Returns:
            ID del mensaje guardado
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO messages (
                        conversation_id, role, content,
                        telegram_message_id, confidence_score,
                        retrieval_metadata
                    )
                    VALUES (%s, 'assistant', %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        conversation_id, content, telegram_message_id,
                        confidence_score, Json(retrieval_metadata)
                    )
                )
                message_id = cur.fetchone()[0]
                conn.commit()

                logger.debug(
                    f"Saved assistant message {message_id}: "
                    f"confidence={confidence_score:.3f}"
                )

                return message_id
        finally:
            conn.close()

    def get_conversation_messages(
        self,
        conversation_id: int,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Obtiene mensajes de una conversación.

        Args:
            conversation_id: ID de la conversación
            limit: Número máximo de mensajes

        Returns:
            Lista de mensajes ordenados por created_at DESC
        """
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT * FROM messages
                    WHERE conversation_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (conversation_id, limit)
                )
                messages = cur.fetchall()
                return [dict(msg) for msg in messages]
        finally:
            conn.close()
```

#### Service 4: ContextService

**Responsabilidad:** Integrar PersistentContextManager con lógica de snapshots.

**Archivo:** `src/services/context_service.py`

```python
"""
Context Service - Integración con PersistentContextManager.

Author: Vicente
Date: 2025-11-19
"""

import logging
from typing import Dict, Any, List

from src.core.persistent_context_manager import (
    PersistentContextManager,
    ContextData
)
from src.core.context_tracker import ContextTracker

logger = logging.getLogger(__name__)


class ContextService:
    """
    Servicio de alto nivel para gestión de contexto.

    Integra:
    - PersistentContextManager (DB + decay)
    - ContextTracker (detección de proyectos en tiempo real)
    """

    def __init__(
        self,
        db_connection_string: str,
        snapshot_interval: int = 5  # Snapshot cada N mensajes
    ):
        self.context_manager = PersistentContextManager(db_connection_string)
        self.context_tracker = ContextTracker()
        self.snapshot_interval = snapshot_interval

    def process_user_message(
        self,
        user_id: int,
        conversation_id: int,
        message_count: int,
        query: str,
        conversation_history: List[Dict[str, str]]
    ) -> tuple[str, ContextData]:
        """
        Procesa mensaje del usuario con contexto persistente.

        Args:
            user_id: ID del usuario
            conversation_id: ID de la conversación
            message_count: Número de mensajes en la conversación
            query: Query del usuario
            conversation_history: Historial reciente (últimos 4 turnos)

        Returns:
            (enriched_query, context_data)
        """
        # 1. Recuperar contexto histórico de DB
        historical_context = self.context_manager.retrieve_context(
            user_id=user_id,
            current_query=query
        )

        # 2. Detectar proyecto en conversación actual
        current_context = self.context_tracker.get_context(
            conversation_history=conversation_history
        )

        # 3. Decidir enrichment (prioridad: contexto actual > histórico)
        if current_context['detected_project'] != 'unknown':
            # Hay proyecto detectado en conversación actual
            enriched_query = query  # No enriquecer
            final_context = historical_context
        elif historical_context.should_enrich:
            # Usar contexto histórico
            enriched_query = self.context_manager.enrich_query_with_context(
                query, historical_context
            )
            final_context = historical_context
        else:
            # Sin contexto
            enriched_query = query
            final_context = historical_context

        # 4. Guardar snapshot si toca (cada N mensajes)
        if message_count % self.snapshot_interval == 0:
            self._save_snapshot(
                conversation_id=conversation_id,
                user_id=user_id,
                message_count=message_count,
                current_context=current_context,
                conversation_history=conversation_history
            )

        return enriched_query, final_context

    def _save_snapshot(
        self,
        conversation_id: int,
        user_id: int,
        message_count: int,
        current_context: Dict[str, Any],
        conversation_history: List[Dict[str, str]]
    ):
        """Guarda snapshot del contexto actual."""
        snapshot_data = {
            'project_confidence': current_context.get('project_confidence', 0.0),
            'topic_confidence': current_context.get('topic_confidence', 0.0),
            'last_5_messages': conversation_history[-10:],  # Últimos 5 turnos
            'keywords': current_context.get('keywords', []),
            'context_tracker_state': {
                'window_size': len(conversation_history),
                'projects_detected': [current_context.get('detected_project')],
                'decay_applied': False
            }
        }

        self.context_manager.save_snapshot(
            conversation_id=conversation_id,
            user_id=user_id,
            project_context=current_context.get('detected_project', 'unknown'),
            detected_topics=current_context.get('detected_topic', [])
                if isinstance(current_context.get('detected_topic'), list)
                else [current_context.get('detected_topic', 'general')],
            message_count=message_count,
            last_user_query=conversation_history[-1]['content']
                if conversation_history else '',
            snapshot_data=snapshot_data
        )

        logger.info(f"Saved context snapshot at message {message_count}")
```

---

## 5. INTEGRACIÓN TELEGRAM BOT

### 5.1 Justificación de python-telegram-bot

#### Comparación de Librerías

| Criterio | python-telegram-bot | pyTelegramBotAPI | aiogram | telethon |
|----------|---------------------|------------------|---------|----------|
| **Versión estable** | v20+ (async) | v4+ | v3+ | v1.8+ |
| **Async/await** | ✅ Nativo | ⚠️ Parcial | ✅ Nativo | ✅ Nativo |
| **Documentación** | ✅ Excelente | ⚠️ Básica | ✅ Buena | ⚠️ Compleja |
| **Type hints** | ✅ Completo | ❌ Limitado | ✅ Bueno | ⚠️ Parcial |
| **Handler pattern** | ✅ Flexible | ⚠️ Básico | ✅ Routers | ❌ Manual |
| **Inline keyboards** | ✅ Built-in | ✅ Built-in | ✅ Built-in | ✅ Built-in |
| **File uploads** | ✅ Simplificado | ✅ Manual | ✅ Bueno | ✅ Complejo |
| **Comunidad** | ✅ 25k+ estrellas | ✅ 7k+ estrellas | ✅ 4k+ estrellas | ✅ 9k+ estrellas |
| **Mantenimiento** | ✅ Activo | ✅ Activo | ✅ Activo | ✅ Activo |

**Decisión:** python-telegram-bot (v20+) seleccionado por:
1. ✅ Async/await nativo (compatible con FastAPI existente)
2. ✅ Type hints completos (mypy strict compliance)
3. ✅ Documentación excelente (crítico para TFG)
4. ✅ Handler pattern flexible (CommandHandler, MessageHandler, etc.)
5. ✅ Comunidad más grande y madura

### 5.2 Arquitectura del Bot

#### Componentes Principales

```
┌─────────────────────────────────────────────────────┐
│           TelegramBotApplication                    │
│  ┌──────────────────────────────────────────────┐  │
│  │  Application.builder().token(TOKEN).build()  │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  Handlers (Dispatcher)                       │  │
│  │  ┌────────────┐  ┌─────────────┐  ┌────────┐│  │
│  │  │ Command    │  │ Message     │  │Callback││  │
│  │  │ Handler    │  │ Handler     │  │ Query  ││  │
│  │  │ /start     │  │ text msgs   │  │Handler ││  │
│  │  │ /help      │  │             │  │buttons ││  │
│  │  │ /reset     │  │             │  │        ││  │
│  │  └────────────┘  └─────────────┘  └────────┘│  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  Business Logic Layer                        │  │
│  │  • UserService                               │  │
│  │  • ConversationService                       │  │
│  │  • MessageService                            │  │
│  │  • ContextService                            │  │
│  │  • ConversationalRAG                         │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### 5.3 Implementación del Bot

**Archivo:** `interface/telegram_bot/bot.py`

```python
"""
Telegram Bot para Chatbot DNI con persistencia cross-sesión.

Implementa:
- Comandos: /start, /help, /reset, /history, /delete_data, /feedback
- Message handler para conversación
- Inline keyboards para sugerencias
- Integración completa con Service Layer

Author: Vicente
Date: 2025-11-19
"""

import logging
import os
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

from src.services.user_service import UserService
from src.services.conversation_service import ConversationService
from src.services.message_service import MessageService
from src.services.context_service import ContextService
from src.core.conversational_rag import ConversationalRAG
from src.core.question_suggester import QuestionSuggester

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class DNITelegramBot:
    """Bot de Telegram para DNI con persistencia cross-sesión."""

    def __init__(
        self,
        telegram_token: str,
        db_connection_string: str
    ):
        """
        Args:
            telegram_token: Token del bot de Telegram (BotFather)
            db_connection_string: PostgreSQL connection string
        """
        self.token = telegram_token

        # Inicializar servicios
        self.user_service = UserService(db_connection_string)
        self.conversation_service = ConversationService(db_connection_string)
        self.message_service = MessageService(db_connection_string)
        self.context_service = ContextService(db_connection_string)

        # Inicializar RAG y suggester
        self.conversational_rag = ConversationalRAG()
        self.question_suggester = QuestionSuggester()

        # Build application
        self.application = Application.builder().token(self.token).build()

        # Register handlers
        self._register_handlers()

        logger.info("DNITelegramBot initialized")

    def _register_handlers(self):
        """Registra todos los handlers del bot."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("reset", self.reset_command))
        self.application.add_handler(CommandHandler("history", self.history_command))
        self.application.add_handler(CommandHandler("delete_data", self.delete_data_command))
        self.application.add_handler(CommandHandler("feedback", self.feedback_command))

        # Message handler (debe ser último para catch-all)
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler)
        )

        # Callback query handler (inline keyboards)
        self.application.add_handler(CallbackQueryHandler(self.button_callback))

        logger.info("Handlers registered")

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handler para /start.

        Muestra mensaje de bienvenida y registra usuario.
        """
        user = update.effective_user
        telegram_user_id = user.id

        # Registrar/obtener usuario
        db_user = self.user_service.get_or_create_user(
            telegram_user_id=telegram_user_id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
            language_code=user.language_code or 'es'
        )

        welcome_message = f"""
👋 ¡Hola {user.first_name}! Soy el asistente virtual de **DNI (Damos Nuestra Ilusión)**.

🎯 **Qué puedo hacer:**
• Responder preguntas sobre nuestros proyectos
• Recordar conversaciones anteriores
• Ayudarte a participar como voluntario

🔹 **Proyectos DNI:**
🍞 Desayunos Solidarios
👴 Charlas con Abuelitos (RESIS)
📚 Refuerzo Escolar (COLES)
🏗️ Rehabilitar Valencia (DANA)
🚣 Recogida de Plásticos

💬 **Pregúntame lo que quieras** sobre cualquier proyecto.

ℹ️ Usa /help para ver todos los comandos disponibles.

---
⚠️ **Privacidad:** Almaceno tus conversaciones para recordar el contexto.
Puedes borrar todos tus datos en cualquier momento con /delete_data.
"""

        await update.message.reply_text(welcome_message, parse_mode='Markdown')

        logger.info(f"User {db_user['id']} started bot (telegram_id={telegram_user_id})")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler para /help."""
        help_text = """
📖 **Comandos disponibles:**

/start - Iniciar el bot y ver bienvenida
/help - Mostrar esta ayuda
/reset - Iniciar conversación nueva (borrar contexto actual)
/history - Ver tus últimas conversaciones
/delete_data - ⚠️ Borrar TODOS tus datos (GDPR)
/feedback - Enviar feedback sobre el bot

💡 **Consejos:**
• Puedo recordar conversaciones anteriores (hasta 30 días)
• Si preguntas algo ambiguo ("¿a qué hora era?"), intentaré recordar el contexto
• Las respuestas tienen un score de confianza (0-100%)

❓ **Ejemplos de preguntas:**
• ¿Qué es DNI?
• ¿Cuándo son los Desayunos Solidarios?
• ¿Cómo puedo participar en COLES?
• ¿Dónde está la residencia L'Acollida?

🔗 **Contacto directo:**
Instagram: @dni.vlc
Email: dni.vlc@gmail.com
"""

        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def reset_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handler para /reset.

        Cierra conversación actual y crea una nueva.
        """
        user = update.effective_user
        db_user = self.user_service.get_or_create_user(
            telegram_user_id=user.id,
            first_name=user.first_name
        )

        # Crear nueva conversación (automáticamente cierra la anterior)
        new_conversation = self.conversation_service.create_conversation(
            user_id=db_user['id']
        )

        await update.message.reply_text(
            "✅ Conversación reiniciada.\n\n"
            "He olvidado el contexto actual. ¿En qué puedo ayudarte?",
            parse_mode='Markdown'
        )

        logger.info(f"User {db_user['id']} reset conversation → new conv_id={new_conversation['id']}")

    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handler para /history.

        Muestra últimas 5 conversaciones del usuario.
        """
        user = update.effective_user
        db_user = self.user_service.get_or_create_user(
            telegram_user_id=user.id,
            first_name=user.first_name
        )

        # TODO: Implementar query para obtener últimas conversaciones
        # Por ahora, mensaje placeholder

        await update.message.reply_text(
            "📋 **Tu historial de conversaciones:**\n\n"
            "🔜 Funcionalidad en desarrollo...\n\n"
            "Próximamente podrás ver tus últimas conversaciones y exportarlas.",
            parse_mode='Markdown'
        )

    async def delete_data_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handler para /delete_data.

        Borra TODOS los datos del usuario (GDPR compliance).
        """
        user = update.effective_user
        db_user = self.user_service.get_or_create_user(
            telegram_user_id=user.id,
            first_name=user.first_name
        )

        # Confirmación con inline keyboard
        keyboard = [
            [
                InlineKeyboardButton("✅ Sí, borrar TODO", callback_data=f"delete_confirm_{db_user['id']}"),
                InlineKeyboardButton("❌ Cancelar", callback_data="delete_cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "⚠️ **¿Estás seguro?**\n\n"
            "Esta acción borrará:\n"
            "• Todas tus conversaciones\n"
            "• Todos tus mensajes\n"
            "• Todo tu contexto histórico\n"
            "• Tu registro de usuario\n\n"
            "**Esta acción NO se puede deshacer.**",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def feedback_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler para /feedback."""
        await update.message.reply_text(
            "💬 **Enviar feedback:**\n\n"
            "Envía tu feedback escribiendo:\n"
            "`/feedback Tu mensaje aquí`\n\n"
            "O contáctanos directamente:\n"
            "📧 dni.vlc@gmail.com\n"
            "📱 Instagram: @dni.vlc",
            parse_mode='Markdown'
        )

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handler principal para mensajes de texto.

        Flujo:
        1. Obtener/crear usuario
        2. Obtener/crear conversación
        3. Guardar mensaje del usuario
        4. Recuperar contexto histórico
        5. Generar respuesta con RAG
        6. Guardar respuesta
        7. Enviar respuesta + sugerencias (opcional)
        """
        user = update.effective_user
        user_message = update.message.text

        # 1. Obtener/crear usuario
        db_user = self.user_service.get_or_create_user(
            telegram_user_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username
        )

        # 2. Obtener/crear conversación
        active_conv = self.conversation_service.get_active_conversation(db_user['id'])

        if not active_conv or self.conversation_service.should_create_new_conversation(active_conv):
            active_conv = self.conversation_service.create_conversation(db_user['id'])

        # 3. Guardar mensaje del usuario
        user_msg_id = self.message_service.save_user_message(
            conversation_id=active_conv['id'],
            content=user_message,
            telegram_message_id=update.message.message_id
        )

        # 4. Obtener historial de la conversación
        conversation_messages = self.message_service.get_conversation_messages(
            conversation_id=active_conv['id'],
            limit=10  # Últimos 10 mensajes (5 turnos)
        )

        # Formatear para ContextService
        conversation_history = [
            {'role': msg['role'], 'content': msg['content']}
            for msg in reversed(conversation_messages)  # Orden cronológico
        ]

        # 5. Procesar mensaje con contexto persistente
        enriched_query, historical_context = self.context_service.process_user_message(
            user_id=db_user['id'],
            conversation_id=active_conv['id'],
            message_count=len(conversation_messages) + 1,
            query=user_message,
            conversation_history=conversation_history
        )

        # 6. Generar respuesta con RAG (forzar question_id=0)
        await update.message.chat.send_action("typing")

        rag_response = self.conversational_rag.generate_response(
            query=enriched_query,
            conversation_history=conversation_history,
            question_id=0  # Forzar RAG avanzado
        )

        answer = rag_response['answer']
        confidence = rag_response.get('confidence', 0.7)

        # 7. Guardar respuesta del asistente
        assistant_msg_id = self.message_service.save_assistant_message(
            conversation_id=active_conv['id'],
            content=answer,
            confidence_score=confidence,
            retrieval_metadata={
                'enriched_query': enriched_query,
                'historical_context_used': historical_context.should_enrich,
                'dominant_project': historical_context.dominant_project,
                'project_confidence': historical_context.project_confidence,
                'max_context_weight': historical_context.max_weight,
                'raw_rag_response': rag_response
            }
        )

        # 8. Actualizar project_context si detectado
        current_project = rag_response.get('detected_project', 'unknown')
        if current_project != 'unknown' and current_project != active_conv['project_context']:
            self.conversation_service.update_project_context(
                conversation_id=active_conv['id'],
                project_context=current_project
            )

        # 9. Enviar respuesta
        await update.message.reply_text(answer, parse_mode='Markdown')

        # 10. Sugerencias de preguntas (solo si conversación corta)
        if len(conversation_messages) < 10:
            suggestions = self.question_suggester.get_suggestions(
                query=user_message,
                detected_project=current_project,
                num_suggestions=3
            )

            if suggestions:
                keyboard = [
                    [InlineKeyboardButton(sugg, callback_data=f"suggest_{i}")]
                    for i, sugg in enumerate(suggestions)
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.message.reply_text(
                    "💡 También puedes preguntar:",
                    reply_markup=reply_markup
                )

        logger.info(
            f"User {db_user['id']} message processed: "
            f"confidence={confidence:.3f}, enriched={historical_context.should_enrich}"
        )

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handler para callbacks de inline keyboards.

        Maneja:
        - Confirmación de borrado de datos
        - Sugerencias de preguntas
        """
        query = update.callback_query
        await query.answer()

        callback_data = query.data

        # Borrado de datos
        if callback_data.startswith("delete_confirm_"):
            user_id = int(callback_data.split("_")[2])

            # Borrar datos
            deleted = self.user_service.delete_user_data(user_id)

            if deleted:
                await query.edit_message_text(
                    "✅ **Datos borrados correctamente.**\n\n"
                    "Todos tus datos han sido eliminados de nuestra base de datos.\n\n"
                    "Puedes volver a usar el bot cuando quieras con /start.",
                    parse_mode='Markdown'
                )
                logger.warning(f"GDPR: User {user_id} deleted all data")
            else:
                await query.edit_message_text(
                    "❌ Error al borrar datos. Por favor, contacta con dni.vlc@gmail.com"
                )

        elif callback_data == "delete_cancel":
            await query.edit_message_text(
                "✅ Operación cancelada. Tus datos están seguros."
            )

        elif callback_data.startswith("suggest_"):
            # Usuario clickeó sugerencia
            suggestion_text = query.message.reply_markup.inline_keyboard[int(callback_data.split("_")[1])][0].text

            # Simular mensaje del usuario
            await query.edit_message_text(f"Preguntaste: {suggestion_text}")

            # Procesar como mensaje normal (reutilizar message_handler logic)
            # Nota: Requiere crear un Update sintético - simplificado aquí
            await query.message.reply_text(
                f"🔄 Procesando: _{suggestion_text}_\n\n"
                "🔜 Funcionalidad en desarrollo...",
                parse_mode='Markdown'
            )

    def run(self, webhook: bool = False, webhook_url: Optional[str] = None):
        """
        Inicia el bot.

        Args:
            webhook: Si True, usa webhook. Si False, usa long polling.
            webhook_url: URL del webhook (requerido si webhook=True)
        """
        if webhook:
            if not webhook_url:
                raise ValueError("webhook_url required when webhook=True")

            logger.info(f"Starting bot with webhook: {webhook_url}")
            self.application.run_webhook(
                listen="0.0.0.0",
                port=8443,
                url_path=self.token,
                webhook_url=f"{webhook_url}/{self.token}"
            )
        else:
            logger.info("Starting bot with long polling")
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Entry point."""
    # Configuración desde environment variables
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    DB_CONNECTION_STRING = os.getenv(
        "DATABASE_URL",
        "postgresql://chatbot_user:password@localhost:5432/chatbot_dni_db"
    )

    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")

    # Inicializar y ejecutar bot
    bot = DNITelegramBot(
        telegram_token=TELEGRAM_TOKEN,
        db_connection_string=DB_CONNECTION_STRING
    )

    # Long polling (desarrollo) o webhook (producción)
    USE_WEBHOOK = os.getenv("USE_WEBHOOK", "false").lower() == "true"
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")

    bot.run(webhook=USE_WEBHOOK, webhook_url=WEBHOOK_URL)


if __name__ == "__main__":
    main()
```

### 5.4 Comandos del Bot

#### Tabla de Comandos

| Comando | Descripción | Prioridad | Respuesta Esperada |
|---------|-------------|-----------|-------------------|
| `/start` | Mensaje de bienvenida + registro de usuario | ALTA | Texto markdown con info DNI + aviso GDPR |
| `/help` | Ayuda completa | ALTA | Lista de comandos + ejemplos |
| `/reset` | Reiniciar conversación (borrar contexto actual) | MEDIA | Confirmación + conversación nueva |
| `/history` | Ver últimas 5 conversaciones | BAJA | Lista con fechas y proyectos |
| `/delete_data` | Borrar TODOS los datos (GDPR) | ALTA | Inline keyboard confirmación |
| `/feedback` | Enviar feedback | BAJA | Instrucciones para contacto |

---

## 6. API REST (Opcional - Fuera de MVP)

### 6.1 Justificación

**Propósito:** Permitir integración externa y gestión administrativa del chatbot.

**Casos de uso:**
- Dashboard web para monitoreo de métricas
- Exportación de conversaciones (usuarios avanzados)
- Administración de usuarios (GDPR compliance)
- Integración futura con WhatsApp Business API

### 6.2 Endpoints Principales

**Archivo:** `interface/telegram_bot/api.py`

```python
"""
API REST para gestión del Chatbot DNI.

Endpoints:
- GET /api/users/{user_id} - Obtener info de usuario
- GET /api/conversations/{conversation_id} - Obtener conversación
- POST /api/query - Generar respuesta (sin Telegram)
- DELETE /api/users/{user_id} - Borrar datos GDPR

Author: Vicente
Date: 2025-11-19
"""

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional

from src.services.user_service import UserService
from src.services.conversation_service import ConversationService
from src.services.message_service import MessageService

app = FastAPI(title="Chatbot DNI API", version="1.0.0")

# TODO: Implementar autenticación (API keys, OAuth2, etc.)

class QueryRequest(BaseModel):
    """Request para generar respuesta."""
    query: str
    user_id: Optional[int] = None
    conversation_id: Optional[int] = None


class QueryResponse(BaseModel):
    """Response de respuesta generada."""
    answer: str
    confidence: float
    sources: List[str]


@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    """Obtener información de usuario."""
    # TODO: Implementar
    raise HTTPException(status_code=501, detail="Not implemented")


@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int):
    """Borrar datos de usuario (GDPR)."""
    # TODO: Implementar con autenticación
    raise HTTPException(status_code=501, detail="Not implemented")


@app.post("/api/query", response_model=QueryResponse)
async def generate_query(request: QueryRequest):
    """Generar respuesta a query (sin Telegram)."""
    # TODO: Implementar
    raise HTTPException(status_code=501, detail="Not implemented")
```

---

## 7. ESTRATEGIA DE TESTING

### 7.1 Pirámide de Testing

```
           ╱╲
          ╱  ╲
         ╱ E2E╲         5% - End-to-End (bot completo)
        ╱──────╲
       ╱        ╲
      ╱Integration╲     25% - Integration (Service Layer + DB)
     ╱────────────╲
    ╱              ╲
   ╱  Unit Tests    ╲   70% - Unit (lógica aislada)
  ╱──────────────────╲
```

### 7.2 Unit Tests

**Objetivo:** Testear lógica de negocio aislada (sin DB, sin Telegram).

**Coverage mínimo:** 85%

**Ejemplo:** `tests/unit/test_persistent_context_manager.py`

```python
"""
Unit tests para PersistentContextManager.

Mockea DB con pytest fixtures.

Author: Vicente
Date: 2025-11-19
"""

import pytest
import math
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from src.core.persistent_context_manager import (
    PersistentContextManager,
    ContextSnapshot,
    ContextData
)


@pytest.fixture
def context_manager():
    """Fixture: PersistentContextManager con DB mockeada."""
    with patch('src.core.persistent_context_manager.psycopg2.connect'):
        manager = PersistentContextManager(
            db_connection_string="mock://db",
            half_life_days=3.0
        )
        return manager


def test_calculate_decay_weight(context_manager):
    """Test decay weight calculation."""
    # Half-life = 3 días
    # λ = ln(2) / 3 ≈ 0.231

    # Día 0: weight = 1.0
    assert context_manager.calculate_decay_weight(0) == pytest.approx(1.0, abs=0.001)

    # Día 3 (half-life): weight = 0.5
    assert context_manager.calculate_decay_weight(3) == pytest.approx(0.5, abs=0.001)

    # Día 6 (2x half-life): weight = 0.25
    assert context_manager.calculate_decay_weight(6) == pytest.approx(0.25, abs=0.001)

    # Día 10: weight = 0.1
    assert context_manager.calculate_decay_weight(10) == pytest.approx(0.1, abs=0.01)


def test_is_query_ambiguous(context_manager):
    """Test detección de queries ambiguas."""
    # Queries ambiguas (contienen pattern pero NO proyecto)
    assert context_manager._is_query_ambiguous("¿A qué hora era?") is True
    assert context_manager._is_query_ambiguous("¿Dónde quedamos?") is True
    assert context_manager._is_query_ambiguous("¿Quién organiza?") is True

    # Queries NO ambiguas (mencionan proyecto)
    assert context_manager._is_query_ambiguous("¿A qué hora son los desayunos?") is False
    assert context_manager._is_query_ambiguous("¿Dónde es COLES?") is False

    # Queries NO ambiguas (no contienen pattern)
    assert context_manager._is_query_ambiguous("¿Qué es DNI?") is False


def test_enrich_query_with_context(context_manager):
    """Test enrichment de query."""
    # Context con proyecto detectado y should_enrich=True
    context = ContextData(
        dominant_project='desayunos',
        project_confidence=0.85,
        should_enrich=True,
        snapshots=[],
        max_weight=0.6,
        warning_old_context=False
    )

    enriched = context_manager.enrich_query_with_context(
        "¿A qué hora era?",
        context
    )

    assert enriched == "[Contexto: Desayunos Solidarios] ¿A qué hora era?"

    # Context sin enrichment
    context_no_enrich = ContextData(
        dominant_project=None,
        project_confidence=0.0,
        should_enrich=False,
        snapshots=[],
        max_weight=0.0,
        warning_old_context=False
    )

    enriched_no = context_manager.enrich_query_with_context(
        "¿Qué es DNI?",
        context_no_enrich
    )

    assert enriched_no == "¿Qué es DNI?"  # Sin cambios


def test_retrieve_context_no_history(context_manager):
    """Test retrieval cuando usuario no tiene historial."""
    # Mockear DB query que devuelve vacío
    with patch.object(context_manager, '_get_connection') as mock_conn:
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_conn.return_value.__enter__.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        result = context_manager.retrieve_context(
            user_id=999,  # Usuario sin historial
            current_query="¿Qué es DNI?"
        )

        assert result.dominant_project is None
        assert result.project_confidence == 0.0
        assert result.should_enrich is False
        assert len(result.snapshots) == 0
        assert result.max_weight == 0.0
```

### 7.3 Integration Tests

**Objetivo:** Testear interacción entre componentes (Service Layer + DB real).

**Requiere:** PostgreSQL test database.

**Ejemplo:** `tests/integration/test_conversation_flow.py`

```python
"""
Integration tests para flujo completo de conversación.

Usa PostgreSQL test database (Docker).

Author: Vicente
Date: 2025-11-19
"""

import pytest
import psycopg2
from datetime import datetime

from src.services.user_service import UserService
from src.services.conversation_service import ConversationService
from src.services.message_service import MessageService
from src.services.context_service import ContextService


@pytest.fixture(scope="module")
def test_db():
    """Fixture: PostgreSQL test database."""
    # Conectar a test DB
    conn_string = "postgresql://test_user:test_pass@localhost:5433/test_chatbot_db"
    conn = psycopg2.connect(conn_string)

    # Setup: crear tablas (ejecutar migrations)
    # TODO: Ejecutar Alembic migrations

    yield conn_string

    # Teardown: limpiar DB
    conn.close()


def test_complete_conversation_flow(test_db):
    """
    Test flujo completo:
    1. Crear usuario
    2. Crear conversación
    3. Guardar mensaje usuario
    4. Guardar mensaje asistente
    5. Verificar contexto guardado
    """
    # Inicializar servicios
    user_service = UserService(test_db)
    conv_service = ConversationService(test_db)
    msg_service = MessageService(test_db)

    # 1. Crear usuario
    user = user_service.get_or_create_user(
        telegram_user_id=123456789,
        first_name="Test",
        last_name="User"
    )

    assert user['id'] is not None
    assert user['telegram_user_id'] == 123456789

    # 2. Crear conversación
    conv = conv_service.create_conversation(
        user_id=user['id'],
        project_context='desayunos'
    )

    assert conv['id'] is not None
    assert conv['project_context'] == 'desayunos'
    assert conv['is_active'] is True

    # 3. Guardar mensaje usuario
    user_msg_id = msg_service.save_user_message(
        conversation_id=conv['id'],
        content="¿Cuándo son los desayunos?"
    )

    assert user_msg_id is not None

    # 4. Guardar mensaje asistente
    assistant_msg_id = msg_service.save_assistant_message(
        conversation_id=conv['id'],
        content="Los Desayunos Solidarios son todos los sábados a las 8:00 AM...",
        confidence_score=0.87,
        retrieval_metadata={'chunks_used': 10}
    )

    assert assistant_msg_id is not None

    # 5. Verificar mensajes guardados
    messages = msg_service.get_conversation_messages(conv['id'])

    assert len(messages) == 2
    assert messages[0]['role'] == 'assistant'  # Orden DESC
    assert messages[1]['role'] == 'user'

    # Cleanup
    user_service.delete_user_data(user['id'])
```

### 7.4 End-to-End Tests

**Objetivo:** Testear bot completo con Telegram API.

**Requiere:** Bot de prueba en Telegram + cuenta de test.

**Herramienta:** pytest-telegram-bot

**Ejemplo:** `tests/e2e/test_telegram_bot.py`

```python
"""
E2E tests para Telegram bot.

Requiere bot de prueba y TELEGRAM_TEST_TOKEN.

Author: Vicente
Date: 2025-11-19
"""

import pytest
from telegram import Update
from telegram.ext import ApplicationBuilder

# TODO: Implementar E2E tests con bot real
# Requiere configuración adicional
```

### 7.5 Coverage Report

**Comando:**

```bash
# Ejecutar todos los tests con coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term

# Coverage mínimo requerido: 85%
# Target TFG: 90%+
```

---

## 8. DEPLOYMENT E INFRAESTRUCTURA

### 8.1 Docker Compose

**Archivo:** `docker-compose.yml`

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:14
    container_name: chatbot_dni_db
    environment:
      POSTGRES_USER: chatbot_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: chatbot_dni_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U chatbot_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Telegram Bot
  telegram_bot:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: chatbot_dni_telegram
    environment:
      TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN}
      DATABASE_URL: postgresql://chatbot_user:${DB_PASSWORD}@postgres:5432/chatbot_dni_db
      USE_WEBHOOK: ${USE_WEBHOOK:-false}
      WEBHOOK_URL: ${WEBHOOK_URL:-}
      LOG_LEVEL: INFO
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs

  # Adminer (DB admin tool - opcional)
  adminer:
    image: adminer
    container_name: chatbot_dni_adminer
    ports:
      - "8080:8080"
    depends_on:
      - postgres

volumes:
  postgres_data:
```

**Archivo:** `Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY src/ ./src/
COPY interface/ ./interface/
COPY data/ ./data/

# Crear directorio de logs
RUN mkdir -p /app/logs

# Comando por defecto
CMD ["python", "-m", "interface.telegram_bot.bot"]
```

**Archivo:** `.env.example`

```bash
# PostgreSQL
DB_PASSWORD=your_secure_password_here

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# Deployment
USE_WEBHOOK=false
WEBHOOK_URL=https://yourdomain.com

# Opcional
LOG_LEVEL=INFO
```

### 8.2 Deployment en Producción

#### Opción 1: VPS (DigitalOcean, Hetzner, etc.)

**Requisitos mínimos:**
- CPU: 2 cores
- RAM: 4 GB
- Almacenamiento: 20 GB SSD
- OS: Ubuntu 22.04 LTS

**Pasos:**

```bash
# 1. Clonar repositorio
git clone https://github.com/your-org/rag-optimizer.git
cd rag-optimizer

# 2. Configurar environment
cp .env.example .env
nano .env  # Editar con valores reales

# 3. Iniciar servicios
docker-compose up -d

# 4. Ver logs
docker-compose logs -f telegram_bot

# 5. Ejecutar migrations
docker-compose exec telegram_bot alembic upgrade head
```

#### Opción 2: Railway / Render (PaaS)

**Ventajas:**
- ✅ Deployment automático desde Git
- ✅ PostgreSQL managed incluido
- ✅ HTTPS automático
- ✅ Free tier disponible (testing)

**Desventajas:**
- ❌ Costo mayor a escala
- ❌ Menos control

---

## 9. PRIVACIDAD Y GDPR

### 9.1 Checklist de Compliance

| Requisito GDPR | Implementación | Estado |
|----------------|----------------|--------|
| **Consentimiento explícito** | Mensaje en /start avisando de almacenamiento | ✅ Implementado |
| **Derecho al olvido** | Comando /delete_data con CASCADE delete | ✅ Implementado |
| **Minimización de datos** | Solo almacenamos telegram_user_id, nombre, mensajes | ✅ Cumplido |
| **Data retention** | Auto-borrado después de 90 días inactividad | ✅ Cron job |
| **Encryption at rest** | PostgreSQL con pgcrypto (opcional) | ⚠️ Recomendado |
| **Encryption in transit** | TLS para DB connections, HTTPS para webhook | ✅ Implementado |
| **Transparencia** | Comando /help explica qué datos almacenamos | ✅ Implementado |
| **Exportación de datos** | Comando /history (pendiente MVP) | ⏳ Futuro |

### 9.2 Política de Privacidad (Ejemplo)

**Texto para mostrar en /start:**

```
⚠️ PRIVACIDAD Y DATOS:

Este bot almacena:
• Tu nombre de Telegram
• Tus conversaciones (mensajes enviados y recibidos)
• Contexto conversacional (proyectos detectados)

NO almacenamos:
❌ Tu número de teléfono
❌ Tu ubicación
❌ Información sensible

Tus datos se utilizan SOLO para:
✅ Recordar conversaciones previas (hasta 30 días)
✅ Mejorar la calidad de las respuestas

Tus derechos:
• Borrar tus datos: /delete_data
• Exportar tus datos: /history
• Contacto: dni.vlc@gmail.com

Al usar este bot, aceptas esta política.
```

---

## 10. GESTIÓN DE RIESGOS

### 10.1 Tabla de Riesgos

| ID | Riesgo | Probabilidad | Impacto | Mitigación | Responsable |
|----|--------|--------------|---------|------------|-------------|
| R1 | **Caída de servidor UPV Ollama** | Media | Alto | Implementar retry logic + fallback a respuesta predefinida | Dev |
| R2 | **DB PostgreSQL llena disco** | Baja | Crítico | Monitoreo de espacio + cleanup job mensual | DevOps |
| R3 | **Telegram API rate limit** | Media | Medio | Implementar exponential backoff + queue de mensajes | Dev |
| R4 | **Context decay incorrecto** | Baja | Medio | Unit tests exhaustivos + validación con usuarios reales | Dev |
| R5 | **Fuga de datos (GDPR)** | Muy baja | Crítico | Encryption at rest + access control + auditoría | Security |
| R6 | **Usuario abuse (spam)** | Media | Bajo | Rate limiting por usuario (5 msg/min) | Dev |
| R7 | **Costos de infraestructura** | Media | Medio | Monitoreo de costos + alertas + optimización queries | DevOps |
| R8 | **Pérdida de conexión DB** | Baja | Alto | Connection pooling + retry logic + health checks | Dev |

### 10.2 Plan de Contingencia

#### Scenario: Servidor Ollama UPV caído

**Detección:**
- Health check cada 60s: `curl https://ollama.gti-ia.upv.es/api/health`
- Timeout > 10s → considerado caído

**Acciones:**
1. **Inmediato (0-5 min):**
   - Activar fallback a respuesta predefinida:
     ```
     "⚠️ El sistema está experimentando problemas técnicos.
     Por favor, contacta directamente con DNI:
     📧 dni.vlc@gmail.com | 📱 @dni.vlc"
     ```

2. **Corto plazo (5-30 min):**
   - Notificar a administradores (email/Telegram)
   - Verificar si es problema de red UPV

3. **Largo plazo (>30 min):**
   - Considerar migración temporal a modelo local (gemma2:2b)
   - Comunicación a usuarios via mensaje broadcast

---

## 11. TIMELINE DETALLADO (12 SEMANAS)

### Fase 1: DISEÑO Y FUNDAMENTOS (Semanas 1-4)

#### **Semana 1: Documentación y Diseño**
- [x] Actualizar CLAUDE.md con historial completo ✅
- [x] Crear TELEGRAM_INTEGRATION_SPEC.md (PARTES 1-4) ✅
- [ ] Diseñar diagramas de arquitectura (Mermaid)
- [ ] Crear .github/BRANCH_STRATEGY.md
- [ ] Configurar GitHub Project board (Kanban)

**Entregables:** Documentación técnica completa (2,500+ líneas)

#### **Semana 2: Setup de Infraestructura**
- [ ] Configurar PostgreSQL local con Docker
- [ ] Ejecutar Alembic migrations (schema inicial)
- [ ] Poblar DB con datos de prueba (10 usuarios, 50 mensajes)
- [ ] Configurar pgAdmin para monitoreo
- [ ] Escribir script de backup automatizado

**Entregables:** DB funcional + scripts de gestión

#### **Semana 3: Implementar Service Layer**
- [ ] Implementar UserService completo
- [ ] Implementar ConversationService completo
- [ ] Implementar MessageService completo
- [ ] Escribir unit tests para cada servicio (coverage >85%)
- [ ] Documentar API de cada servicio (docstrings)

**Entregables:** 4 servicios + tests

#### **Semana 4: Implementar PersistentContextManager**
- [ ] Implementar PersistentContextManager (380 líneas)
- [ ] Implementar ContextService (integración)
- [ ] Escribir unit tests (decay, retrieval, enrichment)
- [ ] Benchmark de performance (context retrieval <50ms)
- [ ] Validar con datos sintéticos (100 snapshots)

**Entregables:** Context management completo + benchmarks

---

### Fase 2: IMPLEMENTACIÓN CORE (Semanas 5-8)

#### **Semana 5: Telegram Bot - Comandos Básicos**
- [ ] Setup python-telegram-bot (v20+)
- [ ] Implementar handlers: /start, /help, /reset
- [ ] Implementar message_handler (sin RAG)
- [ ] Conectar con UserService + ConversationService
- [ ] Testing manual con bot de prueba

**Entregables:** Bot funcional (sin RAG)

#### **Semana 6: Integración RAG + Contexto**
- [ ] Integrar ConversationalRAG existente
- [ ] Conectar ContextService con bot
- [ ] Implementar query enrichment end-to-end
- [ ] Guardar metadata completa en DB
- [ ] Testing con conversaciones multi-día

**Entregables:** Bot con RAG + contexto persistente

#### **Semana 7: Comandos Avanzados + UX**
- [ ] Implementar /history con paginación
- [ ] Implementar /delete_data con confirmación
- [ ] Implementar inline keyboards (sugerencias)
- [ ] Añadir typing indicator ("escribiendo...")
- [ ] Mejorar mensajes de error

**Entregables:** UX pulida

#### **Semana 8: Integration Tests**
- [ ] Escribir integration tests (Service Layer + DB)
- [ ] Escribir E2E tests (bot completo)
- [ ] Configurar pytest con fixtures
- [ ] Alcanzar coverage >85%
- [ ] Documentar casos de test

**Entregables:** Suite de tests completa

---

### Fase 3: TESTING, DEPLOYMENT Y DOCUMENTACIÓN TFG (Semanas 9-12)

#### **Semana 9: Testing con Usuarios Reales**
- [ ] Desplegar bot en servidor de prueba
- [ ] Invitar 5-10 voluntarios DNI a testear
- [ ] Recopilar feedback cualitativo
- [ ] Analizar métricas (confidence, context retrieval accuracy)
- [ ] Iterar basado en feedback

**Entregables:** Informe de testing (usuarios reales)

#### **Semana 10: Deployment en Producción**
- [ ] Configurar VPS (DigitalOcean/Hetzner)
- [ ] Setup Docker Compose en producción
- [ ] Configurar SSL/TLS (Let's Encrypt)
- [ ] Configurar backup automático de DB
- [ ] Monitoreo básico (logs, uptime)

**Entregables:** Sistema en producción

#### **Semana 11: Documentación TFG**
- [ ] Redactar capítulo 1: Introducción
- [ ] Redactar capítulo 2: Estado del Arte
- [ ] Redactar capítulo 3: Diseño del Sistema
- [ ] Redactar capítulo 4: Implementación
- [ ] Redactar capítulo 5: Evaluación

**Entregables:** Borrador TFG (70% completo)

#### **Semana 12: Finalización y Presentación**
- [ ] Redactar capítulo 6: Conclusiones
- [ ] Revisar y corregir documento completo
- [ ] Preparar presentación (slides)
- [ ] Ensayar presentación (15-20 min)
- [ ] Envío de TFG

**Entregables:** TFG final + presentación

---

## 12. MÉTRICAS DE ÉXITO

### 12.1 Métricas Técnicas

| Métrica | Target | Crítico | Medición |
|---------|--------|---------|----------|
| **Response time** | <3s | <6s | P95 latency |
| **Context retrieval accuracy** | >80% | >70% | Manual eval (50 queries) |
| **Cross-session memory recall** | >70% | >60% | Benchmark automatizado |
| **Confidence score variabilidad** | σ > 0.1 | σ > 0.05 | Desviación estándar |
| **DB query time** | <300ms | <1s | PostgreSQL EXPLAIN |
| **Coverage de tests** | >90% | >85% | pytest --cov |
| **Uptime** | >99% | >95% | UptimeRobot |

### 12.2 Métricas de Usuario (Post-Launch)

| Métrica | Target | Medición |
|---------|--------|----------|
| **Daily Active Users** | 20+ | Telegram Analytics |
| **Avg messages/user/day** | 3-5 | DB analytics |
| **User satisfaction** | >80% positive feedback | /feedback ratings |
| **Context usage rate** | >40% queries use historical context | DB logs |
| **Data deletion requests** | <5% users | /delete_data count |

---

## 13. ANEXO: DIAGRAMAS MERMAID DETALLADOS

Esta sección presenta todos los diagramas arquitectónicos y de flujo del sistema en formato Mermaid para facilitar la comprensión visual del diseño completo.

### 13.1 Arquitectura del Sistema (C4 Container View)

#### Diagrama de Arquitectura Completa

```mermaid
graph TB
    subgraph "Usuario Final"
        U1[Usuario Telegram<br/>📱 Mobile/Desktop]
    end

    subgraph "Telegram Infrastructure"
        TS[Telegram Server<br/>🌐 Bot API]
    end

    subgraph "Application Layer - Docker Compose"
        subgraph "Telegram Bot Container"
            TB[TelegramBotService<br/>🤖 python-telegram-bot]
            IH[Intent Handler]
            FH[Feedback Handler]
            CH[Command Handlers<br/>/start /help /reset]
        end

        subgraph "Service Layer"
            US[UserService<br/>👤 User CRUD]
            CS[ConversationService<br/>💬 Conversation CRUD]
            MS[MessageService<br/>📝 Message CRUD]
            CTX[ContextService<br/>🧠 Context Management]
        end

        subgraph "RAG Engine"
            PCM[PersistentContextManager<br/>⏰ Decay + Enrichment]
            CRAG[ConversationalRAG<br/>📚 Context Tracker]
            ERAG[EnhancedRAGEngineNew<br/>🔍 Confidence + Validation]
            CRAG2[ConfigurableRAGEngine<br/>⚖️ Hybrid Search]
        end
    end

    subgraph "Data Layer"
        subgraph "PostgreSQL Container"
            PG[(PostgreSQL 14+<br/>💾 Persistent Storage)]
            T1[users table]
            T2[conversations table]
            T3[messages table]
            T4[context_snapshots table]
            T5[feedback table]
            T6[user_consents table]
        end

        subgraph "Vector Store"
            CHR[(ChromaDB<br/>🗂️ 263 chunks)]
            EMB[mpnet-768dim<br/>Embeddings]
        end
    end

    subgraph "External Services"
        OLL[Ollama Server UPV<br/>🧠 gemma2:27b<br/>ollama.gti-ia.upv.es]
    end

    subgraph "Monitoring & Admin"
        ADM[Adminer<br/>📊 DB Admin UI]
        LOG[Logging System<br/>📋 Structured Logs]
    end

    %% Flujo principal
    U1 -->|Mensajes| TS
    TS -->|Updates<br/>Long Polling/Webhook| TB
    TB --> IH
    TB --> FH
    TB --> CH

    %% Service Layer
    TB --> US
    TB --> CS
    TB --> MS
    TB --> CTX

    %% Context Management
    CTX --> PCM
    CTX --> CRAG

    %% RAG Pipeline
    CRAG --> ERAG
    ERAG --> CRAG2
    CRAG2 --> CHR
    CRAG2 --> EMB

    %% LLM Generation
    ERAG --> OLL

    %% Database Access
    US --> PG
    CS --> PG
    MS --> PG
    CTX --> PG
    PCM --> PG

    PG --> T1
    PG --> T2
    PG --> T3
    PG --> T4
    PG --> T5
    PG --> T6

    %% Admin
    ADM -.->|Visualización| PG
    TB -.->|Logs| LOG

    %% Response Flow
    TB -->|Respuestas| TS
    TS -->|Deliver| U1

    classDef userClass fill:#e1f5ff,stroke:#0066cc,stroke-width:2px
    classDef botClass fill:#fff4e1,stroke:#ff9900,stroke-width:2px
    classDef serviceClass fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    classDef dataClass fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px
    classDef externalClass fill:#ffebee,stroke:#f44336,stroke-width:2px

    class U1 userClass
    class TB,IH,FH,CH botClass
    class US,CS,MS,CTX,PCM,CRAG,ERAG,CRAG2 serviceClass
    class PG,T1,T2,T3,T4,T5,T6,CHR,EMB dataClass
    class OLL,TS externalClass
```

#### Leyenda del Diagrama

| Componente | Responsabilidad | Tecnología |
|------------|----------------|------------|
| **TelegramBotService** | Orchestración de mensajes, routing | python-telegram-bot v20+ |
| **UserService** | Gestión de usuarios (CRUD) | SQLAlchemy ORM |
| **ConversationService** | Gestión de conversaciones | SQLAlchemy ORM |
| **MessageService** | Guardar/recuperar mensajes | SQLAlchemy ORM |
| **ContextService** | Integración context manager + RAG | Custom (src/core) |
| **PersistentContextManager** | Decay exponencial + query enrichment | Custom (math.exp) |
| **ConversationalRAG** | Context tracker + historial | Custom (v3.3 adapted) |
| **EnhancedRAGEngineNew** | Confidence dinámico (6 factores) | Custom (v3.3) |
| **ConfigurableRAGEngine** | Hybrid search (BM25 + Semantic) | ChromaDB + BM25Retriever |
| **PostgreSQL** | Persistencia transaccional | PostgreSQL 14+ |
| **ChromaDB** | Vector store | ChromaDB 1.0+ |
| **Ollama** | LLM inference | gemma2:27b (UPV server) |

---

### 13.2 Diagrama Entidad-Relación (Mermaid)

#### ER Diagram Completo

```mermaid
erDiagram
    users ||--o{ conversations : "has many"
    users ||--o{ context_snapshots : "has many"
    users ||--o{ feedback : "submits"
    users ||--o{ user_consents : "gives"
    users ||--o{ analytics_events : "generates"

    conversations ||--o{ messages : "contains"
    conversations ||--o{ context_snapshots : "has snapshots"

    messages ||--o| feedback : "receives feedback"

    users {
        bigint id PK
        bigint telegram_user_id UK "NOT NULL"
        varchar first_name "NOT NULL"
        varchar last_name
        varchar username
        varchar language_code
        timestamp created_at "DEFAULT NOW()"
        timestamp last_interaction_at "DEFAULT NOW()"
        boolean is_active "DEFAULT TRUE"
    }

    conversations {
        bigint id PK
        bigint user_id FK "NOT NULL"
        enum project_context "desayunos|resis|coles|dana|kayak|general|unknown"
        timestamp created_at "DEFAULT NOW()"
        timestamp updated_at "DEFAULT NOW()"
        boolean is_active "DEFAULT TRUE"
    }

    messages {
        bigint id PK
        bigint conversation_id FK "NOT NULL"
        enum role "user|assistant"
        text content "NOT NULL"
        jsonb metadata "confidence, chunks, sources"
        float confidence_score
        timestamp created_at "DEFAULT NOW()"
    }

    context_snapshots {
        bigint id PK
        bigint user_id FK "NOT NULL"
        bigint conversation_id FK "NOT NULL"
        enum project_context
        jsonb detected_entities "projects, topics, keywords"
        int message_count
        text summary
        timestamp created_at "DEFAULT NOW()"
        timestamp updated_at "DEFAULT NOW()"
    }

    feedback {
        bigint id PK
        bigint user_id FK "NOT NULL"
        bigint message_id FK "NULL"
        enum rating "positive|negative"
        text comment
        timestamp created_at "DEFAULT NOW()"
    }

    user_consents {
        bigint id PK
        bigint user_id FK "NOT NULL"
        enum consent_type "data_processing|analytics"
        boolean granted "NOT NULL"
        timestamp granted_at "DEFAULT NOW()"
        timestamp revoked_at "NULL"
    }

    analytics_events {
        bigint id PK
        bigint user_id FK "NOT NULL"
        varchar event_type "message_sent|command_used|error_occurred"
        jsonb event_data
        timestamp created_at "DEFAULT NOW()"
    }
```

#### Relaciones Clave

| Relación | Cardinalidad | Constraint | Propósito |
|----------|--------------|------------|-----------|
| users → conversations | 1:N | CASCADE DELETE | Usuario elimina todas sus conversaciones |
| conversations → messages | 1:N | CASCADE DELETE | Conversación elimina todos sus mensajes |
| users → context_snapshots | 1:N | CASCADE DELETE | Usuario elimina todos sus snapshots |
| conversations → context_snapshots | 1:N | CASCADE DELETE | Conversación elimina snapshots asociados |
| messages → feedback | 1:0..1 | SET NULL | Borrar mensaje no borra feedback (analytics) |
| users → feedback | 1:N | CASCADE DELETE | Usuario elimina todo su feedback |

---

### 13.3 Flujos de Datos Completos

#### Flujo 3: Registro de Usuario Nuevo (/start)

```mermaid
sequenceDiagram
    participant U as Usuario
    participant TB as TelegramBot
    participant US as UserService
    participant CS as ConversationService
    participant DB as PostgreSQL
    participant UCS as UserConsentService

    U->>TB: /start

    rect rgb(240, 248, 255)
        Note over TB,US: FASE 1: Verificar Usuario
        TB->>US: get_or_create_user(telegram_user_id, first_name, ...)
        US->>DB: SELECT * FROM users WHERE telegram_user_id = ?

        alt Usuario NO existe
            DB-->>US: NULL
            US->>DB: INSERT INTO users (telegram_user_id, first_name, created_at)
            DB-->>US: User{id=1, telegram_user_id=12345, ...}

            US->>UCS: create_default_consents(user_id=1)
            UCS->>DB: INSERT INTO user_consents (user_id, consent_type='data_processing', granted=TRUE)
            DB-->>UCS: ✅ Consent created

        else Usuario existe
            DB-->>US: User{id=1, ...}
            US->>DB: UPDATE users SET last_interaction_at = NOW() WHERE id = 1
        end

        US-->>TB: User{id=1, telegram_user_id=12345, first_name="Juan"}
    end

    rect rgb(255, 250, 240)
        Note over TB,CS: FASE 2: Crear Primera Conversación
        TB->>CS: create_conversation(user_id=1, project_context='unknown')
        CS->>DB: INSERT INTO conversations (user_id, project_context, created_at)
        DB-->>CS: Conversation{id=1, user_id=1, project_context='unknown'}
        CS-->>TB: Conversation{id=1}
    end

    rect rgb(240, 255, 240)
        Note over TB,U: FASE 3: Mensaje de Bienvenida + GDPR Notice
        TB->>U: 🎉 ¡Hola Juan! Soy el chatbot de DNI...<br/><br/>📋 AVISO DE PRIVACIDAD:<br/>• Guardamos tu historial de conversación<br/>• Puedes borrar tus datos con /delete_data<br/>• Datos se eliminan automáticamente tras 90 días<br/><br/>¿En qué puedo ayudarte hoy?
    end

    rect rgb(255, 240, 245)
        Note over TB,U: FASE 4: Sugerencias Inline Keyboard
        TB->>U: InlineKeyboard:<br/>• "¿Qué es DNI?"<br/>• "¿Cómo participar?"<br/>• "Proyectos activos"
    end
```

#### Flujo 4: Procesamiento de Mensaje con Context Enrichment

```mermaid
sequenceDiagram
    participant U as Usuario
    participant TB as TelegramBot
    participant MS as MessageService
    participant PCM as PersistentContextManager
    participant CRAG as ConversationalRAG
    participant ERAG as EnhancedRAGEngine
    participant CHR as ChromaDB
    participant OLL as Ollama
    participant DB as PostgreSQL

    U->>TB: "¿A qué hora era?"

    rect rgb(255, 250, 240)
        Note over TB,MS: PASO 1: Guardar Mensaje Usuario
        TB->>MS: save_user_message(conversation_id=1, content="¿A qué hora era?")
        MS->>DB: INSERT INTO messages (conversation_id, role='user', content, created_at)
        DB-->>MS: Message{id=42, ...}
    end

    rect rgb(240, 248, 255)
        Note over TB,PCM: PASO 2: Recuperar Contexto Histórico
        TB->>PCM: retrieve_context(user_id=1, current_query="¿A qué hora era?")

        PCM->>DB: SELECT cs.*, c.updated_at, c.project_context<br/>FROM context_snapshots cs<br/>JOIN conversations c ON cs.conversation_id = c.id<br/>WHERE cs.user_id = 1<br/>AND c.updated_at > NOW() - INTERVAL '30 days'<br/>ORDER BY c.updated_at DESC<br/>LIMIT 10

        DB-->>PCM: [<br/>  {project='Desayunos', updated_at='5 days ago', message_count=8},<br/>  {project='RESIS', updated_at='10 days ago', message_count=5}<br/>]

        loop Para cada snapshot
            PCM->>PCM: days_ago = (NOW() - updated_at).days<br/>weight = exp(-0.231 * days_ago)
            Note over PCM: Desayunos: weight = exp(-0.231 * 5) = 0.315<br/>RESIS: weight = exp(-0.231 * 10) = 0.099
        end

        PCM->>PCM: filter(weight > 0.01)
        PCM->>PCM: Proyecto dominante = max(weight) = 'Desayunos' (0.315)

        alt Confianza alta (weight > 0.2) + Query ambigua
            PCM->>PCM: enrich_query = "[Contexto: Desayunos Solidarios] ¿A qué hora era?"
            PCM-->>TB: ContextData{<br/>  enriched_query="[Contexto: Desayunos...] ¿A qué hora era?",<br/>  historical_context=[...],<br/>  dominant_project='Desayunos',<br/>  should_enrich=True<br/>}
        else Confianza baja o query específica
            PCM-->>TB: ContextData{<br/>  enriched_query="¿A qué hora era?",<br/>  should_enrich=False<br/>}
        end
    end

    rect rgb(240, 255, 240)
        Note over TB,OLL: PASO 3: Generar Respuesta con RAG
        TB->>CRAG: generate_response(<br/>  query="[Contexto: Desayunos...] ¿A qué hora era?",<br/>  context_data=ContextData{...}<br/>)

        CRAG->>ERAG: retrieve_with_rag(enriched_query)
        ERAG->>CHR: hybrid_search(query, k=10, threshold=0.30)
        CHR-->>ERAG: [chunk1, chunk2, ...] (12 chunks relevantes)

        ERAG->>ERAG: cross_encoder_rerank(chunks)
        ERAG->>ERAG: select_top_k(5)

        ERAG->>OLL: POST /api/generate<br/>{<br/>  model: "gemma2:27b",<br/>  prompt: "Contexto: [chunks]...<br/>           Pregunta: ¿A qué hora era?",<br/>  temperature: 0.2<br/>}

        OLL-->>ERAG: {<br/>  response: "Los Desayunos Solidarios se realizan<br/>            a las 8:00 AM todos los domingos..."<br/>}

        ERAG->>ERAG: calculate_confidence(<br/>  num_chunks=12,<br/>  answer_length=234,<br/>  has_negative=False,<br/>  specificity_patterns=2,<br/>  context_overlap=0.78,<br/>  keyword_coverage=0.85<br/>)

        ERAG-->>CRAG: {<br/>  answer="Los Desayunos Solidarios...",<br/>  confidence=0.863,<br/>  sources=["07_desayunos_logistica.txt"]<br/>}

        CRAG-->>TB: RAGResponse{answer, confidence, sources}
    end

    rect rgb(255, 240, 245)
        Note over TB,DB: PASO 4: Guardar Respuesta + Actualizar Snapshot
        TB->>MS: save_assistant_message(<br/>  conversation_id=1,<br/>  content="Los Desayunos Solidarios...",<br/>  confidence=0.863,<br/>  metadata={sources: [...], chunks: 12}<br/>)

        MS->>DB: INSERT INTO messages (<br/>  conversation_id, role='assistant',<br/>  content, confidence_score, metadata, created_at<br/>)

        TB->>PCM: save_context_snapshot(<br/>  user_id=1,<br/>  conversation_id=1,<br/>  detected_project='Desayunos',<br/>  message_count=9<br/>)

        alt Cada 5 mensajes
            PCM->>DB: INSERT INTO context_snapshots (...)<br/>ON CONFLICT (user_id, conversation_id)<br/>DO UPDATE SET message_count=9, updated_at=NOW()
        end
    end

    rect rgb(250, 250, 255)
        Note over TB,U: PASO 5: Enviar Respuesta + Sugerencias
        TB->>U: 📅 Los Desayunos Solidarios se realizan<br/>a las 8:00 AM todos los domingos...<br/><br/>📍 Punto de encuentro:<br/>Carrer de Sagunt, 177, Valencia

        TB->>U: InlineKeyboard (sugerencias contextuales):<br/>• "¿Qué necesito llevar?"<br/>• "¿Cómo llego al punto de encuentro?"<br/>• "¿Puedo ir aunque sea mi primera vez?"
    end
```

#### Flujo 5: GDPR Data Deletion (/delete_data)

```mermaid
sequenceDiagram
    participant U as Usuario
    participant TB as TelegramBot
    participant US as UserService
    participant DB as PostgreSQL

    U->>TB: /delete_data

    rect rgb(255, 240, 240)
        Note over TB,U: PASO 1: Confirmación Inline Keyboard
        TB->>U: ⚠️ ADVERTENCIA: Esta acción es IRREVERSIBLE<br/><br/>Se borrarán:<br/>• Todo tu historial de conversaciones<br/>• Todos tus mensajes<br/>• Tus preferencias<br/>• Tus datos personales<br/><br/>¿Estás seguro?<br/><br/>InlineKeyboard:<br/>[✅ Sí, borrar TODO] [❌ Cancelar]
    end

    alt Usuario confirma
        U->>TB: Click "✅ Sí, borrar TODO"

        rect rgb(240, 248, 255)
            Note over TB,DB: PASO 2: Borrado en Cascada
            TB->>US: delete_user_data(telegram_user_id=12345)

            US->>DB: BEGIN TRANSACTION

            Note over DB: CASCADE DELETE automático
            US->>DB: DELETE FROM users WHERE telegram_user_id = 12345

            DB->>DB: CASCADE DELETE conversations WHERE user_id = ?
            DB->>DB: CASCADE DELETE messages WHERE conversation_id IN (...)
            DB->>DB: CASCADE DELETE context_snapshots WHERE user_id = ?
            DB->>DB: CASCADE DELETE feedback WHERE user_id = ?
            DB->>DB: CASCADE DELETE user_consents WHERE user_id = ?
            DB->>DB: CASCADE DELETE analytics_events WHERE user_id = ?

            US->>DB: COMMIT TRANSACTION

            DB-->>US: ✅ Deleted (67 rows affected)
            US-->>TB: DeletionResult{success=True, rows_deleted=67}
        end

        rect rgb(240, 255, 240)
            Note over TB,U: PASO 3: Confirmación + Logout
            TB->>U: ✅ Tus datos han sido eliminados completamente.<br/><br/>Puedes volver a usar /start en cualquier momento.
        end

    else Usuario cancela
        U->>TB: Click "❌ Cancelar"
        TB->>U: Operación cancelada. Tus datos siguen guardados.
    end
```

---

### 13.4 Diagramas de Estado

#### Estado del Ciclo de Vida de Conversaciones

```mermaid
stateDiagram-v2
    [*] --> New: Usuario envía primer mensaje

    New --> Active: Conversación creada

    Active --> Active: Usuario envía mensajes<br/>(< 5 días inactividad)

    Active --> Dormant: 5+ días sin mensajes

    Dormant --> Active: Usuario envía nuevo mensaje<br/>(context weight > 0.2)

    Dormant --> Archived: Usuario envía /reset<br/>o context weight < 0.01

    Active --> Archived: Usuario envía /reset

    Archived --> [*]: 90 días sin actividad<br/>(auto-cleanup)

    Active --> [*]: Usuario ejecuta /delete_data
    Dormant --> [*]: Usuario ejecuta /delete_data
    Archived --> [*]: Usuario ejecuta /delete_data

    note right of Active
        is_active = TRUE
        updated_at se actualiza
        project_context se detecta
    end note

    note right of Dormant
        is_active = TRUE
        context decay aplicado
        weight = exp(-λ * days)
    end note

    note right of Archived
        is_active = FALSE
        no aparece en /history
        solo visible en DB
    end note
```

#### Estado del Ciclo de Vida de Usuarios

```mermaid
stateDiagram-v2
    [*] --> Unregistered: Usuario no conocido

    Unregistered --> Registered: /start (primer uso)

    Registered --> Active: Interacciones regulares<br/>(< 7 días desde última)

    Active --> Active: Envía mensajes

    Active --> Idle: 7-30 días sin mensajes

    Idle --> Active: Usuario vuelve

    Idle --> Inactive: 30-90 días sin mensajes

    Inactive --> Active: Usuario vuelve

    Inactive --> Anonymized: 90+ días sin mensajes<br/>(auto-cleanup)

    Registered --> Deleted: /delete_data
    Active --> Deleted: /delete_data
    Idle --> Deleted: /delete_data
    Inactive --> Deleted: /delete_data

    Deleted --> [*]: Datos eliminados (CASCADE)
    Anonymized --> [*]: Datos anonimizados

    note right of Registered
        Consent dado
        first_name guardado
        is_active = TRUE
    end note

    note right of Active
        last_interaction_at actualizado
        Conversaciones activas
    end note

    note right of Anonymized
        first_name = "Usuario Inactivo"
        last_name = NULL
        username = NULL
        is_active = FALSE
    end note
```

#### Máquina de Estados del Procesamiento de Mensajes

```mermaid
stateDiagram-v2
    [*] --> Received: Telegram Update recibido

    Received --> ValidatingUser: Extraer telegram_user_id

    ValidatingUser --> LoadingContext: Usuario válido
    ValidatingUser --> Error: Usuario inválido

    LoadingContext --> CheckingIntent: Contexto cargado (weight calculado)

    CheckingIntent --> HandlingCommand: Intent = command (/start, /help, etc.)
    CheckingIntent --> ProcessingQuestion: Intent = question
    CheckingIntent --> HandlingGreeting: Intent = greeting

    HandlingCommand --> SendingResponse: Comando ejecutado
    HandlingGreeting --> SendingResponse: Saludo generado

    ProcessingQuestion --> EnrichingQuery: Context weight > 0.2 + ambiguous query
    ProcessingQuestion --> RetrievingRAG: Query específica o weight < 0.2

    EnrichingQuery --> RetrievingRAG: Query enriquecida

    RetrievingRAG --> GeneratingLLM: Chunks recuperados (k=10-15)

    GeneratingLLM --> CalculatingConfidence: Respuesta generada

    CalculatingConfidence --> SavingMessage: Confidence calculado (6 factors)

    SavingMessage --> UpdatingSnapshot: Mensaje guardado en DB

    UpdatingSnapshot --> GeneratingSuggestions: Snapshot actualizado (cada 5 msg)
    UpdatingSnapshot --> SendingResponse: No es múltiplo de 5

    GeneratingSuggestions --> SendingResponse: Sugerencias contextuales generadas

    SendingResponse --> [*]: Respuesta enviada + InlineKeyboard

    Error --> SendingError: Generar mensaje de error
    SendingError --> [*]: Error notificado al usuario

    note right of EnrichingQuery
        Prefix: "[Contexto: Desayunos]"
        Mejora retrieval accuracy
    end note

    note right of CalculatingConfidence
        6 factores ponderados:
        1. Num chunks
        2. Answer length
        3. No negativos
        4. Especificidad
        5. Context overlap
        6. Keyword coverage
    end note
```

---

### 13.5 Arquitectura de Deployment (Docker Compose)

```mermaid
graph TB
    subgraph "Host Machine - VPS (DigitalOcean/Hetzner)"
        subgraph "Docker Network: chatbot_network"

            subgraph "Container: telegram_bot"
                BOT[Python App<br/>FastAPI + python-telegram-bot<br/>Port: 8000 internal]
                VENV[venv/<br/>Python 3.12]
                SRC[src/<br/>Service Layer + RAG]
                DATA[data/<br/>vectorstore/chroma_db]
            end

            subgraph "Container: postgres"
                PG[PostgreSQL 14<br/>Port: 5432 internal]
                PGDATA[/var/lib/postgresql/data<br/>Volume: postgres_data]
            end

            subgraph "Container: adminer (opcional)"
                ADM[Adminer UI<br/>Port: 8080 → Host 8080]
            end

            subgraph "Volumes (Docker Managed)"
                VOL1[(postgres_data<br/>Persistent DB)]
                VOL2[(chroma_data<br/>Vector Store)]
                VOL3[(logs<br/>Application Logs)]
            end
        end

        subgraph "Host Network"
            NGINX[Nginx Reverse Proxy<br/>SSL/TLS (Let's Encrypt)<br/>Port 443]
            UFW[UFW Firewall<br/>Allow: 22, 80, 443]
        end
    end

    subgraph "External Services"
        TG[Telegram Server<br/>api.telegram.org]
        OLL[Ollama UPV<br/>ollama.gti-ia.upv.es:443]
    end

    %% Connections
    TG -->|Webhook HTTPS| NGINX
    NGINX -->|Proxy to :8000| BOT

    BOT -->|Long Polling<br/>getUpdates API| TG
    BOT -->|SQL Queries| PG
    BOT -->|Vector Search| DATA
    BOT -->|LLM Generate| OLL

    PG -->|Persist| PGDATA
    PGDATA -.->|Mounted| VOL1
    DATA -.->|Mounted| VOL2
    BOT -.->|Write Logs| VOL3

    ADM -.->|Connect :5432| PG

    %% Health Checks
    BOT -.->|Health Check<br/>pg_isready| PG

    classDef containerClass fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef volumeClass fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef externalClass fill:#ffebee,stroke:#c62828,stroke-width:2px
    classDef networkClass fill:#e8f5e9,stroke:#388e3c,stroke-width:2px

    class BOT,PG,ADM containerClass
    class VOL1,VOL2,VOL3,PGDATA volumeClass
    class TG,OLL externalClass
    class NGINX,UFW networkClass
```

#### Comandos Docker Compose

```bash
# Iniciar todos los servicios
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f telegram_bot

# Verificar health checks
docker-compose ps

# Ejecutar migraciones Alembic
docker-compose exec telegram_bot alembic upgrade head

# Backup de base de datos
docker-compose exec postgres pg_dump -U chatbot_user chatbot_dni_db > backup_$(date +%Y%m%d).sql

# Restore de backup
docker-compose exec -T postgres psql -U chatbot_user chatbot_dni_db < backup_20251119.sql

# Detener servicios
docker-compose down

# Detener y borrar volúmenes (CUIDADO!)
docker-compose down -v
```

---

### 13.6 Diagrama de Decisión: Query Enrichment

```mermaid
flowchart TD
    Start([Nueva Query de Usuario]) --> LoadContext[Cargar Contexto Histórico<br/>últimos 30 días]

    LoadContext --> CalcWeights[Calcular Decay Weights<br/>weight = exp-λ * days_ago]

    CalcWeights --> FilterWeights{¿Algún snapshot<br/>con weight > 0.01?}

    FilterWeights -->|NO| NoEnrich[No Enrich Query<br/>use_original_query = True]
    FilterWeights -->|SÍ| FindDominant[Encontrar Proyecto Dominante<br/>max_weight_project]

    FindDominant --> CheckWeight{¿max_weight > 0.2?}

    CheckWeight -->|NO| NoEnrich
    CheckWeight -->|SÍ| CheckAmbiguity{¿Query es ambigua?<br/>Detectar pronombres,<br/>referencias temporales}

    CheckAmbiguity -->|NO<br/>Query específica| NoEnrich
    CheckAmbiguity -->|SÍ<br/>Query ambigua| EnrichQuery[Enriquecer Query<br/>Prefix: Contexto: dominant_project<br/>enriched_query]

    EnrichQuery --> LogDecision[Log: Query enriched<br/>original → enriched<br/>reason: dominant_project]

    NoEnrich --> LogNoDecision[Log: Query NOT enriched<br/>reason: insufficient_weight<br/>or specific_query]

    LogDecision --> RAGRetrieval[Enviar a RAG Engine<br/>enriched_query]
    LogNoDecision --> RAGRetrieval

    RAGRetrieval --> End([Continuar con<br/>Generación LLM])

    style Start fill:#e1f5ff
    style End fill:#e1f5ff
    style EnrichQuery fill:#c8e6c9,stroke:#2e7d32,stroke-width:3px
    style NoEnrich fill:#ffccbc,stroke:#d84315,stroke-width:2px
    style CheckWeight fill:#fff9c4
    style CheckAmbiguity fill:#fff9c4
```

#### Ejemplos de Query Enrichment

| Query Original | Contexto Dominante | Weight | Ambigua? | Query Enriquecida | Decisión |
|----------------|-------------------|--------|----------|-------------------|----------|
| "¿A qué hora era?" | Desayunos (5 días) | 0.315 | ✅ Sí | `[Contexto: Desayunos Solidarios] ¿A qué hora era?` | ✅ Enrich |
| "¿Dónde se queda la gente?" | RESIS (3 días) | 0.500 | ✅ Sí | `[Contexto: RESIS (Charlas Abuelitos)] ¿Dónde se queda la gente?` | ✅ Enrich |
| "Horario de Desayunos Solidarios" | COLES (10 días) | 0.100 | ❌ No | `Horario de Desayunos Solidarios` | ❌ NO Enrich (específica) |
| "¿Qué necesito llevar?" | General (15 días) | 0.050 | ✅ Sí | `¿Qué necesito llevar?` | ❌ NO Enrich (weight < 0.2) |
| "¿Es la primera vez que participáis?" | Ninguno | 0.000 | ✅ Sí | `¿Es la primera vez que participáis?` | ❌ NO Enrich (sin contexto) |

---

### 13.7 Diagrama de Componentes RAG Pipeline

```mermaid
flowchart LR
    subgraph "Input Layer"
        Q[User Query<br/>"¿A qué hora era?"]
        CTX[Historical Context<br/>weight=0.315<br/>project=Desayunos]
    end

    subgraph "Context Processing"
        PCM[PersistentContextManager]
        PCM --> DECAY[Decay Calculation<br/>exp-0.231 * days]
        PCM --> ENRICH[Query Enrichment<br/>Decision Logic]

        DECAY --> FILTER[Filter weight > 0.01]
        FILTER --> ENRICH
    end

    subgraph "RAG Engine"
        CRAG[ConversationalRAG<br/>Context Tracker]

        CRAG --> BM25[BM25 Retriever<br/>Keyword Matching]
        CRAG --> SEM[Semantic Retriever<br/>mpnet-768dim]

        BM25 --> HYBRID[Hybrid Merge<br/>50% BM25 + 50% Semantic]
        SEM --> HYBRID

        HYBRID --> RERANK[Cross-Encoder Reranker<br/>Rerank top-20 → top-10]
    end

    subgraph "Vector Store"
        CHR[(ChromaDB<br/>263 chunks)]
        EMB[Embeddings<br/>mpnet-768dim]
    end

    subgraph "LLM Generation"
        PROMPT[Prompt Builder<br/>System + Context + Query]
        OLL[Ollama gemma2:27b<br/>Temperature=0.2]

        PROMPT --> OLL
    end

    subgraph "Validation & Confidence"
        CONF[Confidence Calculator<br/>6 Factors]

        CONF --> F1[Factor 1: Num Chunks<br/>12 chunks → 0.15]
        CONF --> F2[Factor 2: Answer Length<br/>234 chars → 0.12]
        CONF --> F3[Factor 3: No Negativos<br/>✅ → 0.20]
        CONF --> F4[Factor 4: Especificidad<br/>2 patterns → 0.18]
        CONF --> F5[Factor 5: Context Overlap<br/>0.78 → 0.20]
        CONF --> F6[Factor 6: Keyword Coverage<br/>0.85 → 0.15]

        F1 --> SUM[Σ = 0.863]
        F2 --> SUM
        F3 --> SUM
        F4 --> SUM
        F5 --> SUM
        F6 --> SUM
    end

    subgraph "Output Layer"
        RESP[Final Response<br/>answer + confidence + sources]
    end

    %% Flow
    Q --> PCM
    CTX --> PCM

    ENRICH --> CRAG

    BM25 -.->|Query| CHR
    SEM -.->|Embedding| EMB
    EMB -.->|Search| CHR
    CHR -.->|Results| HYBRID

    RERANK --> PROMPT
    PROMPT --> OLL
    OLL --> CONF

    SUM --> RESP

    classDef inputClass fill:#e1f5ff,stroke:#0277bd
    classDef processClass fill:#fff9c4,stroke:#f57f17
    classDef ragClass fill:#c8e6c9,stroke:#388e3c
    classDef llmClass fill:#f8bbd0,stroke:#c2185b
    classDef outputClass fill:#e1bee7,stroke:#7b1fa2

    class Q,CTX inputClass
    class PCM,DECAY,ENRICH,FILTER processClass
    class CRAG,BM25,SEM,HYBRID,RERANK,CHR,EMB ragClass
    class PROMPT,OLL,CONF,F1,F2,F3,F4,F5,F6,SUM llmClass
    class RESP outputClass
```

---

### 13.8 Timeline Visual del Proyecto (Gantt)

```mermaid
gantt
    title Timeline de Implementación - Chatbot DNI v4.0 Telegram
    dateFormat YYYY-MM-DD
    section Fase 1: Fundamentos
    PostgreSQL Schema Design     :done, schema, 2025-11-19, 3d
    Alembic Migrations Setup     :done, alembic, after schema, 2d
    Service Layer (CRUD)         :active, services, 2025-11-24, 5d
    Unit Tests (Service Layer)   :tests1, after services, 3d

    section Fase 2: Context Management
    PersistentContextManager     :context, 2025-12-02, 5d
    Context Decay Implementation :decay, after context, 3d
    Query Enrichment Logic       :enrich, after decay, 3d
    Integration Tests (Context)  :tests2, after enrich, 3d

    section Fase 3: Telegram Bot
    TelegramBotService Setup     :bot, 2025-12-11, 4d
    Command Handlers             :commands, after bot, 3d
    Message Handler Integration  :messages, after commands, 4d
    Inline Keyboards             :keyboards, after messages, 2d
    E2E Tests (Bot)             :tests3, after keyboards, 3d

    section Fase 4: API REST (opcional)
    FastAPI Endpoints            :api, 2025-12-24, 3d
    API Documentation            :docs_api, after api, 2d

    section Fase 5: Testing & QA
    User Testing (5-10 users)    :crit, user_test, 2026-01-02, 7d
    Bug Fixes & Iteration        :fixes, after user_test, 5d

    section Fase 6: Deployment
    Docker Compose Setup         :docker, 2026-01-14, 3d
    VPS Configuration            :vps, after docker, 2d
    SSL/TLS Setup                :ssl, after vps, 1d
    Production Deployment        :milestone, deploy, after ssl, 1d

    section Fase 7: Documentación TFG
    Redacción Capítulos 1-3      :tfg1, 2026-01-18, 7d
    Redacción Capítulos 4-6      :tfg2, after tfg1, 7d
    Revisión y Presentación      :crit, tfg3, after tfg2, 4d
    Entrega Final TFG            :milestone, entrega, 2026-02-05, 1d
```

---

## 14. CONCLUSIONES DEL DISEÑO

### 13.1 Resumen de Decisiones Técnicas

| Decisión | Justificación | Trade-off |
|----------|---------------|-----------|
| **PostgreSQL** | ACID compliance, relaciones complejas, JSONB | Mayor complejidad vs SQLite |
| **python-telegram-bot** | Async nativo, type hints, docs excelentes | Curva de aprendizaje vs librerías simples |
| **Exponential decay (3 días)** | Balance memoria corto/largo plazo para DNI | Configuración manual vs ML adaptativo |
| **Service Layer Pattern** | Testabilidad, reutilización | Más código vs lógica directa |
| **Snapshots cada 5 mensajes** | Balance performance/granularidad | Storage vs precisión |
| **Long polling (desarrollo)** | Simplicidad setup | Latencia vs webhook |

### 13.2 Contribuciones del Proyecto

**Académicas:**
1. ✅ Diseño completo de sistema RAG con persistencia cross-sesión
2. ✅ Implementación de context decay exponencial (justificado matemáticamente)
3. ✅ Evaluación rigurosa con métricas cuantitativas (coverage >85%)

**Prácticas:**
1. ✅ Chatbot production-ready para asociación real (DNI Valencia)
2. ✅ Código reutilizable para otros proyectos (Service Layer genérico)
3. ✅ GDPR compliance completo (derecho al olvido, data retention)

### 13.3 Trabajo Futuro

**Extensiones inmediatas (post-TFG):**
- [ ] Integración WhatsApp Business API
- [ ] Dashboard web de analytics (Streamlit/Dash)
- [ ] Fine-tuning de gemma2 específico para DNI
- [ ] Multimodalidad (imágenes de eventos)

**Investigación académica:**
- [ ] Context decay adaptativo con ML (aprender half-life por usuario)
- [ ] Multi-idioma con embeddings multilingües
- [ ] Comparación empírica: decay exponencial vs lineal vs constant
- [ ] Meta-learning para optimización de parámetros

---

**FIN DEL DOCUMENTO**

**Total de líneas:** ~4,970 (PARTES 1-4 + Anexo Diagramas Mermaid)

**Estado:** ✅ ESPECIFICACIÓN TÉCNICA COMPLETA CON DIAGRAMAS - TFG READY

**Contenido completo:**
- ✅ PARTE 1: Análisis de Requisitos + Arquitectura (Secciones 1-2)
- ✅ PARTE 2: Diseño de Base de Datos PostgreSQL (Sección 3)
- ✅ PARTE 3: Gestión de Contexto Persistente + Servicios (Secciones 4-5)
- ✅ PARTE 4: Telegram Bot + API + Testing + Deployment (Secciones 6-12)
- ✅ ANEXO: 13 Diagramas Mermaid detallados (Sección 13)
  - Arquitectura del Sistema (C4 Container)
  - Diagrama ER (Mermaid)
  - 3 Flujos de datos end-to-end (registro, mensaje, GDPR)
  - 3 Diagramas de estado (conversaciones, usuarios, procesamiento)
  - Arquitectura de Deployment (Docker)
  - Diagrama de decisión (Query Enrichment)
  - Pipeline RAG completo
  - Timeline Gantt visual

**Próximos pasos:**
1. ✅ ~~Crear diagramas Mermaid faltantes~~ COMPLETADO
2. Crear estrategia de branching (.github/BRANCH_STRATEGY.md)
3. Configurar GitHub Actions CI inicial
4. Iniciar implementación (Semana 1 del timeline)

---

**Autor:** Vicente
**Institución:** Universitat Politècnica de València
**Fecha Creación:** 2025-11-19
**Última Actualización:** 2025-11-19 (Diagramas Mermaid añadidos)
**Versión:** 1.1 (Draft Final con Diagramas Completos)
