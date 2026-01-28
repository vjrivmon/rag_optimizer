"""
Security Module
Detección de injection, sanitización y scoring de riesgo
"""

from .injection_detector import (
    InjectionDetector,
    detect_injection,
    DEFAULT_INJECTION_PATTERNS,
    DEFAULT_MALICIOUS_PHRASES,
)

from .sanitizer import (
    Sanitizer,
    sanitize_input,
    sanitize_strict,
    detect_xss,
    DEFAULT_XSS_PATTERNS,
)

from .risk_scorer import (
    RiskScorer,
    calculate_risk_score,
    DEFAULT_SUSPICIOUS_WORDS,
)

__all__ = [
    # Injection
    "InjectionDetector",
    "detect_injection",
    "DEFAULT_INJECTION_PATTERNS",
    "DEFAULT_MALICIOUS_PHRASES",
    # Sanitizer
    "Sanitizer",
    "sanitize_input",
    "sanitize_strict",
    "detect_xss",
    "DEFAULT_XSS_PATTERNS",
    # Risk
    "RiskScorer",
    "calculate_risk_score",
    "DEFAULT_SUSPICIOUS_WORDS",
]
