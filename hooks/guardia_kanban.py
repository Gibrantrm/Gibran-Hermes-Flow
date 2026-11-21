"""pre_tool_call (kanban_request_review|kanban_complete|tool_call), solo en el implementador.

Sin reviewer, kanban_request_review deja la tarjeta asignada al implementador y el despachador
lanza OTRO implementador a revisarla, que la cierra él mismo.
Dos barreras: la revisión siempre va al revisor y el implementador nunca cierra tarjetas.
"""
from comun import bloquear, ejecutar, llamadas

REVISOR = "revisor"
MENSAJE_REVISION = ('Gibran Flow: pide la revisión con reviewer="revisor"; sin él la tarjeta '
                    'no llega al revisor.')
MENSAJE_CIERRE = ("Gibran Flow: el implementador no cierra tarjetas. Pide revisión con "
                  'kanban_request_review(reviewer="revisor") o bloquéala con kanban_block.')


def evaluar(payload):
    directa = payload.get("tool_name") != "tool_call"
    for nombre, args in llamadas(payload):
        if nombre == "kanban_complete":
            return bloquear(MENSAJE_CIERRE)
        if nombre == "kanban_request_review" and args.get("reviewer") != REVISOR:
            if not directa:  # dentro del envoltorio no se puede reescribir
                return bloquear(MENSAJE_REVISION)
            # Reescribir en vez de bloquear: el worker no gasta una llamada en corregirse.
            return {"action": "modify", "args": {**args, "reviewer": REVISOR}}
    return {}


if __name__ == "__main__":
    ejecutar(evaluar)
