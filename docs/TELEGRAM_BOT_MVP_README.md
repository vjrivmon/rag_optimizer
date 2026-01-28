# 🤖 Chatbot DNI - MVP Telegram

Bot de Telegram con **persistencia de contexto cross-sesión** para la asociación DNI (Damos Nuestra Ilusión).

## ✨ Características

✅ **Persistencia completa** - El bot recuerda conversaciones previas
✅ **Context tracking inteligente** - Detecta proyectos DNI y temas conversacionales
✅ **Exponential decay** - Contexto antiguo pierde peso gradualmente (half-life = 3 días)
✅ **RAG avanzado** - Respuestas basadas en documentos oficiales DNI
✅ **Feedback system** - Usuarios pueden dar 👍/👎 a respuestas
✅ **GDPR compliant** - /delete_my_data para eliminar datos

---

## 🚀 Inicio Rápido

### 1. Requisitos Previos

- ✅ PostgreSQL corriendo (ver sección [Database Setup](#database-setup))
- ✅ Token de Telegram Bot (ver [Configuración Telegram](#configuración-telegram))
- ✅ Python 3.12+ con virtualenv activado

### 2. Configurar Token

Edita `.env` y añade tu token:

```bash
# .env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz1234567890

# Ya configurados
DATABASE_URL=postgresql://chatbot_user:chatbot_password@localhost:5434/chatbot_dni
OLLAMA_API_URL=https://ollama.gti-ia.upv.es:443/api/generate
OLLAMA_MODEL=gemma2:27b
```

### 3. Ejecutar el Bot

```bash
# Asegúrate de estar en el directorio del proyecto
cd /home/vicente/Practicas/rag_optimizer_complete/rag_optimizer

# Activar virtualenv
source venv/bin/activate

# Ejecutar bot
python run_telegram_bot.py
```

**Salida esperada:**

```
======================================================================
🤖 CHATBOT DNI - TELEGRAM BOT MVP
======================================================================

📱 Bot de Telegram con persistencia de contexto
💾 PostgreSQL + RAG + Context Tracking

🔄 Presiona Ctrl+C para detener el bot
======================================================================

2025-11-19 17:00:00 - telegram.ext.Application - INFO - ✅ Application creada con todos los handlers registrados
2025-11-19 17:00:01 - __main__ - INFO - 🚀 Iniciando bot en modo POLLING...
2025-11-19 17:00:02 - __main__ - INFO - ✅ Bot activo! Presiona Ctrl+C para detener.
```

### 4. Probar el Bot en Telegram

1. **Abre Telegram** y busca tu bot (`@chatbot_dni_bot` o el username que elegiste)

2. **Envía** `/start`

3. **Haz una pregunta**:
   ```
   ¿Qué día son los desayunos solidarios?
   ```

4. **Recibe respuesta** con fuentes y botón de feedback 👍/👎

5. **Prueba contexto persistente**:
   - Pregunta algo sobre desayunos
   - Cierra Telegram
   - Vuelve 1 hora después
   - Pregunta algo implícito: "¿a qué hora es?"
   - El bot debería recordar que hablaste de desayunos ✅

---

## 🗄️ Database Setup

### Iniciar PostgreSQL

```bash
# Desde el directorio del proyecto
docker-compose up -d
```

**Verificar que está corriendo:**

```bash
docker ps | grep rag-telegram-postgres
```

### Ejecutar Migraciones (Primera vez)

```bash
# Si aún no ejecutaste las migraciones:
export DATABASE_URL=postgresql://chatbot_user:chatbot_password@localhost:5434/chatbot_dni
venv/bin/alembic upgrade head
```

**Salida esperada:**

```
INFO  [alembic.runtime.migration] Running upgrade  -> 1f61cecb9b98, Initial schema: 7 tables for Telegram chatbot with persistent memory
```

### Verificar Tablas Creadas

```bash
docker exec rag-telegram-postgres psql -U chatbot_user -d chatbot_dni -c "\dt"
```

**Salida esperada:**

```
               List of relations
 Schema |        Name         | Type  |     Owner
--------+---------------------+-------+---------------
 public | analytics_events    | table | chatbot_user
 public | context_snapshots   | table | chatbot_user
 public | conversations       | table | chatbot_user
 public | feedback            | table | chatbot_user
 public | messages            | table | chatbot_user
 public | user_consents       | table | chatbot_user
 public | users               | table | chatbot_user
```

---

## 📱 Configuración Telegram

### Crear Bot con BotFather

1. **Abre Telegram** y busca `@BotFather`

2. **Envía** `/newbot`

3. **Elige nombre**: `Chatbot DNI Voluntarios`

4. **Elige username**: `chatbot_dni_bot` (debe terminar en `_bot`)

5. **Copia el token** que te da BotFather

### Configurar Descripción (Opcional)

Envía `/setdescription` a BotFather y luego:

```
Asistente virtual oficial de DNI (Damos Nuestra Ilusión) 💙

Soy un bot inteligente que te ayuda con información sobre los proyectos de voluntariado de DNI en Valencia:

🍞 Desayunos Solidarios (sábados)
👴 Charlas con Abuelitos (RESIS)
📚 Refuerzo Escolar (COLES)
🏗️ Rehabilitar Valencia (DANA)
🚣 Recogida de Plásticos (Kayak)

Pregúntame lo que quieras sobre horarios, ubicaciones, requisitos o cómo participar!

PARA. MIRA. AYUDA. ❤️
```

### Configurar Comandos

Envía `/setcommands` a BotFather, **haz click en tu bot** de la lista, y envía:

```
start - Iniciar conversación con el bot
help - Mostrar ayuda y comandos disponibles
reset - Reiniciar conversación (nuevo contexto)
history - Ver historial de conversaciones
delete_my_data - Eliminar todos mis datos (GDPR)
```

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                     USUARIO (Telegram App)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                      ┌──────▼──────┐
                      │  Telegram    │  (Bot API)
                      │   Servers    │
                      └──────┬──────┘
                             │
              ┌──────────────▼──────────────┐
              │  python-telegram-bot v20+   │  (Polling)
              │  - CommandHandler           │
              │  - MessageHandler           │
              │  - CallbackQueryHandler     │
              └──────────────┬──────────────┘
                             │
         ┌───────────────────┴───────────────────┐
         │                                       │
    ┌────▼────┐                           ┌─────▼────┐
    │ Service  │                           │   RAG    │
    │  Layer   │                           │  Engine  │
    │ (CRUD)   │                           │ (Query)  │
    └────┬────┘                           └─────┬────┘
         │                                       │
         │              ┌───────────┐           │
         └──────────────►           ◄───────────┘
                        │ Persistent │
                        │  Context   │
                        │  Tracker   │
                        └─────┬─────┘
                              │
         ┌────────────────────┴────────────────────┐
         │                                         │
    ┌────▼────┐                              ┌────▼────┐
    │ Postgres │                              │ ChromaDB │
    │ Database │                              │ Vectors  │
    │ (Context)│                              │  (Docs)  │
    └─────────┘                              └──────────┘
```

### Componentes Principales

#### 1. **Service Layer** (`src/services/`)

- `UserService` - Gestión de usuarios Telegram
- `ConversationService` - Gestión de conversaciones
- `MessageService` - Almacenamiento de mensajes
- `ContextService` - Snapshots de contexto

#### 2. **Persistent Context Tracker** (`src/core/persistent_context_tracker.py`)

- Extiende `ContextTracker` base
- Recupera snapshots históricos (últimos 7 días)
- Aplica exponential decay: `weight = exp(-days_ago / 3.0)`
- Merge contexto reciente + histórico

#### 3. **Telegram Handlers** (`src/telegram/handlers/`)

- **Commands**: `/start`, `/help`, `/reset`, `/history`, `/delete_my_data`
- **Messages**: Procesa texto + integra RAG + guarda en DB
- **Callbacks**: Feedback 👍/👎, confirmaciones

#### 4. **Database Schema** (7 tablas)

- `users` - Usuarios de Telegram
- `conversations` - Conversaciones agrupadas por proyecto DNI
- `messages` - Mensajes con metadata RAG (JSONB)
- `context_snapshots` - Snapshots cada 5 mensajes
- `feedback` - Feedback de usuarios
- `user_consents` - Consentimientos GDPR
- `analytics_events` - Eventos de analytics

---

## 🧪 Testing

### Test Básico de Conversación

```python
# tests/test_telegram_bot_basic.py
import pytest
from src.services import UserService, MessageService

@pytest.mark.asyncio
async def test_user_creation():
    user_service = UserService()

    user = await user_service.get_or_create_user(
        telegram_user_id=123456789,
        first_name="Test",
        last_name="User",
    )

    assert user.telegram_user_id == 123456789
    assert user.first_name == "Test"
```

### Test de Persistencia de Contexto

1. **Envía pregunta sobre desayunos** a las 10:00 AM
2. **Espera 1 hora**
3. **Envía pregunta implícita**: "¿a qué hora es?"
4. **Verifica** que el bot recuerda el contexto de desayunos

---

## 🐛 Troubleshooting

### Error: "No module named 'telegram'"

**Solución:**
```bash
venv/bin/pip install python-telegram-bot[all]>=20.0
```

### Error: "Connection refused" al conectar a PostgreSQL

**Solución:**
```bash
# Verificar que PostgreSQL está corriendo
docker ps | grep rag-telegram-postgres

# Si no está corriendo:
docker-compose up -d
```

### Error: "TELEGRAM_BOT_TOKEN no configurado"

**Solución:**
```bash
# Verificar que .env tiene el token
cat .env | grep TELEGRAM_BOT_TOKEN

# Si no está, añádelo:
echo "TELEGRAM_BOT_TOKEN=tu_token_aqui" >> .env
```

### Bot no responde a mensajes

**Posibles causas:**

1. **Token incorrecto** - Verifica que el token en `.env` es correcto
2. **Bot no iniciado** - Asegúrate de que `run_telegram_bot.py` está corriendo
3. **Firewall bloqueando** - Si estás en VPN/firewall, puede bloquear polling

---

## 📊 Métricas y Monitoreo

### Ver Logs del Bot

El bot imprime logs en consola:

```
✅ Response sent | User: 123456789 | Confidence: 0.87 | Snapshot: True
```

### Consultar Base de Datos

```bash
# Número de usuarios activos
docker exec rag-telegram-postgres psql -U chatbot_user -d chatbot_dni -c "SELECT COUNT(*) FROM users WHERE is_active = true;"

# Últimas 10 conversaciones
docker exec rag-telegram-postgres psql -U chatbot_user -d chatbot_dni -c "SELECT id, project_context, created_at FROM conversations ORDER BY created_at DESC LIMIT 10;"

# Snapshots creados hoy
docker exec rag-telegram-postgres psql -U chatbot_user -d chatbot_dni -c "SELECT COUNT(*) FROM context_snapshots WHERE DATE(created_at) = CURRENT_DATE;"
```

---

## 🚀 Próximos Pasos (Post-MVP)

- [ ] **Webhook mode** para producción (HTTPS con ngrok/servidor)
- [ ] **Multi-idioma** (español, valenciano, inglés)
- [ ] **Analytics dashboard** con métricas en tiempo real
- [ ] **A/B testing** de prompts y estrategias RAG
- [ ] **Fine-tuning** de gemma2:27b con conversaciones reales DNI
- [ ] **Voice messages** support
- [ ] **WhatsApp integration** (mismo backend)

---

## 📄 Licencia

MIT License - Chatbot DNI © 2025

**Desarrollado para:** Asociación DNI (Damos Nuestra Ilusión) Valencia

---

**¿Problemas?** Crea un issue o contacta al desarrollador.
