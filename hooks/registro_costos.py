"""post_api_request: agrega una línea por llamada al modelo en costos.jsonl."""
import datetime
import json
import os
from pathlib import Path

from comun import ejecutar


def destino():
    if os.environ.get("GIBRAN_COSTOS"):
        return Path(os.environ["GIBRAN_COSTOS"])
    return Path(os.environ["LOCALAPPDATA"]) / "hermes" / "logs" / "costos.jsonl"


def perfil_actual():
    home = os.environ.get("HERMES_HOME", "")
    return Path(home).name if "profiles" in Path(home).parts else "default"


def linea(payload, perfil, ahora):
    extra = payload.get("extra") or {}
    usage = extra.get("usage")
    return {"ts": ahora, "perfil": perfil, "session": payload.get("session_id"),
            "model": extra.get("model"), "provider": extra.get("provider"),
            "duracion": extra.get("api_duration"),
            "usage": usage if isinstance(usage, dict) else {}}


def evaluar(payload):
    if not payload:
        return {}
    registro = linea(payload, perfil_actual(), datetime.datetime.now().isoformat(timespec="seconds"))
    ruta = destino()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return {}


if __name__ == "__main__":
    ejecutar(evaluar)
