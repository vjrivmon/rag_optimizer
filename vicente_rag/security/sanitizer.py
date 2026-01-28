"""
Sanitizer Module
Protección XSS y limpieza de input

Traducido de: @vicente-rag/core/security/sanitizer.ts
"""

import re
import html
from typing import List, Tuple, Optional
from dataclasses import dataclass

# =============================================================================
# PATRONES XSS
# =============================================================================

DEFAULT_XSS_PATTERNS: List[re.Pattern] = [
    # Script tags
    re.compile(r"<script[\s\S]*?>[\s\S]*?</script>", re.IGNORECASE),
    re.compile(r"<script", re.IGNORECASE),

    # Protocol handlers
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"vbscript\s*:", re.IGNORECASE),
    re.compile(r"data\s*:", re.IGNORECASE),

    # Event handlers (onclick, onerror, onload, etc.)
    re.compile(r"\bon\w+\s*=", re.IGNORECASE),

    # CSS expressions (IE legacy)
    re.compile(r"expression\s*\(", re.IGNORECASE),

    # Dangerous embed elements
    re.compile(r"<iframe", re.IGNORECASE),
    re.compile(r"<object", re.IGNORECASE),
    re.compile(r"<embed", re.IGNORECASE),
    re.compile(r"<frame", re.IGNORECASE),
    re.compile(r"<frameset", re.IGNORECASE),

    # SVG with event handlers
    re.compile(r"<svg[\s\S]*?\bon\w+", re.IGNORECASE),

    # HTML entity encoding (bypass attempts)
    re.compile(r"&#x?[0-9a-f]{2,6};", re.IGNORECASE),

    # URL encoding of < and >
    re.compile(r"%3C", re.IGNORECASE),
    re.compile(r"%3E", re.IGNORECASE),

    # Base64 data URIs
    re.compile(r"base64\s*,", re.IGNORECASE),
]


@dataclass
class SanitizeResult:
    """Resultado de sanitización"""
    clean: str
    was_attack: bool
    removed_patterns: List[str]


class Sanitizer:
    """
    Sanitizador de input con protección XSS.
    """

    def __init__(
        self,
        max_length: int = 5000,
        custom_patterns: Optional[List[re.Pattern]] = None,
        debug: bool = False
    ):
        self.max_length = max_length
        self.patterns = DEFAULT_XSS_PATTERNS + (custom_patterns or [])
        self.debug = debug

    def _log(self, message: str):
        if self.debug:
            print(f"[Sanitizer] {message}")

    def detect_xss(self, text: str) -> Tuple[bool, List[str]]:
        """Detecta intentos de XSS en el texto"""
        if not text or not isinstance(text, str):
            return False, []

        matched = []
        for pattern in self.patterns:
            if pattern.search(text):
                matched.append(pattern.pattern)

        return len(matched) > 0, matched

    def sanitize_strict(self, text: str) -> str:
        """
        Sanitización estricta: elimina TODO HTML.
        Ideal para chat messages y user input.
        """
        if not text or not isinstance(text, str):
            return ""

        # Eliminar tags HTML
        cleaned = re.sub(r"<[^>]*>", "", text)

        # Decodificar entidades HTML comunes
        cleaned = html.unescape(cleaned)

        # Eliminar caracteres de control
        cleaned = re.sub(r"[\x00-\x1F\x7F]", "", cleaned)

        # Normalizar whitespace
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # Eliminar brackets HTML-like restantes
        cleaned = re.sub(r"[<>]", "", cleaned)

        # Truncar a max length
        cleaned = cleaned[:self.max_length]

        return cleaned

    def sanitize_relaxed(self, text: str) -> str:
        """
        Sanitización relajada: permite algunos tags de formato básico.
        Ideal para contenido que puede tener formato simple.
        """
        if not text or not isinstance(text, str):
            return ""

        # Tags permitidos (solo formato básico)
        allowed_tags = {"b", "i", "em", "strong", "p", "br", "ul", "ol", "li", "code", "pre"}

        # Eliminar tags no permitidos pero mantener contenido
        def replace_tag(match):
            tag = match.group(1).lower().split()[0]  # Obtener solo el nombre del tag
            if tag in allowed_tags or tag.startswith("/") and tag[1:] in allowed_tags:
                return match.group(0)  # Mantener tag permitido
            return ""  # Eliminar tag no permitido

        cleaned = re.sub(r"<(/?\w+)[^>]*>", replace_tag, text)

        # Eliminar caracteres de control
        cleaned = re.sub(r"[\x00-\x1F\x7F]", "", cleaned)

        # Truncar
        cleaned = cleaned[:self.max_length]

        return cleaned

    def sanitize_and_detect(self, text: str) -> SanitizeResult:
        """
        Combina sanitización con detección de ataques.
        Útil para logging de intentos maliciosos.
        """
        was_attack, patterns = self.detect_xss(text)
        clean = self.sanitize_strict(text)

        if was_attack:
            self._log(f"XSS attempt detected: {patterns}")

        return SanitizeResult(
            clean=clean,
            was_attack=was_attack,
            removed_patterns=patterns
        )

    def normalize_input(self, text: str) -> str:
        """
        Normalización básica de input (sin eliminar HTML).
        Útil para queries de búsqueda.
        """
        if not text or not isinstance(text, str):
            return ""

        # Normalizar whitespace
        cleaned = re.sub(r"\s+", " ", text).strip()

        # Eliminar caracteres de control
        cleaned = re.sub(r"[\x00-\x1F\x7F]", "", cleaned)

        # Truncar
        cleaned = cleaned[:self.max_length]

        return cleaned


# =============================================================================
# FUNCIONES DE CONVENIENCIA
# =============================================================================

_default_sanitizer = Sanitizer()


def sanitize_input(text: str, max_length: int = 5000) -> str:
    """
    Función de conveniencia para sanitización estricta.

    Uso:
        clean = sanitize_input(user_message)
    """
    sanitizer = Sanitizer(max_length=max_length)
    return sanitizer.sanitize_strict(text)


def sanitize_strict(text: str) -> str:
    """Alias para sanitize_input"""
    return _default_sanitizer.sanitize_strict(text)


def detect_xss(text: str) -> Tuple[bool, List[str]]:
    """
    Función de conveniencia para detectar XSS.

    Uso:
        is_attack, patterns = detect_xss(user_input)
    """
    return _default_sanitizer.detect_xss(text)
