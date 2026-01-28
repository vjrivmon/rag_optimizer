"""
Enhanced Model Wrapper con timeouts adaptativos y prompts optimizados
"""

import time
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# Importar wrappers y engines existentes
from .model_wrapper import LLMWrapper
from .enhanced_rag_engine_new import EnhancedRAGEngine

logger = logging.getLogger(__name__)

class EnhancedModelWrapper(LLMWrapper):
    """Wrapper mejorado con timeouts adaptativos y prompts optimizados"""

    def __init__(self, model_name: str, api_endpoint: str = "https://ollama.gti-ia.upv.es:443/api/generate", context_window: int = 2048):
        super().__init__(model_name, api_endpoint, context_window)
        self.enhanced_rag_engine = None
        self._setup_enhanced_engine()

    def _setup_enhanced_engine(self):
        """Configura el enhanced RAG engine"""
        try:
            vector_store_path = "data/vectorstore/chroma_db"
            if Path(vector_store_path).exists():
                self.enhanced_rag_engine = EnhancedRAGEngine(vector_store_path, use_hybrid=True)
                logger.info(f"Enhanced RAG Engine configurado para {self.model_name}")
            else:
                logger.warning(f"Vector store no encontrado en {vector_store_path}")
        except Exception as e:
            logger.error(f"Error configurando enhanced RAG engine: {e}")

    def get_adaptive_config(self, question_id: int) -> Dict[str, Any]:
        """Obtiene configuración adaptativa para la pregunta"""
        if not self.enhanced_rag_engine:
            return {}

        return self.enhanced_rag_engine.get_optimization_summary(question_id, self.model_name)

    def generate_response_with_optimization(self, question: str, question_id: int, contexts: List[str] = None) -> Dict[str, Any]:
        """Genera respuesta con optimizaciones adaptativas"""
        start_time = time.time()

        # Obtener configuración adaptativa
        config = self.get_adaptive_config(question_id)
        timeout = config.get('applied_optimizations', {}).get('timeout', 120)
        temperature = config.get('applied_optimizations', {}).get('temperature', 0.7)

        # Si no hay contexts, usar enhanced retrieval
        if contexts is None and self.enhanced_rag_engine:
            try:
                retrieved_docs = self.enhanced_rag_engine.retrieve_with_optimization(
                    question, question_id, self.model_name
                )
                contexts = [doc['content'] for doc in retrieved_docs]
            except Exception as e:
                logger.error(f"Error en enhanced retrieval: {e}")
                contexts = []

        # Crear prompt optimizado
        if self.enhanced_rag_engine and contexts:
            prompt = self.enhanced_rag_engine.create_enhanced_prompt(
                question, contexts, self.model_name, question_id
            )
        else:
            # Fallback a prompt básico
            prompt = self._create_basic_prompt(question, contexts or [])

        # Generar respuesta con timeout adaptativo
        try:
            response = self._generate_with_timeout(prompt, timeout, temperature)
            generation_time = time.time() - start_time

            # Analizar resultado
            analysis = self._analyze_response(question, response, contexts or [])

            return {
                'question': question,
                'question_id': question_id,
                'answer': response,
                'contexts': contexts or [],
                'generation_time': generation_time,
                'config_used': config,
                'optimization_applied': bool(config),
                'response_analysis': analysis
            }

        except Exception as e:
            logger.error(f"Error generando respuesta: {e}")
            return {
                'question': question,
                'question_id': question_id,
                'answer': f"Error generating response: {str(e)}",
                'contexts': contexts or [],
                'generation_time': time.time() - start_time,
                'config_used': config,
                'error': True
            }

    def _generate_with_timeout(self, prompt: str, timeout: int, temperature: float) -> str:
        """Genera respuesta con timeout específico"""
        try:
            # Llamar al método generate con parámetros ajustados
            response_data = super().generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=512
            )

            # El método generate devuelve un diccionario, extraer la respuesta
            if isinstance(response_data, dict):
                return response_data.get('response', str(response_data))
            else:
                return str(response_data)

        except Exception as e:
            if "timeout" in str(e).lower():
                logger.warning(f"Timeout en generación para {self.model_name} después de {timeout}s")
                return "[Respuesta truncada por timeout]"
            raise

    def _create_basic_prompt(self, question: str, contexts: List[str]) -> str:
        """Crea prompt básico como fallback"""
        prompt = f"Basado en la siguiente información, responde la pregunta: {question}\n\n"

        if contexts:
            prompt += "Información disponible:\n"
            for i, context in enumerate(contexts, 1):
                prompt += f"{i}. {context}\n"
        else:
            prompt += "No hay información específica disponible. Responde basándote en conocimientos generales.\n"

        prompt += "\nRespuesta:"
        return prompt

    def _analyze_response(self, question: str, response: str, contexts: List[str]) -> Dict[str, Any]:
        """Analiza la calidad de la respuesta generada"""
        analysis = {
            'response_length': len(response),
            'is_truncated': '[Respuesta truncada' in response,
            'has_no_info': 'no tengo información' in response.lower(),
            'contexts_used': len(contexts),
            'question_words_in_response': 0,
            'has_keywords': False
        }

        # Análisis básico de uso de información
        question_words = set(question.lower().split())
        response_words = set(response.lower().split())
        analysis['question_words_in_response'] = len(question_words & response_words)

        # Verificar si usa palabras clave relevantes
        if contexts:
            context_words = set()
            for context in contexts[:3]:  # Analizar primeros 3 contexts
                context_words.update(context.lower().split())

            keyword_overlap = len(context_words & response_words)
            analysis['has_keywords'] = keyword_overlap > 5  # Umbral básico

        return analysis

class EnhancedModelManager:
    """Manager para manejar múltiples modelos mejorados"""

    def __init__(self, model_names: List[str] = None):
        if model_names is None:
            model_names = ["gemma2:27b", "llama3.3:70b", "deepseek-r1:latest", "qwen3:32b"]

        self.models = {}
        self._initialize_models(model_names)

    def _initialize_models(self, model_names: List[str]):
        """Inicializa los modelos mejorados"""
        for model_name in model_names:
            try:
                self.models[model_name] = EnhancedModelWrapper(model_name)
                logger.info(f"Modelo {model_name} inicializado correctamente")
            except Exception as e:
                logger.error(f"Error inicializando modelo {model_name}: {e}")

    def generate_all_responses(self, question: str, question_id: int, contexts: List[str] = None) -> List[Dict[str, Any]]:
        """Genera respuestas con todos los modelos disponibles"""
        results = []

        for model_name, model in self.models.items():
            try:
                result = model.generate_response_with_optimization(question, question_id, contexts)
                result['model_name'] = model_name
                results.append(result)
                logger.info(f"Respuesta generada para {model_name} en {result['generation_time']:.2f}s")
            except Exception as e:
                logger.error(f"Error generando respuesta con {model_name}: {e}")
                results.append({
                    'model_name': model_name,
                    'question': question,
                    'question_id': question_id,
                    'answer': f"Error: {str(e)}",
                    'contexts': contexts or [],
                    'error': True
                })

        return results

    def get_model_configs_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de configuraciones de todos los modelos"""
        summary = {}

        for model_name, model in self.models.items():
            summary[model_name] = {
                'model_name': model_name,
                'enhanced_engine_available': model.enhanced_rag_engine is not None,
                'configurations': {}
            }

            # Obtener configuraciones para preguntas críticas
            for q_id in [6, 14, 19, 22]:
                config = model.get_adaptive_config(q_id)
                if config:
                    summary[model_name]['configurations'][f'Q{q_id}'] = config

        return summary

# Función de utilidad para crear el manager
def create_enhanced_model_manager(model_names: List[str] = None) -> EnhancedModelManager:
    """Crea una instancia del Enhanced Model Manager"""
    return EnhancedModelManager(model_names)

if __name__ == "__main__":
    # Test básico
    logging.basicConfig(level=logging.INFO)

    manager = create_enhanced_model_manager()

    # Test con pregunta problemática
    test_question = "¿Qué se hace en la actividad de resis?"
    test_question_id = 22

    print(f"🧪 Testeando pregunta Q{test_question_id}: {test_question}")
    results = manager.generate_all_responses(test_question, test_question_id)

    for result in results:
        model = result['model_name']
        answer = result['answer'][:100] + '...' if len(result['answer']) > 100 else result['answer']
        time_taken = result.get('generation_time', 0)

        print(f"\n📊 {model}:")
        print(f"   ⏱️ Tiempo: {time_taken:.2f}s")
        print(f"   💬 Respuesta: {answer}")

        if 'config_used' in result:
            config = result['config_used']
            print(f"   🔧 Optimización: {config.get('optimization_type', 'None')}")