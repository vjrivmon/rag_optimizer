#!/usr/bin/env python3
"""
Benchmark completo del sistema RAG con evaluación RAGAs LOCAL (Ollama)
ALTERNATIVA a benchmark.py que usa OpenAI

Diferencias:
- Usa Ollama local (llama3.1:8b) para métricas RAGAs
- Sin costos de API
- Potencialmente más rápido (sin rate limits de OpenAI)
- Solo 3 métricas RAGAs (answer_relevancy, context_recall, answer_similarity)
"""

import yaml
import warnings
import json
import time
import math
import numpy as np
from datetime import datetime
from tabulate import tabulate
from colorama import init, Fore, Style
from src.core.rag_engine import ConfigurableRAGEngine
from src.core.model_wrapper import LLMWrapper
from src.evaluation.ragas_evaluator import HybridEvaluator
from src.optimization.optimizer import ParameterOptimizer

# Inicializar colorama
init(autoreset=True)

# Suprimir warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')
warnings.filterwarnings('ignore', category=DeprecationWarning)


def convert_numpy_types(obj):
    """
    Convierte recursivamente tipos NumPy a tipos Python nativos para serialización JSON
    """
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


class BenchmarkRunner:
    """Ejecuta benchmark completo y genera tabla comparativa"""

    def __init__(self):
        self.results = []
        self.start_time = None
        self.end_time = None

    def setup(self):
        """Configura el sistema"""
        print(f"{Fore.CYAN}🚀 BENCHMARK RAG AUTO-OPTIMIZER (Ollama Local){Style.RESET_ALL}")
        print("="*80)

        # Cargar configuración
        print(f"\n{Fore.GREEN}⚙️  Cargando configuración...{Style.RESET_ALL}")
        with open('config/models_config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # RAG Engine
        print(f"{Fore.GREEN}📚 Cargando RAG Engine...{Style.RESET_ALL}")
        self.rag = ConfigurableRAGEngine("data/vectorstore/chroma_db")

        # Modelos
        print(f"{Fore.GREEN}🤖 Configurando modelos...{Style.RESET_ALL}")
        self.models = []
        for model_config in config['models']:
            model = LLMWrapper(
                model_name=model_config['name'],
                api_endpoint=model_config['endpoint'],
                context_window=model_config['context_window']
            )
            self.models.append(model)
            print(f"   ✓ {model_config['name']}")

        # Evaluador - USANDO OLLAMA LOCAL
        print(f"{Fore.GREEN}📊 Inicializando evaluador...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}   ⚠️  Modo: RAGAs con Ollama LOCAL (llama3.1:8b){Style.RESET_ALL}")
        print(f"{Fore.YELLOW}   ⚠️  Esto NO requiere OpenAI API key{Style.RESET_ALL}")

        self.evaluator = HybridEvaluator(
            use_ragas=True,
            use_openai=False,           # ❌ NO usar OpenAI
            use_ollama=True,            # ✅ Usar Ollama local
            ollama_model="llama3.1:8b", # Modelo local (ya lo tienes instalado)
            ollama_base_url="http://localhost:11434",  # Ollama local
            filter_thinking_tags=True   # ✂️ Filtrar <think> tags
        )

        # Optimizadores (con detección de modelos thinking)
        self.optimizers = {
            model.model_name: ParameterOptimizer(
                context_window=model.context_window,
                model_name=model.model_name
            )
            for model in self.models
        }

        print(f"\n{Fore.GREEN}✅ Sistema configurado{Style.RESET_ALL}\n")

    def run_benchmark(self, dataset_path: str, max_questions: int = None):
        """Ejecuta benchmark completo"""

        # Cargar dataset
        with open(dataset_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)

        if max_questions:
            questions = questions[:max_questions]

        print(f"🎯 Evaluando {len(questions)} preguntas...\n")
        print("="*80)

        self.start_time = time.time()

        for idx, q_data in enumerate(questions, 1):
            print(f"\n{Fore.CYAN}[{idx}/{len(questions)}] {q_data['question']}{Style.RESET_ALL}")
            print("-"*80)

            result = self.process_question(q_data)
            self.results.append(result)

        self.end_time = time.time()

    def process_question(self, question_data):
        """Procesa una pregunta con todos los modelos"""

        question = question_data['question']
        expected = question_data.get('expected_answer')
        keywords = question_data.get('keywords', [])

        # Recuperar contexto
        docs = self.rag.retrieve(question)

        # OPTIMIZACIÓN: Limitar a top 5 chunks truncados para evitar timeouts RAGAs
        # Reduce carga en servidor Ollama para evaluación
        contexts = [doc['content'][:400] for doc in docs[:5]]
        context_text = self.rag.build_context(docs[:5])

        print(f"   📚 Contexto: {len(docs)} documentos recuperados, usando top 5 truncados")

        # Resultados por modelo
        model_results = {}

        for model in self.models:
            print(f"   🤖 {model.model_name}...", end=' ', flush=True)

            # Obtener parámetros
            optimizer = self.optimizers[model.model_name]
            if optimizer.should_rollback():
                params = optimizer.get_best_params()
            else:
                params = optimizer.suggest()

            # Actualizar RAG
            self.rag.update_params({
                'top_k': params['top_k'],
                'similarity_threshold': params['similarity_threshold']
            })

            # Generar prompt
            prompt = model.build_rag_prompt(question, context_text, params['strictness'])

            # Generar respuesta
            generation = model.generate(
                prompt,
                temperature=params['temperature'],
                top_p=params['top_p'],
                max_tokens=params['max_tokens']
            )

            if generation['success']:
                response = generation['response']
                latency = generation['latency']

                # Evaluar
                try:
                    metrics = self.evaluator.evaluate(
                        question=question,
                        answer=response,
                        contexts=contexts,
                        ground_truth=expected,
                        keywords=keywords
                    )

                    score = metrics['combined_score']

                    # Validar score antes de reportar al optimizador
                    # Si score es NaN (error en evaluación), usar 0.0 por defecto
                    if score is None or math.isnan(score):
                        print(f"{Fore.YELLOW}⚠️  {latency:.1f}s (score: nan - Error en evaluación RAGAs){Style.RESET_ALL}")
                        score = 0.0  # Score por defecto para evitar crash del optimizador
                        # NO reportar al optimizador para evitar contaminar el modelo Bayesiano
                    else:
                        # Reportar al optimizador solo si el score es válido
                        optimizer.report(params, score)
                        print(f"{Fore.GREEN}✓ {latency:.1f}s (score: {score:.3f}){Style.RESET_ALL}")

                except Exception as e:
                    # Si hay error en evaluación, usar métricas vacías
                    print(f"{Fore.YELLOW}⚠️  {latency:.1f}s (Error en evaluación: {str(e)[:50]}){Style.RESET_ALL}")
                    metrics = {}
                    score = 0.0

                model_results[model.model_name] = {
                    'response': response,
                    'latency': latency,
                    'metrics': metrics,
                    'score': score,
                    'params': params,
                    'success': True
                }

            else:
                print(f"{Fore.RED}✗ Error{Style.RESET_ALL}")
                model_results[model.model_name] = {
                    'response': '',
                    'latency': generation['latency'],
                    'metrics': {},
                    'score': 0.0,
                    'params': params,
                    'success': False,
                    'error': generation.get('error')
                }

        # Identificar ganador
        winner = max(model_results.items(), key=lambda x: x[1]['score'])

        return {
            'question_id': question_data.get('id', 0),
            'question': question,
            'expected_answer': expected,
            'contexts': contexts,
            'models': model_results,
            'winner': winner[0]
        }

    def generate_summary_table(self):
        """Genera tabla resumen de resultados"""

        print(f"\n\n{Fore.CYAN}{'='*100}")
        print(f"{Fore.CYAN}TABLA RESUMEN DE RESULTADOS".center(100))
        print(f"{Fore.CYAN}{'='*100}{Style.RESET_ALL}\n")

        # Calcular estadísticas por modelo
        model_stats = {}
        for model in self.models:
            model_name = model.model_name
            scores = []
            latencies = []
            wins = 0

            for result in self.results:
                if model_name in result['models']:
                    model_data = result['models'][model_name]
                    if model_data['success']:
                        scores.append(model_data['score'])
                        latencies.append(model_data['latency'])

                if result['winner'] == model_name:
                    wins += 1

            model_stats[model_name] = {
                'avg_score': sum(scores) / len(scores) if scores else 0,
                'max_score': max(scores) if scores else 0,
                'min_score': min(scores) if scores else 0,
                'avg_latency': sum(latencies) / len(latencies) if latencies else 0,
                'total_time': sum(latencies),
                'wins': wins,
                'success_rate': len(scores) / len(self.results) if self.results else 0
            }

        # Tabla de estadísticas
        table_data = []
        for model_name, stats in model_stats.items():
            table_data.append([
                model_name,
                f"{stats['avg_score']:.3f}",
                f"{stats['max_score']:.3f}",
                f"{stats['avg_latency']:.1f}s",
                f"{stats['total_time']:.0f}s",
                stats['wins'],
                f"{stats['success_rate']*100:.0f}%"
            ])

        # Ordenar por score promedio
        table_data.sort(key=lambda x: float(x[1]), reverse=True)

        print(tabulate(
            table_data,
            headers=['Modelo', 'Score Avg', 'Score Max', 'Latency Avg', 'Total Time', 'Wins', 'Success%'],
            tablefmt='grid'
        ))

        return model_stats

    def generate_detailed_comparison(self, max_questions: int = 5):
        """Genera tabla detallada de comparación por pregunta"""

        print(f"\n\n{Fore.CYAN}{'='*120}")
        print(f"{Fore.CYAN}COMPARACIÓN DETALLADA (Primeras {max_questions} preguntas)".center(120))
        print(f"{Fore.CYAN}{'='*120}{Style.RESET_ALL}\n")

        for idx, result in enumerate(self.results[:max_questions], 1):
            print(f"\n{Fore.YELLOW}[Q{idx}] {result['question']}{Style.RESET_ALL}")
            if result['expected_answer']:
                print(f"{Fore.GREEN}Expected: {result['expected_answer'][:100]}...{Style.RESET_ALL}\n")

            # Tabla de respuestas
            table_data = []
            for model_name, model_data in result['models'].items():
                response_preview = model_data['response'][:80] + '...' if len(model_data['response']) > 80 else model_data['response']
                winner_mark = '🏆' if model_name == result['winner'] else ''

                table_data.append([
                    winner_mark + model_name,
                    f"{model_data['latency']:.1f}s",
                    f"{model_data['score']:.3f}",
                    response_preview
                ])

            print(tabulate(
                table_data,
                headers=['Modelo', 'Tiempo', 'Score', 'Respuesta'],
                tablefmt='grid'
            ))

    def save_results(self):
        """Guarda resultados en JSON"""

        output = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'total_questions': len(self.results),
                'total_time': self.end_time - self.start_time if self.end_time and self.start_time else 0,
                'models': [m.model_name for m in self.models],
                'evaluator': 'ollama_local_llama3.1:8b'  # Indicar que usó Ollama local
            },
            'results': self.results
        }

        # Convertir tipos NumPy a tipos Python nativos
        output = convert_numpy_types(output)

        filename = f"results/benchmark_local_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n{Fore.GREEN}💾 Resultados guardados en: {filename}{Style.RESET_ALL}")

        return filename


def main():
    """Función principal"""

    import argparse

    parser = argparse.ArgumentParser(description='Ejecuta benchmark del sistema RAG con Ollama local')
    parser.add_argument('--max-questions', type=int, default=None,
                       help='Máximo número de preguntas a evaluar')
    parser.add_argument('--detailed', action='store_true',
                       help='Mostrar comparación detallada')

    args = parser.parse_args()

    try:
        # Crear y ejecutar benchmark
        runner = BenchmarkRunner()
        runner.setup()
        runner.run_benchmark('data/evaluation_dataset.json', max_questions=args.max_questions)

        # Generar resumen
        runner.generate_summary_table()

        # Comparación detallada
        if args.detailed:
            runner.generate_detailed_comparison(max_questions=5)

        # Guardar resultados
        runner.save_results()

        print(f"\n{Fore.GREEN}{'='*80}")
        print(f"{Fore.GREEN}✅ BENCHMARK COMPLETADO{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*80}{Style.RESET_ALL}\n")

    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}⚠️  Benchmark interrumpido por el usuario{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
