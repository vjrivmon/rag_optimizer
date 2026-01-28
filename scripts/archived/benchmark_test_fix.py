#!/usr/bin/env python3
"""
🧪 Test rápido para validar la corrección del problema de thinking tags
"""

import json
import re
from datetime import datetime

def clean_thinking_tags_fixed(text: str) -> str:
    """
    Versión corregida que preserva contenido
    """
    if not text or text.strip() == "":
        return text

    cleaned = text

    # Patrón 1: Eliminar solo las etiquetas 🤔, conservar TODO el contenido
    cleaned = re.sub(r'🤔', '', cleaned)  # Solo eliminar las etiquetas 🤔

    # Patrón 2: Eliminar bloques thinking pero conservar contenido antes y después
    cleaned = re.sub(r'<thinking>.*?</thinking>', '', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'<reasoning>.*?</reasoning>', '', cleaned, flags=re.DOTALL)

    # Patrón 3: Si después de limpiar el texto es muy corto, buscar contenido real
    if len(cleaned.strip()) < 20:
        # Buscar oraciones sustanciales en el texto original
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 15 and not any(word in sentence.lower() for word in ['hmm', 'let me', 'i need']):
                cleaned = sentence
                break

    return cleaned.strip()

def test_problematic_cases():
    """Test casos problemáticos del benchmark"""

    # Casos del benchmark real
    test_cases = [
        {
            "name": "Deepseek-R1 truncado real",
            "input": "🤔Hmm...let me think about this question.🤔",  # Simulación del problema real
            "original_patterns": r'🤔.*?🤔'
        },
        {
            "name": "Deepseek-R1 normal",
            "input": "🤔Hmm...let me think about this.🤔 The activity involves volunteers helping homeless people in Valencia."
        },
        {
            "name": "Qwen3 con thinking",
            "input": "Let me analyze this carefully. The meeting point is Porta de la Mar in Valencia."
        }
    ]

    print("🧪 Test de casos problemáticos del benchmark")
    print("=" * 60)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['name']}")
        print(f"Input: {test_case['input']}")

        # Test con patrón original (problemático)
        original_result = re.sub(test_case.get('original_patterns', r'🤔.*?🤔'), '', test_case['input'], flags=re.DOTALL).strip()
        print(f"Original (🔴): {original_result[:100]}...")

        # Test con función corregida
        fixed_result = clean_thinking_tags_fixed(test_case['input'])
        print(f"Fixed (✅): {fixed_result[:100]}...")

        if len(fixed_result) > len(original_result):
            print("✅ Mejora: Contenido preservado")
        elif len(fixed_result) == len(original_result) and len(fixed_result) > 0:
            print("➖ Sin cambio: Ambos funcionan")
        else:
            print("❌ Problema: Función corregida peor")

def analyze_last_benchmark():
    """Analiza el último benchmark para identificar respuestas truncadas"""

    benchmark_file = "results/benchmark_20251011_000329.json"

    try:
        with open(benchmark_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"\n📊 Análisis del último benchmark: {benchmark_file}")
        print("=" * 60)

        # Buscar respuestas truncadas
        truncated_responses = []
        empty_responses = []
        thinking_responses = []

        for record in data:
            answer = record.get('answer', '')
            model = record.get('model_name', '')
            q_id = record.get('question_id', '')
            score = record.get('metrics', {}).get('combined_score', 0)

            if 'truncada' in answer.lower():
                truncated_responses.append((model, q_id, answer[:50], score))
            elif not answer or answer.strip() == '':
                empty_responses.append((model, q_id, score))
            elif 'thinking' in answer.lower() and len(answer) < 100:
                thinking_responses.append((model, q_id, answer[:50], score))

        print(f"📈 Estadísticas:")
        print(f"  - Respuestas truncadas: {len(truncated_responses)}")
        print(f"  - Respuestas vacías: {len(empty_responses)}")
        print(f"  - Solo thinking: {len(thinking_responses)}")

        if truncated_responses:
            print(f"\n🚨 Respuestas truncadas encontradas:")
            for model, q_id, answer, score in truncated_responses:
                print(f"  - {model} Q{q_id}: '{answer}...' (Score: {score:.3f})")

        if thinking_responses:
            print(f"\n⚠️ Respuestas con solo thinking:")
            for model, q_id, answer, score in thinking_responses[:3]:  # Primeras 3
                print(f"  - {model} Q{q_id}: '{answer}...' (Score: {score:.3f})")

    except FileNotFoundError:
        print(f"❌ No se encuentra el archivo: {benchmark_file}")

def main():
    """Función principal"""
    print("🚀 Análisis y Corrección del Problema de Thinking Tags")
    print("=" * 70)

    # Test de casos problemáticos
    test_problematic_cases()

    # Analizar último benchmark
    analyze_last_benchmark()

    print(f"\n💡 CONCLUSIONES Y RECOMENDACIONES:")
    print("1. El problema principal está en la expresión regex r'🤔.*?🤔'")
    print("2. Esta expresión elimina TODO el contenido entre las etiquetas 🤔...🤔")
    print("3. La corrección es cambiar a r'🤔' para solo eliminar las etiquetas")
    print("4. Deepseek-R1 es el más afectado por este problema")
    print("5. La corrección debe aplicarse inmediatamente a benchmark_v2.py")

if __name__ == "__main__":
    main()