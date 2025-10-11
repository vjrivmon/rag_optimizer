#!/usr/bin/env python3
"""
📤 Exportador de Resultados - Compatible con app_advanced.py

Convierte la base de datos SQLite del benchmark_v2.py al formato JSON
que espera la aplicación de Streamlit.

USO:
  python export_to_streamlit.py
  
  O se ejecuta automáticamente al finalizar benchmark_v2.py
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List


def export_benchmark_to_streamlit_format(db_path: str = "results/benchmark.db",
                                         output_dir: str = "results") -> str:
    """
    Exporta los resultados del benchmark al formato esperado por app_advanced.py
    
    Returns:
        str: Ruta del archivo JSON generado
    """
    
    conn = sqlite3.connect(db_path)
    
    # Obtener metadata
    cursor = conn.execute("""
        SELECT 
            COUNT(DISTINCT question_id) as total_questions,
            COUNT(DISTINCT model_name) as total_models,
            GROUP_CONCAT(DISTINCT model_name) as models
        FROM responses
        WHERE error IS NULL
    """)
    meta_row = cursor.fetchone()
    total_questions = meta_row[0]
    models_list = meta_row[2].split(',') if meta_row[2] else []
    
    # Calcular tiempo total (suma de generation + evaluation)
    cursor = conn.execute("""
        SELECT 
            SUM(r.generation_time) + COALESCE(SUM(e.evaluation_time), 0) as total_time
        FROM responses r
        LEFT JOIN evaluations e ON r.id = e.response_id
        WHERE r.error IS NULL
    """)
    total_time = cursor.fetchone()[0] or 0
    
    # Construir resultados por pregunta
    results = []
    
    cursor = conn.execute("""
        SELECT DISTINCT question_id, question
        FROM responses
        WHERE error IS NULL
        ORDER BY question_id
    """)
    
    questions = cursor.fetchall()
    
    for question_id, question_text in questions:
        # Obtener contextos (tomamos los del primer modelo)
        cursor_ctx = conn.execute("""
            SELECT contexts
            FROM responses
            WHERE question_id = ? AND error IS NULL
            LIMIT 1
        """, (question_id,))
        
        contexts_row = cursor_ctx.fetchone()
        contexts = json.loads(contexts_row[0]) if contexts_row else []
        
        # Obtener respuestas de cada modelo
        models_data = {}
        best_score = -1
        winner = None
        
        for model_name in models_list:
            # Obtener respuesta y evaluación
            cursor_model = conn.execute("""
                SELECT 
                    r.answer,
                    r.generation_time,
                    e.combined_score,
                    e.faithfulness,
                    e.answer_relevancy,
                    e.context_precision,
                    e.context_recall,
                    e.answer_correctness,
                    e.answer_similarity
                FROM responses r
                LEFT JOIN evaluations e ON r.id = e.response_id
                WHERE r.question_id = ? AND r.model_name = ? AND r.error IS NULL
            """, (question_id, model_name))
            
            model_row = cursor_model.fetchone()
            
            if model_row:
                answer = model_row[0]
                latency = model_row[1]
                combined_score = model_row[2] if model_row[2] else 0
                
                # Determinar ganador
                if combined_score > best_score:
                    best_score = combined_score
                    winner = model_name
                
                # Construir métricas
                metrics = {
                    'combined_score': round(combined_score, 4) if combined_score else 0,
                    'faithfulness': round(model_row[3], 4) if model_row[3] else 0,
                    'answer_relevancy': round(model_row[4], 4) if model_row[4] else 0,
                    'context_precision': round(model_row[5], 4) if model_row[5] else 0,
                    'context_recall': round(model_row[6], 4) if model_row[6] else 0,
                    'answer_correctness': round(model_row[7], 4) if model_row[7] else 0,
                    'answer_similarity': round(model_row[8], 4) if model_row[8] else 0,
                    'response_length': len(answer),
                    'context_overlap': 0.0  # Placeholder, puedes calcularlo si quieres
                }
                
                models_data[model_name] = {
                    'success': True,
                    'score': round(combined_score, 4) if combined_score else 0,
                    'latency': round(latency, 2),
                    'response': answer,
                    'params': {},  # Placeholder para parámetros si los quieres añadir
                    'metrics': metrics
                }
        
        # Añadir resultado de esta pregunta
        results.append({
            'question_id': question_id,
            'question': question_text,
            'expected_answer': '',  # No tenemos ground truth en el nuevo sistema
            'contexts': contexts,
            'winner': winner,
            'models': models_data
        })
    
    conn.close()
    
    # Construir objeto final
    output = {
        'metadata': {
            'total_questions': total_questions,
            'total_time': round(total_time, 2),
            'models': models_list,
            'timestamp': datetime.now().isoformat(),
            'version': '2.0'
        },
        'results': results
    }
    
    # Guardar archivo
    Path(output_dir).mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = f"{output_dir}/benchmark_{timestamp}.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    return output_path


if __name__ == "__main__":
    import sys
    
    db_path = sys.argv[1] if len(sys.argv) > 1 else "results/benchmark.db"
    
    print("📤 Exportando resultados a formato Streamlit...")
    print(f"   Base de datos: {db_path}")
    
    try:
        output_path = export_benchmark_to_streamlit_format(db_path)
        print(f"✅ Exportado correctamente: {output_path}")
        print(f"\n💡 Ahora puedes usar: streamlit run app_advanced.py")
    except Exception as e:
        print(f"❌ Error al exportar: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
