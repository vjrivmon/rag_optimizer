from typing import Dict, Any, Optional
from rouge_score import rouge_scorer
import difflib

class ResponseEvaluator:
    """Evalúa calidad de respuestas RAG"""

    def __init__(self):
        self.rouge = rouge_scorer.RougeScorer(
            ['rouge1', 'rouge2', 'rougeL'],
            use_stemmer=False
        )

    def evaluate(
        self,
        query: str,
        response: str,
        context: str,
        expected_answer: Optional[str] = None,
        keywords: Optional[list] = None
    ) -> Dict[str, float]:
        """Evaluación completa"""

        metrics = {}

        # 1. Verificar que no esté vacía
        if not response or len(response.strip()) < 10:
            metrics['combined_score'] = 0.0
            return metrics

        # 2. Faithfulness (basado en contexto)
        metrics['faithfulness'] = self._check_faithfulness(response, context)

        # 3. Keyword coverage (si hay keywords)
        if keywords:
            metrics['keyword_coverage'] = self._check_keywords(response, keywords)

        # 4. Similitud con respuesta esperada
        if expected_answer:
            metrics.update(self._calculate_similarity(response, expected_answer))

        # 5. Score combinado
        metrics['combined_score'] = self._calculate_combined_score(metrics)

        return metrics

    def _check_faithfulness(self, response: str, context: str) -> float:
        """Verifica fidelidad al contexto (simple)"""

        # Contar palabras de la respuesta que están en el contexto
        response_words = set(response.lower().split())
        context_words = set(context.lower().split())

        if not response_words:
            return 0.0

        overlap = len(response_words & context_words)
        faithfulness = overlap / len(response_words)

        return min(faithfulness * 1.5, 1.0)  # Boost

    def _check_keywords(self, response: str, keywords: list) -> float:
        """Verifica presencia de keywords"""

        if not keywords:
            return 1.0

        response_lower = response.lower()
        found = sum(1 for kw in keywords if kw.lower() in response_lower)

        return found / len(keywords)

    def _calculate_similarity(self, response: str, expected: str) -> Dict[str, float]:
        """Similitud con respuesta esperada"""

        # ROUGE scores
        rouge_scores = self.rouge.score(expected, response)

        # Similarity ratio (simple pero efectivo)
        similarity = difflib.SequenceMatcher(None, expected.lower(), response.lower()).ratio()

        return {
            'rouge1_f1': rouge_scores['rouge1'].fmeasure,
            'rouge2_f1': rouge_scores['rouge2'].fmeasure,
            'rougeL_f1': rouge_scores['rougeL'].fmeasure,
            'similarity_ratio': similarity
        }

    def _calculate_combined_score(self, metrics: Dict[str, float]) -> float:
        """Score final ponderado"""

        weights = {
            'faithfulness': 0.3,
            'keyword_coverage': 0.2,
            'rouge1_f1': 0.2,
            'rougeL_f1': 0.2,
            'similarity_ratio': 0.1
        }

        score = 0.0
        total_weight = 0.0

        for metric, weight in weights.items():
            if metric in metrics:
                score += metrics[metric] * weight
                total_weight += weight

        return score / total_weight if total_weight > 0 else 0.0

    def is_hallucinating(self, metrics: Dict[str, float]) -> bool:
        """Detecta alucinaciones"""
        return metrics.get('faithfulness', 1.0) < 0.4
