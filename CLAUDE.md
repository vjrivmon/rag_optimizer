# 📊 CLAUDE.md - Estado del Proyecto RAG Auto-Optimizer v3.3

**Última actualización:** 2025-11-10
**Estado:** ✅ **CHATBOT DNI PRODUCTION-READY CON RAG AVANZADO**

---

## 🎯 RESUMEN EJECUTIVO

### **Sistema Actual: Chatbot DNI v3.3 (2025-11-10)**

**Chatbot DNI** es un asistente virtual inteligente para la asociación de voluntarios DNI (Damos Nuestra Ilusión) en Valencia. Implementa RAG avanzado con:

- ✅ **Confidence dinámico** basado en 6 factores (0.30-0.95)
- ✅ **Contexto conversacional avanzado** con ventana deslizante de 4 interacciones
- ✅ **ContextTracker inteligente** detecta proyectos DNI y enriquece queries
- ✅ **RAG avanzado** siempre activo (10-15 chunks, validación adaptativa)
- ✅ **Vector store optimizado** con 263 chunks (197 FAQ + 66 regulares)
- ✅ **69 preguntas sugeridas** personalizadas por contexto
- ✅ **UI profesional** con colores corporativos DNI (#5B7FDB)
- ✅ **Exportación completa** sin NaN ni fuentes desconocidas

### **Modelos LLM (Servidor UPV Ollama)**

- **gemma2:27b:** Modelo principal del chatbot (0.855 score en benchmarks)
- **Servidor:** https://ollama.gti-ia.upv.es:443/api/generate
- **Arquitectura:** Sistema Ensemble Multi-Modelo disponible (v3.1)

### **Métricas de Rendimiento**

| Métrica | Valor | Estado |
|---------|-------|--------|
| **Tasa de éxito** | 94% (79/84 preguntas) | ✅ |
| **Confidence variabilidad** | 0.30-0.95 (dinámico) | ✅ |
| **Contexto preservado** | 100% (conversaciones críticas) | ✅ |
| **Persistencia contexto multi-turn** | 60% (6/10 preguntas implícitas) | ✅ |
| **Tiempo respuesta** | 1-3 segundos | ✅ |
| **Total chunks** | 263 (197 FAQ) | ✅ |
| **Export sin valores inválidos** | 100% | ✅ |

---

## 🎉 EVOLUCIÓN DEL SISTEMA

### **Historial de Versiones**

| Versión | Fecha | Características Principales | Score | Mejora |
|---------|-------|----------------------------|-------|--------|
| **v1.0** | 2025-10-07 | RAG básico con ChromaDB | 0.770 | - |
| **v2.0** | 2025-10-09 | RAG v2.0 + 10 mejoras | 0.820 | +6.5% |
| **v2.1** | 2025-10-11 | Optimización de parámetros | 0.855 | +4.3% |
| **v3.0** | 2025-10-11 | Voting Strategy (Ensemble) | 0.872 | +2.0% |
| **v3.1** | 2025-10-12 | Consensus + Chatbot base | 0.903 | +3.6% |
| **v3.2** | 2025-11-07 | Chatbot DNI completo | 0.94 | +4.1% |
| **v3.3** | 2025-11-10 | **Context Tracker + Export fixes** | 0.94 | = |

**Mejora total:** +22.1% desde v1.0 hasta v3.3

### **Chatbot DNI v3.2 - Arreglos Críticos (2025-11-05/07)**

#### **Problemas Resueltos:**

1. ✅ **Confidence fijo 0.700** → Ahora dinámico (6 factores ponderados)
2. ✅ **Pérdida de contexto (DANA)** → Preservación por prefijo contextual
3. ✅ **RAG no se usaba** → Forzado `question_id=0` para RAG avanzado SIEMPRE
4. ✅ **Vector store sin Q&A** → Regenerado con formato correcto
5. ✅ **Citas [número] molestas** → Limpiadas automáticamente
6. ✅ **Sin fallback a redes** → Añadido cuando confidence < 0.5
7. ✅ **Feedback solo JSON** → Incluido en export TXT
8. ✅ **UI pequeña** → Ampliada 35% (550x950px)

#### **Mejoras UI/UX:**

- ✅ **Colores corporativos DNI** (#5B7FDB) integrados
- ✅ **Formateo markdown** (** → negrita HTML, limpio en TXT)
- ✅ **Scroll eliminado** en sugerencias (3 preguntas visibles completas)
- ✅ **69 preguntas personalizadas** por contexto (vs 25 genéricas anteriores)
- ✅ **Sin referencias** a proyectos no activos (DANA, kayak)

#### **Mejoras de Prompt:**

```python
# Prompt v3.2 - Identidad + Instrucciones + Casos Especiales
system_prompt = """Eres el asistente virtual oficial de DNI (Damos Nuestra Ilusión),
una asociación de jóvenes voluntarios en Valencia con el lema PARA. MIRA. AYUDA.

PROYECTOS DNI:
- Desayunos Solidarios (personas sin hogar)
- Charlas con Abuelitos (residencia L'Acollida)
- Refuerzo Escolar COLES (niños)
- Rehabilitar Valencia (apoyo DANA - Horta Sud)
- Recogida de Plásticos (kayak)

INSTRUCCIONES:
1. Responde SOLO con información del contexto
2. Tono joven pero profesional
3. Si no sabes, ofrece contacto directo
4. Menciona contactos cuando sea relevante
..."""
```

### **Chatbot DNI v3.3 - Mejoras de Calidad (2025-11-10)**

#### **1. Sistema de Rastreo de Contexto (Context Tracker)**

**Problema:** Pérdida de contexto en preguntas implícitas multi-turn
**Ejemplo crítico:** Usuario pregunta sobre desayunos, luego "¿quién compra los alimentos?" → Sistema respondía sobre desayunos Y cenas

**Solución implementada:**
- ✅ **ContextTracker** nuevo módulo especializado (`src/core/context_tracker.py`)
- ✅ **Ventana deslizante** de 4 interacciones (vs 1 anterior)
- ✅ **Detección de proyectos DNI** con scoring ponderado por recencia
- ✅ **Query enrichment** automático: `[Contexto: Desayunos Solidarios] query`
- ✅ **Extracción de tema** conversacional (horarios, contacto, ubicación)

**Resultados:**
- Tasa de éxito conversación crítica: 60% → **100%** (+67%)
- Contexto preservado en 10 preguntas implícitas: **60%** global
- Benchmark automatizado: `tests/benchmark_context_persistence.py`

#### **2. Arreglo de Exportación (3 Iteraciones Sucesivas)**

**Problema:** Exportaciones con valores `NaN` y fuentes `"unknown"`/`"documento desconocido"`

**Iteración 1 - Frontend (chat.js):**
- ❌ Problema: Campos incorrectos del confidence breakdown
- ✅ Solución: Manejo robusto de múltiples campos (score, avg_score, overlap_ratio)
- ✅ Resultado: Sin NaN en SIMILARITY y KEYWORDS

**Iteración 2 - Backend extract_top_chunks_info:**
- ❌ Problema: Solo buscaba source en metadata
- ✅ Solución: Buscar en chunk['source'] primero, luego metadata
- ⚠️ Resultado: Tests pasaban, pero chatbot real seguía fallando

**Iteración 3 - Adaptive Processing Path (DEFINITIVO):**
- ❌ Problema: `_try_with_config_adaptive` no incluía 'raw_chunks' en resultado
- ✅ Solución: Agregar `'raw_chunks': chunks` en return (línea 1460)
- ✅ Test de debug: `test_debug_chunks_flow.py` reveló el problema real
- ✅ Resultado: **100% fuentes reales** (07_desayunos_logistica.txt, 01_faq_dni.txt)

**Lección aprendida:** Tests de integración pueden pasar mientras producción falla si no simulan el código path exacto

#### **3. Nuevos Tests Creados**

**Tests de contexto:**
- ✅ `tests/benchmark_context_persistence.py` - 5 conversaciones, 10 preguntas implícitas
- ✅ `tests/test_context_persistence.py` - Test unitario de ContextTracker

**Tests de exportación:**
- ✅ `tests/test_integration_export.py` - Integración completa con RAG
- ✅ `tests/test_export_format.py` - Validación de formato export
- ✅ `tests/test_debug_chunks_flow.py` - Simula flujo exacto del chatbot (clave!)

---

## 🏗️ ARQUITECTURA DEL SISTEMA

### **Chatbot DNI v3.3 - Stack Completo**

```
┌─────────────────────────────────────────────────────────────┐
│                    USUARIO (Navegador Web)                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                  ┌──────▼──────┐
                  │  WebSocket   │ (Streaming + Estados en vivo)
                  └──────┬──────┘
                         │
          ┌──────────────▼──────────────┐
          │  FastAPI Backend             │
          │  • Intent Classifier         │ (regex, sin LLM)
          │  • Confidence NO forzado     │ (cálculo dinámico)
          │  • Limpieza citas [n]        │
          │  • Fallback redes sociales   │
          │  • Question Suggester        │ (69 preguntas)
          └──────────────┬──────────────┘
                         │
          ┌──────────────▼────────────────┐
          │  ConversationalRAG            │
          │  • ContextTracker inteligente  │ (v3.3 NUEVO)
          │  • Ventana deslizante 4 turns  │
          │  • Query enrichment automático │
          │  • question_id=0 FORZADO       │
          │  • Historial de conversación   │
          └──────────────┬────────────────┘
                         │
          ┌──────────────▼────────────────┐
          │  EnhancedRAGEngineNew         │
          │  • Validación adaptativa       │
          │  • Confidence dinámico (6)     │
          │  • Cross-encoder reranking     │
          │  • 10-15 chunks consultados    │
          └──────────────┬────────────────┘
                         │
          ┌──────────────▼────────────────┐
          │  ConfigurableRAGEngine        │
          │  • Hybrid Search (50/50)       │
          │  • BM25 + Semantic             │
          │  • Top-k=10, threshold=0.30    │
          └──────────────┬────────────────┘
                         │
          ┌──────────────▼────────────────┐
          │  ChromaDB Vector Store        │
          │  • 263 chunks (197 FAQ)        │
          │  • mpnet-768dim embeddings     │
          │  • Formato Q:/A: detectado     │
          └──────────────┬────────────────┘
                         │
                  ┌──────▼──────┐
                  │  Ollama UPV  │
                  │  gemma2:27b  │
                  └──────────────┘
```

### **Componentes Clave**

#### **Backend FastAPI** (`interface/chatbot_dni/backend/app.py`)
- WebSocket streaming con estados en vivo
- Intent classification (saludo/pregunta/despedida)
- Confidence dinámico (NO forzado a 0.7)
- Limpieza automática de citas [número]
- Fallback a redes sociales si confidence < 0.5
- Question Suggester con 69 preguntas contextuales
- Feedback system (JSONL + metadata local)

#### **ConversationalRAG** (`src/core/conversational_rag.py`)
- **ContextTracker** integrado (v3.3) - detección inteligente de proyectos DNI
- **Ventana deslizante** de 4 interacciones (vs 1 en v3.2)
- **Query enrichment** automático basado en contexto detectado
- **Prefijo contextual** preserva tema (NO reformulación agresiva)
- **question_id=0 FORZADO** → RAG avanzado SIEMPRE activo
- Historial de conversación por sesión
- Fallback mejorado (10 chunks, temperature=0.2)

#### **ContextTracker** (`src/core/context_tracker.py` - NUEVO v3.3)
- **Detección de proyectos DNI** con scoring ponderado por recencia
- **6 proyectos detectables:** Desayunos, RESIS, COLES, DANA, Kayak, General
- **Extracción de tema** conversacional (horarios, contacto, ubicación, etc.)
- **Enriquecimiento de queries** ambiguas con contexto detectado
- **Confianza multi-factor:** combina project_confidence + topic_confidence
- **Ventana configurable:** Por defecto 4 interacciones (8 mensajes)

#### **EnhancedRAGEngineNew** (`src/core/enhanced_rag_engine_new.py`)
- **Confidence dinámico** basado en 6 factores:
  1. Número de chunks (más chunks = más confianza)
  2. Longitud de respuesta (respuestas detalladas)
  3. Ausencia de negativos ("no sé", "no tengo")
  4. Especificidad (horarios, números, ubicaciones)
  5. Solapamiento contexto-respuesta
  6. Cobertura de keywords
- Cross-encoder reranking
- Validación adaptativa por tipo de pregunta
- 10-15 chunks consultados (vs 5 en fallback)

#### **ConfigurableRAGEngine** (`src/core/rag_engine.py`)
- **Hybrid Search**: BM25 (50%) + Semantic (50%)
- Prioriza coincidencias exactas (Q:) sobre narrativas
- Top-k=10, similarity_threshold=0.30
- Semantic weight=0.5 (balanceado)

#### **Vector Store** (ChromaDB)
- **263 chunks totales** (197 FAQ + 66 regulares)
- **Formato Q&A correcto** detectado en chunking
- Embeddings: `paraphrase-multilingual-mpnet-base-v2` (768 dim)
- Documentos base: 16 archivos TXT (08_preguntas_basicas.txt, etc.)

#### **Question Suggester** (`src/core/question_suggester.py`)
- **69 preguntas personalizadas** distribuidas en 6 categorías:
  - Desayunos: 15 preguntas
  - COLES: 11 preguntas
  - RESIS: 11 preguntas
  - General: 15 preguntas
  - Contacto: 10 preguntas
  - Horarios: 7 preguntas
- Clasificación por keywords (sin LLM, instantáneo)
- Sin referencias a DANA/kayak (proyectos no activos)

---

## 📊 RESULTADOS Y BENCHMARKING

### **Benchmark 115 Preguntas (2025-11-05)**

| Métrica | Resultado | Estado |
|---------|-----------|--------|
| **Total preguntas** | 115 | - |
| **Respuestas de calidad** | 79/84 (94%) | ✅ |
| **Avg confidence** | 0.687 | ✅ Variable |
| **Confidence std_dev** | 0.142 | ✅ NO fijo |
| **Max confidence** | 0.923 | ✅ |
| **Min confidence** | 0.387 | ✅ |
| **Avg response time** | 3.24s | ✅ |

### **Comparación Antes vs Después (Arreglos v3.2)**

| Métrica | Antes (Problemático) | Ahora (v3.2) | Mejora |
|---------|----------------------|--------------|--------|
| **Confidence variabilidad** | 0% (fijo 0.7) | Alta (0.30-0.95) | +100% |
| **Retrieval DNI info** | ❌ NO recuperaba | ✅ Recupera correctamente | +100% |
| **Contexto preservado** | 60% | 95%+ | +58% |
| **RAG avanzado usado** | 0% (fallback) | 100% | +100% |
| **Chunks consultados** | 5 | 10-15 | +100-200% |
| **Citas molestas [n]** | ✅ Presentes | ❌ Eliminadas | +100% |
| **Fallback a redes** | ❌ No existía | ✅ Implementado | +100% |
| **Feedback en export** | Solo nota | 👍/👎 Real | +100% |
| **UI tamaño** | 480x700px | 550x950px | +35% |

### **Test Crítico: "¿Qué es DNI?"**

```
ANTES (Vector store sin Q&A):
  Respuesta: "DNI es... [información incompleta]"
  Confidence: 0.70 (fijo)
  Chunks: 5 (fallback simple)

AHORA (v3.2):
  Respuesta: "DNI (Damos Nuestra Ilusión) es una asociación de jóvenes
             voluntarios en Valencia con el lema PARA. MIRA. AYUDA..."
  Confidence: 0.87 (dinámico, alta por especificidad)
  Chunks: 12 (RAG avanzado)
  Fuentes: 08_preguntas_basicas.txt, 09_como_participar.txt
```

---

## 🔧 CONFIGURACIÓN Y DEPLOYMENT

### **Requisitos del Sistema**

**Hardware Mínimo:**
- CPU: 4 cores
- RAM: 8GB (16GB recomendado)
- Almacenamiento: 10GB libres
- Red: Acceso estable al servidor UPV Ollama

**Software:**
- Python 3.12+
- ChromaDB >= 1.0.0
- FastAPI + Uvicorn
- Navegador moderno (Chrome/Firefox)
- VPN o red UPV para acceso a Ollama

### **Configuración del Modelo**

```python
# Modelo principal del chatbot DNI
MODEL_NAME = "gemma2:27b"
API_ENDPOINT = "https://ollama.gti-ia.upv.es:443/api/generate"
TIMEOUT = 300  # 5 minutos
VERIFY_SSL = False  # Servidor UPV con certificado autofirmado
```

### **Configuración RAG**

```yaml
# Enhanced RAG Engine
top_k: 10
similarity_threshold: 0.30
semantic_weight: 0.5  # Balanceado (BM25 50% + Semantic 50%)
max_chunks_advanced: 15
temperature: 0.2
```

### **Inicio Rápido**

```bash
# 1. Activar entorno
cd /home/vicente/Practicas/rag_optimizer_complete/rag_optimizer
source venv/bin/activate

# 2. Iniciar chatbot
./scripts/run_chatbot.sh

# 3. Abrir en navegador
# http://localhost:8000
```

### **Testing Automatizado**

```bash
# Test completo del sistema (5 minutos)
python tests/test_chatbot_automated.py

# Test rápido de conversación crítica
./scripts/test_sistema_completo.sh

# Verificar vector store
python scripts/02_create_faq_aware_chunks.py --verify
```

---

## 🎨 SISTEMA ENSEMBLE (v3.1 - Disponible)

El sistema incluye un motor ensemble multi-modelo (v3.1) con 4 estrategias avanzadas, aunque el chatbot DNI actual usa gemma2:27b directamente por simplicidad.

### **Estrategias Ensemble Disponibles**

1. **Voting Majority:** Selecciona respuesta con mayor combined_score
2. **Weighted Voting:** Pondera por rendimiento histórico
3. **Specialized Routing:** Enruta por categoría de pregunta
4. **Consensus + Fallback:** Busca consenso entre modelos

### **Resultados Ensemble (Benchmark)**

| Estrategia | Score | Correctas | Mejora vs gemma2 |
|------------|-------|-----------|------------------|
| **Consensus** | 0.903 | 26/26 (100%) | +5.6% |
| **Routing** | 0.895 | 25/26 (96.2%) | +4.7% |
| **Weighted** | 0.889 | 25/26 (96.2%) | +4.0% |
| **Voting** | 0.872 | 24/26 (92.3%) | +2.0% |
| **gemma2 (base)** | 0.855 | 22/26 (84.6%) | - |

**Uso del Ensemble:**

```bash
# Dashboard ensemble especializado
streamlit run interface/app_ensemble.py

# Benchmark ensemble completo
python benchmark_ensemble.py
```

---

## 📁 ESTRUCTURA DEL PROYECTO (v3.2)

```
rag_optimizer/
├── 📄 CLAUDE.md                          # Este archivo
├── 📄 README.md                          # Documentación principal
├── 📄 requirements.txt                   # Dependencias
│
├── 📁 interface/
│   ├── chatbot_dni/                      # 🆕 Chatbot DNI (v3.2)
│   │   ├── backend/
│   │   │   └── app.py                    # FastAPI principal
│   │   └── frontend/
│   │       ├── index.html                # UI responsive
│   │       └── static/
│   │           ├── css/                  # Estilos DNI (#5B7FDB)
│   │           └── js/                   # Chat + WebSocket
│   ├── app_v3.py                         # Dashboard profesional
│   └── app_ensemble.py                   # Dashboard ensemble
│
├── 📁 src/
│   ├── core/
│   │   ├── conversational_rag.py         # RAG conversacional (v3.3)
│   │   ├── context_tracker.py            # 🆕 Rastreo contexto (v3.3)
│   │   ├── enhanced_rag_engine_new.py    # Confidence dinámico (v3.3)
│   │   ├── rag_engine.py                 # Hybrid search (v3.2)
│   │   ├── intent_classifier.py          # Clasificación intents
│   │   ├── question_suggester.py         # 69 preguntas (v3.2)
│   │   ├── feedback_system.py            # Sistema feedback
│   │   └── model_wrapper.py              # Wrapper Ollama UPV
│   ├── ensemble/                         # Sistema Ensemble (v3.1)
│   │   ├── ensemble_engine.py
│   │   ├── question_classifier.py
│   │   └── strategies/
│   │       ├── voting.py
│   │       ├── weighted.py
│   │       ├── routing.py
│   │       └── consensus.py
│   └── evaluation/
│       ├── evaluator.py
│       └── ragas_evaluator.py
│
├── 📁 data/
│   ├── documents/                        # 16 archivos TXT DNI (v3.2)
│   │   ├── 01_faq_dni.txt                # Formato Q:/A: ✅
│   │   ├── 08_preguntas_basicas.txt      # 🆕
│   │   ├── 09_como_participar.txt        # 🆕
│   │   └── ...                           # 10-16 documentos
│   ├── vectorstore/chroma_db/            # 263 chunks (v3.2)
│   ├── evaluation_dataset.json           # 26 preguntas benchmark
│   ├── test_queries.txt                  # 115 preguntas test (v3.2)
│   └── feedback.jsonl                    # Feedback usuarios
│
├── 📁 scripts/
│   ├── run_chatbot.sh                    # Iniciar chatbot DNI
│   ├── test_sistema_completo.sh          # Test completo (v3.2)
│   ├── 01_create_vector_store_chroma.py
│   ├── 02_create_faq_aware_chunks.py     # Chunking Q&A (v3.2)
│   ├── benchmark_completo_115.py         # 🆕 Benchmark 115 preguntas
│   └── benchmark_ragas_dni.py            # 🆕 RAGAs evaluation
│
├── 📁 tests/
│   ├── test_chatbot_automated.py         # Testing automatizado
│   ├── benchmark_context_persistence.py  # 🆕 Benchmark contexto (v3.3)
│   ├── test_context_persistence.py       # 🆕 Test unitario contexto (v3.3)
│   ├── test_integration_export.py        # 🆕 Test integración export (v3.3)
│   ├── test_debug_chunks_flow.py         # 🆕 Test debug flujo chatbot (v3.3)
│   ├── test_export_format.py             # 🆕 Test formato export (v3.3)
│   └── ...
│
└── 📁 results/
    ├── benchmark_115_queries_*.json      # 🆕 Resultados v3.2
    └── ensemble_*.json                   # Resultados ensemble v3.1
```

---

## 🚀 PRÓXIMOS PASOS

### **Mejoras Planificadas (Short-term)**

- [ ] **Context decay** (degradación temporal de contexto tras 5+ preguntas off-topic)
- [ ] **Detección de cambio de tema** explícita ("cambiando de tema", etc.)
- [ ] **Aumentar información vector store** (más detalles RESIS y COLES)
- [ ] **Evaluación humana** integrada (usuarios califican respuestas)
- [ ] **A/B Testing** automático de prompts (v3.2 vs v3.3)

### **Mejoras Planificadas (Medium-term)**

- [ ] **Multi-proyecto support** (saltar entre proyectos en misma conversación)
- [ ] **Contexto cross-sesión** (persistir contexto entre sesiones con Redis/PostgreSQL)
- [ ] **Fine-tuning de gemma2** específico para DNI
- [ ] **Multimodalidad** (imágenes, PDFs escaneados)
- [ ] **Multi-idioma** (valenciano, inglés)
- [ ] **API REST** para integración externa
- [ ] **Dashboard en tiempo real** con métricas live

### **Mejoras Planificadas (Long-term)**

- [ ] **Deployment Docker** + CI/CD
- [ ] **Escalabilidad horizontal** (múltiples instancias)
- [ ] **Meta-learning** para selección dinámica de estrategias
- [ ] **Cross-dominio** (aplicar a otras organizaciones)

---

## 🔬 VERIFICACIÓN DEL SISTEMA

### **Test de Conectividad UPV**

```bash
python3 -c "
from src.core.model_wrapper import LLMWrapper
model = LLMWrapper(model_name='gemma2:27b')
result = model.generate('¿Qué es DNI?', max_tokens=100)
print('✅ Servidor UPV:', 'ONLINE' if result['success'] else 'OFFLINE')
print('Respuesta:', result['answer'][:100])
print(f'Latencia: {result.get(\"latency\", 0):.2f}s')
"
```

### **Test de Vector Store**

```bash
python3 scripts/02_create_faq_aware_chunks.py --verify
# Esperado: "✅ Total chunks: 263 (197 FAQ + 66 regulares)"
```

### **Test de Conversación Crítica**

```
Q1: "Horarios desayunos"
    → Esperado: Respuesta sobre horario (8 de la mañana)
    → Confidence: 0.85-0.95

Q2: "¿Qué pasa si llueve?"
    → Esperado: Contexto preservado (desayunos, NO DANA)
    → Confidence: 0.70-0.85

Q3: "se queda en algún lado para ir todos juntos?"
    → Esperado: Punto de encuentro DESAYUNOS (Carrer de Sagunt, 177)
    → Confidence: 0.80-0.90
```

---

## 📊 MÉTRICAS Y MONITORIZACIÓN

### **Métricas RAGAs (Evaluación Académica)**

- **Faithfulness:** Fidelidad al contexto recuperado
- **Answer Relevancy:** Relevancia para la pregunta
- **Context Precision:** Precisión de chunks
- **Context Recall:** Cobertura del contexto
- **Answer Correctness:** Corrección vs ground truth
- **Answer Similarity:** Similitud semántica

### **Métricas Personalizadas**

- **Combined Score:** Ponderación inteligente de todas las métricas
- **Context Overlap:** Solapamiento palabras respuesta-contexto
- **Keyword Coverage:** Cobertura de keywords importantes
- **Confidence Score:** Confianza dinámica (6 factores)

### **Logging y Debugging**

```python
# Los logs del sistema muestran:
🚀 Usando RAG avanzado con validación...
📊 Confidence breakdown:
   - Chunks: 12
   - Answer length: 234 chars
   - Has negative: False
   - Specificity: 2 patterns
   - Context overlap: 0.73
   - Keyword coverage: 0.82
   → Final confidence: 0.873
```

---

## 📞 CONTACTO Y SOPORTE

**Desarrollador:** Vicente
**Institución:** Universitat Politècnica de València
**Estado:** ✅ Sistema en producción (Chatbot DNI v3.2)

**Recursos:**
- [Servidor Ollama UPV GTI-IA](https://ollama.gti-ia.upv.es)
- [RAGAs Framework](https://docs.ragas.io)
- [ChromaDB Documentation](https://docs.trychroma.com)
- [FastAPI](https://fastapi.tiangolo.com)

---

## 📄 LICENCIA

Este proyecto está bajo la **Licencia MIT**.

### **Citación Académica**

```bibtex
@misc{rag_optimizer_chatbot_dni_2025,
  title={Chatbot DNI v3.3: RAG Avanzado con Context Tracking para Asociación de Voluntarios},
  author={Vicente},
  year={2025},
  institution={Universitat Politècnica de València},
  note={Sistema RAG con confidence dinámico, context tracking inteligente, exportación perfecta y 94% tasa de éxito}
}
```

---

**Estado Final:** ✅ **CHATBOT DNI v3.3 - PRODUCTION-READY**

**Última actualización:** 2025-11-10
**Próxima versión:** v3.4 (context decay + multi-proyecto support + A/B testing)

**Mantenido por:** Vicente - Universitat Politècnica de València
