#!/usr/bin/env python3
"""
🧪 Test Rápido de Benchmark Ensemble

Ejecuta el benchmark ensemble solo con las preguntas más conflictivas
para validar que el sistema funciona correctamente antes del benchmark completo.

Preguntas de prueba:
- P11 (COLES): Fallo crítico histórico
- P20 (RESIS ubicación): Fallo crítico histórico  
- P25 (Para-Mira-Ayuda): Fallo filosófico en todos los modelos
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
VECTOR_STORE_PATH = "data/vectorstore/chroma_db"  # Vector store principal con datos
DATASET_PATH = "data/evaluation_dataset.json"
OUTPUT_DIR = Path("results")

# Endpoint por defecto (todos usan el mismo servidor)
DEFAULT_API_ENDPOINT = "https://ollama.gti-ia.upv.es:443/api/generate"

# Solo preguntas conflictivas
TEST_QUESTION_IDS = [11, 20, 25]  # COLES, RESIS ubicación, Para-Mira-Ayuda

# Modelos a probar
MODELS_CONFIG = [
    {'name': 'gemma2:27b'},
    {'name': 'llama3.3:70b'},
    {'name': 'qwen3:32b'},
    {'name': 'deepseek-r1:latest'}
]

# Estrategias ensemble
STRATEGIES = ['voting', 'weighted', 'routing', 'consensus']


# === FUNCIONES AUXILIARES ===
def load_test_dataset() -> List[Dict]:
    """Carga solo las preguntas de prueba"""
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        all_questions = json.load(f)
    
    # Filtrar solo las preguntas de test (el dataset usa 'id', no 'question_id')
    test_questions = [q for q in all_questions if q['id'] in TEST_QUESTION_IDS]
    return test_questions


def save_results(results: Dict, output_path: str):
    """Guarda resultados en JSON convirtiendo objetos no serializables"""
    def convert_to_serializable(obj):
        """Convierte objetos no serializables a diccionarios"""
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
    
    # Convertir todo el resultado
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
async def run_quick_test():
    """Ejecuta test rápido con preguntas conflictivas"""
    
    print("="*80)
    print("🧪 TEST RÁPIDO - BENCHMARK ENSEMBLE")
    print("="*80)
    print(f"\n📊 Configuración:")
    print(f"   Preguntas de prueba: {TEST_QUESTION_IDS}")
    print(f"   Modelos: {len(MODELS_CONFIG)}")
    print(f"   Estrategias: {len(STRATEGIES)}")
    
    # Cargar dataset de prueba
    dataset = load_test_dataset()
    print(f"   Total preguntas: {len(dataset)}")
    
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
            print(f"      ❌ Error cargando {model_name}: {str(e)}")
            continue
    
    if not rag_engines:
        print("\n❌ No se pudieron cargar modelos. Abortando.")
        return None
    
    # Inicializar Ensemble Engine
    print(f"\n🎲 Inicializando Ensemble Engine...")
    ensemble_engine = EnsembleRAGEngine(
        rag_engines=rag_engines,
        enabled_strategies=STRATEGIES
    )
    
    # Inicializar cliente OpenAI (usa OPENAI_API_KEY desde .env automáticamente)
    print(f"\n🔑 Inicializando cliente OpenAI para evaluación...")
    openai_client = AsyncOpenAI()
    
    # Preparar estructura de resultados
    timestamp = datetime.now().isoformat()
    results = {
        'timestamp': timestamp,
        'benchmark_type': 'ensemble_quick_test',
        'test_questions': TEST_QUESTION_IDS,
        'models': [m['name'] for m in MODELS_CONFIG],
        'strategies': STRATEGIES,
        'total_questions': len(dataset),
        'results': []
    }
    
    # Archivo temporal
    temp_output = OUTPUT_DIR / f"ensemble_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # === FASE 1: GENERACIÓN ===
    print("\n" + "="*80)
    print("📝 FASE 1/2: Generación de Respuestas")
    print("="*80)
    
    start_time = time.time()
    
    for idx, question_data in enumerate(dataset, 1):
        question_id = question_data['id']  # El dataset usa 'id'
        question = question_data['question']
        
        print(f"\n[{idx}/{len(dataset)}] P{question_id}: {question}")
        print("="*80)
        
        q_start = time.time()
        
        # Generar respuestas individuales y ensemble
        question_result = ensemble_engine.process_question_complete(
            question=question,
            question_id=question_id
        )
        
        q_time = time.time() - q_start
        
        results['results'].append(question_result)
        
        print(f"\n✅ Pregunta P{question_id} completada en {q_time:.1f}s")
        print(f"✅ P{question_id} completada")
        
        # Guardar progreso
        save_results(results, temp_output)
    
    gen_time = time.time() - start_time
    
    print("\n" + "="*80)
    print(f"✅ GENERACIÓN COMPLETADA en {gen_time/60:.1f} minutos")
    print("="*80)
    
    # === FASE 2: EVALUACIÓN ===
    print("\n" + "="*80)
    print("📈 FASE 2/2: Evaluación RAGAs")
    print("="*80)
    
    total_responses = sum(
        len(q['individual']) + len(q['ensemble'])
        for q in results['results']
    )
    
    print(f"\n   Total de respuestas a evaluar: {total_responses}")
    
    eval_start = time.time()
    evaluated_count = 0
    
    for question_result in results['results']:
        question_id = question_result['question_id']
        question = question_result['question']
        
        # Buscar expected_answer (el dataset usa 'id')
        expected = next(
            (q['expected_answer'] for q in dataset if q['id'] == question_id),
            ""
        )
        
        print(f"\n   P{question_id}: Evaluando {len(question_result['individual'])} individuales + {len(question_result['ensemble'])} ensemble...")
        
        # Evaluar respuestas individuales
        for individual in question_result['individual']:
            answer = individual['answer']
            contexts = individual['contexts']
            
            metrics = await evaluate_with_ragas(
                question=question,
                answer=answer,
                contexts=contexts,
                expected_answer=expected,
                client=openai_client
            )
            
            individual['metrics'] = metrics
            evaluated_count += 1
            print(f"      ✅ {individual['model_name']}: {metrics['combined_score']:.3f}")
        
        # Evaluar respuestas ensemble (ensemble es un dict de estrategias)
        for strategy_name, ensemble_result in question_result['ensemble'].items():
            answer = ensemble_result['answer']
            contexts = ensemble_result.get('contexts', [])
            
            # Si no hay contextos en ensemble, usar los del primer modelo
            if not contexts and question_result['individual']:
                contexts = question_result['individual'][0]['contexts']
            
            metrics = await evaluate_with_ragas(
                question=question,
                answer=answer,
                contexts=contexts,
                expected_answer=expected,
                client=openai_client
            )
            
            ensemble_result['metrics'] = metrics
            evaluated_count += 1
            print(f"      ✅ {strategy_name}: {metrics['combined_score']:.3f}")
        
        # Guardar progreso después de cada pregunta
        save_results(results, temp_output)
    
    eval_time = time.time() - eval_start
    total_time = time.time() - start_time
    
    print(f"\n✅ Evaluación completada en {eval_time:.1f}s")
    
    # === GUARDAR RESULTADOS FINALES ===
    final_output = OUTPUT_DIR / f"ensemble_quick_test_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_results(results, final_output)
    
    print("\n" + "="*80)
    print("✅ TEST RÁPIDO COMPLETADO")
    print("="*80)
    print(f"\n⏱️  Tiempo total: {total_time/60:.1f} minutos")
    print(f"   Generación: {gen_time/60:.1f} min")
    print(f"   Evaluación: {eval_time:.1f}s")
    print(f"\n📊 Resultados evaluados: {evaluated_count}")
    print(f"📁 Archivo final: {final_output}")
    
    # === RESUMEN RÁPIDO ===
    print("\n" + "="*80)
    print("📊 RESUMEN POR PREGUNTA")
    print("="*80)
    
    for q_result in results['results']:
        qid = q_result['question_id']
        question = q_result['question'][:60]
        
        print(f"\nP{qid}: {question}...")
        
        # Mejor individual
        best_ind = max(q_result['individual'], key=lambda x: x['metrics']['combined_score'])
        print(f"   🥇 Mejor individual: {best_ind['model_name']} ({best_ind['metrics']['combined_score']:.3f})")
        
        # Mejor ensemble (ensemble es un dict, no lista)
        best_ens_name, best_ens = max(
            q_result['ensemble'].items(),
            key=lambda item: item[1]['metrics']['combined_score']
        )
        print(f"   🎯 Mejor ensemble: {best_ens_name} ({best_ens['metrics']['combined_score']:.3f})")
        
        # Comparación
        improvement = best_ens['metrics']['combined_score'] - best_ind['metrics']['combined_score']
        if improvement > 0:
            print(f"   ✅ Ensemble mejora: +{improvement:.3f}")
        else:
            print(f"   ⚠️  Ensemble no mejora: {improvement:.3f}")
    
    return final_output


if __name__ == "__main__":
    print("\n🧪 Iniciando test rápido de benchmark ensemble...")
    print("   Preguntas: P11 (COLES), P20 (RESIS), P25 (Para-Mira-Ayuda)\n")
    
    result = asyncio.run(run_quick_test())
    
    if result:
        print(f"\n✅ Test completado exitosamente")
        print(f"📁 Resultados en: {result}")
    else:
        print(f"\n❌ Test falló")

