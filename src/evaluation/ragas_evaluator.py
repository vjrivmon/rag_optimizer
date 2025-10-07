from typing import Dict, Any, Optional, List
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_correctness,
    answer_similarity
)
from ragas.llms import LangchainLLMWrapper
import warnings
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Suprimir warnings de deprecación y SSL
warnings.filterwarnings('ignore', category=DeprecationWarning)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Intentar importar ChatOllama (nuevo paquete langchain_ollama)
try:
    from langchain_ollama import ChatOllama
    OLLAMA_AVAILABLE = True
except ImportError:
    # Fallback a langchain_community si no está disponible
    try:
        from langchain_community.chat_models import ChatOllama
        OLLAMA_AVAILABLE = True
    except ImportError:
        OLLAMA_AVAILABLE = False
        ChatOllama = None

class OllamaRAGASEvaluator:
    """Evaluador RAGAs usando modelos Ollama (SIN OpenAI API key)"""

    def __init__(
        self,
        model_name: str = "llama3.3:70b",
        base_url: str = "https://ollama.gti-ia.upv.es:443"
    ):
        """
        Args:
            model_name: Nombre del modelo Ollama a usar para evaluación
            base_url: URL del servidor Ollama
        """
        if not OLLAMA_AVAILABLE:
            raise ImportError(
                "ChatOllama no está disponible. Instala langchain_ollama: "
                "pip install langchain-ollama"
            )

        # Crear LLM de Ollama sin http_client explícito
        # Dejar que Ollama maneje su propio ciclo de vida del cliente
        self.ollama_llm = ChatOllama(
            model=model_name,
            base_url=base_url,
            temperature=0.1,  # Baja temperatura para evaluación consistente
            client_kwargs={"verify": False, "timeout": 120}  # Desactivar verificación SSL
        )

        # Wrap para RAGAs
        self.evaluator_llm = LangchainLLMWrapper(self.ollama_llm)

        # Métricas completas con LLM
        self.metrics = [
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
            answer_correctness,
            answer_similarity
        ]

    def evaluate_single(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Evalúa una respuesta individual usando Ollama

        Args:
            question: Pregunta realizada
            answer: Respuesta del modelo
            contexts: Lista de contextos recuperados
            ground_truth: Respuesta esperada/correcta
        """

        # Crear dataset en formato RAGAs
        data = {
            'question': [question],
            'answer': [answer],
            'contexts': [contexts],
        }

        if ground_truth:
            data['ground_truth'] = [ground_truth]

        dataset = Dataset.from_dict(data)

        try:
            # Evaluar con RAGAs usando Ollama LLM
            result = evaluate(
                dataset,
                metrics=self.metrics,
                llm=self.evaluator_llm
            )

            # Convertir resultados a diccionario
            metrics_dict = {}
            df = result.to_pandas()

            # Extraer métricas
            for col in df.columns:
                if col not in ['question', 'answer', 'contexts', 'ground_truth']:
                    value = df[col].iloc[0]
                    try:
                        metrics_dict[col] = float(value) if value is not None else 0.0
                    except (ValueError, TypeError):
                        # Si no se puede convertir a float, ignorar la columna
                        continue

            return metrics_dict

        except Exception as e:
            print(f"   ⚠️  Error en evaluación RAGAs con Ollama: {e}")
            return {}


class RAGASEvaluator:
    """Evaluador usando RAGAs framework (con OpenAI)"""

    def __init__(self, use_openai: bool = False):
        """
        Args:
            use_openai: Si True, usa modelos OpenAI para evaluación (requiere API key)
                       Si False, usa métricas sin LLM
        """
        self.use_openai = use_openai

        # Seleccionar métricas según disponibilidad de OpenAI
        if use_openai:
            # Métricas completas (requieren LLM)
            self.metrics = [
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall,
                answer_correctness,
                answer_similarity
            ]
        else:
            # Métricas sin LLM (solo las que no requieren modelo externo)
            self.metrics = [
                answer_similarity,  # Solo usa embeddings
            ]

    def evaluate_single(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Evalúa una respuesta individual

        Args:
            question: Pregunta realizada
            answer: Respuesta del modelo
            contexts: Lista de contextos recuperados
            ground_truth: Respuesta esperada/correcta
        """

        # Sin ground_truth, no hay métricas RAGAs disponibles sin OpenAI
        if not ground_truth and not self.use_openai:
            return {}

        # Crear dataset en formato RAGAs
        data = {
            'question': [question],
            'answer': [answer],
            'contexts': [contexts],
        }

        if ground_truth:
            data['ground_truth'] = [ground_truth]

        dataset = Dataset.from_dict(data)

        try:
            # Evaluar con RAGAs
            if self.use_openai:
                result = evaluate(dataset, metrics=self.metrics)
            else:
                # Solo answer_similarity requiere ground_truth
                if not ground_truth:
                    return {}
                result = evaluate(
                    dataset,
                    metrics=[answer_similarity]
                )

            # Convertir resultados a diccionario
            # RAGAs devuelve un EvaluationResult object, no un dict
            metrics_dict = {}

            # Convertir a pandas y extraer scores
            df = result.to_pandas()

            # Iterar sobre las columnas (métricas)
            for col in df.columns:
                if col not in ['question', 'answer', 'contexts', 'ground_truth']:
                    value = df[col].iloc[0]  # Primera fila (única pregunta)
                    try:
                        metrics_dict[col] = float(value) if value is not None else 0.0
                    except (ValueError, TypeError):
                        # Si no se puede convertir a float, ignorar la columna
                        continue

            return metrics_dict

        except Exception as e:
            # Silencioso en modo interactivo sin ground_truth
            if ground_truth:
                print(f"   ⚠️  Error en evaluación RAGAs: {e}")
            return {}

    def evaluate_batch(
        self,
        questions: List[str],
        answers: List[str],
        contexts_list: List[List[str]],
        ground_truths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Evalúa un batch de respuestas

        Returns:
            Dict con métricas agregadas y por pregunta
        """

        # Crear dataset
        data = {
            'question': questions,
            'answer': answers,
            'contexts': contexts_list,
        }

        if ground_truths:
            data['ground_truth'] = ground_truths

        dataset = Dataset.from_dict(data)

        try:
            # Evaluar
            result = evaluate(dataset, metrics=self.metrics)

            return {
                'overall': dict(result),
                'per_question': [
                    {metric: result[metric][i] for metric in result.keys()
                     if metric not in ['question', 'answer', 'contexts', 'ground_truth']}
                    for i in range(len(questions))
                ]
            }

        except Exception as e:
            print(f"   ⚠️  Error en evaluación batch RAGAs: {e}")
            return {'overall': {}, 'per_question': []}


class HybridEvaluator:
    """Evaluador híbrido: métricas clásicas + RAGAs"""

    def __init__(
        self,
        use_ragas: bool = True,
        use_openai: bool = False,
        use_ollama: bool = False,
        ollama_model: str = "llama3.3:70b",
        ollama_base_url: str = "https://ollama.gti-ia.upv.es:443"
    ):
        """
        Args:
            use_ragas: Si True, incluye métricas RAGAs
            use_openai: Si True, usa métricas RAGAs con OpenAI LLM (requiere API key)
            use_ollama: Si True, usa métricas RAGAs con Ollama LLM (NO requiere API key)
            ollama_model: Modelo Ollama para evaluación (solo si use_ollama=True)
            ollama_base_url: URL servidor Ollama (solo si use_ollama=True)
        """
        self.use_ragas = use_ragas

        if use_ragas:
            if use_ollama:
                # Usar Ollama para RAGAs (NO requiere OpenAI API key)
                print(f"   🦙 Usando Ollama ({ollama_model}) para métricas RAGAs")
                self.ragas_evaluator = OllamaRAGASEvaluator(
                    model_name=ollama_model,
                    base_url=ollama_base_url
                )
            else:
                # Usar evaluador tradicional (OpenAI o sin LLM)
                self.ragas_evaluator = RAGASEvaluator(use_openai=use_openai)
        else:
            self.ragas_evaluator = None

    def evaluate(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None,
        keywords: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Evaluación completa: métricas clásicas + RAGAs

        Returns:
            Dict con todas las métricas
        """

        metrics = {}

        # 1. Métricas clásicas básicas
        if not answer or len(answer.strip()) < 10:
            metrics['response_length'] = 0.0
            metrics['has_response'] = 0.0
        else:
            metrics['response_length'] = len(answer)
            metrics['has_response'] = 1.0

        # 2. Keyword coverage
        if keywords:
            answer_lower = answer.lower()
            found = sum(1 for kw in keywords if kw.lower() in answer_lower)
            metrics['keyword_coverage'] = found / len(keywords) if keywords else 0.0

        # 3. Context overlap (faithfulness simple)
        context_text = ' '.join(contexts) if contexts else ''
        if context_text and answer:
            answer_words = set(answer.lower().split())
            context_words = set(context_text.lower().split())
            if answer_words:  # Evitar división por cero
                overlap = len(answer_words & context_words)
                metrics['context_overlap'] = overlap / len(answer_words)
            else:
                metrics['context_overlap'] = 0.0
        else:
            # Si no hay contexto, context_overlap es 0
            metrics['context_overlap'] = 0.0

        # 4. RAGAs metrics (solo si hay contexto y ground_truth o OpenAI)
        if self.use_ragas and self.ragas_evaluator and answer and contexts:
            ragas_metrics = self.ragas_evaluator.evaluate_single(
                question=question,
                answer=answer,
                contexts=contexts,
                ground_truth=ground_truth
            )
            metrics.update(ragas_metrics)

        # 5. Score combinado
        metrics['combined_score'] = self._calculate_combined_score(metrics)

        return metrics

    def _calculate_combined_score(self, metrics: Dict[str, float]) -> float:
        """Calcula score combinado de todas las métricas disponibles"""

        # Pesos para diferentes métricas
        weights = {
            'has_response': 0.1,
            'keyword_coverage': 0.15,
            'context_overlap': 0.2,
            'answer_similarity': 0.3,  # RAGAs
            'faithfulness': 0.25,       # RAGAs (si disponible)
        }

        score = 0.0
        total_weight = 0.0

        for metric, weight in weights.items():
            if metric in metrics and metrics[metric] is not None:
                score += metrics[metric] * weight
                total_weight += weight

        return score / total_weight if total_weight > 0 else 0.0

    def is_hallucinating(self, metrics: Dict[str, float]) -> bool:
        """Detecta alucinaciones basado en métricas"""

        # Usar faithfulness de RAGAs si está disponible
        if 'faithfulness' in metrics:
            return metrics['faithfulness'] < 0.4

        # Fallback a context_overlap
        if 'context_overlap' in metrics:
            return metrics['context_overlap'] < 0.3

        return False
