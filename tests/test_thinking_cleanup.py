from src.core.model_wrapper import LLMWrapper

# Simular respuesta truncada de qwen3:32b (solo thinking, sin cierre)
truncated_response = "<think>\nOkay, the user is asking for a"

# Test de extracción
wrapper = LLMWrapper("qwen3:32b", "https://ollama.gti-ia.upv.es:443/api/generate")

# Simular el procesamiento manual
full_response = truncated_response
thinking = None
answer = full_response

if '<think>' in full_response.lower():
    start_think = full_response.lower().find('<think>')
    end_think = full_response.lower().find('</think>')
    
    print(f"start_think: {start_think}")
    print(f"end_think: {end_think}")
    
    if end_think != -1:
        # Tag completo
        thinking = full_response[start_think+7:end_think].strip()
        answer = full_response[end_think+8:].strip()
        print(f"Caso 1: Tag completo")
    else:
        # Tag sin cerrar (truncado)
        if start_think > 10:
            answer = full_response[:start_think].strip()
            thinking = full_response[start_think+7:].strip()
            print(f"Caso 2: Tag sin cerrar, texto antes del think")
        else:
            # Todo es thinking truncado
            thinking = full_response
            answer = "[Respuesta truncada - solo thinking]"
            print(f"Caso 3: Solo thinking truncado")

print(f"\nAnswer: '{answer}'")
print(f"Thinking: '{thinking}'")
