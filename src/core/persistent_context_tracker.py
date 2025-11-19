"""
Persistent Context Tracker - Rastreador de Contexto con Memoria Persistente
=============================================================================

Extiende ContextTracker añadiendo persistencia de largo plazo con PostgreSQL.

Características nuevas:
- Recuperación de contexto histórico (últimos 7 días)
- Exponential decay por recencia (half-life = 3 días)
- Merge inteligente de contextos reciente + histórico
- Snapshot automático cada 5 mensajes
- Cross-session memory (usuario vuelve días después)

Workflow:
1. Usuario envía mensaje
2. Recuperar contexto reciente (ventana deslizante de 4 mensajes)
3. Recuperar snapshots históricos (últimos 7 días)
4. Merge con exponential decay
5. Enriquecer query con contexto combinado
6. Guardar snapshot si es necesario
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone, timedelta
import math

from .context_tracker import ContextTracker
from ..services.context_service import ContextService
from ..database.models import ProjectContextEnum


class PersistentContextTracker(ContextTracker):
    """
    Context tracker con persistencia de largo plazo en PostgreSQL.

    Extiende ContextTracker añadiendo:
    - Recuperación de snapshots históricos
    - Exponential decay weighting
    - Cross-session memory
    """

    def __init__(
        self,
        context_service: ContextService,
        window_size: int = 4,
        history_days: int = 7,
        decay_half_life_days: float = 3.0,
        snapshot_interval: int = 5,
    ):
        """
        Inicializa el persistent context tracker.

        Args:
            context_service: Servicio de base de datos para snapshots
            window_size: Tamaño de ventana deslizante (pares pregunta-respuesta)
            history_days: Días hacia atrás para buscar snapshots
            decay_half_life_days: Half-life para exponential decay (default: 3 días)
            snapshot_interval: Crear snapshot cada N mensajes
        """
        super().__init__()
        self.context_service = context_service
        self.window_size = window_size
        self.history_days = history_days
        self.decay_half_life_days = decay_half_life_days
        self.snapshot_interval = snapshot_interval

    def _calculate_decay_weight(self, days_ago: float) -> float:
        """
        Calcula peso con exponential decay.

        Formula: weight = exp(-days_ago / half_life)

        Args:
            days_ago: Días desde el snapshot

        Returns:
            Peso (0.0 - 1.0)
        """
        if days_ago < 0:
            return 1.0

        # Exponential decay: w(t) = exp(-t / τ)
        # τ = half_life / ln(2)
        tau = self.decay_half_life_days / math.log(2)
        weight = math.exp(-days_ago / tau)

        return weight

    async def get_active_context(
        self,
        conversation_history: List,
        current_query: str,
        user_id: int,
        conversation_id: int,
    ) -> Dict:
        """
        Obtiene contexto activo combinando reciente + histórico.

        Args:
            conversation_history: Lista de mensajes recientes (LangChain format)
            current_query: Query actual del usuario
            user_id: Database user ID
            conversation_id: Database conversation ID

        Returns:
            Dict con contexto combinado:
            - active_project: Proyecto DNI detectado
            - active_topic: Tema general
            - confidence: Confianza combinada (0-1)
            - enriched_query: Query enriquecida con contexto
            - source: 'recent' | 'historical' | 'combined'
        """
        # 1. Obtener contexto reciente (ventana deslizante)
        recent_context = self.extract_context_from_history(
            messages=conversation_history,
            window_size=self.window_size
        )

        # 2. Obtener snapshots históricos (últimos N días)
        historical_snapshots = await self.context_service.get_recent_snapshots(
            user_id=user_id,
            days=self.history_days,
            limit=10,
        )

        # 3. Si no hay historial, usar solo contexto reciente
        if not historical_snapshots:
            enriched_query = self.enrich_query_with_context(
                query=current_query,
                context_info=recent_context
            )

            return {
                'active_project': recent_context.get('active_project'),
                'active_topic': recent_context.get('active_topic'),
                'confidence': recent_context.get('confidence', 0.0),
                'enriched_query': enriched_query,
                'source': 'recent',
                'recent_context': recent_context,
                'historical_snapshots': None,
            }

        # 4. Merge contextos con exponential decay
        merged_project, merged_confidence = self._merge_contexts(
            recent_context=recent_context,
            historical_snapshots=historical_snapshots,
        )

        # 5. Crear contexto combinado
        combined_context = {
            'active_project': merged_project,
            'active_topic': recent_context.get('active_topic'),  # Topic siempre de contexto reciente
            'confidence': merged_confidence,
            'project_score': merged_confidence,
            'topic_score': recent_context.get('topic_score', 0.0),
            'summary': f"Proyecto: {merged_project}" if merged_project else None,
        }

        # 6. Enriquecer query con contexto combinado
        enriched_query = self.enrich_query_with_context(
            query=current_query,
            context_info=combined_context
        )

        return {
            'active_project': merged_project,
            'active_topic': combined_context['active_topic'],
            'confidence': merged_confidence,
            'enriched_query': enriched_query,
            'source': 'combined' if merged_confidence > recent_context.get('confidence', 0.0) else 'recent',
            'recent_context': recent_context,
            'historical_snapshots': len(historical_snapshots),
        }

    def _merge_contexts(
        self,
        recent_context: Dict,
        historical_snapshots: List,
    ) -> Tuple[Optional[str], float]:
        """
        Merge contexto reciente + snapshots históricos con exponential decay.

        Args:
            recent_context: Contexto de ventana deslizante reciente
            historical_snapshots: Lista de ContextSnapshot (DB models)

        Returns:
            Tuple (proyecto_combinado, confianza_combinada)
        """
        project_scores = {}

        # 1. Añadir proyecto del contexto reciente (peso máximo)
        if recent_context.get('active_project'):
            project_name = recent_context['active_project']
            recent_confidence = recent_context.get('project_score', 0.0)
            project_scores[project_name] = recent_confidence

        # 2. Añadir proyectos de snapshots históricos con decay
        now = datetime.now(timezone.utc)

        for snapshot in historical_snapshots:
            project_name = self._map_enum_to_name(snapshot.project_context)

            # Calcular días desde el snapshot
            days_ago = (now - snapshot.created_at).total_seconds() / 86400.0

            # Calcular peso con exponential decay
            decay_weight = self._calculate_decay_weight(days_ago)

            # Confianza del snapshot (stored in snapshot_data)
            snapshot_confidence = snapshot.snapshot_data.get('confidence', 0.5)

            # Score ponderado = confidence * decay_weight
            weighted_score = snapshot_confidence * decay_weight

            # Acumular scores para el mismo proyecto
            if project_name in project_scores:
                # Promedio ponderado (recent tiene más peso)
                project_scores[project_name] = max(
                    project_scores[project_name],
                    weighted_score
                )
            else:
                project_scores[project_name] = weighted_score

        # 3. Determinar proyecto con mayor score combinado
        if not project_scores:
            return None, 0.0

        # Encontrar proyecto con máximo score
        best_project = max(project_scores.items(), key=lambda x: x[1])
        project_name, confidence = best_project

        # Normalizar confianza (max = 1.0)
        normalized_confidence = min(confidence, 1.0)

        return project_name, normalized_confidence

    def _map_enum_to_name(self, project_enum: ProjectContextEnum) -> str:
        """
        Mapea ProjectContextEnum a nombre legible.

        Args:
            project_enum: Enum de la base de datos

        Returns:
            Nombre del proyecto (ej: "Desayunos Solidarios")
        """
        mapping = {
            ProjectContextEnum.DESAYUNOS: "Desayunos Solidarios",
            ProjectContextEnum.RESIS: "Charlas con Abuelitos (RESIS)",
            ProjectContextEnum.COLES: "Refuerzo Escolar (COLES)",
            ProjectContextEnum.DANA: "Rehabilitar Valencia (DANA)",
            ProjectContextEnum.KAYAK: "Recogida de Plásticos (Kayak)",
            ProjectContextEnum.GENERAL: "DNI (General)",
            ProjectContextEnum.UNKNOWN: None,
        }

        return mapping.get(project_enum)

    def _map_name_to_enum(self, project_name: str) -> ProjectContextEnum:
        """
        Mapea nombre legible a ProjectContextEnum.

        Args:
            project_name: Nombre del proyecto

        Returns:
            ProjectContextEnum
        """
        mapping = {
            "Desayunos Solidarios": ProjectContextEnum.DESAYUNOS,
            "Charlas con Abuelitos (RESIS)": ProjectContextEnum.RESIS,
            "Refuerzo Escolar (COLES)": ProjectContextEnum.COLES,
            "Rehabilitar Valencia (DANA)": ProjectContextEnum.DANA,
            "Recogida de Plásticos (Kayak)": ProjectContextEnum.KAYAK,
            "DNI (General)": ProjectContextEnum.GENERAL,
        }

        return mapping.get(project_name, ProjectContextEnum.UNKNOWN)

    async def create_snapshot_if_needed(
        self,
        conversation_id: int,
        user_id: int,
        context_info: Dict,
        message_count: int,
        last_user_query: str,
    ) -> bool:
        """
        Crea un snapshot si se cumple alguna condición:
        - Cada N mensajes (snapshot_interval)
        - Cambio de proyecto detectado
        - Alta confianza (> 0.7)

        Args:
            conversation_id: Database conversation ID
            user_id: Database user ID
            context_info: Información de contexto actual
            message_count: Número total de mensajes en conversación
            last_user_query: Última query del usuario

        Returns:
            True si se creó snapshot, False otherwise
        """
        # Verificar si es momento de crear snapshot
        should_create = await self.context_service.should_create_snapshot(
            conversation_id=conversation_id,
            current_message_count=message_count,
            snapshot_interval=self.snapshot_interval,
        )

        # Triggers adicionales
        high_confidence = context_info.get('confidence', 0.0) > 0.7
        has_project = context_info.get('active_project') is not None

        if should_create or (high_confidence and has_project):
            # Detectar proyecto enum
            project_name = context_info.get('active_project')
            project_enum = self._map_name_to_enum(project_name) if project_name else ProjectContextEnum.UNKNOWN

            # Detectar topics
            detected_topics = []
            if context_info.get('active_topic'):
                detected_topics.append(context_info['active_topic'])

            # Crear snapshot
            await self.context_service.create_snapshot(
                conversation_id=conversation_id,
                user_id=user_id,
                project_context=project_enum,
                detected_topics=detected_topics,
                message_count=message_count,
                last_user_query=last_user_query,
                snapshot_data={
                    'confidence': context_info.get('confidence', 0.0),
                    'project_score': context_info.get('project_score', 0.0),
                    'topic_score': context_info.get('topic_score', 0.0),
                    'summary': context_info.get('summary'),
                }
            )

            return True

        return False
