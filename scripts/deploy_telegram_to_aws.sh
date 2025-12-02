#!/bin/bash

# ============================================================================
# Script de Deployment - Telegram Bot a AWS
# ============================================================================
#
# Este script:
# 1. Prepara los archivos necesarios para el bot de Telegram
# 2. Los sube al servidor AWS
# 3. Ejecuta el script de instalación en el servidor
#
# USO:
#   ./scripts/deploy_telegram_to_aws.sh
#
# IMPORTANTE:
# - NO toca /var/www/html/ (chatbot web sigue funcionando)
# - Crea directorio separado /home/ec2-user/telegram-bot/
# - Reutiliza RAG y documentos mediante symlinks
# ============================================================================

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "========================================================================"
echo "🚀 DEPLOYMENT: TELEGRAM BOT TO AWS"
echo "========================================================================"
echo ""

# ============================================================================
# 1. CONFIGURACIÓN
# ============================================================================

AWS_HOST="ec2-user@34.224.93.171"
AWS_KEY="/home/vicente/Descargas/voluntarios.pem"
REMOTE_DIR="/home/ec2-user/telegram-bot"
TEMP_DIR="/tmp/telegram-bot-deployment"

echo -e "${BLUE}📋 Configuración:${NC}"
echo "   AWS Host: $AWS_HOST"
echo "   Remote Dir: $REMOTE_DIR"
echo "   SSH Key: $AWS_KEY"
echo ""

# ============================================================================
# 2. PREPARAR DIRECTORIO TEMPORAL
# ============================================================================

echo -e "${BLUE}📦 Preparando archivos para deployment...${NC}"

# Limpiar si existe
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

# Copiar archivos necesarios
echo "   ✓ Copiando src/telegram/"
cp -r src/telegram "$TEMP_DIR/"

echo "   ✓ Copiando src/services/"
cp -r src/services "$TEMP_DIR/"

echo "   ✓ Copiando src/database/"
cp -r src/database "$TEMP_DIR/"

echo "   ✓ Copiando src/core/persistent_context_tracker.py"
mkdir -p "$TEMP_DIR/src/core"
cp src/core/persistent_context_tracker.py "$TEMP_DIR/src/core/"

echo "   ✓ Copiando alembic/"
cp -r alembic "$TEMP_DIR/"
cp alembic.ini "$TEMP_DIR/"

echo "   ✓ Copiando run_telegram_bot.py"
cp run_telegram_bot.py "$TEMP_DIR/"

echo "   ✓ Copiando requirements-dev.txt como requirements.txt"
cp requirements-dev.txt "$TEMP_DIR/requirements.txt"

echo "   ✓ Copiando docker-compose.yml"
cp docker-compose.yml "$TEMP_DIR/"

echo "   ✓ Copiando .env.example"
cp .env.example "$TEMP_DIR/"

echo ""

# ============================================================================
# 3. CREAR SCRIPT DE INSTALACIÓN REMOTA
# ============================================================================

echo -e "${BLUE}📝 Creando script de instalación remota...${NC}"

cat > "$TEMP_DIR/install.sh" << 'EOF'
#!/bin/bash

# ============================================================================
# Script de Instalación - Telegram Bot en AWS
# ============================================================================
# Este script SE EJECUTA EN EL SERVIDOR AWS
# ============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================================================"
echo "🔧 INSTALACIÓN: TELEGRAM BOT EN AWS"
echo "========================================================================"
echo ""

# ============================================================================
# 1. CREAR SYMLINKS A CÓDIGO COMPARTIDO
# ============================================================================

echo -e "${BLUE}🔗 Creando symlinks a código compartido...${NC}"

# Directorio base del chatbot web
WEB_DIR="/var/www/html"

# Crear symlinks a src/core/ (RAG engine)
echo "   ✓ Symlink src/core/ (RAG engine)"
ln -sf "$WEB_DIR/src/core/rag_engine.py" src/core/
ln -sf "$WEB_DIR/src/core/enhanced_rag_engine_new.py" src/core/
ln -sf "$WEB_DIR/src/core/model_wrapper.py" src/core/
ln -sf "$WEB_DIR/src/core/conversational_rag.py" src/core/
ln -sf "$WEB_DIR/src/core/context_tracker.py" src/core/
ln -sf "$WEB_DIR/src/core/intent_classifier.py" src/core/

# Crear symlink a data/ (documentos + vectorstore)
echo "   ✓ Symlink data/ (documentos + vectorstore)"
ln -sf "$WEB_DIR/data" data

# Crear directorio logs
mkdir -p logs

echo ""

# ============================================================================
# 2. VERIFICAR PYTHON Y VENV
# ============================================================================

echo -e "${BLUE}🐍 Configurando Python virtual environment...${NC}"

# Verificar Python 3.12
if ! command -v python3.12 &> /dev/null; then
    echo -e "${RED}❌ Python 3.12 no encontrado${NC}"
    echo "Instalando Python 3.12..."
    sudo dnf install -y python3.12 python3.12-pip python3.12-devel
fi

# Crear venv si no existe
if [ ! -d "venv" ]; then
    echo "   ✓ Creando virtual environment..."
    python3.12 -m venv venv
fi

# Activar venv e instalar dependencias
echo "   ✓ Instalando dependencias..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""

# ============================================================================
# 3. CONFIGURAR .ENV
# ============================================================================

echo -e "${BLUE}⚙️  Configurando .env...${NC}"

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Archivo .env no encontrado${NC}"
    echo "   Creando .env desde .env.example..."
    cp .env.example .env
    echo ""
    echo -e "${YELLOW}⚠️  IMPORTANTE: Debes editar .env y añadir:${NC}"
    echo "   - TELEGRAM_BOT_TOKEN=tu_token_aqui"
    echo ""
    echo "   Edita con: nano .env"
    echo ""
fi

echo ""

# ============================================================================
# 4. CONFIGURAR POSTGRESQL CON DOCKER
# ============================================================================

echo -e "${BLUE}🐘 Configurando PostgreSQL...${NC}"

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker no encontrado${NC}"
    echo "Instalando Docker..."
    sudo dnf install -y docker
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
fi

# Verificar Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker Compose no encontrado, instalando...${NC}"
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Iniciar PostgreSQL
echo "   ✓ Iniciando PostgreSQL..."
docker-compose up -d

# Esperar a que PostgreSQL esté listo
echo "   ✓ Esperando a que PostgreSQL esté listo..."
sleep 5

echo ""

# ============================================================================
# 5. EJECUTAR MIGRACIONES ALEMBIC
# ============================================================================

echo -e "${BLUE}📊 Ejecutando migraciones de base de datos...${NC}"

# Activar venv si no está activo
source venv/bin/activate

# Ejecutar migraciones
venv/bin/alembic upgrade head

echo ""

# ============================================================================
# 6. CREAR SERVICIO SYSTEMD
# ============================================================================

echo -e "${BLUE}🔧 Configurando servicio systemd...${NC}"

CURRENT_DIR=$(pwd)
VENV_PYTHON="$CURRENT_DIR/venv/bin/python"

# Crear archivo de servicio
sudo tee /etc/systemd/system/telegram-bot-dni.service > /dev/null << SERVICEEOF
[Unit]
Description=Chatbot DNI - Telegram Bot
After=network.target docker.service

[Service]
Type=simple
User=ec2-user
WorkingDirectory=$CURRENT_DIR
Environment="PATH=$CURRENT_DIR/venv/bin"
ExecStart=$VENV_PYTHON run_telegram_bot.py

# Restart automático si falla
Restart=always
RestartSec=10

# Logs
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Recargar systemd
sudo systemctl daemon-reload

echo "   ✓ Servicio systemd creado"
echo ""

# ============================================================================
# 7. RESUMEN
# ============================================================================

echo "========================================================================"
echo -e "${GREEN}✅ INSTALACIÓN COMPLETA${NC}"
echo "========================================================================"
echo ""
echo -e "${BLUE}📝 Próximos pasos:${NC}"
echo ""
echo "1. Configurar TELEGRAM_BOT_TOKEN en .env:"
echo "   nano .env"
echo ""
echo "2. Iniciar el bot:"
echo "   sudo systemctl start telegram-bot-dni"
echo ""
echo "3. Ver logs:"
echo "   sudo journalctl -u telegram-bot-dni -f"
echo ""
echo "4. Verificar estado:"
echo "   sudo systemctl status telegram-bot-dni"
echo ""
echo "5. Habilitar auto-start:"
echo "   sudo systemctl enable telegram-bot-dni"
echo ""
echo "========================================================================"

EOF

chmod +x "$TEMP_DIR/install.sh"

echo "   ✓ Script de instalación creado"
echo ""

# ============================================================================
# 4. SUBIR ARCHIVOS AL SERVIDOR
# ============================================================================

echo -e "${BLUE}📤 Subiendo archivos al servidor AWS...${NC}"

# Crear directorio remoto si no existe
ssh -i "$AWS_KEY" "$AWS_HOST" "mkdir -p $REMOTE_DIR"

# Subir archivos con rsync
echo "   ✓ Usando rsync para subir archivos..."
rsync -avz --progress \
    -e "ssh -i $AWS_KEY" \
    "$TEMP_DIR/" \
    "$AWS_HOST:$REMOTE_DIR/"

echo ""
echo -e "${GREEN}✅ Archivos subidos correctamente${NC}"
echo ""

# ============================================================================
# 5. EJECUTAR INSTALACIÓN REMOTA
# ============================================================================

echo -e "${BLUE}🚀 Ejecutando instalación en el servidor...${NC}"
echo ""

ssh -i "$AWS_KEY" "$AWS_HOST" "cd $REMOTE_DIR && bash install.sh"

echo ""

# ============================================================================
# 6. LIMPIAR ARCHIVOS TEMPORALES
# ============================================================================

echo -e "${BLUE}🧹 Limpiando archivos temporales...${NC}"
rm -rf "$TEMP_DIR"
echo "   ✓ Archivos temporales eliminados"
echo ""

# ============================================================================
# 7. RESUMEN FINAL
# ============================================================================

echo "========================================================================"
echo -e "${GREEN}🎉 DEPLOYMENT COMPLETADO${NC}"
echo "========================================================================"
echo ""
echo -e "${BLUE}Próximos pasos EN EL SERVIDOR:${NC}"
echo ""
echo "1. Conectar al servidor:"
echo "   ssh -i $AWS_KEY $AWS_HOST"
echo ""
echo "2. Ir al directorio del bot:"
echo "   cd $REMOTE_DIR"
echo ""
echo "3. Configurar TELEGRAM_BOT_TOKEN:"
echo "   nano .env"
echo ""
echo "4. Iniciar el bot:"
echo "   sudo systemctl start telegram-bot-dni"
echo ""
echo "5. Ver logs en tiempo real:"
echo "   sudo journalctl -u telegram-bot-dni -f"
echo ""
echo "========================================================================"
echo ""
