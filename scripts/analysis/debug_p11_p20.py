#!/usr/bin/env python3
"""
🔍 Script de Debugging Específico para Preguntas 11 y 20

Diagnostica por qué las preguntas 11 (coles) y 20 (resis) están fallando
con puntuaciones de 0 en la mayoría de modelos.

Objetivos:
1. Analizar qué chunks se recuperan actualmente
2. Investigar embeddings y similitud
3. Identificar problemas en el retrieval
4. Probar soluciones específicas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
import time

# Imports del proyecto
from src.core.rag_engine import ConfigurableRAGEngine
from src.core.model_wrapper import LLMWrapper

# Configuración
VECTOR_STORE_PATH = "data/vectorstore/chroma_db"
DATASET_PATH = "data/evaluation_dataset.json"
MODELS_CONFIG = {
    "name": "gemma2:27b",
    "endpoint": "https://ollama.gti-ia.upv.es:443/api/generate"
}

class P11P20Debugger:
    """Debugger especializado para las preguntas problemáticas 11 y 20"""

    def __init__(self):
        print("🔧 Inicializando debugger para P11 y P20...")
        self.rag_engine = ConfigurableRAGEngine(VECTOR_STORE_PATH)
        self.model = LLMWrapper(MODELS_CONFIG["name"], MODELS_CONFIG["endpoint"])

        # Cargar dataset
        with open(DATASET_PATH, 'r', encoding='utf-8') as f:
            self.dataset = json.load(f)

        # Extraer preguntas 11 y 20
        self.p11_data = next(q for q in self.dataset if q['id'] == 11)
        self.p20_data = next(q for q in self.dataset if q['id'] == 20)

        print(f"✅ P11: {self.p11_data['question']}")
        print(f"✅ P20: {self.p20_data['question']}")

    def analyze_retrieval(self, question: str, question_id: int,
                         top_k_values: List[int] = [5, 10, 15]) -> Dict[str, Any]:
        """Analiza el retrieval para diferentes configuraciones"""

        print(f"\n🔍 ANALIZANDO RETRIEVAL PARA P{question_id}: '{question}'")
        print("=" * 80)

        results = {}

        for top_k in top_k_values:
            print(f"\n📊 TOP_K = {top_k}")
            print("-" * 40)

            # Probar diferentes similarity thresholds
            for threshold in [0.1, 0.2, 0.3, 0.4]:
                self.rag_engine.update_params({
                    'top_k': top_k,
                    'similarity_threshold': threshold,
                    'semantic_weight': 0.6,
                    'keyword_weight': 0.4
                })

                # Recuperar chunks
                chunks = self.rag_engine.retrieve(question)

                # Analizar chunks recuperados
                analysis = {
                    'top_k': top_k,
                    'threshold': threshold,
                    'num_chunks': len(chunks),
                    'chunks': []
                }

                for i, chunk in enumerate(chunks):
                    chunk_content = chunk['content'] if isinstance(chunk, dict) else str(chunk)
                    chunk_score = chunk.get('score', 0.0) if isinstance(chunk, dict) else 0.0

                    # Clasificar chunk por categoría
                    category = self._classify_chunk(chunk_content)

                    analysis['chunks'].append({
                        'rank': i + 1,
                        'content': chunk_content[:200] + "..." if len(chunk_content) > 200 else chunk_content,
                        'score': chunk_score,
                        'category': category,
                        'is_relevant': self._is_relevant_chunk(chunk_content, question_id)
                    })

                results[f"k{top_k}_t{threshold}"] = analysis

                # Mostrar resumen
                relevant_chunks = sum(1 for c in analysis['chunks'] if c['is_relevant'])
                print(f"   Threshold {threshold}: {len(chunks)} chunks, {relevant_chunks} relevantes")

                # Mostrar top 3 chunks
                for chunk in analysis['chunks'][:3]:
                    relevance = "✅" if chunk['is_relevant'] else "❌"
                    print(f"     {relevance} [{chunk['category']}] Score: {chunk['score']:.3f} - {chunk['content'][:80]}...")

        return results

    def _classify_chunk(self, content: str) -> str:
        """Clasifica el chunk por categoría (coles, resis, desayunos, etc.)"""
        content_lower = content.lower()

        if 'coles' in content_lower or 'refuerzo escolar' in content_lower or 'ceip antonio ferrandis' in content_lower:
            return 'COLES'
        elif 'resis' in content_lower or 'acollida' in content_lower or 'residencia' in content_lower:
            return 'RESIS'
        elif 'desayunos' in content_lower or 'cenas' in content_lower or 'porta de la mar' in content_lower:
            return 'DESAYUNOS'
        elif 'charlas' in content_lower or 'abuelos' in content_lower or 'mayores' in content_lower:
            return 'CHARLAS'
        elif 'filosofía' in content_lower or 'dni' in content_lower or 'asociación' in content_lower:
            return 'FILOSOFÍA'
        else:
            return 'GENERAL'

    def _is_relevant_chunk(self, content: str, question_id: int) -> bool:
        """Determina si un chunk es relevante para la pregunta específica"""
        content_lower = content.lower()

        if question_id == 11:  # ¿Dónde es la actividad de coles?
            # Buscar específicamente información sobre CEIP Antonio Ferrandis
            return ('ceip antonio ferrandis' in content_lower or
                   'antonio ferrandis' in content_lower or
                   ('coles' in content_lower and 'dónde' in content_lower))

        elif question_id == 20:  # ¿Dónde es la actividad de resis?
            # Buscar específicamente información sobre La Acollida
            return ('la acollida' in content_lower or
                   'crevillente 22' in content_lower or
                   'blasco ibáñez' in content_lower or
                   ('resis' in content_lower and 'dónde' in content_lower))

        return False

    def test_generation_with_analysis(self, question: str, question_id: int,
                                   chunks: List[str]) -> Dict[str, Any]:
        """Testea la generación con análisis detallado"""

        print(f"\n🤖 TEST DE GENERACIÓN PARA P{question_id}")
        print("=" * 50)

        # Construir prompt
        prompt = f"""Basado ÚNICAMENTE en la siguiente información proporcionada, responde a la pregunta.

PREGUNTA: {question}

INFORMACIÓN DISPONIBLE:
"""

        for i, context in enumerate(chunks[:5], 1):  # Top 5 chunks
            prompt += f"\n[{i}] {context}"

        prompt += """

RESPUESTA:"""

        print(f"📝 Prompt construido con {len(chunks)} contextos")

        # Generar respuesta
        start_time = time.time()
        try:
            response = self.model.generate(prompt=prompt, temperature=0.3, max_tokens=200)
            generation_time = time.time() - start_time

            if isinstance(response, dict):
                answer = response.get('response', str(response))
            else:
                answer = str(response)

            # Analizar respuesta
            analysis = self._analyze_generated_answer(answer, question_id)

            print(f"✅ Respuesta generada en {generation_time:.2f}s")
            print(f"📝 Respuesta: {answer}")
            print(f"📊 Análisis: {analysis}")

            return {
                'answer': answer,
                'generation_time': generation_time,
                'analysis': analysis,
                'prompt': prompt
            }

        except Exception as e:
            print(f"❌ Error en generación: {e}")
            return {
                'answer': f"Error: {str(e)}",
                'generation_time': time.time() - start_time,
                'analysis': {'error': True},
                'prompt': prompt
            }

    def _analyze_generated_answer(self, answer: str, question_id: int) -> Dict[str, Any]:
        """Analiza la calidad de la respuesta generada"""
        answer_lower = answer.lower()

        if question_id == 11:  # Coles
            has_correct_location = ('ceip antonio ferrandis' in answer_lower or
                                  'antonio ferrandis' in answer_lower)
            has_wrong_location = ('la acollida' in answer_lower or
                                'residencia' in answer_lower)
            says_no_info = ('no hay información' in answer_lower or
                          'no dispongo' in answer_lower or
                          'no mencionan' in answer_lower)

            return {
                'has_correct_location': has_correct_location,
                'has_wrong_location': has_wrong_location,
                'says_no_info': says_no_info,
                'is_correct': has_correct_location and not has_wrong_location and not says_no_info,
                'confidence': 1.0 if has_correct_location else 0.0
            }

        elif question_id == 20:  # Resis
            has_correct_location = ('la acollida' in answer_lower or
                                  'crevillente 22' in answer_lower or
                                  'blasco ibáñez' in answer_lower)
            has_wrong_location = ('ceip antonio ferrandis' in answer_lower or
                                'coles' in answer_lower)
            says_no_info = ('no hay información' in answer_lower or
                          'no dispongo' in answer_lower or
                          'no mencionan' in answer_lower)

            return {
                'has_correct_location': has_correct_location,
                'has_wrong_location': has_wrong_location,
                'says_no_info': says_no_info,
                'is_correct': has_correct_location and not has_wrong_location and not says_no_info,
                'confidence': 1.0 if has_correct_location else 0.0
            }

        return {'is_correct': False, 'confidence': 0.0}

    def run_comprehensive_analysis(self):
        """Ejecuta análisis completo para ambas preguntas"""

        print("\n" + "=" * 100)
        print("🔍 ANÁLISIS COMPLETO DE PREGUNTAS PROBLEMÁTICAS P11 y P20")
        print("=" * 100)

        # Configuración actual del sistema
        current_config = {
            'top_k': 6,
            'similarity_threshold': 0.2,
            'semantic_weight': 0.6,
            'keyword_weight': 0.4
        }

        print(f"\n⚙️ CONFIGURACIÓN ACTUAL: {current_config}")

        # Análisis para P11
        print("\n" + "🎯 ANÁLISIS PREGUNTA 11 (COLES)" + "\n" + "=" * 80)
        p11_results = self.analyze_retrieval(
            self.p11_data['question'],
            11,
            top_k_values=[5, 10, 15]
        )

        # Testear generación con mejor configuración encontrada
        best_config_p11 = self._find_best_config(p11_results)
        if best_config_p11:
            print(f"\n🏆 MEJOR CONFIGURACIÓN ENCONTRADA PARA P11: {best_config_p11}")
            self.rag_engine.update_params({
                'top_k': best_config_p11['top_k'],
                'similarity_threshold': best_config_p11['threshold'],
                'semantic_weight': 0.6,
                'keyword_weight': 0.4
            })

            chunks = self.rag_engine.retrieve(self.p11_data['question'])
            chunk_contents = [c['content'] if isinstance(c, dict) else str(c) for c in chunks]

            gen_result_p11 = self.test_generation_with_analysis(
                self.p11_data['question'], 11, chunk_contents
            )

        # Análisis para P20
        print("\n" + "🎯 ANÁLISIS PREGUNTA 20 (RESIS)" + "\n" + "=" * 80)
        p20_results = self.analyze_retrieval(
            self.p20_data['question'],
            20,
            top_k_values=[5, 10, 15]
        )

        # Testear generación con mejor configuración encontrada
        best_config_p20 = self._find_best_config(p20_results)
        if best_config_p20:
            print(f"\n🏆 MEJOR CONFIGURACIÓN ENCONTRADA PARA P20: {best_config_p20}")
            self.rag_engine.update_params({
                'top_k': best_config_p20['top_k'],
                'similarity_threshold': best_config_p20['threshold'],
                'semantic_weight': 0.6,
                'keyword_weight': 0.4
            })

            chunks = self.rag_engine.retrieve(self.p20_data['question'])
            chunk_contents = [c['content'] if isinstance(c, dict) else str(c) for c in chunks]

            gen_result_p20 = self.test_generation_with_analysis(
                self.p20_data['question'], 20, chunk_contents
            )

        # Resumen y recomendaciones
        self._generate_summary(p11_results, p20_results, best_config_p11, best_config_p20)

    def _find_best_config(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Encuentra la mejor configuración basada en chunks relevantes"""
        best_config = None
        max_relevant = 0

        for config_key, analysis in results.items():
            relevant_count = sum(1 for c in analysis['chunks'] if c['is_relevant'])
            if relevant_count > max_relevant:
                max_relevant = relevant_count
                best_config = {
                    'top_k': analysis['top_k'],
                    'threshold': analysis['threshold'],
                    'relevant_chunks': relevant_count,
                    'total_chunks': analysis['num_chunks']
                }

        return best_config

    def _generate_summary(self, p11_results: Dict, p20_results: Dict,
                         best_p11: Dict, best_p20: Dict):
        """Genera resumen del análisis y recomendaciones"""

        print("\n" + "📋 RESUMEN DEL ANÁLISIS Y RECOMENDACIONES" + "\n" + "=" * 80)

        print(f"\n🎯 PREGUNTA 11 (COLES):")
        print(f"   Expected: 'CEIP Antonio Ferrandis de la Coma, Valencia'")
        print(f"   Best config: top_k={best_p11['top_k']}, threshold={best_p11['threshold']}")
        print(f"   Relevant chunks: {best_p11['relevant_chunks']}/{best_p11['total_chunks']}")

        print(f"\n🎯 PREGUNTA 20 (RESIS):")
        print(f"   Expected: 'La Acollida, Crevillente 22'")
        print(f"   Best config: top_k={best_p20['top_k']}, threshold={best_p20['threshold']}")
        print(f"   Relevant chunks: {best_p20['relevant_chunks']}/{best_p20['total_chunks']}")

        print(f"\n🔧 RECOMENDACIONES:")

        if best_p11['relevant_chunks'] == 0:
            print(f"   ❌ P11: No se recuperaron chunks relevantes. Problema grave de retrieval.")
            print(f"      - Considerar búsqueda exacta por keywords")
            print(f"      - Revisar embeddings para 'CEIP Antonio Ferrandis'")
        else:
            print(f"   ✅ P11: Se encontraron {best_p11['relevant_chunks']} chunks relevantes")
            print(f"      - Usar configuración: top_k={best_p11['top_k']}, threshold={best_p11['threshold']}")

        if best_p20['relevant_chunks'] == 0:
            print(f"   ❌ P20: No se recuperaron chunks relevantes. Problema grave de retrieval.")
            print(f"      - Considerar búsqueda exacta por keywords")
            print(f"      - Revisar embeddings para 'La Acollida'")
        else:
            print(f"   ✅ P20: Se encontraron {best_p20['relevant_chunks']} chunks relevantes")
            print(f"      - Usar configuración: top_k={best_p20['top_k']}, threshold={best_p20['threshold']}")

        print(f"\n⚡ ACCIONES INMEDIATAS RECOMENDADAS:")
        print(f"   1. Implementar metadata filtering por categoría")
        print(f"   2. Añadir búsqueda híbrida exacta para nombres propios")
        print(f"   3. Sistema de fallback con diferentes configuraciones")
        print(f"   4. Validación en tiempo real durante benchmarks")

def main():
    """Función principal"""
    debugger = P11P20Debugger()
    debugger.run_comprehensive_analysis()

if __name__ == "__main__":
    main()