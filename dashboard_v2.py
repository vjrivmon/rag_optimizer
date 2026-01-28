#!/usr/bin/env python3
"""
📊 RAG Benchmark Dashboard - Versión Profesional

Dashboard minimalista con actualización en tiempo real

USO:
  python dashboard.py
  
Luego abre: http://localhost:8000
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
import sqlite3
import asyncio
import json
from pathlib import Path
from typing import List
from datetime import datetime
import tempfile
import os

# Para generación de PDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT

app = FastAPI(title="RAG Benchmark Dashboard")

# Ruta a la base de datos
DB_PATH = "results/benchmark.db"

# Lista de clientes WebSocket conectados
connected_clients: List[WebSocket] = []


# ============================================================================
# FUNCIONES DE CONSULTA A LA BD
# ============================================================================

def get_progress_stats():
    """Obtiene estadísticas actuales del benchmark"""
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Total de respuestas y evaluaciones
        cursor = conn.execute("""
            SELECT 
                COUNT(DISTINCT r.id) as total_responses,
                COUNT(DISTINCT e.id) as total_evaluations,
                COUNT(DISTINCT r.question_id) as total_questions,
                COUNT(DISTINCT r.model_name) as total_models
            FROM responses r
            LEFT JOIN evaluations e ON r.id = e.response_id
            WHERE r.error IS NULL
        """)
        totals = cursor.fetchone()
        
        # Progreso por modelo
        cursor = conn.execute("""
            SELECT 
                r.model_name,
                COUNT(DISTINCT r.id) as total,
                COUNT(DISTINCT e.id) as evaluated,
                AVG(e.combined_score) as avg_score,
                AVG(e.faithfulness) as avg_faithfulness,
                AVG(e.answer_relevancy) as avg_relevancy,
                AVG(e.context_precision) as avg_precision,
                AVG(e.context_recall) as avg_recall,
                AVG(e.answer_correctness) as avg_correctness,
                AVG(e.answer_similarity) as avg_similarity,
                AVG(r.generation_time) as avg_gen_time,
                AVG(e.evaluation_time) as avg_eval_time
            FROM responses r
            LEFT JOIN evaluations e ON r.id = e.response_id
            WHERE r.error IS NULL
            GROUP BY r.model_name
            ORDER BY avg_score DESC
        """)
        models = [
            {
                'name': row[0],
                'total': row[1],
                'evaluated': row[2],
                'progress': (row[2] / row[1] * 100) if row[1] > 0 else 0,
                'avg_score': round(row[3], 3) if row[3] else None,
                'faithfulness': round(row[4], 3) if row[4] else None,
                'relevancy': round(row[5], 3) if row[5] else None,
                'precision': round(row[6], 3) if row[6] else None,
                'recall': round(row[7], 3) if row[7] else None,
                'correctness': round(row[8], 3) if row[8] else None,
                'similarity': round(row[9], 3) if row[9] else None,
                'avg_gen_time': round(row[10], 2) if row[10] else None,
                'avg_eval_time': round(row[11], 2) if row[11] else None
            }
            for row in cursor.fetchall()
        ]
        
        # Actividad reciente (últimas 5 evaluaciones)
        cursor = conn.execute("""
            SELECT 
                r.model_name,
                r.question_id,
                e.combined_score,
                e.evaluated_at
            FROM evaluations e
            JOIN responses r ON e.response_id = r.id
            ORDER BY e.evaluated_at DESC
            LIMIT 5
        """)
        recent = [
            {
                'model': row[0],
                'question_id': row[1],
                'score': round(row[2], 3) if row[2] else None,
                'timestamp': row[3]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return {
            'total_responses': totals[0],
            'total_evaluations': totals[1],
            'total_questions': totals[2],
            'total_models': totals[3],
            'models': models,
            'recent_activity': recent,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'error': str(e),
            'total_responses': 0,
            'total_evaluations': 0,
            'total_questions': 0,
            'total_models': 0,
            'models': [],
            'recent_activity': [],
            'timestamp': datetime.now().isoformat()
        }


def get_detailed_report_data():
    """Obtiene datos detallados para el reporte PDF"""
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Cargar dataset para obtener respuestas esperadas
        dataset = []
        dataset_path = "data/evaluation_dataset.json"
        if os.path.exists(dataset_path):
            with open(dataset_path, 'r', encoding='utf-8') as f:
                dataset = json.load(f)
        
        # Crear diccionario de respuestas esperadas
        expected_answers = {
            q['question']: q.get('ground_truth', 'No disponible')
            for q in dataset
        }
        
        # Obtener todas las respuestas con evaluaciones
        cursor = conn.execute("""
            SELECT 
                r.question_id,
                r.question,
                r.model_name,
                r.answer,
                r.generation_time,
                e.combined_score,
                e.faithfulness,
                e.answer_relevancy,
                e.context_precision,
                e.context_recall,
                e.answer_correctness,
                e.answer_similarity
            FROM responses r
            LEFT JOIN evaluations e ON r.id = e.response_id
            WHERE r.error IS NULL
            ORDER BY r.question_id, e.combined_score DESC
        """)
        
        # Organizar por pregunta
        questions_data = {}
        for row in cursor.fetchall():
            q_id = row[0]
            question = row[1]
            
            if q_id not in questions_data:
                questions_data[q_id] = {
                    'question': question,
                    'expected_answer': expected_answers.get(question, 'No disponible'),
                    'responses': []
                }
            
            questions_data[q_id]['responses'].append({
                'model': row[2],
                'answer': row[3],
                'time': round(row[4], 2) if row[4] else None,
                'score': round(row[5], 3) if row[5] else None,
                'faithfulness': round(row[6], 3) if row[6] else None,
                'relevancy': round(row[7], 3) if row[7] else None,
                'precision': round(row[8], 3) if row[8] else None,
                'recall': round(row[9], 3) if row[9] else None,
                'correctness': round(row[10], 3) if row[10] else None,
                'similarity': round(row[11], 3) if row[11] else None,
            })
        
        conn.close()
        
        return list(questions_data.values())
    
    except Exception as e:
        print(f"Error obteniendo datos del reporte: {e}")
        return []


# ============================================================================
# ENDPOINTS HTTP
# ============================================================================

@app.get("/")
async def get_dashboard():
    """Página principal del dashboard"""
    html = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAG Benchmark Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --bg-primary: #0f1419;
            --bg-secondary: #1a1f2e;
            --bg-card: #232936;
            --text-primary: #e4e6eb;
            --text-secondary: #9ca3af;
            --border-color: #2d3748;
            --accent: #3b82f6;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'SF Pro Display', 'Segoe UI', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        /* Header */
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border-color);
        }
        
        .header h1 {
            font-size: 1.75rem;
            font-weight: 600;
            letter-spacing: -0.025em;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: var(--bg-secondary);
            border-radius: 8px;
            font-size: 0.875rem;
            color: var(--text-secondary);
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--success);
            animation: pulse 2s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }
        
        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.25rem;
        }
        
        .stat-label {
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        /* Models Section */
        .section {
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }
        
        .section-header {
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            color: var(--text-primary);
        }
        
        .model-item {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1.25rem;
            margin-bottom: 1rem;
        }
        
        .model-item:last-child {
            margin-bottom: 0;
        }
        
        .model-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        
        .model-name {
            font-size: 1rem;
            font-weight: 500;
            color: var(--text-primary);
        }
        
        .model-score {
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--accent);
        }
        
        .progress-bar {
            width: 100%;
            height: 6px;
            background: var(--bg-primary);
            border-radius: 3px;
            overflow: hidden;
            margin-bottom: 1rem;
        }
        
        .progress-fill {
            height: 100%;
            background: var(--accent);
            transition: width 0.5s ease;
        }
        
        .progress-text {
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin-bottom: 1rem;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
        }
        
        .metric-item {
            display: flex;
            flex-direction: column;
        }
        
        .metric-label {
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-bottom: 0.25rem;
        }
        
        .metric-value {
            font-size: 1rem;
            font-weight: 500;
            color: var(--text-primary);
        }
        
        .metric-value.good {
            color: var(--success);
        }
        
        .metric-value.medium {
            color: var(--warning);
        }
        
        .metric-value.bad {
            color: var(--danger);
        }
        
        /* Activity Log */
        .activity-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem;
            border-bottom: 1px solid var(--border-color);
        }
        
        .activity-item:last-child {
            border-bottom: none;
        }
        
        .activity-model {
            font-weight: 500;
            color: var(--text-primary);
        }
        
        .activity-question {
            color: var(--text-secondary);
            font-size: 0.875rem;
        }
        
        .activity-score {
            font-weight: 600;
            color: var(--accent);
        }
        
        .activity-time {
            font-size: 0.75rem;
            color: var(--text-secondary);
        }
        
        .empty-state {
            text-align: center;
            padding: 2rem;
            color: var(--text-secondary);
        }
        
        /* Status Badge */
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 500;
        }
        
        .status-badge.complete {
            background: rgba(16, 185, 129, 0.1);
            color: var(--success);
        }
        
        .status-badge.evaluating {
            background: rgba(59, 130, 246, 0.1);
            color: var(--accent);
        }
        
        .status-badge.pending {
            background: rgba(156, 163, 175, 0.1);
            color: var(--text-secondary);
        }
        
        /* Export Button */
        .export-button {
            padding: 0.5rem 1rem;
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .export-button:hover {
            background: #2563eb;
            transform: translateY(-1px);
        }
        
        .export-button:active {
            transform: translateY(0);
        }
        
        .export-button:disabled {
            background: var(--text-secondary);
            cursor: not-allowed;
            transform: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>RAG Benchmark Dashboard</h1>
            <div style="display: flex; gap: 1rem; align-items: center;">
                <button class="export-button" onclick="exportPDF()">
                    📄 Exportar PDF
                </button>
                <div class="status-indicator">
                    <div class="status-dot"></div>
                    <span>En vivo</span>
                </div>
            </div>
        </div>
        
        <!-- Stats -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Preguntas</div>
                <div class="stat-value" id="total-questions">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Modelos</div>
                <div class="stat-value" id="total-models">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Respuestas</div>
                <div class="stat-value" id="total-responses">-</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Evaluaciones</div>
                <div class="stat-value" id="total-evaluations">-</div>
            </div>
        </div>
        
        <!-- Live Events (Nueva sección) -->
        <div class="section" id="live-events-section" style="display: none;">
            <div class="section-header">🔴 Ejecución en Vivo</div>
            
            <!-- Current Question Card -->
            <div id="current-question-card" style="display: none; background: var(--bg-card); border: 1px solid var(--accent); border-radius: 8px; padding: 1rem; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <div style="font-size: 0.875rem; color: var(--text-secondary);">Pregunta Actual</div>
                    <div id="current-q-number" style="font-size: 0.875rem; color: var(--accent);"></div>
                </div>
                <div id="current-question-text" style="font-size: 1rem; color: var(--text-primary); margin-bottom: 1rem;"></div>
                <div id="current-model" style="font-size: 0.875rem; color: var(--text-secondary);"></div>
            </div>
            
            <!-- Live Log Console -->
            <div style="background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; padding: 1rem;">
                <div style="font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 0.5rem;">Console de Eventos</div>
                <div id="live-log-container" style="max-height: 400px; overflow-y: auto; font-family: 'Courier New', monospace; font-size: 0.875rem;">
                    <div style="color: var(--text-secondary); text-align: center; padding: 2rem;">
                        Esperando eventos del benchmark...
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Models -->
        <div class="section">
            <div class="section-header">Modelos</div>
            <div id="models-container"></div>
        </div>
        
        <!-- Recent Activity -->
        <div class="section">
            <div class="section-header">Actividad Reciente</div>
            <div id="activity-container"></div>
        </div>
    </div>
    
    <script>
        let ws = null;
        let reconnectTimeout = null;
        let liveLogBuffer = [];
        let maxLogEntries = 50;
        let currentPhase = null;
        
        function connectWebSocket() {
            ws = new WebSocket(`ws://${window.location.host}/ws`);
            
            ws.onopen = function() {
                console.log('WebSocket conectado');
                if (reconnectTimeout) {
                    clearTimeout(reconnectTimeout);
                    reconnectTimeout = null;
                }
            };
            
            ws.onmessage = function(event) {
                const message = JSON.parse(event.data);
                
                // Distinguir entre tipos de mensajes
                if (message.type === 'stats_update') {
                    updateDashboard(message.data);
                } else if (message.type === 'event_history') {
                    // Cargar historial de eventos
                    message.data.events.forEach(evt => handleLiveEvent(evt));
                } else {
                    // Evento en tiempo real del benchmark
                    handleLiveEvent(message);
                }
            };
            
            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
            
            ws.onclose = function() {
                console.log('WebSocket desconectado, reintentando en 3s...');
                reconnectTimeout = setTimeout(connectWebSocket, 3000);
            };
        }
        
        function handleLiveEvent(event) {
            const eventType = event.type;
            const data = event.data;
            const timestamp = new Date(event.timestamp).toLocaleTimeString();
            
            // Mostrar sección de eventos en vivo si hay actividad
            const liveSection = document.getElementById('live-events-section');
            if (liveSection) {
                liveSection.style.display = 'block';
            }
            
            // Manejar diferentes tipos de eventos
            switch(eventType) {
                case 'phase_start':
                    currentPhase = data.phase;
                    addLogEntry(`🚀 FASE ${data.phase === 'generation' ? '1: GENERACIÓN' : '2: EVALUACIÓN'} INICIADA`, 'info', timestamp);
                    if (data.phase === 'generation') {
                        addLogEntry(`   Preguntas: ${data.total_questions} | Modelos: ${data.total_models} | Total: ${data.total_responses}`, 'info', timestamp);
                    } else {
                        addLogEntry(`   Respuestas pendientes: ${data.total_pending} | Concurrencia: ${data.max_concurrent}`, 'info', timestamp);
                    }
                    break;
                    
                case 'question_start':
                    addLogEntry(`📝 [${data.q_idx}/${data.total_questions}] P${data.question_id}: ${data.question}`, 'question', timestamp);
                    // Actualizar tarjeta de pregunta actual
                    updateCurrentQuestion(data);
                    break;
                    
                case 'model_start':
                    addLogEntry(`   🤖 ${data.model_name} procesando...`, 'model', timestamp);
                    updateCurrentModel(data.model_name);
                    break;
                    
                case 'model_complete':
                    if (data.success) {
                        const symbol = data.confidence >= 0.8 ? '✅' : '⚠️';
                        const extra = data.is_problematic ? ' 🚨' : '';
                        addLogEntry(`   ${symbol} ${data.model_name}: ${data.generation_time.toFixed(1)}s (${data.config_name}) Score=${data.confidence.toFixed(2)}${extra}`, 'success', timestamp);
                        if (data.answer) {
                            addLogEntry(`      Respuesta: ${data.answer}`, 'detail', timestamp);
                        }
                    } else {
                        addLogEntry(`   ❌ ${data.model_name}: Error - ${data.error}`, 'error', timestamp);
                    }
                    break;
                    
                case 'evaluation_complete':
                    if (data.success) {
                        const score = data.metrics.combined_score.toFixed(3);
                        addLogEntry(`   ✅ ${data.model_name}: Score ${score}`, 'success', timestamp);
                        addLogEntry(`      F=${data.metrics.faithfulness.toFixed(2)} R=${data.metrics.answer_relevancy.toFixed(2)} P=${data.metrics.context_precision.toFixed(2)}`, 'detail', timestamp);
                    } else {
                        addLogEntry(`   ❌ ${data.model_name}: ${data.error}`, 'error', timestamp);
                    }
                    break;
                    
                case 'log':
                    addLogEntry(data.message, data.level || 'info', timestamp);
                    break;
            }
        }
        
        function addLogEntry(message, level, timestamp) {
            // Colores según nivel
            const colors = {
                'info': 'var(--text-primary)',
                'question': 'var(--accent)',
                'model': 'var(--text-secondary)',
                'success': 'var(--success)',
                'error': 'var(--danger)',
                'detail': 'var(--text-secondary)'
            };
            
            const entry = {
                message: message,
                level: level,
                timestamp: timestamp,
                color: colors[level] || colors['info']
            };
            
            liveLogBuffer.push(entry);
            
            // Mantener solo las últimas N entradas
            if (liveLogBuffer.length > maxLogEntries) {
                liveLogBuffer.shift();
            }
            
            // Renderizar log
            renderLiveLog();
        }
        
        function renderLiveLog() {
            const container = document.getElementById('live-log-container');
            if (!container) return;
            
            if (liveLogBuffer.length === 0) {
                container.innerHTML = '<div style="color: var(--text-secondary); text-align: center; padding: 2rem;">Esperando eventos del benchmark...</div>';
                return;
            }
            
            const html = liveLogBuffer.map(entry => {
                return `<div style="color: ${entry.color}; padding: 0.25rem 0; border-bottom: 1px solid var(--border-color);">
                    <span style="color: var(--text-secondary); font-size: 0.75rem;">[${entry.timestamp}]</span> ${entry.message}
                </div>`;
            }).join('');
            
            container.innerHTML = html;
            
            // Auto-scroll al final
            container.scrollTop = container.scrollHeight;
        }
        
        function updateCurrentQuestion(data) {
            const card = document.getElementById('current-question-card');
            const qNumber = document.getElementById('current-q-number');
            const qText = document.getElementById('current-question-text');
            
            if (card && qNumber && qText) {
                card.style.display = 'block';
                qNumber.textContent = `P${data.question_id} [${data.q_idx}/${data.total_questions}]`;
                qText.textContent = data.question;
            }
        }
        
        function updateCurrentModel(modelName) {
            const modelDiv = document.getElementById('current-model');
            if (modelDiv) {
                modelDiv.textContent = `🤖 Modelo actual: ${modelName}`;
            }
        }
        
        function updateDashboard(data) {
            // Actualizar estadísticas globales
            document.getElementById('total-questions').textContent = data.total_questions || 0;
            document.getElementById('total-models').textContent = data.total_models || 0;
            document.getElementById('total-responses').textContent = data.total_responses || 0;
            document.getElementById('total-evaluations').textContent = data.total_evaluations || 0;
            
            // Actualizar modelos
            const modelsHtml = data.models.map(model => {
                const progress = model.progress || 0;
                const score = model.avg_score;
                const scoreClass = score >= 0.85 ? 'good' : score >= 0.70 ? 'medium' : 'bad';
                
                let statusBadge = '';
                if (progress === 100) {
                    statusBadge = '<span class="status-badge complete">Completado</span>';
                } else if (progress > 0) {
                    statusBadge = '<span class="status-badge evaluating">Evaluando</span>';
                } else {
                    statusBadge = '<span class="status-badge pending">Pendiente</span>';
                }
                
                return `
                    <div class="model-item">
                        <div class="model-header">
                            <div class="model-name">${model.name}</div>
                            <div class="model-score">
                                ${score !== null ? score.toFixed(3) : '---'}
                            </div>
                        </div>
                        
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${progress}%"></div>
                        </div>
                        
                        <div class="progress-text">
                            ${model.evaluated}/${model.total} evaluaciones (${progress.toFixed(1)}%)
                            ${statusBadge}
                        </div>
                        
                        ${model.avg_score !== null ? `
                        <div class="metrics-grid">
                            <div class="metric-item">
                                <div class="metric-label">Faithfulness</div>
                                <div class="metric-value ${getMetricClass(model.faithfulness)}">
                                    ${model.faithfulness !== null ? model.faithfulness.toFixed(3) : '---'}
                                </div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-label">Relevancy</div>
                                <div class="metric-value ${getMetricClass(model.relevancy)}">
                                    ${model.relevancy !== null ? model.relevancy.toFixed(3) : '---'}
                                </div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-label">Precision</div>
                                <div class="metric-value ${getMetricClass(model.precision)}">
                                    ${model.precision !== null ? model.precision.toFixed(3) : '---'}
                                </div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-label">Recall</div>
                                <div class="metric-value ${getMetricClass(model.recall)}">
                                    ${model.recall !== null ? model.recall.toFixed(3) : '---'}
                                </div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-label">Correctness</div>
                                <div class="metric-value ${getMetricClass(model.correctness)}">
                                    ${model.correctness !== null ? model.correctness.toFixed(3) : '---'}
                                </div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-label">Similarity</div>
                                <div class="metric-value ${getMetricClass(model.similarity)}">
                                    ${model.similarity !== null ? model.similarity.toFixed(3) : '---'}
                                </div>
                            </div>
                        </div>
                        ` : ''}
                    </div>
                `;
            }).join('');
            
            document.getElementById('models-container').innerHTML = modelsHtml || 
                '<div class="empty-state">No hay modelos evaluados aún</div>';
            
            // Actualizar actividad reciente
            const activityHtml = data.recent_activity.map(item => `
                <div class="activity-item">
                    <div>
                        <div class="activity-model">${item.model}</div>
                        <div class="activity-question">Pregunta ${item.question_id}</div>
                    </div>
                    <div style="text-align: right;">
                        <div class="activity-score">
                            ${item.score !== null ? item.score.toFixed(3) : '---'}
                        </div>
                        <div class="activity-time">${formatTime(item.timestamp)}</div>
                    </div>
                </div>
            `).join('');
            
            document.getElementById('activity-container').innerHTML = activityHtml || 
                '<div class="empty-state">Sin actividad reciente</div>';
        }
        
        function getMetricClass(value) {
            if (value === null) return '';
            if (value >= 0.85) return 'good';
            if (value >= 0.70) return 'medium';
            return 'bad';
        }
        
        function formatTime(timestamp) {
            if (!timestamp) return '';
            const date = new Date(timestamp);
            const now = new Date();
            const diff = (now - date) / 1000;
            
            if (diff < 60) return 'hace un momento';
            if (diff < 3600) return `hace ${Math.floor(diff/60)}m`;
            if (diff < 86400) return `hace ${Math.floor(diff/3600)}h`;
            return `hace ${Math.floor(diff/86400)}d`;
        }
        
        async function exportPDF() {
            const button = document.querySelector('.export-button');
            button.disabled = true;
            button.textContent = '⏳ Generando PDF...';
            
            try {
                const response = await fetch('/export-pdf', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                
                if (!response.ok) {
                    throw new Error('Error al generar PDF');
                }
                
                // Descargar el PDF
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `benchmark_report_${new Date().toISOString().split('T')[0]}.pdf`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                button.textContent = '✅ PDF generado';
                setTimeout(() => {
                    button.disabled = false;
                    button.textContent = '📄 Exportar PDF';
                }, 2000);
            } catch (error) {
                console.error('Error:', error);
                button.textContent = '❌ Error';
                setTimeout(() => {
                    button.disabled = false;
                    button.textContent = '📄 Exportar PDF';
                }, 2000);
            }
        }
        
        // Iniciar conexión WebSocket
        connectWebSocket();
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html)


@app.get("/api/stats")
async def get_stats():
    """API para obtener estadísticas actuales"""
    return get_progress_stats()


def generate_pdf_report(output_path: str):
    """Genera un reporte PDF profesional con los resultados del benchmark"""
    
    # Configurar documento
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1f2e'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1a1f2e'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2d3748'),
        spaceAfter=6,
        fontName='Helvetica'
    )
    
    # Elementos del documento
    elements = []
    
    # =========================================================================
    # PORTADA
    # =========================================================================
    elements.append(Spacer(1, 2*inch))
    elements.append(Paragraph("Reporte de Benchmark RAG", title_style))
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph(
        f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        normal_style
    ))
    elements.append(PageBreak())
    
    # =========================================================================
    # EXPLICACIÓN DE MÉTRICAS
    # =========================================================================
    elements.append(Paragraph("Métricas de Evaluación RAGAs", heading_style))
    elements.append(Spacer(1, 0.2*inch))
    
    metrics_explanation = [
        ("Faithfulness (Fidelidad)", 
         "Mide si la respuesta es fiel al contexto recuperado. Evalúa si el modelo inventa información no presente en el contexto. Valores cercanos a 1.0 indican que el modelo no alucina."),
        
        ("Answer Relevancy (Relevancia)", 
         "Evalúa si la respuesta es relevante para la pregunta formulada. Una respuesta puede ser correcta pero no relevante si no aborda directamente la pregunta. Valores altos indican respuestas directas y pertinentes."),
        
        ("Context Precision (Precisión del Contexto)", 
         "Mide la precisión del contexto recuperado. Evalúa si los documentos recuperados son realmente relevantes para responder la pregunta. Valores altos indican que el sistema RAG recupera información precisa."),
        
        ("Context Recall (Exhaustividad del Contexto)", 
         "Evalúa si se recuperó todo el contexto necesario para responder completamente la pregunta. Valores bajos indican que falta información relevante."),
        
        ("Answer Correctness (Corrección)", 
         "Mide la corrección factual de la respuesta comparada con la respuesta esperada. Evalúa tanto la precisión como la exhaustividad de la información."),
        
        ("Answer Similarity (Similitud)", 
         "Evalúa la similitud semántica entre la respuesta generada y la respuesta esperada. Valores altos indican que la respuesta es conceptualmente similar a lo esperado."),
    ]
    
    for metric_name, explanation in metrics_explanation:
        elements.append(Paragraph(f"<b>{metric_name}</b>", normal_style))
        elements.append(Paragraph(explanation, normal_style))
        elements.append(Spacer(1, 0.1*inch))
    
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph(
        "<b>Interpretación de Scores:</b> Todas las métricas van de 0.0 (peor) a 1.0 (mejor). "
        "Un score ≥0.85 es excelente, ≥0.70 es bueno, y <0.70 requiere mejora.",
        normal_style
    ))
    
    elements.append(PageBreak())
    
    # =========================================================================
    # TABLA COMPARATIVA POR PREGUNTA
    # =========================================================================
    elements.append(Paragraph("Comparativa Detallada por Pregunta", heading_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Obtener datos
    questions_data = get_detailed_report_data()
    
    for q_data in questions_data:
        # Título de la pregunta
        elements.append(Paragraph(f"<b>Pregunta:</b> {q_data['question']}", normal_style))
        elements.append(Spacer(1, 0.1*inch))
        
        # Respuesta esperada
        expected = q_data['expected_answer']
        if len(expected) > 200:
            expected = expected[:200] + "..."
        elements.append(Paragraph(f"<b>Respuesta Esperada:</b> {expected}", normal_style))
        elements.append(Spacer(1, 0.15*inch))
        
        # Tabla con respuestas de cada modelo
        table_data = [
            ['Modelo', 'Respuesta', 'Tiempo (s)', 'Score', 'Faith.', 'Relev.', 'Correct.']
        ]
        
        for resp in q_data['responses']:
            # Truncar respuesta si es muy larga
            answer = resp['answer']
            if len(answer) > 150:
                answer = answer[:150] + "..."
            
            table_data.append([
                Paragraph(resp['model'], normal_style),
                Paragraph(answer, normal_style),
                f"{resp['time']:.1f}s" if resp['time'] else '-',
                f"{resp['score']:.3f}" if resp['score'] else '-',
                f"{resp['faithfulness']:.2f}" if resp['faithfulness'] else '-',
                f"{resp['relevancy']:.2f}" if resp['relevancy'] else '-',
                f"{resp['correctness']:.2f}" if resp['correctness'] else '-',
            ])
        
        # Crear tabla
        table = Table(table_data, colWidths=[1.2*inch, 4*inch, 0.8*inch, 0.7*inch, 0.6*inch, 0.6*inch, 0.7*inch])
        table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            
            # Body
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2d3748')),
            ('ALIGN', (2, 1), (-1, -1), 'CENTER'),  # Alinear números al centro
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Page break cada 2 preguntas
        if questions_data.index(q_data) % 2 == 1:
            elements.append(PageBreak())
    
    # Construir PDF
    doc.build(elements)


@app.post("/export-pdf")
async def export_pdf():
    """Endpoint para generar y descargar el PDF"""
    try:
        # Crear archivo temporal
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_path = temp_file.name
        temp_file.close()
        
        # Generar PDF
        generate_pdf_report(temp_path)
        
        # Devolver archivo
        return FileResponse(
            temp_path,
            media_type='application/pdf',
            filename=f'benchmark_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
            background=None
        )
    
    except Exception as e:
        print(f"Error generando PDF: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


@app.get("/api/stats")
async def get_stats():
    """API para obtener estadísticas actuales"""
    return get_progress_stats()


# ============================================================================
# WEBSOCKET PARA ACTUALIZACIONES EN TIEMPO REAL
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint para streaming de actualizaciones y eventos en tiempo real"""
    await websocket.accept()
    connected_clients.append(websocket)
    
    # Registrar en el broadcaster para recibir eventos del benchmark
    try:
        from src.utils.event_broadcaster import get_broadcaster
        broadcaster = get_broadcaster()
        broadcaster.subscribe(websocket)
    except Exception as e:
        print(f"⚠️ No se pudo conectar al broadcaster: {e}")
        broadcaster = None
    
    try:
        # Enviar actualización inicial inmediatamente
        stats = get_progress_stats()
        await websocket.send_json({
            'type': 'stats_update',
            'data': stats,
            'timestamp': datetime.now().isoformat()
        })
        
        # Enviar historial de eventos si hay broadcaster
        last_event_timestamp = None
        if broadcaster:
            history = broadcaster.get_history()
            if history:
                await websocket.send_json({
                    'type': 'event_history',
                    'data': {'events': history},
                    'timestamp': datetime.now().isoformat()
                })
                # Guardar último timestamp
                if history:
                    last_event_timestamp = history[-1].get('timestamp')
        
        # Loop de actualizaciones periódicas
        # - Eventos nuevos cada 0.5s (polling rápido)
        # - Stats cada 2s
        stats_counter = 0
        while True:
            try:
                await asyncio.sleep(0.5)
                
                # Enviar eventos nuevos si hay broadcaster
                if broadcaster:
                    # Recargar eventos desde archivo (comunicación entre procesos)
                    broadcaster.reload_events_from_file()
                    
                    recent_events = broadcaster.get_recent_events(last_event_timestamp)
                    if recent_events:
                        # Enviar cada evento individualmente
                        for event in recent_events:
                            await websocket.send_json(event)
                        # Actualizar último timestamp
                        last_event_timestamp = recent_events[-1].get('timestamp')
                
                # Enviar stats cada 2 segundos (cada 4 iteraciones de 0.5s)
                stats_counter += 1
                if stats_counter >= 4:
                    stats_counter = 0
                    stats = get_progress_stats()
                    await websocket.send_json({
                        'type': 'stats_update',
                        'data': stats,
                        'timestamp': datetime.now().isoformat()
                    })
            except Exception as e:
                print(f"⚠️ Error en loop WebSocket: {e}")
                break
    
    except WebSocketDisconnect:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        if broadcaster:
            broadcaster.unsubscribe(websocket)
        print(f"Cliente desconectado. Quedan {len(connected_clients)} clientes")
    
    except Exception as e:
        print(f"Error en WebSocket: {e}")
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        if broadcaster:
            broadcaster.unsubscribe(websocket)


# ============================================================================
# INICIO DE LA APLICACIÓN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n🚀 Iniciando RAG Benchmark Dashboard Profesional...")
    print("=" * 60)
    print("📊 Dashboard: http://localhost:8000")
    print("📡 API Stats: http://localhost:8000/api/stats")
    print("=" * 60)
    
    # Verificar que existe la base de datos
    if not Path(DB_PATH).exists():
        print("⚠️  Advertencia: No se encuentra la base de datos")
        print(f"   Esperada en: {DB_PATH}")
        print("   Ejecuta primero: python benchmark_v2.py --phase generation")
    else:
        print("✅ Base de datos encontrada")
    
    print("\n💡 El dashboard se actualizará automáticamente cada 2 segundos")
    print("=" * 60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")