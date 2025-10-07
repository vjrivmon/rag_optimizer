# 🚀 RAG Auto-Optimizer

Sistema RAG (Retrieval-Augmented Generation) completo con optimización automática y evaluación avanzada usando RAGAs framework.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Características Principales

- **4 modelos LLM** del servidor UPV Ollama (qwen3:32b, deepseek-r1, gemma2:27b, llama3.3:70b)
- **ChromaDB vector store** con embeddings multilingües
- **Optimización Bayesiana** de parámetros RAG
- **Evaluación con RAGAs** usando Ollama (sin OpenAI API key)
- **Testing interactivo** con preguntas personalizadas
- **Benchmark completo** con tablas comparativas
- **Dashboard avanzado** Streamlit con 8 secciones
- **26 preguntas de evaluación** sobre documentación DNI

## 🎉 RAGAs SIN OpenAI API Key

**NOVEDAD:** El sistema ahora evalúa con RAGAs usando Ollama del servidor UPV:
- ✅ **100% GRATIS** - No requiere OpenAI API key
- ✅ **Métricas completas** - faithfulness, answer_relevancy, context_precision, etc.
- ✅ **Privacidad total** - Datos no salen del servidor UPV
- ✅ **Mismo modelo** que estás evaluando

## 📦 Instalación

### Requisitos
- Python 3.12+
- 8GB RAM (para embeddings)
- Acceso al servidor Ollama UPV

### Setup

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/rag_optimizer.git
cd rag_optimizer

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## 🚀 Uso Rápido

### 1. Testing Interactivo (Recomendado para empezar)

```bash
python test_interactive.py
```

Permite:
- Hacer preguntas personalizadas sobre los documentos DNI
- Comparar respuestas de los 4 modelos simultáneamente
- Ver métricas de calidad en tiempo real
- No requiere configuración adicional

### 2. Benchmark Completo

```bash
# Evaluar todas las 26 preguntas
python benchmark.py --detailed

# O solo algunas preguntas para prueba rápida
python benchmark.py --max-questions 5
```

Genera:
- Tabla resumen de estadísticas por modelo
- Comparación detallada pregunta por pregunta
- Archivo JSON con todos los resultados

### 3. Dashboard Avanzado

```bash
streamlit run interface/app_advanced.py
```

Features:
- 📊 Overview general con métricas por modelo
- 📈 Gráficos comparativos de scores
- ⏱️ Análisis de latencias
- 🏆 Victorias por modelo
- 🔍 Detalle por pregunta lado a lado
- 📉 Evolución de scores

## 📊 Métricas Implementadas

### RAGAs (Framework Especializado)
- **faithfulness** - Fidelidad de respuesta al contexto
- **answer_relevancy** - Relevancia de la respuesta
- **context_precision** - Precisión del contexto recuperado
- **context_recall** - Recall del contexto
- **answer_correctness** - Corrección vs respuesta esperada
- **answer_similarity** - Similitud semántica con ground truth

### Métricas Clásicas
- **context_overlap** - Overlap de palabras respuesta-contexto
- **keyword_coverage** - Proporción de keywords presentes
- **has_response** - Si generó respuesta válida
- **combined_score** - Score ponderado de todas las métricas

## 🔧 Arquitectura del Sistema

### Componentes Core

#### RAG Engine ([rag_engine.py](src/core/rag_engine.py))
- Vector store ChromaDB con 41 chunks
- Embeddings: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- Parámetros ajustables: `top_k`, `similarity_threshold`

#### Model Wrapper ([model_wrapper.py](src/core/model_wrapper.py))
- API Ollama REST con SSL bypass
- Tracking de latencia
- Parámetros: `temperature`, `top_p`, `max_tokens`

#### Evaluadores
- **Clásico** ([evaluator.py](src/evaluation/evaluator.py)) - ROUGE, similarity, faithfulness
- **RAGAs** ([ragas_evaluator.py](src/evaluation/ragas_evaluator.py)) - Métricas especializadas RAG

#### Optimizador Bayesiano ([optimizer.py](src/optimization/optimizer.py))
- Framework: scikit-optimize
- Algoritmo: Gaussian Process + Expected Improvement
- Rollback tras 3 fallos consecutivos

## 📁 Estructura del Proyecto

```
rag_optimizer/
├── data/
│   ├── documents/                    # 4 documentos DNI (14.9KB)
│   ├── evaluation_dataset.json       # 26 preguntas
│   └── vectorstore/chroma_db/        # ChromaDB (41 chunks)
├── src/
│   ├── core/
│   │   ├── rag_engine.py            # Motor RAG
│   │   └── model_wrapper.py         # Wrapper API Ollama
│   ├── evaluation/
│   │   ├── evaluator.py             # Evaluador clásico
│   │   └── ragas_evaluator.py       # Evaluador RAGAs con Ollama
│   ├── optimization/
│   │   └── optimizer.py             # Optimizador Bayesiano
│   └── orchestrator/
│       └── orchestrator.py          # Orquestador maestro
├── scripts/
│   ├── 01_create_vector_store_chroma.py
│   └── 02_test_rag.py
├── interface/
│   ├── app.py                       # Dashboard básico
│   └── app_advanced.py              # Dashboard avanzado
├── config/
│   └── models_config.yaml           # 4 modelos UPV
├── results/                         # Resultados JSON
├── main.py                          # Script principal
├── test_interactive.py              # Testing interactivo
├── benchmark.py                     # Benchmark completo
└── requirements.txt
```

## 🛠️ Configuración de Modelos

Los modelos están configurados en [config/models_config.yaml](config/models_config.yaml):

```yaml
models:
  - name: "qwen3:32b"
    endpoint: "https://ollama.gti-ia.upv.es:443/api/generate"
    context_window: 2048

  - name: "deepseek-r1:latest"
    endpoint: "https://ollama.gti-ia.upv.es:443/api/generate"
    context_window: 2048

  - name: "gemma2:27b"
    endpoint: "https://ollama.gti-ia.upv.es:443/api/generate"
    context_window: 2048

  - name: "llama3.3:70b"
    endpoint: "https://ollama.gti-ia.upv.es:443/api/generate"
    context_window: 4096
```

## 📈 Dataset de Evaluación

- **Total:** 26 preguntas
- **Fuente:** Documentos DNI (desayunos, coles, residencias, filosofía)
- **Formato:** JSON estructurado con:
  - `question` - Pregunta en lenguaje natural
  - `expected_answer` - Respuesta esperada
  - `keywords` - Keywords relevantes
  - `category` - Categoría de la pregunta

## 🔍 Fixes Críticos Implementados

### Fix 1: ChromaDB Scores Negativos
- **Problema:** ChromaDB devolvía distancias L2 negativas que rechazaban todos los documentos
- **Solución:** Uso de `similarity_search` simple sin filtrado por threshold problemático

### Fix 2: RAGAs Sin Ground Truth
- **Problema:** RAGAs fallaba en modo interactivo sin `ground_truth`
- **Solución:** Retorno temprano cuando no hay ground_truth disponible

### Fix 3: Event Loop Cerrado
- **Problema:** `RuntimeError: Event loop is closed` con httpx async
- **Solución:** Eliminación del cliente httpx manual, dejando que ChatOllama maneje su ciclo de vida

### Fix 4: Conversión a Float
- **Problema:** RAGAs devolvía columnas no numéricas que fallaban al convertir a float
- **Solución:** Try-except para ignorar columnas no convertibles

### Fix 5: Serialización JSON de NumPy
- **Problema:** Tipos NumPy (int64, float64) no son serializables a JSON
- **Solución:** Conversión recursiva de tipos NumPy a tipos Python nativos

## 🚨 Troubleshooting

### Sistema muy lento
```bash
# Usar menos preguntas
python benchmark.py --max-questions 3
```

### Error: "chromadb not found"
```bash
pip install chromadb>=1.0.0
```

### Error: "numpy.core.multiarray failed"
```bash
pip install "numpy<2.0"
```

### Warning: "Relevance scores must be between 0 and 1"
Normal. ChromaDB usa distancias L2 internamente. Ignorar.

## 📝 Resultados

Los resultados se guardan en formato JSON en `results/`:

```json
{
  "metadata": {
    "timestamp": "2025-10-07T14:30:22",
    "total_questions": 26,
    "total_time": 3419.5,
    "models": ["qwen3:32b", "deepseek-r1:latest", "gemma2:27b", "llama3.3:70b"]
  },
  "results": [...]
}
```

## 🔧 MCP Sequential Thinking

El proyecto incluye configuración MCP ([.mcp.json](.mcp.json)) para análisis profundo con sequential thinking:

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    }
  }
}
```

## 📖 Documentación Completa

Para documentación detallada, consulta [CLAUDE.md](CLAUDE.md).

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

## 📧 Contacto

Vicente - [@tu-usuario](https://github.com/tu-usuario)

Project Link: [https://github.com/tu-usuario/rag_optimizer](https://github.com/tu-usuario/rag_optimizer)

## 🙏 Agradecimientos

- [RAGAs Framework](https://docs.ragas.io)
- [ChromaDB](https://docs.trychroma.com)
- [Streamlit](https://docs.streamlit.io)
- [scikit-optimize](https://scikit-optimize.github.io)
- Servidor Ollama UPV GTI-IA

---

**Estado:** ✅ SISTEMA 100% FUNCIONAL - RAGAs SIN OPENAI

**Última actualización:** 2025-10-07 20:00
