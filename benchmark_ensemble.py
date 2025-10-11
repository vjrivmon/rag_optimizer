#!/usr/bin/env python3
"""
🎯 Benchmark Ensemble - Evaluación de Estrategias Multi-Modelo

Ejecuta un benchmark completo comparando:
- Respuestas individuales de cada modelo
- Respuestas de diferentes estrategias de ensemble

Objetivo: Demostrar que el ensemble puede superar al mejor modelo individual.
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import sys

# OpenAI para evaluaciones RAGAs
from openai import AsyncOpenAI
from dotenv import load_dotenv
load_dotenv()

# Imports del proyecto
from src.core.model_wrapper import LLMWrapper
from src.core.enhanced_rag_engine_new import EnhancedRAGEngineNew
from src.ensemble.ensemble_engine import EnsembleRAGEngine
from benchmark_v2 import clean_thinking_tags

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

VECTOR_STORE_PATH = "data/vectorstore/chroma_db"
DATASET_PATH = "data/evaluation_dataset.json"

MODELS_CONFIG = [
    {"name": "gemma2:27b"},
    {"name": "llama3.3:70b"},
    {"name": "qwen3:32b"},
    {"name": "deepseek-r1:latest"},
]

# Endpoint por defecto (todos usan el mismo servidor)
DEFAULT_API_ENDPOINT = "https://ollama.gti-ia.upv.es:443/api/generate"

# Estrategias a evaluar
STRATEGIES = ['voting', 'weighted', 'routing', 'consensus']


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def load_dataset() -> List[Dict]:
    """Carga el dataset de evaluación"""
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


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

Sé muy estricto en las evaluaciones (escala 0-1):
1. faithfulness: ¿La respuesta se basa 100% en el contexto? ¿Alucina información?
2. answer_relevancy: ¿La respuesta aborda directamente la pregunta?
3. context_precision: ¿El contexto recuperado contiene la información necesaria?
4. context_recall: ¿Se recuperó suficiente contexto para responder bien?
5. answer_correctness: ¿La respuesta es correcta comparada con la RESPUESTA ESPERADA?
6. answer_similarity: ¿Qué tan similar es la respuesta a la RESPUESTA ESPERADA?

CRITERIOS DE PUNTUACIÓN:
- 1.0 = Perfecto, sin errores
- 0.8-0.9 = Excelente, errores menores
- 0.6-0.7 = Bueno, errores moderados
- 0.4-0.5 = Regular, errores significativos
- 0.2-0.3 = Pobre, muchos errores
- 0.0-0.1 = Muy malo o irrelevante

Responde SOLO con JSON:
{"faithfulness": 0.X, "answer_relevancy": 0.X, "context_precision": 0.X, "context_recall": 0.X, "answer_correctness": 0.X, "answer_similarity": 0.X}"""

    user_prompt = f"""PREGUNTA: {question}

RESPUESTA ESPERADA (Ground Truth):
{expected_answer}

CONTEXTO RECUPERADO:
{chr(10).join(contexts[:3])}

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
        
        # Parsear respuesta
        metrics = json.loads(completion.choices[0].message.content)
        
        # Calcular score combinado CON LOS MISMOS PESOS que benchmark_v2.py
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
        # Retornar métricas en 0 si falla
        return {
            'faithfulness': 0.0,
            'answer_relevancy': 0.0,
            'context_precision': 0.0,
            'context_recall': 0.0,
            'answer_correctness': 0.0,
            'answer_similarity': 0.0,
            'combined_score': 0.0
        }


# ============================================================================
# BENCHMARK PRINCIPAL
# ============================================================================

async def run_ensemble_benchmark():
    """Ejecuta el benchmark ensemble completo"""
    
    print("="*80)
    print("🎯 BENCHMARK ENSEMBLE - EVALUACIÓN MULTI-MODELO")
    print("="*80)
    print(f"\n📊 Configuración:")
    print(f"   Modelos: {len(MODELS_CONFIG)}")
    print(f"   Estrategias: {len(STRATEGIES)}")
    
    # Cargar dataset
    dataset = load_dataset()
    print(f"   Preguntas: {len(dataset)}")
    
    # Inicializar modelos
    print(f"\n🔧 Inicializando modelos...")
    models = {}
    rag_engines = {}
    
    for config in MODELS_CONFIG:
        model_name = config['name']
        print(f"   Cargando {model_name}...")
        
        try:
            model = LLMWrapper(
                model_name=model_name,
                api_endpoint=DEFAULT_API_ENDPOINT
            )
            models[model_name] = model
            
            # Crear RAG engine para cada modelo
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
    
    # Inicializar cliente OpenAI para evaluación
    print(f"\n🔧 Inicializando evaluador RAGAs...")
    openai_client = AsyncOpenAI()
    
    # Estructura de resultados
    results = {
        "timestamp": datetime.now().isoformat(),
        "benchmark_type": "ensemble",
        "models": list(rag_engines.keys()),
        "strategies": STRATEGIES,
        "total_questions": len(dataset),
        "results": []
    }
    
    # Procesar cada pregunta
    print(f"\n{'='*80}")
    print(f"🚀 INICIANDO GENERACIÓN DE RESPUESTAS")
    print(f"{'='*80}\n")
    
    generation_start = time.time()
    
    for idx, q in enumerate(dataset, 1):
        question_id = q['id']
        question = q['question']
        expected_answer = q['expected_answer']
        
        print(f"\n[{idx}/{len(dataset)}] P{question_id}: {question}")
        
        try:
            # Generar respuestas con ensemble (individuales + estrategias)
            result = ensemble_engine.process_question_complete(question, question_id)
            
            # Limpiar tags de razonamiento en todas las respuestas
            for individual in result['individual']:
                individual['answer'] = clean_thinking_tags(individual['answer'])
            
            for strategy_name, strategy_result in result['ensemble'].items():
                if 'answer' in strategy_result:
                    strategy_result['answer'] = clean_thinking_tags(strategy_result['answer'])
            
            # Añadir respuesta esperada
            result['expected_answer'] = expected_answer
            result['category'] = q.get('category', 'N/A')
            result['difficulty'] = q.get('difficulty', 'N/A')
            
            results['results'].append(result)
            
            print(f"✅ P{question_id} completada")
            
        except Exception as e:
            print(f"❌ Error procesando P{question_id}: {str(e)}")
            continue
    
    generation_time = time.time() - generation_start
    print(f"\n{'='*80}")
    print(f"✅ GENERACIÓN COMPLETADA en {generation_time/60:.1f} minutos")
    print(f"{'='*80}\n")
    
    # Guardar resultados temporales (antes de evaluación)
    temp_output = f"results/ensemble_temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_results(results, temp_output)
    
    # FASE 2: Evaluación con RAGAs
    print(f"\n{'='*80}")
    print(f"🎯 INICIANDO EVALUACIÓN CON RAGAs")
    print(f"{'='*80}\n")
    
    evaluation_start = time.time()
    total_evaluations = 0
    
    for result in results['results']:
        question = result['question']
        question_id = result['question_id']
        expected = result['expected_answer']
        
        print(f"\n📊 Evaluando P{question_id}...")
        
        # Evaluar respuestas individuales
        for individual in result['individual']:
            try:
                metrics = await evaluate_with_ragas(
                    question=question,
                    answer=individual['answer'],
                    contexts=individual['contexts'],
                    expected_answer=expected,
                    client=openai_client
                )
                individual['metrics'] = metrics
                total_evaluations += 1
                print(f"   ✅ {individual['model_name']}: {metrics['combined_score']:.2f}")
                
            except Exception as e:
                print(f"   ❌ Error evaluando {individual['model_name']}: {str(e)}")
                continue
        
        # Evaluar respuestas de estrategias ensemble
        for strategy_name, strategy_result in result['ensemble'].items():
            if 'answer' not in strategy_result or 'error' in strategy_result:
                continue
            
            try:
                metrics = await evaluate_with_ragas(
                    question=question,
                    answer=strategy_result['answer'],
                    contexts=strategy_result.get('contexts', []),
                    expected_answer=expected,
                    client=openai_client
                )
                strategy_result['metrics'] = metrics
                total_evaluations += 1
                print(f"   ✅ {strategy_name}: {metrics['combined_score']:.2f}")
                
            except Exception as e:
                print(f"   ❌ Error evaluando {strategy_name}: {str(e)}")
                continue
    
    evaluation_time = time.time() - evaluation_start
    
    print(f"\n{'='*80}")
    print(f"✅ EVALUACIÓN COMPLETADA en {evaluation_time/60:.1f} minutos")
    print(f"   Total evaluaciones: {total_evaluations}")
    print(f"{'='*80}\n")
    
    # Calcular estadísticas agregadas
    print(f"\n📊 Calculando estadísticas...")
    results['summary'] = calculate_summary_stats(results['results'])
    results['total_time'] = {
        'generation_minutes': generation_time / 60,
        'evaluation_minutes': evaluation_time / 60,
        'total_minutes': (generation_time + evaluation_time) / 60
    }
    
    # Guardar resultados finales
    output_path = f"results/ensemble_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_results(results, output_path)
    
    # Mostrar resumen
    print_summary(results['summary'])
    
    return results


def calculate_summary_stats(results: List[Dict]) -> Dict:
    """Calcula estadísticas agregadas del benchmark"""
    
    summary = {
        'individual_models': {},
        'ensemble_strategies': {},
        'best_individual': None,
        'best_ensemble': None,
        'improvement': None
    }
    
    # Agrupar scores por modelo
    model_scores = {}
    for result in results:
        for individual in result['individual']:
            model_name = individual['model_name']
            if model_name not in model_scores:
                model_scores[model_name] = []
            
            if 'metrics' in individual and 'combined_score' in individual['metrics']:
                model_scores[model_name].append(individual['metrics']['combined_score'])
    
    # Calcular promedios individuales
    for model, scores in model_scores.items():
        if scores:
            avg_score = sum(scores) / len(scores)
            correct_count = sum(1 for s in scores if s >= 0.8)
            summary['individual_models'][model] = {
                'avg_score': avg_score,
                'correct_count': correct_count,
                'total_questions': len(scores)
            }
    
    # Agrupar scores por estrategia
    strategy_scores = {}
    for result in results:
        for strategy_name, strategy_result in result.get('ensemble', {}).items():
            if strategy_name not in strategy_scores:
                strategy_scores[strategy_name] = []
            
            if 'metrics' in strategy_result and 'combined_score' in strategy_result['metrics']:
                strategy_scores[strategy_name].append(strategy_result['metrics']['combined_score'])
    
    # Calcular promedios ensemble
    for strategy, scores in strategy_scores.items():
        if scores:
            avg_score = sum(scores) / len(scores)
            correct_count = sum(1 for s in scores if s >= 0.8)
            summary['ensemble_strategies'][strategy] = {
                'avg_score': avg_score,
                'correct_count': correct_count,
                'total_questions': len(scores)
            }
    
    # Encontrar mejor individual
    if summary['individual_models']:
        best_model = max(summary['individual_models'].items(), key=lambda x: x[1]['avg_score'])
        summary['best_individual'] = {
            'model': best_model[0],
            'avg_score': best_model[1]['avg_score'],
            'correct_count': best_model[1]['correct_count']
        }
    
    # Encontrar mejor ensemble
    if summary['ensemble_strategies']:
        best_strategy = max(summary['ensemble_strategies'].items(), key=lambda x: x[1]['avg_score'])
        summary['best_ensemble'] = {
            'strategy': best_strategy[0],
            'avg_score': best_strategy[1]['avg_score'],
            'correct_count': best_strategy[1]['correct_count']
        }
        
        # Calcular mejora sobre mejor individual
        if summary['best_individual'] and summary['best_ensemble']:
            improvement = summary['best_ensemble']['avg_score'] - summary['best_individual']['avg_score']
            improvement_pct = (improvement / summary['best_individual']['avg_score']) * 100
            
            summary['improvement'] = {
                'absolute': improvement,
                'percentage': improvement_pct,
                'beats_individual': improvement > 0
            }
    
    return summary


def print_summary(summary: Dict):
    """Imprime resumen de resultados"""
    
    print(f"\n{'='*80}")
    print(f"📊 RESUMEN DE RESULTADOS")
    print(f"{'='*80}\n")
    
    # Modelos individuales
    print(f"🤖 MODELOS INDIVIDUALES:")
    for model, stats in sorted(summary['individual_models'].items(), key=lambda x: x[1]['avg_score'], reverse=True):
        print(f"   {model:20s} | Avg: {stats['avg_score']:.3f} | Correctas: {stats['correct_count']}/{stats['total_questions']}")
    
    # Estrategias ensemble
    print(f"\n🎲 ESTRATEGIAS ENSEMBLE:")
    for strategy, stats in sorted(summary['ensemble_strategies'].items(), key=lambda x: x[1]['avg_score'], reverse=True):
        print(f"   {strategy:20s} | Avg: {stats['avg_score']:.3f} | Correctas: {stats['correct_count']}/{stats['total_questions']}")
    
    # Comparación
    if summary['best_individual'] and summary['best_ensemble']:
        print(f"\n🏆 COMPARACIÓN:")
        print(f"   Mejor Individual:  {summary['best_individual']['model']:20s} | Score: {summary['best_individual']['avg_score']:.3f}")
        print(f"   Mejor Ensemble:    {summary['best_ensemble']['strategy']:20s} | Score: {summary['best_ensemble']['avg_score']:.3f}")
        
        if summary['improvement']:
            imp = summary['improvement']
            if imp['beats_individual']:
                print(f"\n   🎉 ¡ENSEMBLE GANA! Mejora: +{imp['absolute']:.3f} ({imp['percentage']:+.1f}%)")
            else:
                print(f"\n   📉 Ensemble no superó al individual: {imp['absolute']:.3f} ({imp['percentage']:.1f}%)")
    
    print(f"\n{'='*80}\n")


# ============================================================================
# EJECUCIÓN
# ============================================================================

if __name__ == "__main__":
    print("\n🚀 Iniciando Benchmark Ensemble...\n")
    
    try:
        results = asyncio.run(run_ensemble_benchmark())
        
        if results:
            print("\n✅ Benchmark completado exitosamente!")
            print(f"\n💡 Siguiente paso: Ejecutar dashboard ensemble para análisis visual")
            print(f"   streamlit run interface/app_ensemble.py")
        else:
            print("\n❌ Benchmark falló")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Benchmark interrumpido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error fatal: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

