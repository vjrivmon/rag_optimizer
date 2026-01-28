# 🚀 RAG Auto-Optimizer v3.3 - Chatbot DNI

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Estado](https://img.shields.io/badge/estado-production--ready-brightgreen.svg)](https://github.com/tu-usuario/rag_optimizer)

**Asistente virtual inteligente con RAG avanzado y Context Tracking para DNI (Damos Nuestra Ilusión) - Asociación de voluntarios en Valencia**

---

## 🎯 Características Principales

### **Chatbot DNI v3.3 (Production-Ready)**

✅ **Context Tracker Inteligente:** Detecta proyectos DNI y enriquece queries automáticamente
✅ **Ventana Deslizante:** 4 interacciones para contexto multi-turn perfecto
✅ **RAG Avanzado:** 10-15 chunks consultados con validación adaptativa
✅ **Confidence Dinámico:** Basado en 6 factores (0.30-0.95)
✅ **Exportación Perfecta:** Sin valores NaN ni fuentes desconocidas
✅ **69 Preguntas Sugeridas:** Personalizadas por contexto
✅ **UI Profesional:** Colores corporativos DNI (#5B7FDB)
✅ **Vector Store Optimizado:** 263 chunks (197 FAQ + 66 regulares)
✅ **Servidor UPV:** gemma2:27b sin API keys externas

### **Sistema Ensemble (v3.1 - Disponible)**

✅ **4 Estrategias:** Voting, Weighted, Routing, Consensus
✅ **4 Modelos LLM:** gemma2:27b, llama3.3:70b, qwen3:32b, deepseek-r1
✅ **Mejora del rendimiento:** Hasta +5.6% vs mejor modelo individual
✅ **Dashboard especializado:** Análisis comparativo de estrategias

---

## 🏆 Resultados Actuales

### **Métricas del Chatbot DNI v3.3**

| Métrica | Valor | Estado |
|---------|-------|--------|
| **Tasa de éxito** | 94% (79/84 preguntas) | ✅ |
| **Confidence variabilidad** | 0.30-0.95 (dinámico) | ✅ |
| **Contexto preservado** | 100% (conversaciones críticas) | ✅ |
| **Contexto multi-turn** | 60% (6/10 preguntas implícitas) | ✅ |
| **Tiempo de respuesta** | 1-3 segundos | ✅ |
| **Export sin valores inválidos** | 100% | ✅ |
| **Avg confidence** | 0.687 | ✅ |

### **Mejoras vs Versión Anterior (v3.2 → v3.3)**

| Métrica | v3.2 | v3.3 | Mejora |
|---------|------|------|--------|
| **Ventana contextual** | 1 interacción | 4 interacciones | +300% |
| **Context tracking** | Básico (prefijo) | Avanzado (ContextTracker) | +100% |
| **Conversación crítica** | 60% | 100% | +67% |
| **Export NaN/unknown** | Presentes | Eliminados (100%) | +100% |
| **Query enrichment** | ❌ No | ✅ Sí | +100% |
| **Tests automatizados** | 2 | 7 | +250% |

### **Mejoras Históricas (v3.0 → v3.3)**

| Métrica | v3.0 | v3.3 | Mejora |
|---------|------|------|--------|
| Confidence | Fijo 0.70 | 0.30-0.95 | +100% |
| Contexto | 60% | 100% | +67% |
| RAG usado | Fallback (0%) | Siempre (100%) | +100% |
| Chunks | 5 | 10-15 | +100-200% |
| UI tamaño | 480x700px | 550x950px | +35% |

---

## 📦 Instalación

### **Requisitos**

- Python 3.12+
- 8GB RAM (16GB recomendado)
- Acceso al servidor Ollama UPV (VPN o red UPV)

### **Setup Rápido**

```bash
# 1. Clonar repositorio
git clone https://github.com/tu-usuario/rag_optimizer.git
cd rag_optimizer

# 2. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Iniciar chatbot
./scripts/run_chatbot.sh

# 5. Abrir en navegador
# http://localhost:8000
```

---

## 🚀 Uso Rápido

### **1. Chatbot DNI (Recomendado)**

```bash
# Opción 1: Script automatizado (recomendado)
./scripts/run_chatbot.sh

# Opción 2: Manual
cd interface/chatbot_dni/backend
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

**Acceso:** http://localhost:8000

**Funcionalidades:**
- 🤖 **Streaming en tiempo real** con estados visuales
- 📊 **Confidence score** dinámico por respuesta
- 📚 **Citación automática** de fuentes relevantes
- 💬 **69 preguntas sugeridas** por contexto
- 📱 **Diseño responsive** mobile-first
- 💾 **Exportación TXT** de conversaciones con feedback

### **2. Testing Automatizado**

```bash
# Test completo del sistema (5 minutos, 115 preguntas)
python tests/test_chatbot_automated.py

# Test rápido conversación crítica
./scripts/test_sistema_completo.sh

# Verificar vector store
python scripts/02_create_faq_aware_chunks.py --verify
```

### **3. Dashboard Profesional v3**

```bash
# Dashboard con análisis cualitativo/cuantitativo
streamlit run interface/app_v3.py

# Dashboard especializado ensemble
streamlit run interface/app_ensemble.py
```

**Características del Dashboard v3:**
- 📈 Análisis cualitativo pregunta por pregunta
- 📊 Evaluación automática: ✅ Correcta / ⚠️ Incompleta / ❌ Incorrecta
- 📤 Exportación: Excel (4 sheets) + PDF + Markdown
- 🔥 Heatmap interactivo con filtros
- 📖 Guía de métricas RAGAs con histogramas

### **4. Sistema Ensemble (Opcional)**

```bash
# Benchmark ensemble completo
python benchmark_ensemble.py

# Test ensemble rápido (5 preguntas)
python test_ensemble_quick.py
```

---

## 🎯 Test Crítico

### **Pregunta de Verificación: "¿Qué es DNI?"**

**Respuesta esperada (v3.2):**
```
DNI (Damos Nuestra Ilusión) es una asociación de jóvenes voluntarios
en Valencia con el lema PARA. MIRA. AYUDA...

📊 Confidence: 0.87 (alta, por especificidad)
📚 Fuentes: 08_preguntas_basicas.txt, 09_como_participar.txt
✅ Sin citas [número]
```

### **Test de Contexto Conversacional**

```
Q1: "Horarios desayunos"
    → Responde sobre horarios (8 de la mañana)
    → Confidence: 0.85-0.95

Q2: "¿Qué pasa si llueve?"
    → Mantiene contexto (desayunos, NO DANA)
    → Confidence: 0.70-0.85

Q3: "¿se queda en algún lado para ir todos juntos?"
    → Punto de encuentro DESAYUNOS (Carrer de Sagunt, 177)
    → Confidence: 0.80-0.90
    → ✅ CONTEXTO PRESERVADO
```

---

## 🏗️ Arquitectura del Sistema

### **Stack Tecnológico**

```
Frontend: HTML5 + CSS3 + JavaScript (WebSocket)
Backend: FastAPI + Uvicorn
RAG Engine: Custom (Enhanced RAG v3.2)
Vector Store: ChromaDB (263 chunks)
Embeddings: paraphrase-multilingual-mpnet-base-v2 (768 dim)
LLM: gemma2:27b (Servidor Ollama UPV)
```

### **Flujo de una Pregunta**

```
1. USUARIO → WebSocket → FastAPI Backend
2. Intent Classification (saludo/pregunta/despedida)
3. ConversationalRAG (contexto + historial)
4. EnhancedRAGEngineNew (retrieval + validación)
5. ChromaDB (hybrid search: BM25 50% + Semantic 50%)
6. gemma2:27b (generación respuesta)
7. Confidence dinámico (6 factores)
8. Limpieza citas + Fallback redes (si confidence < 0.5)
9. Question Suggester (69 preguntas por contexto)
10. USUARIO ← WebSocket ← Streaming respuesta
```

---

## 📁 Estructura del Proyecto

```
rag_optimizer/
├── 📄 README.md                          # Este archivo
├── 📄 CLAUDE.md                          # Documentación técnica detallada
├── 📄 requirements.txt                   # Dependencias
│
├── 📁 interface/
│   ├── chatbot_dni/                      # 🆕 Chatbot DNI v3.2
│   │   ├── backend/app.py                # FastAPI + WebSocket
│   │   └── frontend/                     # HTML + CSS + JS
│   ├── app_v3.py                         # Dashboard profesional
│   └── app_ensemble.py                   # Dashboard ensemble
│
├── 📁 src/
│   ├── core/
│   │   ├── conversational_rag.py         # RAG conversacional (v3.3)
│   │   ├── context_tracker.py            # 🆕 Rastreo contexto (v3.3)
│   │   ├── enhanced_rag_engine_new.py    # Confidence dinámico (v3.3)
│   │   ├── rag_engine.py                 # Hybrid search
│   │   ├── intent_classifier.py          # Clasificación sin LLM
│   │   ├── question_suggester.py         # 69 preguntas contextuales
│   │   ├── feedback_system.py            # Sistema feedback
│   │   └── model_wrapper.py              # Wrapper Ollama UPV
│   ├── ensemble/                         # Sistema Ensemble v3.1
│   │   └── strategies/                   # 4 estrategias
│   └── evaluation/                       # Evaluadores RAGAs
│
├── 📁 data/
│   ├── documents/                        # 16 archivos TXT DNI
│   ├── vectorstore/chroma_db/            # 263 chunks (197 FAQ)
│   ├── evaluation_dataset.json           # 26 preguntas benchmark
│   ├── test_queries.txt                  # 115 preguntas test
│   └── feedback.jsonl                    # Feedback usuarios
│
├── 📁 scripts/
│   ├── run_chatbot.sh                    # 🚀 Iniciar chatbot
│   ├── test_sistema_completo.sh          # Testing completo
│   ├── 02_create_faq_aware_chunks.py     # Regenerar vector store
│   └── benchmark_completo_115.py         # Benchmark 115 preguntas
│
└── 📁 tests/
    ├── test_chatbot_automated.py         # Testing automatizado
    ├── benchmark_context_persistence.py  # 🆕 Benchmark contexto (v3.3)
    ├── test_context_persistence.py       # 🆕 Test contexto (v3.3)
    ├── test_integration_export.py        # 🆕 Test export (v3.3)
    ├── test_debug_chunks_flow.py         # 🆕 Test debug (v3.3)
    └── ...
```

---

## 🔧 Configuración

### **Modelos LLM (Servidor UPV)**

```yaml
# Modelo principal (Chatbot DNI)
model: gemma2:27b
endpoint: https://ollama.gti-ia.upv.es:443/api/generate
timeout: 300  # 5 minutos
verify_ssl: false

# Modelos adicionales (Ensemble)
- llama3.3:70b
- qwen3:32b
- deepseek-r1:latest
```

### **Configuración RAG**

```yaml
# Enhanced RAG Engine v3.2
top_k: 10
similarity_threshold: 0.30
semantic_weight: 0.5  # Hybrid: BM25 50% + Semantic 50%
max_chunks_advanced: 15
temperature: 0.2
context_window: 2048
```

### **Confidence Dinámico (6 Factores)**

1. **Número de chunks** (más chunks = más confianza)
2. **Longitud de respuesta** (respuestas detalladas)
3. **Ausencia de negativos** ("no sé", "no tengo")
4. **Especificidad** (horarios, números, ubicaciones)
5. **Solapamiento contexto-respuesta**
6. **Cobertura de keywords**

---

## 🎨 Sistema Ensemble (v3.1)

### **Estrategias Disponibles**

1. **Voting Majority:** Respuesta con mayor combined_score
2. **Weighted Voting:** Ponderación por rendimiento histórico
3. **Specialized Routing:** Por categoría (Desayunos, COLES, RESIS)
4. **Consensus + Fallback:** Busca consenso, fallback al mejor

### **Resultados Benchmark Ensemble**

| Estrategia | Score | Correctas | Mejora vs gemma2 |
|------------|-------|-----------|------------------|
| **Consensus** | 0.903 | 26/26 (100%) | +5.6% |
| **Routing** | 0.895 | 25/26 (96.2%) | +4.7% |
| **Weighted** | 0.889 | 25/26 (96.2%) | +4.0% |
| **Voting** | 0.872 | 24/26 (92.3%) | +2.0% |
| **gemma2 (base)** | 0.855 | 22/26 (84.6%) | - |

---

## 🧪 Testing y Verificación

### **Checklist de Verificación**

- [ ] Chatbot inicia sin errores
- [ ] "¿Qué es DNI?" responde con "Damos Nuestra Ilusión"
- [ ] Confidence varía entre preguntas (no siempre 0.70)
- [ ] Contexto preservado en conversaciones
- [ ] Sin citas [número] en respuestas
- [ ] Export TXT incluye confidence y feedback
- [ ] UI se ve más grande (550x950px)
- [ ] 3 preguntas sugeridas visibles sin scroll

### **Verificación del Sistema**

```bash
# 1. Test de conectividad UPV
python3 -c "
from src.core.model_wrapper import LLMWrapper
model = LLMWrapper(model_name='gemma2:27b')
result = model.generate('Test', max_tokens=10)
print('✅ Servidor UPV:', 'ONLINE' if result['success'] else 'OFFLINE')
"

# 2. Test de vector store
python scripts/02_create_faq_aware_chunks.py --verify
# Esperado: "✅ Total chunks: 263 (197 FAQ + 66 regulares)"

# 3. Test automatizado completo
python tests/test_chatbot_automated.py
# Esperado: 94% success rate, confidence 0.60-0.75
```

---

## 🚨 Troubleshooting

### **Problema: "¿Qué es DNI?" no responde correctamente**

```bash
# Solución: Regenerar vector store
python3 scripts/02_create_faq_aware_chunks.py
./scripts/run_chatbot.sh
```

### **Problema: Confidence siempre 0.70**

```bash
# Verificar que no hay fallback forzado
grep -n "confidence = 0.7" interface/chatbot_dni/backend/app.py
# NO debería aparecer (excepto en comentarios)
```

### **Problema: Pérdida de contexto (DANA)**

```bash
# Verificar prefijo contextual
grep -n "Contexto: Estábamos hablando" src/core/conversational_rag.py
# Debería aparecer en ~línea 180
```

### **Problema: Chatbot no inicia**

```bash
# Verificar servidor UPV
curl -k https://ollama.gti-ia.upv.es:443/api/tags

# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

---

## 📊 Comparación: Ensemble vs Chatbot DNI

| Característica | Chatbot DNI v3.2 | Ensemble v3.1 |
|----------------|------------------|---------------|
| **Modelos** | 1 (gemma2:27b) | 4 modelos |
| **Tiempo respuesta** | 1-3s | 11-15s |
| **Complejidad** | Media | Alta |
| **Mejor para** | Producción, usuarios finales | Research, benchmarking |
| **Score** | 0.87 (avg) | 0.90+ (consensus) |
| **Robustez** | Alta | Muy alta |

---

## 🎯 Casos de Uso

### **Para Usuarios Finales**

✅ **Chatbot interactivo:** Mejor experiencia, streaming en tiempo real
✅ **Dashboard v3:** Análisis completo, exportación profesional

### **Para Desarrolladores**

✅ **Testing automatizado:** `python tests/test_chatbot_automated.py`
✅ **Benchmarking:** `python scripts/benchmark_completo_115.py`
✅ **Regenerar vector store:** `python scripts/02_create_faq_aware_chunks.py`

### **Para Investigación**

✅ **Sistema Ensemble:** Comparación de estrategias multi-modelo
✅ **Métricas RAGAs:** Evaluación académica rigurosa
✅ **Dashboard especializado:** `streamlit run interface/app_ensemble.py`

---

## 🚀 Próximos Pasos

### **Short-term (1-2 semanas)**

- [ ] Evaluación humana integrada
- [ ] A/B Testing automático de prompts
- [ ] Dashboard en tiempo real
- [ ] Contexto multi-sesión

### **Medium-term (1-2 meses)**

- [ ] Fine-tuning gemma2 específico DNI
- [ ] Multimodalidad (imágenes, PDFs)
- [ ] Multi-idioma (valenciano, inglés)
- [ ] API REST para integración

### **Long-term (3-6 meses)**

- [ ] Deployment Docker + CI/CD
- [ ] Escalabilidad horizontal
- [ ] Meta-learning para estrategias
- [ ] Cross-dominio (otras organizaciones)

---

## 📚 Documentación Completa

Para documentación técnica detallada, consulta:

- **[CLAUDE.md](CLAUDE.md)** - Documentación técnica completa (arquitectura, métricas, configuración)
- **[LICENSE](LICENSE)** - Licencia MIT

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas:

1. Fork el proyecto
2. Crea una rama: `git checkout -b feature/AmazingFeature`
3. Commit: `git commit -m 'Add AmazingFeature'`
4. Push: `git push origin feature/AmazingFeature`
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto está bajo la **Licencia MIT**. Ver [LICENSE](LICENSE) para detalles.

---

## 📞 Contacto

**Desarrollador:** Vicente
**Institución:** Universitat Politècnica de València
**Estado:** ✅ Chatbot DNI v3.3 - Production-Ready (Context Tracking + Export Perfecto)

---

## 🙏 Agradecimientos

- [Servidor Ollama UPV GTI-IA](https://ollama.gti-ia.upv.es) - Acceso a modelos LLM
- [RAGAs Framework](https://docs.ragas.io) - Métricas de evaluación
- [ChromaDB](https://docs.trychroma.com) - Vector store eficiente
- [FastAPI](https://fastapi.tiangolo.com) - Backend asíncrono
- [Streamlit](https://docs.streamlit.io) - Dashboards interactivos

---

**Estado Final:** ✅ **CHATBOT DNI v3.3 - PRODUCTION-READY**

**Última actualización:** 2025-11-10
**Próxima versión:** v3.4 (context decay + multi-proyecto + A/B testing)
