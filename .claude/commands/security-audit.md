# /security-audit - Auditoria de Seguridad Completa

## Descripcion

Ejecuta una auditoria de seguridad completa del sistema Chatbot DNI, escaneando
entry points (web + Telegram), ejecutando tests de seguridad, y generando un
reporte detallado.

## Pasos

1. **Escanear entry points** web y Telegram en busca de vulnerabilidades
2. **Ejecutar** `pytest tests/security/ -v --tb=short`
3. **Verificar** integracion del SDK de seguridad en produccion
4. **Comprobar** configuracion CORS, SSL, rate limiting
5. **Revisar** uso de innerHTML en frontend
6. **Generar** reporte en `docs/security/AUDIT_REPORT.md`

## Uso

```
/security-audit
```

## Archivos a Escanear

### Criticos (entry points de usuario)

- `interface/chatbot_dni/backend/app.py` - CORS, WebSocket handler
- `src/telegram/handlers/messages.py` - Telegram message handler
- `interface/chatbot_dni/frontend/static/js/chat.js` - DOM manipulation

### SDK de Seguridad

- `vicente_rag/security/injection_detector.py`
- `vicente_rag/security/sanitizer.py`
- `vicente_rag/security/risk_scorer.py`

### Tests

- `tests/security/test_injection_detector.py`
- `tests/security/test_sanitizer.py`
- `tests/security/test_risk_scorer.py`

## Formato del Reporte

El reporte generado en `docs/security/AUDIT_REPORT.md` incluye:

- Fecha de auditoria
- Vulnerabilidades encontradas (critica/alta/media/baja)
- Estado de integracion del SDK
- Resultados de tests
- Recomendaciones priorizadas
- Checklist de cumplimiento (ver `.claude/agents/08-security/AGENT.md`)
