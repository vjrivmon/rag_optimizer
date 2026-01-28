# Skill: TFG Cap 3 - Metodologia y Desarrollo

## Descripcion

Genera el Capitulo 3 (Metodologia y Desarrollo) del TFG. Es el capitulo mas
largo (~20-25 paginas) y documenta toda la arquitectura, implementacion y
decisiones tecnicas del sistema.

## Activacion

- Comando: `/tfg-cap3 <seccion>`
- Triggers: "escribe metodologia", "capitulo 3", "arquitectura",
  "implementacion"

## Archivo Destino

`docs/tfg/capitulos/03-metodologia.tex`

## Principio Clave

> Documenta el sistema ACTUAL antes de modificarlo. Cada decision tecnica debe
> tener justificacion + resultado medible.

## Patron de Escritura por Seccion

```
Decision tecnica -> Justificacion -> Implementacion -> Resultado medible
```

Ejemplo:

```latex
Se selecciono ChromaDB como base de datos vectorial (decision) por su
simplicidad de despliegue y licencia open-source (justificacion). La
implementacion almacena 263 chunks con embeddings de 768 dimensiones
(implementacion), logrando tiempos de busqueda inferiores a 50ms para
top-10 resultados (resultado medible).
```

---

## Estructura del Capitulo (~20-25 paginas)

### 3.1 Metodologia de Desarrollo (2 pags)

**Contenido:**

- Enfoque iterativo incremental (NO waterfall, NO agile puro)
- 9 fases de desarrollo en 43 dias (7 Oct - 19 Nov 2025)
- Cronograma visual (tabla o diagrama de Gantt simplificado)
- Herramientas: Python 3.12, Git, Docker, GitHub Actions
- Proceso: disenar -> implementar -> evaluar -> iterar
- Gestion: commits atomicos, documentacion continua (CLAUDE.md, 2400+ lineas)

**Datos fuente:** CLAUDE.md seccion "CRONOLOGIA COMPLETA DEL DESARROLLO"

**Tabla requerida:** Fases de desarrollo con fechas, hitos y resultados

| Fase                 | Periodo  | Hito                                  | Score |
| -------------------- | -------- | ------------------------------------- | ----- |
| 1. Foundation        | 7-8 Oct  | RAG basico + FAISS                    | 0.770 |
| 2. Model Testing     | 8 Oct    | ChromaDB + Hybrid                     | -     |
| 3. Crisis & Recovery | 9-10 Oct | Benchmark paralelo (fracaso+recovery) | 0.820 |
| 4. Optimization      | 11 Oct   | Params tuning                         | 0.855 |
| 5. Ensemble          | 12 Oct   | Multi-modelo + Chatbot                | 0.903 |
| 6. Thesis Draft      | 21 Oct   | Borrador TFG                          | -     |
| 7. Production        | 5-7 Nov  | Chatbot DNI v3.2                      | 0.940 |
| 8. Context Tracking  | 10 Nov   | ContextTracker v3.3                   | 0.940 |
| 9. Telegram          | 19 Nov   | Bot + Persistencia v4.1.1             | 0.940 |

### 3.2 Arquitectura del Sistema (3 pags)

**Contenido:**

- Diagrama de arquitectura general (FIGURA REQUERIDA)
- Stack tecnologico completo (tabla)
- Separacion web vs Telegram

**Datos fuente:** CLAUDE.md seccion "ARQUITECTURA DEL SISTEMA"

**Figura requerida:** Diagrama de bloques mostrando:

```
Usuario Web/Telegram -> Frontend/Bot -> Backend FastAPI -> ConversationalRAG
-> EnhancedRAGEngine -> ChromaDB + Ollama
+ PostgreSQL (solo Telegram)
```

**Subsecciones:**

- 3.2.1 Arquitectura Web (v3.3): FastAPI + WebSocket + HTML/CSS/JS
- 3.2.2 Arquitectura Telegram (v4.1.1): python-telegram-bot + PostgreSQL

### 3.3 Pipeline RAG (4 pags)

**Contenido detallado:**

- **3.3.1 Ingesta y Chunking:**
  - 16 documentos DNI -> 263 chunks (197 FAQ + 66 regulares)
  - FAQ-aware chunking: `02_create_faq_aware_chunks.py`
  - Formato Q:/A: detectado automaticamente
  - Embeddings: `paraphrase-multilingual-mpnet-base-v2` (768 dim)
  - Datos fuente: `scripts/02_create_faq_aware_chunks.py`

- **3.3.2 Busqueda Hibrida:**
  - BM25 (50%) + Semantic (50%), configurable
  - ChromaDB como vector store
  - top_k=10, similarity_threshold=0.30
  - Codigo fuente: `src/core/rag_engine.py`

- **3.3.3 Generacion y Validacion:**
  - EnhancedRAGEngineNew con validacion adaptativa
  - question_id=0 forzado (RAG avanzado siempre)
  - 10-15 chunks consultados
  - Cross-encoder reranking
  - Confidence dinamico (6 factores: chunks, length, negatives, specificity,
    overlap, keywords)
  - System prompt v3.2 completo
  - Codigo fuente: `src/core/enhanced_rag_engine_new.py`

### 3.4 Context Tracking Inteligente (3 pags)

**Contenido detallado:**

- **3.4.1 ContextTracker:**
  - `src/core/context_tracker.py` (415 lineas)
  - 6 proyectos DNI detectables con scoring ponderado
  - Ventana deslizante de 4 interacciones (8 mensajes)
  - Ponderacion: user messages (1.0), assistant messages (0.15)
  - Umbral de confianza: 0.6

- **3.4.2 Query Enrichment:**
  - Prefijo contextual `[Contexto: Desayunos Solidarios] query`
  - Extraccion de tema (6 temas: horarios, ubicacion, requisitos, inscripcion,
    funcionamiento, contacto)
  - Multi-factor: project_confidence(0.7) + topic_confidence(0.3)

- **3.4.3 ConversationalRAG:**
  - `src/core/conversational_rag.py` (492 lineas)
  - Integracion completa ContextTracker + RAG engine
  - Historial por sesion (web) / por DB (Telegram)
  - Fallback mejorado (10 chunks, temperature=0.2)

**Figura requerida:** Diagrama de flujo del context tracking

```
Query ambigua -> ContextTracker -> Detectar proyecto -> Enriquecer query
-> RAG Engine -> Respuesta contextualizada
```

### 3.5 Persistencia Cross-Sesion (3 pags)

**Contenido detallado:**

- **3.5.1 Esquema BD PostgreSQL:**
  - 7 tablas: users, conversations, messages, context_snapshots, feedback,
    user_consents, analytics_events
  - Diagrama ER (FIGURA REQUERIDA)
  - JSONB para metadata flexible
  - Alembic migrations (version 1f61cecb9b98)

- **3.5.2 PersistentContextTracker:**
  - `src/core/persistent_context_tracker.py` (345 lineas)
  - Exponential decay: weight = exp(-days_ago / tau), tau = half_life / ln(2)
  - Merge: recent + historical snapshots
  - Anti-contaminacion v4.1.1 (3 capas):
    1. Deteccion conversacion activa (2+ mensajes -> NO consultar DB)
    2. Umbral sensibilidad bajado 0.5 -> 0.3
    3. DB solo en primera interaccion

- **3.5.3 Service Layer:**
  - 4 servicios async: UserService, ConversationService, MessageService,
    ContextService
  - Patron Repository con SQLAlchemy ORM
  - Fix critico: expire_on_commit=False

**Datos fuente:** `src/services/`, `src/database/`, `alembic/`

### 3.6 Sistema Ensemble Multi-Modelo (2 pags)

**Contenido:**

- `src/ensemble/ensemble_engine.py` (287 lineas)
- `src/ensemble/question_classifier.py` (130 lineas)
- 4 estrategias: Voting (92 LOC), Weighted (109), Routing (184), Consensus (142)
- Modelos: gemma2:27b, llama3.3:70b, qwen2.5:32b, deepseek-r1
- Decision pragmatica: gemma2:27b directo en produccion

**Datos fuente:** `src/ensemble/`

### 3.7 Seguridad (1.5 pags)

**Contenido:**

- Amenazas: prompt injection, XSS, CORS, input validation
- SDK: InjectionDetector, Sanitizer, RiskScorer, RateLimiter
- GDPR: /delete_my_data en Telegram
- Integracion en web y Telegram

**Datos fuente:** `vicente_rag/security/`

### 3.8 Infraestructura y Deployment (1.5 pags)

**Contenido:**

- Servidor Ollama UPV (ollama.gti-ia.upv.es:443)
- Docker Compose: PostgreSQL 16 (puerto 5434)
- GitHub Actions: 5 workflows CI/CD
- Scripts de deployment: `scripts/run_chatbot.sh`

---

## Figuras Requeridas (6)

1. Diagrama de arquitectura general (web + Telegram)
2. Pipeline RAG completo (3 fases con componentes)
3. Flujo del Context Tracking (query -> enriquecimiento -> RAG)
4. Diagrama ER de la base de datos (7 tablas)
5. Arquitectura del sistema Ensemble con routing
6. Cronograma de desarrollo (9 fases)

## Tablas Requeridas (5+)

1. Fases de desarrollo con fechas y scores
2. Stack tecnologico (componente, tecnologia, version)
3. Configuracion del pipeline RAG (parametros y valores)
4. Factores del confidence dinamico (6 factores)
5. Comparativa 4 estrategias ensemble

## Formato LaTeX

Usar `\cite{}` para todas las referencias. Codigo con `lstlisting` (Python,
bash). Tablas con `booktabs`. Acentos LaTeX.

## Checklist de Calidad

- [ ] Cada decision tecnica tiene justificacion
- [ ] Resultados medibles para cada componente
- [ ] Diagramas para arquitectura y flujos
- [ ] Codigo fuente referenciado (archivo + lineas)
- [ ] Problemas encontrados y soluciones documentados
- [ ] Conexion explicita con objetivos del Cap 1
