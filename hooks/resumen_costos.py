"""Quick commands /costos (tokens y costo por perfil y modelo) y /costos-inicio (marca desde dónde contar)."""
import datetime
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

from registro_costos import destino

PRECIOS = Path(__file__).with_name("precios.json")
VENTANAS = {"seven_day": "semanal", "five_hour": "5 h"}


def uso_suscripcion():
    """% usado de los límites de la suscripción de Claude ({"seven_day": {...}, ...}) o None.

    Es el endpoint que usa /usage de Claude Code (no documentado): si cambia o falla, /costos
    solo muestra pesos. La credencial es la de Claude Code, la misma que usa Hermes (claude_code).
    """
    try:
        import urllib.request
        carpeta = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
        token = json.loads((carpeta / ".credentials.json").read_text(encoding="utf-8"))["claudeAiOauth"]["accessToken"]
        req = urllib.request.Request("https://api.anthropic.com/api/oauth/usage", headers={
            "Authorization": f"Bearer {token}", "anthropic-beta": "oauth-2025-04-20"})
        d = json.load(urllib.request.urlopen(req, timeout=10))
        return {k: d[k] for k in VENTANAS if isinstance(d.get(k), dict)}
    except Exception:
        return None


def texto_uso(inicio, ahora):
    """'semanal 11% (+9 desde el inicio) · 5 h 5%'. El aumento solo cuenta si la ventana no se reinició."""
    partes = []
    for k, nombre in VENTANAS.items():
        a = ahora.get(k) or {}
        if a.get("utilization") is None:
            continue
        t = f"{nombre} {a['utilization']:.0f}%"
        i = (inicio or {}).get(k) or {}
        if i.get("utilization") is not None:
            t += (f" (+{a['utilization'] - i['utilization']:.0f} desde el inicio)"
                  if i.get("resets_at") == a.get("resets_at") else " (la ventana se reinició desde el inicio)")
        partes.append(t)
    return " · ".join(partes)


def dolares(modelo, proveedor, perfil, u, precios):
    """USD de una llamada según precios.json; None si el modelo no tiene precio.

    Copilot escribe "claude-haiku-5.5" y Anthropic "claude-haiku-5-5": se comparan sin puntos.
    """
    p = (precios.get("modelos") or {}).get(str(modelo).replace(".", "-"))
    if not p:
        return None
    lee = u.get("cache_read_tokens") or 0
    escribe = u.get("cache_write_tokens") or 0
    prompt = u.get("prompt_tokens") or 0
    fresca = max(prompt - lee - escribe, 0)
    salida = u.get("completion_tokens") or u.get("output_tokens") or 0
    # Caché de 1 hora en Anthropic: escribir cuesta 2x la entrada (la de 5 min, 1.25x).
    tarifa_escribe = 2 * p["entrada"] if proveedor == "anthropic" and perfil in precios.get("ttl_1h", []) \
        else p["cache_escribe"]
    usd = (fresca * p["entrada"] + lee * p["cache_lee"] + escribe * tarifa_escribe + salida * p["salida"]) / 1e6
    return usd * p.get("factor_largo", 1) if prompt > p.get("umbral_largo", float("inf")) else usd


def resumir(lineas, desde=None, precios=None):
    """Filas (perfil, modelo, proveedor, llamadas, entrada, de caché, a caché, salida, USD o None).

    "de caché" se lee barato; "a caché" se escribe con recargo: es la que más conviene bajar.
    """
    precios = precios or {}
    acum = defaultdict(lambda: [0, 0, 0, 0, 0, None])
    for l in lineas:
        if desde and (l.get("ts") or "") < desde:
            continue
        u = l.get("usage") or {}
        a = acum[(l.get("perfil"), l.get("model"), l.get("provider"))]
        a[0] += 1
        a[1] += u.get("prompt_tokens") or 0
        a[2] += u.get("cache_read_tokens") or 0
        a[3] += u.get("cache_write_tokens") or 0
        a[4] += u.get("completion_tokens") or u.get("output_tokens") or 0
        usd = dolares(l.get("model"), l.get("provider"), l.get("perfil"), u, precios)
        if usd is not None:
            a[5] = (a[5] or 0) + usd
    return [k + tuple(v) for k, v in sorted(acum.items(), key=lambda kv: -kv[1][1])]


def main(argv):
    ruta = destino()
    marca = ruta.with_name("costos.inicio")
    marca_uso = ruta.with_name("costos.inicio.uso.json")
    if "--inicio" in argv:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        marca.write_text(datetime.datetime.now().isoformat(timespec="seconds"), encoding="utf-8")
        marca_uso.write_text(json.dumps(uso_suscripcion()), encoding="utf-8")
        print("Costos: contando desde ahora. /costos muestra solo lo gastado desde esta marca.")
        return
    if not ruta.exists():
        print(f"Sin registros en {ruta}")
        return
    lineas = []
    for texto in ruta.read_text(encoding="utf-8").splitlines():
        try:
            lineas.append(json.loads(texto))
        except ValueError:
            continue
    precios = json.loads(PRECIOS.read_text(encoding="utf-8"))
    tc = precios["tipo_cambio_mxn"]
    desde = marca.read_text(encoding="utf-8").strip() if marca.exists() else None
    print(f"Desde {desde} (/costos-inicio para reiniciar)" if desde else "Histórico completo")
    print(f"{'perfil':<14}{'modelo':<20}{'llamadas':>9}{'entrada':>11}{'de caché':>10}{'a caché':>9}"
          f"{'salida':>9}{'MXN':>10}{'AIC':>9}")
    total = {"anthropic": 0.0, "copilot": 0.0}
    sin_precio = set()
    for perfil, modelo, prov, n, ent, lee, escribe, sal, usd in resumir(lineas, desde, precios):
        pct = lambda x: f"{x * 100 // ent}%" if ent else "-"
        if usd is None:
            sin_precio.add(str(modelo))
            mxn = aic = "?"
        else:
            total[prov if prov == "copilot" else "anthropic"] += usd
            mxn = f"{usd * tc:,.2f}"
            aic = f"{usd * 100:,.0f}" if prov == "copilot" else "-"
        print(f"{str(perfil):<14}{str(modelo):<20}{n:>9}{ent:>11}{pct(lee):>10}{pct(escribe):>9}{sal:>9}"
              f"{mxn:>10}{aic:>9}")
    print(f"\nClaude (suscripción, costo fijo): equivale a ${total['anthropic'] * tc:,.2f} MXN si fuera API.")
    uso = uso_suscripcion()
    if uso:
        inicio = json.loads(marca_uso.read_text(encoding="utf-8")) if desde and marca_uso.exists() else None
        print(f"Límite de la suscripción (toda la cuenta, no solo Hermes): {texto_uso(inicio, uso)}")
    if total["copilot"]:
        print(f"Copilot: {total['copilot'] * 100:,.0f} AIC (${total['copilot'] * tc:,.2f} MXN).")
    print(f"Tipo de cambio {tc} ({precios.get('tipo_cambio_fecha', '?')}); precios en hooks/precios.json.")
    if sin_precio:
        print(f"Sin precio (no suman): {', '.join(sorted(sin_precio))}. Agrégalos en precios.json.")


if __name__ == "__main__":
    main(sys.argv[1:])
