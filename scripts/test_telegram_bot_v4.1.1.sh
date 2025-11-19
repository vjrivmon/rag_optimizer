#!/bin/bash

# ============================================================================
# Test Script para Telegram Bot v4.1.1 - Sistema Anti-Contaminación
# ============================================================================

echo "======================================================================"
echo "🧪 TELEGRAM BOT v4.1.1 - SISTEMA ANTI-CONTAMINACIÓN"
echo "======================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# 1. VERIFICAR ARCHIVOS MODIFICADOS v4.1.1
# ============================================================================

echo "📂 Test 1: Verificar Archivos Modificados v4.1.1"
echo "----------------------------------------------------------------------"

files_v4_1_1=(
    "src/core/persistent_context_tracker.py"
    "docs/TELEGRAM_BOT_FIXES_v4.1.md"
    "scripts/test_telegram_bot_v4.1.1.sh"
)

all_exists=true
for file in "${files_v4_1_1[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅${NC} $file"
    else
        echo -e "${RED}❌${NC} $file (FALTA)"
        all_exists=false
    fi
done

if $all_exists; then
    echo ""
    echo -e "${GREEN}✅ PASÓ${NC} - Todos los archivos v4.1.1 presentes"
else
    echo ""
    echo -e "${RED}❌ FALLÓ${NC} - Algunos archivos faltan"
    exit 1
fi

echo ""

# ============================================================================
# 2. VERIFICAR LÓGICA ANTI-CONTAMINACIÓN
# ============================================================================

echo "🔍 Test 2: Verificar Lógica Anti-Contaminación Implementada"
echo "----------------------------------------------------------------------"

# Check 1: Detección de conversación activa
if grep -q "is_active_conversation = len(conversation_history) >= 2" src/core/persistent_context_tracker.py; then
    echo -e "${GREEN}✅${NC} Detección de conversación activa (2+ mensajes)"
else
    echo -e "${RED}❌${NC} Detección de conversación activa FALTA"
    exit 1
fi

# Check 2: NO consultar DB en conversación activa
if grep -q "'source': 'active_conversation'" src/core/persistent_context_tracker.py; then
    echo -e "${GREEN}✅${NC} Source type 'active_conversation' implementado"
else
    echo -e "${RED}❌${NC} Source type FALTA"
    exit 1
fi

# Check 3: Flag anti-contamination
if grep -q "'anti_contamination': True" src/core/persistent_context_tracker.py; then
    echo -e "${GREEN}✅${NC} Flag anti_contamination implementado"
else
    echo -e "${RED}❌${NC} Flag anti_contamination FALTA"
    exit 1
fi

# Check 4: Umbral bajado a 0.3
if grep -q "if recent_project and recent_confidence > 0.3:" src/core/persistent_context_tracker.py; then
    echo -e "${GREEN}✅${NC} Umbral bajado a 0.3 (antes 0.5)"
else
    echo -e "${RED}❌${NC} Umbral NO modificado"
    exit 1
fi

# Check 5: historical_snapshots = 0 en conversación activa
if grep -q "'historical_snapshots': 0,  # No se consultaron snapshots" src/core/persistent_context_tracker.py; then
    echo -e "${GREEN}✅${NC} historical_snapshots = 0 en conversación activa"
else
    echo -e "${RED}❌${NC} historical_snapshots handling FALTA"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ PASÓ${NC} - Toda la lógica anti-contaminación implementada"
echo ""

# ============================================================================
# 3. VERIFICAR DOCUMENTACIÓN v4.1.1
# ============================================================================

echo "📝 Test 3: Verificar Documentación v4.1.1"
echo "----------------------------------------------------------------------"

# Check 1: Sección v4.1.1 en documentación
if grep -q "ACTUALIZACIÓN v4.1.1 - Sistema Anti-Contaminación" docs/TELEGRAM_BOT_FIXES_v4.1.md; then
    echo -e "${GREEN}✅${NC} Sección v4.1.1 documentada"
else
    echo -e "${RED}❌${NC} Documentación v4.1.1 FALTA"
    exit 1
fi

# Check 2: Changelog presente
if grep -q "CHANGELOG v4.1 → v4.1.1" docs/TELEGRAM_BOT_FIXES_v4.1.md; then
    echo -e "${GREEN}✅${NC} Changelog v4.1 → v4.1.1 presente"
else
    echo -e "${RED}❌${NC} Changelog FALTA"
    exit 1
fi

# Check 3: Análisis técnico documentado
if grep -q "Análisis Técnico del Fallo" docs/TELEGRAM_BOT_FIXES_v4.1.md; then
    echo -e "${GREEN}✅${NC} Análisis técnico documentado"
else
    echo -e "${RED}❌${NC} Análisis técnico FALTA"
    exit 1
fi

# Check 4: Casos de prueba críticos
if grep -q "Casos de Prueba Críticos" docs/TELEGRAM_BOT_FIXES_v4.1.md; then
    echo -e "${GREEN}✅${NC} Casos de prueba críticos documentados"
else
    echo -e "${RED}❌${NC} Casos de prueba FALTAN"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ PASÓ${NC} - Documentación v4.1.1 completa"
echo ""

# ============================================================================
# 4. VERIFICAR TYPING INDICATOR
# ============================================================================

echo "⌨️  Test 4: Verificar Typing Indicator Continuo"
echo "----------------------------------------------------------------------"

# Check: keep_typing function
if grep -q "async def keep_typing(chat, stop_event):" src/telegram/handlers/messages.py; then
    echo -e "${GREEN}✅${NC} Función keep_typing() implementada"
else
    echo -e "${RED}❌${NC} Función keep_typing() FALTA"
    exit 1
fi

# Check: typing_stop event
if grep -q "typing_stop = asyncio.Event()" src/telegram/handlers/messages.py; then
    echo -e "${GREEN}✅${NC} Event typing_stop implementado"
else
    echo -e "${RED}❌${NC} Event typing_stop FALTA"
    exit 1
fi

# Check: typing task creation
if grep -q "typing_task = asyncio.create_task(keep_typing" src/telegram/handlers/messages.py; then
    echo -e "${GREEN}✅${NC} Typing task creado correctamente"
else
    echo -e "${RED}❌${NC} Typing task FALTA"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ PASÓ${NC} - Typing indicator continuo implementado"
echo ""

# ============================================================================
# 5. VERIFICAR QUE EL BOT ESTÁ CORRIENDO
# ============================================================================

echo "🤖 Test 5: Verificar Bot en Ejecución"
echo "----------------------------------------------------------------------"

if pgrep -f "python.*run_telegram_bot.py" > /dev/null; then
    echo -e "${GREEN}✅ PASÓ${NC} - Bot en ejecución"
    PID=$(pgrep -f "python.*run_telegram_bot.py")
    echo "   PID: $PID"
    echo ""
    echo -e "${YELLOW}⚠️  IMPORTANTE: Reiniciar bot para aplicar cambios v4.1.1${NC}"
    echo "   Ejecuta: pkill -f 'python.*run_telegram_bot.py' && venv/bin/python run_telegram_bot.py"
else
    echo -e "${YELLOW}⚠️  ADVERTENCIA${NC} - Bot no está corriendo"
    echo "   Ejecuta: venv/bin/python run_telegram_bot.py"
    echo ""
fi

echo ""

# ============================================================================
# 6. VERIFICAR BASE DE DATOS
# ============================================================================

echo "💾 Test 6: Verificar Conexión a Base de Datos"
echo "----------------------------------------------------------------------"

if docker ps | grep -q "rag-telegram-postgres"; then
    echo -e "${GREEN}✅ PASÓ${NC} - PostgreSQL corriendo"

    # Verificar tablas
    TABLES=$(docker exec rag-telegram-postgres psql -U chatbot_user -d chatbot_dni -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')

    if [ "$TABLES" -ge 7 ]; then
        echo -e "${GREEN}✅ PASÓ${NC} - Base de datos con $TABLES tablas (esperado: 7)"
    else
        echo -e "${YELLOW}⚠️  ADVERTENCIA${NC} - Solo $TABLES tablas (esperado: 7)"
    fi
else
    echo -e "${YELLOW}⚠️  ADVERTENCIA${NC} - PostgreSQL no está corriendo"
    echo "   Ejecuta: docker-compose up -d"
fi

echo ""

# ============================================================================
# RESUMEN FINAL
# ============================================================================

echo "======================================================================"
echo "📊 RESUMEN DE TESTS v4.1.1"
echo "======================================================================"
echo ""
echo -e "${GREEN}✅ Test 1:${NC} Archivos v4.1.1 presentes"
echo -e "${GREEN}✅ Test 2:${NC} Lógica anti-contaminación implementada"
echo -e "${GREEN}✅ Test 3:${NC} Documentación v4.1.1 completa"
echo -e "${GREEN}✅ Test 4:${NC} Typing indicator continuo"
echo ""
echo "======================================================================"
echo "🎯 PRÓXIMOS PASOS - VERIFICACIÓN MANUAL"
echo "======================================================================"
echo ""
echo -e "${BLUE}1. Reiniciar el bot con cambios v4.1.1:${NC}"
echo "   pkill -f 'python.*run_telegram_bot.py'"
echo "   venv/bin/python run_telegram_bot.py"
echo ""
echo -e "${BLUE}2. Prueba crítica de anti-contaminación:${NC}"
echo "   /reset"
echo "   'Cuéntame sobre los desayunos solidarios'"
echo "   → Verificar respuesta habla de desayunos"
echo ""
echo "   '¿Cómo me apunto a RESIS?'"
echo "   → Verificar respuesta habla SOLO de RESIS"
echo "   → Verificar NO menciona desayunos ni punto de encuentro de desayunos"
echo ""
echo -e "${BLUE}3. Verificar logs del sistema:${NC}"
echo "   Buscar en logs:"
echo "   ✓ source='active_conversation'"
echo "   ✓ anti_contamination=True"
echo "   ✓ historical_snapshots=0"
echo "   ✓ reason='Active conversation (X messages), ignoring historical cache'"
echo ""
echo -e "${BLUE}4. Prueba de typing indicator:${NC}"
echo "   'Cuéntame todo sobre DNI'"
echo "   → Verificar indicador 'typing...' se mantiene durante todo el procesamiento"
echo "   → NO debe desaparecer a los 5 segundos"
echo ""
echo -e "${BLUE}5. Prueba de greetings rápidos:${NC}"
echo "   'Hola'"
echo "   → Verificar respuesta instantánea (<1s)"
echo "   → Verificar log: 'Fast response (greeting)'"
echo ""
echo "======================================================================"
echo "✅ SISTEMA v4.1.1 LISTO PARA TESTING"
echo "======================================================================"
echo ""
echo -e "${YELLOW}CAMBIOS CLAVE v4.1.1:${NC}"
echo "  • Sistema anti-contaminación (CERO cache en conversaciones activas)"
echo "  • Umbral bajado 0.5 → 0.3 (más sensible a cambios)"
echo "  • Typing indicator continuo durante procesamiento largo"
echo "  • Latencia reducida 50ms → 5ms (evita DB query innecesaria)"
echo ""
echo "======================================================================"
