# ÍNDICE PROPUESTO - TFG Chatbot RAG DNI Valencia

**Título:** Desarrollo de un Chatbot Conversacional con RAG para DNI Valencia  
**Autor:** Vicente Rivas Monferrer  
**Grado:** Tecnologías Interactivas (GTI) - EPSG/UPV  
**Entidad:** Cátedra ENIA-UPV  
**Curso:** 2025-2026  

**Páginas objetivo:** ~50 (sin bibliografía ni anexos)

---

## ESTRUCTURA PROPUESTA

| Cap. | Título | Págs. Est. |
|------|--------|------------|
| 1 | Introducción | 6-7 |
| 2 | Marco Teórico | 10-12 |
| 3 | Metodología y Desarrollo | 18-20 |
| 4 | Resultados y Evaluación | 10-12 |
| 5 | Conclusiones y Trabajo Futuro | 4-5 |
| - | **TOTAL** | **48-56** |

---

## CAPÍTULO 1: INTRODUCCIÓN (6-7 págs)

### 1.1 Contexto y Motivación (1.5 págs)
- Transformación digital del tercer sector en España
- Asociación DNI (Damos Nuestra Ilusión): misión y alcance
- Problema de saturación de consultas repetitivas
- Oportunidad de IA conversacional en ONGs

### 1.2 Definición del Problema (1 pág)
- Consultas FAQ manuales: tiempo, inconsistencias, latencia
- Limitaciones de sistemas FAQ estáticos tradicionales
- Requisitos específicos de DNI: multicanal, privacidad, coste cero

### 1.3 Objetivos (1.5 págs)
- **Objetivo General:** Desarrollar un chatbot conversacional con RAG para DNI Valencia
- **Objetivos Específicos (6 OEs SMART):**
  - OE1: Implementar pipeline RAG con búsqueda híbrida (BM25 + semántica)
  - OE2: Desarrollar sistema de contexto conversacional multi-turn
  - OE3: Integrar bot de Telegram con persistencia cross-sesión
  - OE4: Evaluar rendimiento con framework RAGAs (target: >0.85 score)
  - OE5: Garantizar privacidad mediante despliegue local (Ollama UPV)
  - OE6: Documentar evolución del sistema y lecciones aprendidas

### 1.4 Alcance y Limitaciones (1 pág)
- **Alcance:**
  - Corpus DNI: 16 documentos, 263 chunks
  - Interfaces: Web (FastAPI) + Telegram
  - Modelos: gemma2:27b + ensemble disponible
  - Evaluación: 115 preguntas + métricas RAGAs
- **Limitaciones:**
  - Idioma español únicamente
  - Sin fine-tuning de modelos (recursos)
  - Sin evaluación con usuarios reales (fuera de scope)

### 1.5 Estructura del Documento (0.5 págs)
- Breve descripción de cada capítulo

---

## CAPÍTULO 2: MARCO TEÓRICO (10-12 págs)

### 2.1 Sistemas de Recuperación de Información (2 págs)
- 2.1.1 Búsqueda léxica: BM25 y TF-IDF
- 2.1.2 Búsqueda semántica: embeddings y similitud coseno
- 2.1.3 Búsqueda híbrida: combinación ponderada

### 2.2 Generación Aumentada por Recuperación (RAG) (2.5 págs)
- 2.2.1 Pipeline RAG: ingesta, recuperación, generación
- 2.2.2 Ventajas sobre fine-tuning
- 2.2.3 Técnicas de chunking y su impacto
- 2.2.4 FAQ-aware chunking

### 2.3 Modelos de Lenguaje de Gran Escala (LLMs) (2 págs)
- 2.3.1 Arquitectura Transformer y generación de texto
- 2.3.2 Modelos open-source: Gemma, LLaMA, Qwen
- 2.3.3 Ollama: despliegue local de LLMs
- 2.3.4 Sistemas Ensemble multi-modelo

### 2.4 Contexto Conversacional Multi-turn (1.5 págs)
- 2.4.1 Historial de conversación y ventana deslizante
- 2.4.2 Query enrichment y reescritura
- 2.4.3 Confidence dinámico basado en factores múltiples

### 2.5 Evaluación de Sistemas RAG (2 págs)
- 2.5.1 Framework RAGAs: métricas end-to-end
- 2.5.2 Faithfulness, Context Precision, Answer Relevancy
- 2.5.3 Evaluación automática vs. humana
- 2.5.4 Limitaciones de la evaluación automática

### 2.6 Trabajos Relacionados (1.5 págs)
- 2.6.1 RAG en entornos de producción
- 2.6.2 Chatbots para ONGs y tercer sector
- 2.6.3 Posicionamiento del proyecto

---

## CAPÍTULO 3: METODOLOGÍA Y DESARROLLO (18-20 págs)

### 3.1 Metodología de Desarrollo (2 págs)
- 3.1.1 Enfoque iterativo incremental
- 3.1.2 Cronograma: 9 fases en 43 días
- 3.1.3 Herramientas: Python 3.12, Git, Docker
- 3.1.4 Gestión del proyecto: documentación continua (CLAUDE.md)

### 3.2 Arquitectura del Sistema (3 págs)
- 3.2.1 Visión general: componentes y flujo de datos
- 3.2.2 Arquitectura Web (v3.3): FastAPI + WebSocket
- 3.2.3 Arquitectura Telegram (v4.1.1): python-telegram-bot + PostgreSQL
- 3.2.4 Stack tecnológico completo
- **Figura:** Diagrama de arquitectura general

### 3.3 Pipeline RAG (4 págs)
- 3.3.1 Ingesta y chunking de documentos
  - 16 documentos DNI → 263 chunks (197 FAQ + 66 regulares)
  - FAQ-aware chunking: detección formato Q:/A:
- 3.3.2 Vector store: ChromaDB
  - Embeddings: paraphrase-multilingual-mpnet-base-v2 (768 dim)
- 3.3.3 Búsqueda híbrida implementada
  - BM25 (50%) + Semántica (50%)
  - top_k=10, similarity_threshold=0.30
- 3.3.4 Generación y validación adaptativa
  - EnhancedRAGEngineNew
  - System prompt v3.2
  - **Tabla:** Configuración del pipeline RAG
- **Figura:** Flujo del pipeline RAG

### 3.4 Context Tracking Inteligente (3 págs)
- 3.4.1 ContextTracker: detección de proyectos DNI
  - 6 proyectos detectables con scoring ponderado
  - Ventana deslizante de 4 interacciones
- 3.4.2 Query Enrichment automático
  - Prefijo contextual vs. reformulación
  - Multi-factor confidence: project(0.7) + topic(0.3)
- 3.4.3 Confidence dinámico (6 factores)
  - **Tabla:** Factores del confidence score
- **Figura:** Flujo del Context Tracking

### 3.5 Persistencia Cross-Sesión (Telegram) (3 págs)
- 3.5.1 Esquema de base de datos PostgreSQL
  - 7 tablas: users, conversations, messages, context_snapshots...
  - **Figura:** Diagrama ER
- 3.5.2 PersistentContextTracker
  - Exponential decay (half-life = 3 días)
  - Sistema anti-contaminación v4.1.1
- 3.5.3 Service Layer (4 servicios async)

### 3.6 Sistema Ensemble Multi-Modelo (2 págs)
- 3.6.1 Arquitectura del motor Ensemble
- 3.6.2 4 estrategias implementadas
  - Voting, Weighted, Routing, Consensus
- 3.6.3 Resultados y decisión final
  - **Tabla:** Comparativa de estrategias

### 3.7 Seguridad (1.5 págs)
- 3.7.1 Amenazas identificadas (prompt injection, XSS)
- 3.7.2 SDK de seguridad implementado
- 3.7.3 GDPR compliance

---

## CAPÍTULO 4: RESULTADOS Y EVALUACIÓN (10-12 págs)

### 4.1 Métricas de Evaluación (1.5 págs)
- 4.1.1 Métricas RAGAs utilizadas
- 4.1.2 Métricas adicionales: confidence, latencia
- 4.1.3 Dataset de evaluación: 115 preguntas

### 4.2 Evolución del Rendimiento (2.5 págs)
- 4.2.1 Benchmark v1.0 → v4.1.1
  - **Tabla:** Evolución de métricas por versión
  - **Figura:** Gráfica de evolución del score
- 4.2.2 Mejora total: +22.1%

### 4.3 Resultados del Chatbot DNI (3 págs)
- 4.3.1 Benchmark 115 preguntas
  - Tasa de éxito: 94% (79/84)
  - Avg confidence: 0.687
  - **Tabla:** Métricas completas
- 4.3.2 Rendimiento del Context Tracking
  - Contexto preservado: 100%
  - Multi-turn: 60%
- 4.3.3 Análisis de errores
  - **Tabla:** Categorización de fallos

### 4.4 Resultados del Sistema Ensemble (2 págs)
- 4.4.1 Comparativa de 4 estrategias
  - **Tabla:** Resultados por estrategia
- 4.4.2 Consensus vs. modelo individual: +5.6%
- 4.4.3 Trade-off latencia vs. precisión

### 4.5 Discusión (2 págs)
- 4.5.1 Cumplimiento de objetivos
- 4.5.2 Comparación con trabajos relacionados
- 4.5.3 Análisis de fortalezas y debilidades

---

## CAPÍTULO 5: CONCLUSIONES Y TRABAJO FUTURO (4-5 págs)

### 5.1 Conclusiones (1.5 págs)
- Resumen de logros principales
- Validación de hipótesis inicial
- Impacto potencial en DNI Valencia

### 5.2 Contribuciones del Proyecto (1 pág)
- Sistema RAG production-ready
- Metodología de evaluación reproducible
- Documentación técnica completa (CLAUDE.md, 94KB)

### 5.3 Limitaciones (0.5 págs)
- Dependencia del servidor Ollama UPV
- Sin evaluación con usuarios reales
- Corpus limitado a DNI

### 5.4 Trabajo Futuro (1 pág)
- Corto plazo: evaluación con voluntarios, A/B testing
- Medio plazo: multimodalidad, WhatsApp, valenciano
- Largo plazo: fine-tuning, cross-dominio

### 5.5 Reflexión Personal (0.5 págs)
- Aprendizajes técnicos y metodológicos
- Impacto del proyecto en formación profesional

---

## ANEXOS (fuera de las 50 págs)

- **Anexo A:** Bibliografía (30+ referencias)
- **Anexo B:** Código fuente relevante (extractos)
- **Anexo C:** Dataset de evaluación completo (115 preguntas)
- **Anexo D:** Logs de benchmarks

---

## FIGURAS REQUERIDAS (mínimo)

1. Diagrama de arquitectura general (Web + Telegram)
2. Pipeline RAG (3 fases con componentes)
3. Flujo del Context Tracking
4. Diagrama ER base de datos (7 tablas)
5. Gráfica evolución scores v1.0 → v4.1.1
6. Histograma distribución confidence

## TABLAS REQUERIDAS (mínimo)

1. Objetivos específicos (OEs) con métricas
2. Stack tecnológico
3. Configuración pipeline RAG
4. Factores del confidence dinámico
5. Comparativa estrategias Ensemble
6. Evolución de métricas por versión
7. Benchmark 115 preguntas (métricas completas)
8. Categorización de errores

---

**Nota:** Este índice está alineado con:
- Estructura de 5 capítulos (estándar UPV/EPSG)
- Contenido real del proyecto (CLAUDE.md, código)
- Extensión de ~50 páginas (sin anexos)
- Formato académico con figuras y tablas

---

*Generado por VisiClaw — 2026-02-05*
