def clean_thinking_tags(text: str) -> str:
    """
    Elimina etiquetas de razonamiento interno de los modelos PRESERVANDO el contenido real.

    Algunos modelos (qwen3:32b, deepseek-r1:latest) generan etiquetas como:
     🤔Hmm...let me think...🤔
    <thinking>razonamiento interno...</thinking>
    <reasoning>razonamiento interno...</reasoning>

    Estas etiquetas deben eliminarse PERO el contenido real debe conservarse.

    Args:
        text: Texto generado por el modelo

    Returns:
        Texto limpio sin etiquetas de razonamiento pero conservando las respuestas

    Examples:
        >>> text = "🤔Hmm...let me think...🤔 The answer is 42"
        >>> clean_thinking_tags(text)
        "The answer is 42"
    """
    import re

    if not text or text.strip() == "":
        return text

    cleaned = text

    # Patrón 1: Eliminar solo las etiquetas 🤔, pero conservar el contenido
    # NO eliminar todo entre 🤔...🤔, solo eliminar las etiquetas mismas
    cleaned = re.sub(r'🤔', '', cleaned)  # Eliminar todas las etiquetas 🤔

    # Patrón 2: Eliminar bloques thinking pero conservar contenido antes y después
    # Ejemplo: "Respuesta anterior <thinking>proceso</thinking> respuesta final"
    # Resultado: "Respuesta anterior  respuesta final"
    cleaned = re.sub(r'<thinking>.*?</thinking>', '', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'<reasoning>.*?</reasoning>', '', cleaned, flags=re.DOTALL)

    # Patrón 3: Manejar casos donde el thinking está al inicio
    # Si el texto empieza con thinking, buscar la respuesta real después
    if cleaned.startswith('Hmm') or cleaned.startswith('Let me') or cleaned.startswith('I need'):
        # Buscar el primer punto o respuesta real después del thinking
        sentences = re.split(r'[.!?]+', cleaned, maxsplit=2)
        if len(sentences) > 1 and ('answer' in sentences[1].lower() or 'respuesta' in sentences[1].lower() or len(sentences[1]) > 20):
            # Mantener desde la segunda oración en adelante
            cleaned = '. '.join(sentences[1:]).strip()

    # Patrón 4: Eliminar contenido puramente de thinking al inicio
    # Si después de limpiar, el texto empieza con thinking, buscar contenido real
    thinking_starters = ['Hmm', 'Let me think', 'I need to', 'Let me analyze', 'I think']
    for starter in thinking_starters:
        if cleaned.startswith(starter):
            # Buscar la primera respuesta real después del thinking
            match = re.search(r'(?:Let me think|I need|Hmm).*?[.!?]\s*(.+)', cleaned, re.IGNORECASE | re.DOTALL)
            if match:
                cleaned = match.group(1).strip()
                break

    # Patrón 5: Si todo lo demás falla, buscar cualquier oración con contenido sustancial
    if len(cleaned) < 20:
        # Buscar oraciones que no sean thinking en el texto original
        sentences = re.split(r'[.!?]+', text)
        non_thinking = []
        for sentence in sentences:
            sentence = sentence.strip()
            if (len(sentence) > 15 and
                not any(starter in sentence.lower() for starter in ['hmm', 'let me', 'i need', 'i think', 'razonamiento'])):
                non_thinking.append(sentence)

        if non_thinking:
            cleaned = '. '.join(non_thinking[:2])  # Primeras 2 oraciones no-thinking
        else:
            # Último recurso: devolver el texto original limpiando solo las etiquetas
            cleaned = re.sub(r'🤔', '', text).strip()
            if len(cleaned) < 10:
                cleaned = "[Error: Respuesta eliminada por limpieza de tags thinking]"

    # Limpiar espacios múltiples y espacios al inicio/final
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    return cleaned