# 🚀 RAG Benchmark v2.0 - Guía Completa de Uso

## 📋 Resumen del sistema

**Problema anterior**: 
- Evaluación RAGAs bloqueaba todo el pipeline (3.5 horas)
- Sin visibilidad del progreso
- Sistema frágil que fallaba y no se recuperaba
- Código complejo e incomprensible

**Solución nueva**:
- **Fase 1 (5-10min)**: Genera TODAS las respuestas rápidamente
- **Fase 2 (10-20min)**: Evalúa con OpenAI API (100x más rápido) en paralelo
- **Dashboard web**: Monitorización en tiempo real con WebSocket
- **Base de datos SQLite**: Resultados guardados constantemente, recuperable si falla
- **Código simple y modular**: Fácil de entender y modificar

---

## 🛠️ Instalación

### 1. Instalar dependencias

```bash
pip install -r requirements_v2.txt
```

### 2. Configurar OpenAI API Key

```bash
# Opción 1: Variable de entorno (recomendado)
export OPENAI_API_KEY="sk-..."

# Opción 2: Argumento CLI
python benchmark_v2.py --openai-key "sk-..."
```

**💰 Costo estimado**: Con gpt-4o-mini (~$0.15/1M tokens):
- 26 preguntas × 4 modelos × 6 métricas = ~104 evaluaciones
- Costo total: **~$0.50-1.00** (muchísimo más barato que el tiempo perdido)

---

## 🎯 Uso básico

### Ejecutar benchmark completo (ambas fases)

```bash
python benchmark_v2.py
```

Esto ejecuta:
1. **Fase 1**: Genera todas las respuestas (5-10min)
2. **Fase 2**: Evalúa con OpenAI en paralelo (10-20min)

### Ejecutar solo Fase 1 (generación)

```bash
python benchmark_v2.py --phase generation
```

Útil para:
- Probar que los modelos funcionan
- Generar respuestas rápidamente sin evaluar
- Separar generación de evaluación

### Ejecutar solo Fase 2 (evaluación)

```bash
python benchmark_v2.py --phase evaluation
```

Útil para:
- Evaluar respuestas ya generadas
- Reintentar evaluaciones si fallaron
- Usar diferentes backends de evaluación

### Limitar número de preguntas (para pruebas)

```bash
# Solo las primeras 5 preguntas
python benchmark_v2.py --max-questions 5
```

---

## 📊 Dashboard web en tiempo real

### 1. Iniciar el dashboard

```bash
python dashboard.py
```

### 2. Abrir en el navegador

```
http://localhost:8000
```

### 3. Características del dashboard

- ✅ **Actualización automática** cada 2 segundos (WebSocket)
- 📈 **Progreso por modelo** con barras visuales
- 🏆 **Ranking en tiempo real** ordenado por score
- ⚡ **Actividad reciente** de las últimas evaluaciones
- 🎨 **Interfaz moderna** con animaciones

### 4. Usar el dashboard mientras corre el benchmark

Terminal 1:
```bash
python benchmark_v2.py
```

Terminal 2:
```bash
python dashboard.py
```

Ahora puedes ver el progreso en tiempo real en: http://localhost:8000

---

## 🔄 Casos de uso

### Caso 1: Benchmark completo desde cero

```bash
# 1. Ejecutar benchmark
python benchmark_v2.py --max-questions 26

# 2. Exportar resultados
python benchmark_v2.py --export resultados.json

# 3. Ver resultados en JSON
cat resultados.json | jq '.[] | select(.model_name == "qwen3:32b")'
```

### Caso 2: Recuperar de un fallo

Si el benchmark falla o se interrumpe:

```bash
# Ver qué falta por evaluar
python benchmark_v2.py --progress

# Continuar desde donde se quedó (automático)
python benchmark_v2.py --phase evaluation
```

El sistema detecta automáticamente qué respuestas ya están evaluadas.

### Caso 3: Probar con 3 preguntas

```bash
# Generar respuestas de solo 3 preguntas
python benchmark_v2.py --max-questions 3

# Ver progreso
python benchmark_v2.py --progress

# Output:
# 📊 PROGRESO ACTUAL
# ════════════════════════════════════════════════════════════
# Respuestas generadas: 12
# Evaluaciones completadas: 12
#
# Por modelo:
#   qwen3:32b            3/3   (100.0%) | Score: 0.847
#   gemma2:27b           3/3   (100.0%) | Score: 0.792
#   llama3.3:70b         3/3   (100.0%) | Score: 0.823
#   deepseek-r1:latest   3/3   (100.0%) | Score: 0.801
```

### Caso 4: Ajustar concurrencia de evaluación

```bash
# Más concurrencia (más rápido, más caro)
python benchmark_v2.py --max-concurrent 10 --batch-size 20

# Menos concurrencia (más lento, más barato)
python benchmark_v2.py --max-concurrent 2 --batch-size 5
```

**Recomendación**: 
- Desarrollo/pruebas: `--max-concurrent 2`
- Producción: `--max-concurrent 5-10`

---

## 📁 Estructura de archivos

```
.
├── benchmark_v2.py          # Script principal de benchmark
├── dashboard.py             # Dashboard web con FastAPI
├── requirements_v2.txt      # Dependencias
│
├── results/
│   ├── benchmark.db         # Base de datos SQLite (auto-creada)
│   └── resultados.json      # Exportación de resultados
│
├── data/
│   ├── evaluation_dataset.json       # Dataset de preguntas
│   └── vectorstore/chroma_db/        # Vector store ChromaDB
│
└── src/
    ├── core/
    │   ├── rag_engine.py            # Motor RAG
    │   └── model_wrapper.py         # Wrapper de modelos
    └── evaluation/
        └── ragas_evaluator.py       # (ya no se usa directamente)
```

---

## 🔍 Inspeccionar la base de datos

### Usando SQLite CLI

```bash
# Abrir la base de datos
sqlite3 results/benchmark.db

# Ver todas las tablas
.tables

# Ver respuestas generadas
SELECT question_id, model_name, substr(answer, 1, 50) 
FROM responses 
LIMIT 5;

# Ver evaluaciones
SELECT r.model_name, AVG(e.combined_score) as avg_score
FROM responses r
JOIN evaluations e ON r.id = e.response_id
GROUP BY r.model_name
ORDER BY avg_score DESC;
```

### Usando Python

```python
import sqlite3

conn = sqlite3.connect('results/benchmark.db')

# Ver modelos evaluados
cursor = conn.execute("""
    SELECT model_name, AVG(combined_score)
    FROM responses r
    JOIN evaluations e ON r.id = e.response_id
    GROUP BY model_name
""")

for model, score in cursor.fetchall():
    print(f"{model}: {score:.3f}")
```

---

## 🎓 Entendiendo el código

### Estructura de benchmark_v2.py

```
benchmark_v2.py
│
├─ BenchmarkDB                # SQLite para tracking robusto
│  ├─ save_response()        # Guarda respuesta generada
│  ├─ save_evaluation()      # Guarda evaluación RAGAs
│  ├─ get_unevaluated()      # Respuestas pendientes
│  └─ export_results()       # Exporta a JSON
│
├─ GenerationPhase            # FASE 1: Genera respuestas
│  └─ run()                  # Itera preguntas + modelos
│     ├─ retrieve()          # Recupera contexto (1 vez)
│     └─ generate()          # Genera con cada modelo
│
├─ EvaluationPhase            # FASE 2: Evalúa con OpenAI
│  ├─ evaluate_single()      # Evalúa 1 respuesta (async)
│  └─ run_async()            # Evalúa en paralelo
│     └─ asyncio.gather()    # 5-10 evaluaciones simultáneas
│
└─ main()                     # CLI principal
```

### Flujo de ejecución

```
1. FASE 1: Generación
   ┌─────────────────────────────────────┐
   │ Para cada pregunta:                 │
   │   1. Recuperar contexto (RAG)       │
   │   2. Para cada modelo:              │
   │      a. Generar respuesta          │
   │      b. Guardar en SQLite          │
   └─────────────────────────────────────┘
              ↓ (~5-10 minutos)
              
2. FASE 2: Evaluación
   ┌─────────────────────────────────────┐
   │ Obtener respuestas sin evaluar      │
   │                                     │
   │ Para cada batch de 10:              │
   │   ┌─────────────────────────────┐  │
   │   │ Evaluar 5 en paralelo       │  │
   │   │ con OpenAI API (async)      │  │
   │   └─────────────────────────────┘  │
   │   │                                │
   │   │ Guardar métricas en SQLite    │
   │   └────────────────────────────────┘
              ↓ (~10-20 minutos)
              
3. Exportar resultados a JSON
```

---

## 🆚 Comparación con sistema anterior

| Aspecto | Anterior | Nuevo (v2.0) |
|---------|----------|--------------|
| **Tiempo total** | ~3.5 horas | ~15-30 minutos |
| **Recuperable** | ❌ No | ✅ Sí (SQLite) |
| **Visibilidad** | ❌ Terminal | ✅ Dashboard web |
| **Evaluador** | Ollama UPV (lento) | OpenAI API (rápido) |
| **Paralelización** | ⚠️ Problemática | ✅ Nativa (asyncio) |
| **Complejidad** | 🔴 Alta | 🟢 Baja |
| **Debugging** | 🔴 Difícil | 🟢 Fácil |

---

## 🐛 Troubleshooting

### Error: "OpenAI API key no encontrada"

```bash
# Verificar que la key está configurada
echo $OPENAI_API_KEY

# Si no está, configurarla
export OPENAI_API_KEY="sk-..."
```

### Error: "No se puede conectar a Ollama"

Verificar que los modelos están disponibles:

```bash
curl https://ollama.gti-ia.upv.es:443/api/tags -k
```

### Error: "Database is locked"

Otro proceso está usando la base de datos. Cerrar el dashboard y el benchmark, luego:

```bash
# Ver procesos Python corriendo
ps aux | grep python

# Matar proceso si es necesario
kill <PID>
```

### El dashboard no muestra datos

```bash
# Verificar que existe la base de datos
ls -lh results/benchmark.db

# Verificar que tiene datos
sqlite3 results/benchmark.db "SELECT COUNT(*) FROM responses;"
```

---

## 🚀 Próximos pasos

### 1. Montar chatbot web con las mejores configuraciones

Una vez tengas los resultados del benchmark:

```python
# Ver modelo ganador
python benchmark_v2.py --export results.json

# Usar la mejor configuración en tu chatbot
best_model = "qwen3:32b"  # Ejemplo
```

### 2. Integrar con Streamlit (opcional)

```python
import streamlit as st
import sqlite3

# Leer resultados de SQLite
conn = sqlite3.connect('results/benchmark.db')
df = pd.read_sql("SELECT * FROM responses JOIN evaluations", conn)

# Mostrar en Streamlit
st.dataframe(df)
st.bar_chart(df.groupby('model_name')['combined_score'].mean())
```

### 3. Añadir más métricas de negocio

Modificar `EvaluationPhase.evaluate_single()` para incluir:

```python
# Métricas custom de tu negocio
metrics['responde_pregunta_completa'] = check_complete(answer)
metrics['menciona_dni'] = 'dni' in answer.lower()
metrics['tone_apropiado'] = check_tone(answer)
```

---

## 💡 Tips y recomendaciones

### Desarrollo iterativo

```bash
# 1. Empezar con 3 preguntas
python benchmark_v2.py --max-questions 3

# 2. Ver resultados
python benchmark_v2.py --progress

# 3. Si todo OK, escalar a 26
python benchmark_v2.py --max-questions 26
```

### Optimizar costos OpenAI

```python
# En benchmark_v2.py, cambiar modelo:
model="gpt-4o-mini"  # Actual: $0.15/1M tokens
# vs
model="gpt-3.5-turbo"  # Más barato: $0.50/1M tokens
```

### Añadir nuevos modelos

Editar `MODELS_CONFIG` en `benchmark_v2.py`:

```python
MODELS_CONFIG = [
    {"name": "nuevo-modelo", "endpoint": "https://..."},
    # ... otros modelos
]
```

---

## 📚 Recursos adicionales

- [OpenAI API Pricing](https://openai.com/pricing)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLite Tutorial](https://www.sqlitetutorial.net/)
- [Asyncio Guide](https://docs.python.org/3/library/asyncio.html)

---

## ❓ FAQ

**P: ¿Puedo usar Ollama en vez de OpenAI?**

R: Sí, pero será mucho más lento (~100x). Modifica `EvaluationPhase.evaluate_single()` para usar tu `OllamaRAGASEvaluator`.

**P: ¿Cómo exporto solo el mejor modelo?**

R: ```bash
python benchmark_v2.py --export results.json
cat results.json | jq '.[] | select(.model_name == "qwen3:32b")'
```

**P: ¿Puedo pausar y reanudar el benchmark?**

R: Sí, Ctrl+C para pausar. Luego `python benchmark_v2.py --phase evaluation` para continuar.

**P: ¿Dónde veo los errores?**

R: En SQLite:
```sql
SELECT model_name, error FROM responses WHERE error IS NOT NULL;
SELECT response_id, error FROM evaluations WHERE error IS NOT NULL;
```

---

## 📞 Soporte

Si algo no funciona:

1. Verifica el progreso: `python benchmark_v2.py --progress`
2. Inspecciona la base de datos: `sqlite3 results/benchmark.db`
3. Revisa los logs en terminal
4. Consulta esta guía de troubleshooting

---

**¡Listo!** Ahora tienes un sistema de benchmark profesional, rápido, visual y recuperable. 🎉
