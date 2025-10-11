"""
Perfiles de Modelos y Estrategias Ensemble
===========================================

Define características, pros/contras y metadata de cada modelo LLM
y estrategia ensemble basados en resultados reales del benchmark.
"""

MODEL_PROFILES = {
    "gemma2:27b": {
        "name": "Gemma 2 27B",
        "provider": "Google",
        "description": "La reina indiscutible del sistema",
        "score": 0.915,
        "correctas": "22/26",
        "pros": [
            "Mejor rendimiento general (91.5%)",
            "Alta consistencia en respuestas",
            "Excelente comprensión de contexto",
            "Rápido y eficiente"
        ],
        "contras": [
            "Ventana de contexto limitada (4096 tokens)",
            "Puede ser muy conciso en ocasiones"
        ],
        "best_for": "Preguntas generales, respuestas precisas y rápidas",
        "color": "#4285F4",
        "logo": "gemma"
    },
    "llama3.3:70b": {
        "name": "Llama 3.3 70B",
        "provider": "Meta",
        "description": "El gigante con razonamiento profundo",
        "score": 0.886,
        "correctas": "21/26",
        "pros": [
            "Excelente capacidad de razonamiento",
            "Respuestas muy detalladas",
            "Buen balance precisión/detalle"
        ],
        "contras": [
            "Más lento (70B parámetros)",
            "Ventana de contexto más pequeña (2048)",
            "Consume más recursos"
        ],
        "best_for": "Preguntas complejas que requieren análisis profundo",
        "color": "#9333EA",
        "logo": "llama"
    },
    "qwen3:32b": {
        "name": "Qwen 3 32B",
        "provider": "Alibaba",
        "description": "Modelo multilingüe versátil",
        "score": 0.850,
        "correctas": "17/26",
        "pros": [
            "Soporte multilingüe nativo",
            "Bueno para contextos diversos",
            "Balance eficiencia/calidad"
        ],
        "contras": [
            "A veces responde en inglés",
            "Menos consistente que Gemma",
            "Problemas con preguntas filosóficas"
        ],
        "best_for": "Preguntas variadas, contextos internacionales",
        "color": "#EF4444",
        "logo": "qwen"
    },
    "deepseek-r1:latest": {
        "name": "DeepSeek R1",
        "provider": "DeepSeek",
        "description": "Especializado en razonamiento step-by-step",
        "score": 0.633,
        "correctas": "10/26",
        "pros": [
            "Muestra proceso de razonamiento",
            "Bueno para debugging",
            "Transparencia en el pensamiento"
        ],
        "contras": [
            "Rendimiento más bajo (63.3%)",
            "Respuestas largas con <think> tags",
            "Menos preciso en general"
        ],
        "best_for": "Cuando quieres ver el proceso de razonamiento",
        "color": "#10B981",
        "logo": "deepseek"
    }
}

ENSEMBLE_PROFILES = {
    "ensemble_voting": {
        "name": "Voting (Votación Mayoritaria)",
        "description": "Selecciona la mejor respuesta por score",
        "score": 0.915,
        "correctas": "22/26",
        "pros": [
            "Empata con el mejor modelo individual",
            "Muy robusto y confiable",
            "Simple y efectivo"
        ],
        "contras": [
            "No mejora sobre Gemma individual",
            "Requiere todos los modelos (más lento)"
        ],
        "best_for": "Máxima confiabilidad, respuestas críticas",
        "how_it_works": "Genera con los 4 modelos y elige la respuesta con mayor combined_score",
        "color": "#F59E0B",
        "logo": "ensemble",
        "icon": "🗳️"
    },
    "ensemble_weighted": {
        "name": "Weighted (Votación Ponderada)",
        "description": "Combina respuestas con pesos por rendimiento",
        "score": 0.913,
        "correctas": "22/26",
        "pros": [
            "Considera rendimiento histórico",
            "Favorece modelos consistentes",
            "Muy cercano al mejor individual"
        ],
        "contras": [
            "Levemente más lento",
            "Pesos fijos (no adaptativos)"
        ],
        "best_for": "Balance entre velocidad y calidad",
        "how_it_works": "Pondera: Gemma 40%, Qwen 30%, Llama 25%, DeepSeek 5%",
        "color": "#8B5CF6",
        "logo": "ensemble",
        "icon": "⚖️"
    },
    "ensemble_routing": {
        "name": "Routing (Enrutamiento Inteligente)",
        "description": "Ruta preguntas a modelos especializados",
        "score": 0.910,
        "correctas": "22/26",
        "pros": [
            "Adaptativo según tipo de pregunta",
            "Configs especiales para P11, P20, P25",
            "Optimizado para casos específicos"
        ],
        "contras": [
            "Más complejo",
            "Requiere clasificación previa"
        ],
        "best_for": "Preguntas variadas, dominio conocido",
        "how_it_works": "Clasifica pregunta y ruta a modelos recomendados según tipo",
        "color": "#06B6D4",
        "logo": "ensemble",
        "icon": "🎯"
    },
    "ensemble_consensus": {
        "name": "Consensus (Consenso con Fallback)",
        "description": "Busca consenso o aplica fallback inteligente",
        "score": 0.909,
        "correctas": "21/26",
        "pros": [
            "Robusto ante respuestas conflictivas",
            "Fallback a Gemma si hay divergencia",
            "Conservador y seguro"
        ],
        "contras": [
            "Puede ser conservador en exceso",
            "Requiere todos los modelos"
        ],
        "best_for": "Preguntas con alta incertidumbre",
        "how_it_works": "Si stdev < 0.15 usa consenso, sino fallback a gemma2:27b",
        "color": "#EC4899",
        "logo": "ensemble",
        "icon": "🤝"
    }
}


def get_all_profiles():
    """Retorna todos los perfiles combinados"""
    return {**MODEL_PROFILES, **ENSEMBLE_PROFILES}


def get_profile(model_key: str):
    """Obtiene perfil de un modelo o estrategia específica"""
    all_profiles = get_all_profiles()
    return all_profiles.get(model_key, None)

