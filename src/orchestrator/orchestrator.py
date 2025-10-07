import json
from typing import Dict, List, Any
from src.core.rag_engine import ConfigurableRAGEngine
from src.core.model_wrapper import LLMWrapper
from src.evaluation.evaluator import ResponseEvaluator
from src.optimization.optimizer import ParameterOptimizer

class SystemOrchestrator:
    """Orquesta todo el sistema"""

    def __init__(
        self,
        rag_engine: ConfigurableRAGEngine,
        models: List[LLMWrapper],
        evaluator: ResponseEvaluator
    ):
        self.rag = rag_engine
        self.models = models
        self.evaluator = evaluator

        # Un optimizador por modelo
        self.optimizers = {
            model.model_name: ParameterOptimizer(model.context_window)
            for model in models
        }

        # Resultados
        self.results = []

    def process_question(
        self,
        question_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Procesa una pregunta con todos los modelos"""

        question = question_data['question']
        expected = question_data.get('expected_answer')
        keywords = question_data.get('keywords', [])

        print(f"\n{'='*60}")
        print(f"📝 PREGUNTA: {question}")
        print(f"{'='*60}")

        results_per_model = {}

        for model in self.models:
            print(f"\n🤖 Modelo: {model.model_name}")

            # Obtener parámetros del optimizador
            optimizer = self.optimizers[model.model_name]

            if optimizer.should_rollback():
                print("   ⚠️  Rollback activado")
                params = optimizer.get_best_params()
            else:
                params = optimizer.suggest()

            print(f"   Params: top_k={params['top_k']}, "
                  f"temp={params['temperature']:.2f}, "
                  f"strict={params['strictness']}")

            # Actualizar RAG
            self.rag.update_params({
                'top_k': params['top_k'],
                'similarity_threshold': params['similarity_threshold']
            })

            # Recuperar contexto
            docs = self.rag.retrieve(question)
            context = self.rag.build_context(docs)

            # Construir prompt
            prompt = model.build_rag_prompt(
                question,
                context,
                params['strictness']
            )

            # Generar respuesta
            generation = model.generate(
                prompt,
                temperature=params['temperature'],
                top_p=params['top_p'],
                max_tokens=params['max_tokens']
            )

            if generation['success']:
                response = generation['response']
                print(f"   ✓ Generada ({generation['latency']:.2f}s)")
                print(f"   📄 {response[:100]}...")

                # Evaluar
                metrics = self.evaluator.evaluate(
                    question,
                    response,
                    context,
                    expected,
                    keywords
                )

                score = metrics['combined_score']
                is_halluc = self.evaluator.is_hallucinating(metrics)

                print(f"   📊 Score: {score:.3f} {'❌ ALUCINA' if is_halluc else '✅'}")

                # Reportar al optimizador
                optimizer.report(params, score)

            else:
                response = ""
                metrics = {'combined_score': 0.0}
                score = 0.0
                print(f"   ❌ Error: {generation.get('error')}")

            # Guardar resultado
            results_per_model[model.model_name] = {
                'params': params,
                'response': response,
                'metrics': metrics,
                'score': score,
                'latency': generation['latency']
            }

        # Identificar mejor modelo
        best_model = max(
            results_per_model.items(),
            key=lambda x: x[1]['score']
        )

        print(f"\n🏆 GANADOR: {best_model[0]} (score: {best_model[1]['score']:.3f})")

        result = {
            'question_id': question_data['id'],
            'question': question,
            'expected_answer': expected,
            'models': results_per_model,
            'winner': best_model[0]
        }

        self.results.append(result)
        return result

    def run_evaluation(self, dataset_path: str):
        """Ejecuta evaluación completa"""

        with open(dataset_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)

        print(f"\n🎯 Evaluando {len(questions)} preguntas...")

        for q in questions:
            self.process_question(q)

        # Guardar resultados
        with open('results/evaluation_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        print("\n✅ Evaluación completada!")
        print(f"   Resultados guardados en: results/evaluation_results.json")
