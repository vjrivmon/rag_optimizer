#!/usr/bin/env python3
"""Test completo: ejecuta benchmark mientras simula un navegador conectado"""

import asyncio
import websockets
import json
import subprocess
import time
import sys

async def websocket_listener():
    """Escucha eventos del WebSocket"""
    uri = "ws://localhost:8000/ws"
    events_received = []
    
    print("🔌 Conectando al WebSocket...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket conectado\n")
            
            async for message in websocket:
                data = json.loads(message)
                msg_type = data.get('type', 'unknown')
                
                # Filtrar solo eventos relevantes (no stats_update repetitivas)
                if msg_type != 'stats_update':
                    events_received.append(data)
                    timestamp = data.get('timestamp', '').split('T')[1][:8] if 'T' in data.get('timestamp', '') else ''
                    
                    print(f"📨 [{timestamp}] {msg_type}")
                    
                    if msg_type == 'phase_start':
                        phase = data.get('data', {}).get('phase', '')
                        print(f"   → Fase: {phase}")
                    elif msg_type == 'question_start':
                        q = data.get('data', {}).get('question', '')
                        print(f"   → {q[:60]}...")
                    elif msg_type == 'model_complete':
                        model = data.get('data', {}).get('model_name', '')
                        success = data.get('data', {}).get('success', False)
                        if success:
                            conf = data.get('data', {}).get('confidence', 0)
                            print(f"   → {model}: Score {conf:.2f}")
                        else:
                            print(f"   → {model}: ERROR")
                
    except Exception as e:
        print(f"❌ Error en WebSocket: {e}")
    
    return events_received

async def main():
    print("=" * 70)
    print("🧪 TEST COMPLETO: Dashboard en Tiempo Real")
    print("=" * 70)
    print()
    print("Este test verificará:")
    print("1. ✅ Conexión WebSocket al dashboard")
    print("2. ✅ Ejecución del benchmark con 1 pregunta")
    print("3. ✅ Recepción de eventos en tiempo real")
    print()
    print("=" * 70)
    print()
    
    # Iniciar el listener en background
    listener_task = asyncio.create_task(websocket_listener())
    
    # Esperar 2 segundos para que el WebSocket se conecte
    await asyncio.sleep(2)
    
    # Ejecutar benchmark
    print("\n🚀 Ejecutando benchmark con 1 pregunta...")
    print("   (Esto tomará ~1 minuto dependiendo de los modelos)\n")
    
    # Usar subprocess para ejecutar el benchmark
    import os
    os.chdir('/home/vicente/Practicas/rag_optimizer_complete/rag_optimizer')
    
    proc = subprocess.Popen(
        'source venv/bin/activate && python3 benchmark_v2.py --phase generation --max-questions 1',
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        executable='/bin/bash'
    )
    
    # Esperar a que termine el benchmark (con timeout)
    try:
        stdout, stderr = proc.communicate(timeout=180)
        print("\n✅ Benchmark completado\n")
    except subprocess.TimeoutExpired:
        proc.kill()
        print("\n⏱️ Benchmark timeout (3 minutos)\n")
    
    # Esperar 2 segundos más para recibir eventos finales
    await asyncio.sleep(2)
    
    # Cancelar el listener
    listener_task.cancel()
    
    try:
        events = await listener_task
    except asyncio.CancelledError:
        events = []
    
    # Resumen
    print("\n" + "=" * 70)
    print("📊 RESUMEN DEL TEST")
    print("=" * 70)
    
    if events:
        print(f"✅ Se recibieron {len(events)} eventos en tiempo real")
        print("\nTipos de eventos recibidos:")
        event_types = {}
        for event in events:
            etype = event.get('type', 'unknown')
            event_types[etype] = event_types.get(etype, 0) + 1
        
        for etype, count in event_types.items():
            print(f"   - {etype}: {count}")
        
        print("\n✅ EL SISTEMA FUNCIONA CORRECTAMENTE")
        print("   Los eventos se transmiten en tiempo real al navegador")
    else:
        print("❌ NO se recibieron eventos en tiempo real")
        print("\nPosibles causas:")
        print("   1. El benchmark no se ejecutó correctamente")
        print("   2. El broadcaster no está emitiendo eventos")
        print("   3. Problema de conexión WebSocket")
    
    print("=" * 70)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrumpido por el usuario")
        sys.exit(1)

