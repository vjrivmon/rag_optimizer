"""Test rápido para verificar que las fuentes se muestran correctamente"""
import asyncio
import websockets
import json

async def test_sources():
    uri = "ws://localhost:8000/ws/chat"
    session_id = "test_sources_123"

    print("🧪 Test rápido de fuentes...")
    print("📌 Pregunta: ¿Qué es DNI?\n")

    async with websockets.connect(uri, ping_interval=None) as ws:
        # Enviar pregunta
        await ws.send(json.dumps({
            'question': '¿Qué es DNI?',
            'session_id': session_id
        }))

        # Recibir respuesta
        top_chunks = None
        while True:
            try:
                message = await asyncio.wait_for(ws.recv(), timeout=60.0)
                data = json.loads(message)

                if data['type'] == 'complete':
                    response = data['response']
                    top_chunks = response.get('top_chunks', [])
                    break
            except asyncio.TimeoutError:
                print("❌ Timeout")
                break

        # Mostrar chunks
        if top_chunks:
            print(f"\n✅ Top chunks recibidos: {len(top_chunks)}\n")
            for chunk in top_chunks:
                print(f"Chunk {chunk['rank']}:")
                print(f"  Fuente: {chunk.get('source', 'N/A')}")
                print(f"  Ubicacion: {chunk.get('location', 'N/A')}")
                print(f"  Contenido: {chunk.get('content', 'N/A')[:100]}...")
                print()
        else:
            print("❌ No se recibieron chunks")

if __name__ == "__main__":
    asyncio.run(test_sources())
