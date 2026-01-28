# Security Policy - Chatbot DNI

## Security SDK

The project includes a dedicated security SDK at `vicente_rag/security/` with
three components:

| Module                  | Class               | Purpose                                     |
| ----------------------- | ------------------- | ------------------------------------------- |
| `injection_detector.py` | `InjectionDetector` | Detects prompt injection (regex + semantic) |
| `sanitizer.py`          | `Sanitizer`         | XSS protection and input cleaning           |
| `risk_scorer.py`        | `RiskScorer`        | Multi-factor risk scoring                   |

## Entry Points Protected

### Web (FastAPI) - `interface/chatbot_dni/backend/app.py`

1. **Input sanitisation** - `Sanitizer.sanitize_strict()` strips HTML tags,
   control characters, and truncates to 5000 characters.
2. **Injection detection** - `InjectionDetector.detect()` checks for prompt
   injection patterns in EN/ES/FR. Blocked requests receive a safe fallback
   response and the WebSocket is closed.
3. **Risk scoring** - `RiskScorer.calculate()` flags high/critical inputs in
   server logs for monitoring.
4. **CORS** - Origins restricted via `CORS_ORIGINS` environment variable
   (default: `http://localhost:8000,http://127.0.0.1:8000`). **Never use `*` in
   production.**
5. **Security headers** - `SecurityHeadersMiddleware` adds:
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
   - `X-XSS-Protection: 1; mode=block`
   - `Referrer-Policy: strict-origin-when-cross-origin`

### Telegram - `src/telegram/handlers/messages.py`

1. **Input sanitisation** - `Sanitizer.sanitize_strict()` applied to raw message
   text.
2. **Injection detection** - `InjectionDetector.detect()` blocks malicious
   messages with a safe response.
3. **HTML output safety** - `markdown_to_html()` calls `html.escape()` before
   any markdown-to-HTML conversion. URLs are validated to only allow `http://`
   and `https://` schemes.

### Frontend - `interface/chatbot_dni/frontend/static/js/chat.js`

1. **`escapeHTML()`** - Escapes all HTML entities using a DOM text node.
2. **`sanitizeHTML()`** - Parses HTML with DOMParser and only keeps allowed tags
   (`<strong>`, `<em>`, `<b>`, `<i>`, `<br>`, `<code>`, `<a>` with safe href).
3. **`markdownToSafeHTML()`** - Combines escape + markdown conversion + sanitise
   for defence-in-depth.
4. All `innerHTML` assignments use `markdownToSafeHTML()` or set static content
   via `textContent`.

## Types of Attacks Mitigated

### Prompt Injection

- Regex patterns cover English, Spanish, and French injection attempts.
- Patterns include: "ignore previous instructions", "system prompt",
  "jailbreak", role impersonation, delimiter attacks.
- Blocked at both Web and Telegram entry points before RAG processing.

### XSS (Cross-Site Scripting)

- Server-side: strict sanitisation removes all HTML tags from user input.
- Client-side: `sanitizeHTML()` allowlist approach ensures only safe tags
  render.
- Telegram: `html.escape()` applied before markdown conversion.

### HTML Injection

- `markdown_to_html()` escapes HTML entities first, then converts markdown
  patterns.
- URLs validated to prevent `javascript:` and `data:` protocol injection.

## SSL Configuration

The Ollama server at `ollama.gti-ia.upv.es` uses a self-signed certificate.
`verify=False` is set in `src/core/model_wrapper.py` for this internal
connection only. This is documented and acceptable because:

- The server is on the UPV internal network.
- No sensitive user data is sent to the LLM (only sanitised queries).
- All external-facing connections use HTTPS with proper certificates.

## GDPR Compliance

- `/delete_my_data` Telegram command removes all user data (user record,
  conversations, messages, context snapshots).
- No personal data is logged in production (only user IDs for debugging).
- Consent is implicit on first interaction (documented in `/start` message).

## Running Security Tests

```bash
# All security tests
pytest tests/security/ -v

# With coverage
pytest tests/security/ -v --cov=vicente_rag/security --cov-report=term-missing

# Integration tests only
pytest tests/security/test_security_integration.py -v
```

## Reporting Vulnerabilities

If you discover a security vulnerability, please report it privately to the
project maintainer rather than opening a public issue.
