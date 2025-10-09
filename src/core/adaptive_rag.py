#!/usr/bin/env python3
"""
Sistema de RAG Adaptativo con selección dinámica de chunks
Ajusta automáticamente el número de chunks según el tipo de pregunta
"""

import re
from typing import List, Dict, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class QuestionType:
    """Tipos de preguntas y sus configuraciones"""
    SIMPLE = "simple"      # ¿Dónde?, ¿Cuándo?, ¿Quién?
    COMPLEX = "complex"    # ¿Qué se hace?, ¿Cómo funciona?
    CONCEPTUAL = "conceptual"  # ¿Qué significa?, ¿Por qué?


class QuestionClassifier:
    """Clasificador simple de preguntas basado en patrones"""

    def __init__(self):
        # Patrones para identificar tipos de preguntas
        self.simple_patterns = [
            r"^¿?dónde\s",
            r"^¿?cuándo\s",
            r"^¿?quién\s",
            r"^¿?a qué hora\s",
            r"^¿?cuántos?\s",
            r"^¿?cada cuánto\s"
        ]

        self.conceptual_patterns = [
            r"¿qué significa",
            r"¿por qué",
            r"¿cuál es el objetivo",
            r"¿qué es\s",
            r"explica(me)?",
            r"define"
        ]

        self.complex_patterns = [
            r"¿qué se hace",
            r"¿cómo se",
            r"¿cómo funciona",
            r"describe",
            r"proceso de",
            r"pasos para"
        ]

    def classify(self, question: str) -> str:
        """
        Clasifica una pregunta según su tipo

        Args:
            question: Pregunta a clasificar

        Returns:
            Tipo de pregunta (simple, complex, conceptual)
        """
        question_lower = question.lower().strip()

        # Verificar patrones simples
        for pattern in self.simple_patterns:
            if re.search(pattern, question_lower):
                return QuestionType.SIMPLE

        # Verificar patrones conceptuales
        for pattern in self.conceptual_patterns:
            if re.search(pattern, question_lower):
                return QuestionType.CONCEPTUAL

        # Verificar patrones complejos
        for pattern in self.complex_patterns:
            if re.search(pattern, question_lower):
                return QuestionType.COMPLEX

        # Por defecto, considerar como compleja
        return QuestionType.COMPLEX


class ChunkSelector:
    """Selector dinámico de chunks basado en relevancia"""

    def __init__(self):
        self.configs = {
            QuestionType.SIMPLE: {
                'initial_k': 10,
                'min_chunks': 3,
                'max_chunks': 5,
                'confidence_threshold': 0.75,
                'char_limit': 300
            },
            QuestionType.COMPLEX: {
                'initial_k': 12,
                'min_chunks': 5,
                'max_chunks': 7,
                'confidence_threshold': 0.65,
                'char_limit': 400
            },
            QuestionType.CONCEPTUAL: {
                'initial_k': 15,
                'min_chunks': 6,
                'max_chunks': 8,
                'confidence_threshold': 0.60,
                'char_limit': 400
            }
        }

    def calculate_relevance_score(self, query: str, chunk: Dict) -> float:
        """
        Calcula score de relevancia para un chunk

        Args:
            query: Pregunta original
            chunk: Chunk con content y metadata

        Returns:
            Score de relevancia [0, 1]
        """
        content = chunk.get('content', '').lower()
        query_lower = query.lower()

        # Score base del vector store
        base_score = chunk.get('score', 0.5)

        # Bonus por palabras clave exactas
        query_words = set(query_lower.split())
        content_words = set(content.split())
        keyword_overlap = len(query_words & content_words) / max(len(query_words), 1)

        # Bonus por tipo de chunk (FAQ es más relevante para preguntas simples)
        metadata = chunk.get('metadata', {})
        type_bonus = 0.0
        if metadata.get('type') == 'faq':
            type_bonus = 0.2

        # Score combinado
        final_score = (base_score * 0.6) + (keyword_overlap * 0.3) + (type_bonus * 0.1)

        return min(1.0, final_score)

    def select_optimal_chunks(
        self,
        query: str,
        chunks: List[Dict],
        question_type: str
    ) -> Tuple[List[Dict], Dict]:
        """
        Selecciona el número óptimo de chunks según el tipo de pregunta

        Args:
            query: Pregunta original
            chunks: Lista de chunks recuperados
            question_type: Tipo de pregunta clasificada

        Returns:
            Tupla (chunks_seleccionados, metadata_seleccion)
        """
        config = self.configs[question_type]

        # Calcular scores de relevancia
        scored_chunks = []
        for chunk in chunks[:config['initial_k']]:
            score = self.calculate_relevance_score(query, chunk)
            chunk_copy = chunk.copy()
            chunk_copy['relevance_score'] = score
            scored_chunks.append(chunk_copy)

        # Ordenar por relevancia
        scored_chunks.sort(key=lambda x: x['relevance_score'], reverse=True)

        # Selección dinámica basada en confianza acumulada
        selected = []
        cumulative_confidence = 0.0

        for i, chunk in enumerate(scored_chunks):
            if i < config['min_chunks']:
                # Siempre incluir mínimo de chunks
                selected.append(chunk)
                cumulative_confidence += chunk['relevance_score']
            elif i < config['max_chunks']:
                # Incluir si mejora la confianza promedio
                avg_confidence = cumulative_confidence / len(selected)
                if chunk['relevance_score'] >= avg_confidence * 0.8:
                    selected.append(chunk)
                    cumulative_confidence += chunk['relevance_score']
                elif cumulative_confidence / len(selected) < config['confidence_threshold']:
                    # Incluir si aún no alcanzamos confianza objetivo
                    selected.append(chunk)
                    cumulative_confidence += chunk['relevance_score']
            else:
                break

        # Truncar contenido según configuración
        for chunk in selected:
            chunk['content'] = chunk['content'][:config['char_limit']]

        # Metadata de selección
        metadata = {
            'question_type': question_type,
            'chunks_selected': len(selected),
            'avg_relevance': cumulative_confidence / len(selected) if selected else 0,
            'config_used': config
        }

        return selected, metadata


class AdaptiveRAGEngine:
    """Motor RAG con selección adaptativa de chunks"""

    def __init__(self, base_rag_engine):
        """
        Inicializa el motor adaptativo

        Args:
            base_rag_engine: Motor RAG base (ConfigurableRAGEngine)
        """
        self.base_engine = base_rag_engine
        self.classifier = QuestionClassifier()
        self.selector = ChunkSelector()

    def retrieve_adaptive(self, query: str) -> Tuple[List[Dict], Dict]:
        """
        Recupera chunks de manera adaptativa según el tipo de pregunta

        Args:
            query: Pregunta del usuario

        Returns:
            Tupla (chunks_seleccionados, metadata)
        """
        # 1. Clasificar pregunta
        question_type = self.classifier.classify(query)

        # 2. Recuperar candidatos iniciales
        initial_chunks = self.base_engine.retrieve(query)

        # 3. Selección óptima de chunks
        selected_chunks, metadata = self.selector.select_optimal_chunks(
            query,
            initial_chunks,
            question_type
        )

        # Log para debug
        print(f"   🎯 Tipo: {question_type}, Chunks: {len(selected_chunks)}, "
              f"Relevancia: {metadata['avg_relevance']:.2f}")

        return selected_chunks, metadata

    def build_context(self, chunks: List[Dict]) -> str:
        """
        Construye contexto a partir de chunks seleccionados

        Args:
            chunks: Lista de chunks seleccionados

        Returns:
            Contexto formateado
        """
        return self.base_engine.build_context(chunks)


def create_adaptive_rag(vector_store_path: str):
    """
    Factory para crear un motor RAG adaptativo

    Args:
        vector_store_path: Ruta al vector store

    Returns:
        Motor RAG adaptativo configurado
    """
    from src.core.rag_engine import ConfigurableRAGEngine

    base_engine = ConfigurableRAGEngine(
        vector_store_path=vector_store_path,
        use_hybrid=True
    )

    return AdaptiveRAGEngine(base_engine)


# Ejemplo de uso
if __name__ == "__main__":
    # Test del clasificador
    classifier = QuestionClassifier()

    test_questions = [
        "¿Dónde es la actividad de coles?",  # Simple
        "¿Qué se hace en la actividad de desayunos?",  # Complex
        "¿Qué significa Para-Mira-Ayuda?",  # Conceptual
        "¿Cuándo es la actividad?",  # Simple
        "¿Cómo me apunto a desayunos solidarios?",  # Complex
    ]

    print("=== Test del Clasificador ===\n")
    for q in test_questions:
        q_type = classifier.classify(q)
        print(f"{q_type:12s} <- {q}")