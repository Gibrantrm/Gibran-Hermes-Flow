"""pre_tool_call (terminal|execute_code), solo en workers: dotnet que compila pasa por dotnet_seguro.

Los workers de una feature comparten worktree; dos builds simultáneos chocan en bin/obj
y QA rechazaría trabajo correcto. dotnet_seguro serializa solo la compilación.
"""
import re
import sys
from pathlib import Path

from comun import bloquear, ejecutar, textos

# "dotnet_seguro.py build" no coincide: tras "dotnet" viene "_", que no es límite de palabra.
COMPILA = re.compile(r"(?i)\bdotnet(?:\.exe)?\s+(build|test|run|publish)\b")
SCRIPT = (Path(__file__).resolve().parents[1] / "scripts" / "dotnet_seguro.py").as_posix()
PY = Path(sys.executable).as_posix()


def evaluar(payload):
    entrada = payload.get("tool_input")
    texto = textos(entrada)
    plano = re.sub(r"[\"'\[\],]", " ", texto)
    m = COMPILA.search(texto) or COMPILA.search(plano)
    if not m:
        return {}
    comando = entrada.get("command")
    if payload.get("tool_name") == "terminal" and isinstance(comando, str) and COMPILA.search(comando):
        # Reescribir en vez de bloquear: el worker no gasta una llamada en buscar la ruta.
        return {"action": "modify", "args": {"command": COMPILA.sub(
            lambda c: f'"{PY}" "{SCRIPT}" {c.group(1).lower()}', comando)}}
    return bloquear(
        f"Gibran Flow: en el worktree compartido compila con el candado. Usa: "
        f"\"{PY}\" \"{SCRIPT}\" {m.group(1).lower()} <mismos argumentos>")


if __name__ == "__main__":
    ejecutar(evaluar)
