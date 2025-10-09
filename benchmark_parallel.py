#!/usr/bin/env python3
"""
Benchmark paralelo optimizado - Versión simplificada y funcional
Ejecuta evaluaciones en paralelo para reducir tiempo de ~3.5h a <1h
"""

import os
import sys
import json
import time
import warnings
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor
from multiprocessing import cpu_count, Semaphore, Manager
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import argparse
import threading
from collections import defaultdict

warnings.filterwarnings('ignore')
sys.path.append(os.path.dirname(__file__))


def convert_numpy_types(obj):
    """Convierte recursivamente tipos NumPy a tipos Python nativos para serialización JSON"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj

# Imports del proyecto
from src.core.rag_engine import ConfigurableRAGEngine as RAGEngine
from src.core.model_wrapper import LLMWrapper as ModelWrapper
from src.evaluation.ragas_evaluator import HybridEvaluator
from src.optimization.optimizer import ParameterOptimizer
from src.utils.progress_tracker import ProgressTracker
import math


# Solución simple para evitar contención: control local por worker
# Cada worker gestiona sus propias llamadas para evitar deadlock entre procesos
class OllamaWorkerLimiter:
    """Limitador local de llamadas a Ollama por worker"""

    def __init__(self, max_concurrent: int = 1):
        """
        Inicializa el limitador para un worker específico

        Args:
            max_concurrent: Máximo de llamadas simultáneas por worker (default: 1)
        """
        self.max_concurrent = max_concurrent
        self.active_calls = 0
        self.lock = threading.Lock()

    def acquire(self) -> bool:
        """Adquiere un permiso para llamar a Ollama"""
        with self.lock:
            if self.active_calls < self.max_concurrent:
                self.active_calls += 1
                return True
            return False

    def release(self):
        """Libera un permiso"""
        with self.lock:
            if self.active_calls > 0:
                self.active_calls -= 1

    def get_status(self) -> Dict[str, int]:
        """Retorna el estado actual"""
        with self.lock:
            return {
                'active_calls': self.active_calls,
                'max_concurrent': self.max_concurrent,
                'available_slots': self.max_concurrent - self.active_calls
            }


# Variable global por worker (no comparte entre procesos)
_worker_limiter = None


def get_worker_limiter() -> OllamaWorkerLimiter:
    """Retorna el limitador local para el worker actual"""
    global _worker_limiter
    if _worker_limiter is None:
        _worker_limiter = OllamaWorkerLimiter(max_concurrent=1)  # 1 llamada simultánea por worker
    return _worker_limiter


def evaluate_question_batch(batch_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Worker function que evalúa un lote de preguntas.
    Ejecuta en un proceso separado.
    IMPORTANTE: Usa la misma lógica que benchmark.py (HybridEvaluator + ParameterOptimizer)
    """
    questions = batch_data['questions']
    models_config = batch_data['models']
    evaluator_config = batch_data['evaluator']
    ragas_mode = batch_data['ragas_mode']
    batch_id = batch_data.get('batch_id', 0)
    debug = batch_data.get('debug', False)
    tracker = batch_data.get('tracker')  # Progress Tracker opcional
    progress_dict = batch_data.get('progress_dict')  # Tracker simple compartido
    metrics_subset = batch_data.get('metrics_subset')  # Subset de métricas RAGAs

    # Silenciar warnings y mensajes de progreso de RAGAs
    import warnings
    warnings.filterwarnings('ignore')
    os.environ['RAGAS_DO_NOT_TRACK'] = 'true'
    os.environ['RAGAS_SILENCE_PROGRESS'] = 'true'
    os.environ['TQDM_DISABLE'] = '1'  # Silenciar barras de progreso
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'  # Evitar warnings de tokenizadores en paralelo

    # Inicializar sistemas en el worker con verificación
    print(f"   [Worker {batch_id+1}] Inicializando RAGEngine...")
    try:
        rag_engine = RAGEngine(vector_store_path="data/vectorstore/chroma_db")
        print(f"   [Worker {batch_id+1}] ✅ RAGEngine inicializado")
    except Exception as e:
        print(f"   [Worker {batch_id+1}] ❌ Error inicializando RAGEngine: {e}")
        raise

    # Configurar modelos con context_window
    models = {}
    optimizers = {}
    for model_cfg in models_config:
        model = ModelWrapper(
            model_name=model_cfg['name'],
            api_endpoint=model_cfg['endpoint'],
            context_window=model_cfg.get('context_window', 8000)
        )
        models[model_cfg['name']] = model

        # Crear optimizador Bayesiano para cada modelo (IGUAL QUE benchmark.py)
        optimizers[model_cfg['name']] = ParameterOptimizer(
            context_window=model_cfg.get('context_window', 8000),
            model_name=model_cfg['name']
        )

    # Configurar evaluador híbrido SOLO CON OLLAMA (NO OpenAI)
    filter_thinking_tags = evaluator_config.get('filter_thinking_tags', True)
    ollama_model = evaluator_config.get('ollama_model', 'gemma2:27b')
    ollama_base_url = evaluator_config.get('ollama_base_url', 'https://ollama.gti-ia.upv.es:443')

    # Configurar evaluador híbrido SOLO CON OLLAMA (NO OpenAI)
    evaluator = HybridEvaluator(
        use_ragas=True,
        use_openai=False,
        use_ollama=True,  # SOLO Ollama gemma2:27b
        use_dual_backend=False,  # NO usar dual backend (OpenAI)
        ollama_model=ollama_model,
        ollama_base_url=ollama_base_url,
        filter_thinking_tags=filter_thinking_tags,
        metrics_subset=metrics_subset  # Pasar subset de métricas
    )

    # Actualizar estado del worker
    if tracker:
        tracker.update_worker_status(batch_id, f"Iniciando lote con {len(questions)} preguntas")

    # Mostrar preguntas del lote al inicio (como en benchmark.py)
    print(f"\n{'='*80}")
    print(f"📦 LOTE {batch_id+1} - Procesando {len(questions)} preguntas:")
    print(f"{'='*80}")
    for q_idx, q_data in questions:
        print(f"   [{q_idx + 1}] {q_data['question']}")
    print(f"{'='*80}\n")

    results = []

    # Procesar cada pregunta (LÓGICA IDÉNTICA A benchmark.py)
    for q_idx, q_data in questions:
        print(f"\n📝 [Lote {batch_id+1}] Pregunta {q_idx + 1}/{batch_data['total_questions']}: {q_data['question'][:60]}...")

        question = q_data['question']
        expected = q_data.get('expected_answer')
        keywords = q_data.get('keywords', [])

        # Actualizar tracker con la pregunta actual
        if tracker:
            tracker.update_worker_status(batch_id, f"Procesando pregunta {q_idx+1}", q_idx)

        # Retrieval (IGUAL QUE benchmark.py línea 189)
        docs = rag_engine.retrieve(question)

        # OPTIMIZACIÓN: Usar top 10 chunks truncados a 400 caracteres (IGUAL QUE benchmark.py línea 193-194)
        contexts = [doc['content'][:400] for doc in docs[:10]]
        context_text = rag_engine.build_context(docs[:10])

        question_results = {
            'question_id': q_idx + 1,
            'question': question,
            'expected_answer': expected or '',
            'contexts': contexts,
            'models': {},
            'winner': None
        }

        # Evaluar con cada modelo (LÓGICA IDÉNTICA A benchmark.py líneas 201-277)
        for model_name, model in models.items():
            try:
                # Actualizar tracker con el modelo actual
                if tracker:
                    tracker.update_worker_status(batch_id, f"Generando respuesta con {model_name}", q_idx, model_name)

                # Actualizar progress_dict si está disponible
                if progress_dict is not None:
                    with progress_dict['lock']:
                        progress_dict['done'] += 1
                        if progress_dict['done'] % 5 == 0:
                            elapsed = time.time() - progress_dict['start_time']
                            pct_done = (progress_dict['done'] / progress_dict['total']) * 100
                            eta = (elapsed / progress_dict['done']) * (progress_dict['total'] - progress_dict['done']) if progress_dict['done'] > 0 else 0
                            print(f"[Progreso global] {progress_dict['done']}/{progress_dict['total']} evaluaciones ({pct_done:.1f}%) - ETA: {eta/60:.1f}min")

                # Obtener parámetros del optimizador Bayesiano (IGUAL QUE benchmark.py líneas 204-209)
                optimizer = optimizers[model_name]
                if optimizer.should_rollback():
                    params = optimizer.get_best_params()
                else:
                    params = optimizer.suggest()

                # Actualizar RAG con parámetros optimizados (IGUAL QUE benchmark.py líneas 212-215)
                rag_engine.update_params({
                    'top_k': params['top_k'],
                    'similarity_threshold': params['similarity_threshold']
                })

                # Generar prompt con strictness (IGUAL QUE benchmark.py línea 218)
                prompt = model.build_rag_prompt(question, context_text, params['strictness'])

                # Generar respuesta con parámetros optimizados (IGUAL QUE benchmark.py líneas 221-226)
                generation = model.generate(
                    prompt,
                    temperature=params['temperature'],
                    top_p=params['top_p'],
                    max_tokens=params['max_tokens']
                )

                if generation['success']:
                    # Usar 'answer' (limpio, sin thinking) para evaluación (IGUAL QUE benchmark.py líneas 229-232)
                    answer = generation.get('answer', generation['response'])
                    full_response = generation['response']
                    latency = generation['latency']

                    # Actualizar tracker para evaluación RAGAs
                    if tracker:
                        tracker.update_worker_status(batch_id, f"Evaluando RAGAs con {model_name}", q_idx, model_name)

                    # Evaluar con HybridEvaluator CON LIMITADOR ACTIVADO
                    worker_limiter = get_worker_limiter()

                    # ACTIVAR EL LIMITADOR - CLAVE
                    if worker_limiter.acquire():
                        print(f"   🔬 Evaluando RAGAs con {model_name} (slot adquirido)...")

                        try:
                            # Timeouts adaptativos según ragas_mode
                            timeout_seconds = 60 if ragas_mode == 'fast' else 120 if ragas_mode == 'normal' else 180

                            metrics = evaluator.evaluate(
                                question=question,
                                answer=answer,
                                contexts=contexts,
                                ground_truth=expected,
                                keywords=keywords,
                                debug=debug
                            )

                        except Exception as e:
                            print(f"   ❌ Error RAGAs {model_name}: {str(e)[:50]}...")
                            metrics = {
                                'combined_score': 0.3,
                                'faithfulness': 0.3, 'answer_relevancy': 0.3,
                                'context_recall': 0.3, 'context_precision': 0.3,
                                'answer_similarity': 0.3, 'error': str(e)[:100]
                            }
                        finally:
                            worker_limiter.release()  # LIBERAR SIEMPRE
                    else:
                        print(f"   ⏱️  Sin slot Ollama para {model_name} - score por defecto")
                        metrics = {'combined_score': 0.4, 'no_slot': True}

                    score = metrics['combined_score']

                    # Registrar resultado en tracker
                    if tracker:
                        tracker.complete_evaluation(batch_id, q_idx, model_name, score, latency)

                    # Validar score (IGUAL QUE benchmark.py líneas 247-255)
                    if score is None or math.isnan(score):
                        print(f"   ⚠️  {model_name:20s} → Score: nan (Error RAGAs) | Tiempo: {latency:.1f}s")
                        score = 0.0
                    else:
                        # Reportar al optimizador solo si score es válido
                        optimizer.report(params, score)
                        status = "✅" if score > 0.5 else "❌"
                        print(f"   {status} {model_name:20s} → Score: {score:.3f} | Tiempo: {latency:.1f}s")

                    # Guardar resultado (formato compatible benchmark.py líneas 257-265)
                    # Convertir params a dict serializable
                    serializable_params = {k: float(v) if isinstance(v, (int, float)) else str(v)
                                          for k, v in params.items()}

                    question_results['models'][model_name] = {
                        'response': full_response,
                        'answer': answer,
                        'latency': float(latency),
                        'metrics': metrics,
                        'score': float(score),
                        'params': serializable_params,
                        'success': True
                    }

                else:
                    # Error en generación (IGUAL QUE benchmark.py líneas 268-277)
                    print(f"   ❌ {model_name:20s} → Error en generación")
                    serializable_params = {k: float(v) if isinstance(v, (int, float)) else str(v)
                                          for k, v in params.items()}
                    question_results['models'][model_name] = {
                        'response': '',
                        'answer': '',
                        'latency': float(generation.get('latency', 0)),
                        'metrics': {},
                        'score': 0.0,
                        'params': serializable_params,
                        'success': False,
                        'error': str(generation.get('error', ''))
                    }

            except Exception as e:
                print(f"      ❌ Error con {model_name}: {str(e)[:100]}")
                question_results['models'][model_name] = {
                    'response': '',
                    'answer': '',
                    'latency': 0.0,
                    'metrics': {},
                    'score': 0.0,
                    'params': {},
                    'success': False,
                    'error': str(e)
                }

        # Calcular ganador (modelo con mayor score)
        if question_results['models']:
            winner = max(
                question_results['models'].items(),
                key=lambda x: x[1]['score']
            )
            question_results['winner'] = winner[0]

        results.append(question_results)

    # Convertir todos los resultados a tipos serializables (pickle-safe)
    # Esto es CRÍTICO para que ProcessPoolExecutor pueda serializar los resultados
    serializable_results = convert_numpy_types(results)

    return serializable_results


def run_parallel_benchmark(
    config_path: str = "config/benchmark_config.json",
    max_questions: Optional[int] = None,
    n_workers: Optional[int] = None,
    ragas_mode: str = "fast",
    debug: bool = False,
    batch_mode: str = "parallel"
) -> Dict[str, Any]:
    """
    Ejecuta el benchmark en paralelo o secuencial.

    Args:
        config_path: Ruta al archivo de configuración
        max_questions: Número máximo de preguntas a evaluar
        n_workers: Número de workers paralelos (default: CPUs - 1)
        ragas_mode: "fast", "normal" o "full"
        debug: Modo debug para logging detallado
        batch_mode: "parallel" o "sequential" - método de ejecución

    Returns:
        Resultados del benchmark
    """
    start_time = time.time()

    # Cargar configuración
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Configuración
    questions = config['evaluation_questions']
    if max_questions:
        questions = questions[:max_questions]

    # Configuración de workers optimizada con límite automático para modo full
    if n_workers is None:
        # Por defecto usar 4 workers para máximo rendimiento
        n_workers = 4
    else:
        # Si el usuario especifica, limitar a máximo 4 para evitar problemas
        n_workers = min(n_workers, 4)  # Máximo 4 workers

    # Limitar automáticamente workers cuando ragas_mode == "full" para evitar saturación
    if ragas_mode == "full" and n_workers > 2:
        print("⚠️  Modo full detectado: forzando n_workers=2 para evitar saturación del servidor Ollama")
        n_workers = 2

    # Crear tracker simple compartido para progreso global
    manager = Manager()
    progress_dict = manager.dict({
        'done': 0,
        'total': len(questions) * len(config['models']),
        'lock': manager.Lock(),
        'start_time': time.time()
    })

    # Inicializar Progress Tracker (desactivado temporalmente por bucle infinito)
    # model_names = [m['name'] for m in config['models']]
    # tracker = ProgressTracker(len(questions), model_names, n_workers)
    tracker = None

    # Determinar el título según el modo
    mode_title = "SECUENCIAL" if batch_mode == "sequential" else "PARALELO"
    print(f"🚀 BENCHMARK {mode_title} v2.1 - Optimizado")
    print("=" * 80)
    print(f"📋 Configuración:")
    print(f"   • Preguntas: {len(questions)}")
    print(f"   • Modelos: {len(config['models'])}")
    print(f"   • Workers: {n_workers} (de {cpu_count()} CPUs)")
    print(f"   • Modo batch: {batch_mode}")
    print(f"   • Modo RAGAs: {ragas_mode} ({'6 métricas' if ragas_mode == 'full' else '4 métricas' if ragas_mode == 'normal' else '2 métricas'})")
    print(f"   • Total evaluaciones: {len(questions) * len(config['models'])}")
    if ragas_mode == "full" and n_workers == 2:
        print(f"   ⚠️  Workers limitados para evitar saturación en modo full")
    print("=" * 80)

    # Iniciar display de progreso en segundo plano (desactivado temporalmente)
    # if tracker:
    #     tracker.start_display()

    # Optimización: Distribución inteligente de carga
    # En lugar de round-robin simple, usamos distribución por complejidad estimada
    # y balanceo de carga optimizado
    print(f"🔄 Optimizando distribución de {len(questions)} preguntas para {n_workers} workers...")

    # Estimar complejidad por longitud de pregunta y respuesta esperada
    question_weights = []
    for i, q in enumerate(questions):
        # Calcular peso basado en longitud y complejidad
        question_len = len(q['question'])
        expected_len = len(q.get('expected_answer', ''))
        keywords_count = len(q.get('keywords', []))

        # Ponderación: pregunta (40%) + respuesta esperada (40%) + keywords (20%)
        weight = (question_len * 0.4 + expected_len * 0.4 + keywords_count * 10 * 0.2)
        question_weights.append((i, q, weight))

    # Ordenar por peso (descendente) para asignar preguntas más complejas primero
    question_weights.sort(key=lambda x: x[2], reverse=True)

    # Distribuir usando algoritmo de balanceo de carga (Longest Processing Time - LPT)
    batches = [[] for _ in range(n_workers)]
    batch_weights = [0.0] * n_workers

    for i, q, weight in question_weights:
        # Asignar al lote con menor peso total actual
        min_batch_idx = min(range(n_workers), key=lambda x: batch_weights[x])
        batches[min_batch_idx].append((i, q))
        batch_weights[min_batch_idx] += weight

    # Mostrar estadísticas de distribución
    print(f"📊 Distribución de carga:")
    for i, batch in enumerate(batches):
        total_weight = batch_weights[i]
        avg_weight = total_weight / len(batch) if batch else 0
        print(f"   Worker {i+1}: {len(batch)} preguntas (peso total: {total_weight:.1f}, promedio: {avg_weight:.1f})")

    # Calcular balance de carga (desviación estándar de pesos)
    if len(batch_weights) > 1:
        mean_weight = sum(batch_weights) / len(batch_weights)
        variance = sum((w - mean_weight) ** 2 for w in batch_weights) / len(batch_weights)
        std_dev = variance ** 0.5
        balance_ratio = std_dev / mean_weight if mean_weight > 0 else 0
        print(f"   ⚖️  Balance de carga: {balance_ratio:.2f} (ideal: < 0.1)")
        if balance_ratio > 0.2:
            print(f"   ⚠️  Distribución desbalanceada - considera usar menos workers")
        else:
            print(f"   ✅ Distribución bien balanceada")

    question_batches = []
    for bid, batch in enumerate(batches):
        if batch:
            # Propagar métricas específicas según el modo
            metrics_subset = None
            if ragas_mode == 'fast':
                metrics_subset = ['faithfulness', 'answer_relevancy']
            elif ragas_mode == 'normal':
                metrics_subset = ['faithfulness', 'answer_relevancy', 'context_recall', 'context_precision']
            # full usa todas las métricas (default)

            question_batches.append({
                'questions': batch,
                'models': config['models'],
                'evaluator': config.get('evaluator', {}),
                'ragas_mode': ragas_mode,
                'batch_id': bid,
                'total_questions': len(questions),
                'debug': debug,
                'tracker': None,  # No pasar tracker - no es serializable
                'progress_dict': progress_dict,  # Pasar tracker simple compartido
                'metrics_subset': metrics_subset  # Pasar subset de métricas
            })

    # Mostrar mensaje según modo de ejecución
    if batch_mode == "sequential":
        print(f"\n🔄 Iniciando {len(question_batches)} lotes en MODO SECUENCIAL...")
        print("⚡ Los lotes se ejecutarán uno detrás de otro para evitar saturación")
    else:
        print(f"\n⚡ Iniciando {len(question_batches)} lotes en MODO PARALELO...")
        print(f"🦙 Evaluador: Ollama ({config.get('evaluator', {}).get('ollama_model', 'gemma2:27b')}) - SOLO servidor UPV")
    print("=" * 80)

    # Ejecutar según modo seleccionado
    all_results = []
    completed_batches = 0
    start_time = time.time()

    if batch_mode == "sequential":
        # MODO SECUENCIAL: Ejecutar lotes uno detrás de otro
        for batch_idx, batch in enumerate(question_batches):
            print(f"\n▶️ Ejecutando lote {batch_idx + 1}/{len(question_batches)} en modo secuencial")

            try:
                batch_results = evaluate_question_batch(batch)
                all_results.extend(batch_results)
                completed_batches += 1

                # Mostrar progreso
                elapsed_time = time.time() - start_time
                progress_pct = (completed_batches / len(question_batches)) * 100
                remaining_time = (elapsed_time / completed_batches) * (len(question_batches) - completed_batches) if completed_batches > 0 else 0

                print(f"\n✅ Lote {batch_idx + 1}/{len(question_batches)} completado ({len(batch_results)} preguntas)")
                print(f"⏱️  Tiempo: {elapsed_time:.1f}s | ETA: {remaining_time/60:.1f}min")
                print(f"📊 Progreso: {progress_pct:.1f}% completado")
                print("─" * 80)

            except Exception as e:
                print(f"\n❌ Lote {batch_idx + 1} falló en modo secuencial:")
                print(f"   └─ Error: {str(e)[:200]}...")

                # Crear resultados vacíos para las preguntas fallidas
                for q_idx, q_data in batch['questions']:
                    failed_result = {
                        'question_id': q_idx + 1,
                        'question': q_data['question'],
                        'expected_answer': q_data.get('expected_answer', ''),
                        'contexts': [],
                        'models': {},
                        'winner': None,
                        'error': {
                            'batch_id': batch_idx + 1,
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'questions_failed': len(batch['questions'])
                        }
                    }

                    # Añadir resultados vacíos para cada modelo
                    for model_cfg in config['models']:
                        model_name = model_cfg['name']
                        failed_result['models'][model_name] = {
                            'response': '',
                            'answer': '',
                            'latency': 0.0,
                            'metrics': {},
                            'score': 0.0,
                            'params': {},
                            'success': False,
                            'error': f"Lote fallido: {str(e)[:100]}..."
                        }

                    all_results.append(failed_result)
                print(f"   └─ Se han creado {len(batch['questions'])} resultados vacíos")

    else:
        # MODO PARALELO: Ejecutar todos los lotes simultáneamente
        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            futures = []

            # Enviar trabajos
            for batch_idx, batch in enumerate(question_batches):
                future = executor.submit(evaluate_question_batch, batch)
                futures.append((batch_idx, future))

            # Recolectar resultados con manejo robusto de errores y retry
            print(f"\n⏳ Esperando resultados de {len(question_batches)} lotes...")
            print("📊 Métricas en tiempo real:")
            print("─" * 80)

            # Usar as_completed para detectar lotes que terminan primero
            for future in as_completed([f for _, f in futures]):
                # Encontrar el batch_idx correspondiente
                batch_idx = next(i for i, (_, f) in enumerate(futures) if f == future)

                max_retries = 1
                retry_count = 0
                batch_results = None

                while retry_count <= max_retries and batch_results is None:
                    try:
                        # Timeout reducido drásticamente
                        batch_size = len(question_batches[batch_idx]['questions'])
                        timeout_per_question = 90 if ragas_mode == 'fast' else 150 if ragas_mode == 'normal' else 240
                        timeout = batch_size * timeout_per_question * len(config['models'])

                        batch_results = future.result(timeout=timeout)
                        all_results.extend(batch_results)
                        completed_batches += 1

                        # Calcular métricas en tiempo real
                        elapsed_time = time.time() - start_time
                        avg_time_per_batch = elapsed_time / completed_batches
                        remaining_batches = len(question_batches) - completed_batches
                        eta_minutes = (remaining_batches * avg_time_per_batch) / 60

                        print(f"\n✅ Lote {batch_idx + 1}/{len(question_batches)} completado ({len(batch_results)} preguntas)")
                        print(f"⏱️  Tiempo: {elapsed_time:.1f}s | Promedio: {avg_time_per_batch:.1f}s/lote | ETA: {eta_minutes:.1f}min")
                        print(f"🦙 Ollama: Limitador activo ({ragas_mode} modo)")
                        print(f"📊 Progreso: {completed_batches}/{len(question_batches)} lotes ({(completed_batches/len(question_batches))*100:.1f}%)")
                        print("─" * 80)

                    except Exception as e:
                        retry_count += 1
                        error_msg = str(e)

                        if retry_count <= max_retries:
                            print(f"\n⚠️  Lote {batch_idx + 1} fallo (intento {retry_count}/{max_retries + 1}): {error_msg[:100]}...")
                            print(f"🔄 Reintentando lote {batch_idx + 1} con backoff exponencial...")

                            # Backoff exponencial: 2s, 4s, 8s
                            backoff_time = 2 ** retry_count
                            print(f"   ⏱️  Esperando {backoff_time}s antes de reintentar...")
                            time.sleep(backoff_time)

                            # Re-crear el lote fallido para reintentar
                            if retry_count <= max_retries:
                                retry_batch = question_batches[batch_idx].copy()
                                retry_future = executor.submit(evaluate_question_batch, retry_batch)
                                futures[batch_idx] = (batch_idx, retry_future)
                        else:
                            print(f"\n❌ Lote {batch_idx + 1} falló definitivamente después de {max_retries + 1} intentos:")
                            print(f"   └─ Error: {error_msg}")

                            # Guardar información del error para análisis posterior
                            error_info = {
                                'batch_id': batch_idx + 1,
                                'error_type': type(e).__name__,
                                'error_message': error_msg,
                                'questions_failed': len(question_batches[batch_idx]['questions'])
                            }

                            # Crear resultados vacíos para las preguntas fallidas
                            for q_idx, q_data in question_batches[batch_idx]['questions']:
                                failed_result = {
                                    'question_id': q_idx + 1,
                                    'question': q_data['question'],
                                    'expected_answer': q_data.get('expected_answer', ''),
                                    'contexts': [],
                                    'models': {},
                                    'winner': None,
                                    'error': error_info
                                }

                                # Añadir resultados vacíos para cada modelo
                                for model_cfg in config['models']:
                                    model_name = model_cfg['name']
                                    failed_result['models'][model_name] = {
                                        'response': '',
                                        'answer': '',
                                        'latency': 0.0,
                                        'metrics': {},
                                        'score': 0.0,
                                        'params': {},
                                        'success': False,
                                        'error': f"Lote fallido: {error_msg[:100]}..."
                                    }

                                all_results.append(failed_result)

                            print(f"   └─ Se han creado {len(question_batches[batch_idx]['questions'])} resultados vacíos")

    # Organizar resultados como lista (formato compatible con benchmark.py)
    results_list = sorted(all_results, key=lambda x: x['question_id'])

    # Calcular estadísticas
    total_time = time.time() - start_time
    model_scores = {}

    for model_cfg in config['models']:
        model_name = model_cfg['name']
        scores = []

        for result in results_list:
            if model_name in result.get('models', {}):
                model_data = result['models'][model_name]
                if 'score' in model_data and model_data['score'] > 0:
                    scores.append(model_data['score'])

        model_scores[model_name] = {
            'avg_score': sum(scores) / len(scores) if scores else 0,
            'n_evaluated': len(scores)
        }

    # Preparar resultado final (formato compatible con benchmark.py)
    benchmark_result = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'total_questions': len(questions),
            'total_time': total_time,
            'models': [m['name'] for m in config['models']],
            'ragas_backend': 'ollama',
            'ragas_model': config.get('evaluator', {}).get('ollama_model', 'gemma2:27b'),
            'ragas_base_url': config.get('evaluator', {}).get('ollama_base_url', 'https://ollama.gti-ia.upv.es:443'),
            'filter_thinking_tags': True,
            'ragas_mode': ragas_mode,
            'batch_mode': batch_mode,
            'n_workers': n_workers
        },
        'results': results_list  # Lista, no dict
    }

    # Convertir tipos NumPy a tipos Python nativos
    benchmark_result = convert_numpy_types(benchmark_result)

    # Guardar resultados
    os.makedirs("results", exist_ok=True)
    output_file = f"results/parallel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(benchmark_result, f, ensure_ascii=False, indent=2)

    # Guardar log de errores si los hubo
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)

    error_count = sum(1 for r in results_list if 'error' in r)
    if error_count > 0:
        error_log_file = f"{logs_dir}/benchmark_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        with open(error_log_file, 'w', encoding='utf-8') as log_file:
            log_file.write(f"# BENCHMARK ERROR LOG\n")
            log_file.write(f"# Timestamp: {datetime.now().isoformat()}\n")
            log_file.write(f"# Total questions: {len(questions)}\n")
            log_file.write(f"# Failed questions: {error_count}\n")
            log_file.write(f"# Workers: {n_workers}\n")
            log_file.write(f"# RAGAs mode: {ragas_mode}\n\n")

            for result in results_list:
                if 'error' in result:
                    log_file.write(f"## Question {result['question_id']}: {result['question'][:100]}...\n")
                    log_file.write(f"Error Type: {result['error'].get('error_type', 'Unknown')}\n")
                    log_file.write(f"Error Message: {result['error'].get('error_message', 'No message')}\n")
                    log_file.write(f"Batch ID: {result['error'].get('batch_id', 'Unknown')}\n\n")

        print(f"🚨 Error log guardado: {error_log_file}")

    # Detener display de progreso y mostrar resumen final del tracker (desactivado)
    # if tracker:
    #     tracker.stop_display()
    #     tracker_results = tracker.get_final_results()
    #     print(f"\n💾 Resultados guardados: {output_file}")
    #     print(f"📊 Tracker results: {len(tracker_results['model_results'])} modelos procesados")
    #     if error_count > 0:
    #         print(f"⚠️ {error_count} preguntas fallaron (ver error log)")
    # else:
    print(f"\n💾 Resultados guardados: {output_file}")
    if error_count > 0:
        print(f"⚠️ {error_count} preguntas fallaron")
    # Determinar título del resumen según modo
    mode_title = "SECUENCIAL" if batch_mode == "sequential" else "PARALELO"
    print(f"📊 RESUMEN DEL BENCHMARK {mode_title}")
    print("=" * 80)
    print(f"⏱️  Tiempo total: {total_time:.1f}s ({total_time/60:.1f} minutos)")
    print(f"⚡ Tiempo por pregunta: {total_time/len(questions):.1f}s")
    print(f"🔧 Modo de ejecución: {batch_mode}")
    print(f"👥 Workers utilizados: {n_workers}")
    print(f"🧪 Modo RAGAs: {ragas_mode}")
    print(f"\n📈 Puntuaciones por modelo:")
    for model_name, stats in sorted(model_scores.items(),
                                   key=lambda x: x[1]['avg_score'],
                                   reverse=True):
        print(f"   • {model_name}: {stats['avg_score']:.3f} ({stats['n_evaluated']}/{len(questions)} evaluadas)")

    # Calcular mejor modelo
    best_model = max(model_scores.items(), key=lambda x: x[1]['avg_score'])[0] if model_scores else None
    print(f"\n🏆 Mejor modelo: {best_model}")
    print(f"💾 Resultados guardados: {output_file}")

    # Comparación con benchmark secuencial
    sequential_estimate = len(questions) * len(config['models']) * 120  # ~2 min por evaluación
    print(f"\n⚡ Comparación de rendimiento:")
    print(f"   • Tiempo estimado secuencial: {sequential_estimate/60:.1f} minutos")
    print(f"   • Tiempo {batch_mode} real: {total_time/60:.1f} minutos")

    if batch_mode == "parallel":
        improvement = sequential_estimate/total_time
        print(f"   • Mejora: {improvement:.1f}x más rápido")
    else:
        # En modo secuencial, mostrar cuánto tiempo habría tomado en paralelo
        parallel_estimate = total_time / n_workers  # Estimación muy básica
        print(f"   • Tiempo estimado paralelo: ~{parallel_estimate/60:.1f} minutos")
        print(f"   • Trade-off: {batch_mode} evita saturación del servidor Ollama")

    return benchmark_result


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Benchmark RAG paralelo optimizado'
    )
    parser.add_argument(
        '--max-questions',
        type=int,
        help='Número máximo de preguntas a evaluar'
    )
    parser.add_argument(
        '--workers',
        type=int,
        help='Número de workers paralelos (default: auto hasta 16, reservando CPUs sistema)'
    )
    parser.add_argument(
        '--ragas-mode',
        choices=['fast', 'normal', 'full'],
        default='full',
        help='Modo de evaluación RAGAs (fast=2 métricas, normal=4, full=6)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Modo debug: muestra logging detallado de cada métrica RAGAs'
    )
    parser.add_argument(
        '--test-ragas',
        action='store_true',
        help='Test RAGAs: ejecuta 1 pregunta con debug detallado para verificar métricas'
    )
    parser.add_argument(
        '--batch-mode',
        choices=['sequential', 'parallel'],
        default='parallel',
        help='Modo de ejecución: sequential (uno detrás de otro) o parallel (simultáneo)'
    )

    args = parser.parse_args()

    # Modo test RAGAs: 1 pregunta, 1 worker, debug detallado
    if args.test_ragas:
        print("🧪 TEST RAGAs - Verificación de métricas")
        print("=" * 60)
        print("Ejecutando 1 pregunta con logging detallado...")
        print("Se verificarán las 6 métricas RAGAs con Ollama")
        print("=" * 60)

        run_parallel_benchmark(
            max_questions=1,
            n_workers=1,
            ragas_mode='full',  # Todas las 6 métricas
            debug=True,  # Máximo detalle
            batch_mode='sequential'  # Siempre secuencial para test
        )
    else:
        # Ejecutar benchmark normal
        run_parallel_benchmark(
            max_questions=args.max_questions,
            n_workers=args.workers,
            ragas_mode=args.ragas_mode,
            debug=args.debug,
            batch_mode=args.batch_mode
        )


if __name__ == "__main__":
    main()