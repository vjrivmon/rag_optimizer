"""
Risk Scorer Module
Scoring de riesgo para mensajes de usuario

Traducido de: @vicente-rag/core/security/risk-scorer.ts
"""

from typing import List, Dict, Optional
from dataclasses import dataclass

# =============================================================================
# PALABRAS SOSPECHOSAS POR CATEGORÍA
# =============================================================================

DEFAULT_SUSPICIOUS_WORDS: Dict[str, List[str]] = {
    "system_manipulation": [
        "system", "prompt", "instruction", "override", "bypass",
        "sistema", "instrucción", "ignorar", "saltar",
        "système", "instruction", "ignorer",
    ],
    "code_injection": [
        "eval", "exec", "script", "import", "require", "__",
        "subprocess", "os.system", "shell",
    ],
    "data_extraction": [
        "password", "secret", "api_key", "token", "credential",
        "contraseña", "secreto", "clave",
        "mot de passe", "clé",
    ],
    "roleplay_abuse": [
        "pretend", "roleplay", "act as", "you are now",
        "finge", "actúa como", "eres ahora",
        "fais semblant", "tu es maintenant",
    ],
    "jailbreak": [
        "jailbreak", "DAN", "developer mode", "unrestricted",
        "modo desarrollador", "sin restricciones",
    ],
}


@dataclass
class RiskScoreResult:
    """Resultado del análisis de riesgo"""
    score: float  # 0.0 - 1.0
    level: str    # "low", "medium", "high", "critical"
    factors: List[str]
    recommendation: str


class RiskScorer:
    """
    Calcula un score de riesgo para mensajes de usuario.
    Combina múltiples señales para una evaluación holística.
    """

    def __init__(
        self,
        suspicious_words: Optional[Dict[str, List[str]]] = None,
        thresholds: Optional[Dict[str, float]] = None,
        debug: bool = False
    ):
        self.suspicious_words = suspicious_words or DEFAULT_SUSPICIOUS_WORDS
        self.thresholds = thresholds or {
            "low": 0.25,
            "medium": 0.50,
            "high": 0.75,
        }
        self.debug = debug

    def _log(self, message: str):
        if self.debug:
            print(f"[RiskScorer] {message}")

    def _count_suspicious_words(self, text: str) -> Dict[str, int]:
        """Cuenta palabras sospechosas por categoría"""
        text_lower = text.lower()
        counts = {}

        for category, words in self.suspicious_words.items():
            count = sum(1 for word in words if word.lower() in text_lower)
            if count > 0:
                counts[category] = count

        return counts

    def _check_structural_patterns(self, text: str) -> List[str]:
        """Detecta patrones estructurales sospechosos"""
        patterns_found = []

        # Longitud anormal
        if len(text) > 2000:
            patterns_found.append("very_long_message")

        # Muchos saltos de línea (posible injection)
        if text.count("\n") > 10:
            patterns_found.append("many_newlines")

        # Delimitadores de sistema
        system_delimiters = ["[SYSTEM]", "[INST]", "<<SYS>>", "<|im_start|>"]
        for delim in system_delimiters:
            if delim.lower() in text.lower():
                patterns_found.append(f"system_delimiter:{delim}")

        # Muchos caracteres especiales
        special_chars = sum(1 for c in text if c in "{}[]<>|\\")
        if special_chars > len(text) * 0.1:  # > 10% special chars
            patterns_found.append("high_special_chars")

        # Encoded content (base64, hex, etc.)
        if "==" in text and len(text) > 50:  # Posible base64
            patterns_found.append("possible_encoding")

        return patterns_found

    def _check_behavioral_signals(self, text: str) -> List[str]:
        """Detecta señales de comportamiento sospechoso"""
        signals = []
        text_lower = text.lower()

        # Urgencia artificial
        urgency_words = ["urgent", "immediately", "now", "urgente", "ahora", "inmediato"]
        if any(word in text_lower for word in urgency_words):
            signals.append("artificial_urgency")

        # Referencias a admin/root
        if any(word in text_lower for word in ["admin", "root", "sudo", "administrator"]):
            signals.append("admin_reference")

        # Petición de código
        code_requests = ["give me code", "write code", "ejecuta", "run this"]
        if any(phrase in text_lower for phrase in code_requests):
            signals.append("code_request")

        # Petición de ignorar algo
        if any(word in text_lower for word in ["ignore", "skip", "bypass", "ignora", "salta"]):
            signals.append("ignore_request")

        return signals

    def calculate(self, text: str) -> RiskScoreResult:
        """
        Calcula el score de riesgo para un texto.

        Returns:
            RiskScoreResult con score (0-1), nivel, factores y recomendación
        """
        if not text or not isinstance(text, str):
            return RiskScoreResult(
                score=0.0,
                level="low",
                factors=[],
                recommendation="Valid input"
            )

        factors = []
        score = 0.0

        # 1. Palabras sospechosas (peso: 0.4)
        word_counts = self._count_suspicious_words(text)
        if word_counts:
            word_score = min(sum(word_counts.values()) * 0.1, 0.4)
            score += word_score
            for category, count in word_counts.items():
                factors.append(f"suspicious_words:{category}({count})")

        # 2. Patrones estructurales (peso: 0.3)
        structural = self._check_structural_patterns(text)
        if structural:
            struct_score = min(len(structural) * 0.1, 0.3)
            score += struct_score
            factors.extend(structural)

        # 3. Señales de comportamiento (peso: 0.3)
        behavioral = self._check_behavioral_signals(text)
        if behavioral:
            behav_score = min(len(behavioral) * 0.1, 0.3)
            score += behav_score
            factors.extend(behavioral)

        # Normalizar score
        score = min(score, 1.0)

        # Determinar nivel
        if score >= self.thresholds["high"]:
            level = "critical"
            recommendation = "Block this request and log for review"
        elif score >= self.thresholds["medium"]:
            level = "high"
            recommendation = "Apply additional validation before processing"
        elif score >= self.thresholds["low"]:
            level = "medium"
            recommendation = "Process with caution, monitor response"
        else:
            level = "low"
            recommendation = "Safe to process normally"

        self._log(f"Score: {score:.2f}, Level: {level}, Factors: {len(factors)}")

        return RiskScoreResult(
            score=score,
            level=level,
            factors=factors,
            recommendation=recommendation
        )


# =============================================================================
# FUNCIÓN DE CONVENIENCIA
# =============================================================================

def calculate_risk_score(text: str, debug: bool = False) -> RiskScoreResult:
    """
    Función de conveniencia para calcular risk score.

    Uso:
        result = calculate_risk_score(user_message)
        if result.level in ["high", "critical"]:
            print(f"High risk detected: {result.factors}")
    """
    scorer = RiskScorer(debug=debug)
    return scorer.calculate(text)
