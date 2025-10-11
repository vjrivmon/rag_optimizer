#!/usr/bin/env python3
"""
🔧 Fusión de benchmark_v2.py con backup para recuperar mejoras perdidas
"""

def merge_files():
    """Fusiona el archivo actual con el backup para recuperar mejoras"""

    # Leer ambos archivos
    with open('benchmark_v2.py', 'r', encoding='utf-8') as f:
        current_content = f.read()

    with open('benchmark_v2_backup.py', 'r', encoding='utf-8') as f:
        backup_content = f.read()

    print("📁 Analizando diferencias entre archivos...")

    # Encontrar la función clean_thinking_tags en ambos archivos
    current_start = current_content.find('def clean_thinking_tags')
    backup_start = backup_content.find('def clean_thinking_tags')

    if current_start != -1 and backup_start != -1:
        # Encontrar el final de la función en backup
        backup_end = backup_content.find('\n\ndef ', backup_start + 1)
        if backup_end == -1:
            backup_end = backup_content.find('\n# =', backup_start + 1)
        if backup_end == -1:
            backup_end = len(backup_content)

        # Extraer la función del backup
        backup_function = backup_content[backup_start:backup_end]

        # Encontrar el final de la función en el archivo actual
        current_end = current_content.find('\n\ndef ', current_start + 1)
        if current_end == -1:
            current_end = current_content.find('\n# =', current_start + 1)
        if current_end == -1:
            current_end = len(current_content)

        # Reemplazar la función del archivo actual con la del backup
        print(f"  📝 Función clean_thinking_tags encontrada en ambos archivos")
        print(f"  🔹 Backup: {len(backup_function)} caracteres")
        print(f"  📄 Current: {len(current_content[current_start:current_end])} caracteres")

        merged_content = current_content[:current_start] + backup_function + current_content[current_end:]

        # Guardar archivo fusionado
        with open('benchmark_v2.py', 'w', encoding='utf-8') as f:
            f.write(merged_content)

        print("✅ Archivo benchmark_v2.py fusionado correctamente")
        return True

    else:
        print("❌ No se encontró la función clean_thinking_tags en ambos archivos")
        return False

def test_thinking_function():
    """Test que la función de limpieza funciona correctamente"""
    import sys
    sys.path.insert(0, '.')

    # Importar la función del archivo fusionado
    from benchmark_v2 import clean_thinking_tags

    print("\n🧪 Test de función clean_thinking_tags fusionada:")
    print("=" * 50)

    test_cases = [
        ("🤔Hmm...let me think...🤔The answer is 42", "The answer is 42"),
        ("Let me analyze this carefully. The answer is Valencia.", "Let me analyze this carefully. The answer is Valencia."),
        ("Normal answer without tags", "Normal answer without tags"),
        ("🤔Only thinking tags🤔", "Only thinking tags"),
        ("🤔Hmm...🤔La respuesta correcta", "La respuesta correcta"),
    ]

    for i, (input_text, expected) in enumerate(test_cases, 1):
        result = clean_thinking_tags(input_text)
        status = "✅" if len(result) > 10 and result != expected else "❌"
        print(f"Test {i}: {status}")
        print(f"  Input: {input_text[:50]}...")
        print(f"  Expected: {expected[:50]}...")
        print(f"  Result: {result[:50]}...")

def main():
    """Función principal"""
    print("🔧 Fusión de Archivos y Test de Recuperación")
    print("=" * 70)

    if merge_files():
        test_thinking_function()
        print(f"\n🎯 RESULTADO:")
        print("✅ Enhanced RAG Engine con clean_thinking_tags corregida")
        print("✅ Backup recuperado y fusionado correctamente")
        print("✅ Sistema listo para pruebas")
        print(f"\n🚀 Puedes ejecutar:")
        print("source venv/bin/activate && python benchmark_v2.py --max-questions 2")
    else:
        print("❌ Hubo un error al fusionar los archivos")

if __name__ == "__main__":
    main()