#!/usr/bin/env python3
"""
Telegram Bot Launcher - Chatbot DNI MVP
=========================================

Script simple para ejecutar el bot de Telegram.

Uso:
    python run_telegram_bot.py
    # o
    ./run_telegram_bot.py

Requisitos:
    - PostgreSQL corriendo (docker-compose up -d)
    - TELEGRAM_BOT_TOKEN configurado en .env
    - Dependencias instaladas (pip install -r requirements.txt)
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import main function
from src.telegram.bot import main

if __name__ == "__main__":
    print("=" * 70)
    print("🤖 CHATBOT DNI - TELEGRAM BOT MVP")
    print("=" * 70)
    print()
    print("📱 Bot de Telegram con persistencia de contexto")
    print("💾 PostgreSQL + RAG + Context Tracking")
    print()
    print("🔄 Presiona Ctrl+C para detener el bot")
    print("=" * 70)
    print()

    # Run bot
    main()
