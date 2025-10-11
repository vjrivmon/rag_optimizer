import requests
import time
from typing import Dict, Any, Optional

class LLMWrapper:
    """Wrapper para modelos del servidor UPV"""

    def __init__(
        self,
        model_name: str,
        api_endpoint: str = "https://ollama.gti-ia.upv.es:443/api/generate",
        context_window: int = 2048
    ):
        self.model_name = model_name
        self.api_endpoint = api_endpoint
        self.context_window = context_window

    def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        top_p: float = 0.9,
        max_tokens: int = 512
    ) -> Dict[str, Any]:
        """Genera respuesta usando la API de Ollama del servidor UPV"""

        # Payload según formato Ollama API
        # Convertir a tipos nativos de Python para serialización JSON
        payload = {
            'model': self.model_name,
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': float(temperature),
                'top_p': float(top_p),
                'num_predict': int(max_tokens)
            }
        }

        start_time = time.time()

        try:
            # Usar verify=False para ignorar certificado SSL (-k en curl)
            response = requests.post(
                self.api_endpoint,
                json=payload,
                headers={'Content-Type': 'application/json'},
                verify=False,  # Equivalente a -k en curl
                timeout=300  # 5 minutos para modelos grandes (deepseek-r1, llama3.3:70b)
            )
            response.raise_for_status()

            result = response.json()

            # Ollama devuelve la respuesta en el campo 'response'
            full_response = result.get('response', '')

            # Para modelos con thinking (DeepSeek, Qwen), extraer thinking y respuesta por separado
            thinking = None
            answer = full_response

            # Detectar si la respuesta tiene tags <think>
            if '<think>' in full_response.lower():
                start_think = full_response.lower().find('<think>')
                end_think = full_response.lower().find('</think>')

                if end_think != -1:
                    # Tag completo: <think>...</think>
                    # Extraer thinking y respuesta limpia
                    thinking = full_response[start_think+7:end_think].strip()
                    answer = full_response[end_think+8:].strip()
                else:
                    # Tag sin cerrar (truncado): <think>...
                    # Si hay texto antes del <think>, conservarlo
                    if start_think > 10:  # Al menos 10 chars de texto útil antes
                        answer = full_response[:start_think].strip()
                        thinking = full_response[start_think+7:].strip()
                    else:
                        # Todo es thinking truncado, sin respuesta real
                        # Marcar como error para que RAGAs lo detecte
                        thinking = full_response
                        answer = "[Respuesta truncada - solo thinking]"

            return {
                'response': full_response,  # Respuesta completa (con <think> si existe)
                'answer': answer,  # Solo la respuesta (sin <think>)
                'thinking': thinking,  # Pensamiento de DeepSeek (None para otros modelos)
                'model': self.model_name,
                'latency': time.time() - start_time,
                'success': True,
                'done': result.get('done', False),
                'total_duration': result.get('total_duration', 0)
            }

        except Exception as e:
            return {
                'response': '',
                'model': self.model_name,
                'latency': time.time() - start_time,
                'success': False,
                'error': str(e)
            }
    
    def build_rag_prompt(
        self,
        query: str,
        context: str,
        strictness: str = 'high'
    ) -> str:
        """Construye prompt RAG con forzado de español para Qwen"""
        
        system_prompts = {
            'low': "Eres un asistente útil. Responde usando el contexto proporcionado.",
            'medium': "Eres un asistente RAG. Responde basándote en el contexto. Si la información no está clara, di 'No tengo información suficiente'.",
            'high': "ERES UN ASISTENTE RAG ESTRICTO. SOLO usa información del contexto. Si NO está en el contexto, di 'No tengo esa información'. NO inventes datos."
        }
        
        system = system_prompts.get(strictness, system_prompts['high'])
        
        # FORZAR ESPAÑOL PARA QWEN (problema detectado en chatbot)
        if 'qwen' in self.model_name.lower():
            system += "\n\n⚠️ IMPORTANTE: DEBES responder SIEMPRE en ESPAÑOL. NUNCA respondas en inglés ni otros idiomas."
        
        prompt = f"""{system}

CONTEXTO:
{context}

PREGUNTA: {query}

RESPUESTA:"""
        
        return prompt