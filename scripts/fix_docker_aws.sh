#!/bin/bash

# ============================================================================
# FIX: Docker not running on AWS server
# ============================================================================
# Este script soluciona el problema de Docker daemon not running
# ============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "========================================================================"
echo "🔧 FIX: Docker Issue en AWS"
echo "========================================================================"
echo ""

# ============================================================================
# 1. VERIFICAR E INSTALAR DOCKER
# ============================================================================

echo -e "${BLUE}📦 Verificando Docker...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker no encontrado, instalando...${NC}"
    sudo dnf install -y docker
    echo "   ✓ Docker instalado"
else
    echo "   ✓ Docker ya está instalado"
fi

echo ""

# ============================================================================
# 2. INICIAR DOCKER SERVICE
# ============================================================================

echo -e "${BLUE}🚀 Iniciando Docker daemon...${NC}"

# Iniciar Docker
sudo systemctl start docker

# Verificar que está corriendo
if sudo systemctl is-active --quiet docker; then
    echo "   ✓ Docker daemon está corriendo"
else
    echo -e "${RED}❌ Docker daemon no pudo iniciar${NC}"
    exit 1
fi

# Habilitar auto-start
sudo systemctl enable docker
echo "   ✓ Docker auto-start habilitado"

echo ""

# ============================================================================
# 3. AÑADIR USUARIO AL GRUPO DOCKER
# ============================================================================

echo -e "${BLUE}👤 Configurando permisos de usuario...${NC}"

# Añadir usuario al grupo docker
sudo usermod -aG docker $USER

echo "   ✓ Usuario $USER añadido al grupo docker"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANTE: Debes ejecutar estos comandos después de este script:${NC}"
echo "   newgrp docker"
echo "   cd /home/ec2-user/telegram-bot"
echo "   docker-compose up -d"
echo ""

# ============================================================================
# 4. VERIFICAR DOCKER COMPOSE
# ============================================================================

echo -e "${BLUE}🔧 Verificando Docker Compose...${NC}"

if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker Compose no encontrado, instalando...${NC}"
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "   ✓ Docker Compose instalado"
else
    echo "   ✓ Docker Compose ya está instalado"
fi

echo ""

# ============================================================================
# 5. EJECUTAR DOCKER-COMPOSE CON SUDO (TEMPORAL)
# ============================================================================

echo -e "${BLUE}🐘 Iniciando PostgreSQL con Docker Compose...${NC}"
echo ""

cd /home/ec2-user/telegram-bot

# Usar sudo temporalmente hasta que el usuario haga newgrp
sudo docker-compose up -d postgres

echo ""
echo "   ✓ Esperando a que PostgreSQL esté listo..."
sleep 10

# Verificar que PostgreSQL está corriendo
if sudo docker-compose ps | grep -q "postgres.*Up"; then
    echo -e "${GREEN}   ✅ PostgreSQL está corriendo correctamente${NC}"
else
    echo -e "${RED}   ❌ PostgreSQL no pudo iniciar${NC}"
    echo ""
    echo "Logs de PostgreSQL:"
    sudo docker-compose logs postgres
    exit 1
fi

echo ""

# ============================================================================
# 6. RESUMEN
# ============================================================================

echo "========================================================================"
echo -e "${GREEN}✅ DOCKER FIXED${NC}"
echo "========================================================================"
echo ""
echo -e "${BLUE}Estado de contenedores:${NC}"
sudo docker-compose ps
echo ""
echo -e "${BLUE}Próximos pasos:${NC}"
echo ""
echo "1. Ejecutar migraciones de base de datos:"
echo "   cd /home/ec2-user/telegram-bot"
echo "   source venv/bin/activate"
echo "   alembic upgrade head"
echo ""
echo "2. Configurar TELEGRAM_BOT_TOKEN en .env:"
echo "   nano .env"
echo ""
echo "3. Iniciar el bot:"
echo "   sudo systemctl start telegram-bot-dni"
echo ""
echo "4. Ver logs:"
echo "   sudo journalctl -u telegram-bot-dni -f"
echo ""
echo "========================================================================"
