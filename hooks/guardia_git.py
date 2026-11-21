"""pre_tool_call (terminal|execute_code): bloquea git que escribe historia o borra trabajo,
comandos que escriben en base de datos y matar procesos por nombre."""
import re

from comun import bloquear, ejecutar, textos

# git o git.exe (cualquier mayúscula), opciones globales (-C ruta, -c k=v, --no-pager), subcomando
PREFIJO = (r"\b[Gg][Ii][Tt](?:\.[Ee][Xx][Ee])?"
           r"(?:\s+(?:-[Cc]\s+(?:\"[^\"]*\"|'[^']*'|\S+)|--[\w-]+(?:=\S+)?))*\s+")
SIN_SEP = r"[^\n;&|]*"
MENSAJE_GIT = ("Gibran Flow: los agentes no hacen commit, push, reset --hard, clean, branch -D, "
               "checkout/restore que descartan cambios ni stash drop/clear. Deja los cambios en el "
               "worktree; Gibran hace el commit tras el control final.")
MENSAJE_BD = ("Gibran Flow: los agentes no escriben en base de datos desde la terminal "
              "(dotnet ef database update/drop, migrations remove, psql con DML/DDL). "
              "Propón el script en docs/scripts/.")
MENSAJE_KILL = ("Gibran Flow: no mates procesos por nombre (taskkill /IM, Stop-Process -Name, pkill, "
                "killall): también cierra los del usuario (su Chrome, sus apps). Tus apps se detienen con "
                "app_local.py detener y el navegador de Playwright con browser_close; si algo sigue vivo, "
                "repórtalo.")
REGLAS = [
    (re.compile(PREFIJO + r"(commit|push|clean|restore)\b"), MENSAJE_GIT),
    (re.compile(PREFIJO + r"reset\b" + SIN_SEP + r"--hard"), MENSAJE_GIT),
    (re.compile(PREFIJO + r"branch\b" + SIN_SEP +
                r"(\s-[a-zA-Z]*D|--delete\b" + SIN_SEP + r"--force|--force\b" + SIN_SEP + r"--delete)"),
     MENSAJE_GIT),
    (re.compile(PREFIJO + r"checkout\b" + SIN_SEP + r"?(\s--(\s|$)|\s-f\b|\s\.(\s|$))"), MENSAJE_GIT),
    (re.compile(PREFIJO + r"stash\s+(drop|clear)\b"), MENSAJE_GIT),
    (re.compile(r"(?i)\bdotnet\s+ef\s+(database\s+(update|drop)|migrations\s+remove)\b"), MENSAJE_BD),
    (re.compile(r"(?i)\bpsql\b[^\n]*(\s-c\b|--command\b)[^\n]*"
                r"\b(insert|update|delete|drop|alter|truncate|create|grant)\b"), MENSAJE_BD),
    (re.compile(r"(?i)\btaskkill\b" + SIN_SEP + r"\s[/-]{1,2}im\b"), MENSAJE_KILL),
    (re.compile(r"(?i)\bstop-process\b" + SIN_SEP + r"\s-(process)?name\b"), MENSAJE_KILL),
    (re.compile(r"(?i)\bget-process\s+(?!-id\b)[^\n;&|]*\|\s*(stop-process|kill)\b"), MENSAJE_KILL),
    (re.compile(r"(?i)\b(pkill|killall)\b"), MENSAJE_KILL),
]


def evaluar(payload):
    texto = textos(payload.get("tool_input"))
    # ["git", "commit"] o & "git" push: sin comillas, comas ni corchetes queda "git commit"
    plano = re.sub(r"[\"'\[\],]", " ", texto)
    for regla, mensaje in REGLAS:
        if regla.search(texto) or regla.search(plano):
            return bloquear(mensaje)
    return {}


if __name__ == "__main__":
    ejecutar(evaluar)
