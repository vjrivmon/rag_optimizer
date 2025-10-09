#!/usr/bin/env python3
"""
Script para limpiar mensajes duplicados en los archivos del proyecto
"""

import os
from pathlib import Path

def clean_file(filepath, replacements):
    """Limpia un archivo aplicando los reemplazos especificados"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content
        for old, new in replacements.items():
            content = content.replace(old, new)

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error procesando {filepath}: {e}")
        return False

# Definir los cambios a realizar
changes = {
    'src/evaluation/ragas_evaluator.py': {
        # Comentar los prints duplicados de thinking tags
        "                print(f\"   ✂️  Filtro de thinking tags: {'ACTIVADO' if filter_thinking_tags else 'DESACTIVADO'}\")":
        "                # print(f\"   ✂️  Filtro de thinking tags: {'ACTIVADO' if filter_thinking_tags else 'DESACTIVADO'}\")",
    },
    'src/optimization/optimizer.py': {
        # Comentar el print duplicado de modelo con thinking
        "            print(f\"   🧠 Modelo con thinking detectado: max_tokens=[1200, 2000]\")":
        "            # print(f\"   🧠 Modelo con thinking detectado: max_tokens=[1200, 2000]\")",
    }
}

print("=" * 60)
print("LIMPIANDO MENSAJES DUPLICADOS")
print("=" * 60)

for filepath, replacements in changes.items():
    full_path = Path(filepath)
    if full_path.exists():
        if clean_file(full_path, replacements):
            print(f"✓ Limpiado: {filepath}")
        else:
            print(f"- Sin cambios: {filepath}")
    else:
        print(f"✗ No encontrado: {filepath}")

print("\n" + "=" * 60)
print("RECOMENDACIONES ADICIONALES:")
print("=" * 60)
print("""
1. Para el benchmark en ejecución:
   - Los warnings de deprecación son normales
   - El filtro de thinking tags SÍ está activado
   - El proceso toma ~3-4 horas en total

2. Cómo verificar que funciona correctamente:
   ✓ Debe mostrar "[1/26]" y procesar cada pregunta
   ✓ Cada modelo debe generar una respuesta
   ✓ Debe aparecer "Evaluating:" con barra de progreso

3. Si quieres menos verbosidad, puedes:
   - Redirigir stderr: python benchmark.py 2>/dev/null
   - O guardar todo: python benchmark.py > benchmark.log 2>&1

4. El benchmark está configurado correctamente con:
   - Vector store v2 (rag_collection_fixed_v2)
   - 79 chunks optimizados
   - Sistema híbrido activado
""")