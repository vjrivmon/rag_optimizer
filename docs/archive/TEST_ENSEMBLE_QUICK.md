# 🧪 Test Rápido - Benchmark Ensemble

## 🎯 Objetivo

Validar que el sistema de ensemble funciona correctamente **antes** de ejecutar el benchmark completo de 40+ minutos.

## 📝 Preguntas de Prueba

El test ejecuta **3 preguntas conflictivas** que históricamente han tenido problemas:

| ID | Pregunta | Problema Histórico |
|----|----------|-------------------|
| **P11** | ¿Qué se hace en la actividad de coles? | ❌ Fallo crítico: contexto correcto, respuesta incorrecta |
| **P20** | ¿Dónde es la actividad de resis? | ❌ Fallo crítico: respuestas vagas e incorrectas |
| **P25** | ¿Qué significa Para-Mira-Ayuda? | ❌ Fallo filosófico: todos los modelos fallan |

## ⏱️ Tiempo Estimado

- **Generación**: 3-5 minutos (3 preguntas × 4 modelos × 4 estrategias)
- **Evaluación RAGAs**: 1-2 minutos (24 respuestas)
- **Total**: **5-8 minutos**

vs. Benchmark completo: 40-50 minutos

## 🚀 Ejecución

### Opción 1: Script automatizado
```bash
./run_quick_test.sh
```

### Opción 2: Manual
```bash
cd /home/vicente/Practicas/rag_optimizer_complete/rag_optimizer
source venv/bin/activate
python test_ensemble_quick.py
```

## 📊 Qué Valida Este Test

### ✅ Funcionalidad
1. **Carga de modelos**: Los 4 modelos se inicializan correctamente
2. **Sistema Ensemble**: Las 4 estrategias funcionan
3. **Generación**: Se generan respuestas individuales + ensemble
4. **Serialización**: Los objetos `ValidationResult` se convierten correctamente a JSON
5. **Evaluación RAGAs**: OpenAI evalúa todas las respuestas
6. **Guardado**: El archivo JSON final se guarda sin errores

### 📈 Resultados Esperados

El test generará:

```
results/
├── ensemble_test_YYYYMMDD_HHMMSS.json        # Progreso intermedio
└── ensemble_test_final_YYYYMMDD_HHMMSS.json  # Resultado final
```

### 🔍 Estructura del Resultado

```json
{
  "timestamp": "2025-10-11T...",
  "benchmark_type": "ensemble_quick_test",
  "test_questions": [11, 20, 25],
  "models": ["gemma2:27b", "llama3.3:70b", "qwen3:32b", "deepseek-r1:latest"],
  "strategies": ["voting", "weighted", "routing", "consensus"],
  "total_questions": 3,
  "results": [
    {
      "question": "¿Qué se hace en la actividad de coles?",
      "question_id": 11,
      "individual": [
        {
          "model_name": "gemma2:27b",
          "answer": "...",
          "contexts": [...],
          "metrics": {
            "combined_score": 0.XXX,
            "faithfulness": 0.XXX,
            ...
          },
          "validation": {...},
          "config_used": {...}
        },
        ...
      ],
      "ensemble": [
        {
          "strategy": "voting",
          "answer": "...",
          "metrics": {
            "combined_score": 0.XXX,
            ...
          },
          "selected_from": "gemma2:27b",
          ...
        },
        ...
      ]
    },
    ...
  ]
}
```

## 📋 Output del Test

El test mostrará:

```
🧪 TEST RÁPIDO - BENCHMARK ENSEMBLE
================================================================================

📊 Configuración:
   Preguntas de prueba: [11, 20, 25]
   Modelos: 4
   Estrategias: 4
   Total preguntas: 3

🔧 Inicializando modelos...
   ✅ gemma2:27b listo
   ✅ llama3.3:70b listo
   ✅ qwen3:32b listo
   ✅ deepseek-r1:latest listo

🎲 Ensemble Engine inicializado con 4 modelos

📝 FASE 1/2: Generación de Respuestas
================================================================================

[1/3] P11: ¿Qué se hace en la actividad de coles?
   🤖 Generando con gemma2:27b...
   ...
   🎲 Aplicando estrategia: voting
   ...

✅ GENERACIÓN COMPLETADA en X.X minutos

📈 FASE 2/2: Evaluación RAGAs
================================================================================
   P11: Evaluando 4 individuales + 4 ensemble...
      ✅ gemma2:27b: 0.XXX
      ✅ voting: 0.XXX
   ...

✅ TEST RÁPIDO COMPLETADO
================================================================================

📊 RESUMEN POR PREGUNTA
================================================================================

P11: ¿Qué se hace en la actividad de coles?...
   🥇 Mejor individual: gemma2:27b (0.XXX)
   🎯 Mejor ensemble: voting (0.XXX)
   ✅ Ensemble mejora: +0.XXX
```

## ✅ Criterios de Éxito

El test es **exitoso** si:

1. ✅ **Todos los modelos cargan** sin errores
2. ✅ **Todas las respuestas se generan** (3 × 4 = 12 individuales + 3 × 4 = 12 ensemble)
3. ✅ **No hay errores de serialización** al guardar JSON
4. ✅ **Todas las respuestas se evalúan** con RAGAs (24 evaluaciones)
5. ✅ **El archivo final se crea** correctamente

## 🚦 Siguiente Paso

### Si el test es exitoso ✅
```bash
python benchmark_ensemble.py
```
Ejecutar el benchmark completo con las 26 preguntas.

### Si el test falla ❌
Revisar los logs para identificar el error específico y corregir antes de ejecutar el benchmark completo.

## 🔧 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'openai'"
```bash
source venv/bin/activate
pip install openai
```

### Error: "Connection timeout"
- El servidor de modelos puede estar sobrecargado
- Esperar unos minutos y reintentar

### Error: "ValidationResult is not JSON serializable"
- **Ya está solucionado** en la versión actual
- Si persiste, revisar `src/ensemble/ensemble_engine.py`

## 📚 Archivos Relacionados

- `test_ensemble_quick.py`: Script principal del test
- `run_quick_test.sh`: Script de ejecución rápida
- `benchmark_ensemble.py`: Benchmark completo (usar después del test)
- `src/ensemble/`: Módulos del sistema ensemble

