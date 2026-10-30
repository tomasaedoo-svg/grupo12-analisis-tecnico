"""Interpretación del análisis. Responsable sugerido: Martín Moraga.

1. `resumen()` junta en un diccionario todo lo que la app detectó (son los únicos
   datos que ve la IA, así no puede inventar información que no está en el gráfico).
2. `interpretar_con_ia()` le pide a la IA (Gemini de Google, o Claude si se
   configura esa clave) que redacte el diagnóstico con las restricciones del enunciado.
3. `interpretar_con_reglas()` es el respaldo si no hay clave de API o falla la conexión.
"""
import json
import os

MODELOS_GEMINI = ["gemini-flash-latest", "gemini-2.5-flash"]  # se prueba en orden
MODELO_CLAUDE = "claude-opus-5-5"

INSTRUCCIONES = """Eres un analista técnico bursátil que apoya a estudiantes de un magíster en finanzas.
Recibirás en JSON los resultados que una aplicación calculó a partir de datos OHLC.
Redacta en español un diagnóstico técnico breve con este formato:

TENDENCIA: ...
ESTRUCTURA: ...
SOPORTE: ... · RESISTENCIA: ...
PATRÓN: ...
DIAGNÓSTICO: un párrafo de 3 a 5 oraciones que relacione los elementos.
NIVEL DE CONFIANZA: alto, medio o bajo, con la razón.

Reglas obligatorias:
- Usa solo los datos del JSON. No inventes precios, fechas, noticias ni indicadores que no estén ahí.
- No presentes predicciones como certezas: usa "podría", "sugiere", "advierte".
- Justifica cada conclusión con la evidencia técnica del JSON (pivotes, toques de la zona, patrón y su ubicación).
- Si la evidencia es débil o contradictoria (por ejemplo, estructura lateral o un patrón contrario a la tendencia), dilo explícitamente.
- Considera la ubicación del patrón (campo "ubicacion"): un patrón bajista en una resistencia o uno alcista en un soporte pesa más; uno fuera de zonas clave pesa menos.
- No des recomendaciones de compra o venta."""


def resumen(df, puntos, tend, soportes, resistencias, patrones_recientes):
    """Diccionario con los hallazgos, en el formato que recibe la IA."""
    cierre = float(df["Cierre"].iat[-1])
    zona = lambda z: {"desde": round(z["bajo"], 2), "hasta": round(z["alto"], 2), "toques": z["toques"],
                      "distancia_pct": round((z["nivel"] / cierre - 1) * 100, 2)}
    return {
        "periodo": f'{df["Fecha"].iat[0]:%d-%m-%Y} a {df["Fecha"].iat[-1]:%d-%m-%Y}',
        "velas": len(df),
        "ultimo_cierre": round(cierre, 2),
        "variacion_periodo_pct": round((cierre / float(df["Cierre"].iat[0]) - 1) * 100, 2),
        "tendencia": tend["tendencia"],
        "estructura": tend["estructura"],
        "medias_moviles": tend["medias"],
        "ultimos_pivotes": [
            {"fecha": f'{p["fecha"]:%d-%m-%Y}', "tipo": p["etiqueta"], "precio": round(p["precio"], 2)}
            for p in puntos[-6:]
        ],
        "soportes": [zona(z) for z in soportes],
        "resistencias": [zona(z) for z in resistencias],
        "patrones_recientes": [
            {"fecha": f'{h["fecha"]:%d-%m-%Y}', "patron": h["patron"], "sesgo": h["sesgo"],
             "velas_atras": len(df) - 1 - h["i"], "ubicacion": h.get("ubicacion", "sin dato")}
            for h in patrones_recientes
        ],
    }


def _secreto(nombre):
    try:
        import streamlit as st
        if nombre in st.secrets:
            return st.secrets[nombre]
    except Exception:
        pass
    return os.environ.get(nombre)


def obtener_clave():
    """Busca la clave en los secretos de Streamlit o en variables de entorno.
    Devuelve (proveedor, clave) o (None, None). Gemini tiene prioridad."""
    if _secreto("GEMINI_API_KEY"):
        return "gemini", _secreto("GEMINI_API_KEY")
    if _secreto("ANTHROPIC_API_KEY"):
        return "claude", _secreto("ANTHROPIC_API_KEY")
    return None, None


def _mensaje(datos):
    return "Resultados del análisis:\n" + json.dumps(datos, ensure_ascii=False, indent=2)


def interpretar_con_ia(datos, proveedor, clave):
    """Pide el diagnóstico a la IA. Devuelve el texto, o lanza una excepción si falla."""
    if proveedor == "gemini":
        return _con_gemini(datos, clave)
    return _con_claude(datos, clave)


def _con_gemini(datos, clave):
    from google import genai
    from google.genai import types

    cliente = genai.Client(api_key=clave)
    config = types.GenerateContentConfig(system_instruction=INSTRUCCIONES)
    ultimo_error = None
    for modelo in MODELOS_GEMINI:
        try:
            respuesta = cliente.models.generate_content(model=modelo, contents=_mensaje(datos), config=config)
            if respuesta.text:
                return respuesta.text.strip()
        except Exception as e:  # si un modelo no está disponible se prueba el siguiente
            ultimo_error = e
    raise RuntimeError(f"Gemini no respondió ({ultimo_error})")


def _con_claude(datos, clave):
    import anthropic

    cliente = anthropic.Anthropic(api_key=clave)
    respuesta = cliente.beta.messages.create(
        model=MODELO_CLAUDE,
        max_tokens=4000,
        system=INSTRUCCIONES,
        output_config={"effort": "low"},
        # Si el modelo rechaza la consulta, la API la reintenta con otro modelo
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        messages=[{"role": "user", "content": _mensaje(datos)}],
    )
    if respuesta.stop_reason == "refusal":
        raise RuntimeError("La IA no respondió esta consulta.")
    return "".join(b.text for b in respuesta.content if b.type == "text").strip()


def interpretar_con_reglas(datos):
    """Diagnóstico armado con reglas fijas (respaldo sin IA)."""
    t = datos["tendencia"]
    sop = datos["soportes"][0] if datos["soportes"] else None
    res = datos["resistencias"][0] if datos["resistencias"] else None
    pats = datos["patrones_recientes"]
    ultimo = pats[-1] if pats else None

    lineas = [
        f"TENDENCIA: {t}",
        f"ESTRUCTURA: {datos['estructura']}",
        "SOPORTE: " + (f"{sop['desde']:,} a {sop['hasta']:,}" if sop else "no identificado")
        + " · RESISTENCIA: " + (f"{res['desde']:,} a {res['hasta']:,}" if res else "no identificada"),
        "PATRÓN: " + (f"{ultimo['patron']} ({ultimo['sesgo']}, hace {ultimo['velas_atras']} velas)" if ultimo else "sin patrones recientes"),
    ]

    texto = {
        "Alcista": "La estructura principal es alcista.",
        "Bajista": "La estructura principal es bajista.",
        "Lateral": "No hay una tendencia clara; el precio se mueve en una estructura lateral o mixta.",
    }[t]
    cerca_res = res and abs(res["distancia_pct"]) <= 3
    cerca_sop = sop and abs(sop["distancia_pct"]) <= 3
    if cerca_res:
        texto += f" El precio está a {abs(res['distancia_pct'])}% de una resistencia con {res['toques']} toques."
    if cerca_sop:
        texto += f" El precio está a {abs(sop['distancia_pct'])}% de un soporte con {sop['toques']} toques."
    if ultimo:
        contrario = (t == "Alcista" and ultimo["sesgo"] == "bajista") or (t == "Bajista" and ultimo["sesgo"] == "alcista")
        texto += f" Aparece un {ultimo['patron']} de sesgo {ultimo['sesgo']} ({ultimo['ubicacion']})"
        if contrario:
            texto += ", contrario a la tendencia, lo que podría advertir una corrección o pausa de corto plazo."
        elif t == "Lateral":
            texto += "; sin tendencia definida su lectura es menos confiable."
        else:
            texto += ", que es coherente con el movimiento actual."
    texto += " Esto no es una certeza: conviene esperar confirmación en las próximas velas."

    confianza = "media"
    if t == "Lateral" or not ultimo:
        confianza = "baja"
    elif (cerca_res and ultimo["sesgo"] == "bajista") or (cerca_sop and ultimo["sesgo"] == "alcista"):
        confianza = "alta"
    lineas += [f"DIAGNÓSTICO: {texto}", f"NIVEL DE CONFIANZA: {confianza} (calculado con reglas, sin IA)."]
    return "\n".join(lineas)
