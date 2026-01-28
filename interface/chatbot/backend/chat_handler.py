"""
Chat Handler - Procesamiento de Preguntas con Streaming
=======================================================

Maneja el procesamiento de preguntas del usuario usando modelos individuales
o estrategias ensemble, con soporte para streaming de estados via WebSocket.
"""

import time
import asyncio
import re
from typing import Dict, Any, Optional
from fastapi import WebSocket


def clean_thinking_tags(text: str) -> str:
    """
    Elimina las etiquetas <think> y razonamiento en inglés de forma INTELIGENTE.
    Preserva la respuesta válida en español.
    """
    if not text:
        return text
    
    original_text = text
    
    # 1. Remover bloques <think>...</think> completos
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # 2. Remover <thinking>...</thinking>
    text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # 3. Si el texto empieza con razonamiento en inglés (sin tags o con tags abiertos)
    # Detectar patrones típicos de razonamiento
    english_reasoning_starts = [
        'looking through the texts',
        'looking at point',
        'okay, let\'s tackle',
        'first, ',
        'so the answer is',
        'but the user is asking',
        'that seems like',
        'they ask if',
    ]
    
    text_lower = text.lower().strip()
    starts_with_reasoning = any(text_lower.startswith(pattern) for pattern in english_reasoning_starts)
    
    if starts_with_reasoning or text_lower.startswith('<think'):
        # Buscar indicadores FUERTES de contenido español válido
        spanish_indicators = [
            (r'(?:Sí|Si|No), (?:puedes|se puede|está permitido)', 'Respuesta directa'),
            (r'(?:La|El|Los|Las) (?:actividad|desayuno|formulario|grupo)', 'Sustantivo específico'),
            (r'En (?:el|la) (?:punto|texto|formulario|actividad)', 'Referencia al texto'),
            (r'Según (?:el|la) (?:información|texto)', 'Referencia'),
            (r'Claro\.', 'Afirmación'),
            (r'Bueno,', 'Inicio de explicación'),
        ]
        
        for pattern, desc in spanish_indicators:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Encontrado inicio de contenido español
                text = text[match.start():]
                print(f"   🔍 Detectado inicio español: {desc} en posición {match.start()}")
                break
    
    # 4. Limpiar espacios múltiples y saltos de línea al inicio
    text = text.strip()
    text = re.sub(r'^\n+', '', text)
    
    # 5. SEGURIDAD: Si después de limpiar queda vacío o muy corto, devolver original
    if len(text.strip()) < 30:
        print(f"   ⚠️ WARNING: Filtro dejó texto muy corto ({len(text.strip())} chars), usando original")
        return original_text
    
    # 6. Verificar que la respuesta filtrada tiene sentido (no es solo inglés)
    # Si más del 50% son palabras en inglés comunes, probablemente falló el filtro
    english_words = ['the', 'is', 'and', 'or', 'but', 'they', 'you', 'that', 'this', 'looking', 'point']
    words = text.lower().split()[:20]  # Primeras 20 palabras
    english_count = sum(1 for word in words if word in english_words)
    
    if len(words) > 5 and english_count > len(words) * 0.4:
        print(f"   ⚠️ WARNING: Respuesta filtrada parece ser mayormente inglés, usando original")
        return original_text
    
    return text


def clean_response(text: str) -> str:
    """
    Limpia respuestas de formato markdown y caracteres no deseados.
    
    - Elimina tags <think>
    - Elimina markdown bold: **texto** → texto
    - Elimina markdown italic: *texto* → texto
    - Elimina asteriscos múltiples: *** → (vacío)
    - Limpia espacios múltiples
    """
    if not text:
        return text
    
    # Limpiar tags <think>
    text = clean_thinking_tags(text)
    
    # Remover markdown bold: **texto** → texto
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    
    # Remover markdown italic: *texto* → texto (solo si no es parte de lista)
    text = re.sub(r'(?<!\n)\*([^\*\n]+?)\*', r'\1', text)
    
    # Remover asteriscos múltiples (3 o más)
    text = re.sub(r'\*{3,}', '', text)
    
    # Limpiar espacios múltiples
    text = re.sub(r' +', ' ', text)
    
    # Limpiar saltos de línea múltiples
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


class InteractiveChatHandler:
    """Maneja procesamiento interactivo de preguntas con streaming de estados"""
    
    def __init__(self, ensemble_engine, rag_engines):
        """
        Inicializa el handler.
        
        Args:
            ensemble_engine: Motor de ensemble (EnsembleRAGEngine)
            rag_engines: Diccionario de engines RAG individuales
        """
        self.ensemble_engine = ensemble_engine
        self.rag_engines = rag_engines
        
        # Contador para asignar IDs únicos a preguntas
        self.question_counter = 0
    
    async def process_question(
        self,
        question: str,
        selected_option: str,
        websocket: Optional[WebSocket] = None
    ) -> Dict[str, Any]:
        """
        Procesa una pregunta y retorna la respuesta.
        
        Args:
            question: Pregunta del usuario
            selected_option: Modelo o estrategia seleccionada
                            (ej: "gemma2:27b", "ensemble_voting")
            websocket: WebSocket opcional para enviar estados intermedios
        
        Returns:
            Dict con answer, sources, time, validation
        """
        self.question_counter += 1
        question_id = self.question_counter
        
        print(f"\n{'='*80}")
        print(f"📥 NUEVA PREGUNTA #{question_id}")
        print(f"{'='*80}")
        print(f"Pregunta: {question}")
        print(f"Modelo/Estrategia: {selected_option}")
        print(f"{'='*80}\n")
        
        start_time = time.time()
        
        try:
            # Estado: Conectando
            await self._send_status(websocket, "connecting")
            await asyncio.sleep(0.5)
            
            # Determinar si es ensemble o individual
            is_ensemble = selected_option.startswith("ensemble_")
            
            if is_ensemble:
                result = await self._process_ensemble(
                    question,
                    question_id,
                    selected_option,
                    websocket
                )
            else:
                result = await self._process_individual(
                    question,
                    question_id,
                    selected_option,
                    websocket
                )
            
            total_time = time.time() - start_time
            
            # DEBUG: Ver respuesta ANTES de limpiar
            raw_answer = result['answer']
            print(f"\n🔍 DEBUG - Respuesta RAW (primeros 300 chars):")
            print(f"{raw_answer[:300]}")
            print(f"\n🔍 Contiene <think>? {('<think>' in raw_answer.lower())}")
            
            # Limpiar respuesta (eliminar markdown y asteriscos)
            cleaned_answer = clean_response(raw_answer)
            
            # DEBUG: Ver respuesta DESPUÉS de limpiar
            print(f"\n🔍 DEBUG - Respuesta LIMPIA (primeros 300 chars):")
            print(f"{cleaned_answer[:300]}")
            print(f"\n🔍 Contiene <think>? {('<think>' in cleaned_answer.lower())}")
            
            # Logging detallado en consola
            print(f"\n{'='*80}")
            print(f"✅ RESPUESTA GENERADA #{question_id}")
            print(f"{'='*80}")
            print(f"Tiempo total: {total_time:.2f}s")
            print(f"Respuesta (limpia): {cleaned_answer[:200]}...")
            print(f"Fuentes consultadas: {len(result.get('contexts', []))}")
            
            if 'metrics' in result:
                print(f"\n📊 MÉTRICAS:")
                metrics = result['metrics']
                print(f"   - Combined Score: {metrics.get('combined_score', 0):.3f}")
                print(f"   - Faithfulness: {metrics.get('faithfulness', 0):.3f}")
                print(f"   - Answer Relevancy: {metrics.get('answer_relevancy', 0):.3f}")
            
            if 'validation' in result:
                validation = result['validation']
                is_valid = validation.get('is_valid', False) if isinstance(validation, dict) else getattr(validation, 'is_valid', False)
                confidence = validation.get('confidence', 0) if isinstance(validation, dict) else getattr(validation, 'confidence', 0)
                print(f"\n✓ VALIDACIÓN:")
                print(f"   - Válida: {is_valid}")
                print(f"   - Confianza: {confidence:.2f}")
            
            print(f"{'='*80}\n")
            
            # Preparar respuesta para frontend
            response = {
                "answer": cleaned_answer,
                "sources": self._format_sources(result.get('contexts', [])),
                "time": total_time
            }
            
            return response
            
        except Exception as e:
            print(f"❌ ERROR procesando pregunta #{question_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return {
                "answer": f"Lo siento, hubo un error al procesar tu pregunta: {str(e)}",
                "sources": [],
                "time": time.time() - start_time
            }
    
    async def _process_individual(
        self,
        question: str,
        question_id: int,
        model_name: str,
        websocket: Optional[WebSocket]
    ) -> Dict[str, Any]:
        """Procesa pregunta con un modelo individual"""
        
        # Estado: Recuperando información
        await self._send_status(websocket, "retrieving")
        
        # Obtener engine del modelo
        engine = self.rag_engines.get(model_name)
        if not engine:
            raise ValueError(f"Modelo {model_name} no disponible")
        
        # Estado: Pensando (durante generación)
        await self._send_status(websocket, "thinking")
        
        print(f"   🔍 Procesando con {model_name}...")
        
        # Generar respuesta
        result = engine.process_query_with_validation(
            question=question,
            question_id=question_id
        )
        
        # Estado: Finalizando
        await self._send_status(websocket, "finalizing")
        await asyncio.sleep(0.5)
        
        return result
    
    async def _process_ensemble(
        self,
        question: str,
        question_id: int,
        strategy_key: str,
        websocket: Optional[WebSocket]
    ) -> Dict[str, Any]:
        """Procesa pregunta con estrategia ensemble"""
        
        # Extraer nombre de estrategia (sin "ensemble_" prefix)
        strategy_name = strategy_key.replace("ensemble_", "")
        
        # Estado: Recuperando información
        await self._send_status(websocket, "retrieving")
        
        print(f"   🎲 Procesando con ensemble ({strategy_name})...")
        print(f"   📝 Generando respuestas con 4 modelos...")
        
        # Estado: Pensando (durante generación de modelos)
        await self._send_status(websocket, "thinking")
        
        # Generar respuestas con todos los modelos
        individual_responses = self.ensemble_engine.generate_individual_responses(
            question=question,
            question_id=question_id
        )
        
        print(f"   ✓ {len(individual_responses)} respuestas individuales generadas")
        
        # Estado: Procesando (aplicando estrategia)
        await self._send_status(websocket, "processing")
        
        print(f"   🎯 Aplicando estrategia {strategy_name}...")
        
        # Aplicar estrategia específica
        ensemble_results = self.ensemble_engine.apply_strategies(
            question=question,
            question_id=question_id,
            individual_responses=individual_responses,
            strategies=[strategy_name]
        )
        
        # Obtener resultado de la estrategia seleccionada
        if strategy_name not in ensemble_results:
            raise ValueError(f"Estrategia {strategy_name} no disponible")
        
        result = ensemble_results[strategy_name]
        
        print(f"   ✓ Estrategia {strategy_name} aplicada")
        print(f"   📌 Respuesta seleccionada de: {result.get('selected_from', 'N/A')}")
        print(f"   💡 Razón: {result.get('selection_reason', 'N/A')}")
        
        # Estado: Finalizando
        await self._send_status(websocket, "finalizing")
        await asyncio.sleep(0.5)
        
        return result
    
    async def _send_status(self, websocket: Optional[WebSocket], status: str):
        """Envía estado intermedio via WebSocket"""
        if websocket:
            try:
                await websocket.send_json({
                    "type": "status",
                    "status": status
                })
            except Exception as e:
                print(f"   ⚠️ Error enviando status via WebSocket: {e}")
    
    def _format_sources(self, contexts: list) -> list:
        """Formatea chunks/contextos como fuentes citables"""
        sources = []
        
        for idx, context in enumerate(contexts):
            # El contexto puede ser string o dict
            if isinstance(context, str):
                text = context
                score = None
            else:
                text = context.get('text', str(context))
                score = context.get('score', None)
            
            sources.append({
                "text": text[:500],  # Limitar a 500 caracteres
                "score": score
            })
        
        return sources

