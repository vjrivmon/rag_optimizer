# 🚀 Benchmark Paralelo Optimizado

## Problema Original
El benchmark secuencial tardaba **~3.5 horas** en evaluar 26 preguntas con 4 modelos y métricas RAGAs completas.

## Solución: Paralelización Multinivel

### ⚡ Optimizaciones Implementadas

1. **Paralelización de Preguntas**
   - Divide las preguntas en lotes
   - Procesa múltiples lotes en paralelo
   - Workers independientes (ProcessPoolExecutor)

2. **Modos de Evaluación RAGAs**
   - **Fast** (2 métricas): faithfulness + answer_similarity (~30s)
   - **Normal** (4 métricas): + answer_relevancy + context_recall (~60s)
   - **Full** (6 métricas): Todas las métricas (~120s)

3. **Sistema de Caché** (opcional)
   - Cachea evaluaciones RAGAs por hash(pregunta+respuesta+contexto)
   - Evita re-evaluar combinaciones idénticas

4. **Timeouts Adaptativos**
   - Modo fast: 120s timeout
   - Modo normal: 180s timeout
   - Modo full: 300s timeout

## 📊 Resultados Esperados

| Configuración | Tiempo Estimado | Reducción |
|--------------|-----------------|-----------|
| **Secuencial (original)** | ~3.5 horas | Baseline |
| **Paralelo + Full** | ~60 minutos | 71% |
| **Paralelo + Normal** | ~45 minutos | 78% |
| **Paralelo + Fast** | ~30 minutos | 85% |
| **Con Caché (2da ejecución)** | ~15 minutos | 93% |

## 🔧 Uso

### Ejecución Básica

```bash
# Modo rápido (recomendado para pruebas)
python benchmark_parallel.py --max-questions 5 --ragas-mode fast

# Evaluación completa en modo normal
python benchmark_parallel.py --ragas-mode normal

# Máximo rendimiento (4 workers, modo fast)
python benchmark_parallel.py --workers 4 --ragas-mode fast
```

### Parámetros

- `--max-questions N`: Limita a N preguntas (útil para pruebas)
- `--workers N`: Número de workers paralelos (default: CPUs-1, max 4)
- `--ragas-mode {fast|normal|full}`: Nivel de detalle de métricas

### Ejemplos de Uso

```bash
# Test rápido (2 preguntas, 2 métricas)
python benchmark_parallel.py --max-questions 2 --ragas-mode fast
# Tiempo esperado: ~2-3 minutos

# Evaluación media (10 preguntas, 4 métricas)
python benchmark_parallel.py --max-questions 10 --ragas-mode normal --workers 3
# Tiempo esperado: ~15 minutos

# Benchmark completo optimizado (26 preguntas, 2 métricas)
python benchmark_parallel.py --ragas-mode fast --workers 4
# Tiempo esperado: ~30 minutos

# Benchmark completo detallado (26 preguntas, 6 métricas)
python benchmark_parallel.py --ragas-mode full --workers 4
# Tiempo esperado: ~60 minutos
```

## 📈 Comparación de Rendimiento

### Benchmark de 26 preguntas × 4 modelos = 104 evaluaciones

| Método | Métricas | Workers | Tiempo | Speedup |
|--------|----------|---------|--------|---------|
| Secuencial | 6 | 1 | ~210 min | 1.0x |
| Paralelo | 6 | 4 | ~60 min | 3.5x |
| Paralelo | 4 | 4 | ~45 min | 4.7x |
| **Paralelo** | **2** | **4** | **~30 min** | **7.0x** |
| Paralelo + Caché | 2 | 4 | ~15 min | 14.0x |

## 🔍 Monitoreo

Durante la ejecución verás:

```
🚀 BENCHMARK PARALELO OPTIMIZADO
================================================================================
📋 Configuración:
   • Preguntas: 26
   • Modelos: 4
   • Workers: 4
   • Modo RAGAs: fast
   • Total evaluaciones: 104
================================================================================

⚡ Ejecutando 4 lotes en paralelo...
   📦 Lote 1: 7 preguntas
   📦 Lote 2: 7 preguntas
   📦 Lote 3: 6 preguntas
   📦 Lote 4: 6 preguntas

   Worker procesando pregunta 1: ¿Qué se hace en la actividad de desayunos?...
      ✓ qwen3:32b: 0.766 (18.5s)
      ✓ deepseek-r1:latest: 0.677 (14.2s)
      ✓ gemma2:27b: 0.703 (12.1s)
      ✓ llama3.3:70b: 0.746 (25.4s)
```

## 🎯 Recomendaciones

1. **Para desarrollo/testing**: Usa `--ragas-mode fast` con 2-5 preguntas
2. **Para evaluación rápida**: Usa `--ragas-mode normal` con todos los modelos
3. **Para análisis completo**: Usa `--ragas-mode full` (preparar ~1 hora)
4. **Para máximo rendimiento**: Usa 4 workers en modo fast con caché activado

## 🐛 Troubleshooting

### Error: "Connection timeout"
- El servidor Ollama puede estar saturado
- Solución: Reducir workers a 2-3

### Error: "Out of memory"
- Demasiados procesos paralelos
- Solución: Reducir workers a 2

### Resultados inconsistentes
- Los modelos pueden dar respuestas diferentes
- Solución: Usar temperatura 0.0 (ya configurado)

## 📊 Archivos de Salida

Los resultados se guardan en `results/parallel_YYYYMMDD_HHMMSS.json` con:
- Respuestas completas de cada modelo
- Métricas RAGAs calculadas
- Tiempos de respuesta
- Estadísticas de rendimiento
- Comparación con benchmark secuencial

## 🔄 Próximas Mejoras

- [ ] Balanceo dinámico de carga
- [ ] API REST para ejecución remota
- [ ] Dashboard en tiempo real
- [ ] Exportación a Excel/PDF automática
- [ ] Integración con MLflow para tracking