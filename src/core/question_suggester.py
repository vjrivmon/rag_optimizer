"""
Question Suggester - Sistema de Sugerencias de Preguntas
=========================================================

Analiza el contexto de la última respuesta y sugiere preguntas relacionadas
que el usuario podría estar interesado en hacer.

Estrategias:
1. Basado en categoría del contexto recuperado
2. Preguntas frecuentes del dataset
3. Análisis de keywords en la respuesta
4. Sugerencias contextuales inteligentes
"""

import random
from typing import List, Dict, Any, Optional


class QuestionSuggester:
    """
    Sistema para sugerir preguntas relevantes al usuario.
    
    Analiza la respuesta actual y el contexto para proporcionar
    3 sugerencias de preguntas relacionadas.
    """
    
    def __init__(self):
        """Inicializa el suggester con preguntas predefinidas por categoría"""
        
        # Preguntas sugeridas por categoría (expandidas y personalizadas)
        self.category_suggestions = {
            'desayunos': [
                "¿Cuándo son los desayunos solidarios?",
                "¿Dónde quedamos para los desayunos?",
                "¿Qué se hace en el voluntariado de desayunos?",
                "¿Cómo me apunto a desayunos?",
                "¿Puedo ir con mis amigos a desayunos?",
                "¿Hace falta experiencia previa?",
                "¿Cuánto dura cada reparto?",
                "¿Qué pasa si llueve?",
                "¿Dónde es el punto de encuentro?",
                "¿Qué comida se reparte?",
                "¿A qué hora nos encontramos?",
                "¿Puedo ir solo o acompañado?",
                "¿Con qué frecuencia son los desayunos?",
                "¿Qué diferencia hay entre desayunos y cenas solidarias?",
                "¿Hay que comprometerse todas las semanas?",
            ],
            'coles': [
                "¿Qué se hace en refuerzo escolar?",
                "¿Dónde es el refuerzo escolar?",
                "¿Qué días vais a COLES?",
                "¿Necesito ser bueno en matemáticas?",
                "¿Qué edad tienen los niños?",
                "¿Hay que comprometerse mucho tiempo?",
                "¿Cuánto tiempo se necesita por sesión?",
                "¿Qué asignaturas se imparten?",
                "¿Hace falta formación previa en educación?",
                "¿Puedo ayudar si soy de ciencias?",
                "¿Cómo es el ambiente en COLES?",
            ],
            'resis': [
                "¿Qué hacemos con los abuelitos?",
                "¿Cuándo son las visitas a la residencia?",
                "¿Dónde está la residencia L'Acollida?",
                "¿Qué actividades se hacen con los ancianos?",
                "¿Puedo ir solo o acompañado?",
                "¿Cómo llego a la residencia?",
                "¿Qué días vais a la residencia?",
                "¿Cuánto tiempo duran las visitas?",
                "¿Hace falta experiencia con personas mayores?",
                "¿Qué tipo de conversaciones se tienen?",
                "¿Hay que comprometerse a ir todas las semanas?",
            ],
            'general': [
                "¿Qué es DNI?",
                "¿Cuál es la filosofía de DNI?",
                "¿Qué proyectos tiene DNI?",
                "¿Cómo puedo unirme a DNI?",
                "¿Qué requisitos necesito?",
                "¿Es gratis participar?",
                "¿Hay límite de edad?",
                "¿Qué significa PARA. MIRA. AYUDA.?",
                "¿Cuántos voluntarios tiene DNI?",
                "¿DNI es una organización religiosa?",
                "¿Desde cuándo existe DNI?",
                "¿Qué diferencia a DNI de otras ONG?",
                "¿Cómo se financia DNI?",
                "¿Puedo proponer nuevos proyectos?",
                "¿Necesito experiencia previa?",
            ],
            'contacto': [
                "¿Cómo puedo contactar con DNI?",
                "¿Tenéis Instagram?",
                "¿Cuál es el WhatsApp de DNI?",
                "¿Dónde puedo ver fotos de las actividades?",
                "¿Cómo puedo donar a DNI?",
                "¿DNI tiene redes sociales?",
                "¿Hay algún correo electrónico?",
                "¿Tenéis oficina física?",
                "¿Cómo sigo las novedades de DNI?",
                "¿Puedo colaborar si soy una empresa?",
            ],
            'horarios': [
                "¿Cuándo son las actividades?",
                "¿A qué hora son los desayunos?",
                "¿Qué días vais a la residencia?",
                "¿Cuánto dura cada actividad?",
                "¿Hay transporte organizado?",
                "¿Las actividades son siempre en Valencia?",
                "¿Cómo me entero de las próximas actividades?",
            ]
        }
        
        # Keywords que indican cada categoría
        self.category_keywords = {
            'desayunos': ['desayuno', 'cena', 'solidari', 'reparto', 'comida', 'bocadillo', 'café', 'persona sin hogar', 'calle'],
            'coles': ['coles', 'refuerzo', 'escolar', 'niños', 'ceip', 'deberes', 'estudio', 'biblioteca', 'tutorizado'],
            'resis': ['resis', 'residencia', 'acollida', 'abuelito', 'anciano', 'mayores', 'charlas', 'miércoles'],
            'contacto': ['contacto', 'whatsapp', 'instagram', 'teléfono', 'redes', 'donar', 'colaborar'],
            'horarios': ['horario', 'cuándo', 'hora', 'día', 'fecha', 'ubicación', 'dónde'],
            'general': ['dni', 'voluntariado', 'proyecto', 'actividad', 'requisito', 'para mira ayuda', 'ilusión']
        }
        
        # Sugerencias genéricas (siempre relevantes)
        self.generic_suggestions = [
            "¿Cómo puedo unirme a DNI?",
            "¿Qué proyectos tenéis?",
            "¿Cuándo son las actividades?",
            "¿Dónde puedo ver más información?",
            "¿Es necesario experiencia previa?",
            "¿Hay que pagar algo?",
        ]
    
    def detect_category(self, text: str) -> str:
        """
        Detecta la categoría predominante en un texto.
        
        Args:
            text: Texto a analizar (respuesta o contexto)
            
        Returns:
            Nombre de la categoría detectada
        """
        text_lower = text.lower()
        
        # Contar matches por categoría
        category_scores = {}
        
        for category, keywords in self.category_keywords.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > 0:
                category_scores[category] = matches
        
        # Retornar categoría con más matches
        if category_scores:
            return max(category_scores.items(), key=lambda x: x[1])[0]
        
        return 'general'
    
    def suggest_questions(
        self,
        last_answer: str,
        contexts: Optional[List[str]] = None,
        last_question: Optional[str] = None,
        asked_questions: Optional[List[str]] = None,
        num_suggestions: int = 3
    ) -> List[str]:
        """
        Genera sugerencias de preguntas basadas en la última interacción.

        Args:
            last_answer: Última respuesta generada
            contexts: Contextos recuperados (chunks)
            last_question: Última pregunta del usuario
            asked_questions: Lista de preguntas ya hechas por el usuario (NUEVO)
            num_suggestions: Número de sugerencias a generar

        Returns:
            Lista de preguntas sugeridas
        """
        suggestions = []
        used_questions = set()

        # Normalizar preguntas ya hechas para comparación
        if asked_questions is None:
            asked_questions = []

        # Crear set de preguntas ya hechas (normalizadas para comparación)
        asked_normalized = set(self._normalize_question(q) for q in asked_questions)

        # 1. Detectar categoría de la respuesta
        if last_answer:
            answer_category = self.detect_category(last_answer)
        else:
            answer_category = 'general'

        # 2. Si hay contextos, también detectar categoría del contexto
        context_category = None
        if contexts:
            combined_context = " ".join(contexts[:3])
            context_category = self.detect_category(combined_context)

        # 3. Detectar categoría de la pregunta
        question_category = None
        if last_question:
            question_category = self.detect_category(last_question)

        # 4. Priorizar categorías (contexto > respuesta > pregunta)
        primary_category = context_category or answer_category or question_category or 'general'

        # 5. Obtener sugerencias de la categoría primaria
        if primary_category in self.category_suggestions:
            category_questions = self.category_suggestions[primary_category].copy()
            random.shuffle(category_questions)

            for q in category_questions:
                # NUEVO: Verificar que no sea similar a preguntas ya hechas
                if (q not in used_questions and
                    q != last_question and
                    not self._is_question_already_asked(q, asked_normalized)):
                    suggestions.append(q)
                    used_questions.add(q)
                    if len(suggestions) >= num_suggestions:
                        return suggestions

        # 6. Si la categoría primaria no dio suficientes, probar categorías relacionadas
        related_categories = self._get_related_categories(primary_category)

        for category in related_categories:
            if len(suggestions) >= num_suggestions:
                break

            if category in self.category_suggestions:
                category_questions = self.category_suggestions[category].copy()
                random.shuffle(category_questions)

                for q in category_questions:
                    # NUEVO: Verificar que no sea similar a preguntas ya hechas
                    if (q not in used_questions and
                        q != last_question and
                        not self._is_question_already_asked(q, asked_normalized)):
                        suggestions.append(q)
                        used_questions.add(q)
                        if len(suggestions) >= num_suggestions:
                            break

        # 7. Si aún faltan sugerencias, añadir genéricas
        if len(suggestions) < num_suggestions:
            generic_shuffled = self.generic_suggestions.copy()
            random.shuffle(generic_shuffled)

            for q in generic_shuffled:
                # NUEVO: Verificar que no sea similar a preguntas ya hechas
                if (q not in used_questions and
                    q != last_question and
                    not self._is_question_already_asked(q, asked_normalized)):
                    suggestions.append(q)
                    used_questions.add(q)
                    if len(suggestions) >= num_suggestions:
                        break

        return suggestions[:num_suggestions]
    
    def _normalize_question(self, question: str) -> str:
        """
        Normaliza una pregunta para comparación.
        Elimina signos de puntuación, convierte a minúsculas, y elimina palabras comunes.

        Args:
            question: Pregunta a normalizar

        Returns:
            Pregunta normalizada
        """
        import re

        # Convertir a minúsculas
        normalized = question.lower().strip()

        # Eliminar signos de puntuación
        normalized = re.sub(r'[¿?¡!.,;:]', '', normalized)

        # Palabras comunes a ignorar (stopwords básicas)
        stopwords = {'el', 'la', 'los', 'las', 'un', 'una', 'de', 'del', 'en', 'a', 'al', 'por', 'para', 'con', 'es', 'son'}
        words = [w for w in normalized.split() if w not in stopwords]

        return ' '.join(words)

    def _is_question_already_asked(self, candidate: str, asked_normalized: set) -> bool:
        """
        Verifica si una pregunta candidata ya fue hecha por el usuario.
        Usa normalización y similitud aproximada.

        Args:
            candidate: Pregunta candidata a verificar
            asked_normalized: Set de preguntas ya hechas (normalizadas)

        Returns:
            True si la pregunta ya fue hecha o es muy similar
        """
        candidate_norm = self._normalize_question(candidate)

        # Verificación exacta (después de normalización)
        if candidate_norm in asked_normalized:
            return True

        # Verificación de similitud aproximada (palabras compartidas)
        candidate_words = set(candidate_norm.split())

        for asked in asked_normalized:
            asked_words = set(asked.split())

            # Si comparten el 80% o más de las palabras, considerarlas duplicadas
            if candidate_words and asked_words:
                overlap = len(candidate_words & asked_words)
                similarity = overlap / min(len(candidate_words), len(asked_words))

                if similarity >= 0.8:  # 80% de similitud = duplicada
                    return True

        return False

    def _get_related_categories(self, category: str) -> List[str]:
        """
        Retorna categorías relacionadas a una categoría dada.

        Args:
            category: Categoría principal

        Returns:
            Lista de categorías relacionadas
        """
        # Mapeo de categorías relacionadas
        related_map = {
            'desayunos': ['horarios', 'contacto', 'general'],
            'coles': ['horarios', 'contacto', 'general'],
            'resis': ['horarios', 'contacto', 'general'],
            'general': ['desayunos', 'coles', 'resis', 'contacto'],
            'contacto': ['general', 'desayunos', 'coles', 'resis'],
            'horarios': ['desayunos', 'coles', 'resis', 'contacto'],
        }

        return related_map.get(category, ['general'])
    
    def suggest_from_intent(self, intent: str) -> List[str]:
        """
        Genera sugerencias basadas en un intent específico.
        
        Args:
            intent: Intent del mensaje (greeting, help, question, etc.)
            
        Returns:
            Lista de preguntas sugeridas
        """
        if intent in ['greeting', 'help']:
            # Para saludos, sugerir preguntas introductorias
            return [
                "¿Qué es DNI?",
                "¿Qué proyectos tenéis?",
                "¿Cómo puedo unirme?",
            ]
        elif intent == 'thanks':
            # Para agradecimientos, sugerir explorar más
            return [
                "¿Hay más actividades?",
                "¿Cuándo son los próximos eventos?",
                "¿Cómo puedo contactaros?",
            ]
        else:
            # Default: sugerencias generales
            return random.sample(self.generic_suggestions, min(3, len(self.generic_suggestions)))


if __name__ == "__main__":
    # Testing del suggester
    suggester = QuestionSuggester()
    
    print("=== TESTING QUESTION SUGGESTER ===\n")
    
    # Test 1: Respuesta sobre desayunos
    print("Test 1: Respuesta sobre desayunos solidarios")
    answer1 = "Los desayunos solidarios se realizan casi todas las semanas en zona centro de Valencia. Preparamos bocadillos, café, zumo..."
    suggestions1 = suggester.suggest_questions(answer1)
    print("Sugerencias:")
    for i, q in enumerate(suggestions1, 1):
        print(f"  {i}. {q}")
    print()
    
    # Test 2: Respuesta sobre refuerzo escolar
    print("Test 2: Respuesta sobre COLES")
    answer2 = "En actividades de refuerzo escolar vamos a un colegio a ayudar a niños con sus deberes..."
    contexts2 = ["CEIP Antonio Ferrandis", "refuerzo escolar", "niños primaria"]
    suggestions2 = suggester.suggest_questions(answer2, contexts2)
    print("Sugerencias:")
    for i, q in enumerate(suggestions2, 1):
        print(f"  {i}. {q}")
    print()
    
    # Test 3: Intent greeting
    print("Test 3: Intent greeting")
    suggestions3 = suggester.suggest_from_intent('greeting')
    print("Sugerencias:")
    for i, q in enumerate(suggestions3, 1):
        print(f"  {i}. {q}")
    print()
    
    # Test 4: Categoría general
    print("Test 4: Respuesta general sobre DNI")
    answer4 = "DNI es una asociación de voluntariado juvenil en Valencia con más de 400 voluntarios activos..."
    suggestions4 = suggester.suggest_questions(answer4)
    print("Sugerencias:")
    for i, q in enumerate(suggestions4, 1):
        print(f"  {i}. {q}")
    print()
    
    print("✅ Testing completado")

