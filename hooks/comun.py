"""Utilidades compartidas por los hooks de Gibran Flow."""
import json
import sys


def leer_payload(texto):
    try:
        datos = json.loads(texto) if texto.strip() else {}
    except ValueError:
        return {}
    return datos if isinstance(datos, dict) else {}


def textos(tool_input):
    if not isinstance(tool_input, dict):
        return ""
    return "\n".join(v for v in tool_input.values() if isinstance(v, str))


def llamadas(payload):
    """(nombre, argumentos) de la llamada, abriendo el envoltorio tool_call de herramientas diferidas."""
    nombre, args = payload.get("tool_name"), payload.get("tool_input")
    if nombre != "tool_call":
        return [(nombre, args if isinstance(args, dict) else {})]
    calls = (args or {}).get("calls") if isinstance(args, dict) else None
    salida = []
    for c in calls if isinstance(calls, list) else []:
        if isinstance(c, dict):
            a = c.get("arguments")
            if isinstance(a, str):
                try:
                    a = json.loads(a)
                except ValueError:
                    a = {}
            salida.append((c.get("name"), a if isinstance(a, dict) else {}))
    return salida


def bloquear(mensaje):
    return {"action": "block", "message": mensaje}


def ejecutar(evaluar):
    try:
        respuesta = evaluar(leer_payload(sys.stdin.read()))
    except Exception:  # un hook roto no debe imprimir trazas: fail_closed bloquearía todo
        respuesta = {}
    print(json.dumps(respuesta))
