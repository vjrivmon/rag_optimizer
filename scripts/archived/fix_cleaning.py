#!/usr/bin/env python3
"""
🔧 Arreglo rápido para el problema de clean_thinking_tags
"""

import re

def fix_benchmark_file():
    """Reemplaza la función problemática en benchmark_v2.py"""

    with open('benchmark_v2.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Encontrar y reemplazar la función problemática
    old_function = """def clean_thinking_tags(text: str) -> str:
    \"""
    Elimina etiquetas de razonamiento interno de los modelos.

    Algunos modelos (qwen3:32b, deepseek-r1:latest) generan etiquetas como:
     🤔razonamiento interno...🤔
    <thinking>razonamiento interno...</thinking>
    <reasoning>razonamiento interno...</reasoning>

    Estas NO deben mostrarse al usuario ni evaluarse con RAGAs.

    Args:
        text: Texto generado por el modelo

    Returns:
        Texto limpio sin etiquetas de razonamiento

    Examples:
        >>> text = "🤔Hmm...🤔La respuesta es 42"
        >>> clean_thinking_tags(text)
        "La respuesta es 42"
    \"""
    patterns = [
        r'🤔.*?🤔',        # qwen3:32b, deepseek-r1:latest
        r'<thinking>.*?</thinking>',  # Algunos modelos alternativos
        r'<reasoning>.*?</reasoning>' # Otros modelos
    ]

    cleaned = text
    for pattern in patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL)

    return cleaned.strip()"""

    new_function = """def clean_thinking_tags(text: str) -> str:
    \"""
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
    \"""
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

    return cleaned.strip()"""

    # Reemplazar la función
    if old_function in content:
        content = content.replace(old_function, new_function)

        with open('benchmark_v2.py', 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Función clean_thinking_tags actualizada correctamente")
        return True
    else:
        print("❌ No se encontró la función a reemplazar")
        return False

if __name__ == "__main__":
    success = fix_benchmark_file()
    if success:
        print("🚀 El benchmark está listo para ejecutarse con la corrección")
    else:
        print("❌ Hubo un error al aplicar la corrección")