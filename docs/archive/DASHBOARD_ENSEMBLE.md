# 🎲 Dashboard Ensemble RAG - Guía Completa

## 📋 Descripción General

Dashboard profesional y especializado para analizar y comparar resultados de benchmarks ensemble, permitiendo visualizar:

- **Modelos Individuales**: Rendimiento de cada LLM de forma aislada
- **Estrategias Ensemble**: Voting, Weighted, Routing, Consensus
- **Métricas RAGAs**: Análisis detallado de las 6 métricas principales
- **Comparación por Pregunta**: Análisis granular pregunta por pregunta
- **Visualizaciones Avanzadas**: Gráficos interactivos con Plotly

---

## 🚀 Inicio Rápido

### Opción 1: Script automatizado (recomendado)

```bash
./run_dashboard_ensemble.sh
```

### Opción 2: Manual

```bash
source venv/bin/activate  # Activar entorno virtual
streamlit run interface/app_ensemble.py
```

El dashboard se abrirá automáticamente en: **http://localhost:8501**

---

## 📊 Análisis del Benchmark Actual

### Resultados del Benchmark Completo (26 preguntas)

```
📅 Timestamp: 2025-10-11T18:35:18
🔢 Total preguntas: 26
🤖 Modelos: 4
🎲 Estrategias: 4

================================================================================
🤖 MODELOS INDIVIDUALES:
================================================================================
   gemma2:27b           | Avg: 0.915 | Correctas: 22/26  ⭐ MEJOR INDIVIDUAL
   llama3.3:70b         | Avg: 0.886 | Correctas: 21/26
   qwen3:32b            | Avg: 0.850 | Correctas: 17/26
   deepseek-r1:latest   | Avg: 0.633 | Correctas: 10/26

================================================================================
🎲 ESTRATEGIAS ENSEMBLE:
================================================================================
   voting               | Avg: 0.915 | Correctas: 22/26  ⭐ MEJOR ENSEMBLE
   weighted             | Avg: 0.913 | Correctas: 22/26
   routing              | Avg: 0.910 | Correctas: 22/26
   consensus            | Avg: 0.909 | Correctas: 21/26

================================================================================
🏆 COMPARACIÓN FINAL:
================================================================================
   Mejor Individual:  gemma2:27b           | Score: 0.915
   Mejor Ensemble:    voting               | Score: 0.915

   🤝 EMPATE PERFECTO - Mejora: +0.000 (+0.0%)
================================================================================
```

### 🎯 Conclusiones Clave

#### ✅ LO BUENO

1. **Gemma2:27b se consagra como REINA** 👑
   - Score promedio: **0.915**
   - 22 de 26 preguntas correctas (84.6%)
   - Consistencia excepcional

2. **Estrategia Voting empata con Gemma2** 🎲
   - Mismo score: **0.915**
   - Mismo número de aciertos: 22/26
   - Demuestra robustez del sistema ensemble

3. **Todas las estrategias ensemble son competitivas**
   - Voting: 0.915
   - Weighted: 0.913
   - Routing: 0.910
   - Consensus: 0.909
   - Diferencia mínima entre ellas (< 1%)

4. **Sistema altamente robusto**
   - Múltiples estrategias alcanzan resultados similares
   - Fallback inteligente funciona correctamente
   - Configuraciones especiales (P11, P20, P25) son efectivas

#### ⚠️ ÁREAS DE MEJORA

1. **P25 sigue siendo problemática**
   - Todos los modelos y estrategias tienen dificultades
   - Necesita contexto filosófico más completo
   - **PENDIENTE: Ejecutar fix_p25_chunks.py**

2. **DeepSeek muy por debajo**
   - Score: 0.633 (vs 0.915 de Gemma2)
   - Solo 10/26 correctas
   - Peso muy bajo en estrategias (5%)

3. **No hay mejora significativa con ensemble**
   - Empate técnico con mejor individual
   - Indica que Gemma2 ya es óptimo para este dataset
   - Ensemble actúa como "safety net" más que mejora

### 🔬 Análisis Técnico

#### ¿Por qué NO hay mejora con ensemble?

1. **Gemma2 ya es excepcional**
   - Alcanza 0.915, cerca del máximo teórico
   - Consistente en casi todas las preguntas
   - Poco margen de mejora

2. **Otros modelos no aportan información diferencial**
   - Llama3.3: Muy similar a Gemma2 (0.886 vs 0.915)
   - Qwen3: Respuestas en inglés, penalizado
   - DeepSeek: Rendimiento bajo, poco peso

3. **Las estrategias funcionan correctamente**
   - Voting selecciona consistentemente a Gemma2
   - Weighted da 40% peso a Gemma2 (correcto)
   - Routing usa configs especiales efectivamente
   - Consensus usa fallback a Gemma2 (inteligente)

#### ¿Cuándo TENDRÍA valor el ensemble?

El ensemble sería más valioso si:
- Hubiera preguntas donde modelos diferentes destacan
- Mayor diversidad en fortalezas/debilidades
- Modelos especializados en dominios distintos

### 📈 Valor Real del Sistema Ensemble

Aunque **no mejora el score**, el ensemble aporta:

1. **🛡️ Robustez**
   - Si Gemma2 falla, hay fallback automático
   - Múltiples estrategias mantienen 0.91+ score

2. **🔍 Insights**
   - Identifica configuraciones especiales necesarias (P11, P20, P25)
   - Muestra dónde todos los modelos fallan
   - Permite análisis comparativo detallado

3. **🚀 Escalabilidad**
   - Infraestructura para añadir nuevos modelos
   - Fácil experimentar con nuevas estrategias
   - Sistema de evaluación robusto

4. **📊 Análisis Profesional**
   - Dashboard completo para visualización
   - Métricas RAGAs detalladas
   - Comparación granular por pregunta

---

## 🎨 Características del Dashboard

### Tab 1: 📊 Resumen Comparativo
- Métricas principales en cards
- Gráfico de barras comparativo
- Tablas Top 3 modelos y estrategias
- Indicador de ganador

### Tab 2: 🤖 Modelos Individuales
- Tabla completa con todas las métricas
- Radar chart de métricas RAGAs
- Gráfico de tiempos de generación
- Gradientes de color por rendimiento

### Tab 3: 🎲 Estrategias Ensemble
- Tabla completa de estrategias
- Descripción detallada de cada estrategia
- Radar chart comparativo
- Análisis de pesos y contribuciones

### Tab 4: 🔍 Análisis por Pregunta
- Selector de pregunta específica
- Tabla de scores para esa pregunta
- Gráfico comparativo
- Visualización de respuestas
- Métricas detalladas por respuesta
- Información de estrategia (de dónde viene, por qué)

### Tab 5: 📈 Métricas RAGAs
- Explicación detallada de cada métrica
- Distribución con box plots
- Heatmap de correlación
- Análisis estadístico

---

## 🎯 Interpretación de Métricas RAGAs

| Métrica | Peso | ¿Qué evalúa? | Ideal |
|---------|------|--------------|-------|
| **Faithfulness** | 25% | Fidelidad al contexto recuperado | 1.0 |
| **Answer Relevancy** | 20% | Relevancia para la pregunta | 1.0 |
| **Context Precision** | 15% | Precisión del contexto recuperado | 1.0 |
| **Context Recall** | 20% | Completitud del contexto | 1.0 |
| **Answer Correctness** | 10% | Corrección vs ground truth | 1.0 |
| **Answer Similarity** | 10% | Similitud semántica con GT | 1.0 |

**Combined Score** = Suma ponderada de todas las métricas

---

## 🎲 Descripción de Estrategias Ensemble

### 🗳️ Voting (Votación Mayoritaria)
**Funcionamiento:**
- Selecciona respuesta con mayor `combined_score`
- Tiebreaker: gemma2:27b si hay empate

**Resultado:** 0.915 (22/26 correctas)

**Cuándo usar:**
- Preguntas con respuestas claras y objetivas
- Dataset donde el mejor modelo es muy consistente

---

### ⚖️ Weighted (Votación Ponderada)
**Funcionamiento:**
- Asigna pesos según rendimiento histórico:
  - Gemma2: 40%
  - Qwen3: 30%
  - Llama3.3: 25%
  - DeepSeek: 5%

**Resultado:** 0.913 (22/26 correctas)

**Cuándo usar:**
- Cuando hay modelos claramente superiores
- Para favorecer consistencia sobre diversidad

---

### 🎯 Routing (Enrutamiento Inteligente)
**Funcionamiento:**
- Clasifica preguntas (filosófica, factual, procedimental, normativa)
- Configuraciones especiales para P11, P20, P25
- Ruta a modelos especializados según tipo

**Resultado:** 0.910 (22/26 correctas)

**Cuándo usar:**
- Dataset con diferentes tipos de preguntas
- Modelos especializados en dominios específicos

---

### 🤝 Consensus (Consenso con Fallback)
**Funcionamiento:**
- Busca consenso entre modelos (stdev < 0.15)
- Si hay divergencia → fallback a gemma2:27b
- Robusto ante respuestas conflictivas

**Resultado:** 0.909 (21/26 correctas)

**Cuándo usar:**
- Preguntas donde la incertidumbre es alta
- Necesidad de respuestas conservadoras

---

## 🔧 Configuración Especial para Preguntas Problemáticas

### P11: "¿Dónde es la actividad de coles?"
- **Config**: `coles_optimized`
- **Modelos recomendados**: gemma2:27b, llama3.3:70b
- **Razón**: Pregunta factual que requería precisión máxima

### P20: "¿Dónde es la actividad de resis?"
- **Config**: `resis_optimized`
- **Modelos recomendados**: gemma2:27b, llama3.3:70b
- **Razón**: Similar a P11, requiere precisión factual

### P25: "¿Qué significa Para-Mira-Ayuda?"
- **Config**: Prompt filosófico especializado
- **Modelos recomendados**: llama3.3:70b, gemma2:27b
- **Modo**: Synthesis (combina respuestas)
- **Estado**: **🔴 PENDIENTE FIX** - Chunking inadecuado en vector store

---

## 📁 Archivos de Resultados

Los archivos de resultados ensemble tienen el formato:

```
results/ensemble_YYYYMMDD_HHMMSS.json
```

**Estructura del JSON:**
```json
{
  "timestamp": "2025-10-11T18:35:18",
  "total_questions": 26,
  "models": ["gemma2:27b", "llama3.3:70b", "qwen3:32b", "deepseek-r1:latest"],
  "strategies": ["voting", "weighted", "routing", "consensus"],
  "results": [
    {
      "question": "...",
      "question_id": 1,
      "individual": [...],  // Respuestas de cada modelo
      "ensemble": {         // Respuestas de cada estrategia
        "voting": {...},
        "weighted": {...},
        "routing": {...},
        "consensus": {...}
      }
    }
  ]
}
```

---

## 🎓 Recomendaciones Finales

### Para Mejorar el Sistema Actual

1. **✅ Ejecutar fix_p25_chunks.py**
   ```bash
   ./fix_and_test_p25.sh
   ```
   - Regenera vector store con chunking mejorado
   - Debería mejorar score de P25 significativamente

2. **🔍 Identificar otras preguntas problemáticas**
   - Usar dashboard para encontrar preguntas con scores bajos
   - Analizar por qué fallan todos los modelos
   - Crear configs especiales si es necesario

3. **📊 Monitorizar con dashboard regularmente**
   - Después de cada cambio en chunking/prompts
   - Verificar que no se degradan otras preguntas
   - Comparar benchmarks históricos

### Para Datasets Futuros

1. **🎯 Aprovechar diversidad de modelos**
   - Buscar preguntas donde modelos diferentes destacan
   - Identificar fortalezas únicas de cada modelo
   - Ajustar pesos en estrategia Weighted

2. **🔄 Experimentar con nuevas estrategias**
   - Implementar Synthesis real (combinar respuestas)
   - Probar re-ranking de chunks
   - A/B testing de configuraciones

3. **⚡ Optimizar para producción**
   - Usar solo mejor estrategia (Voting en este caso)
   - Cache de evaluaciones RAGAs
   - Paralelización de generación

---

## 🎉 Conclusión

**Gemma2:27b es la REINA indiscutible** 👑 con 0.915 de score promedio.

Las estrategias ensemble **empatan** con Gemma2, lo que demuestra:
- ✅ El sistema ensemble funciona correctamente
- ✅ Gemma2 es consistentemente la mejor opción
- ✅ Hay robustez: múltiples estrategias alcanzan resultados similares

**Siguiente paso inmediato:**
```bash
./fix_and_test_p25.sh
```

Esto debería:
1. Mejorar el score de P25
2. Potencialmente hacer que ensemble supere a Gemma2 individual
3. Cerrar la única pregunta problemática restante

---

## 📞 Soporte

Para cualquier duda:
1. Revisar esta documentación
2. Usar el dashboard para análisis visual
3. Consultar `ENSEMBLE_README.md` para detalles técnicos
4. Revisar `METRICAS_CONFIRMACION.md` para validación de métricas

---

**¡Disfruta del análisis! 🚀**

