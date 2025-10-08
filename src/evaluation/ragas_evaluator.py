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
from ragas.run_config import RunConfig
from langchain.embeddings import HuggingFaceEmbeddings
import warnings
import os
import re
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Suprimir warnings de deprecación y SSL
warnings.filterwarnings('ignore', category=DeprecationWarning)
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# FIX: Event loop cerrado en evaluaciones múltiples
# nest_asyncio permite reusar el event loop sin cerrarlo
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    # Si no está instalado, continuar sin él (puede causar errores en evals múltiples)
    pass


def clean_thinking_tags(text: str) -> str:
    """
    Elimina tags <think>...</think> de la respuesta para evaluación limpia.

    Maneja 3 casos:
    1. Tags completos: <think>texto</think> → elimina todo el tag
    2. Tags sin cerrar: <think>texto... → elimina desde <think> hasta el final
    3. Sin tags: devuelve texto original

    Args:
        text: Texto con posibles thinking tags

    Returns:
        Texto sin thinking tags, o texto original si resultado vacío
    """
    if not text:
        return text

    original_text = text
    text_lower = text.lower()

    if '<think>' not in text_lower:
        return text

    # ESTRATEGIA: Procesar desde el principio, eliminando tag por tag
    # Usamos find() en lowercase pero slicing en el texto original
    # Esto evita regex complejo y catastrophic backtracking

    result = []
    pos = 0

    while True:
        # Buscar próximo <think> desde la posición actual
        think_start = text_lower.find('<think>', pos)

        if think_start == -1:
            # No hay más tags, agregar el resto del texto
            result.append(text[pos:])
            break

        # Agregar texto ANTES del <think>
        result.append(text[pos:think_start])

        # Buscar si hay cierre </think>
        think_end = text_lower.find('</think>', think_start)

        if think_end == -1:
            # Tag sin cerrar: ignorar todo desde <think> hasta el final
            break
        else:
            # Tag completo: saltar hasta después del </think>
            pos = think_end + 8

    cleaned = ''.join(result).strip()

    # Si quedó vacío, devolver original
    return cleaned if cleaned else original_text

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
        model_name: str = "gemma2:27b",
        base_url: str = "https://ollama.gti-ia.upv.es:443",
        filter_thinking_tags: bool = True
    ):
        """
        Args:
            model_name: Nombre del modelo Ollama a usar para evaluación
            base_url: URL del servidor Ollama
            filter_thinking_tags: Si True, elimina tags <think>...</think> antes de evaluar
        """
        self.filter_thinking_tags = filter_thinking_tags
        if not OLLAMA_AVAILABLE:
            raise ImportError(
                "ChatOllama no está disponible. Instala langchain_ollama: "
                "pip install langchain-ollama"
            )

        # Crear LLM de Ollama sin http_client explícito
        # Dejar que Ollama maneje su propio ciclo de vida del cliente
        # Timeout adaptativo: local (120s) vs remoto (600s)
        is_local = "localhost" in base_url or "127.0.0.1" in base_url
        timeout = 120 if is_local else 600

        self.ollama_llm = ChatOllama(
            model=model_name,
            base_url=base_url,
            temperature=0.1,  # Baja temperatura para evaluación consistente
            client_kwargs={"verify": False, "timeout": timeout}
        )

        # Wrap para RAGAs
        self.evaluator_llm = LangchainLLMWrapper(self.ollama_llm)

        # RunConfig con timeout extendido para context_precision
        # context_precision es la más costosa (N llamadas LLM, N=num_chunks)
        # Test mostró que 3 de 4 modelos necesitan 78-105s → aumentamos a 180s (3 min)
        self.run_config = RunConfig(
            timeout=180,        # 3 minutos por métrica (vs 120s que era insuficiente)
            max_retries=2,
            max_wait=240
        )

        # Embeddings locales (sin OpenAI API key)
        # Mismo modelo que usa el proyecto en ChromaDB
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        # 6 métricas RAGAs completas (con timeout configurado)
        self.metrics = [
            faithfulness,          # Anti-alucinaciones
            answer_relevancy,      # Relevancia de la respuesta
            context_precision,     # Ranking de chunks (costosa, necesita timeout 120s)
            context_recall,        # Calidad del retrieval (MUY IMPORTANTE)
            answer_correctness,    # Precisión vs ground truth
            answer_similarity      # Similitud semántica
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
            answer: Respuesta del modelo (ya debe estar limpia, sin thinking tags)
            contexts: Lista de contextos recuperados
            ground_truth: Respuesta esperada/correcta
        """

        # FALLBACK: Si aún quedan thinking tags (respuestas truncadas), limpiar aquí
        # Normalmente ya vienen limpias desde model_wrapper.py
        if self.filter_thinking_tags and '<think>' in answer.lower():
            answer = clean_thinking_tags(answer)

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
            # Evaluar con RAGAs usando Ollama LLM + embeddings locales + timeout configurado
            result = evaluate(
                dataset,
                metrics=self.metrics,
                llm=self.evaluator_llm,
                embeddings=self.embeddings,      # Embeddings locales (sin OpenAI)
                run_config=self.run_config       # Timeout 120s para context_precision
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

    def __init__(
        self,
        use_openai: bool = False,
        filter_thinking_tags: bool = True,
        metrics_subset: Optional[List[str]] = None
    ):
        """
        Args:
            use_openai: Si True, usa modelos OpenAI para evaluación (requiere API key)
                       Si False, usa métricas sin LLM
            filter_thinking_tags: Si True, elimina tags <think>...</think> antes de evaluar
            metrics_subset: Lista de nombres de métricas a usar (None = todas)
                          Opciones: 'faithfulness', 'answer_relevancy', 'context_precision',
                                   'context_recall', 'answer_correctness', 'answer_similarity'
        """
        self.use_openai = use_openai
        self.filter_thinking_tags = filter_thinking_tags

        # Mapeo de nombres a objetos de métricas
        all_metrics_map = {
            'faithfulness': faithfulness,
            'answer_relevancy': answer_relevancy,
            'context_precision': context_precision,
            'context_recall': context_recall,
            'answer_correctness': answer_correctness,
            'answer_similarity': answer_similarity
        }

        # Seleccionar métricas según disponibilidad de OpenAI y subset
        if use_openai:
            if metrics_subset:
                # Usar solo las métricas especificadas
                self.metrics = [all_metrics_map[m] for m in metrics_subset if m in all_metrics_map]
            else:
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
            answer: Respuesta del modelo (ya debe estar limpia, sin thinking tags)
            contexts: Lista de contextos recuperados
            ground_truth: Respuesta esperada/correcta
        """

        # FALLBACK: Si aún quedan thinking tags (respuestas truncadas), limpiar aquí
        # Normalmente ya vienen limpias desde model_wrapper.py
        if self.filter_thinking_tags and '<think>' in answer.lower():
            answer = clean_thinking_tags(answer)

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
        use_dual_backend: bool = False,  # NUEVO: Usar ambos backends
        ollama_model: str = "llama3.3:70b",
        ollama_base_url: str = "https://ollama.gti-ia.upv.es:443",
        filter_thinking_tags: bool = True
    ):
        """
        Args:
            use_ragas: Si True, incluye métricas RAGAs
            use_openai: Si True, usa métricas RAGAs con OpenAI LLM (requiere API key)
            use_ollama: Si True, usa métricas RAGAs con Ollama LLM (NO requiere API key)
            use_dual_backend: Si True, usa AMBOS (Ollama + OpenAI) para maximizar métricas sin saturar servidor
            ollama_model: Modelo Ollama para evaluación (solo si use_ollama=True)
            ollama_base_url: URL servidor Ollama (solo si use_ollama=True)
            filter_thinking_tags: Si True, elimina <think>...</think> antes de evaluar
        """
        self.use_ragas = use_ragas
        self.use_dual_backend = use_dual_backend

        if use_ragas:
            if use_dual_backend:
                # DUAL BACKEND: Ollama (3 métricas rápidas) + OpenAI (3 métricas complejas)
                print(f"   🔀 Backend DUAL: Ollama + OpenAI (6 métricas completas)")
                print(f"      🦙 Ollama ({ollama_model}): answer_relevancy, context_recall, answer_similarity")
                print(f"      🤖 OpenAI (gpt-4o-mini): faithfulness, context_precision, answer_correctness")
                print(f"   ✂️  Filtro de thinking tags: {'ACTIVADO' if filter_thinking_tags else 'DESACTIVADO'}")

                # Evaluador Ollama (métricas rápidas)
                self.ollama_evaluator = OllamaRAGASEvaluator(
                    model_name=ollama_model,
                    base_url=ollama_base_url,
                    filter_thinking_tags=filter_thinking_tags
                )

                # Evaluador OpenAI (solo métricas complejas que no saturan Ollama)
                self.openai_evaluator = RAGASEvaluator(
                    use_openai=True,
                    filter_thinking_tags=filter_thinking_tags,
                    metrics_subset=['faithfulness', 'context_precision', 'answer_correctness']
                )

                self.ragas_evaluator = None  # No se usa el evaluador único

            elif use_ollama:
                # Solo Ollama para RAGAs (NO requiere OpenAI API key)
                print(f"   🦙 Usando Ollama ({ollama_model}) para métricas RAGAs")
                print(f"   ✂️  Filtro de thinking tags: {'ACTIVADO' if filter_thinking_tags else 'DESACTIVADO'}")
                self.ragas_evaluator = OllamaRAGASEvaluator(
                    model_name=ollama_model,
                    base_url=ollama_base_url,
                    filter_thinking_tags=filter_thinking_tags
                )
                self.ollama_evaluator = None
                self.openai_evaluator = None
            else:
                # Usar evaluador tradicional (OpenAI o sin LLM)
                self.ragas_evaluator = RAGASEvaluator(
                    use_openai=use_openai,
                    filter_thinking_tags=filter_thinking_tags
                )
                self.ollama_evaluator = None
                self.openai_evaluator = None
        else:
            self.ragas_evaluator = None
            self.ollama_evaluator = None
            self.openai_evaluator = None

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
        if self.use_ragas and answer and contexts:
            if self.use_dual_backend:
                # MODO DUAL: Combinar métricas de Ollama + OpenAI
                # Ollama: 3 métricas rápidas (answer_relevancy, context_recall, answer_similarity)
                ollama_metrics = self.ollama_evaluator.evaluate_single(
                    question=question,
                    answer=answer,
                    contexts=contexts,
                    ground_truth=ground_truth
                )

                # OpenAI: 3 métricas complejas (faithfulness, context_precision, answer_correctness)
                # Estas métricas no saturan el servidor Ollama
                openai_metrics = self.openai_evaluator.evaluate_single(
                    question=question,
                    answer=answer,
                    contexts=contexts,
                    ground_truth=ground_truth
                )

                # Combinar ambas
                metrics.update(ollama_metrics)
                metrics.update(openai_metrics)

            elif self.ragas_evaluator:
                # MODO ÚNICO: Solo un backend
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

        # Pesos actualizados para las 6 métricas RAGAs completas + métricas clásicas
        weights = {
            # Métricas clásicas (peso reducido: 15% total)
            'has_response': 0.03,
            'keyword_coverage': 0.05,
            'context_overlap': 0.07,
            # Métricas RAGAs (peso alto: 85% total)
            'faithfulness': 0.15,          # Anti-alucinaciones
            'answer_relevancy': 0.20,      # Relevancia de la respuesta
            'context_precision': 0.10,     # Ranking de chunks (costosa pero útil)
            'context_recall': 0.25,        # Calidad del retrieval (LA MÁS IMPORTANTE)
            'answer_correctness': 0.10,    # Precisión vs ground truth
            'answer_similarity': 0.05,     # Similitud semántica
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
