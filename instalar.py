"""Aplica Gibran Flow a los perfiles de Hermes: hooks, skills, modelos, SOULs.

Uso:  python instalar.py            # respalda y escribe
      python instalar.py --solo-mostrar
"""
import copy
import datetime
import os
import shutil
import sys
from pathlib import Path

import yaml

MARCA = "hermes-flow/hooks/"
HERMES = Path(os.environ["LOCALAPPDATA"]) / "hermes"
PERFILES = {
    "default": HERMES,
    "implementador": HERMES / "profiles" / "implementador",
    "revisor": HERMES / "profiles" / "revisor",
}
MODELOS = {
    "implementador": {"default": "claude-haiku-5.5", "provider": "copilot"},
    "revisor": {"default": "gpt-6.1-sol", "provider": "copilot"},
}
# Si Copilot devuelve 429/cuota, Hermes cambia a este modelo en ese mismo turno.
# ponytail: el revisor pierde la familia distinta (GPT) mientras dure el respaldo.
RESPALDO = {
    "implementador": [{"provider": "anthropic", "model": "claude-haiku-5-5"}],
    "revisor": [{"provider": "anthropic", "model": "claude-sonnet-5"}],
}
# Los hijos de delegate_task no heredan respaldo (delegation.provider fijado), se cambian a mano.
HIJOS = {
    "copilot": {"provider": "copilot", "model": "claude-haiku-5.5"},
    "anthropic": {"provider": "anthropic", "model": "claude-haiku-5-5"},
}
# Toolsets nativos que no se usan: sus esquemas se pagan en cada llamada.
# Los workers no preguntan (clarify): si dudan, se bloquean.
# code_execution: Hermes lo bloquea en modo -q (sin usuario) y habilitarlo saltaría los hooks.
SIN_USO_WORKERS = ["delegation", "browser", "image_gen", "tts", "vision", "computer_use",
                   "cronjob", "session_search", "clarify", "web", "code_execution"]
# El orquestador conserva web y su navegador es el MCP playwright.
# 0.0.83: la versión con la que se verificó en vivo (2026-10-30). Súbela a mano tras probarla.
PLAYWRIGHT_MCP = "@playwright/mcp@0.0.83"
SIN_USO_ORQUESTADOR = ["browser", "image_gen", "tts", "computer_use", "cronjob"]


def _cmd(py, repo, script):
    return f'"{py}" "{repo}/hooks/{script}"'


def _reemplazar_propios(lista, nuevos):
    return [h for h in (lista or []) if MARCA not in h.get("command", "")] + nuevos


def configurar(cfg, perfil, repo, py):
    if perfil not in PERFILES:
        raise ValueError(f"perfil desconocido: {perfil}")
    cfg = copy.deepcopy(cfg)

    skills = cfg.setdefault("skills", {})
    dirs = skills.setdefault("external_dirs", [])
    if f"{repo}/skills" not in dirs:
        dirs.append(f"{repo}/skills")

    hooks = cfg.setdefault("hooks", {})
    hooks["pre_tool_call"] = _reemplazar_propios(hooks.get("pre_tool_call"), [
        {"matcher": "terminal|execute_code", "command": _cmd(py, repo, "guardia_git.py"),
         "timeout": 10, "fail_closed": True},
        {"matcher": "write_file|patch", "command": _cmd(py, repo, "guardia_secretos.py"),
         "timeout": 10, "fail_closed": True},
        # tool_call: envoltorio de herramientas diferidas; el hook abre sus llamadas.
        {"matcher": "write_file|patch|skill_manage|tool_call",
         "command": _cmd(py, repo, "guardia_rutas.py") + (" --solo-lectura" if perfil == "revisor" else ""),
         "timeout": 10, "fail_closed": True},
    ] + ([
        # Solo workers: comparten worktree y compilan en paralelo.
        {"matcher": "terminal|execute_code", "command": _cmd(py, repo, "guardia_build.py"),
         "timeout": 10, "fail_closed": True},
    ] if perfil in MODELOS else []) + ([
        # Solo implementador: la revisión siempre va al revisor y nunca cierra tarjetas él mismo.
        {"matcher": "kanban_request_review|kanban_complete|tool_call",
         "command": _cmd(py, repo, "guardia_kanban.py"), "timeout": 10, "fail_closed": True},
    ] if perfil == "implementador" else []) + ([
        # Solo revisor, sin matcher (todas las herramientas): foto del worktree al empezar y
        # comparación antes de aprobar o pedir cambios.
        {"command": _cmd(py, repo, "guardia_revision.py"), "timeout": 30, "fail_closed": True},
    ] if perfil == "revisor" else []))
    hooks["post_api_request"] = _reemplazar_propios(hooks.get("post_api_request"), [
        {"command": _cmd(py, repo, "registro_costos.py"), "timeout": 10},
    ])
    cfg["hooks_auto_accept"] = True

    deshabilitados = cfg.setdefault("agent", {}).setdefault("disabled_toolsets", [])
    sin_uso = SIN_USO_WORKERS if perfil in MODELOS else SIN_USO_ORQUESTADOR
    if perfil == "revisor":
        # El revisor mira los screenshots de las pruebas E2E (vision_analyze).
        sin_uso = [t for t in sin_uso if t != "vision"]
        if "vision" in deshabilitados:
            deshabilitados.remove("vision")
    for t in sin_uso:
        if t not in deshabilitados:
            deshabilitados.append(t)

    # Versión fija del MCP de Playwright: con @latest cambia sin aviso entre una prueba y otra.
    playwright = (cfg.get("mcp_servers") or {}).get("playwright") or {}
    playwright["args"] = [PLAYWRIGHT_MCP if str(a).startswith("@playwright/mcp") else a
                          for a in playwright.get("args") or []]

    # Poda sin LLM de resultados de herramientas viejos cuando el historial pasa de 48k: solo en el
    # orquestador (sesión larga). En los workers (prueba 2026-10-26) recortaba las skills cargadas,
    # skill_view respondía "sin cambios" y las releían con read_file; 0 = apagada.
    cfg.setdefault("compression", {})["proactive_prune_tokens"] = 0 if perfil in MODELOS else 48000

    # Auto-revisión de Hermes (tras cada turno un agente extra guarda/edita skills y memoria): apagada
    # en todos. En la prueba 2026-10-27 editó skills del flujo a media prueba; lo aprendido entra
    # solo por propuestas-de-mejora.md y /aprender.
    cfg.setdefault("auxiliary", {}).setdefault("background_review", {})["enabled"] = False

    if perfil not in MODELOS:
        # El orquestador crea tarjetas con kanban_create: así queda suscrito y la TUI le avisa
        # cuando una termina o se bloquea (la CLI clásica no recibe avisos). Los workers ya
        # tienen las herramientas de Kanban por ser despachados.
        plataformas = cfg.setdefault("platform_toolsets", {})
        for plataforma, base in (("cli", "hermes-cli"), ("tui", "hermes-tui")):
            lista = plataformas.setdefault(plataforma, [base])
            if "kanban" not in lista:
                lista.append("kanban")

    if perfil in MODELOS:
        # Freno de emergencia: una tarjeta normal usa ~30 llamadas. Al llegar al tope el worker
        # sale sin kanban_complete y Kanban bloquea la tarjeta (no reintenta en bucle).
        cfg["agent"]["max_turns"] = 150
        cfg["model"] = dict(MODELOS[perfil])
        cfg["fallback_providers"] = copy.deepcopy(RESPALDO[perfil])
    else:
        # El orquestador crea y asigna los worktrees; el aislamiento de Hermes crearía otro
        # por hijo y le pediría commitear (choca con modo-feature y la guardia de git).
        cfg.setdefault("delegation", {})["worktree_isolation"] = False
        # El orquestador espera al usuario y a los workers más de 5 min: con caché de 5m reescribe
        # todo su contexto (con recargo) en cada pausa. Los workers trabajan seguido: se quedan en 5m.
        cfg.setdefault("prompt_caching", {})["cache_ttl"] = "1h"
        qc = cfg.setdefault("quick_commands", {})
        qc["tablero"] = {"type": "exec", "command": "hermes kanban list"}
        qc["despachar"] = {"type": "exec", "command": "hermes kanban dispatch"}
        qc["worktrees"] = {"type": "exec", "command": "git worktree list"}
        qc["costos"] = {"type": "exec", "command": _cmd(py, repo, "resumen_costos.py")}
        qc["costos-inicio"] = {"type": "exec", "command": _cmd(py, repo, "resumen_costos.py") + " --inicio"}
        for nombre, prov in (("hijos-claude", "anthropic"), ("hijos-copilot", "copilot")):
            qc[nombre] = {"type": "exec", "command": f'"{py}" "{repo}/instalar.py" --hijos {prov}'}
    return cfg


def hijos(cfg, proveedor):
    if proveedor not in HIJOS:
        raise ValueError(f"proveedor desconocido: {proveedor}")
    cfg = copy.deepcopy(cfg)
    cfg.setdefault("delegation", {}).update(HIJOS[proveedor])
    return cfg


def _respaldar(ruta, sello):
    if ruta.exists():
        shutil.copy2(ruta, ruta.with_name(f"{ruta.name}.antes-gibran-{sello}.bak"))


# Inspección HTTPS: las raíces pueden rotar y Python (certifi) no lee el almacén de Windows. Se agregan las
# raíces que Windows ya confía y certifi no trae. Regenerar con `instalar.py --certs`.
BUNDLE = Path.home() / ".hermes-ca-bundle.pem"            # SSL_CERT_FILE (Python/Hermes)
SOLO_CORPORATIVOS = Path.home() / ".hermes-ca-corporativo.pem"  # NODE_EXTRA_CA_CERTS (MCPs Node)


def _huellas(pem_texto):
    import re
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes
    import warnings
    huellas = set()
    warnings.filterwarnings("ignore", message="Parsed a serial number")
    for bloque in re.findall(r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----", pem_texto, re.S):
        try:
            huellas.add(x509.load_pem_x509_certificate(bloque.encode()).fingerprint(hashes.SHA256()))
        except ValueError:
            continue
    return huellas


def construir_bundle(base_pem, ders):
    """Devuelve (bundle = base + raíces de Windows que faltan, solo esas raíces)."""
    import warnings
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    vistos, extras = _huellas(base_pem), []
    for der in ders:
        try:
            with warnings.catch_warnings():  # Windows trae raíces viejas con seriales no estándar
                warnings.simplefilter("ignore")
                c = x509.load_der_x509_certificate(der)
        except ValueError:
            continue
        huella = c.fingerprint(hashes.SHA256())
        if huella in vistos:
            continue
        vistos.add(huella)
        extras.append(c.public_bytes(serialization.Encoding.PEM).decode())
    extra = "".join(extras)
    return base_pem.rstrip() + "\n" + extra, extra


def regenerar_certs():
    import ssl
    import certifi
    ders = [der for almacen in ("ROOT",)
            for der, codificacion, _ in ssl.enum_certificates(almacen) if codificacion == "x509_asn"]
    bundle, extra = construir_bundle(Path(certifi.where()).read_text(encoding="ascii"), ders)
    if not extra:
        print("[aviso] Windows no tiene raíces que falten en certifi; nada que hacer")
        return
    sello = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    for ruta, texto in ((BUNDLE, bundle), (SOLO_CORPORATIVOS, extra)):
        _respaldar(ruta, sello)
        ruta.write_text(texto, encoding="ascii")
    print(f"[ok] {extra.count('BEGIN CERTIFICATE')} raíces de Windows agregadas en {BUNDLE} y {SOLO_CORPORATIVOS}")


def main(argv):
    if "--certs" in argv:
        regenerar_certs()
        return
    if "--hijos" in argv:
        proveedor = argv[argv.index("--hijos") + 1]
        ruta = PERFILES["default"] / "config.yaml"
        cfg = hijos(yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}, proveedor)
        ruta.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")
        print(f"Hijos de delegate_task: {HIJOS[proveedor]['provider']} / {HIJOS[proveedor]['model']}"
              " (aplica desde la próxima sesión)")
        return
    repo = Path(__file__).resolve().parent.as_posix()
    py = Path(sys.executable).as_posix()
    solo_mostrar = "--solo-mostrar" in argv
    sello = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    for perfil, home in PERFILES.items():
        ruta = home / "config.yaml"
        if not ruta.exists():
            print(f"[omitido] {perfil}: no existe {ruta} (crea el perfil primero)")
            continue
        cfg = yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}
        nuevo = configurar(cfg, perfil, repo, py)
        texto = yaml.safe_dump(nuevo, sort_keys=False, allow_unicode=True)
        soul = Path(repo) / "souls" / f"{perfil}.md"
        if solo_mostrar:
            print(f"--- {perfil}: {ruta}\n{texto}")
            continue
        _respaldar(ruta, sello)
        ruta.write_text(texto, encoding="utf-8")
        if soul.exists():
            _respaldar(home / "SOUL.md", sello)
            shutil.copy2(soul, home / "SOUL.md")
        else:
            print(f"[aviso] {perfil}: falta {soul}, SOUL sin cambios")
        print(f"[ok] {perfil}")


if __name__ == "__main__":
    main(sys.argv[1:])
