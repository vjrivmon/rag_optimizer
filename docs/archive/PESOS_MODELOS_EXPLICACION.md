# 🎯 Cómo Funcionan los Pesos de los Modelos

## 📊 Pesos Actuales (Benchmark 2025-10-11)

**Fuente**: `results/ensemble_20251011_191914.json`

| Modelo | Score AVG | Correctas | Peso Normalizado |
|--------|-----------|-----------|------------------|
| **Gemma 2 27B** | 0.9146 | 22/26 | 0.9146 |
| **Llama 3.3 70B** | 0.8879 | 20/26 | 0.8879 |
| **Qwen 3 32B** | 0.8498 | 17/26 | 0.8498 |
| **DeepSeek R1** | 0.6325 | 10/26 | 0.6325 |

---

## 🔍 ¿Dónde se Usan los Pesos?

### 1. **Estrategia Weighted Voting**

**Archivo**: `src/ensemble/strategies/weighted.py`

```python
DEFAULT_WEIGHTS = {
    'gemma2:27b': 0.9146,          # 22/26 correctas
    'llama3.3:70b': 0.8879,        # 20/26 correctas
    'qwen3:32b': 0.8498,           # 17/26 correctas
    'deepseek-r1:latest': 0.6325   # 10/26 correctas
}
```

**Cómo funciona**:
1. Cada modelo genera su respuesta y obtiene un score RAGAs
2. Se multiplica el score de cada modelo por su peso:
   - `score_ponderado = score_ragas × peso_modelo`
3. Se selecciona la respuesta del modelo con **mayor score ponderado**

**Ejemplo**:
```python
# Scores RAGAs para P11:
gemma_score = 0.85
llama_score = 0.80

# Scores ponderados:
gemma_weighted = 0.85 × 0.9146 = 0.777
llama_weighted = 0.80 × 0.8879 = 0.710

# Resultado: Se elige respuesta de Gemma (0.777 > 0.710)
```

---

### 2. **Perfiles de Modelo (Frontend)**

**Archivo**: `interface/chatbot/backend/model_profiles.py`

Los scores se muestran al usuario en:
- Card de selección de modelo
- Modal de información (botón `?`)
- Estadísticas en el dashboard

```python
"gemma2:27b": {
    "score": 0.915,      # ← Score del benchmark
    "correctas": "22/26" # ← Preguntas correctas
}
```

---

### 3. **Estrategia Routing**

**Archivo**: `src/ensemble/strategies/routing.py`

Usa pesos implícitos para decidir qué modelo usar según el tipo de pregunta:

| Tipo de Pregunta | Modelo Preferido | Razón |
|------------------|------------------|-------|
| Filosófica | **Llama 3.3 70B** | Mejor razonamiento profundo |
| Factual | **Gemma 2 27B** | Más preciso y rápido |
| Procedural | **Gemma 2 27B** | Mejor seguimiento de pasos |
| Normativa | **Llama 3.3 70B** | Mejor comprensión de reglas |

---

## ⚙️ ¿Cómo se Calculan los Pesos?

Los pesos provienen del **benchmark ensemble** que ejecutas con:

```bash
python benchmark_ensemble.py
```

### Proceso:

1. **Generación** (Fase 1):
   - Cada modelo responde las 26 preguntas del dataset
   - Se guardan respuestas + contextos recuperados

2. **Evaluación** (Fase 2):
   - Cada respuesta se evalúa con RAGAs (OpenAI gpt-4o-mini)
   - Se calculan 6 métricas:
     - faithfulness (25%)
     - answer_relevancy (20%)
     - context_precision (15%)
     - context_recall (20%)
     - answer_correctness (10%)
     - answer_similarity (10%)
   - Se combinan en un `combined_score` (0-1)

3. **Agregación**:
   - Se promedian los `combined_score` de las 26 preguntas
   - El promedio es el **peso final** del modelo

---

## 🚀 Cómo Actualizar los Pesos

### Opción 1: Manualmente (Actual)

1. Ejecuta el benchmark:
   ```bash
   python benchmark_ensemble.py
   ```

2. Abre el JSON generado:
   ```bash
   cat results/ensemble_YYYYMMDD_HHMMSS.json
   ```

3. Busca la sección `summary.individual_models`:
   ```json
   "individual_models": {
     "gemma2:27b": {
       "avg_score": 0.9146,
       ...
     }
   }
   ```

4. Actualiza los pesos en `src/ensemble/strategies/weighted.py`:
   ```python
   DEFAULT_WEIGHTS = {
       'gemma2:27b': 0.9146,  # ← Copiar avg_score
       ...
   }
   ```

5. Actualiza los perfiles en `interface/chatbot/backend/model_profiles.py`:
   ```python
   "gemma2:27b": {
       "score": 0.915,  # ← Redondear avg_score
       ...
   }
   ```

### Opción 2: Automática (Futuro - Recomendado)

Crear un script `update_weights_from_benchmark.py`:

```python
#!/usr/bin/env python3
"""Actualiza pesos automáticamente desde el último benchmark"""

import json
from pathlib import Path
import re

def get_latest_benchmark():
    """Encuentra el último benchmark ensemble"""
    results_dir = Path("results")
    benchmarks = sorted(results_dir.glob("ensemble_*.json"))
    return benchmarks[-1] if benchmarks else None

def extract_weights(benchmark_path):
    """Extrae pesos del benchmark"""
    with open(benchmark_path) as f:
        data = json.load(f)
    
    weights = {}
    for model, stats in data['summary']['individual_models'].items():
        weights[model] = stats['avg_score']
    
    return weights

def update_weighted_strategy(weights):
    """Actualiza src/ensemble/strategies/weighted.py"""
    file_path = Path("src/ensemble/strategies/weighted.py")
    
    # Leer archivo
    content = file_path.read_text()
    
    # Generar nuevo bloque de pesos
    weights_str = "DEFAULT_WEIGHTS = {\n"
    for model, weight in sorted(weights.items(), key=lambda x: -x[1]):
        weights_str += f"        '{model}': {weight:.4f},\n"
    weights_str += "    }"
    
    # Reemplazar
    new_content = re.sub(
        r'DEFAULT_WEIGHTS = \{[^}]+\}',
        weights_str,
        content,
        flags=re.DOTALL
    )
    
    file_path.write_text(new_content)
    print(f"✅ Pesos actualizados en {file_path}")

if __name__ == "__main__":
    benchmark = get_latest_benchmark()
    if not benchmark:
        print("❌ No se encontró ningún benchmark")
        exit(1)
    
    print(f"📊 Usando benchmark: {benchmark.name}")
    weights = extract_weights(benchmark)
    update_weighted_strategy(weights)
    print("\n✅ Pesos actualizados correctamente")
```

---

## 🔧 Problema Resuelto: Timeout de Conexión

### Antes:
```python
timeout=5  # ❌ MUY CORTO, fallaba con HTTPS directo
```

### Ahora:
```python
timeout=15  # ✅ Suficiente para HTTPS directo a UPV
warnings.filterwarnings('ignore', category=InsecureRequestWarning)  # Sin spam
```

**¿Por qué fallaba?**
- El servidor UPV via HTTPS (`https://ollama.gti-ia.upv.es:443`) puede tardar 5-10s en responder
- El timeout de 5s cortaba la conexión antes de tiempo
- NO es un problema de SSH (ya que estás en Linux nativo)

---

## 📝 Resumen

### ✅ Cambios Aplicados:

1. **Pesos actualizados** en `weighted.py`:
   - Gemma: 0.9146 (antes: 0.40)
   - Llama: 0.8879 (antes: 0.25)
   - Qwen: 0.8498 (antes: 0.30)
   - DeepSeek: 0.6325 (antes: 0.05)

2. **Timeout aumentado** en `app.py`:
   - De 5s → 15s
   - Warnings HTTPS suprimidos

3. **Estados simplificados**:
   - Antes: "connected" / "warning" / "offline"
   - Ahora: "connected" / "offline"
   - Frontend muestra: "ONLINE" / "OFFLINE"

### 🎯 Resultado:

- **Chatbot usa scores reales** del último benchmark
- **Estrategia weighted** prioriza correctamente (Gemma > Llama > Qwen > DeepSeek)
- **Conexión más estable** con timeout de 15s
- **UI más clara** con ONLINE/OFFLINE simple

---

## 🚀 Próximos Pasos

1. **Probar el chatbot**:
   ```bash
   ./run_chatbot.sh
   ```

2. **Verificar que conecta**:
   - Debe mostrar "✅ Servidor UPV ONLINE"
   - Badge en frontend debe decir "ONLINE" (verde pulsante)

3. **(Opcional) Automatizar** actualización de pesos:
   - Crear script `update_weights_from_benchmark.py`
   - Ejecutar después de cada benchmark nuevo

---

**Última actualización**: 2025-10-11 (Benchmark ensemble_20251011_191914)

