"""pre_tool_call (write_file|patch): bloquea credenciales literales en lo que se escribe."""
import re

from comun import bloquear, ejecutar

# No es un valor real si empieza como placeholder ($ < { * %) o como código (= ( ref().
NO_PLACEHOLDER = r"(?![$<{*%=(]|ref\()"
# ponytail: un secreto "real" tiene letra y dígito; passwords sin dígitos pasan.
SECRETO = r"(?=[^;\"'\s,<>]*\d)(?=[^;\"'\s,<>]*[A-Za-z])[^;\"'\s,<>]{6,}"
SECRETO_ENTRE_COMILLAS = r"(?=[^\"]*\d)(?=[^\"]*[A-Za-z])[^\"]{6,}"
CLAVE = r"(password|passwd|pwd|secret|key|token)"
PATRONES = [
    ("password en asignación o cadena de conexión",
     re.compile(r"(?i)(?:\b|_)(password|passwd|pwd)[\"']?\s*[=:]\s*[\"']?" + NO_PLACEHOLDER + SECRETO)),
    ("secreto en JSON",
     re.compile(r"(?i)\"[\w.-]*" + CLAVE + r"\"\s*:\s*\"" + NO_PLACEHOLDER + SECRETO_ENTRE_COMILLAS + "\"")),
    ("secreto en XML/config",
     re.compile(r"(?i)key=\"[^\"]*" + CLAVE + r"[^\"]*\"\s+value=\"" + NO_PLACEHOLDER + SECRETO_ENTRE_COMILLAS + "\"")),
    ("URL con usuario:password", re.compile(r"\b[a-z][a-z0-9+.-]*://[^:/\s@]+:(?![<$%{*])[^@\s/]+@")),
    ("token de GitHub", re.compile(r"\b(ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{20,})")),
    ("llave de API (sk-)", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
    ("llave de AWS", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("llave privada", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]


def texto_escrito(tool_input):
    """Solo lo que quedará en disco: content, new_string y líneas '+' de un patch V4A."""
    if not isinstance(tool_input, dict):
        return ""
    partes = [tool_input.get("content"), tool_input.get("new_string")]
    patch = tool_input.get("patch")
    if isinstance(patch, str):
        partes += [l for l in patch.splitlines() if l.startswith("+") and not l.startswith("+++")]
    return "\n".join(p for p in partes if isinstance(p, str))


def evaluar(payload):
    texto = texto_escrito(payload.get("tool_input"))
    for nombre, patron in PATRONES:
        if patron.search(texto):
            return bloquear(
                f"Gibran Flow: el contenido parece incluir un secreto ({nombre}). "
                "Usa un placeholder (${VARIABLE}, <valor>) o user-secrets; nunca el valor real.")
    return {}


if __name__ == "__main__":
    ejecutar(evaluar)
