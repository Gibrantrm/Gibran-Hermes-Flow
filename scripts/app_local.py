"""Levantar y detener la app local de un worktree (pruebas E2E), sin cerrar apps ajenas.

Uso (desde el worktree):
  python app_local.py iniciar --puerto auto --copia <bin del proyecto web> --env ASPNETCORE_ENVIRONMENT=Development       -- dotnet {copia}/App.dll --urls https://localhost:{puerto} --contentRoot <proyecto web>
  python app_local.py iniciar --puerto auto -- pnpm dev --port {puerto} --strictPort
  python app_local.py detener          # mata el árbol de las apps registradas de este worktree
  python app_local.py estado

--puerto auto: uno libre del rango de los agentes (51300-51399), lejos de los de desarrollo.
--puerto N: cuando el puerto es fijo (en código o porque otro componente lo espera); si está
  ocupado (p. ej. por la instancia del usuario) no lo comparte ni lo mata: falla.
--copia: copia esa carpeta a la carpeta temporal y la app corre desde ahí, así no bloquea los
  binarios del worktree y otras tarjetas pueden compilar en paralelo. {copia} y {puerto} se
  sustituyen en el comando.

Registro: un archivo por puerto en <temp>/gibran-apps/ con worktree y tarjeta (HERMES_KANBAN_TASK).
Un archivo por app: dos tarjetas en paralelo no se pisan el registro, y reservar el archivo
reserva el puerto. `detener` mata las apps de este worktree, menos las de OTRA tarjeta que sigue
corriendo o en revisión. Lo que escucha en el rango sin registro solo se reporta: no se puede
demostrar que sea de esta tarea, y tampoco se borra su posible copia.
"""
import argparse
import json
import os
import re
import socket
import sqlite3
import subprocess
import sys
import shutil
import tempfile
import time
from pathlib import Path


RANGO = range(51300, 51400)
DIR = Path(tempfile.gettempdir()) / "gibran-apps"
ACTIVAS = ("running", "review")  # una app de otra tarjeta en estos estados no se toca


def raiz(cwd):
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=cwd, capture_output=True, text=True)
    ruta = r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else str(cwd)
    return os.path.normcase(os.path.normpath(ruta))


def registradas():
    apps = []
    for f in DIR.glob("*.json") if DIR.is_dir() else []:
        try:
            apps.append(json.loads(f.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            pass  # reservado y aún sin escribir, o a medias
    return apps


def apps_de(worktree):
    w = raiz(worktree)
    return [a for a in registradas() if a.get("worktree") == w]


def escuchando(puerto):
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", puerto)) == 0


def vivo(pid):
    if os.name == "nt":
        # En bytes: tasklist responde en la página de códigos de la consola (p. ej. "INFORMACIÓN" en
        # cp850) y con PYTHONUTF8=1 decodificar como texto truena y deja stdout en None.
        r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"], capture_output=True)
        return f'"{pid}"'.encode() in r.stdout
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def matar_arbol(pid):
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
    else:  # ponytail: en POSIX solo el grupo del proceso; basta mientras el flujo corra en Windows
        try:
            os.killpg(pid, 9)
        except OSError:
            pass


def pid_en_puerto(puerto):
    if os.name != "nt":
        return None  # ponytail: huérfanas solo en Windows, donde corre el flujo
    r = subprocess.run(["netstat", "-ano", "-p", "TCP"], capture_output=True)
    m = re.search(rf":{puerto}\s+\S+\s+LISTENING\s+(\d+)".encode(), r.stdout)
    return int(m.group(1)) if m else None


def estado_tarjeta(tarea):
    db = Path(os.environ.get("LOCALAPPDATA", ".")) / "hermes" / "kanban.db"
    try:
        c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        fila = c.execute("select status from tasks where id = ?", (tarea,)).fetchone()
        c.close()
        return fila[0] if fila else None
    except sqlite3.Error:
        return "running"  # sin Kanban legible, no se arriesga a matar la app de otro


def otra_activa_en(worktree, mia):
    """Hay otra tarjeta en estados ACTIVAS con este worktree (dueño desconocido => se protege)."""
    db = Path(os.environ.get("LOCALAPPDATA", ".")) / "hermes" / "kanban.db"
    objetivo = os.path.normcase(os.path.normpath(str(worktree)))
    try:
        c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        filas = c.execute("select id, workspace_path from tasks where status in (?, ?)", ACTIVAS).fetchall()
        c.close()
    except sqlite3.Error:
        return True  # sin Kanban legible, no se arriesga
    return any(i != mia and w and os.path.normcase(os.path.normpath(w)) == objetivo for i, w in filas)


def reservar(puerto):
    """Crea el registro del puerto de forma atómica. Un registro viejo (app muerta, puerto libre) se recicla."""
    DIR.mkdir(parents=True, exist_ok=True)
    f = DIR / f"{puerto}.json"
    try:
        viejo = json.loads(f.read_text(encoding="utf-8"))
        if not vivo(viejo["pid"]) and not escuchando(puerto):
            f.unlink(missing_ok=True)
    except (OSError, ValueError, KeyError):
        pass  # no existe, o es una reserva en curso de otro
    try:
        with open(f, "x"):
            return True
    except FileExistsError:
        return False


def iniciar(cwd, puerto, comando, espera, copia=None, env=(), tarea=None):
    if puerto == "auto":
        puerto = next((n for n in RANGO if not escuchando(n) and reservar(n)), None)
        if puerto is None:
            print(f"app_local: no hay puerto libre en {RANGO.start}-{RANGO.stop - 1}.")
            return 2
    else:
        puerto = int(puerto)
        if escuchando(puerto) or not reservar(puerto):
            print(f"app_local: el puerto {puerto} ya está ocupado por otro proceso. No se comparte ni se "
                  "mata: si es una app de esta tarea, corre `detener`; si no, que el usuario lo libere o "
                  "cambia la configuración que fija ese puerto.")
            return 2
    destino = None
    if copia:
        destino = Path(tempfile.gettempdir()) / f"app-{puerto}"
        shutil.rmtree(destino, ignore_errors=True)
        try:
            shutil.copytree(Path(cwd) / copia, destino)
        except OSError:
            (DIR / f"{puerto}.json").unlink(missing_ok=True)  # suelta la reserva
            raise
    comando = [c.replace("{puerto}", str(puerto)).replace("{copia}", str(destino or "")) for c in comando]
    if not (tarea or os.environ.get("HERMES_KANBAN_TASK")):
        print("app_local: aviso: HERMES_KANBAN_TASK vacío; la app queda registrada sin tarjeta y un "
              "`detener` ajeno solo la respeta mientras haya otra tarjeta activa en este worktree. "
              "Mejor pasa --tarea <id-de-tu-tarjeta>.")
    print(f"PUERTO={puerto}", flush=True)
    log = Path(tempfile.gettempdir()) / f"app-local-{puerto}.log"
    salida = open(log, "wb")
    opciones = ({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS}
                if os.name == "nt" else {"start_new_session": True})
    entorno = {**os.environ, **dict(e.split("=", 1) for e in env)}
    p = subprocess.Popen(comando, cwd=cwd, stdout=salida, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                         env=entorno, **opciones)
    (DIR / f"{puerto}.json").write_text(json.dumps({
        "pid": p.pid, "puerto": puerto, "comando": " ".join(comando), "copia": str(destino) if destino else None,
        "worktree": raiz(cwd), "tarea": tarea or os.environ.get("HERMES_KANBAN_TASK") or None}), encoding="utf-8")
    limite = time.monotonic() + espera
    while time.monotonic() < limite:
        if escuchando(puerto):
            print(f"app_local: lista en el puerto {puerto} (PID {p.pid}). Salida: {log}")
            return 0
        if p.poll() is not None:
            print(f"app_local: la app terminó con código {p.returncode} antes de escuchar. Salida: {log}")
            return 1
        time.sleep(1)
    print(f"app_local: el puerto {puerto} no respondió en {espera} s (la app sigue registrada). Salida: {log}")
    return 1


def detener(cwd, tarea=None):
    mia = tarea or os.environ.get("HERMES_KANBAN_TASK") or None
    propias, ajenas = [], []
    for a in apps_de(cwd):
        otra = (a.get("tarea") and a["tarea"] != mia and estado_tarjeta(a["tarea"]) in ACTIVAS) or (
            not a.get("tarea") and otra_activa_en(a.get("worktree") or raiz(cwd), mia))
        (ajenas if otra else propias).append(a)
    con_registro = {a["puerto"] for a in registradas()}
    sin_registro = [{"pid": pid, "puerto": n}
                    for n in RANGO if n not in con_registro and escuchando(n) and (pid := pid_en_puerto(n))]
    for a in propias:
        matar_arbol(a["pid"])
    time.sleep(1)
    for a in propias:
        if a.get("copia"):
            shutil.rmtree(a["copia"], ignore_errors=True)
    vivas = [a for a in propias if vivo(a["pid"]) or escuchando(a["puerto"])]
    for a in propias:
        if a not in vivas:
            (DIR / f"{a['puerto']}.json").unlink(missing_ok=True)
    if ajenas:
        print(f"app_local: no toqué {len(ajenas)} app(s) de otra tarjeta activa (puertos {[a['puerto'] for a in ajenas]}).")
    if sin_registro:
        print(f"app_local: aviso: no toqué procesos sin registro (PID {[a['pid'] for a in sin_registro]}, "
              f"puertos {[a['puerto'] for a in sin_registro]}): no se puede demostrar que sean de esta tarea.")
    if vivas:
        print(f"app_local: siguen activos PID {[a['pid'] for a in vivas]} / puertos {[a['puerto'] for a in vivas]}. Repórtalo.")
        return 1
    print(f"app_local: {len(propias)} app(s) detenida(s); sus puertos libres." if propias else "app_local: no había apps de esta tarea.")
    return 0


def estado(cwd):
    apps = apps_de(cwd)
    if not apps:
        print("app_local: no hay apps registradas en este worktree.")
    for a in apps:
        print(f"PID {a['pid']} {'vivo' if vivo(a['pid']) else 'muerto'} · puerto {a['puerto']} "
              f"{'escuchando' if escuchando(a['puerto']) else 'libre'} · tarjeta {a.get('tarea')} · {a['comando']}")
    return 0


def main(argv, cwd=None):
    cwd = cwd or os.getcwd()
    p = argparse.ArgumentParser(prog="app_local")
    sub = p.add_subparsers(dest="accion", required=True)
    i = sub.add_parser("iniciar")
    i.add_argument("--puerto", required=True, help="auto o un número")
    i.add_argument("--espera", type=int, default=180)
    i.add_argument("--copia", help="carpeta (relativa al worktree) a copiar y correr desde la temporal")
    i.add_argument("--env", action="append", default=[], help="NOMBRE=valor para la app")
    i.add_argument("--tarea", help="id de la tarjeta dueña (si HERMES_KANBAN_TASK no llega a la shell)")
    i.add_argument("comando", nargs=argparse.REMAINDER)
    d = sub.add_parser("detener")
    d.add_argument("--tarea", help="id de la tarjeta que llama (si HERMES_KANBAN_TASK no llega a la shell)")
    sub.add_parser("estado")
    a = p.parse_args(argv)
    if a.accion == "iniciar":
        comando = a.comando[1:] if a.comando[:1] == ["--"] else a.comando
        if not comando:
            p.error("falta el comando después de --")
        if a.puerto != "auto" and not a.puerto.isdigit():
            p.error("--puerto debe ser auto o un número")
        return iniciar(cwd, a.puerto, comando, a.espera, a.copia, a.env, a.tarea)
    return detener(cwd, a.tarea) if a.accion == "detener" else estado(cwd)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
