#!/usr/bin/env python3
"""
🧪 Test Específico para P25: ¿Qué significa Para-Mira-Ayuda?

Ejecuta solo P25 para verificar que el fix de chunking funciona.
"""

import json
import asyncio
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

from src.core.model_wrapper import LLMWrapper
from src.core.enhanced_rag_engine_new import EnhancedRAGEngineNew
from src.ensemble.ensemble_engine import EnsembleRAGEngine

# === CONFIGURACIÓN ===
VECTOR_STORE_PATH = "data/vectorstore/chroma_db"
DATASET_PATH = "data/evaluation_dataset.json"
OUTPUT_DIR = Path("results")
DEFAULT_API_ENDPOINT = "https://ollama.gti-ia.upv.es:443/api/generate"

# Solo P25
TEST_QUESTION_ID = 25

MODELS_CONFIG = [
    {'name': 'gemma2:27b'},
    {'name': 'llama3.3:70b'},
    {'name': 'qwen3:32b'},
    {'name': 'deepseek-r1:latest'}
]

STRATEGIES = ['voting', 'weighted', 'routing', 'consensus']


def load_p25_question() -> Dict:
    """Carga solo la pregunta P25"""
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        all_questions = json.load(f)
    
    p25 = next((q for q in all_questions if q['id'] == TEST_QUESTION_ID), None)
    if not p25:
        raise ValueError(f"No se encontró la pregunta con id={TEST_QUESTION_ID}")
    
    return p25


def save_results(results: Dict, output_path: str):
    """Guarda resultados en JSON"""
    def convert_to_serializable(obj):
        if hasattr(obj, '__dict__'):
            return {k: convert_to_serializable(v) for k, v in obj.__dict__.items()}
        elif isinstance(obj, dict):
            return {k: convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_serializable(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            return str(obj)
    
    serializable_results = convert_to_serializable(results)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Resultados guardados en: {output_path}")


async def evaluate_with_ragas(
    question: str,
    answer: str,
    contexts: List[str],
    expected_answer: str,
    client: AsyncOpenAI
) -> Dict[str, float]:
    """Evalúa con RAGAs"""
    
    system_prompt = """Eres un evaluador experto y CRÍTICO de sistemas RAG.
Evalúa la respuesta del modelo comparándola con la RESPUESTA ESPERADA (ground truth).

Evalúa las siguientes métricas (0.0 a 1.0):

1. faithfulness: ¿La respuesta está fundamentada en los contextos proporcionados?
2. answer_relevancy: ¿La respuesta es relevante y responde directamente a la pregunta?
3. context_precision: ¿Los contextos proporcionados son precisos y útiles para responder?
4. context_recall: ¿Los contextos cubren toda la información necesaria de la respuesta esperada?
5. answer_correctness: ¿La respuesta es factualmente correcta comparada con la esperada?
6. answer_similarity: ¿Qué tan similar es la respuesta a la respuesta esperada en contenido y estructura?

Responde SOLO con JSON:
{"faithfulness": 0.X, "answer_relevancy": 0.X, "context_precision": 0.X, "context_recall": 0.X, "answer_correctness": 0.X, "answer_similarity": 0.X}"""

    user_prompt = f"""PREGUNTA: {question}

CONTEXTOS PROPORCIONADOS:
{chr(10).join([f"{i+1}. {ctx}" for i, ctx in enumerate(contexts)])}

RESPUESTA ESPERADA (ground truth):
{expected_answer}

RESPUESTA DEL MODELO:
{answer}

Evalúa la respuesta del modelo comparando con la RESPUESTA ESPERADA. Sé crítico y objetivo."""
    
    try:
        completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        metrics = json.loads(completion.choices[0].message.content)
        
        weights = {
            'faithfulness': 0.25,
            'answer_relevancy': 0.20,
            'context_precision': 0.15,
            'context_recall': 0.20,
            'answer_correctness': 0.10,
            'answer_similarity': 0.10
        }
        
        combined = sum(metrics.get(k, 0) * v for k, v in weights.items())
        metrics['combined_score'] = combined
        
        return metrics
        
    except Exception as e:
        print(f"   ⚠️ Error en evaluación: {str(e)[:100]}")
        return {
            'faithfulness': 0.0,
            'answer_relevancy': 0.0,
            'context_precision': 0.0,
            'context_recall': 0.0,
            'answer_correctness': 0.0,
            'answer_similarity': 0.0,
            'combined_score': 0.0
        }


async def test_p25():
    """Test específico para P25"""
    
    print("="*80)
    print("🧪 TEST P25: ¿Qué significa Para-Mira-Ayuda?")
    print("="*80)
    
    # Cargar P25
    question_data = load_p25_question()
    question_id = question_data['id']
    question = question_data['question']
    expected_answer = question_data['expected_answer']
    
    print(f"\n📝 Pregunta: {question}")
    print(f"📌 Respuesta esperada: {expected_answer}")
    
    # Inicializar modelos
    print(f"\n🔧 Inicializando modelos...")
    rag_engines = {}
    
    for config in MODELS_CONFIG:
        model_name = config['name']
        print(f"   Cargando {model_name}...")
        
        try:
            model = LLMWrapper(
                model_name=model_name,
                api_endpoint=DEFAULT_API_ENDPOINT
            )
            
            rag_engine = EnhancedRAGEngineNew(
                vector_store_path=VECTOR_STORE_PATH,
                model=model
            )
            rag_engines[model_name] = rag_engine
            print(f"      ✅ {model_name} listo")
            
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")
            continue
    
    # Inicializar Ensemble
    print(f"\n🎲 Inicializando Ensemble Engine...")
    ensemble_engine = EnsembleRAGEngine(
        rag_engines=rag_engines,
        enabled_strategies=STRATEGIES
    )
    
    # Inicializar OpenAI
    print(f"\n🔑 Inicializando cliente OpenAI...")
    openai_client = AsyncOpenAI()
    
    # GENERACIÓN
    print(f"\n{'='*80}")
    print(f"📝 FASE 1: Generación de Respuestas")
    print(f"{'='*80}\n")
    
    start_time = time.time()
    
    result = ensemble_engine.process_question_complete(
        question=question,
        question_id=question_id
    )
    
    gen_time = time.time() - start_time
    
    print(f"\n✅ Generación completada en {gen_time:.1f}s")
    
    # EVALUACIÓN
    print(f"\n{'='*80}")
    print(f"📈 FASE 2: Evaluación RAGAs")
    print(f"{'='*80}\n")
    
    eval_start = time.time()
    
    # Evaluar individuales
    print(f"🤖 Evaluando respuestas individuales...")
    for individual in result['individual']:
        metrics = await evaluate_with_ragas(
            question=question,
            answer=individual['answer'],
            contexts=individual['contexts'],
            expected_answer=expected_answer,
            client=openai_client
        )
        individual['metrics'] = metrics
        print(f"   ✅ {individual['model_name']}: {metrics['combined_score']:.3f}")
    
    # Evaluar ensemble
    print(f"\n🎲 Evaluando estrategias ensemble...")
    for strategy_name, ensemble_result in result['ensemble'].items():
        answer = ensemble_result['answer']
        contexts = ensemble_result.get('contexts', [])
        
        if not contexts and result['individual']:
            contexts = result['individual'][0]['contexts']
        
        metrics = await evaluate_with_ragas(
            question=question,
            answer=answer,
            contexts=contexts,
            expected_answer=expected_answer,
            client=openai_client
        )
        
        ensemble_result['metrics'] = metrics
        print(f"   ✅ {strategy_name}: {metrics['combined_score']:.3f}")
    
    eval_time = time.time() - eval_start
    total_time = time.time() - start_time
    
    # GUARDAR RESULTADOS
    output_file = OUTPUT_DIR / f"p25_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    test_result = {
        'timestamp': datetime.now().isoformat(),
        'test_type': 'p25_only',
        'question_id': question_id,
        'question': question,
        'expected_answer': expected_answer,
        'result': result,
        'times': {
            'generation': gen_time,
            'evaluation': eval_time,
            'total': total_time
        }
    }
    
    save_results(test_result, output_file)
    
    # RESUMEN
    print(f"\n{'='*80}")
    print(f"📊 RESUMEN DE RESULTADOS")
    print(f"{'='*80}\n")
    
    # Mejor individual
    best_ind = max(result['individual'], key=lambda x: x['metrics']['combined_score'])
    print(f"🥇 Mejor individual:")
    print(f"   Modelo: {best_ind['model_name']}")
    print(f"   Score: {best_ind['metrics']['combined_score']:.3f}")
    print(f"   Respuesta: {best_ind['answer'][:200]}...")
    
    # Mejor ensemble
    best_ens_name, best_ens = max(
        result['ensemble'].items(),
        key=lambda item: item[1]['metrics']['combined_score']
    )
    print(f"\n🎯 Mejor ensemble:")
    print(f"   Estrategia: {best_ens_name}")
    print(f"   Score: {best_ens['metrics']['combined_score']:.3f}")
    print(f"   Respuesta: {best_ens['answer'][:200]}...")
    
    # Mejora
    improvement = best_ens['metrics']['combined_score'] - best_ind['metrics']['combined_score']
    if improvement > 0:
        print(f"\n✅ Ensemble mejora: +{improvement:.3f}")
    elif improvement < 0:
        print(f"\n⚠️  Ensemble no mejora: {improvement:.3f}")
    else:
        print(f"\n➖ Ensemble igual a individual")
    
    # Comparación con objetivo
    print(f"\n🎯 Objetivo: Score >= 0.80")
    if best_ens['metrics']['combined_score'] >= 0.80:
        print(f"   ✅ ¡OBJETIVO ALCANZADO! ({best_ens['metrics']['combined_score']:.3f})")
    elif best_ens['metrics']['combined_score'] >= 0.70:
        print(f"   🟡 Cerca del objetivo ({best_ens['metrics']['combined_score']:.3f})")
    else:
        print(f"   🔴 Por debajo del objetivo ({best_ens['metrics']['combined_score']:.3f})")
    
    print(f"\n{'='*80}")
    print(f"⏱️  Tiempo total: {total_time:.1f}s")
    print(f"📁 Resultados: {output_file}")
    print(f"{'='*80}\n")
    
    return test_result


if __name__ == "__main__":
    print("\n🧪 Iniciando test específico de P25...\n")
    result = asyncio.run(test_p25())
    print("\n✅ Test completado")

