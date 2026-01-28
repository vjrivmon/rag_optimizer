"""
Tests for Sanitizer - XSS protection and input cleaning.

Covers:
- XSS detection (basic and advanced payloads)
- Strict sanitization (removes all HTML)
- Relaxed sanitization (allows safe tags)
- Edge cases (empty, None, very long)
- Verify legitimate DNI queries are not corrupted
"""

import pytest
from vicente_rag.security.sanitizer import (
    Sanitizer,
    SanitizeResult,
    sanitize_input,
    sanitize_strict,
    detect_xss,
)
from tests.fixtures.sample_data import XSS_PAYLOADS, LEGITIMATE_QUERIES


# ---------------------------------------------------------------------------
# XSS detection
# ---------------------------------------------------------------------------

class TestXSSDetection:

    def test_script_tag(self, sanitizer):
        is_attack, patterns = sanitizer.detect_xss('<script>alert("XSS")</script>')
        assert is_attack is True
        assert len(patterns) > 0

    def test_img_onerror(self, sanitizer):
        is_attack, _ = sanitizer.detect_xss('<img src=x onerror=alert(1)>')
        assert is_attack is True

    def test_svg_onload(self, sanitizer):
        is_attack, _ = sanitizer.detect_xss('<svg onload=alert("xss")>')
        assert is_attack is True

    def test_javascript_protocol(self, sanitizer):
        is_attack, _ = sanitizer.detect_xss('javascript:alert(document.cookie)')
        assert is_attack is True

    def test_onclick_event(self, sanitizer):
        is_attack, _ = sanitizer.detect_xss('<a onclick="alert(1)">click</a>')
        assert is_attack is True

    def test_iframe_injection(self, sanitizer):
        is_attack, _ = sanitizer.detect_xss('<iframe src="http://evil.com"></iframe>')
        assert is_attack is True

    def test_object_tag(self, sanitizer):
        is_attack, _ = sanitizer.detect_xss('<object data="evil.swf"></object>')
        assert is_attack is True

    def test_vbscript(self, sanitizer):
        is_attack, _ = sanitizer.detect_xss('vbscript:MsgBox("XSS")')
        assert is_attack is True

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_all_xss_payloads_detected(self, sanitizer, payload):
        is_attack, _ = sanitizer.detect_xss(payload)
        assert is_attack is True, f"XSS payload not detected: {payload}"

    def test_clean_text_not_flagged(self, sanitizer):
        is_attack, _ = sanitizer.detect_xss("¿Cuándo son los desayunos solidarios?")
        assert is_attack is False

    @pytest.mark.parametrize("query", LEGITIMATE_QUERIES)
    def test_legitimate_queries_not_flagged(self, sanitizer, query):
        is_attack, patterns = sanitizer.detect_xss(query)
        assert is_attack is False, f"Legitimate query flagged: '{query}' matched: {patterns}"


# ---------------------------------------------------------------------------
# Strict sanitization
# ---------------------------------------------------------------------------

class TestStrictSanitization:

    def test_removes_script_tags(self, sanitizer):
        result = sanitizer.sanitize_strict('<script>alert("XSS")</script>Hola')
        assert "<script>" not in result
        assert "</script>" not in result
        # strict mode removes tags but may keep text content
        assert "Hola" in result

    def test_removes_all_html_tags(self, sanitizer):
        result = sanitizer.sanitize_strict("<b>bold</b> and <i>italic</i>")
        assert "<b>" not in result
        assert "<i>" not in result
        assert "bold" in result
        assert "italic" in result

    def test_removes_angle_brackets(self, sanitizer):
        result = sanitizer.sanitize_strict("test < value > other")
        assert "<" not in result
        assert ">" not in result

    def test_removes_control_characters(self, sanitizer):
        result = sanitizer.sanitize_strict("hello\x00world\x01test")
        assert "\x00" not in result
        assert "\x01" not in result
        assert "hello" in result

    def test_normalizes_whitespace(self, sanitizer):
        result = sanitizer.sanitize_strict("hello    world\n\nmany   spaces")
        assert "  " not in result  # no double spaces

    def test_truncates_to_max_length(self):
        s = Sanitizer(max_length=10)
        result = s.sanitize_strict("a" * 100)
        assert len(result) == 10

    def test_empty_string(self, sanitizer):
        assert sanitizer.sanitize_strict("") == ""

    def test_none_input(self, sanitizer):
        assert sanitizer.sanitize_strict(None) == ""


# ---------------------------------------------------------------------------
# Relaxed sanitization
# ---------------------------------------------------------------------------

class TestRelaxedSanitization:

    def test_keeps_bold_tags(self, sanitizer):
        result = sanitizer.sanitize_relaxed("<b>important</b>")
        assert "<b>" in result
        assert "</b>" in result

    def test_keeps_italic_tags(self, sanitizer):
        result = sanitizer.sanitize_relaxed("<i>emphasis</i>")
        assert "<i>" in result

    def test_keeps_code_tags(self, sanitizer):
        result = sanitizer.sanitize_relaxed("<code>print()</code>")
        assert "<code>" in result

    def test_removes_script_tags(self, sanitizer):
        result = sanitizer.sanitize_relaxed('<script>alert(1)</script>')
        assert "<script>" not in result

    def test_removes_iframe(self, sanitizer):
        result = sanitizer.sanitize_relaxed('<iframe src="evil"></iframe>')
        assert "<iframe" not in result


# ---------------------------------------------------------------------------
# sanitize_and_detect combined
# ---------------------------------------------------------------------------

class TestSanitizeAndDetect:

    def test_xss_detected_and_cleaned(self, sanitizer):
        result = sanitizer.sanitize_and_detect('<script>alert(1)</script>Hello')
        assert isinstance(result, SanitizeResult)
        assert result.was_attack is True
        assert "<script>" not in result.clean
        assert "Hello" in result.clean
        assert len(result.removed_patterns) > 0

    def test_clean_input_passes(self, sanitizer):
        result = sanitizer.sanitize_and_detect("¿Qué es DNI?")
        assert result.was_attack is False
        assert result.clean == "¿Qué es DNI?"
        assert result.removed_patterns == []


# ---------------------------------------------------------------------------
# Normalize input
# ---------------------------------------------------------------------------

class TestNormalizeInput:

    def test_trims_whitespace(self, sanitizer):
        assert sanitizer.normalize_input("  hello  ") == "hello"

    def test_normalizes_newlines(self, sanitizer):
        result = sanitizer.normalize_input("hello\n\nworld")
        assert result == "hello world"

    def test_empty_string(self, sanitizer):
        assert sanitizer.normalize_input("") == ""

    def test_preserves_html_in_normalize(self, sanitizer):
        """normalize_input does NOT strip HTML (by design)."""
        result = sanitizer.normalize_input("<b>bold</b>")
        assert "<b>" in result


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------

class TestConvenienceFunctions:

    def test_sanitize_input_function(self):
        result = sanitize_input('<script>alert(1)</script>Hello')
        assert "<script>" not in result
        assert "Hello" in result

    def test_sanitize_strict_function(self):
        result = sanitize_strict('<b>bold</b>')
        assert "<b>" not in result
        assert "bold" in result

    def test_detect_xss_function(self):
        is_attack, _ = detect_xss('<script>alert(1)</script>')
        assert is_attack is True
