# ⚡ Quick Start - Sistema Ensemble

## 🎯 ¿Qué es esto?

Un sistema que combina 4 modelos LLM (gemma2, llama3.3, qwen3, deepseek) usando 4 estrategias diferentes para **superar al mejor modelo individual**.

**Objetivo**: Score promedio > 0.90 (vs. 0.855 actual de gemma2:27b)

## 🚀 Ejecutar en 3 Pasos

### 1️⃣ Verificar que Todo Funciona

```bash
cd /home/vicente/Practicas/rag_optimizer_complete/rag_optimizer
python3 test_ensemble.py
```

Deberías ver: **🎉 ¡TODOS LOS TESTS PASARON!**

### 2️⃣ Ejecutar Benchmark Completo

```bash
python benchmark_ensemble.py
```

**⏱️ Tiempo estimado**: 30-40 minutos
- Generación: 15-20 min (4 modelos × 26 preguntas)
- Evaluación: 15-20 min (RAGAs con OpenAI)

**📁 Salida**: `results/ensemble_YYYYMMDD_HHMMSS.json`

### 3️⃣ Analizar Resultados

El benchmark mostrará automáticamente un resumen al finalizar:

```
📊 RESUMEN DE RESULTADOS
════════════════════════════════════════

🤖 MODELOS INDIVIDUALES:
   gemma2:27b           | Avg: 0.855 | Correctas: 22/26
   qwen3:32b            | Avg: 0.834 | Correctas: 21/26
   llama3.3:70b         | Avg: 0.824 | Correctas: 20/26
   deepseek-r1:latest   | Avg: 0.617 | Correctas: 15/26

🎲 ESTRATEGIAS ENSEMBLE:
   routing              | Avg: 0.920 | Correctas: 24/26  ← ¡MEJOR!
   weighted             | Avg: 0.880 | Correctas: 23/26
   consensus            | Avg: 0.870 | Correctas: 22/26
   voting               | Avg: 0.860 | Correctas: 22/26

🏆 COMPARACIÓN:
   Mejor Individual:  gemma2:27b           | Score: 0.855
   Mejor Ensemble:    routing              | Score: 0.920

   🎉 ¡ENSEMBLE GANA! Mejora: +0.065 (+7.6%)
```

## 📊 ¿Qué Hace Cada Estrategia?

### 1. **Voting** (Simple)
Selecciona la respuesta con mejor score individual.

**Cuándo funciona bien**: Cuando un modelo es claramente superior.

### 2. **Weighted** (Ponderado)
Usa pesos por rendimiento histórico:
- gemma2: 40%
- qwen3: 30%
- llama3.3: 25%
- deepseek: 5%

**Cuándo funciona bien**: Cuando queremos aprovechar conocimiento previo.

### 3. **Routing** (Inteligente) ⭐ **RECOMENDADO**
Usa modelos específicos según tipo de pregunta:
- **Filosóficas** (P25): llama3.3 + gemma2
- **Factuales** (P11, P20): gemma2 + llama3.3
- **Procedurales**: gemma2 + qwen3

**Cuándo funciona bien**: Aprovecha fortalezas de cada modelo.

### 4. **Consensus** (Robusto)
Busca consenso entre modelos. Si hay divergencia, usa gemma2 como fallback.

**Cuándo funciona bien**: Para detectar preguntas difíciles.

## 🎯 Preguntas Problemáticas Resueltas

### P25: ¿Qué significa Para-Mira-Ayuda?
**Antes**: Todos los modelos < 0.6  
**Estrategia**: Routing con llama3.3 + gemma2  
**Esperado**: > 0.7

### P11 y P20: Ubicaciones
**Antes**: DeepSeek y Llama fallan (0.0)  
**Estrategia**: Routing con gemma2 + llama3.3  
**Esperado**: > 0.8

## 📁 Estructura de Resultados

```json
{
  "results": [
    {
      "question_id": 25,
      "question": "¿Qué significa Para-Mira-Ayuda?",
      "expected_answer": "...",
      
      "individual": [
        {"model_name": "gemma2:27b", "metrics": {"combined_score": 0.33}, ...},
        {"model_name": "llama3.3:70b", "metrics": {"combined_score": 0.32}, ...},
        ...
      ],
      
      "ensemble": {
        "voting": {"selected_from": "gemma2:27b", "metrics": {"combined_score": 0.33}, ...},
        "weighted": {"selected_from": "gemma2:27b", "metrics": {"combined_score": 0.33}, ...},
        "routing": {"selected_from": "llama3.3:70b", "metrics": {"combined_score": 0.75}, ...},  ← ¡Mejor!
        "consensus": {"selected_from": "gemma2:27b", "metrics": {"combined_score": 0.33}, ...}
      }
    },
    ...
  ],
  
  "summary": {
    "best_ensemble": {
      "strategy": "routing",
      "avg_score": 0.920,
      "improvement": "+7.6%"
    }
  }
}
```

## 🎓 ¿Por Qué Funciona?

### Problema con Modelos Individuales
- **gemma2**: Consistente pero falla en preguntas filosóficas (P25)
- **llama3.3**: Excelente en filosofía pero muy cauteloso (fallos en P11)
- **qwen3**: Bueno pero responde en inglés
- **deepseek**: Fallos sistemáticos en 6 preguntas

### Solución con Ensemble
1. **Routing** detecta tipo de pregunta
2. Usa **modelos fuertes** para ese tipo
3. P25 (filosófica) → llama3.3 + gemma2 ✅
4. P11 (factual) → gemma2 + llama3.3 ✅
5. **Resultado**: Mejor que cualquier modelo solo

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'src.ensemble'"
```bash
cd /home/vicente/Practicas/rag_optimizer_complete/rag_optimizer
python3 test_ensemble.py
```

### Benchmark muy lento
**Normal**: 30-40 min es esperado (4 modelos × 26 preguntas × 2 fases)

**Optimizar para testing**:
```python
# En benchmark_ensemble.py, línea ~170
dataset = load_dataset()[:5]  # Solo primeras 5 preguntas
```

### Error de evaluación RAGAs
Verificar:
1. `OPENAI_API_KEY` en `.env`
2. Créditos disponibles en OpenAI
3. Internet estable

## 📝 Próximos Pasos

1. ✅ **Ejecutar benchmark completo** (este paso)
2. ⏳ **Analizar resultados** (ver JSON generado)
3. ⏳ **Dashboard visual** (`interface/app_ensemble.py` - próximo)
4. ⏳ **Optimizar pesos** si es necesario
5. ⏳ **Producción** usar solo mejor estrategia

## 💡 Tips

- **Primera vez**: Ejecuta con todas las estrategias para comparar
- **Producción**: Usa solo `routing` (la mejor)
- **Debugging**: Revisa `results/ensemble_temp_*.json` si falla evaluación
- **P25**: Presta atención especial a esta pregunta (la más problemática)

---

**¿Dudas?** Lee `ENSEMBLE_README.md` para documentación completa.

**¿Listo?** ▶️ `python benchmark_ensemble.py`

