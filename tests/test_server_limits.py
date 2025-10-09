#!/usr/bin/env python3
"""
Test de límites del servidor UPV Ollama
Encuentra el número óptimo de workers sin interferir con benchmarks en ejecución

Uso:
    python test_server_limits.py [--max-workers 16] [--cooldown 30]
"""

import argparse
import json
import time
import sys
from pathlib import Path
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, List, Tuple

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.core.rag_engine import ConfigurableRAGEngine as RAGEngine
from src.core.model_wrapper import LLMWrapper as ModelWrapper
from src.optimization.optimizer import ParameterOptimizer


# Preguntas de prueba (DIFERENTES a las del benchmark principal)
TEST_QUESTIONS = [
    {
        "question": "¿Qué servicios ofrece la residencia?",
        "expected_answer": "La residencia ofrece servicios de alojamiento, comedor, lavandería, wifi y zonas comunes."
    },
    {
        "question": "¿Cuál es el horario de la biblioteca?",
        "expected_answer": "La biblioteca está abierta de lunes a viernes de 9:00 a 21:00 horas."
    },
    {
        "question": "¿Cómo se solicita una habitación?",
        "expected_answer": "Las habitaciones se solicitan a través del portal online de la residencia."
    }
]


def test_single_question(args: Tuple) -> Dict:
    """
    Evalúa una pregunta con un modelo

    Returns:
        dict con success, latency, error_type
    """
    question_data, model_config, worker_id = args

    try:
        # RAG Engine
        rag_engine = RAGEngine(
            vector_store_path="data/vectorstore/chroma_db"
        )

        # Model Wrapper
        model = ModelWrapper(
            model_name=model_config['name'],
            api_endpoint=model_config['endpoint'],
            context_window=model_config.get('context_window', 8000)
        )

        # Optimizer
        optimizer = ParameterOptimizer(
            context_window=model_config.get('context_window', 8000),
            model_name=model_config['name']
        )

        params = optimizer.suggest()
        rag_engine.update_params({
            'top_k': int(params['top_k']),
            'similarity_threshold': float(params['similarity_threshold'])
        })

        # Generate response
        start_time = time.time()

        docs = rag_engine.retrieve(question_data['question'])
        context = rag_engine.build_context(docs[:10])
        prompt = model.build_rag_prompt(question_data['question'], context, params['strictness'])

        generation = model.generate(
            prompt,
            temperature=params['temperature'],
            top_p=params['top_p'],
            max_tokens=params['max_tokens']
        )

        latency = time.time() - start_time

        if generation['success']:
            return {
                'success': True,
                'latency': latency,
                'error_type': None,
                'worker_id': worker_id
            }
        else:
            return {
                'success': False,
                'latency': latency,
                'error_type': 'GENERATION_FAILED',
                'error_message': str(generation.get('error', 'Unknown generation error')),
                'worker_id': worker_id
            }

    except Exception as e:
        error_str = str(e)

        # Detectar tipo de error
        if '429' in error_str or 'rate limit' in error_str.lower():
            error_type = 'RATE_LIMIT'
        elif 'timeout' in error_str.lower():
            error_type = 'TIMEOUT'
        elif 'connection' in error_str.lower():
            error_type = 'CONNECTION'
        else:
            error_type = 'OTHER'

        return {
            'success': False,
            'latency': None,
            'error_type': error_type,
            'error_message': error_str[:200],
            'worker_id': worker_id
        }


def test_workers(num_workers: int, model_config: Dict, cooldown: int = 10) -> Dict:
    """
    Prueba el servidor con N workers

    Args:
        num_workers: Número de workers a probar
        model_config: Configuración del modelo
        cooldown: Segundos de espera antes de iniciar

    Returns:
        dict con resultados del test
    """
    print(f"\n{'='*80}")
    print(f"🧪 PROBANDO {num_workers} WORKERS")
    print(f"{'='*80}")

    # Cooldown antes de empezar
    if cooldown > 0:
        print(f"⏳ Esperando {cooldown}s antes de iniciar (cooldown)...")
        time.sleep(cooldown)

    # Preparar tareas (1 pregunta por worker)
    tasks = []
    for i in range(num_workers):
        question = TEST_QUESTIONS[i % len(TEST_QUESTIONS)]
        tasks.append((question, model_config, i+1))

    # Ejecutar en paralelo
    results = []
    start_time = time.time()

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = {executor.submit(test_single_question, task): task for task in tasks}

        for future in as_completed(futures):
            result = future.result()
            results.append(result)

            # Mostrar progreso
            if result['success']:
                print(f"   ✅ Worker {result['worker_id']}: {result['latency']:.2f}s")
            else:
                print(f"   ❌ Worker {result['worker_id']}: {result['error_type']}")
                if 'error_message' in result:
                    print(f"      └─ {result['error_message']}")

    total_time = time.time() - start_time

    # Analizar resultados
    success_count = sum(1 for r in results if r['success'])
    error_count = len(results) - success_count
    success_rate = success_count / len(results)

    # Latencias promedio
    latencies = [r['latency'] for r in results if r['success']]
    avg_latency = sum(latencies) / len(latencies) if latencies else None

    # Tipos de errores
    error_types = {}
    for r in results:
        if not r['success']:
            error_type = r['error_type']
            error_types[error_type] = error_types.get(error_type, 0) + 1

    summary = {
        'num_workers': num_workers,
        'total_tasks': len(results),
        'success_count': success_count,
        'error_count': error_count,
        'success_rate': success_rate,
        'avg_latency': avg_latency,
        'total_time': total_time,
        'error_types': error_types,
        'timestamp': datetime.now().isoformat()
    }

    # Mostrar resumen
    print(f"\n📊 Resumen:")
    print(f"   Éxito: {success_count}/{len(results)} ({success_rate*100:.1f}%)")
    if avg_latency:
        print(f"   Latencia promedio: {avg_latency:.2f}s")
    print(f"   Tiempo total: {total_time:.1f}s")

    if error_types:
        print(f"   Errores:")
        for error_type, count in error_types.items():
            print(f"      - {error_type}: {count}")

    return summary


def find_optimal_workers(max_workers: int, model_config: Dict, cooldown: int = 30) -> Dict:
    """
    Encuentra el número óptimo de workers mediante tests incrementales

    Args:
        max_workers: Máximo número de workers a probar
        model_config: Configuración del modelo
        cooldown: Segundos entre tests

    Returns:
        dict con reporte completo
    """
    print(f"\n{'#'*80}")
    print(f"🚀 TEST DE LÍMITES DEL SERVIDOR UPV OLLAMA")
    print(f"{'#'*80}")
    print(f"Modelo: {model_config['name']}")
    print(f"Endpoint: {model_config['endpoint']}")
    print(f"Rango de prueba: 4 → {max_workers} workers")
    print(f"Cooldown entre tests: {cooldown}s")
    print(f"{'#'*80}\n")

    # Tests incrementales
    worker_counts = [4, 6, 8, 12, 16]
    worker_counts = [w for w in worker_counts if w <= max_workers]

    results = []
    optimal_workers = 4  # Default seguro

    for num_workers in worker_counts:
        try:
            summary = test_workers(num_workers, model_config, cooldown)
            results.append(summary)

            # Criterio de parada: si error rate > 20%, parar
            if summary['error_count'] > 0 and summary['success_rate'] < 0.8:
                print(f"\n⚠️ LÍMITE DETECTADO: {summary['error_count']} errores con {num_workers} workers")
                print(f"   Recomendación: Usar {optimal_workers} workers como máximo")
                break

            # Si funciona bien, este es el nuevo óptimo
            if summary['success_rate'] >= 0.95:
                optimal_workers = num_workers
                print(f"   ✅ {num_workers} workers funciona correctamente")

        except KeyboardInterrupt:
            print(f"\n❌ Test interrumpido por usuario")
            break
        except Exception as e:
            print(f"\n❌ Error durante test con {num_workers} workers: {e}")
            break

    # Generar reporte final
    report = {
        'timestamp': datetime.now().isoformat(),
        'model': model_config['name'],
        'endpoint': model_config['endpoint'],
        'max_workers_tested': max(r['num_workers'] for r in results),
        'optimal_workers': optimal_workers,
        'tests': results,
        'recommendation': f"Usar max_workers={optimal_workers} para garantizar estabilidad"
    }

    return report


def print_final_report(report: Dict):
    """Imprime reporte final formateado"""

    print(f"\n\n{'='*80}")
    print(f"📋 REPORTE FINAL - TEST DE LÍMITES")
    print(f"{'='*80}\n")

    print(f"🕐 Fecha: {report['timestamp']}")
    print(f"🤖 Modelo: {report['model']}")
    print(f"🌐 Endpoint: {report['endpoint']}")
    print(f"\n{'='*80}")
    print(f"✅ RESULTADO: Usar máximo {report['optimal_workers']} workers")
    print(f"{'='*80}\n")

    print(f"📊 Resumen de tests:\n")

    for test in report['tests']:
        status = "✅" if test['success_rate'] >= 0.95 else "⚠️" if test['success_rate'] >= 0.8 else "❌"
        print(f"{status} {test['num_workers']:2d} workers: "
              f"{test['success_count']}/{test['total_tasks']} éxitos "
              f"({test['success_rate']*100:.1f}%) "
              f"- {test['avg_latency']:.2f}s promedio" if test['avg_latency'] else "")

        if test['error_types']:
            for error_type, count in test['error_types'].items():
                print(f"      └─ {error_type}: {count} errores")

    print(f"\n💡 Recomendación:")
    print(f"   {report['recommendation']}")
    print(f"   Actualizar benchmark_parallel.py línea 359:")
    print(f"   max_workers = min(workers, {report['optimal_workers']})")
    print(f"\n{'='*80}\n")


def main():
    """Función principal"""

    parser = argparse.ArgumentParser(
        description='Test de límites del servidor UPV Ollama'
    )
    parser.add_argument(
        '--max-workers',
        type=int,
        default=16,
        help='Máximo número de workers a probar (default: 16)'
    )
    parser.add_argument(
        '--cooldown',
        type=int,
        default=30,
        help='Segundos de espera entre tests (default: 30)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='results/server_limits_report.json',
        help='Archivo JSON de salida (default: results/server_limits_report.json)'
    )

    args = parser.parse_args()

    # Cargar configuración de modelos
    config_path = Path(__file__).parent / 'config' / 'benchmark_config.json'

    if not config_path.exists():
        print(f"❌ Error: No se encuentra {config_path}")
        return

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Usar gemma2:27b para el test (mismo que evaluator)
    model_config = None
    for model in config['models']:
        if 'gemma2' in model['name'].lower():
            model_config = model
            break

    if not model_config:
        print(f"❌ Error: No se encuentra gemma2:27b en la configuración")
        return

    try:
        # Ejecutar test de límites
        report = find_optimal_workers(
            max_workers=args.max_workers,
            model_config=model_config,
            cooldown=args.cooldown
        )

        # Guardar reporte
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"💾 Reporte guardado en: {output_path}")

        # Mostrar reporte final
        print_final_report(report)

    except KeyboardInterrupt:
        print(f"\n\n❌ Test interrumpido por usuario")
    except Exception as e:
        print(f"\n❌ Error durante test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
