#!/usr/bin/env python3
"""
Benchmark enfocado en preguntas problemáticas específicas
Para validar rápidamente los fixes implementados
"""

import yaml
import warnings
import json
import time
from datetime import datetime
from tabulate import tabulate
from colorama import init, Fore, Style
import sys
import os

# Añadir path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.rag_engine import ConfigurableRAGEngine
from src.core.model_wrapper import LLMWrapper
from src.evaluation.ragas_evaluator import HybridEvaluator, clean_thinking_tags

# Inicializar colorama
init(autoreset=True)

# Suprimir warnings
warnings.filterwarnings('ignore')


# Preguntas problemáticas seleccionadas
TARGETED_QUESTIONS = [
    {
        "id": 5,
        "question": "¿Cuánto dura la actividad de desayunos?",
        "expected_answer": "Depende del día, de la cantidad de personas que encontramos en la calle y de la zona por la que se reparta. Normalmente solemos estimar que la actividad dura una hora y media más el posterior desayuno voluntario de los propios participantes que se puede alargar lo que ellos quieran.",
        "keywords": ["hora", "media", "depende", "desayuno"],
        "category": "desayunos",
        "benchmark_3_avg": 0.611
    },
    {
        "id": 13,
        "question": "¿Cuánto dura la actividad de coles?",
        "expected_answer": "De 15:30 a 16:30, es decir, una hora.",
        "keywords": ["15:30", "16:30", "hora"],
        "category": "coles",
        "benchmark_3_avg": 0.542
    },
    {
        "id": 25,
        "question": "¿Qué significa Para-Mira-Ayuda?",
        "expected_answer": "Son las tres palabras que guían la labor de los voluntarios de DNI. En un mundo que avanza a un ritmo frenético, es necesario detenerse (PARAR) para ser conscientes de aquellos que nos rodean, MIRAR con cariño y cercanía, y ofrecer nuestra AYUDA con generosidad y alegría.",
        "keywords": ["parar", "mirar", "ayuda", "guían", "voluntarios"],
        "category": "filosofia",
        "benchmark_3_avg": 0.532
    }
]

# NOTA: clean_thinking_tags se importa desde ragas_evaluator (versión mejorada)
# Ya no necesitamos definirla aquí

class TargetedBenchmark:
    """Benchmark enfocado en preguntas problemáticas"""

    def __init__(self):
        print("\n" + "="*80)
        print(f"{Fore.CYAN}🎯 BENCHMARK ENFOCADO - PREGUNTAS PROBLEMÁTICAS")
        print("="*80 + "\n")

        # Cargar configuración de modelos
        with open('config/models_config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        self.models_config = config['models']

        # Inicializar RAG Engine
        print(f"{Fore.YELLOW}🔧 Inicializando RAG Engine...")
        self.rag_engine = ConfigurableRAGEngine(
            vector_store_path="data/vectorstore/chroma_db",
            use_hybrid=True
        )
        print(f"{Fore.GREEN}   ✓ RAG Engine listo (hybrid retrieval activado)")

        # Mostrar parámetros actuales
        print(f"\n{Fore.YELLOW}📊 Parámetros RAG actuales:")
        for key, value in self.rag_engine.params.items():
            print(f"   - {key}: {value}")

        # Inicializar evaluador con filtro de thinking tags
        print(f"\n{Fore.YELLOW}🔍 Inicializando Evaluador RAGAs...")
        # Usar modelo evaluador MÁS PEQUEÑO para evitar timeouts
        self.evaluator = HybridEvaluator(
            use_ragas=True,
            use_ollama=True,
            ollama_model="gemma2:27b",  # Modelo más rápido (antes: llama3.3:70b)
            filter_thinking_tags=True  # ✂️ FILTRO ACTIVADO
        )

        self.results = []

    def run(self):
        """Ejecuta el benchmark enfocado"""

        print(f"\n{Fore.CYAN}📝 Evaluando {len(TARGETED_QUESTIONS)} preguntas problemáticas...")
        print(f"{Fore.CYAN}   Modelos: {len(self.models_config)}")
        print(f"{Fore.CYAN}   Total evaluaciones: {len(TARGETED_QUESTIONS) * len(self.models_config)}\n")

        for q_data in TARGETED_QUESTIONS:
            print("\n" + "="*80)
            print(f"{Fore.YELLOW}PREGUNTA {q_data['id']}: {q_data['question']}")
            print(f"{Fore.YELLOW}Benchmark #3 avg: {q_data['benchmark_3_avg']:.3f}")
            print("="*80 + "\n")

            # Retrieval (una sola vez para todos los modelos)
            print(f"{Fore.CYAN}🔍 Recuperando contextos...")
            start_retrieval = time.time()
            retrieved_docs = self.rag_engine.retrieve(q_data['question'])
            retrieval_time = time.time() - start_retrieval

            # OPTIMIZACIÓN: Usar top 10 chunks + truncar a 400 chars c/u
            # Balance entre calidad de respuesta y carga en servidor Ollama
            contexts = [doc['content'][:400] for doc in retrieved_docs[:10]]
            print(f"{Fore.GREEN}   ✓ Recuperados {len(retrieved_docs)} chunks, usando top 10 truncados ({retrieval_time:.2f}s)")

            # Mostrar preview de contextos
            print(f"\n{Fore.CYAN}📄 Preview de contextos recuperados:")
            for i, ctx in enumerate(contexts[:3], 1):
                preview = ctx[:100].replace('\n', ' ')
                print(f"   {i}. {preview}...")

            # Evaluar con cada modelo
            models_results = {}

            for model_config in self.models_config:
                model_name = model_config['name']
                print(f"\n{Fore.MAGENTA}🤖 Evaluando con {model_name}...")

                # Crear wrapper del modelo
                llm = LLMWrapper(
                    model_name=model_name,
                    api_endpoint=model_config['endpoint']  # Parámetro correcto
                )

                # Generar respuesta
                print(f"   Generando respuesta...")
                start_gen = time.time()

                # Construir prompt RAG
                prompt = llm.build_rag_prompt(
                    query=q_data['question'],
                    context=self.rag_engine.build_context(retrieved_docs[:10]),
                    strictness='medium'
                )

                # Generar con el modelo
                result = llm.generate(
                    prompt=prompt,
                    temperature=0.3,
                    max_tokens=400
                )

                response = result.get('response', '')
                gen_time = result.get('latency', time.time() - start_gen)

                # Detectar thinking tags
                has_thinking = '<think>' in response
                thinking_status = f"{Fore.RED}CON <think> tags" if has_thinking else f"{Fore.GREEN}SIN <think> tags"
                print(f"   {thinking_status}")

                # Limpiar respuesta para evaluación
                response_clean = clean_thinking_tags(response)

                # Mostrar respuesta limpia
                preview = response_clean[:150].replace('\n', ' ')
                print(f"   Respuesta (limpia): {preview}...")
                print(f"   Latencia: {gen_time:.2f}s")

                if has_thinking:
                    print(f"   {Fore.YELLOW}ℹ️  Thinking tags filtrados para evaluación{Style.RESET_ALL}")

                # Evaluar (el evaluador ya tiene filter_thinking_tags=True)
                print(f"   Evaluando con RAGAs...")
                start_eval = time.time()
                metrics = self.evaluator.evaluate(
                    question=q_data['question'],
                    answer=response,  # El evaluador filtrará los thinking tags automáticamente
                    contexts=contexts,
                    ground_truth=q_data['expected_answer'],
                    keywords=q_data.get('keywords')
                )
                eval_time = time.time() - start_eval

                # Calcular score final (manejar nan)
                import math
                score = metrics.get('combined_score', 0.0)
                if math.isnan(score) or score is None:
                    score = 0.0
                    quality = f"{Fore.RED}✗ ERROR (timeout)"
                else:
                    # Determinar calidad (thresholds ajustados para nuevo scoring)
                    if score >= 0.75:  # Bajado de 0.8 → más realista
                        quality = f"{Fore.GREEN}✓ CORRECTA"
                    elif score >= 0.5:
                        quality = f"{Fore.YELLOW}~ INCOMPLETA"
                    else:
                        quality = f"{Fore.RED}✗ INCORRECTA"

                print(f"   Score: {score:.3f} {quality}")
                print(f"   Métricas RAGAs (solo 3 optimizadas):")

                # Manejar nan en cada métrica
                def format_metric(value):
                    if value is None or (isinstance(value, float) and math.isnan(value)):
                        return "ERROR"
                    return f"{value:.3f}"

                # Solo mostrar las 3 métricas que realmente calculamos
                print(f"     - Answer Relevancy: {format_metric(metrics.get('answer_relevancy', 0))}")
                print(f"     - Context Recall: {format_metric(metrics.get('context_recall', 0))}")
                print(f"     - Answer Similarity: {format_metric(metrics.get('answer_similarity', 0))}")

                models_results[model_name] = {
                    'response': response,
                    'response_clean': response_clean,
                    'has_thinking': has_thinking,
                    'score': score,
                    'metrics': metrics,
                    'latency': gen_time
                }

            # Guardar resultado de la pregunta
            self.results.append({
                'question_id': q_data['id'],
                'question': q_data['question'],
                'expected_answer': q_data['expected_answer'],
                'category': q_data['category'],
                'benchmark_3_avg': q_data['benchmark_3_avg'],
                'contexts': contexts,
                'models': models_results
            })

        # Mostrar resumen final
        self.show_summary()

        # Guardar resultados
        self.save_results()

    def show_summary(self):
        """Muestra tabla resumen comparativa"""

        print("\n" + "="*80)
        print(f"{Fore.CYAN}📊 RESUMEN COMPARATIVO: BENCHMARK #3 vs #4 (TARGETED)")
        print("="*80 + "\n")

        # Tabla por pregunta
        table_data = []
        for result in self.results:
            q_id = result['question_id']
            question = result['question'][:40] + "..."
            b3_avg = result['benchmark_3_avg']

            # Scores de cada modelo
            scores = []
            for model_name in [m['name'] for m in self.models_config]:
                if model_name in result['models']:
                    score = result['models'][model_name]['score']
                    scores.append(score)
                else:
                    scores.append(0)

            b4_avg = sum(scores) / len(scores) if scores else 0
            improvement = b4_avg - b3_avg
            improvement_pct = (improvement / b3_avg * 100) if b3_avg > 0 else 0

            symbol = "↑" if improvement > 0 else "↓" if improvement < 0 else "="
            color = Fore.GREEN if improvement > 0 else Fore.RED if improvement < 0 else Fore.YELLOW

            row = [
                f"P{q_id}",
                question,
                f"{b3_avg:.3f}",
                f"{b4_avg:.3f}",
                f"{color}{symbol} {improvement:+.3f}{Style.RESET_ALL}",
                f"{color}{improvement_pct:+.1f}%{Style.RESET_ALL}"
            ]

            # Añadir scores individuales
            for score in scores:
                if score >= 0.8:
                    row.append(f"{Fore.GREEN}{score:.3f}{Style.RESET_ALL}")
                elif score >= 0.5:
                    row.append(f"{Fore.YELLOW}{score:.3f}{Style.RESET_ALL}")
                else:
                    row.append(f"{Fore.RED}{score:.3f}{Style.RESET_ALL}")

            table_data.append(row)

        headers = ["ID", "Pregunta", "B#3 Avg", "B#4 Avg", "Cambio", "%"]
        headers.extend([m['name'].split(':')[0] for m in self.models_config])

        print(tabulate(table_data, headers=headers, tablefmt="grid"))

        # Tabla de thinking tags
        print(f"\n{Fore.CYAN}✂️ ANÁLISIS DE THINKING TAGS:")
        print("="*80 + "\n")

        think_data = []
        for model_config in self.models_config:
            model_name = model_config['name']
            with_think = 0
            total = 0

            for result in self.results:
                if model_name in result['models']:
                    total += 1
                    if result['models'][model_name]['has_thinking']:
                        with_think += 1

            pct = (with_think / total * 100) if total > 0 else 0
            status = f"{Fore.RED}TIENE <think>" if with_think > 0 else f"{Fore.GREEN}LIMPIO"

            think_data.append([
                model_name,
                f"{with_think}/{total}",
                f"{pct:.0f}%",
                f"{status}{Style.RESET_ALL}"
            ])

        print(tabulate(think_data, headers=["Modelo", "Con <think>", "%", "Estado"], tablefmt="grid"))

        # Mejora promedio
        print(f"\n{Fore.CYAN}📈 MEJORA PROMEDIO:")
        print("="*80 + "\n")

        total_b3 = sum(r['benchmark_3_avg'] for r in self.results) / len(self.results)
        total_b4 = 0
        for result in self.results:
            scores = [result['models'][m['name']]['score'] for m in self.models_config if m['name'] in result['models']]
            total_b4 += sum(scores) / len(scores) if scores else 0
        total_b4 /= len(self.results)

        improvement = total_b4 - total_b3
        improvement_pct = (improvement / total_b3 * 100) if total_b3 > 0 else 0

        print(f"Benchmark #3 promedio: {total_b3:.3f}")
        print(f"Benchmark #4 promedio: {total_b4:.3f}")
        print(f"Mejora: {improvement:+.3f} ({improvement_pct:+.1f}%)")

        if improvement > 0:
            print(f"\n{Fore.GREEN}✅ MEJORA DETECTADA! Los fixes funcionan.{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}⚠️  Sin mejora significativa.{Style.RESET_ALL}")

    def save_results(self):
        """Guarda resultados en JSON"""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"results/benchmark_targeted_{timestamp}.json"

        output = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'type': 'targeted',
                'total_questions': len(TARGETED_QUESTIONS),
                'models': [m['name'] for m in self.models_config],
                'fixes_applied': [
                    'thinking_tags_filter',
                    'improved_chunking',
                    'optimized_parameters'
                ]
            },
            'results': self.results
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"\n{Fore.GREEN}💾 Resultados guardados: {filename}")


if __name__ == "__main__":
    benchmark = TargetedBenchmark()
    benchmark.run()
