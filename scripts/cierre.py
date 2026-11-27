"""Cierre de una tarea (paso 12 de modo-feature / §4 de modo-bug): lo mecánico del Control final.

Uso (el orquestador, antes de presentar el Control final):
  python cierre.py --worktree <ruta> --rama <rama> --modo feature --riesgo ALTO --e2e "arnés"

Cuenta tarjetas y rondas del Kanban (no de memoria), alerta si alguna tarjeta quedó sin corrida
del revisor, calcula el costo desde /costos-inicio solo si la marca es de esta tarea, escribe la
fila en metricas/tareas.md, avisa si queda una app corriendo e imprime el comando de integrar.py
con las rutas reales. Su salida se pega tal cual en la sección "Cierre".
"""
import argparse
import datetime
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "hooks"))
sys.path.insert(0, str(RAIZ / "scripts"))
from app_local import apps_de, vivo  # noqa: E402
from registro_costos import destino  # noqa: E402
from resumen_costos import PRECIOS, resumir  # noqa: E402

MARCA_MAX_HORAS = 12  # una marca más vieja que esto antes de la primera tarjeta es de otra tarea


def normal(ruta):
    return os.path.normcase(os.path.normpath(str(ruta)))


def kanban(db, worktree):
    """(tarjetas, revisiones, sin_revisor, primera_creacion, id_inicial) del worktree."""
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    tareas = [(i, s, t) for i, s, w, t in c.execute("select id, status, workspace_path, created_at from tasks")
              if w and normal(w) == normal(worktree)]
    revisiones, sin_revisor = 0, []
    for tid, estado, _ in tareas:
        runs = [o for p, o in c.execute("select profile, outcome from task_runs where task_id = ?", (tid,))
                if p == "revisor" and o in ("completed", "changes_requested")]
        revisiones += len(runs)
        if estado in ("done", "archived") and "completed" not in runs:
            sin_revisor.append(tid)
    c.close()
    inicial = min(tareas, key=lambda t: (t[2], t[0])) if tareas else None
    return len(tareas), revisiones, sin_revisor, inicial[2] if inicial else None, inicial[0] if inicial else None


def costo(primera):
    """(texto para la fila, detalle). Solo cuenta si la marca de /costos-inicio es de esta tarea."""
    ruta = destino()
    marca_f = ruta.with_name("costos.inicio")
    if not marca_f.exists():
        return "sin medir", "no hay marca de /costos-inicio"
    marca = marca_f.read_text(encoding="utf-8").strip()
    if primera is not None:
        inicio = datetime.datetime.fromtimestamp(primera)
        m = datetime.datetime.fromisoformat(marca)
        if m.tzinfo is not None:  # marca con zona (p. ej. date -Iseconds): a hora local naive
            m = m.astimezone().replace(tzinfo=None)
        if m > inicio or inicio - m > datetime.timedelta(hours=MARCA_MAX_HORAS):
            return "sin medir", f"la marca ({marca}) no es de esta tarea"
    lineas = []
    for t in ruta.read_text(encoding="utf-8").splitlines() if ruta.exists() else []:
        try:
            lineas.append(json.loads(t))
        except ValueError:
            pass
    precios = json.loads(PRECIOS.read_text(encoding="utf-8"))
    filas = resumir(lineas, marca, precios)
    usd = sum(f[8] or 0 for f in filas)
    aic = sum((f[8] or 0) * 100 for f in filas if f[2] == "copilot")
    mxn = usd * precios["tipo_cambio_mxn"]
    detalle = f"desde {marca}: ${mxn:,.2f} MXN equivalente" + (f" ({aic:,.0f} AIC de Copilot)" if aic else "")
    return f"{mxn:,.2f}", detalle


def repo_principal(worktree):
    r = subprocess.run(["git", "-C", str(worktree), "rev-parse", "--path-format=absolute", "--git-common-dir"],
                       capture_output=True, text=True)
    return Path(r.stdout.strip()).parent if r.returncode == 0 and r.stdout.strip() else None


def registrar_metrica(metricas, id_inicial, fila):
    """Actualiza por tarjeta inicial, conservando fecha y defectos de la primera fila."""
    marca = f"<!-- cierre:{hashlib.sha256(id_inicial.encode('utf-8')).hexdigest()} -->"
    previas = metricas.read_text(encoding="utf-8") if metricas.exists() else ""
    lineas = previas.splitlines(keepends=True)
    coincidencias = [i for i, linea in enumerate(lineas) if linea.rstrip().endswith(marca)]
    if len(coincidencias) > 1:
        raise ValueError("hay varias filas con la misma identidad de cierre; revisa las métricas")
    if coincidencias:
        i = coincidencias[0]
        anterior = lineas[i].rstrip().removesuffix(marca).rstrip().split("|")
        nueva = fila.split("|")
        if len(anterior) != len(nueva) or anterior[0].strip() or anterior[-1].strip():
            raise ValueError("la fila de esta tarea tiene un formato inválido; revisa las métricas")
        nueva[1], nueva[-2] = anterior[1], anterior[-2]
        lineas[i] = "|".join(nueva) + " " + marca + "\n"
        contenido = "".join(lineas)
        accion = "actualizada"
    else:
        separador = "\n" if previas and not previas.endswith("\n") else ""
        contenido = previas + separador + fila + " " + marca + "\n"
        accion = "agregada"
    if contenido != previas:
        metricas.write_text(contenido, encoding="utf-8")
    return accion


def main(argv, kanban_db=None, metricas=None):
    p = argparse.ArgumentParser(prog="cierre")
    p.add_argument("--worktree", required=True)
    p.add_argument("--rama", required=True)
    p.add_argument("--modo", required=True, choices=["feature", "bug", "nuevo"])
    p.add_argument("--riesgo", required=True, choices=["BAJO", "ALTO"])
    p.add_argument("--e2e", default="no aplica")
    a = p.parse_args(argv)
    db = kanban_db or Path(os.environ.get("LOCALAPPDATA", ".")) / "hermes" / "kanban.db"
    metricas = Path(metricas or RAIZ / "metricas" / "tareas.md")
    repo = repo_principal(a.worktree)
    nombre = repo.name if repo else Path(a.worktree).name

    tarjetas, revisiones, sin_revisor, primera, id_inicial = kanban(db, a.worktree)
    if id_inicial is None:
        print("## Cierre")
        print("- ALERTA: no hay tarjetas del worktree; no se puede identificar la tarea ni registrar su métrica.")
        return 1
    texto_costo, detalle_costo = costo(primera)
    fila = (f"| {datetime.date.today().isoformat()} | {nombre} | {a.modo} | {a.riesgo} | {tarjetas} | "
            f"{revisiones} | {a.e2e} | {texto_costo} | pendiente |")
    try:
        accion_metrica = registrar_metrica(metricas, id_inicial, fila)
    except ValueError as e:
        print("## Cierre")
        print(f"- ALERTA: {e}. No se modificaron las métricas.")
        return 1

    print("## Cierre")
    print(f"- Tarjetas: {tarjetas} · revisiones del revisor: {revisiones}")
    if sin_revisor:
        print(f"- ALERTA: tarjetas terminadas sin aprobación del revisor: {', '.join(sin_revisor)}")
    print(f"- Costo: {detalle_costo}")
    apps = [x for x in apps_de(a.worktree) if vivo(x["pid"])] if Path(a.worktree).is_dir() else []
    print(f"- ALERTA: siguen corriendo apps (PID {[x['pid'] for x in apps]}): corre app_local.py detener"
          if apps else "- Apps de la tarea: ninguna corriendo")
    print(f"- Métrica: fila {accion_metrica} en {metricas}")
    print("\nAl aprobar el Control final, el orquestador integra (cambios staged en la rama de origen, sin commit;")
    print("borra el worktree y la rama). Después el usuario revisa `git diff --cached` y hace el commit:")
    print(f'    python "{RAIZ / "scripts" / "integrar.py"}" --worktree "{a.worktree}" --rama {a.rama}')
    return 1 if sin_revisor or apps else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
