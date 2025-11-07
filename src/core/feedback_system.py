"""
Feedback System - Sistema de Retroalimentación de Usuario
==========================================================

Sistema para recopilar, almacenar y analizar feedback de usuarios sobre las
respuestas del chatbot. Permite mejora continua del sistema RAG.

Características:
- Almacenamiento en JSONL (JSON Lines) para fácil lectura/escritura
- Métricas de satisfacción del usuario
- Identificación de queries problemáticas
- Análisis de tendencias
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class FeedbackEntry:
    """Entrada de feedback del usuario"""
    timestamp: str
    session_id: str
    question: str
    answer: str
    feedback_type: str  # 'positive' o 'negative'
    rating: Optional[int] = None  # 1-5 stars (opcional)
    confidence: Optional[float] = None
    response_time_ms: Optional[int] = None
    model_used: Optional[str] = None
    comment: Optional[str] = None
    response_id: Optional[str] = None


class FeedbackSystem:
    """
    Sistema de gestión de feedback de usuario.
    
    Almacena feedback en formato JSONL para fácil append y lectura.
    Proporciona métricas y análisis de satisfacción del usuario.
    """
    
    def __init__(self, feedback_file: str = "data/feedback.jsonl"):
        """
        Inicializa el sistema de feedback.
        
        Args:
            feedback_file: Ruta al archivo JSONL donde se guardará el feedback
        """
        self.feedback_file = feedback_file
        
        # Crear directorio si no existe
        feedback_path = Path(feedback_file)
        feedback_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Crear archivo si no existe
        if not feedback_path.exists():
            feedback_path.touch()
    
    def add_feedback(
        self,
        session_id: str,
        question: str,
        answer: str,
        feedback_type: str,
        rating: Optional[int] = None,
        confidence: Optional[float] = None,
        response_time_ms: Optional[int] = None,
        model_used: Optional[str] = None,
        comment: Optional[str] = None,
        response_id: Optional[str] = None
    ) -> bool:
        """
        Añade una entrada de feedback al sistema.
        
        Args:
            session_id: ID de la sesión del usuario
            question: Pregunta original
            answer: Respuesta generada
            feedback_type: 'positive' o 'negative'
            rating: Rating de 1-5 estrellas (opcional)
            confidence: Confidence score de la respuesta
            response_time_ms: Tiempo de respuesta en milisegundos
            model_used: Modelo LLM utilizado
            comment: Comentario adicional del usuario
            response_id: ID único de la respuesta
            
        Returns:
            bool: True si se guardó correctamente, False si hubo error
        """
        try:
            # Validar feedback_type
            if feedback_type not in ['positive', 'negative']:
                raise ValueError(f"feedback_type debe ser 'positive' o 'negative', recibido: {feedback_type}")
            
            # Validar rating si se proporciona
            if rating is not None and (rating < 1 or rating > 5):
                raise ValueError(f"rating debe estar entre 1 y 5, recibido: {rating}")
            
            # Crear entrada de feedback
            entry = FeedbackEntry(
                timestamp=datetime.now().isoformat(),
                session_id=session_id,
                question=question,
                answer=answer[:500],  # Limitar a 500 chars para no inflar el archivo
                feedback_type=feedback_type,
                rating=rating,
                confidence=confidence,
                response_time_ms=response_time_ms,
                model_used=model_used,
                comment=comment,
                response_id=response_id
            )
            
            # Guardar en JSONL (append)
            with open(self.feedback_file, 'a', encoding='utf-8') as f:
                json.dump(asdict(entry), f, ensure_ascii=False)
                f.write('\n')
            
            return True
            
        except Exception as e:
            print(f"❌ Error guardando feedback: {e}")
            return False
    
    def load_feedback(self, limit: Optional[int] = None) -> List[FeedbackEntry]:
        """
        Carga todas las entradas de feedback del archivo.
        
        Args:
            limit: Límite de entradas a cargar (None = todas)
            
        Returns:
            List[FeedbackEntry]: Lista de entradas de feedback
        """
        entries = []
        
        try:
            if not os.path.exists(self.feedback_file):
                return entries
            
            with open(self.feedback_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            entry = FeedbackEntry(**data)
                            entries.append(entry)
                            
                            if limit and len(entries) >= limit:
                                break
                        except json.JSONDecodeError:
                            continue  # Skip malformed lines
                        except TypeError:
                            continue  # Skip incompatible data
            
        except Exception as e:
            print(f"❌ Error cargando feedback: {e}")
        
        return entries
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Calcula estadísticas de feedback.
        
        Returns:
            Dict con métricas de feedback:
            - total: Total de feedbacks
            - positive: Número de feedbacks positivos
            - negative: Número de feedbacks negativos
            - positive_rate: Tasa de satisfacción
            - avg_rating: Rating promedio (si hay ratings)
            - avg_confidence: Confidence promedio
            - avg_response_time_ms: Tiempo de respuesta promedio
        """
        entries = self.load_feedback()
        
        if not entries:
            return {
                "total": 0,
                "positive": 0,
                "negative": 0,
                "positive_rate": 0.0,
                "avg_rating": None,
                "avg_confidence": None,
                "avg_response_time_ms": None
            }
        
        total = len(entries)
        positive = sum(1 for e in entries if e.feedback_type == 'positive')
        negative = sum(1 for e in entries if e.feedback_type == 'negative')
        
        # Rating promedio (solo de los que tienen rating)
        ratings = [e.rating for e in entries if e.rating is not None]
        avg_rating = sum(ratings) / len(ratings) if ratings else None
        
        # Confidence promedio
        confidences = [e.confidence for e in entries if e.confidence is not None]
        avg_confidence = sum(confidences) / len(confidences) if confidences else None
        
        # Tiempo de respuesta promedio
        response_times = [e.response_time_ms for e in entries if e.response_time_ms is not None]
        avg_response_time = sum(response_times) / len(response_times) if response_times else None
        
        return {
            "total": total,
            "positive": positive,
            "negative": negative,
            "positive_rate": positive / total if total > 0 else 0.0,
            "avg_rating": round(avg_rating, 2) if avg_rating else None,
            "avg_confidence": round(avg_confidence, 3) if avg_confidence else None,
            "avg_response_time_ms": int(avg_response_time) if avg_response_time else None
        }
    
    def get_problematic_queries(self, min_occurrences: int = 2) -> List[Dict[str, Any]]:
        """
        Identifica queries que han recibido feedback negativo múltiples veces.
        
        Args:
            min_occurrences: Mínimo número de feedbacks negativos para considerar problemática
            
        Returns:
            List de queries problemáticas con estadísticas
        """
        entries = self.load_feedback()
        
        # Agrupar por query
        query_feedback = {}
        
        for entry in entries:
            query_lower = entry.question.lower().strip()
            
            if query_lower not in query_feedback:
                query_feedback[query_lower] = {
                    'query': entry.question,
                    'total': 0,
                    'negative': 0,
                    'positive': 0,
                    'examples': []
                }
            
            query_feedback[query_lower]['total'] += 1
            
            if entry.feedback_type == 'negative':
                query_feedback[query_lower]['negative'] += 1
            else:
                query_feedback[query_lower]['positive'] += 1
            
            # Guardar ejemplos (máximo 3)
            if len(query_feedback[query_lower]['examples']) < 3:
                query_feedback[query_lower]['examples'].append({
                    'answer': entry.answer[:100],
                    'confidence': entry.confidence,
                    'timestamp': entry.timestamp
                })
        
        # Filtrar queries problemáticas
        problematic = []
        
        for query_key, data in query_feedback.items():
            if data['negative'] >= min_occurrences:
                negative_rate = data['negative'] / data['total']
                problematic.append({
                    'query': data['query'],
                    'total_feedback': data['total'],
                    'negative_count': data['negative'],
                    'positive_count': data['positive'],
                    'negative_rate': round(negative_rate, 2),
                    'examples': data['examples']
                })
        
        # Ordenar por tasa de negativos (de mayor a menor)
        problematic.sort(key=lambda x: (x['negative_count'], x['negative_rate']), reverse=True)
        
        return problematic
    
    def get_feedback_by_model(self) -> Dict[str, Dict[str, Any]]:
        """
        Estadísticas de feedback agrupadas por modelo LLM.
        
        Returns:
            Dict con estadísticas por modelo
        """
        entries = self.load_feedback()
        
        model_stats = {}
        
        for entry in entries:
            model = entry.model_used or 'unknown'
            
            if model not in model_stats:
                model_stats[model] = {
                    'total': 0,
                    'positive': 0,
                    'negative': 0,
                    'ratings': [],
                    'confidences': []
                }
            
            model_stats[model]['total'] += 1
            
            if entry.feedback_type == 'positive':
                model_stats[model]['positive'] += 1
            else:
                model_stats[model]['negative'] += 1
            
            if entry.rating:
                model_stats[model]['ratings'].append(entry.rating)
            
            if entry.confidence:
                model_stats[model]['confidences'].append(entry.confidence)
        
        # Calcular promedios
        for model, stats in model_stats.items():
            if stats['total'] > 0:
                stats['positive_rate'] = round(stats['positive'] / stats['total'], 2)
            else:
                stats['positive_rate'] = 0.0
            
            if stats['ratings']:
                stats['avg_rating'] = round(sum(stats['ratings']) / len(stats['ratings']), 2)
            else:
                stats['avg_rating'] = None
            
            if stats['confidences']:
                stats['avg_confidence'] = round(sum(stats['confidences']) / len(stats['confidences']), 3)
            else:
                stats['avg_confidence'] = None
            
            # Limpiar listas innecesarias
            del stats['ratings']
            del stats['confidences']
        
        return model_stats
    
    def export_report(self, output_file: str = "feedback_report.txt"):
        """
        Exporta un reporte de texto con estadísticas de feedback.
        
        Args:
            output_file: Ruta del archivo de reporte
        """
        stats = self.get_stats()
        problematic = self.get_problematic_queries()
        model_stats = self.get_feedback_by_model()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("REPORTE DE FEEDBACK - CHATBOT DNI\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Estadísticas generales
            f.write("ESTADÍSTICAS GENERALES\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total de feedbacks: {stats['total']}\n")
            f.write(f"Feedbacks positivos: {stats['positive']} ({stats['positive_rate']:.1%})\n")
            f.write(f"Feedbacks negativos: {stats['negative']} ({1-stats['positive_rate']:.1%})\n")
            
            if stats['avg_rating']:
                f.write(f"Rating promedio: {stats['avg_rating']:.2f}/5.0 ⭐\n")
            
            if stats['avg_confidence']:
                f.write(f"Confidence promedio: {stats['avg_confidence']:.3f}\n")
            
            if stats['avg_response_time_ms']:
                f.write(f"Tiempo de respuesta promedio: {stats['avg_response_time_ms']}ms\n")
            
            f.write("\n")
            
            # Queries problemáticas
            if problematic:
                f.write("QUERIES PROBLEMÁTICAS\n")
                f.write("-" * 80 + "\n")
                for i, query_data in enumerate(problematic[:10], 1):  # Top 10
                    f.write(f"\n{i}. {query_data['query']}\n")
                    f.write(f"   Negativos: {query_data['negative_count']}/{query_data['total_feedback']} ({query_data['negative_rate']:.0%})\n")
                f.write("\n")
            
            # Estadísticas por modelo
            if model_stats:
                f.write("ESTADÍSTICAS POR MODELO\n")
                f.write("-" * 80 + "\n")
                for model, mstats in model_stats.items():
                    f.write(f"\n{model}:\n")
                    f.write(f"  Total: {mstats['total']}\n")
                    f.write(f"  Tasa positiva: {mstats['positive_rate']:.1%}\n")
                    if mstats['avg_rating']:
                        f.write(f"  Rating promedio: {mstats['avg_rating']:.2f}/5.0\n")
                    if mstats['avg_confidence']:
                        f.write(f"  Confidence promedio: {mstats['avg_confidence']:.3f}\n")
            
            f.write("\n" + "=" * 80 + "\n")
        
        print(f"✅ Reporte exportado a: {output_file}")


if __name__ == "__main__":
    # Testing del sistema de feedback
    feedback = FeedbackSystem()
    
    # Añadir feedback de prueba
    feedback.add_feedback(
        session_id="test_session_1",
        question="¿Qué es DNI?",
        answer="DNI es una asociación de voluntariado...",
        feedback_type="positive",
        rating=5,
        confidence=0.85,
        response_time_ms=2500,
        model_used="gemma2:27b"
    )
    
    feedback.add_feedback(
        session_id="test_session_2",
        question="¿Cómo me apunto?",
        answer="Puedes apuntarte por WhatsApp...",
        feedback_type="positive",
        rating=4,
        confidence=0.72,
        response_time_ms=3000,
        model_used="gemma2:27b"
    )
    
    feedback.add_feedback(
        session_id="test_session_3",
        question="horarios de RESIS",
        answer="No tengo información específica...",
        feedback_type="negative",
        rating=2,
        confidence=0.45,
        response_time_ms=2800,
        model_used="gemma2:27b"
    )
    
    # Mostrar estadísticas
    print("\n=== ESTADÍSTICAS DE FEEDBACK ===\n")
    stats = feedback.get_stats()
    print(f"Total: {stats['total']}")
    print(f"Tasa positiva: {stats['positive_rate']:.1%}")
    print(f"Rating promedio: {stats['avg_rating']}")
    print(f"Confidence promedio: {stats['avg_confidence']}")
    
    print("\n=== QUERIES PROBLEMÁTICAS ===\n")
    problematic = feedback.get_problematic_queries(min_occurrences=1)
    for query in problematic:
        print(f"- {query['query']}: {query['negative_count']} negativos")
    
    print("\n=== FEEDBACK POR MODELO ===\n")
    by_model = feedback.get_feedback_by_model()
    for model, mstats in by_model.items():
        print(f"{model}: {mstats['positive_rate']:.1%} positivos")

