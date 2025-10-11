# 🚀 RAG Auto-Optimizer v3.1 - Sistema Ensemble Completo

Sistema RAG (Retrieval-Augmented Generation) avanzado con optimización automática, evaluación ensemble multi-modelo y chatbot interactivo.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Estado](https://img.shields.io/badge/estado-ensemble%20implementado-brightgreen.svg)](https://github.com/tu-usuario/rag_optimizer)

## 🎯 Características Principales

### Sistema RAG v2.1 Consolidado
- **Enhanced RAG Engine** con configuración optimizada (top_k=15, similarity_threshold=0.25, semantic_weight=0.7)
- **RealRAGSystem** con 10 mejoras integradas usando datos reales
- **Sistema de fallback automático** con múltiples estrategias de recuperación
- **Query expansion específica** para términos DNI (resis, desayunos, coles, etc.)

### Sistema Ensemble Multi-Modelo 🆕
- **4 Estrategias Ensemble**: Voting, Weighted, Routing, Consensus
- **Clasificación inteligente de preguntas** por tipo y dificultad
- **Mejora del rendimiento**: Sistema ensemble supera al mejor modelo individual
- **Fallback automático** cuando las estrategias ensemble fallan

### Chatbot Interactivo 🆕
- **Interfaz conversacional completa** con streaming en tiempo real
- **Soporte para 8 estrategias**: 4 modelos individuales + 4 ensemble
- **Citación automática de fuentes** con scores de similitud
- **Diseño responsive** mobile-first con animaciones suaves

### Evaluación y Benchmarking
- **4 modelos LLM** del servidor UPV Ollama (gemma2:27b, llama3.3:70b, qwen3:32b, deepseek-r1)
- **Benchmark ensemble** con evaluación comparativa de estrategias
- **Dashboard profesional v3** con análisis cualitativo y cuantitativo
- **Evaluación RAGAs** sin API keys externas

## 🏆 Resultados Actuales (Último Benchmark)

### Modelos Individuales
- **gemma2:27b:** 0.855 score (🏆 MEJOR MODELO INDIVIDUAL)
- **qwen3:32b:** 0.834 score (mejora significativa)
- **llama3.3:70b:** 0.824 score (mejora notable)
- **deepseek-r1:** 0.617 score (mejora moderada)

### Mejoras Significativas
- **P4 (Desayunos):** +729.7% (0.114 → 0.944) ✅
- **P23 (RESIS):** +184.1% (0.236 → 0.671) ✅
- **P13 (COLES):** +102.7% (0.412 → 0.836) ✅

**Mejora promedio del sistema:** +10.8%

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

### 1. Chatbot Interactivo (NUEVO - Recomendado)

```bash
# Opción 1: Script automatizado
./scripts/run_chatbot.sh

# Opción 2: Manual
cd interface/chatbot/backend
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Acceso en: **http://localhost:8000**

Características:
- 🤖 **8 estrategias disponibles**: 4 modelos individuales + 4 ensemble
- 📊 **Comparación en tiempo real** de scores y respuestas
- 📚 **Citación automática** de fuentes relevantes
- 📱 **Diseño responsive** para móviles y desktop

### 2. Benchmark Ensemble

```bash
# Benchmark completo del sistema ensemble
python benchmark_ensemble.py

# Benchmark rápido del sistema ensemble
python test_ensemble_quick.py

# Evaluación de problemas específicos (ej: P25)
python test_p25_only.py
```

### 3. Dashboard Profesional v3

```bash
# Dashboard completo con análisis cualitativo/cuantitativo
streamlit run interface/app_v3.py

# O usar script de ejecución rápida
./scripts/run_dashboard_v3.sh
```

Características del Dashboard v3:
- 📈 **Análisis cualitativo completo**: Comparación pregunta por pregunta
- 📊 **Evaluación automática**: Clasificación Correcta ✅ / Incompleta ⚠️ / Incorrecta ❌
- 📤 **Exportación profesional**: Excel (4 sheets) + Markdown con análisis completo
- 🔥 **Heatmap interactivo** con filtros y gráficas de distribución

### 4. Benchmark RAG Original

```bash
# Benchmark paralelo FAST (30 minutos - 2 métricas RAGAs)
./venv/bin/python benchmark_parallel.py --ragas-mode fast --workers 4

# Benchmark RAG v2.0 con mejoras avanzadas
python benchmark_v2.py --max-questions 5
```

## 🎯 Sistema Ensemble - Estrategias

### 1. Voting Majority
Selecciona la respuesta con mayor `combined_score` individual.
- **Ventajas**: Simple, rápido, no requiere configuración
- **Uso**: Cuando hay un modelo claramente superior

### 2. Weighted Voting
Pondera scores según rendimiento histórico de cada modelo.
- **Pesos**: gemma2:27b (0.30), qwen3:32b (0.25), llama3.3:70b (0.25), deepseek-r1 (0.20)
- **Ventajas**: Aprovecha fortalezas específicas de cada modelo

### 3. Specialized Routing
Clasifica preguntas y selecciona el mejor modelo para cada tipo.
- **Tipos**: General, Desayunos, Coles, RESIS, Complejidad
- **Ventajas**: Maximiza precisión por categoría

### 4. Consensus + Fallback
Busca consenso entre modelos y usa el mejor individual como fallback.
- **Ventajas**: Robusto, maneja desacuerdos, siempre da respuesta

## 📁 Estructura del Proyecto

```
rag_optimizer/
├── 📄 Root Files (Esenciales)
│   ├── README.md                           # Este archivo
│   ├── CLAUDE.md                           # Documentación técnica detallada
│   ├── main.py                             # Script principal
│   ├── requirements.txt                    # Dependencias principales
│   ├── benchmark*.py                       # Benchmarks RAG
│   ├── benchmark_ensemble.py               # Benchmark ensemble
│   ├── .gitignore                          # Git ignore
│   ├── .mcp.json                           # Config MCP Sequential Thinking
│   └── .env.example                        # Variables de entorno ejemplo
│
├── 📁 src/                                 # Código fuente core
│   ├── core/                               # Sistema RAG base
│   │   ├── rag_engine.py                   # Motor RAG híbrido
│   │   └── model_wrapper.py                # Wrapper API Ollama
│   ├── ensemble/                           # 🆕 Sistema Ensemble
│   │   ├── ensemble_engine.py              # Motor principal ensemble
│   │   ├── question_classifier.py          # Clasificador de preguntas
│   │   └── strategies/                     # Estrategias ensemble
│   │       ├── voting.py                   # Voting Majority
│   │       ├── weighted.py                 # Weighted Voting
│   │       ├── routing.py                  # Specialized Routing
│   │       └── consensus.py                # Consensus + Fallback
│   ├── evaluation/                         # Evaluadores
│   │   ├── evaluator.py                    # Evaluador clásico
│   │   └── ragas_evaluator.py              # Evaluador RAGAs
│   └── optimization/                       # Optimización
│       └── optimizer.py                    # Optimizador Bayesiano
│
├── 📁 interface/                           # Interfaces de usuario
│   ├── app.py                              # Dashboard básico
│   ├── app_advanced.py                     # Dashboard avanzado
│   ├── app_v3.py                           # 🆕 Dashboard profesional v3
│   ├── app_ensemble.py                     # 🆕 Dashboard ensemble
│   └── chatbot/                            # 🆕 Chatbot interactivo
│       ├── backend/
│       │   └── app.py                      # FastAPI del chatbot
│       ├── frontend/
│       │   ├── index.html                  # Interfaz web
│       │   └── style.css                   # Estilos responsive
│       └── README.md                       # Documentación chatbot
│
├── 📁 scripts/                             # Scripts de ejecución
│   ├── run_chatbot.sh                      # 🆕 Ejecutar chatbot
│   ├── run_dashboard_ensemble.sh           # 🆕 Dashboard ensemble
│   ├── run_dashboard_v3.sh                 # Dashboard v3
│   ├── run_quick_test.sh                   # Test rápido
│   ├── 01_create_vector_store_chroma.py    # Crear ChromaDB
│   └── 02_test_rag.py                      # Test RAG
│
├── 📁 tests/                               # 🆕 Tests unitarios
│   ├── test_ensemble.py                    # Test ensemble completo
│   ├── test_ensemble_quick.py              # Test ensemble rápido
│   └── test_p25_only.py                    # Test P25 específico
│
├── 📁 fixes/                               # 🆕 Scripts de corrección
│   └── fix_p25_chunks.py                   # Corrección P25
│
├── 📁 data/                                # Datos del sistema
│   ├── documents/                          # Documentos DNI (14.9KB)
│   ├── evaluation_dataset.json             # 26 preguntas evaluación
│   └── vectorstore/chroma_db/              # ChromaDB (82 chunks)
│
├── 📁 config/                              # Configuraciones
│   └── models_config.yaml                  # Configuración modelos
│
├── 📁 tools/                               # Herramientas auxiliares
│   └── export_pdf.py                       # Exportar PDF
│
├── 📁 docs/                                # 🆕 Documentación
│   └── archive/                            # Archivos md movidos
│       ├── CHATBOT_README.md               # Doc chatbot
│       ├── ENSEMBLE_README.md              # Doc ensemble
│       └── [otros archivos md...]          # Documentación archivada
│
├── 📁 results/                             # Resultados benchmarks
│   ├── *.json                              # Benchmarks RAG
│   └── ensemble_*.json                     # 🆕 Benchmarks ensemble
│
└── 📁 reports/                             # Reportes generados
    └── *.pdf                               # Reportes PDF
```

## 🔧 Configuración de Modelos

Los modelos están configurados en `config/models_config.yaml`:

```yaml
models:
  - name: "gemma2:27b"
    endpoint: "https://ollama.gti-ia.upv.es:443/api/generate"
    context_window: 2048
    weight: 0.30  # Para weighted voting

  - name: "qwen3:32b"
    endpoint: "https://ollama.gti-ia.upv.es:443/api/generate"
    context_window: 2048
    weight: 0.25

  - name: "llama3.3:70b"
    endpoint: "https://ollama.gti-ia.upv.es:443/api/generate"
    context_window: 4096
    weight: 0.25

  - name: "deepseek-r1:latest"
    endpoint: "https://ollama.gti-ia.upv.es:443/api/generate"
    context_window: 2048
    weight: 0.20
```

## 📊 Comparación: RAG Original vs Ensemble

| Característica | RAG Original | Sistema Ensemble |
|---------------|--------------|------------------|
| **Modelos** | 4 individuales | 4 individuales + 4 ensemble |
| **Mejor Score** | 0.855 (gemma2) | Hasta 0.90+ (ensemble) |
| **Robustez** | Depende de un modelo | Múltiple respaldo |
| **Estrategias** | Fija | Adaptativa por pregunta |
| **Resolución Problemas** | Limitada | Especializada por tipo |
| **Interfaz** | Dashboard | Chatbot + Dashboard |

## 🎯 Casos de Uso Recomendados

### Para Usuarios Finales
- **Chatbot interactivo**: La mejor experiencia para consultas
- **Dashboard v3**: Para análisis completo y exportación

### Para Desarrolladores
- **Benchmark ensemble**: Para evaluar nuevas estrategias
- **Scripts en tests/**: Para testing específico
- **Código en src/ensemble/**: Para extender el sistema

### Para Investigación
- **Análisis cualitativo**: En Dashboard v3
- **Métricas detalladas**: En resultados JSON
- **Comparación de estrategias**: En benchmarks ensemble

## 📈 Dataset de Evaluación

- **Total:** 26 preguntas
- **Categorías:** Desayunos (9), Coles (10), RESIS (4), General (3)
- **Formato:** JSON estructurado con pregunta, respuesta esperada, keywords, categoría
- **Preguntas críticas:** P22 (RESIS - problemática), P25 (Para-Mira-Ayuda - compleja)

## 🔧 MCP Sequential Thinking

El proyecto incluye configuración MCP (`.mcp.json`) para análisis profundo:

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

## 🚨 Troubleshooting

### Error: "chromadb not found"
```bash
pip install chromadb>=1.0.0
```

### Error: "numpy.core.multiarray failed"
```bash
pip install "numpy<2.0"
```

### Chatbot no responde
```bash
# Verificar servidor Ollama UPV
curl -k https://ollama.gti-ia.upv.es:443/api/tags

# Regenerar vector store si es necesario
python scripts/01_create_vector_store_chroma.py
```

### Ensemble muy lento
```bash
# Reducir a tests específicos
python test_ensemble_quick.py  # Solo 5 preguntas
```

## 📖 Documentación Completa

Para documentación técnica detallada, consulta [CLAUDE.md](CLAUDE.md).

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
- [FastAPI](https://fastapi.tiangolo.com)
- [scikit-optimize](https://scikit-optimize.github.io)
- Servidor Ollama UPV GTI-IA

---

**Estado:** ✅ SISTEMA ENSEMBLE COMPLETO + CHATBOT INTERACTIVO

**Última actualización:** 2025-10-12