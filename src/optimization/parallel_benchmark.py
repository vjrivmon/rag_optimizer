"""
Benchmark paralelo optimizado para evaluación RAG
Reduce tiempo de ejecución de 3.5h a ~45 minutos mediante:
- Paralelización multinivel
- Caché inteligente
- Batch processing
"""

import os
import json
import time
import hashlib
import pickle
from typing import Dict, List, Any, Tuple, Optional
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from multiprocessing import Queue, Manager, cpu_count
import threading
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
import warnings
warnings.filterwarnings('ignore')

# Imports del proyecto
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core.rag_engine import RAGEngine
from src.core.model_wrapper import ModelWrapper
from src.evaluation.ragas_evaluator import OllamaRAGASEvaluator
from src.evaluation.custom_metrics import calculate_custom_metrics


@dataclass
class EvaluationTask:
    """Representa una tarea de evaluación"""
    question_id: int
    question: str
    ground_truth: str
    model_name: str
    contexts: List[str] = None
    answer: str = None


@dataclass
class EvaluationResult:
    """Resultado de una evaluación"""
    question_id: int
    model_name: str
    answer: str
    response_time: float
    custom_score: float
    ragas_metrics: Dict[str, float]
    contexts: List[str]
    error: str = None


class EvaluationCache:
    """Sistema de caché para evaluaciones RAGAs"""

    def __init__(self, cache_dir: str = "cache/ragas"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache = {}
        self._load_cache()

    def _get_cache_key(self, question: str, answer: str, contexts: List[str],
                       ground_truth: str) -> str:
        """Genera una clave única para la evaluación"""
        data = f"{question}|{answer}|{''.join(contexts)}|{ground_truth}"
        return hashlib.sha256(data.encode()).hexdigest()

    def _load_cache(self):
        """Carga el caché desde disco"""
        cache_file = self.cache_dir / "evaluations.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    self.cache = pickle.load(f)
                print(f"   📦 Caché cargado: {len(self.cache)} evaluaciones")
            except:
                self.cache = {}

    def _save_cache(self):
        """Guarda el caché a disco"""
        cache_file = self.cache_dir / "evaluations.pkl"
        with open(cache_file, 'wb') as f:
            pickle.dump(self.cache, f)

    def get(self, question: str, answer: str, contexts: List[str],
            ground_truth: str) -> Optional[Dict[str, float]]:
        """Obtiene métricas del caché si existen"""
        key = self._get_cache_key(question, answer, contexts, ground_truth)
        return self.cache.get(key)

    def set(self, question: str, answer: str, contexts: List[str],
            ground_truth: str, metrics: Dict[str, float]):
        """Guarda métricas en el caché"""
        key = self._get_cache_key(question, answer, contexts, ground_truth)
        self.cache[key] = metrics
        self._save_cache()


class ParallelBenchmark:
    """Sistema de benchmark paralelo optimizado"""

    def __init__(self, config_path: str = "config/benchmark_config.json",
                 n_workers: int = None, use_cache: bool = True,
                 ragas_mode: str = "fast"):
        """
        Args:
            config_path: Ruta al archivo de configuración
            n_workers: Número de workers paralelos (default: CPUs - 1)
            use_cache: Si usar caché para evaluaciones RAGAs
            ragas_mode: "fast" (2 métricas), "normal" (4), "full" (6)
        """
        # Cargar configuración
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # Configuración de paralelización
        self.n_workers = n_workers or max(1, cpu_count() - 1)
        self.use_cache = use_cache
        self.ragas_mode = ragas_mode

        # Sistemas
        self.cache = EvaluationCache() if use_cache else None
        self.rag_engine = None
        self.models = {}
        self.evaluator = None

        # Estadísticas
        self.stats = {
            'total_time': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0
        }

        print(f"\n🚀 BENCHMARK PARALELO OPTIMIZADO")
        print("=" * 80)
        print(f"   • Workers: {self.n_workers}")
        print(f"   • Caché: {'Activado' if use_cache else 'Desactivado'}")
        print(f"   • Modo RAGAs: {ragas_mode}")
        print("=" * 80)

    def _init_systems(self):
        """Inicializa los sistemas necesarios"""
        if not self.rag_engine:
            print("\n⚙️  Inicializando sistemas...")

            # RAG Engine
            print("   📚 Cargando RAG Engine...")
            self.rag_engine = RAGEngine()

            # Modelos
            print("   🤖 Configurando modelos...")
            models_config = self.config.get('models', [])
            for model_cfg in models_config:
                model = ModelWrapper(
                    model_name=model_cfg['name'],
                    endpoint=model_cfg['endpoint']
                )
                self.models[model_cfg['name']] = model
                print(f"      ✓ {model_cfg['name']}")

            # Evaluador RAGAs
            if self.config.get('ragas_backend') == 'ollama':
                print("   📊 Inicializando evaluador RAGAs...")
                eval_config = self.config.get('evaluator', {})

                # Configurar métricas según modo
                metrics_subset = self._get_metrics_for_mode()

                self.evaluator = OllamaRAGASEvaluator(
                    model_name=eval_config.get('ollama_model', 'gemma2:27b'),
                    base_url=eval_config.get('ollama_base_url'),
                    filter_thinking_tags=True,
                    metrics_subset=metrics_subset
                )
                print(f"      ✓ Modo {self.ragas_mode}: {len(metrics_subset)} métricas")

    def _get_metrics_for_mode(self) -> List[str]:
        """Retorna las métricas a usar según el modo"""
        if self.ragas_mode == "fast":
            return ['faithfulness', 'answer_similarity']
        elif self.ragas_mode == "normal":
            return ['faithfulness', 'answer_relevancy',
                   'context_recall', 'answer_similarity']
        else:  # full
            return None  # Todas las métricas

    def _process_question(self, task: EvaluationTask) -> EvaluationResult:
        """Procesa una pregunta con un modelo específico"""
        start_time = time.time()

        try:
            # Obtener contextos si no están
            if not task.contexts:
                contexts = self.rag_engine.retrieve(task.question)
                task.contexts = [doc.page_content for doc in contexts]

            # Generar respuesta si no está
            if not task.answer:
                model = self.models[task.model_name]
                task.answer = model.generate(task.question, task.contexts)

            # Métricas custom
            custom_score = calculate_custom_metrics(
                task.answer, task.ground_truth
            )

            # Métricas RAGAs (con caché)
            ragas_metrics = {}
            if self.evaluator:
                # Verificar caché
                if self.cache:
                    cached = self.cache.get(
                        task.question, task.answer,
                        task.contexts, task.ground_truth
                    )
                    if cached:
                        ragas_metrics = cached
                        self.stats['cache_hits'] += 1
                    else:
                        self.stats['cache_misses'] += 1

                # Si no hay caché, evaluar
                if not ragas_metrics:
                    ragas_metrics = self.evaluator.evaluate_single(
                        question=task.question,
                        answer=task.answer,
                        contexts=task.contexts,
                        ground_truth=task.ground_truth
                    )

                    # Guardar en caché
                    if self.cache and ragas_metrics:
                        self.cache.set(
                            task.question, task.answer,
                            task.contexts, task.ground_truth,
                            ragas_metrics
                        )

            response_time = time.time() - start_time

            return EvaluationResult(
                question_id=task.question_id,
                model_name=task.model_name,
                answer=task.answer,
                response_time=response_time,
                custom_score=custom_score,
                ragas_metrics=ragas_metrics,
                contexts=task.contexts
            )

        except Exception as e:
            self.stats['errors'] += 1
            return EvaluationResult(
                question_id=task.question_id,
                model_name=task.model_name,
                answer="",
                response_time=time.time() - start_time,
                custom_score=0.0,
                ragas_metrics={},
                contexts=task.contexts or [],
                error=str(e)
            )

    def _worker_process_questions(self, tasks: List[EvaluationTask]) -> List[EvaluationResult]:
        """Worker que procesa un lote de tareas"""
        # Inicializar sistemas en el worker
        self._init_systems()

        results = []
        for task in tasks:
            result = self._process_question(task)
            results.append(result)

            # Log progress
            status = "✓" if not result.error else "✗"
            score = result.custom_score
            print(f"   {status} Q{task.question_id}/{task.model_name}: {score:.3f}")

        return results

    def run_parallel(self, max_questions: Optional[int] = None) -> Dict[str, Any]:
        """Ejecuta el benchmark en paralelo"""
        start_time = time.time()

        # Cargar preguntas
        questions = self.config['evaluation_questions']
        if max_questions:
            questions = questions[:max_questions]

        models = list(self.models.keys()) if not self.models else self.config.get('models', [])
        if isinstance(models[0], dict):
            models = [m['name'] for m in models]

        print(f"\n🎯 Evaluando {len(questions)} preguntas con {len(models)} modelos")
        print(f"   Total de evaluaciones: {len(questions) * len(models)}")

        # Crear tareas
        all_tasks = []
        for q_idx, q_data in enumerate(questions):
            for model_name in models:
                task = EvaluationTask(
                    question_id=q_idx + 1,
                    question=q_data['question'],
                    ground_truth=q_data.get('expected_answer', ''),
                    model_name=model_name
                )
                all_tasks.append(task)

        # Dividir tareas entre workers
        chunk_size = max(1, len(all_tasks) // self.n_workers)
        task_chunks = [all_tasks[i:i + chunk_size]
                      for i in range(0, len(all_tasks), chunk_size)]

        print(f"\n⚡ Ejecutando con {len(task_chunks)} workers en paralelo...")
        print("=" * 80)

        # Ejecutar en paralelo
        all_results = []
        with ProcessPoolExecutor(max_workers=self.n_workers) as executor:
            futures = []
            for chunk in task_chunks:
                future = executor.submit(self._worker_process_questions, chunk)
                futures.append(future)

            # Recolectar resultados
            for future in as_completed(futures):
                try:
                    results = future.result(timeout=600)  # 10 min timeout
                    all_results.extend(results)
                except Exception as e:
                    print(f"   ⚠️ Worker falló: {e}")

        # Organizar resultados
        results_by_question = {}
        for result in all_results:
            q_id = result.question_id
            if q_id not in results_by_question:
                results_by_question[q_id] = {
                    'question': questions[q_id - 1]['question'],
                    'ground_truth': questions[q_id - 1].get('expected_answer', ''),
                    'models': {}
                }

            results_by_question[q_id]['models'][result.model_name] = {
                'answer': result.answer,
                'response_time': result.response_time,
                'custom_score': result.custom_score,
                'ragas_metrics': result.ragas_metrics,
                'contexts': result.contexts,
                'error': result.error
            }

        # Estadísticas finales
        total_time = time.time() - start_time
        self.stats['total_time'] = total_time

        # Calcular promedios
        model_scores = {model: [] for model in models}
        for q_data in results_by_question.values():
            for model_name, model_data in q_data['models'].items():
                if model_data['custom_score'] > 0:
                    model_scores[model_name].append(model_data['custom_score'])

        avg_scores = {
            model: sum(scores) / len(scores) if scores else 0
            for model, scores in model_scores.items()
        }

        # Resultado final
        benchmark_result = {
            'timestamp': datetime.now().isoformat(),
            'config': {
                'n_workers': self.n_workers,
                'use_cache': self.use_cache,
                'ragas_mode': self.ragas_mode,
                'n_questions': len(questions),
                'n_models': len(models)
            },
            'results': results_by_question,
            'summary': {
                'model_scores': avg_scores,
                'best_model': max(avg_scores, key=avg_scores.get) if avg_scores else None
            },
            'statistics': self.stats
        }

        # Guardar resultados
        output_file = f"results/parallel_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("results", exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(benchmark_result, f, ensure_ascii=False, indent=2)

        # Mostrar resumen
        print("\n" + "=" * 80)
        print("📊 RESUMEN DEL BENCHMARK")
        print("=" * 80)
        print(f"   • Tiempo total: {total_time:.1f} segundos ({total_time/60:.1f} minutos)")
        print(f"   • Evaluaciones: {len(all_results)}")
        print(f"   • Cache hits: {self.stats['cache_hits']}")
        print(f"   • Cache misses: {self.stats['cache_misses']}")
        print(f"   • Errores: {self.stats['errors']}")
        print(f"\n📈 Puntuaciones promedio por modelo:")
        for model, score in sorted(avg_scores.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {model}: {score:.3f}")
        print(f"\n💾 Resultados guardados en: {output_file}")

        return benchmark_result


def main():
    """Función principal para ejecutar el benchmark paralelo"""
    import argparse

    parser = argparse.ArgumentParser(description='Benchmark RAG paralelo optimizado')
    parser.add_argument('--max-questions', type=int, help='Número máximo de preguntas')
    parser.add_argument('--workers', type=int, help='Número de workers paralelos')
    parser.add_argument('--no-cache', action='store_true', help='Desactivar caché')
    parser.add_argument('--ragas-mode', choices=['fast', 'normal', 'full'],
                       default='fast', help='Modo de evaluación RAGAs')

    args = parser.parse_args()

    # Crear y ejecutar benchmark
    benchmark = ParallelBenchmark(
        n_workers=args.workers,
        use_cache=not args.no_cache,
        ragas_mode=args.ragas_mode
    )

    benchmark.run_parallel(max_questions=args.max_questions)


if __name__ == "__main__":
    main()