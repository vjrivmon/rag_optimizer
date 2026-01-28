#!/usr/bin/env python3
"""
🔔 Event Broadcaster - Sistema de eventos en tiempo real para el dashboard

Sistema thread-safe y no bloqueante que captura eventos del benchmark
y los transmite a clientes WebSocket conectados.

Características:
- Singleton para única instancia global
- Cola en memoria con límite (últimos 100 eventos)
- Persistencia en archivo temporal para comunicación entre procesos
- No bloquea si no hay clientes conectados
- Fallback seguro ante errores
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque
import threading
import tempfile
from pathlib import Path


class EventBroadcaster:
    """Broadcaster singleton para eventos del benchmark"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.clients = []  # Lista de WebSocket clientes
        self.event_history = deque(maxlen=100)  # Últimos 100 eventos
        self.enabled = True
        
        # Archivo temporal para comunicación entre procesos
        self.events_file = Path(tempfile.gettempdir()) / "rag_benchmark_events.json"
        
        # Cargar eventos existentes si hay
        self._load_events_from_file()
        
        print(f"📡 EventBroadcaster inicializado (eventos persistentes en {self.events_file})")
    
    def emit(self, event_type: str, data: Dict[str, Any]):
        """
        Emite un evento a todos los clientes conectados
        
        Args:
            event_type: Tipo de evento (log, question_start, model_complete, etc.)
            data: Datos del evento
        """
        if not self.enabled:
            return
        
        try:
            # Crear evento con timestamp
            event = {
                'type': event_type,
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            # Guardar en historial
            self.event_history.append(event)
            
            # Guardar en archivo para persistencia entre procesos
            self._save_events_to_file()
            
            # DEBUG: Log para verificar que se están guardando eventos
            if len(self.event_history) <= 5:  # Solo los primeros 5
                print(f"📡 Evento guardado: {event_type} (total: {len(self.event_history)})")
            
            # Enviar a clientes conectados (si hay alguno)
            if self.clients:
                # Intentar broadcast sin bloquear el hilo principal
                # Guardar el evento para que el dashboard lo recoja en el próximo poll
                pass  # Los clientes recibirán el evento a través del historial
                
        except Exception as e:
            # Fallar silenciosamente para no interrumpir el benchmark
            print(f"⚠️ Error en EventBroadcaster.emit: {e}")
    
    async def _broadcast(self, event: Dict[str, Any]):
        """Envía evento a todos los clientes (async)"""
        disconnected = []
        
        for client in self.clients:
            try:
                await client.send_json(event)
            except Exception as e:
                # Marcar cliente desconectado
                print(f"⚠️ Cliente desconectado: {e}")
                disconnected.append(client)
        
        # Limpiar clientes desconectados
        for client in disconnected:
            if client in self.clients:
                self.clients.remove(client)
    
    def subscribe(self, websocket):
        """Registra un nuevo cliente WebSocket"""
        self.clients.append(websocket)
        print(f"📡 Cliente conectado. Total clientes: {len(self.clients)}")
    
    def unsubscribe(self, websocket):
        """Desregistra un cliente WebSocket"""
        if websocket in self.clients:
            self.clients.remove(websocket)
            print(f"📡 Cliente desconectado. Total clientes: {len(self.clients)}")
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Obtiene historial de eventos"""
        return list(self.event_history)
    
    def get_recent_events(self, since_timestamp: str = None) -> List[Dict[str, Any]]:
        """Obtiene eventos recientes desde un timestamp"""
        if not since_timestamp:
            return list(self.event_history)
        
        recent = []
        for event in self.event_history:
            if event.get('timestamp', '') > since_timestamp:
                recent.append(event)
        return recent
    
    def disable(self):
        """Deshabilita el broadcaster"""
        self.enabled = False
    
    def enable(self):
        """Habilita el broadcaster"""
        self.enabled = True
    
    def clear_history(self):
        """Limpia el historial de eventos"""
        self.event_history.clear()
        # También limpiar archivo
        try:
            if self.events_file.exists():
                self.events_file.unlink()
        except Exception:
            pass
    
    def _save_events_to_file(self):
        """Guarda eventos en archivo para comunicación entre procesos"""
        try:
            with open(self.events_file, 'w') as f:
                json.dump(list(self.event_history), f)
        except Exception as e:
            # Fallar silenciosamente
            pass
    
    def _load_events_from_file(self):
        """Carga eventos desde archivo"""
        try:
            if self.events_file.exists():
                with open(self.events_file, 'r') as f:
                    events = json.load(f)
                    for event in events[-100:]:  # Solo últimos 100
                        self.event_history.append(event)
        except Exception as e:
            # Fallar silenciosamente
            pass
    
    def reload_events_from_file(self):
        """Recarga eventos desde archivo (para dashboard)"""
        try:
            if self.events_file.exists():
                with open(self.events_file, 'r') as f:
                    events = json.load(f)
                    # Reemplazar historial con eventos del archivo
                    self.event_history.clear()
                    for event in events[-100:]:
                        self.event_history.append(event)
        except Exception:
            pass


# Instancia global singleton
_broadcaster = EventBroadcaster()


def get_broadcaster() -> EventBroadcaster:
    """Obtiene la instancia global del broadcaster"""
    return _broadcaster

