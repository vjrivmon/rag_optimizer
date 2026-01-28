#!/usr/bin/env python3
"""Test simple del EventBroadcaster"""

import sys
import asyncio
from src.utils.event_broadcaster import get_broadcaster

async def test_broadcaster():
    broadcaster = get_broadcaster()
    
    print("✅ Broadcaster inicializado")
    print(f"   Clientes conectados: {len(broadcaster.clients)}")
    print(f"   Eventos en historial: {len(broadcaster.event_history)}")
    
    # Mostrar últimos eventos
    if broadcaster.event_history:
        print("\n📜 Últimos eventos:")
        for i, event in enumerate(list(broadcaster.event_history)[-10:], 1):
            print(f"   {i}. [{event['type']}] {event['timestamp']}")
            if 'data' in event:
                if event['type'] == 'question_start':
                    print(f"      → P{event['data'].get('question_id')}: {event['data'].get('question', '')[:60]}")
                elif event['type'] == 'model_complete':
                    success = event['data'].get('success')
                    if success:
                        print(f"      → {event['data'].get('model_name')}: {event['data'].get('generation_time', 0):.1f}s")
                    else:
                        print(f"      → {event['data'].get('model_name')}: ERROR")
    else:
        print("\n⚠️ No hay eventos en el historial")
        print("   Esto es normal si no se ha ejecutado el benchmark aún")
    
    # Emitir un evento de prueba
    print("\n🧪 Emitiendo evento de prueba...")
    broadcaster.emit('test_event', {
        'message': 'Evento de prueba desde test_broadcaster.py',
        'timestamp': 'now'
    })
    
    print(f"✅ Evento emitido. Total eventos: {len(broadcaster.event_history)}")
    
    return True

if __name__ == "__main__":
    result = asyncio.run(test_broadcaster())
    sys.exit(0 if result else 1)

