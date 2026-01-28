"""
Intent Classifier - Clasificación de Intents de Usuario
========================================================

Clasifica mensajes del usuario en intents específicos:
- greeting: Saludos (hola, buenos días, etc.)
- goodbye: Despedidas (adiós, hasta luego, etc.)
- thanks: Agradecimientos (gracias, etc.)
- help: Solicitudes de ayuda (ayuda, opciones, menú)
- question: Preguntas complejas que requieren RAG

Basado en el documento 13_mensajes_genericos.txt para respuestas predefinidas.
"""

import re
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class IntentResult:
    """Resultado de clasificación de intent"""
    intent: str
    confidence: float
    predefined_response: Optional[str] = None


class IntentClassifier:
    """
    Clasificador de intents basado en regex patterns.
    
    Proporciona clasificación rápida para mensajes genéricos comunes,
    permitiendo respuestas instantáneas sin necesidad de RAG.
    """
    
    def __init__(self):
        """Inicializa el clasificador con patterns y respuestas predefinidas"""
        
        # Patterns de detección por intent
        self.patterns = {
            'greeting': [
                r'\b(hola|hey|buenas?|buenos? días|buenos? tardes|buenas? noches|hi|hello|saludos?)\b',
                r'^hola\b',
                r'^hey\b',
                r'^buenos?\s+días?\b',
            ],
            'goodbye': [
                r'\b(adiós|adios|chao|chau|hasta luego|hasta pronto|bye|nos vemos|me voy)\b',
                r'^adiós?\b',
                r'^chao\b',
                r'^hasta\s+(luego|pronto)\b',
            ],
            'thanks': [
                r'\b(gracias|muchas gracias|mil gracias|thanks|thank you|agradec)',
                r'^gracias\b',
                r'^muchas gracias\b',
            ],
            'help': [
                # Excluir "PARA.MIRA.AYUDA" específicamente - eso debe ir al RAG
                r'^(?!.*para\.?\s*mira\.?\s*ayuda)(ayuda|help|opciones|menú|menu|info|información|que puedes hacer|qué puedes hacer)\b',
                r'^ayuda$',  # Solo "ayuda" exacto, no parte de frase
                r'^help$',
                r'^info$',
                r'^\?+$',  # Solo signos de interrogación
            ],
        }
        
        # Respuestas predefinidas (basadas en 13_mensajes_genericos.txt)
        self.predefined_responses = {
            'greeting': """¡Hola! 👋 Soy el asistente virtual de DNI (Damos Nuestra Ilusión). Estoy aquí para ayudarte con información sobre nuestros proyectos de voluntariado. ¿En qué puedo ayudarte?""",
            
            'goodbye': """¡Hasta pronto! 💙 Recuerda que puedes contactarnos cuando quieras por WhatsApp (962 025 978 / 647 440 275) o Instagram [@dnivalenciaa](https://www.instagram.com/dnivalenciaa?igsh=MWRicTFocW5jODN6NQ==). ¡Esperamos verte en nuestras actividades! 🌟""",
            
            'thanks': """¡De nada! 😊 Si tienes más preguntas sobre DNI o nuestros proyectos, aquí estoy. ¡Esperamos verte pronto en nuestras actividades! 💙""",
            
            'help': """Puedo ayudarte con información sobre:

• **¿Qué es DNI?** - Nuestra filosofía y valores
• **Proyectos** - Desayunos solidarios, residencias, refuerzo escolar
• **Cómo participar** - Requisitos, cómo apuntarse, contacto
• **Horarios y ubicaciones** - Cuándo y dónde son las actividades
• **Contacto** - WhatsApp, Instagram, donaciones

¿Sobre qué te gustaría saber más?"""
        }
    
    def classify(self, message: str) -> IntentResult:
        """
        Clasifica un mensaje en un intent específico.
        
        Args:
            message: Mensaje del usuario a clasificar
            
        Returns:
            IntentResult con intent, confidence y respuesta predefinida (si aplica)
        """
        # Normalizar mensaje
        msg = message.lower().strip()
        
        # Si el mensaje está vacío
        if not msg:
            return IntentResult(
                intent='question',
                confidence=0.0,
                predefined_response=None
            )
        
        # Detectar mensajes muy cortos (probabilidades de ser genéricos)
        if len(msg) <= 15:
            # Buscar matches exactos o muy cercanos para mensajes cortos
            for intent, patterns in self.patterns.items():
                for pattern in patterns:
                    if re.search(pattern, msg, re.IGNORECASE):
                        return IntentResult(
                            intent=intent,
                            confidence=0.95,  # Alta confianza para matches cortos
                            predefined_response=self.predefined_responses.get(intent)
                        )
        
        # Para mensajes más largos, buscar patterns en todo el texto
        intent_scores = {}
        
        for intent, patterns in self.patterns.items():
            matches = 0
            for pattern in patterns:
                if re.search(pattern, msg, re.IGNORECASE):
                    matches += 1
            
            if matches > 0:
                # Confianza basada en número de matches
                confidence = min(0.7 + (matches * 0.1), 0.95)
                intent_scores[intent] = confidence
        
        # Si encontramos algún intent
        if intent_scores:
            # Obtener intent con mayor confianza
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            intent_name, confidence = best_intent
            
            return IntentResult(
                intent=intent_name,
                confidence=confidence,
                predefined_response=self.predefined_responses.get(intent_name)
            )
        
        # Si no encontramos ningún intent genérico, es una pregunta para RAG
        return IntentResult(
            intent='question',
            confidence=0.5,  # Confianza media para questions
            predefined_response=None
        )
    
    def is_generic_message(self, message: str) -> bool:
        """
        Determina rápidamente si un mensaje es genérico (no necesita RAG).
        
        Args:
            message: Mensaje a evaluar
            
        Returns:
            True si el mensaje es genérico, False si necesita RAG
        """
        result = self.classify(message)
        return result.intent != 'question' and result.confidence > 0.7
    
    def get_response(self, message: str) -> Tuple[str, str, float]:
        """
        Obtiene respuesta directa para un mensaje (si es genérico).
        
        Args:
            message: Mensaje del usuario
            
        Returns:
            Tuple de (intent, response, confidence)
            Si intent es 'question', response será None
        """
        result = self.classify(message)
        
        return (
            result.intent,
            result.predefined_response,
            result.confidence
        )


# Función helper para uso directo
def classify_intent(message: str) -> Tuple[str, float]:
    """
    Función helper para clasificar un mensaje rápidamente.
    
    Args:
        message: Mensaje a clasificar
        
    Returns:
        Tuple de (intent, confidence)
    """
    classifier = IntentClassifier()
    result = classifier.classify(message)
    return (result.intent, result.confidence)


if __name__ == "__main__":
    # Testing del clasificador
    classifier = IntentClassifier()
    
    test_messages = [
        "hola",
        "buenos días",
        "¿Qué es DNI?",
        "gracias",
        "adiós",
        "ayuda",
        "¿Cómo me apunto a desayunos solidarios?",
        "info",
        "hasta luego",
        "¿Cuándo son las actividades con abuelitos?",
    ]
    
    print("=== TESTING INTENT CLASSIFIER ===\n")
    
    for msg in test_messages:
        result = classifier.classify(msg)
        print(f"Mensaje: '{msg}'")
        print(f"  Intent: {result.intent}")
        print(f"  Confidence: {result.confidence:.2f}")
        if result.predefined_response:
            preview = result.predefined_response[:80].replace('\n', ' ')
            print(f"  Response: {preview}...")
        print()

