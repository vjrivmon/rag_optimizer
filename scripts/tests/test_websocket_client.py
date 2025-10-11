#!/usr/bin/env python3
"""Cliente WebSocket de prueba para verificar eventos en tiempo real"""

import asyncio
import websockets
import json
import sys

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    
    print(f"🔌 Conectando a {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Conectado al WebSocket")
            print("📡 Esperando mensajes...\n")
            
            # Esperar mensajes por 10 segundos
            try:
                async for message in websocket:
                    data = json.loads(message)
                    msg_type = data.get('type', 'unknown')
                    timestamp = data.get('timestamp', '')
                    
                    print(f"📨 [{timestamp}] Tipo: {msg_type}")
                    
                    if msg_type == 'stats_update':
                        stats = data.get('data', {})
                        print(f"   Respuestas: {stats.get('total_responses', 0)}")
                        print(f"   Evaluaciones: {stats.get('total_evaluations', 0)}")
                    elif msg_type == 'event_history':
                        events = data.get('data', {}).get('events', [])
                        print(f"   Historial: {len(events)} eventos")
                    elif msg_type == 'phase_start':
                        phase = data.get('data', {}).get('phase', '')
                        print(f"   🚀 FASE {phase.upper()} INICIADA")
                    elif msg_type == 'question_start':
                        q_id = data.get('data', {}).get('question_id', '')
                        question = data.get('data', {}).get('question', '')
                        print(f"   📝 P{q_id}: {question}")
                    elif msg_type == 'model_start':
                        model = data.get('data', {}).get('model_name', '')
                        print(f"   🤖 {model} procesando...")
                    elif msg_type == 'model_complete':
                        model = data.get('data', {}).get('model_name', '')
                        success = data.get('data', {}).get('success', False)
                        if success:
                            time = data.get('data', {}).get('generation_time', 0)
                            confidence = data.get('data', {}).get('confidence', 0)
                            print(f"   ✅ {model}: {time:.1f}s Score={confidence:.2f}")
                        else:
                            error = data.get('data', {}).get('error', '')
                            print(f"   ❌ {model}: {error[:50]}")
                    
                    print()
                    
            except asyncio.TimeoutError:
                print("⏱️ Timeout esperando mensajes")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 Test de WebSocket - Presiona Ctrl+C para detener\n")
    try:
        asyncio.run(test_websocket())
    except KeyboardInterrupt:
        print("\n\n✅ Test detenido por el usuario")
        sys.exit(0)

