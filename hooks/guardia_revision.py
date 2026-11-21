"""pre_tool_call (todas las herramientas), solo en el revisor: no aprobar sobre un worktree distinto.

En la primera llamada de la sesión guarda una foto de lo que recibe (archivos con cambios y el
hash de su contenido). Antes de kanban_complete o kanban_request_changes la compara: si el
worktree cambió (lo modificó el revisor, o su build regeneró archivos versionados), bloquea y
pide reportarlo con kanban_block. No impide escribir; impide aprobar en silencio.

Con tarjetas en paralelo en el mismo worktree (un implementador corriendo durante la revisión),
los archivos que no estaban en la foto se atribuyen a esa tarjeta y no bloquean; los que sí
estaban (lo que se revisa) bloquean siempre.
"""
import hashlib
import json
import os
import sqlite3
import subprocess
import time
from pathlib import Path

from comun import bloquear, ejecutar, llamadas

CIERRES = {"kanban_complete", "kanban_request_changes"}


def carpeta_fotos():
    base = os.environ.get("GIBRAN_FOTOS") or Path(os.environ.get("LOCALAPPDATA", ".")) / "hermes" / "gibran-revision"
    return Path(base)


def foto(cwd):
    """{ruta: hash} de los archivos con cambios respecto a HEAD (incluye nuevos; ignorados no)."""
    r = subprocess.run(["git", "-C", cwd, "status", "--porcelain=v1", "-z", "--untracked-files=all"],
                       capture_output=True, timeout=30)
    if r.returncode != 0:
        return None
    raiz = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True, timeout=30).stdout.strip()
    resultado = {}
    entradas = r.stdout.decode("utf-8", "replace").split("\0")
    i = 0
    while i < len(entradas):
        e = entradas[i]
        i += 1
        if len(e) < 4:
            continue
        estado, ruta = e[:2], e[3:]
        if "R" in estado or "C" in estado:
            i += 1  # el siguiente campo es la ruta de origen
        archivo = Path(raiz) / ruta
        resultado[ruta] = hashlib.sha1(archivo.read_bytes()).hexdigest() if archivo.is_file() else "borrado"
    return resultado


def kanban_db():
    return Path(os.environ.get("GIBRAN_KANBAN_DB") or
                Path(os.environ.get("LOCALAPPDATA", ".")) / "hermes" / "kanban.db")


def paralelas(cwd, desde):
    """Tarjetas de otro perfil que el revisor (los revisores no escriben) trabajando en este
    worktree desde `desde`. Sin kanban legible devuelve [] (se comporta como antes)."""
    raiz = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True, timeout=30).stdout.strip()
    normal = lambda r: os.path.normcase(os.path.realpath(r))  # realpath: nombres cortos 8.3
    try:
        c = sqlite3.connect(f"file:{kanban_db()}?mode=ro", uri=True)
        filas = c.execute("select t.id, t.workspace_path from task_runs r join tasks t on t.id = r.task_id "
                          "where r.profile != 'revisor' and (r.ended_at is null or r.ended_at >= ?)",
                          (desde,)).fetchall()
        c.close()
    except sqlite3.Error:
        return []
    return sorted({i for i, w in filas if raiz and w and normal(w) == normal(raiz)})


def diferencias(antes, ahora):
    return sorted(r for r in set(antes) | set(ahora) if antes.get(r) != ahora.get(r))


def evaluar(payload):
    sid, cwd = payload.get("session_id"), payload.get("cwd")
    if not sid or not cwd:
        return {}
    ruta_foto = carpeta_fotos() / f"{hashlib.sha1(sid.encode()).hexdigest()}.json"
    if not ruta_foto.exists():
        actual = foto(cwd)
        if actual is not None:
            ruta_foto.parent.mkdir(parents=True, exist_ok=True)
            ruta_foto.write_text(json.dumps({"cwd": cwd, "archivos": actual, "ts": int(time.time())}),
                                 encoding="utf-8")
        return {}
    if not any(nombre in CIERRES for nombre, _ in llamadas(payload)):
        return {}
    guardada = json.loads(ruta_foto.read_text(encoding="utf-8"))
    actual = foto(guardada["cwd"])
    if actual is None:
        return {}
    cambiados = diferencias(guardada["archivos"], actual)
    otras = paralelas(guardada["cwd"], guardada.get("ts", 0)) if cambiados else []
    if otras:  # lo nuevo fuera de la foto es de la tarjeta en paralelo
        cambiados = [r for r in cambiados if r in guardada["archivos"]]
    if not cambiados:
        return {}
    lista = ", ".join(cambiados[:10]) + (f" y {len(cambiados) - 10} más" if len(cambiados) > 10 else "")
    return bloquear(
        "Gibran Flow: el worktree ya no es el que recibiste para revisar. Cambiaron: " + lista + ". "
        "Tú no lo modificas; si fue tu build o una herramienta que regenera archivos versionados, "
        "igual es un hallazgo. No apruebes ni pidas cambios así: usa kanban_block diciendo qué "
        "cambió y por qué."
        + (f" Hay tarjetas en paralelo en este worktree ({', '.join(otras)}): si fueron ellas, dilo "
           "así; lo que revisaste cambió y el veredicto ya no aplica." if otras else ""))


if __name__ == "__main__":
    ejecutar(evaluar)
