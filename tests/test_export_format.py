"""
Test automatizado para verificar el formato de export con métricas detalladas
===============================================================================
"""
import asyncio
import websockets
import json
from datetime import datetime

# Preguntas de test (incluyen context persistence)
TEST_QUESTIONS = [
    "¿Qué es DNI?",
    "¿Qué requisitos necesito?",
    "¿Cuántos voluntarios tiene DNI?",
    "¿Es gratis participar?",
    "¿Cómo me puedo apuntar a la actividad de desayunos?",  # Contexto explícito
    "¿Cuánto dura la actividad?",                            # Contexto implícito
    "¿y que se hace?",                                       # Contexto implícito
    "¿Si me apunto un día tengo que ir el resto?",           # Contexto implícito
    "¿quién compra los alimentos?"                            # Contexto implícito (CRÍTICO)
]

class ExportTester:
    def __init__(self):
        self.message_history = []
        self.session_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def clean_markdown(self, text):
        """Limpia markdown del texto (para exportación TXT plana)"""
        if not text:
            return ''

        return text.replace('***', '').replace('**', '').replace('*', '').replace('<br>', '\n').strip()

    async def send_question_and_receive(self, ws, question):
        """Envía una pregunta y recibe la respuesta completa"""
        print(f"\n{'='*80}")
        print(f"📤 PREGUNTA: {question}")
        print(f"{'='*80}")

        # Enviar pregunta
        await ws.send(json.dumps({
            'question': question,
            'session_id': self.session_id
        }))

        # Guardar mensaje del usuario
        user_msg = {
            'text': question,
            'type': 'user',
            'timestamp': datetime.now().timestamp() * 1000,
            'metadata': {}
        }
        self.message_history.append(user_msg)

        # Recibir respuesta (streaming)
        answer_text = ""
        metadata = {}

        while True:
            try:
                message = await asyncio.wait_for(ws.recv(), timeout=60.0)
                data = json.loads(message)

                if data['type'] == 'status':
                    print(f"  ⏳ Status: {data.get('status', 'unknown')}")

                elif data['type'] == 'log':
                    print(f"  📝 Log: {data.get('log', '')}")

                elif data['type'] == 'chunk':
                    answer_text += data['chunk']

                elif data['type'] == 'complete':
                    response = data['response']
                    metadata = {
                        'confidence': response.get('confidence'),
                        'responseId': response.get('response_id'),
                        'sources': response.get('sources', []),
                        'suggestions': response.get('suggestions', []),
                        # ✨ NUEVOS CAMPOS DETALLADOS
                        'confidence_breakdown': response.get('confidence_breakdown'),
                        'top_chunks': response.get('top_chunks', []),
                        'context_info': response.get('context_info'),
                        'alerts': response.get('alerts', []),
                        'chunks_count': response.get('chunks_count', 0),
                        'question_original': response.get('question_original', question)
                    }

                    print(f"  ✅ Respuesta recibida (confidence: {metadata['confidence']:.2f})")
                    print(f"  📊 Chunks: {metadata['chunks_count']}")

                    # Mostrar contexto detectado
                    if metadata['context_info'] and metadata['context_info'].get('active_project'):
                        ctx = metadata['context_info']
                        print(f"  🎯 Contexto: {ctx['active_project']} (conf: {ctx['confidence']:.2f})")

                    # Mostrar alertas si hay
                    if metadata['alerts']:
                        print(f"  ⚠️  Alertas: {len(metadata['alerts'])}")

                    break

                elif data['type'] == 'error':
                    print(f"  ❌ Error: {data.get('error')}")
                    break

            except asyncio.TimeoutError:
                print("  ⏰ Timeout esperando respuesta")
                break

        # Guardar mensaje del bot
        bot_msg = {
            'text': answer_text,
            'type': 'bot',
            'timestamp': datetime.now().timestamp() * 1000,
            'metadata': metadata
        }
        self.message_history.append(bot_msg)

        print(f"  💬 Respuesta: {answer_text[:100]}...")

        return answer_text, metadata

    def generate_export(self):
        """Genera el export en formato TXT con toda la metadata"""
        content = '=' * 80 + '\n'
        content += 'CONVERSACION CON ASISTENTE DNI\n'
        content += '=' * 80 + '\n\n'
        content += f'Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
        content += f'Sesion: {self.session_id}\n\n'
        content += '=' * 80 + '\n\n'

        for msg in self.message_history:
            role = 'USUARIO' if msg['type'] == 'user' else 'ASISTENTE DNI'
            timestamp = datetime.fromtimestamp(msg['timestamp'] / 1000).strftime('%H:%M:%S')

            content += f'[{timestamp}] {role}:\n'
            clean_text = self.clean_markdown(msg['text'])
            content += clean_text + '\n\n'

            # Añadir metadata para mensajes del bot
            if msg['type'] == 'bot' and msg['metadata']:
                meta = msg['metadata']

                # Confidence general
                if meta.get('confidence') is not None:
                    content += f"  Confidence: {int(meta['confidence'] * 100)}%\n"

                # Feedback (placeholder)
                content += f"  Feedback: No proporcionado\n"

                # ✨ CONFIDENCE BREAKDOWN
                if meta.get('confidence_breakdown'):
                    breakdown = meta['confidence_breakdown']
                    content += '\n  --- CONFIDENCE BREAKDOWN ---\n'
                    content += f"  Confidence final: {breakdown['confidence'] * 100:.1f}%\n"
                    content += f"  Formula: {breakdown['formula']}\n"
                    content += f"  Factores ({breakdown['total_factors']}):\n"

                    if breakdown.get('breakdown'):
                        for factor, data in breakdown['breakdown'].items():
                            factor_name = factor.replace('_', ' ').upper()
                            score = int(data.get('score', 0) * 100)
                            weight = int(data.get('weight', 0) * 100)
                            contribution = data.get('contribution', 0) * 100
                            content += f"    - {factor_name}: {score}% (peso: {weight}%, contribucion: {contribution:.1f}%)\n"

                            # Detalles adicionales
                            if 'count' in data:
                                content += f"      Valor: {data['count']}\n"
                            if 'length' in data:
                                content += f"      Longitud: {data['length']} chars\n"
                            if 'keywords_found' in data:
                                content += f"      Keywords: {data['keywords_found']}/{data.get('keywords_total', 0)}\n"
                            if 'patterns_found' in data:
                                content += f"      Patrones: {data['patterns_found']}\n"
                            if 'has_negative' in data:
                                content += f"      Sin negativos: {not data['has_negative']}\n"

                    content += '  ' + '-' * 30 + '\n'

                # ✨ TOP CHUNKS
                if meta.get('top_chunks'):
                    content += '\n  --- TOP CHUNKS RECUPERADOS ---\n'
                    content += f"  Total chunks consultados: {meta.get('chunks_count', len(meta['top_chunks']))}\n"

                    for chunk in meta['top_chunks']:
                        content += f"\n  Chunk {chunk['rank']}:\n"
                        if chunk['score'] is not None:
                            content += f"    Score: {chunk['score'] * 100:.1f}%\n"
                        content += f"    Fuente: {chunk['source']}\n"
                        if chunk.get('location'):
                            content += f"    Ubicacion: Lineas {chunk['location']}\n"
                        content += f"    Contenido: \"{chunk['content']}\"\n"

                    content += '  ' + '-' * 30 + '\n'

                # ✨ CONTEXTO DETECTADO
                if meta.get('context_info'):
                    ctx = meta['context_info']
                    if ctx.get('active_project') or ctx.get('active_topic'):
                        content += '\n  --- CONTEXTO DETECTADO ---\n'
                        if ctx.get('active_project'):
                            content += f"  Proyecto activo: {ctx['active_project']}\n"
                            content += f"  Confianza proyecto: {int(ctx['project_score'] * 100)}%\n"
                        if ctx.get('active_topic'):
                            content += f"  Tema detectado: {ctx['active_topic'].replace('_', ' ')}\n"
                            content += f"  Confianza tema: {int(ctx['topic_score'] * 100)}%\n"
                        content += f"  Confianza total: {int(ctx['confidence'] * 100)}%\n"
                        if ctx.get('summary'):
                            content += f"  Resumen: {ctx['summary']}\n"
                        content += '  ' + '-' * 30 + '\n'

                # ✨ ALERTAS
                if meta.get('alerts'):
                    content += '\n  --- ALERTAS DEL SISTEMA ---\n'
                    for i, alert in enumerate(meta['alerts'], 1):
                        severity = f" [{alert['severity'].upper()}]" if alert.get('severity') else ''
                        content += f"  {i}.{severity} {alert['type']}\n"
                        content += f"     {alert['message']}\n"
                        if alert.get('recommendation'):
                            content += f"     Recomendacion: {alert['recommendation']}\n"
                    content += '  ' + '-' * 30 + '\n'

                # Sugerencias
                if meta.get('suggestions'):
                    content += '\n  --- SUGERENCIAS PROPUESTAS ---\n'
                    for i, suggestion in enumerate(meta['suggestions'], 1):
                        content += f"  {i}. {suggestion}\n"
                    content += '  ' + '-' * 30 + '\n'

                content += '\n'

            content += '-' * 80 + '\n\n'

        content += '=' * 80 + '\n'
        content += 'Fin de la conversacion\n'
        content += '=' * 80 + '\n'

        return content

    async def run_test(self):
        """Ejecuta el test completo"""
        print("\n" + "="*80)
        print("🧪 TEST DE FORMATO DE EXPORT CON MÉTRICAS DETALLADAS")
        print("="*80)

        uri = "ws://localhost:8000/ws/chat"
        print(f"📝 Sesión: {self.session_id}")

        try:
            # ✨ IMPORTANTE: El backend cierra el WebSocket después de cada respuesta
            # Por lo tanto, debemos RECONECTAR para cada pregunta
            # (esto imita el comportamiento real del frontend)

            for i, question in enumerate(TEST_QUESTIONS, 1):
                print(f"\n{'='*80}")
                print(f"Pregunta {i}/{len(TEST_QUESTIONS)}")
                print(f"🔌 Conectando al WebSocket...")

                # Reconectar para cada pregunta
                async with websockets.connect(uri, ping_interval=None) as ws:
                    print(f"  ✅ Conectado")
                    await self.send_question_and_receive(ws, question)
                    # El WebSocket se cerrará automáticamente al salir del context manager

                await asyncio.sleep(0.5)  # Pequeña pausa entre preguntas

            print(f"\n{'='*80}")
            print("✅ Todas las preguntas completadas")
            print(f"📊 Total mensajes: {len(self.message_history)}")

            # Generar export
            print(f"\n{'='*80}")
            print("📄 GENERANDO EXPORT...")
            print(f"{'='*80}")

            export_content = self.generate_export()

            # Guardar a archivo
            filename = f"/tmp/export_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(export_content)

            print(f"✅ Export guardado en: {filename}")
            print(f"📏 Tamaño: {len(export_content)} caracteres")

            # Mostrar preview del export
            print(f"\n{'='*80}")
            print("📄 PREVIEW DEL EXPORT (primeras 100 líneas):")
            print(f"{'='*80}\n")
            lines = export_content.split('\n')
            for line in lines[:100]:
                print(line)

            if len(lines) > 100:
                print(f"\n... ({len(lines) - 100} líneas más) ...\n")

            print(f"\n{'='*80}")
            print(f"✅ TEST COMPLETADO - Revisar archivo: {filename}")
            print(f"{'='*80}")

            return filename

        except Exception as e:
            print(f"❌ Error en el test: {e}")
            import traceback
            traceback.print_exc()
            return None


if __name__ == "__main__":
    tester = ExportTester()
    result = asyncio.run(tester.run_test())

    if result:
        print(f"\n✅ Export disponible en: {result}")
    else:
        print(f"\n❌ Test falló")
