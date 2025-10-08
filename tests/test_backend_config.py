#!/usr/bin/env python3
"""Test simple de configuración de backend"""

from benchmark import BenchmarkRunner

print("Creando BenchmarkRunner...")
runner = BenchmarkRunner()

print(f"\nConfiguración:")
print(f"  backend: {runner.evaluator_config.get('backend')}")
print(f"  ollama_model: {runner.evaluator_config.get('ollama_model')}")

print("\nLlamando a setup() solo para ver mensajes de inicialización...")
try:
    runner.setup()
except KeyboardInterrupt:
    print("\nInterrumpido por el usuario")
