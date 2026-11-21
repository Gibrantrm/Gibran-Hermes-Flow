"""pre_tool_call (write_file|patch|skill_manage|tool_call): nadie escribe en hermes-flow; con
--solo-lectura (revisor) tampoco en un repo git (el worktree que revisa)."""
import re
import sys
from pathlib import Path

from comun import bloquear, ejecutar, llamadas

HERMES_FLOW = Path(__file__).resolve().parents[1]
# Lo único de hermes-flow que los agentes escriben: el canal de propuestas (escriba) y las
# métricas (/aprender y el cierre de cada tarea).
PERMITIDOS = {HERMES_FLOW / "propuestas-de-mejora.md", HERMES_FLOW / "metricas" / "correcciones.md",
              HERMES_FLOW / "metricas" / "tareas.md"}
ESCRITURA = {"write_file", "patch", "skill_manage"}
ARCHIVO_V4A = re.compile(r"^\*\*\* (?:Update|Add|Delete) File: (.+)$", re.M)
MENSAJE_FLOW = ("Gibran Flow: nadie escribe en hermes-flow (skills, souls, hooks). Si aprendiste algo "
                "para el flujo, anótalo en tu entrega como propuesta; si es del repo, va en su .hermes.md.")
MENSAJE_REVISOR = ("Gibran Flow: el revisor no modifica el código que revisa. Lee, compila y corre "
                   "tests; lo que haya que cambiar va como hallazgo (kanban_request_changes).")


def rutas(nombre, args):
    if nombre == "skill_manage":
        ops = args.get("operations") if isinstance(args.get("operations"), list) else [args]
        nombres = {o.get("name") or args.get("name") for o in ops if isinstance(o, dict)}
        return [p.parent for n in nombres if n for p in (HERMES_FLOW / "skills").rglob("SKILL.md")
                if p.parent.name == n]
    encontradas = [args.get("path")] + ARCHIVO_V4A.findall(args.get("patch") or "")
    return [Path(r.strip()) for r in encontradas if isinstance(r, str) and r.strip()]


def dentro(ruta, raiz):
    try:
        ruta.resolve().relative_to(raiz)
        return True
    except ValueError:
        return False


def en_repo_git(ruta):
    return any((d / ".git").exists() for d in [ruta.resolve(), *ruta.resolve().parents])


def evaluar(payload, solo_lectura=False):
    for nombre, args in llamadas(payload):
        if nombre not in ESCRITURA:
            continue
        for ruta in rutas(nombre, args):
            if dentro(ruta, HERMES_FLOW) and ruta.resolve() not in PERMITIDOS:
                return bloquear(MENSAJE_FLOW)
            if solo_lectura and nombre != "skill_manage" and en_repo_git(ruta):
                return bloquear(MENSAJE_REVISOR)
    return {}


if __name__ == "__main__":
    ejecutar(lambda p: evaluar(p, "--solo-lectura" in sys.argv))
