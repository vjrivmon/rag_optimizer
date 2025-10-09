#!/usr/bin/env python3
"""
Progress Tracker centralizado para benchmark paralelo
Usa multiprocessing.Manager para compartir estado entre workers
"""

import time
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from multiprocessing import Manager
import sys


class ProgressTracker:
    """Sistema de progreso compartido entre procesos workers"""

    def __init__(self, total_questions: int, models: List[str], n_workers: int):
        """
        Inicializa el tracker de progreso

        Args:
            total_questions: Número total de preguntas
            models: Lista de nombres de modelos
            n_workers: Número de workers paralelos
        """
        self.total_questions = total_questions
        self.models = models
        self.n_workers = n_workers
        self.total_evaluations = total_questions * len(models)

        # Estado compartido (multiprocessing-safe)
        self.manager = Manager()
        self.progress = self.manager.dict()
        self.worker_progress = self.manager.dict()
        self.model_scores = self.manager.dict()
        self.start_time = self.manager.Value('d', time.time())
        self.last_update_time = self.manager.Value('d', time.time())

        # Inicializar estado
        self._init_state()

        # Thread para actualizar display
        self.display_thread = None
        self.running = self.manager.Value('b', True)

    def _init_state(self):
        """Inicializa el estado del tracker"""
        # Progreso general
        self.progress['questions_completed'] = 0
        self.progress['evaluations_completed'] = 0
        self.progress['current_worker'] = ''
        self.progress['current_question'] = ''
        self.progress['current_model'] = ''

        # Progreso por worker
        for worker_id in range(self.n_workers):
            self.worker_progress[f'worker_{worker_id}'] = self.manager.dict()
            self.worker_progress[f'worker_{worker_id}']['completed'] = 0
            self.worker_progress[f'worker_{worker_id}']['current'] = ''
            self.worker_progress[f'worker_{worker_id}']['last_activity'] = time.time()

        # Scores por modelo
        for model in self.models:
            self.model_scores[model] = self.manager.dict()
            self.model_scores[model]['scores'] = self.manager.list()
            self.model_scores[model]['total_time'] = 0.0
            self.model_scores[model]['count'] = 0

    def update_worker_status(self, worker_id: int, status: str,
                           question_id: Optional[int] = None,
                           model_name: Optional[str] = None):
        """Actualiza el estado de un worker"""
        worker_key = f'worker_{worker_id}'
        if worker_key in self.worker_progress:
            self.worker_progress[worker_key]['current'] = status
            self.worker_progress[worker_key]['last_activity'] = time.time()
            self.last_update_time.value = time.time()

            if question_id is not None:
                self.progress['current_question'] = f"Q{question_id + 1}"
            if model_name is not None:
                self.progress['current_model'] = model_name
                self.progress['current_worker'] = f"Worker {worker_id + 1}"

    def complete_evaluation(self, worker_id: int, question_id: int,
                          model_name: str, score: float, eval_time: float):
        """Registra una evaluación completada"""
        # Actualizar contadores generales
        self.progress['evaluations_completed'] += 1

        # Actualizar scores del modelo
        if model_name in self.model_scores:
            self.model_scores[model_name]['scores'].append(score)
            self.model_scores[model_name]['total_time'] += eval_time
            self.model_scores[model_name]['count'] += 1

        # Actualizar progreso del worker
        worker_key = f'worker_{worker_id}'
        if worker_key in self.worker_progress:
            self.worker_progress[worker_key]['completed'] += 1
            self.worker_progress[worker_key]['current'] = 'idle'

        # Verificar si se completó una pregunta (todos los modelos evaluados)
        completed_evals = self.progress['evaluations_completed']
        if completed_evals % len(self.models) == 0:
            self.progress['questions_completed'] = completed_evals // len(self.models)

        self.last_update_time.value = time.time()

    def start_display(self):
        """Inicia el thread de display en segundo plano"""
        self.running.value = True
        self.display_thread = threading.Thread(target=self._display_loop, daemon=True)
        self.display_thread.start()

    def stop_display(self):
        """Detiene el display y muestra resumen final"""
        self.running.value = False
        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=2)
        self._show_final_summary()

    def _display_loop(self):
        """Loop principal del display de progreso"""
        try:
            while self.running.value:
                self._refresh_display()
                time.sleep(2)  # Actualizar cada 2 segundos
        except KeyboardInterrupt:
            pass

    def _refresh_display(self):
        """Actualiza el display de progreso"""
        # Limpiar pantalla (compatible con diferentes terminales)
        print('\033[2J\033[H', end='')

        # Calcular estadísticas
        current_time = time.time()
        elapsed_time = current_time - self.start_time.value

        completed_evals = self.progress['evaluations_completed']
        completed_questions = self.progress['questions_completed']

        # Progreso
        eval_progress = completed_evals / self.total_evaluations
        question_progress = completed_questions / self.total_questions

        # Velocidad y tiempo estimado
        if elapsed_time > 0:
            evals_per_second = completed_evals / elapsed_time
            remaining_evals = self.total_evaluations - completed_evals
            if evals_per_second > 0:
                eta_seconds = remaining_evals / evals_per_second
            else:
                eta_seconds = float('inf')
        else:
            evals_per_second = 0
            eta_seconds = float('inf')

        # Display principal
        completed_evals = self.progress['evaluations_completed']
        self._print_header(eval_progress, question_progress, elapsed_time, eta_seconds, evals_per_second, completed_evals)

        # Scores parciales
        self._print_partial_scores()

        # Velocidad por modelo
        self._print_model_speed()

        # Status de recursos Ollama
        self._print_ollama_status()

        # Status de workers
        self._print_worker_status()

    def _print_header(self, eval_progress: float, question_progress: float,
                     elapsed_time: float, eta_seconds: float, evals_per_second: float, completed_evals: int):
        """Imprime el encabezado del progreso"""
        print("╔" + "═" * 118 + "╗")
        print("║" + " RAG BENCHMARK PARALELO - Progreso Global".center(118) + "║")
        print("╠" + "═" * 118 + "╣")
        print("║" + " " * 118 + "║")

        # Barra de progreso de evaluaciones
        eval_bar = self._create_progress_bar(eval_progress, 50)
        print(f"║  📊 Progreso Evaluaciones: [{eval_bar}] {completed_evals}/{self.total_evaluations} ({eval_progress*100:.1f}%)".ljust(118) + "║")

        # Barra de progreso de preguntas
        completed_questions = self.progress['questions_completed']
        question_bar = self._create_progress_bar(question_progress, 50)
        print(f"║  📝 Progreso Preguntas:   [{question_bar}] {completed_questions}/{self.total_questions} ({question_progress*100:.1f}%)".ljust(118) + "║")

        print("║" + " " * 118 + "║")

        # Tiempo y velocidad
        elapsed_str = self._format_duration(elapsed_time)
        eta_str = self._format_duration(eta_seconds) if eta_seconds != float('inf') else "∞"

        print(f"║  ⏱️  Tiempo: {elapsed_str} transcurridos | ~{eta_str} restantes".ljust(118) + "║")
        print(f"║  ⚡ Velocidad: {evals_per_second:.1f} evals/minuto (promedio)".ljust(118) + "║")

        # Actividad actual
        current_worker = self.progress.get('current_worker', 'Ninguno')
        current_question = self.progress.get('current_question', 'N/A')
        current_model = self.progress.get('current_model', 'N/A')

        print(f"║  🔬 Actividad: {current_worker} → {current_question} → {current_model}".ljust(118) + "║")
        print("║" + " " * 118 + "║")

    def _print_partial_scores(self):
        """Imprime los scores parciales por modelo"""
        print("║  🏆 Scores Parciales:".ljust(118) + "║")

        for model in self.models:
            if model in self.model_scores:
                scores_list = list(self.model_scores[model]['scores'])
                count = len(scores_list)

                if count > 0:
                    avg_score = sum(scores_list) / count
                    status = "✅ MEJOR" if avg_score >= 0.8 else "🟡 NORMAL" if avg_score >= 0.6 else "❌ BAJO"
                    print(f"║     {model:20s}: {avg_score:.3f} ({count}/{self.total_questions}) {status}".ljust(118) + "║")
                else:
                    print(f"║     {model:20s}: --- (0/{self.total_questions})".ljust(118) + "║")

        print("║" + " " * 118 + "║")

    def _print_model_speed(self):
        """Imprime la velocidad por modelo"""
        print("║  📈 Velocidad por modelo:".ljust(118) + "║")

        for model in self.models:
            if model in self.model_scores:
                count = self.model_scores[model]['count']
                total_time = self.model_scores[model]['total_time']

                if count > 0:
                    avg_time = total_time / count
                    remaining = self.total_questions - count
                    eta_model = avg_time * remaining
                    eta_str = self._format_duration(eta_model)
                    print(f"║     {model:20s}: {avg_time:.1f}s/eval → ~{eta_str} restantes".ljust(118) + "║")
                else:
                    print(f"║     {model:20s}: --- s/eval".ljust(118) + "║")

        print("║" + " " * 118 + "║")

    def _print_ollama_status(self):
        """Imprime el estado de los recursos Ollama"""
        print("║  🦙 Recursos Ollama:".ljust(118) + "║")

        # Mostrar estado simplificado sin dependencias externas para evitar deadlock
        print("║     🟢 Control local por worker (sin contención global)".ljust(118) + "║")
        print("║     📊 Cada worker gestiona sus propias llamadas a Ollama".ljust(118) + "║")

        print("║" + " " * 118 + "║")

    def _print_worker_status(self):
        """Imprime el estado de los workers"""
        print("║  👥 Estado Workers:".ljust(118) + "║")

        worker_line = "║     "
        for worker_id in range(min(self.n_workers, 8)):  # Máximo 8 workers en una línea
            worker_key = f'worker_{worker_id}'
            if worker_key in self.worker_progress:
                status = self.worker_progress[worker_key]['current']
                completed = self.worker_progress[worker_key]['completed']

                # Iconos de estado
                if status == 'idle':
                    icon = "⚪"
                elif 'evaluating' in status.lower():
                    icon = "🟡"
                elif 'generating' in status.lower():
                    icon = "🔵"
                else:
                    icon = "🟢"

                worker_line += f"{icon} W{worker_id+1}:{completed} "

        print(worker_line.ljust(118) + "║")
        print("╚" + "═" * 118 + "╝")

    def _show_final_summary(self):
        """Muestra el resumen final al completar"""
        total_time = time.time() - self.start_time.value

        print("\n" + "═" * 80)
        print("✅ BENCHMARK COMPLETADO")
        print("═" * 80)
        print(f"⏱️  Tiempo total: {self._format_duration(total_time)}")
        print(f"📊 Evaluaciones completadas: {self.progress['evaluations_completed']}/{self.total_evaluations}")
        print(f"📝 Preguntas completadas: {self.progress['questions_completed']}/{self.total_questions}")

        # Score final por modelo
        print(f"\n📈 Scores Finales:")
        best_model = None
        best_score = 0.0

        for model in self.models:
            if model in self.model_scores:
                scores_list = list(self.model_scores[model]['scores'])
                if scores_list:
                    avg_score = sum(scores_list) / len(scores_list)
                    count = len(scores_list)
                    total_time = self.model_scores[model]['total_time']
                    avg_time = total_time / count if count > 0 else 0

                    print(f"   • {model}: {avg_score:.3f} ({count} evaluaciones, {avg_time:.1f}s/eval)")

                    if avg_score > best_score:
                        best_score = avg_score
                        best_model = model

        if best_model:
            print(f"\n🏆 Mejor modelo: {best_model} ({best_score:.3f})")

        # Estadísticas de rendimiento
        total_evals = self.progress['evaluations_completed']
        if total_evals > 0:
            throughput = total_evals / total_time
            sequential_estimate = total_evals * 120  # 2 minutos por evaluación secuencial
            improvement = sequential_estimate / total_time

            print(f"\n⚡ Estadísticas de Rendimiento:")
            print(f"   • Throughput: {throughput:.2f} evals/minuto")
            print(f"   • Mejora vs secuencial: {improvement:.1f}x más rápido")
            print(f"   • Tiempo estimado secuencial: {self._format_duration(sequential_estimate)}")

        print("═" * 80)

    def _create_progress_bar(self, progress: float, width: int) -> str:
        """Crea una barra de progreso ASCII"""
        filled = int(progress * width)
        bar = "█" * filled + "░" * (width - filled)
        return bar

    def _format_duration(self, seconds: float) -> str:
        """Formatea duración en texto legible"""
        if seconds == float('inf'):
            return "∞"

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

    def get_final_results(self) -> Dict[str, Any]:
        """Retorna los resultados finales para guardar en JSON"""
        results = {
            'metadata': {
                'total_time': time.time() - self.start_time.value,
                'total_questions': self.total_questions,
                'total_evaluations': self.total_evaluations,
                'completed_evaluations': self.progress['evaluations_completed'],
                'completed_questions': self.progress['questions_completed'],
                'n_workers': self.n_workers,
                'models': self.models
            },
            'model_results': {}
        }

        for model in self.models:
            if model in self.model_scores:
                scores_list = list(self.model_scores[model]['scores'])
                if scores_list:
                    results['model_results'][model] = {
                        'scores': scores_list,
                        'average_score': sum(scores_list) / len(scores_list),
                        'count': len(scores_list),
                        'total_time': self.model_scores[model]['total_time'],
                        'average_time': self.model_scores[model]['total_time'] / len(scores_list)
                    }

        return results