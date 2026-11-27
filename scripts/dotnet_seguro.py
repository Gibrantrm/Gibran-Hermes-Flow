"""dotnet con candado por worktree: evita que dos workers compilen a la vez la misma carpeta.

Uso:  python dotnet_seguro.py build Proyecto.csproj   (mismos argumentos que dotnet)
      python dotnet_seguro.py test --tarea <id> Tests.csproj --filter "<filtro>"
      python dotnet_seguro.py autorizar-test --tarea <id> --worktree <ruta> -- <args-test>
El orquestador registra cada comando aprobado antes de despachar. Test exige coincidencia
exacta y guarda la salida completa fuera del repo. Es control del flujo, no un sandbox.
Solo build/test/run/publish esperan el candado; el resto pasa directo a dotnet.
"""
import argparse
import contextlib
import datetime
import json
import msvcrt
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path

COMPILAN = {"build", "test", "run", "publish"}
ESPERA_MAX = 15 * 60
ESPERA_AGOTADA = 75  # código propio: el agente sabe que fue el candado, no el build
ALCANCE_INVALIDO = 2


def estado_tests():
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise ValueError("falta LOCALAPPDATA; no se puede localizar el registro de pruebas")
    return Path(local) / "hermes" / "gibran-tests"


def identificar_tarea(explicita=None):
    entorno = os.environ.get("HERMES_KANBAN_TASK", "")
    tarea = explicita or entorno
    if not tarea or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", tarea):
        raise ValueError("falta una tarea válida; usa test --tarea <id> <proyecto> --filter <filtro>")
    if explicita and entorno and explicita != entorno:
        raise ValueError("--tarea no coincide con HERMES_KANBAN_TASK")
    return tarea


def seleccion_test(args, worktree):
    """Un proyecto concreto y un filtro; sin propiedades MSBuild, rsp ni argumentos de VSTest."""
    if not args or args[0].startswith(("-", "@")) or any(c in args[0] for c in "*?"):
        raise ValueError("test requiere un proyecto .csproj explícito")
    proyecto = (worktree / args[0]).resolve()
    if proyecto.suffix.lower() != ".csproj" or not proyecto.is_relative_to(worktree):
        raise ValueError("el proyecto de tests debe ser un .csproj dentro del worktree autorizado")
    sin_valor = {"--no-build", "--no-restore", "--nologo"}
    con_valor = {"--filter", "--configuration", "--framework", "--verbosity", "--logger"}
    alias = {"-c": "--configuration", "-f": "--framework", "-v": "--verbosity", "-l": "--logger"}
    vistas = set()
    i = 1
    while i < len(args):
        opcion = alias.get(args[i], args[i])
        if opcion in vistas or opcion not in sin_valor | con_valor:
            raise ValueError(f"opción de test no admitida o repetida: {args[i]}")
        vistas.add(opcion)
        i += 1
        if opcion in con_valor:
            if i == len(args) or not args[i].strip() or args[i].startswith(("-", "@")):
                raise ValueError(f"falta un valor explícito para {opcion}")
            i += 1
    if "--filter" not in vistas:
        raise ValueError("test sin --filter bloqueado; no ejecutes la suite completa")
    return [str(proyecto), *args[1:]]


def guardar_json(ruta, datos):
    temporal = ruta.with_name(f"{ruta.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
        temporal.replace(ruta)
    finally:
        temporal.unlink(missing_ok=True)


def leer_autorizacion(ruta, tarea, worktree):
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    if (not isinstance(datos, dict) or datos.get("version") != 1
            or datos.get("tarea") != tarea or datos.get("worktree") != str(worktree)
            or not isinstance(datos.get("comandos"), list)
            or not datos["comandos"]
            or any(not isinstance(c, list) or not c or
                   any(not isinstance(a, str) for a in c) for c in datos["comandos"])):
        raise ValueError("autorización inválida o perteneciente a otra tarea/worktree")
    return datos


def autorizar_test(argv):
    base = estado_tests()
    home = Path(os.environ.get("HERMES_HOME") or base.parent).resolve()
    if home != base.parent.resolve() or os.environ.get("HERMES_KANBAN_TASK"):
        raise ValueError("solo el orquestador (perfil default, fuera de un worker) autoriza tests")
    parser = argparse.ArgumentParser(description="Registrar un comando de tests aprobado")
    parser.add_argument("--tarea", required=True)
    parser.add_argument("--worktree", type=Path, required=True)
    parser.add_argument("comando", nargs=argparse.REMAINDER)
    opciones = parser.parse_args(argv)
    tarea = identificar_tarea(opciones.tarea)
    worktree = opciones.worktree.resolve()
    if not worktree.is_dir():
        raise ValueError("el worktree autorizado no existe")
    args = opciones.comando
    if not args or args[0] != "--":
        raise ValueError("separa los argumentos del test con --")
    seleccion = seleccion_test(args[1:], worktree)
    carpeta = base / "autorizaciones"
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"{tarea}.json"
    with con_candado(base / "autorizaciones.lock"):
        datos = (leer_autorizacion(ruta, tarea, worktree) if ruta.exists() else
                 {"version": 1, "tarea": tarea, "worktree": str(worktree), "comandos": []})
        if seleccion not in datos["comandos"]:
            datos["comandos"].append(seleccion)
            guardar_json(ruta, datos)
    print(f"dotnet_seguro: autorización registrada para {tarea}: {ruta}", flush=True)
    return 0


def validar_test(args):
    explicita = None
    if args and args[0] == "--tarea":
        if len(args) < 2:
            raise ValueError("falta el valor de --tarea")
        explicita, args = args[1], args[2:]
    tarea = identificar_tarea(explicita)
    worktree = Path.cwd().resolve()
    seleccion = seleccion_test(args, worktree)
    ruta = estado_tests() / "autorizaciones" / f"{tarea}.json"
    if not ruta.is_file():
        raise ValueError(f"no hay autorización de tests para {tarea}; pide registro al orquestador")
    datos = leer_autorizacion(ruta, tarea, worktree)
    if seleccion not in datos["comandos"]:
        raise ValueError("proyecto/filtro/opciones fuera del alcance aprobado; pide autorización")
    return tarea, ["test", *seleccion]


def ruta_candado(cwd):
    """<git-dir>/gibran-build.lock: uno por worktree y fuera del diff. Sin git: en cwd."""
    r = subprocess.run(["git", "rev-parse", "--absolute-git-dir"], cwd=cwd,
                       capture_output=True, text=True)
    base = Path(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else Path(cwd)
    return base / "gibran-build.lock"


@contextlib.contextmanager
def con_candado(ruta, espera_max=ESPERA_MAX, intervalo=2.0):
    # Windows libera el bloqueo si el proceso muere: un worker colgado no deja el candado tomado.
    f = open(ruta, "a+b")
    limite = time.monotonic() + espera_max
    avisado = False
    try:
        while True:
            try:
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError:
                if time.monotonic() >= limite:
                    raise TimeoutError
                if not avisado:
                    print("dotnet_seguro: esperando a otra compilación en este worktree…", flush=True)
                    avisado = True
                time.sleep(intervalo)
        yield
        f.seek(0)
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
    finally:
        f.close()


def compactar(salida):
    """Quita líneas repetidas (MSBuild repite cada warning, también una vez por proyecto que lo
    hereda: se compara sin el "[Proyecto.csproj]" final) y las rutas "Proyecto -> bin/...".

    Cada línea que llega al agente se reenvía en todas sus llamadas siguientes.
    En bytes para no depender de la página de códigos de la consola.
    """
    vistas, quedan = set(), []
    for linea in salida.splitlines():
        clave = re.sub(rb"\s*\[[^\]]*\]\s*$", b"", linea)
        if clave in vistas or re.match(rb"^\s+\S+ -> \S", linea):
            continue
        vistas.add(clave)
        quedan.append(linea)
    return b"\n".join(quedan) + b"\n"


# Opciones de `dotnet run` que también entiende `dotnet build` (el resto son solo de run).
OPCIONES_BUILD = {"-c": True, "--configuration": True, "-f": True, "--framework": True,
                  "-r": True, "--runtime": True, "--no-restore": False}


def partir_run(argv):
    """`run …` → (build con candado, run --no-build sin candado).

    Con el candado durante toda la vida de la app, un `dotnet test` (p. ej. las E2E contra esa
    app) esperaría hasta agotar el candado: solo la compilación lo necesita.
    """
    resto = argv[1:]
    corte = resto.index("--") if "--" in resto else len(resto)
    opciones, de_la_app = resto[:corte], resto[corte:]
    build = ["build"]
    i = 0
    while i < len(opciones):
        o = opciones[i]
        if o == "--project" and i + 1 < len(opciones):
            build.append(opciones[i + 1])
            i += 2
            continue
        if o in OPCIONES_BUILD:
            lleva_valor = OPCIONES_BUILD[o] and i + 1 < len(opciones)
            build += opciones[i:i + 2] if lleva_valor else [o]
            i += 2 if lleva_valor else 1
            continue
        i += 1
    return build, ["run", *opciones, "--no-build", *de_la_app]


def test_con_evidencia(cmd, tarea):
    carpeta = estado_tests() / "ejecuciones"
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"{tarea}-{uuid.uuid4().hex}.json"
    datos = {"tarea": tarea, "worktree": str(Path.cwd().resolve()), "comando": cmd,
             "inicio": datetime.datetime.now(datetime.timezone.utc).isoformat(), "codigo": None}
    guardar_json(ruta, datos)
    print(f"dotnet_seguro: evidencia completa en {ruta.with_suffix('.log')}", file=sys.stderr, flush=True)
    try:
        # Abrir antes de lanzar: si no podemos conservar la evidencia, no ejecutamos pruebas.
        with ruta.with_suffix(".log").open("xb") as salida:
            r = subprocess.run(cmd, stdout=salida, stderr=subprocess.STDOUT,
                               env={**os.environ, "DOTNET_NOLOGO": "1"})
        datos["codigo"] = r.returncode
    except OSError as exc:
        datos["error"] = str(exc)
        raise
    finally:
        datos["fin"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        guardar_json(ruta, datos)
    sys.stdout.buffer.write(compactar(ruta.with_suffix(".log").read_bytes()))
    sys.stdout.flush()
    return r.returncode


def compilar(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       env={**os.environ, "DOTNET_NOLOGO": "1"})
    sys.stdout.buffer.write(compactar(r.stdout))
    sys.stdout.flush()
    return r.returncode


def main(argv, dotnet=("dotnet",), candado=None, espera_max=ESPERA_MAX, intervalo=2.0):
    try:
        if argv and argv[0] == "autorizar-test":
            return autorizar_test(argv[1:])
        tarea = None
        if argv and argv[0] == "test":
            tarea, argv = validar_test(argv[1:])
    except (ValueError, OSError, UnicodeError) as exc:
        print(f"dotnet_seguro: BLOQUEADO: {exc}", file=sys.stderr, flush=True)
        return ALCANCE_INVALIDO
    cmd = [*dotnet, *argv]
    if not argv or argv[0] not in COMPILAN or (argv[0] == "run" and "--no-build" in argv):
        return subprocess.run(cmd).returncode
    try:
        with con_candado(candado or ruta_candado(Path.cwd()), espera_max, intervalo):
            if tarea:
                return test_con_evidencia(cmd, tarea)
            if argv[0] != "run":
                return compilar(cmd)
            build, run = partir_run(argv)
            codigo = compilar([*dotnet, *build])
        # Fuera del candado: la app corre (y su salida en vivo) sin bloquear otros builds o tests.
        return codigo if codigo else subprocess.run([*dotnet, *run]).returncode
    except TimeoutError:
        print(f"dotnet_seguro: el candado de build siguió ocupado {espera_max // 60} min. "
              "Otra compilación no termina; reintenta más tarde o reporta el bloqueo.", flush=True)
        return ESPERA_AGOTADA
    except OSError as exc:
        print(f"dotnet_seguro: no se pudo ejecutar o conservar la evidencia: {exc}",
              file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
