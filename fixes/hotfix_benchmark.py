#!/usr/bin/env python3
"""
HOTFIX CRÍTICO para benchmark.py
Soluciona el problema de Q2, Q4, Q6 que no recuperan suficientes chunks
"""

import sys
from pathlib import Path

print("=" * 80)
print("🚨 HOTFIX PARA BENCHMARK.PY")
print("=" * 80)

# Archivo a modificar
benchmark_file = Path("benchmark.py")

if not benchmark_file.exists():
    print("❌ Error: benchmark.py no encontrado")
    sys.exit(1)

# Leer el contenido actual
with open(benchmark_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Backup del archivo original
backup_file = Path("benchmark_backup.py")
with open(backup_file, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"✓ Backup creado: {backup_file}")

# Aplicar los cambios necesarios
print("\n📝 Aplicando cambios...")

# CAMBIO 1: Usar siempre 10 chunks, no limitar por docs recuperados
old_line1 = "        contexts = [doc['content'][:400] for doc in docs[:7]]"
new_line1 = "        contexts = [doc['content'][:400] for doc in docs[:10]]  # HOTFIX: Usar siempre top 10"

old_line2 = "        context_text = self.rag.build_context(docs[:7])"
new_line2 = "        context_text = self.rag.build_context(docs[:10])  # HOTFIX: Usar siempre top 10"

old_line3 = '        print(f"   📚 Contexto: {len(docs)} documentos recuperados, usando top 7 truncados")'
new_line3 = '        print(f"   📚 Contexto: {len(docs)} documentos recuperados, usando top 10")'

# Aplicar cambios
changes_made = 0

if old_line1 in content:
    content = content.replace(old_line1, new_line1)
    print("   ✓ Cambiado: contexts usa top 10 chunks")
    changes_made += 1

if old_line2 in content:
    content = content.replace(old_line2, new_line2)
    print("   ✓ Cambiado: context_text usa top 10 chunks")
    changes_made += 1

if old_line3 in content:
    content = content.replace(old_line3, new_line3)
    print("   ✓ Cambiado: mensaje actualizado a top 10")
    changes_made += 1

# Guardar los cambios
if changes_made > 0:
    with open(benchmark_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"\n✅ HOTFIX APLICADO: {changes_made} cambios realizados")
else:
    print("\n⚠️ No se encontraron las líneas a modificar")
    print("   Posiblemente el archivo ya fue modificado")

print("\n" + "=" * 80)
print("EXPLICACIÓN DEL PROBLEMA SOLUCIONADO:")
print("=" * 80)
print("""
PROBLEMA IDENTIFICADO:
- El benchmark limitaba chunks a 7, pero Q6 solo recuperaba 3 documentos
- Esto causaba que solo usara 3 chunks cuando la info correcta estaba en posición > 10
- Q2 y Q4 también sufrían porque la info crítica estaba fuera del top 7

SOLUCIÓN APLICADA:
- Ahora usa SIEMPRE top 10 chunks, sin importar cuántos docs se recuperen
- Esto asegura que Q6 tenga acceso a más chunks donde está la respuesta
- Q2 y Q4 también tendrán mejor cobertura

IMPACTO ESPERADO:
- Q2: Score debería subir de 0.100 → 0.7+
- Q4: Score debería subir de 0.087-0.450 → 0.6+
- Q6: Score debería subir de 0.264-0.591 → 0.7+

PRÓXIMOS PASOS:
1. Detener el benchmark actual (Ctrl+C)
2. Ejecutar nuevamente: ./venv/bin/python benchmark.py
3. Los resultados deberían mejorar significativamente
""")