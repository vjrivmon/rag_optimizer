#!/usr/bin/env python3
"""
🔄 Script de Recuperación de Benchmark Ensemble

Recupera los datos de generación ya completados y ejecuta solo la evaluación RAGAs.
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import os
from openai import AsyncOpenAI

# === CONFIGURACIÓN ===
TEMP_FILE = "results/ensemble_temp_20251011_175506.json"
OUTPUT_DIR = Path("results")
OPENAI_KEY = os.environ["OPENAI_API_KEY"]

# === CARGAR DATASET PARA EXPECTED ANSWERS ===
def load_dataset() -> List[Dict]:
    """Carga el dataset de evaluación"""
    with open("data/evaluation_dataset.json", 'r', encoding='utf-8') as f:
        return json.load(f)


# === EVALUACIÓN RAGAs (IDÉNTICA A benchmark_ensemble.py) ===
async def evaluate_with_ragas(
    question: str,
    answer: str,
    contexts: List[str],
    expected_answer: str,
    client: AsyncOpenAI
) -> Dict[str, float]:
    """
    Evalúa una respuesta con métricas RAGAs usando OpenAI.
    
    EXACTAMENTE LAS MISMAS MÉTRICAS que benchmark_v2.py:
    - faithfulness (25%)
    - answer_relevancy (20%)
    - context_precision (15%)
    - context_recall (20%)
    - answer_correctness (10%)
    - answer_similarity (10%)
    """
    
    system_prompt = """Eres un evaluador experto y CRÍTICO de sistemas RAG.
Evalúa la respuesta del modelo comparándola con la RESPUESTA ESPERADA (ground truth).

Evalúa las siguientes métricas (0.0 a 1.0):

1. faithfulness: ¿La respuesta está fundamentada en los contextos proporcionados? (0.0 = no fundamentada, 1.0 = completamente fiel)
2. answer_relevancy: ¿La respuesta es relevante y responde directamente a la pregunta? (0.0 = irrelevante, 1.0 = perfectamente relevante)
3. context_precision: ¿Los contextos proporcionados son precisos y útiles para responder? (0.0 = contextos inútiles, 1.0 = contextos perfectos)
4. context_recall: ¿Los contextos cubren toda la información necesaria de la respuesta esperada? (0.0 = no cubren nada, 1.0 = cubren todo)
5. answer_correctness: ¿La respuesta es factualmente correcta comparada con la esperada? (0.0 = incorrecta, 1.0 = perfectamente correcta)
6. answer_similarity: ¿Qué tan similar es la respuesta a la respuesta esperada en contenido y estructura? (0.0 = totalmente diferente, 1.0 = idéntica)

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
            model="gpt-4o-mini",  # Mismo modelo que benchmark_v2.py
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
        
        combined = sum(
            metrics.get(k, 0) * v
            for k, v in weights.items()
        )
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


# === FUNCIÓN PRINCIPAL ===
async def recover_and_evaluate():
    """Recupera resultados y ejecuta solo la evaluación RAGAs"""
    
    print("="*80)
    print("🔄 RECUPERACIÓN Y EVALUACIÓN DE BENCHMARK ENSEMBLE")
    print("="*80)
    
    # 1. Cargar datos temporales
    print(f"\n📂 Cargando datos de: {TEMP_FILE}")
    try:
        with open(TEMP_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            # El JSON está incompleto, arreglarlo
            if not content.strip().endswith('}'):
                # Buscar el último objeto completo
                content = content.rsplit('},', 1)[0] + '}]}'
            results = json.loads(content)
        print(f"   ✅ {len(results['results'])} preguntas cargadas")
    except Exception as e:
        print(f"   ❌ Error cargando archivo: {e}")
        return
    
    # 2. Cargar dataset para expected answers
    print("\n📊 Cargando dataset...")
    dataset = load_dataset()
    expected_answers = {q['question_id']: q['expected_answer'] for q in dataset}
    print(f"   ✅ {len(expected_answers)} respuestas esperadas cargadas")
    
    # 3. Inicializar cliente OpenAI
    print("\n🔑 Inicializando cliente OpenAI...")
    client = AsyncOpenAI(api_key=OPENAI_KEY)
    
    # 4. Evaluar todas las respuestas
    print("\n📈 FASE 2/2: Evaluación RAGAs")
    print("="*80)
    
    total_responses = sum(
        len(q['individual']) + len(q['ensemble'])
        for q in results['results']
    )
    
    print(f"\n   Total de respuestas a evaluar: {total_responses}")
    print(f"   Estrategias ensemble: {len(results['strategies'])}")
    
    evaluated_count = 0
    
    for question_result in results['results']:
        question_id = question_result['question_id']
        question = question_result['question']
        expected = expected_answers.get(question_id, "")
        
        print(f"\n   [{question_id}/26] Evaluando: {question[:50]}...")
        
        # Evaluar respuestas individuales
        for individual in question_result['individual']:
            answer = individual['answer']
            contexts = individual['contexts']
            
            metrics = await evaluate_with_ragas(
                question=question,
                answer=answer,
                contexts=contexts,
                expected_answer=expected,
                client=client
            )
            
            individual['metrics'] = metrics
            evaluated_count += 1
            print(f"      ✅ {individual['model_name']}: {metrics['combined_score']:.3f}")
        
        # Evaluar respuestas ensemble
        for ensemble in question_result['ensemble']:
            answer = ensemble['answer']
            contexts = ensemble.get('contexts', [])
            
            # Si no hay contextos en ensemble, usar los del primer modelo
            if not contexts and question_result['individual']:
                contexts = question_result['individual'][0]['contexts']
            
            metrics = await evaluate_with_ragas(
                question=question,
                answer=answer,
                contexts=contexts,
                expected_answer=expected,
                client=client
            )
            
            ensemble['metrics'] = metrics
            evaluated_count += 1
            print(f"      ✅ {ensemble['strategy']}: {metrics['combined_score']:.3f}")
    
    print(f"\n✅ Evaluación completada: {evaluated_count} respuestas evaluadas")
    
    # 5. Guardar resultados finales
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_output = OUTPUT_DIR / f"benchmark_ensemble_{timestamp}.json"
    
    print(f"\n💾 Guardando resultados finales en: {final_output}")
    with open(final_output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*80)
    print("✅ BENCHMARK ENSEMBLE COMPLETADO")
    print("="*80)
    print(f"\n📊 Archivo final: {final_output}")
    
    return final_output


if __name__ == "__main__":
    asyncio.run(recover_and_evaluate())

