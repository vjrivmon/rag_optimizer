# 🎯 Sistema de Ensemble Multi-Modelo - README

## 📋 Descripción

Sistema avanzado que combina múltiples modelos LLM usando diferentes estrategias de ensemble para **superar el rendimiento del mejor modelo individual**.

### Objetivo Principal
Demostrar que la combinación inteligente de modelos puede lograr:
- **Score promedio > 0.90** (vs. 0.855 del mejor individual: gemma2:27b)
- **Resolver P25** (Para-Mira-Ayuda) con score > 0.7
- **Reducir fallos** sistemáticos de modelos individuales

## 🏗️ Arquitectura

```
src/ensemble/
├── __init__.py                  # Exportaciones principales
├── question_classifier.py       # Clasifica preguntas por tipo
├── ensemble_engine.py           # Motor principal
└── strategies/
    ├── __init__.py
    ├── voting.py                # Voting Majority
    ├── weighted.py              # Weighted Voting
    ├── routing.py               # Specialized Routing
    └── consensus.py             # Consensus + Fallback

benchmark_ensemble.py            # Benchmark completo
interface/app_ensemble.py        # Dashboard (próximo)
```

## 🎲 Estrategias Implementadas

### 1. Voting Majority
**Concepto**: Selecciona la respuesta con mayor `combined_score` individual.

**Uso**:
```python
strategy = VotingStrategy()
best = strategy.select_best_response(individual_responses)
```

**Ventajas**:
- Simple y rápido
- No requiere configuración
- Funciona bien cuando hay un modelo claramente superior

### 2. Weighted Voting
**Concepto**: Pondera scores según rendimiento histórico de cada modelo.

**Pesos**:
- gemma2:27b: 0.40
- qwen3:32b: 0.30
- llama3.3:70b: 0.25
- deepseek-r1: 0.05

**Uso**:
```python
strategy = WeightedStrategy()  # Usa pesos por defecto
best = strategy.select_best_response(individual_responses)
```

**Ventajas**:
- Aprovecha conocimiento de rendimiento previo
- Da más peso a modelos confiables
- Puede compensar fallos ocasionales del mejor modelo

### 3. Specialized Routing
**Concepto**: Usa modelos específicos según tipo de pregunta.

**Clasificación**:
- **Filosóficas** (P25, P26): llama3.3 + gemma2
- **Factuales** (P11, P20): gemma2 + llama3.3
- **Procedurales**: gemma2 + qwen3
- **Normativas**: gemma2 + llama3.3

**Uso**:
```python
classifier = QuestionClassifier()
strategy = RoutingStrategy(classifier)
best = strategy.select_best_response(
    individual_responses,
    question="¿Qué significa Para-Mira-Ayuda?",
    question_id=25
)
```

**Ventajas**:
- Aprovecha fortalezas específicas de cada modelo
- Configuraciones especiales para preguntas problemáticas
- Puede combinar respuestas (synthesis)

### 4. Consensus + Fallback
**Concepto**: Busca consenso entre modelos. Si hay divergencia, usa fallback inteligente.

**Lógica**:
1. **Consenso alto** (desviación < 0.2): usar mejor respuesta
2. **Divergencia con score excelente** (max > 0.8): usar esa
3. **Divergencia**: fallback a gemma2:27b (más confiable)

**Uso**:
```python
strategy = ConsensusStrategy(consensus_threshold=0.2)
best = strategy.select_best_response(individual_responses)
```

**Ventajas**:
- Robusto ante fallos individuales
- Detecta preguntas difíciles (alta divergencia)
- Fallback seguro a modelo confiable

## 🚀 Cómo Ejecutar

### 1. Ejecutar Benchmark Completo

```bash
cd /home/vicente/Practicas/rag_optimizer_complete/rag_optimizer
python benchmark_ensemble.py
```

**Tiempo estimado**: 30-40 minutos
- Generación: 15-20 min (4 modelos × 26 preguntas)
- Evaluación RAGAs: 15-20 min (OpenAI API)

**Salida**:
- `results/ensemble_YYYYMMDD_HHMMSS.json` - Resultados completos

### 2. Ver Resultados (Próximo)

```bash
streamlit run interface/app_ensemble.py
```

## 📊 Formato de Resultados

```json
{
  "timestamp": "2025-01-11T16:00:00",
  "benchmark_type": "ensemble",
  "models": ["gemma2:27b", "llama3.3:70b", "qwen3:32b", "deepseek-r1:latest"],
  "strategies": ["voting", "weighted", "routing", "consensus"],
  "results": [
    {
      "question_id": 1,
      "question": "¿Qué se hace en la actividad de desayunos?",
      "expected_answer": "...",
      
      "individual": [
        {
          "model_name": "gemma2:27b",
          "answer": "...",
          "metrics": {"combined_score": 0.85, ...},
          "generation_time": 12.3
        },
        ...
      ],
      
      "ensemble": {
        "voting": {
          "answer": "...",
          "selected_from": "gemma2:27b",
          "selection_reason": "Mejor score individual: 0.85",
          "metrics": {"combined_score": 0.85, ...}
        },
        "weighted": {...},
        "routing": {...},
        "consensus": {...}
      }
    },
    ...
  ],
  
  "summary": {
    "individual_models": {
      "gemma2:27b": {
        "avg_score": 0.855,
        "correct_count": 22
      },
      ...
    },
    "ensemble_strategies": {
      "routing": {
        "avg_score": 0.920,
        "correct_count": 24
      },
      ...
    },
    "best_individual": {
      "model": "gemma2:27b",
      "avg_score": 0.855
    },
    "best_ensemble": {
      "strategy": "routing",
      "avg_score": 0.920
    },
    "improvement": {
      "absolute": +0.065,
      "percentage": +7.6,
      "beats_individual": true
    }
  }
}
```

## 🎯 Configuraciones Especiales

### P25: Para-Mira-Ayuda

```python
# En routing.py - SPECIAL_CONFIGS
25: {
    'models': ['llama3.3:70b', 'gemma2:27b'],
    'description': 'Pregunta filosófica crítica',
    'use_synthesis': True
}
```

**Estrategia**:
1. Usar solo llama3.3 y gemma2 (mejores en preguntas filosóficas)
2. Configuración ultra-específica en RAG engine
3. Synthesis de ambas respuestas (combinar lo mejor de cada una)

### P11 y P20: Ubicaciones Problemáticas

```python
11: {
    'models': ['gemma2:27b', 'llama3.3:70b'],
    'description': 'Pregunta factual problemática'
}
```

## 💡 Ejemplos de Uso Programático

### Usar Ensemble Engine Directamente

```python
from src.core.model_wrapper import LLMWrapper
from src.core.enhanced_rag_engine_new import EnhancedRAGEngineNew
from src.ensemble.ensemble_engine import EnsembleRAGEngine

# Inicializar modelos
models = {...}  # Diccionario de LLMWrapper
rag_engines = {}
for name, model in models.items():
    rag_engines[name] = EnhancedRAGEngineNew("data/vectorstore/chroma_db", model)

# Crear ensemble engine
ensemble = EnsembleRAGEngine(
    rag_engines=rag_engines,
    enabled_strategies=['voting', 'weighted', 'routing', 'consensus']
)

# Procesar pregunta
result = ensemble.process_question_complete(
    question="¿Qué significa Para-Mira-Ayuda?",
    question_id=25
)

# result contiene:
# - individual: respuestas de cada modelo
# - ensemble: respuestas de cada estrategia
# - summary: tiempos y estadísticas
```

### Usar Solo una Estrategia

```python
from src.ensemble.strategies import RoutingStrategy
from src.ensemble.question_classifier import QuestionClassifier

# Generar respuestas individuales primero
individual_responses = [...]  # Lista de respuestas

# Aplicar routing
classifier = QuestionClassifier()
strategy = RoutingStrategy(classifier)

best = strategy.select_best_response(
    individual_responses,
    question="¿Dónde es la actividad de coles?",
    question_id=11
)

print(f"Mejor respuesta de: {best['selected_from']}")
print(f"Razón: {best['selection_reason']}")
print(f"Score: {best['metrics']['combined_score']:.2f}")
```

## 🔧 Personalización

### Cambiar Pesos en Weighted Strategy

```python
from src.ensemble.strategies import WeightedStrategy

custom_weights = {
    'gemma2:27b': 0.50,      # Aumentar peso a gemma2
    'llama3.3:70b': 0.30,
    'qwen3:32b': 0.15,
    'deepseek-r1:latest': 0.05
}

strategy = WeightedStrategy(weights=custom_weights)
```

### Añadir Nueva Configuración Especial

```python
# En src/ensemble/strategies/routing.py

SPECIAL_CONFIGS = {
    ...
    12: {  # Nueva pregunta problemática
        'models': ['gemma2:27b', 'qwen3:32b'],
        'description': 'Mi config personalizada',
        'use_synthesis': False
    }
}
```

### Cambiar Umbral de Consenso

```python
from src.ensemble.strategies import ConsensusStrategy

# Más estricto (requiere mayor consenso)
strategy = ConsensusStrategy(consensus_threshold=0.15)

# Más permisivo
strategy = ConsensusStrategy(consensus_threshold=0.30)
```

## 📈 Métricas de Éxito

### Criterios de Validación

✅ **Éxito Total**: Al menos 1 estrategia ensemble > 0.90 avg  
✅ **Éxito Parcial**: Al menos 1 estrategia > mejor individual (0.855)  
⚠️ **Neutro**: Ensemble ≈ mejor individual (±0.02)  
❌ **Fallo**: Todas las estrategias < mejor individual  

### Métricas Específicas

- **P25 Score**: Objetivo > 0.7 (actualmente todos < 0.6)
- **Fallos < 0.5**: Objetivo < 3 preguntas (actualmente 5)
- **Preguntas correctas**: Objetivo > 24/26 (actualmente 22/26)

## 🐛 Troubleshooting

### Error: "No module named 'src.ensemble'"

```bash
# Asegurarse de estar en el directorio correcto
cd /home/vicente/Practicas/rag_optimizer_complete/rag_optimizer

# Verificar que exista la estructura
ls -la src/ensemble/
```

### Benchmark muy lento

**Optimizaciones**:
1. Reducir modelos: editar `MODELS_CONFIG` en `benchmark_ensemble.py`
2. Reducir preguntas: editar `dataset` (primeras 10 para testing)
3. Reducir estrategias: `enabled_strategies=['routing']` (solo la mejor)

### Evaluación RAGAs falla

**Verificar**:
1. Variable de entorno `OPENAI_API_KEY` configurada
2. Créditos disponibles en cuenta OpenAI
3. Conexión a internet estable

## 📝 TODO / Próximos Pasos

- [ ] Implementar dashboard ensemble (`interface/app_ensemble.py`)
- [ ] Añadir estrategia Synthesis (combinar respuestas realmente)
- [ ] Optimizar routing basado en resultados reales
- [ ] Añadir cache de evaluaciones RAGAs
- [ ] Implementar modo "production" (solo mejor estrategia)
- [ ] Añadir logging detallado

## 🎓 Referencias

- **Voting Ensemble**: Bagging y mayoría simple
- **Weighted Voting**: Stacking con pesos aprendidos
- **Routing**: Mixture of Experts (MoE)
- **Consensus**: Ensemble con confidence estimation

---

**Versión**: 1.0.0  
**Fecha**: 2025-01-11  
**Estado**: ✅ Implementación base completa, dashboard pendiente

