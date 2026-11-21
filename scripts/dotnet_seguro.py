"""dotnet con candado por worktree: evita que dos workers compilen a la vez la misma carpeta.

Uso:  python dotnet_seguro.py build Proyecto.csproj   (mismos argumentos que dotnet)
Solo build/test/run/publish esperan el candado; el resto pasa directo a dotnet.
"""
import contextlib
import msvcrt
import os
import re
import subprocess
import sys
import time
from pathlib import Path

COMPILAN = {"build", "test", "run", "publish"}
ESPERA_MAX = 15 * 60
ESPERA_AGOTADA = 75  # código propio: el agente sabe que fue el candado, no el build


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


def compilar(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       env={**os.environ, "DOTNET_NOLOGO": "1"})
    sys.stdout.buffer.write(compactar(r.stdout))
    sys.stdout.flush()
    return r.returncode


def main(argv, dotnet=("dotnet",), candado=None, espera_max=ESPERA_MAX, intervalo=2.0):
    cmd = [*dotnet, *argv]
    if not argv or argv[0] not in COMPILAN or (argv[0] == "run" and "--no-build" in argv):
        return subprocess.run(cmd).returncode
    try:
        with con_candado(candado or ruta_candado(Path.cwd()), espera_max, intervalo):
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


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
