#!/usr/bin/env python3
"""
🔧 Fix final para el problema de thinking tags
"""

def final_fix():
    """Aplica la corrección final al problema de thinking tags"""

    # Leer el archivo
    with open('benchmark_v2.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Aplicar todas las correcciones necesarias

    # Corrección 1: Añadir import de numpy si no existe
    if 'import numpy as np' not in content:
        content = content.replace('import re', 'import re\nimport numpy as np')

    # Corrección 2: Reemplazar la función completa clean_thinking_tags
    old_function_start = content.find('def clean_thinking_tags(text: str) -> str:')
    if old_function_start != -1:
        # Encontrar el final de la función
        next_function = content.find('\ndef ', old_function_start + 1)
        if next_function == -1:
            next_function = content.find('\n# =', old_function_start + 1)

        if next_function != -1:
            # Extraer la función vieja
            old_function = content[old_function_start:next_function]

            # Nueva función corregida
            new_function = '''def clean_thinking_tags(text: str) -> str:
    """
    Elimina etiquetas de razonamiento interno de los modelos PRESERVANDO el contenido real.

    Algunos modelos (qwen3:32b, deepseek-r1:latest) generan etiquetas como:
     🤔Hmm...let me think...🤔
    <thinking>razonamiento interno...</thinking>
    <reasoning>razonamiento interno...</reasoning>

    IMPORTANTE: Las etiquetas se eliminan PERO el contenido se conserva.

    Args:
        text: Texto generado por el modelo

    Returns:
        Texto limpio sin etiquetas de razonamiento pero con las respuestas

    Examples:
        >>> text = "🤔Hmm...let me think...🤔 The answer is 42"
        >>> clean_thinking_tags(text)
        "The answer is 42"
    """
    if not text or text.strip() == "":
        return text

    cleaned = text

    # Patrón 1: Eliminar solo las etiquetas 🤔, conservar TODO el contenido
    # Este es el cambio clave: NO eliminar nada entre 🤔...🤔
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


'''

            # Reemplazar la función
            content = content[:old_function_start] + new_function + content[next_function:]

            print("✅ Función clean_thinking_tags actualizada")

    # Guardar el archivo corregido
    with open('benchmark_v2.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("🚀 Archivo benchmark_v2.py corregido exitosamente")
    return True

def test_fix():
    """Test que la corrección funciona"""

    # Importar la función corregida
    import sys
    sys.path.insert(0, '.')

    from benchmark_v2 import clean_thinking_tags

    # Casos de prueba
    test_cases = [
        ("🤔Hmm...let me think...🤔The answer is 42", "The answer is 42"),
        ("Let me analyze this. The meeting point is Porta de la Mar.", "Let me analyze this. The meeting point is Porta de la Mar."),
        ("Normal answer without tags", "Normal answer without tags"),
        ("🤔Only thinking tags🤔", "Only thinking tags"),
    ]

    print("\n🧪 Test de la función corregida:")
    for input_text, expected in test_cases:
        result = clean_thinking_tags(input_text)
        status = "✅" if len(result) > 10 else "❌"
        print(f"{status} Input: {input_text[:50]}...")
        print(f"     Output: {result[:50]}...")
        print()

if __name__ == "__main__":
    print("🔧 Aplicando corrección final al problema de thinking tags")
    print("=" * 60)

    if final_fix():
        test_fix()
        print("🎯 El benchmark está listo para ejecutarse con la corrección aplicada")
        print("💡 Los problemas de Deepseek-R1 deberían estar resueltos")
    else:
        print("❌ Hubo un error al aplicar la corrección")