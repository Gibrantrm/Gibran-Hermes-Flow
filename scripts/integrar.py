"""Integrar una tarea aprobada: pasa los cambios del worktree a la rama de origen SIN commit.

Uso (el orquestador, solo después de que el usuario aprueba el Control final):
  python integrar.py --worktree <ruta> --rama <rama del worktree>

Destino: la rama que tiene abierta el repo principal (de la que salió el worktree: dev, una
feature, la que sea). Falla sin tocar nada si el worktree no salió de esa rama, si el repo
principal tiene cambios sin commit (se mezclarían con los de la tarea), si queda una app viva o
si el parche no entra limpio. Si entra, los cambios quedan staged en el repo principal, guarda
el parche de respaldo en la carpeta temporal y borra el worktree y su rama. El commit lo hace
el usuario.
"""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from app_local import apps_de, vivo  # noqa: E402


def git(cwd, *args, entrada=None):
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, input=entrada)


def texto(r):
    return r.stdout.decode("utf-8", "replace").strip()


def main(argv):
    p = argparse.ArgumentParser(prog="integrar")
    p.add_argument("--worktree", required=True)
    p.add_argument("--rama", required=True)
    a = p.parse_args(argv)
    wt = Path(a.worktree)

    comun = texto(git(wt, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    if not comun:
        print(f"integrar: {wt} no es un worktree de git.")
        return 2
    repo = Path(comun).parent
    if texto(git(wt, "branch", "--show-current")) != a.rama:
        print(f"integrar: el worktree no está en la rama {a.rama}.")
        return 2
    destino = texto(git(repo, "branch", "--show-current"))
    if not destino:
        print(f"integrar: el repo principal ({repo}) no tiene una rama abierta (HEAD separado).")
        return 2
    if git(repo, "merge-base", "--is-ancestor", a.rama, destino).returncode != 0:
        print(f"integrar: {a.rama} no salió de {destino} (la rama abierta en {repo}) o tiene commits "
              "propios. Abre ahí la rama de origen y vuelve a correrlo; los commits los resuelve el usuario.")
        return 2
    if texto(git(repo, "status", "--porcelain", "--untracked-files=no")):
        print(f"integrar: {repo} tiene cambios sin commit en {destino}; se mezclarían con los de la tarea. "
              "Que el usuario los guarde o los commitee primero.")
        return 2
    vivas = [x["pid"] for x in apps_de(wt) if vivo(x["pid"])]
    if vivas:
        print(f"integrar: siguen corriendo apps del worktree (PID {vivas}): corre app_local.py detener.")
        return 2

    git(wt, "add", "-A")  # solo stage, para incluir archivos nuevos en el parche; no hay commit
    parche = git(wt, "diff", "--cached", "--binary", "HEAD").stdout
    if not parche.strip():
        print("integrar: el worktree no tiene cambios.")
        return 2
    respaldo = Path(tempfile.gettempdir()) / f"integrar-{a.rama.replace('/', '-')}.patch"
    respaldo.write_bytes(parche)
    if git(repo, "apply", "--check", "--index", entrada=parche).returncode == 0:
        r = git(repo, "apply", "--index", entrada=parche)
    else:  # la rama de origen avanzó en esos archivos: merge de 3 vías
        r = git(repo, "apply", "--3way", "--index", entrada=parche)
    if r.returncode != 0 or git(repo, "diff", "--name-only", "--diff-filter=U").stdout.strip():
        # Seguro: arriba se verificó que no había cambios sin commit en archivos versionados.
        git(repo, "reset", "-q", "--hard", "HEAD")
        print(f"integrar: el parche no entra limpio en {destino} (conflictos con lo que cambió en la rama). "
              f"Dejé {destino} como estaba y el worktree intacto. Parche: {respaldo}")
        return 1
    esperados = set(texto(git(wt, "diff", "--cached", "--name-only", "HEAD")).splitlines())
    aplicados = set(texto(git(repo, "diff", "--cached", "--name-only")).splitlines())
    if esperados != aplicados:
        print(f"integrar: los archivos staged en {destino} no coinciden con los del worktree "
              f"(faltan {sorted(esperados - aplicados)}, sobran {sorted(aplicados - esperados)}). "
              f"Worktree intacto. Parche: {respaldo}")
        return 1

    git(repo, "worktree", "remove", "--force", str(wt))
    git(repo, "branch", "-D", a.rama)  # sin commits propios: no se pierde nada que no esté staged en destino
    print(f"integrar: {len(aplicados)} archivo(s) staged en {destino} ({repo}), sin commit.")
    print(f"integrar: worktree y rama {a.rama} borrados. Parche de respaldo: {respaldo}")
    print(f'Para terminar (usuario): cd "{repo}" && git diff --cached && git commit -m "<mensaje>"')
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
