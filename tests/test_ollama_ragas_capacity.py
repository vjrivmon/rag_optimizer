#!/usr/bin/env python3
"""
Test para determinar cuántas métricas RAGAs puede evaluar Ollama sin timeout.
Prueba progresivamente desde 6 métricas hasta 3 (conocido que funciona).
"""

import warnings
warnings.filterwarnings('ignore')

import json
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_correctness,
    answer_similarity
)
from datasets import Dataset
from ragas import evaluate
from ragas.llms import LangchainLLMWrapper
from langchain_ollama import ChatOllama
from langchain.embeddings import HuggingFaceEmbeddings
import time

# Cargar datos de benchmark anterior para usar como test
print("📂 Cargando datos del benchmark anterior...")
with open('results/benchmark_20251008_093326.json', 'r') as f:
    benchmark_data = json.load(f)

# Usar la primera pregunta como test case
test_question = benchmark_data['results'][0]
question = test_question['question']
contexts = test_question['contexts']
expected = test_question['expected_answer']
# Usar respuesta de gemma2:27b (modelo sin thinking tags)
answer = test_question['models']['gemma2:27b']['response']

print(f"\n📝 Pregunta de test: {question}")
print(f"✅ Respuesta de gemma2:27b: {answer[:100]}...")
print(f"📚 Contextos: {len(contexts)} documentos")

# Configurar Ollama LLM
print(f"\n⚙️  Configurando Ollama (gemma2:27b)...")
ollama_llm = ChatOllama(
    model="gemma2:27b",
    base_url="https://ollama.gti-ia.upv.es:443",
    temperature=0.1,
    client_kwargs={"verify": False, "timeout": 600}  # 10 minutos timeout
)
evaluator_llm = LangchainLLMWrapper(ollama_llm)

# Configurar embeddings locales (mismo modelo que el proyecto usa)
print(f"⚙️  Configurando embeddings locales (paraphrase-multilingual-mpnet-base-v2)...")
local_embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    model_kwargs={'device': 'cpu'},
    encode_kwargs={'normalize_embeddings': True}
)

# Definir conjuntos de métricas para probar
metric_sets = {
    6: {
        'name': '6 métricas (todas)',
        'metrics': [faithfulness, answer_relevancy, context_precision,
                   context_recall, answer_correctness, answer_similarity],
        'names': ['faithfulness', 'answer_relevancy', 'context_precision',
                 'context_recall', 'answer_correctness', 'answer_similarity']
    },
    5: {
        'name': '5 métricas (sin answer_correctness)',
        'metrics': [faithfulness, answer_relevancy, context_precision,
                   context_recall, answer_similarity],
        'names': ['faithfulness', 'answer_relevancy', 'context_precision',
                 'context_recall', 'answer_similarity']
    },
    4: {
        'name': '4 métricas (sin answer_correctness, faithfulness)',
        'metrics': [answer_relevancy, context_precision,
                   context_recall, answer_similarity],
        'names': ['answer_relevancy', 'context_precision',
                 'context_recall', 'answer_similarity']
    },
    3: {
        'name': '3 métricas (answer_relevancy, context_recall, answer_similarity)',
        'metrics': [answer_relevancy, context_recall, answer_similarity],
        'names': ['answer_relevancy', 'context_recall', 'answer_similarity']
    }
}

# Crear dataset RAGAs
data = {
    'question': [question],
    'answer': [answer],
    'contexts': [contexts],
    'ground_truth': [expected]
}
dataset = Dataset.from_dict(data)

# Probar cada conjunto de métricas
results = {}

print(f"\n{'='*80}")
print(f"🧪 INICIANDO PRUEBAS DE CAPACIDAD OLLAMA")
print(f"{'='*80}\n")

for num_metrics in [6, 5, 4, 3]:
    metric_set = metric_sets[num_metrics]

    print(f"\n{'─'*80}")
    print(f"📊 Probando {metric_set['name']}")
    print(f"   Métricas: {', '.join(metric_set['names'])}")
    print(f"{'─'*80}")

    start_time = time.time()
    success = False
    error_msg = None
    metrics_result = {}

    try:
        print(f"⏳ Evaluando con timeout de 600s (10 minutos)...")

        result = evaluate(
            dataset,
            metrics=metric_set['metrics'],
            llm=evaluator_llm,
            embeddings=local_embeddings  # Usar embeddings locales en lugar de OpenAI
        )

        elapsed = time.time() - start_time

        # Extraer scores
        df = result.to_pandas()
        for col in df.columns:
            if col not in ['question', 'answer', 'contexts', 'ground_truth']:
                value = df[col].iloc[0]
                try:
                    metrics_result[col] = float(value) if value is not None else 0.0
                except (ValueError, TypeError):
                    continue

        success = True

        print(f"✅ ÉXITO en {elapsed:.1f}s")
        print(f"   Métricas obtenidas:")
        for metric_name, score in metrics_result.items():
            print(f"      • {metric_name}: {score:.4f}")

        results[num_metrics] = {
            'success': True,
            'elapsed': elapsed,
            'metrics': metrics_result,
            'error': None
        }

    except TimeoutError as e:
        elapsed = time.time() - start_time
        error_msg = f"Timeout después de {elapsed:.1f}s"
        print(f"❌ TIMEOUT después de {elapsed:.1f}s")

        results[num_metrics] = {
            'success': False,
            'elapsed': elapsed,
            'metrics': {},
            'error': error_msg
        }

    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = str(e)
        print(f"❌ ERROR: {error_msg}")
        print(f"   Tiempo transcurrido: {elapsed:.1f}s")

        results[num_metrics] = {
            'success': False,
            'elapsed': elapsed,
            'metrics': {},
            'error': error_msg
        }

    # Si falla, continuar con menos métricas
    if not success:
        print(f"\n⚠️  Falló con {num_metrics} métricas, probando con {num_metrics-1}...")
        continue
    else:
        # Si tiene éxito, podemos parar aquí si queremos
        # Pero vamos a probar todas para tener datos completos
        print(f"\n✅ Éxito con {num_metrics} métricas, continuando para recopilar datos...")

# Resumen final
print(f"\n\n{'='*80}")
print(f"📈 RESUMEN DE RESULTADOS")
print(f"{'='*80}\n")

print(f"{'Métricas':<12} {'Estado':<12} {'Tiempo (s)':<15} {'Observaciones'}")
print(f"{'─'*80}")

for num_metrics in [6, 5, 4, 3]:
    result = results[num_metrics]
    status = "✅ ÉXITO" if result['success'] else "❌ FALLO"
    elapsed = f"{result['elapsed']:.1f}s"

    if result['success']:
        num_obtained = len(result['metrics'])
        obs = f"{num_obtained} métricas obtenidas"
    else:
        obs = result['error'][:40] + "..." if len(result['error']) > 40 else result['error']

    print(f"{num_metrics:<12} {status:<12} {elapsed:<15} {obs}")

print(f"{'─'*80}")

# Determinar capacidad máxima
max_capacity = max([n for n, r in results.items() if r['success']], default=0)

print(f"\n{'='*80}")
print(f"🎯 CONCLUSIÓN")
print(f"{'='*80}")

if max_capacity == 0:
    print(f"\n❌ Ollama NO pudo evaluar ninguna métrica RAGAs")
    print(f"   Problema: Todas las configuraciones fallaron")
    print(f"   Recomendación: Revisar logs de error arriba")
else:
    print(f"\n✅ Capacidad máxima de Ollama (gemma2:27b): {max_capacity} métricas RAGAs simultáneas")
    print(f"\n📝 Métricas soportadas: {', '.join(metric_sets[max_capacity]['names'])}")

if max_capacity > 0:
    if max_capacity < 6:
        print(f"\n⚠️  Ollama NO puede evaluar las 6 métricas simultáneamente")
        print(f"   Recomendación: Usar dual backend (Ollama {max_capacity} + OpenAI {6-max_capacity})")
    else:
        print(f"\n🎉 Ollama puede evaluar las 6 métricas completas!")
        print(f"   Recomendación: Cambiar de dual backend a Ollama-only (gratis)")

# Guardar resultados
output_file = 'results/ollama_capacity_test.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'model': 'gemma2:27b',
        'base_url': 'https://ollama.gti-ia.upv.es:443',
        'test_question': question,
        'max_capacity': max_capacity,
        'results': results
    }, f, indent=2, ensure_ascii=False)

print(f"\n💾 Resultados guardados en: {output_file}")
print(f"\n{'='*80}\n")
