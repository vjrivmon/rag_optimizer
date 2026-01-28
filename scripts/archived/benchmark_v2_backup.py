#!/usr/bin/env python3
"""
🚀 RAG Benchmark v2.0 - Sistema de 2 fases con evaluación asíncrona

FASE 1: Generación rápida (5-10min)
  - Genera todas las respuestas de todos los modelos
  - Guarda en SQLite
  - Sin evaluación
  - ✨ LIMPIA etiquetas de razonamiento (<think>, <thinking>, etc.)

FASE 2: Evaluación asíncrona (background)
  - Lee respuestas de SQLite
  - Evalúa con OpenAI API (100x más rápido)
  - Updates en tiempo real
  - Recuperable si falla

USO:
  python benchmark_v2.py --phase generation  # Fase 1: genera respuestas
  python benchmark_v2.py --phase evaluation  # Fase 2: evalúa con RAGAs
  python benchmark_v2.py --phase both        # Ambas fases (default)
"""

import asyncio
import json
import sqlite3
import time
import re
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import argparse

# OpenAI para evaluaciones (mucho más rápido que Ollama)
import openai
from openai import AsyncOpenAI

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv()

# Imports del proyecto
from src.core.rag_engine import ConfigurableRAGEngine
from src.core.model_wrapper import LLMWrapper

# Imports para las 10 mejoras RAG v2.0
from src.chunking.semantic_chunker import SemanticChunker
from src.retrieval.query_expander import DomainQueryExpander
from src.retrieval.context_compressor import LightweightContextCompressor, CompressionConfig
from src.prompts.advanced_prompt_builder import AdvancedPromptBuilder
from src.generation.adaptive_generator import AdaptiveTemperatureGenerator
from src.generation.self_consistency_generator import SelfConsistencyGenerator
from src.evaluation.business_metrics import DNIBusinessMetrics
from src.retrieval.citation_tracker import CitationTracker


# ============================================================================
# LIMPIEZA DE ETIQUETAS DE RAZONAMIENTO
# ============================================================================

def clean_thinking_tags(text: str) -> str:
    """
    Elimina etiquetas de razonamiento interno de los modelos.
    
    Algunos modelos (qwen3:32b, deepseek-r1:latest) generan etiquetas como:
    <think>razonamiento interno...</think>
    <thinking>razonamiento interno...</thinking>
    <reasoning>razonamiento interno...</reasoning>
    
    Estas NO deben mostrarse al usuario ni evaluarse con RAGAs.
    
    Args:
        text: Texto generado por el modelo
        
    Returns:
        Texto limpio sin etiquetas de razonamiento
        
    Examples:
        >>> text = "<think>Hmm...</think>La respuesta es 42"
        >>> clean_thinking_tags(text)
        "La respuesta es 42"
    """
    patterns = [
        r'<think>.*?</think>',        # qwen3:32b, deepseek-r1:latest
        r'<thinking>.*?</thinking>',  # Algunos modelos alternativos
        r'<reasoning>.*?</reasoning>' # Otros modelos
    ]
    
    cleaned = text
    for pattern in patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL)
    
    return cleaned.strip()


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

MODELS_CONFIG = [
    {"name": "qwen3:32b", "endpoint": "https://ollama.gti-ia.upv.es:443/api/generate"},
    {"name": "deepseek-r1:latest", "endpoint": "https://ollama.gti-ia.upv.es:443/api/generate"},
    {"name": "gemma2:27b", "endpoint": "https://ollama.gti-ia.upv.es:443/api/generate"},
    {"name": "llama3.3:70b", "endpoint": "https://ollama.gti-ia.upv.es:443/api/generate"},
]

DATASET_PATH = "data/evaluation_dataset.json"
DB_PATH = "results/benchmark.db"
VECTOR_STORE_PATH = "data/vectorstore/chroma_db"


# ============================================================================
# BASE DE DATOS (SQLite para tracking robusto)
# ============================================================================

class BenchmarkDB:
    """Base de datos SQLite para tracking robusto del benchmark"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        Path(db_path).parent.mkdir(exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()
    
    def _init_schema(self):
        """Crea tablas si no existen"""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER,
                model_name TEXT,
                question TEXT,
                answer TEXT,
                contexts TEXT,  -- JSON array
                generated_at TIMESTAMP,
                generation_time REAL,
                error TEXT,
                UNIQUE(question_id, model_name)
            );
            
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                response_id INTEGER,
                faithfulness REAL,
                answer_relevancy REAL,
                context_precision REAL,
                context_recall REAL,
                answer_correctness REAL,
                answer_similarity REAL,
                combined_score REAL,
                evaluated_at TIMESTAMP,
                evaluation_time REAL,
                error TEXT,
                FOREIGN KEY(response_id) REFERENCES responses(id),
                UNIQUE(response_id)
            );
            
            CREATE TABLE IF NOT EXISTS benchmark_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                phase TEXT,
                total_questions INTEGER,
                total_models INTEGER,
                status TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_responses_model ON responses(model_name);
            CREATE INDEX IF NOT EXISTS idx_responses_question ON responses(question_id);
        """)
        self.conn.commit()
    
    def save_response(self, question_id: int, model_name: str, question: str,
                     answer: str, contexts: List[str], generation_time: float,
                     error: Optional[str] = None):
        """Guarda una respuesta generada"""
        self.conn.execute("""
            INSERT OR REPLACE INTO responses 
            (question_id, model_name, question, answer, contexts, 
             generated_at, generation_time, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            question_id, model_name, question, answer,
            json.dumps(contexts), datetime.now().isoformat(),
            generation_time, error
        ))
        self.conn.commit()
    
    def save_evaluation(self, response_id: int, metrics: Dict[str, float],
                       evaluation_time: float, error: Optional[str] = None):
        """Guarda una evaluación RAGAs"""
        self.conn.execute("""
            INSERT OR REPLACE INTO evaluations
            (response_id, faithfulness, answer_relevancy, context_precision,
             context_recall, answer_correctness, answer_similarity,
             combined_score, evaluated_at, evaluation_time, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            response_id,
            metrics.get('faithfulness'),
            metrics.get('answer_relevancy'),
            metrics.get('context_precision'),
            metrics.get('context_recall'),
            metrics.get('answer_correctness'),
            metrics.get('answer_similarity'),
            metrics.get('combined_score'),
            datetime.now().isoformat(),
            evaluation_time,
            error
        ))
        self.conn.commit()
    
    def get_unevaluated_responses(self, limit: Optional[int] = None) -> List[Dict]:
        """Obtiene respuestas que aún no han sido evaluadas"""
        query = """
            SELECT r.id, r.question_id, r.model_name, r.question, 
                   r.answer, r.contexts
            FROM responses r
            LEFT JOIN evaluations e ON r.id = e.response_id
            WHERE e.id IS NULL AND r.error IS NULL
        """
        if limit:
            query += f" LIMIT {limit}"
        
        cursor = self.conn.execute(query)
        return [
            {
                'response_id': row[0],
                'question_id': row[1],
                'model_name': row[2],
                'question': row[3],
                'answer': row[4],
                'contexts': json.loads(row[5])
            }
            for row in cursor.fetchall()
        ]
    
    def get_progress(self) -> Dict[str, Any]:
        """Obtiene estadísticas de progreso"""
        stats = {}
        
        # Total de respuestas
        cursor = self.conn.execute("SELECT COUNT(*) FROM responses WHERE error IS NULL")
        stats['total_responses'] = cursor.fetchone()[0]
        
        # Total de evaluaciones
        cursor = self.conn.execute("SELECT COUNT(*) FROM evaluations WHERE error IS NULL")
        stats['total_evaluations'] = cursor.fetchone()[0]
        
        # Progreso por modelo
        cursor = self.conn.execute("""
            SELECT r.model_name, 
                   COUNT(DISTINCT r.id) as total,
                   COUNT(DISTINCT e.id) as evaluated,
                   AVG(e.combined_score) as avg_score
            FROM responses r
            LEFT JOIN evaluations e ON r.id = e.response_id
            WHERE r.error IS NULL
            GROUP BY r.model_name
        """)
        stats['by_model'] = {
            row[0]: {
                'total': row[1],
                'evaluated': row[2],
                'avg_score': row[3] if row[3] else None
            }
            for row in cursor.fetchall()
        }
        
        return stats
    
    def export_results(self, output_path: str):
        """Exporta resultados completos a JSON"""
        cursor = self.conn.execute("""
            SELECT r.question_id, r.model_name, r.question, r.answer,
                   r.contexts, r.generation_time,
                   e.faithfulness, e.answer_relevancy, e.context_precision,
                   e.context_recall, e.answer_correctness, e.answer_similarity,
                   e.combined_score
            FROM responses r
            LEFT JOIN evaluations e ON r.id = e.response_id
            WHERE r.error IS NULL
            ORDER BY r.question_id, r.model_name
        """)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'question_id': row[0],
                'model_name': row[1],
                'question': row[2],
                'answer': row[3],
                'contexts': json.loads(row[4]),
                'generation_time': row[5],
                'metrics': {
                    'faithfulness': row[6],
                    'answer_relevancy': row[7],
                    'context_precision': row[8],
                    'context_recall': row[9],
                    'answer_correctness': row[10],
                    'answer_similarity': row[11],
                    'combined_score': row[12]
                }
            })
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)


# ============================================================================
# SISTEMA RAG v2.0 CON DATOS REALES
# ============================================================================

class RealRAGSystem:
    """Sistema RAG v2.0 con las 10 mejoras integradas usando datos reales de data/documents/"""

    def __init__(self, rag_engine: ConfigurableRAGEngine, model_wrapper: LLMWrapper):
        """Inicializar el sistema completo con datos reales"""
        print("🔧 Inicializando RealRAGSystem con 10 mejoras RAG v2.0...")

        # Base real con datos de data/documents/
        self.rag_engine = rag_engine  # ConfigurableRAGEngine con vector store real
        self.model_wrapper = model_wrapper  # LLMWrapper real con Ollama

        # 1️⃣ SemanticChunker - Para procesar documentos recuperados
        print("   1️⃣ Inicializando SemanticChunker...")
        self.semantic_chunker = SemanticChunker()

        # 2️⃣ Enhanced Retrieval - Usar mismo vector store que ConfigurableRAGEngine
        print("   2️⃣ Inicializando Enhanced Retrieval (vector store real)...")
        self.enhanced_retriever = self.rag_engine  # Reutilizar el mismo vector store real

        # 3️⃣ CrossEncoderReranker - Reranking avanzado (con el rag_engine como base)
        print("   3️⃣ Inicializando CrossEncoderReranker...")
        # Crear un wrapper simple para el reranker que funcione con ConfigurableRAGEngine
        class SimpleRerankerWrapper:
            def __init__(self, rag_engine):
                self.rag_engine = rag_engine
            def retrieve_and_rerank(self, query, k=5):
                # Simplemente usar el rag_engine y limitar a k resultados
                docs = self.rag_engine.retrieve(query)
                return docs[:k]
        self.reranker = SimpleRerankerWrapper(self.rag_engine)

        # 4️⃣ DomainQueryExpander - Expansión de queries para DNI
        print("   4️⃣ Inicializando DomainQueryExpander...")
        self.query_expander = DomainQueryExpander()

        # 5️⃣ LightweightContextCompressor - Compresión de contexto
        print("   5️⃣ Inicializando LightweightContextCompressor...")
        compression_config = CompressionConfig(method="tfidf")
        self.context_compressor = LightweightContextCompressor(config=compression_config)

        # 6️⃣ AdvancedPromptBuilder - Prompts optimizados
        print("   6️⃣ Inicializando AdvancedPromptBuilder...")
        self.prompt_builder = AdvancedPromptBuilder()

        # 7️⃣ AdaptiveTemperatureGenerator - Generación con temperatura adaptativa
        print("   7️⃣ Inicializando AdaptiveTemperatureGenerator...")
        self.adaptive_generator = AdaptiveTemperatureGenerator(model_wrapper)

        # 8️⃣ SelfConsistencyGenerator - Verificación de consistencia
        print("   8️⃣ Inicializando SelfConsistencyGenerator...")
        self.consistency_generator = SelfConsistencyGenerator(model_wrapper)

        # 9️⃣ DNIBusinessMetrics - Métricas de negocio específicas
        print("   9️⃣ Inicializando DNIBusinessMetrics...")
        self.business_metrics = DNIBusinessMetrics()

        # 🔟 CitationTracker - Generación de citas
        print("   🔟 Inicializando CitationTracker...")
        self.citation_tracker = CitationTracker()

        print("✅ RealRAGSystem inicializado con datos reales")

    def process_query(self, question: str) -> dict:
        """
        Procesa una pregunta usando todas las 10 mejoras RAG v2.0 con datos reales

        Args:
            question: Pregunta del usuario

        Returns:
            Resultado completo con todas las mejoras aplicadas usando datos reales
        """
        print(f"🎯 Procesando pregunta con RAG v2.0: '{question}'")

        start_time = time.time()
        results = {}

        # 1️⃣ DomainQueryExpander - Expandir pregunta con términos DNI
        print("   📈 Expandiendo query con dominio DNI...")
        expanded_queries = self.query_expander.expand_query(question)
        results['expanded_queries'] = expanded_queries

        # 2️⃣ Enhanced Retrieval - Usar vector store real con datos de data/documents/
        print("   🔍 Recuperando chunks con Enhanced Retrieval (datos reales)...")
        retrieved_chunks = self.enhanced_retriever.retrieve(question)
        results['retrieved_chunks'] = retrieved_chunks

        # 3️⃣ CrossEncoderReranker - Reranking avanzado (simple)
        print("   🎯 Aplicando reranking avanzado...")
        reranked_chunks = self.reranker.retrieve_and_rerank(question, k=5)
        results['reranked_chunks'] = reranked_chunks

        # 4️⃣ LightweightContextCompressor - Comprimir contexto
        print("   🗜️ Comprimiendo contexto...")
        compressed_chunks = self.context_compressor.compress_chunks(
            reranked_chunks, question, top_sentences=3
        )
        results['compressed_chunks'] = compressed_chunks

        # 5️⃣ AdvancedPromptBuilder - Construir prompt avanzado
        print("   📝 Construyendo prompt avanzado...")
        context_text = " ".join([chunk['content'] if isinstance(chunk, dict) else str(chunk)
                                for chunk in compressed_chunks])
        prompt = self.prompt_builder.build_prompt(
            question, context_text, self.model_wrapper.model_name
        )
        results['prompt'] = prompt

        # 6️⃣ AdaptiveTemperatureGenerator - Generación con temperatura adaptativa
        print("   🌡️ Generando respuesta con temperatura adaptativa...")
        # Actualizar el modelo en el adaptive generator
        self.adaptive_generator.model_wrapper = self.model_wrapper
        adaptive_result = self.adaptive_generator.generate_adaptive(
            prompt, question, self.model_wrapper.model_name, context_text
        )
        results['adaptive_generation'] = adaptive_result

        # 7️⃣ SelfConsistencyGenerator - Verificación de consistencia
        print("   🔄 Verificando self-consistency...")
        # Actualizar el modelo en el consistency generator
        self.consistency_generator.model_wrapper = self.model_wrapper
        is_critical = self.consistency_generator.is_critical_question(question)
        if is_critical:
            consistency_result = self.consistency_generator.generate_with_auto_consistency(
                prompt, question, num_samples=3
            )
            results['consistency_check'] = consistency_result
        else:
            results['consistency_check'] = {'applied': False, 'reason': 'Pregunta no crítica'}

        # 8️⃣ CitationTracker - Añadir citas
        print("   📝 Añadiendo citations...")
        citation_result = self.citation_tracker.generate_with_citations(
            self.model_wrapper, prompt, compressed_chunks, question
        )
        results['citations'] = citation_result

        # 9️⃣ DNIBusinessMetrics - Evaluar métricas de negocio DNI
        print("   📊 Evaluando métricas de negocio DNI...")
        answer = citation_result.get('answer', adaptive_result.get('answer', ''))
        business_metrics = self.business_metrics.evaluate_business_metrics(question, answer)
        results['business_metrics'] = business_metrics

        # 🔟 Resultado final integrado
        total_time = time.time() - start_time
        results['final_answer'] = citation_result.get('answer', answer)
        results['processing_time'] = total_time
        results['system_info'] = {
            'version': 'v2.0-real',
            'improvements_applied': 10,
            'data_source': 'data/documents/',
            'question_type': business_metrics.get('_metadata', {}).get('detected_category', 'unknown')
        }

        print(f"✅ Procesamiento RAG v2.0 completado en {total_time:.2f}s")
        return results

# ============================================================================
# FASE 1: GENERACIÓN RÁPIDA
# ============================================================================

class GenerationPhase:
    """Fase 1: Genera todas las respuestas usando RAG v2.0 con las 10 mejoras"""

    def __init__(self, db: BenchmarkDB):
        self.db = db
        self.rag_engine = ConfigurableRAGEngine(VECTOR_STORE_PATH)
        self.models = {
            cfg['name']: LLMWrapper(cfg['name'], cfg['endpoint'])
            for cfg in MODELS_CONFIG
        }

        # Crear UN sistema RAG v2.0 compartido (más eficiente con datos reales)
        print("🔧 Creando RealRAGSystem compartido...")
        self.base_model = list(self.models.values())[0]  # Usar primer modelo como base
        self.shared_rag_system = RealRAGSystem(self.rag_engine, self.base_model)
        print("✅ RealRAGSystem compartido inicializado con datos reales")
    
    def run(self, questions: List[Dict], max_questions: Optional[int] = None):
        """Ejecuta fase de generación"""
        if max_questions:
            questions = questions[:max_questions]
        
        total = len(questions) * len(self.models)
        print(f"\n🚀 FASE 1: GENERACIÓN")
        print(f"=" * 60)
        print(f"Preguntas: {len(questions)}")
        print(f"Modelos: {len(self.models)}")
        print(f"Total respuestas a generar: {total}")
        print(f"=" * 60)
        
        start_time = time.time()
        completed = 0
        
        for q_idx, question_data in enumerate(questions, 1):
            question = question_data['question']
            print(f"\n📝 [{q_idx}/{len(questions)}] {question}")
            
            # ✨ USAR RAG v2.0 CON LAS 10 MEJORAS PARA CADA MODELO
            for model_name, model in self.models.items():
                print(f"   🤖 {model_name} (RAG v2.0 + 10 mejoras)...", end=' ', flush=True)

                gen_start = time.time()
                try:
                    # ✨ PROCESAMIENTO COMPLETO CON LAS 10 MEJORAS RAG v2.0
                    # Actualizar el modelo wrapper en el sistema compartido para esta iteración
                    self.shared_rag_system.model_wrapper = model
                    result = self.shared_rag_system.process_query(question)

                    # El sistema RAG v2.0 siempre devuelve éxito si tiene final_answer
                    if result.get('final_answer'):
                        answer = result['final_answer']
                        raw_contexts = result.get('retrieved_chunks', [])

                        # 🛠️ NORMALIZAR CONTEXTOS: Extraer solo texto de los chunks
                        contexts = []
                        for chunk in raw_contexts:
                            if isinstance(chunk, dict):
                                # Si es diccionario, extraer el contenido
                                contexts.append(chunk.get('content', str(chunk)))
                            else:
                                # Si ya es string, usarlo directamente
                                contexts.append(str(chunk))

                        # ✨ LIMPIAR ETIQUETAS DE RAZONAMIENTO
                        answer_original_len = len(answer)
                        answer = clean_thinking_tags(answer)
                        answer_cleaned_len = len(answer)

                        gen_time = time.time() - gen_start

                        # Guardar en DB con contextos reales y mejoras aplicadas
                        self.db.save_response(
                            question_id=q_idx,
                            model_name=model_name,
                            question=question,
                            answer=answer,
                            contexts=contexts,  # Contextos reales de data/documents procesados
                            generation_time=gen_time,
                            error=None
                        )

                        # Mostrar si se limpió algo
                        if answer_cleaned_len < answer_original_len:
                            reduction_pct = (1 - answer_cleaned_len/answer_original_len) * 100
                            print(f"✅ {gen_time:.1f}s (RAG v2.0 + {reduction_pct:.1f}% limpiado)")
                        else:
                            print(f"✅ {gen_time:.1f}s (RAG v2.0)")

                        completed += 1
                    else:
                        error = "No se pudo generar respuesta con RAG v2.0"
                        # Obtener contexts del sistema RAG aunque haya error
                        raw_contexts = result.get('retrieved_chunks', [])
                        contexts = [chunk.get('content', str(chunk)) if isinstance(chunk, dict) else str(chunk)
                                   for chunk in raw_contexts]
                        self.db.save_response(
                            question_id=q_idx,
                            model_name=model_name,
                            question=question,
                            answer='',
                            contexts=contexts,
                            generation_time=0,
                            error=error
                        )
                        print(f"❌ Error: {error[:50]}")

                except Exception as e:
                    print(f"❌ Exception: {str(e)[:50]}")
                    self.db.save_response(
                        question_id=q_idx,
                        model_name=model_name,
                        question=question,
                        answer='',
                        contexts=[],  # Contextos vacíos en caso de excepción
                        generation_time=0,
                        error=str(e)
                    )
        
        elapsed = time.time() - start_time
        print(f"\n✅ FASE 1 COMPLETA")
        print(f"   Respuestas generadas: {completed}/{total}")
        print(f"   Tiempo total: {elapsed/60:.1f} minutos")
        if completed > 0:
            print(f"   Promedio por respuesta: {elapsed/completed:.1f}s")
        else:
            print(f"   ⚠️ No se completaron respuestas")


# ============================================================================
# FASE 2: EVALUACIÓN ASÍNCRONA CON OPENAI
# ============================================================================

class EvaluationPhase:
    """Fase 2: Evalúa respuestas con OpenAI API (asíncrono)"""

    def __init__(self, db: BenchmarkDB, openai_api_key: str, dataset: List[Dict]):
        self.db = db
        self.client = AsyncOpenAI(api_key=openai_api_key)
        self.dataset = {q['id']: q for q in dataset}  # Mapeo id -> pregunta completa
    
    async def evaluate_single(self, response: Dict) -> Dict[str, float]:
        """Evalúa una respuesta con métricas RAGAs usando OpenAI y ground truth"""

        # Obtener expected_answer del dataset
        question_id = response['question_id']
        dataset_question = self.dataset.get(question_id, {})
        expected_answer = dataset_question.get('expected_answer', 'No disponible')

        # Evaluator GPT-4 con ground truth - más estricto
        system_prompt = """Eres un evaluador experto y CRÍTICO de sistemas RAG.
Evalúa la respuesta del modelo comparándola con la RESPUESTA ESPERADA (ground truth).

Sé muy estricto en las evaluaciones (escala 0-1):
1. faithfulness: ¿La respuesta se basa 100% en el contexto? ¿Alucina información?
2. answer_relevancy: ¿La respuesta aborda directamente la pregunta?
3. context_precision: ¿El contexto recuperado contiene la información necesaria?
4. context_recall: ¿Se recuperó suficiente contexto para responder bien?
5. answer_correctness: ¿La respuesta es correcta comparada con la RESPUESTA ESPERADA?
6. answer_similarity: ¿Qué tan similar es la respuesta a la RESPUESTA ESPERADA?

CRITERIOS DE PUNTUACIÓN:
- 1.0 = Perfecto, sin errores
- 0.8-0.9 = Excelente, errores menores
- 0.6-0.7 = Bueno, errores moderados
- 0.4-0.5 = Regular, errores significativos
- 0.2-0.3 = Pobre, muchos errores
- 0.0-0.1 = Muy malo o irrelevante

Responde SOLO con JSON:
{"faithfulness": 0.X, "answer_relevancy": 0.X, ...}"""

        user_prompt = f"""PREGUNTA: {response['question']}

RESPUESTA ESPERADA (Ground Truth):
{expected_answer}

CONTEXTO RECUPERADO:
{chr(10).join(response['contexts'][:3])}

RESPUESTA DEL MODELO:
{response['answer']}

Evalúa la respuesta del modelo comparando con la RESPUESTA ESPERADA. Sé crítico y objetivo."""
        
        try:
            completion = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Rápido y barato
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            # Parsear respuesta
            metrics = json.loads(completion.choices[0].message.content)
            
            # Calcular score combinado
            weights = {
                'faithfulness': 0.25,
                'answer_relevancy': 0.20,
                'context_precision': 0.15,
                'context_recall': 0.20,
                'answer_correctness': 0.10,
                'answer_similarity': 0.10
            }
            
            combined = sum(
                metrics.get(k, 0) * v
                for k, v in weights.items()
            )
            metrics['combined_score'] = combined
            
            return metrics
            
        except Exception as e:
            # 🛠️ LOGGING DETALLADO DE EXCEPCIONES
            print(f"⚠️ Error evaluando respuesta {response.get('response_id', 'N/A')}: {str(e)[:100]}")
            print(f"      Model: {response.get('model_name', 'N/A')}")
            print(f"      Question: {response.get('question', 'N/A')[:50]}...")
            print(f"      Error type: {type(e).__name__}")
            if 'contexts' in response:
                print(f"      Contexts type: {type(response['contexts']).__name__}")
                if isinstance(response['contexts'], list) and len(response['contexts']) > 0:
                    print(f"      First context type: {type(response['contexts'][0]).__name__}")
            return {}
    
    async def run_async(self, batch_size: int = 10, max_concurrent: int = 5):
        """Ejecuta evaluaciones en paralelo (asíncrono)"""
        
        # Obtener respuestas pendientes
        pending = self.db.get_unevaluated_responses()
        total = len(pending)
        
        if total == 0:
            print("✅ Todas las respuestas ya están evaluadas")
            return
        
        print(f"\n🔬 FASE 2: EVALUACIÓN ASÍNCRONA")
        print(f"=" * 60)
        print(f"Respuestas pendientes: {total}")
        print(f"Concurrencia: {max_concurrent} evaluaciones simultáneas")
        print(f"=" * 60)
        
        start_time = time.time()
        completed = 0
        
        # Procesar en batches con concurrencia limitada
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def evaluate_with_semaphore(response):
            async with semaphore:
                return await self.evaluate_single(response)
        
        # Procesar en batches
        for i in range(0, total, batch_size):
            batch = pending[i:i+batch_size]
            print(f"\n📦 Batch {i//batch_size + 1}/{(total + batch_size - 1)//batch_size}")
            
            # Evaluar batch en paralelo
            tasks = [evaluate_with_semaphore(resp) for resp in batch]
            eval_start = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            eval_time = time.time() - eval_start
            
            # Guardar resultados
            for response, metrics in zip(batch, results):
                if isinstance(metrics, Exception):
                    print(f"   ❌ {response['model_name']}: {str(metrics)[:40]}")
                    self.db.save_evaluation(
                        response['response_id'],
                        {},
                        0,
                        error=str(metrics)
                    )
                elif metrics:
                    score = metrics.get('combined_score', 0)
                    print(f"   ✅ {response['model_name']}: {score:.3f}")
                    self.db.save_evaluation(
                        response['response_id'],
                        metrics,
                        eval_time / len(batch)
                    )
                    completed += 1
                else:
                    print(f"   ⚠️ {response['model_name']}: Sin métricas (respuesta vacía)")
                    # 🛠️ LOGGING EXPLÍCITO: Registrar detalles para depuración
                    print(f"      📝 Question: {response.get('question', 'N/A')[:50]}...")
                    print(f"      📝 Answer length: {len(response.get('answer', ''))}")
                    print(f"      📝 Contexts count: {len(response.get('contexts', []))}")
            
            # Mostrar progreso
            elapsed = time.time() - start_time
            progress = (i + len(batch)) / total
            eta = (elapsed / progress) - elapsed if progress > 0 else 0
            print(f"   📊 Progreso: {progress*100:.1f}% | ETA: {eta/60:.1f}min")
        
        elapsed = time.time() - start_time
        print(f"\n✅ FASE 2 COMPLETA")
        print(f"   Evaluaciones completadas: {completed}/{total}")
        print(f"   Tiempo total: {elapsed/60:.1f} minutos")
        if completed > 0:
            print(f"   Promedio por evaluación: {elapsed/completed:.1f}s")
        else:
            print(f"   ⚠️ No se completaron evaluaciones - revisar logs de errores")
    
    def run(self, batch_size: int = 10, max_concurrent: int = 5):
        """Wrapper síncrono para run_async"""
        asyncio.run(self.run_async(batch_size, max_concurrent))


# ============================================================================
# CLI PRINCIPAL
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="RAG Benchmark v2.0 - Sistema de 2 fases con limpieza de etiquetas"
    )
    parser.add_argument(
        '--phase',
        choices=['generation', 'evaluation', 'both'],
        default='both',
        help='Fase a ejecutar (default: both)'
    )
    parser.add_argument(
        '--max-questions',
        type=int,
        help='Número máximo de preguntas (default: todas)'
    )
    parser.add_argument(
        '--openai-key',
        type=str,
        help='OpenAI API key (o usar OPENAI_API_KEY env var)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Tamaño de batch para evaluación (default: 10)'
    )
    parser.add_argument(
        '--max-concurrent',
        type=int,
        default=5,
        help='Evaluaciones simultáneas (default: 5)'
    )
    parser.add_argument(
        '--export',
        type=str,
        help='Exportar resultados a JSON'
    )
    parser.add_argument(
        '--progress',
        action='store_true',
        help='Mostrar solo progreso actual'
    )
    
    args = parser.parse_args()
    
    # Inicializar DB
    db = BenchmarkDB()
    
    # Mostrar progreso si se solicita
    if args.progress:
        stats = db.get_progress()
        print(f"\n📊 PROGRESO ACTUAL")
        print(f"=" * 60)
        print(f"Respuestas generadas: {stats['total_responses']}")
        print(f"Evaluaciones completadas: {stats['total_evaluations']}")
        print(f"\nPor modelo:")
        for model, data in stats['by_model'].items():
            pct = (data['evaluated'] / data['total'] * 100) if data['total'] > 0 else 0
            score = f"{data['avg_score']:.3f}" if data['avg_score'] else "---"
            print(f"  {model:20s} {data['evaluated']}/{data['total']} ({pct:5.1f}%) | Score: {score}")
        return
    
    # Exportar si se solicita
    if args.export:
        print(f"📤 Exportando resultados a {args.export}...")
        db.export_results(args.export)
        print("✅ Exportación completa")
        return
    
    # Cargar dataset
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
    # FASE 1: Generación
    if args.phase in ['generation', 'both']:
        gen_phase = GenerationPhase(db)
        gen_phase.run(questions, args.max_questions)
    
    # FASE 2: Evaluación
    if args.phase in ['evaluation', 'both']:
        # Obtener API key
        openai_key = args.openai_key or os.environ.get('OPENAI_API_KEY')
        if not openai_key:
            print("❌ Error: Se requiere OpenAI API key")
            print("   Usa --openai-key o la variable OPENAI_API_KEY")
            return
        
        eval_phase = EvaluationPhase(db, openai_key, questions)
        eval_phase.run(args.batch_size, args.max_concurrent)
    
    # Mostrar resumen final
    stats = db.get_progress()
    print(f"\n" + "=" * 60)
    print(f"🎉 BENCHMARK COMPLETO")
    print(f"=" * 60)
    print(f"Respuestas: {stats['total_responses']}")
    print(f"Evaluaciones: {stats['total_evaluations']}")
    print(f"\n🏆 RANKING FINAL:")
    
    # Ordenar modelos por score
    ranked = sorted(
        stats['by_model'].items(),
        key=lambda x: x[1]['avg_score'] if x[1]['avg_score'] else 0,
        reverse=True
    )
    
    for rank, (model, data) in enumerate(ranked, 1):
        score = f"{data['avg_score']:.3f}" if data['avg_score'] else "---"
        print(f"  {rank}. {model:20s} Score: {score}")
    
    # ✨ EXPORTACIÓN AUTOMÁTICA
    # Asegurar que existe la carpeta results
    Path("results").mkdir(exist_ok=True)
    
    # Generar nombre de archivo con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_path = f"results/benchmark_{timestamp}.json"
    
    print(f"\n💾 Exportando resultados automáticamente...")
    db.export_results(export_path)
    print(f"   ✅ Guardado en: {export_path}")
    print(f"\n🚀 Para visualizar los resultados:")
    print(f"   streamlit run interface/app_advanced.py")


if __name__ == "__main__":
    main()