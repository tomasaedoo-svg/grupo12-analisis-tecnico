"""Estructura de mercado: máximos/mínimos (pivotes), tendencia, línea de tendencia,
soportes y resistencias. Responsable sugerido: Tomás.

Todo se calcula con reglas explícitas, para poder explicar en la defensa
de dónde sale cada resultado.
"""
import pandas as pd


def atr(df, n=14):
    """Average True Range: rango promedio de las velas, sirve como medida de volatilidad."""
    cierre_ant = df["Cierre"].shift(1)
    rango = pd.concat(
        [df["Maximo"] - df["Minimo"], (df["Maximo"] - cierre_ant).abs(), (df["Minimo"] - cierre_ant).abs()],
        axis=1,
    ).max(axis=1)
    return rango.rolling(n, min_periods=1).mean()


def pivotes(df, ventana=5):
    """Un máximo relevante es una vela cuyo Máximo es el mayor de las `ventana` velas
    a cada lado (igual para el mínimo). Devuelve una lista de dicts ordenada por fecha:
    {i, fecha, tipo ('max'|'min'), precio, etiqueta (HH/LH/HL/LL)}.
    """
    puntos = []
    n = len(df)
    for i in range(ventana, n - ventana):
        tramo = df.iloc[i - ventana : i + ventana + 1]
        if df["Maximo"].iat[i] == tramo["Maximo"].max():
            puntos.append({"i": i, "fecha": df["Fecha"].iat[i], "tipo": "max", "precio": float(df["Maximo"].iat[i])})
        if df["Minimo"].iat[i] == tramo["Minimo"].min():
            puntos.append({"i": i, "fecha": df["Fecha"].iat[i], "tipo": "min", "precio": float(df["Minimo"].iat[i])})

    puntos = _alternar(puntos)

    # Etiquetas: cada máximo se compara con el máximo anterior, y cada mínimo con el mínimo anterior
    ultimo = {"max": None, "min": None}
    for p in puntos:
        previo = ultimo[p["tipo"]]
        if previo is None:
            p["etiqueta"] = "H" if p["tipo"] == "max" else "L"
        elif p["tipo"] == "max":
            p["etiqueta"] = "HH" if p["precio"] > previo else "LH"
        else:
            p["etiqueta"] = "HL" if p["precio"] > previo else "LL"
        ultimo[p["tipo"]] = p["precio"]
    return puntos


def _alternar(puntos):
    """Si salen dos máximos seguidos sin un mínimo entre ellos, se queda el más alto
    (y al revés con los mínimos). Así la estructura queda máximo-mínimo-máximo..."""
    limpios = []
    for p in sorted(puntos, key=lambda x: (x["i"], x["tipo"] == "min")):
        if limpios and limpios[-1]["tipo"] == p["tipo"]:
            mejor_nuevo = p["precio"] > limpios[-1]["precio"] if p["tipo"] == "max" else p["precio"] < limpios[-1]["precio"]
            if mejor_nuevo:
                limpios[-1] = p
        else:
            limpios.append(p)
    return limpios


def tendencia(puntos, df):
    """Tendencia según la estructura de los dos últimos máximos y mínimos.

    Alcista: máximo y mínimo crecientes (HH + HL).
    Bajista: máximo y mínimo decrecientes (LH + LL).
    Lateral: señales mezcladas o sin pivotes suficientes.
    Devuelve dict con tendencia, explicación y apoyo de medias móviles.
    """
    maximos = [p for p in puntos if p["tipo"] == "max"]
    minimos = [p for p in puntos if p["tipo"] == "min"]
    sma20 = df["Cierre"].rolling(20).mean().iat[-1]
    sma50 = df["Cierre"].rolling(50).mean().iat[-1]
    cierre = df["Cierre"].iat[-1]

    if len(maximos) < 2 or len(minimos) < 2:
        return {
            "tendencia": "Lateral",
            "estructura": "Sin máximos y mínimos suficientes para definir estructura",
            "medias": _texto_medias(cierre, sma20, sma50),
        }

    sube_max = maximos[-1]["precio"] > maximos[-2]["precio"]
    sube_min = minimos[-1]["precio"] > minimos[-2]["precio"]
    if sube_max and sube_min:
        t, e = "Alcista", "Máximos y mínimos crecientes (HH y HL)"
    elif not sube_max and not sube_min:
        t, e = "Bajista", "Máximos y mínimos decrecientes (LH y LL)"
    else:
        t = "Lateral"
        e = "Estructura mixta: " + ("máximo creciente" if sube_max else "máximo decreciente") + " y " + (
            "mínimo creciente" if sube_min else "mínimo decreciente"
        )
    return {"tendencia": t, "estructura": e, "medias": _texto_medias(cierre, sma20, sma50)}


def _texto_medias(cierre, sma20, sma50):
    if pd.isna(sma50):
        return "Datos insuficientes para la media de 50."
    pos = "sobre" if cierre > sma50 else "bajo"
    cruce = "sobre" if sma20 > sma50 else "bajo"
    return f"El precio está {pos} la media de 50 y la media de 20 está {cruce} la de 50."


def linea_tendencia(puntos, df, tend):
    """Línea que une los dos últimos mínimos (tendencia alcista) o máximos (bajista),
    proyectada hasta la última vela. Devuelve dict con fechas y precios, o None."""
    tipo = {"Alcista": "min", "Bajista": "max"}.get(tend)
    if tipo is None:
        return None
    sel = [p for p in puntos if p["tipo"] == tipo][-2:]
    if len(sel) < 2:
        return None
    p1, p2 = sel
    pendiente = (p2["precio"] - p1["precio"]) / (p2["i"] - p1["i"])
    i_fin = len(df) - 1
    return {
        "x": [p1["fecha"], df["Fecha"].iat[i_fin]],
        "y": [p1["precio"], p1["precio"] + pendiente * (i_fin - p1["i"])],
        "tipo": tipo,
    }


def soportes_resistencias(df, puntos, tolerancia_atr=0.6, max_niveles=3):
    """Agrupa los precios de los pivotes que están cerca entre sí (a menos de
    `tolerancia_atr` veces el ATR). Cada grupo es una zona; se cuentan los toques.
    Devuelve (soportes, resistencias): listas de dicts {bajo, alto, nivel, toques},
    ordenadas de la más cercana al precio actual a la más lejana.
    """
    if not puntos:
        return [], []
    tol = float(atr(df).iat[-1]) * tolerancia_atr
    precios = sorted(p["precio"] for p in puntos)

    grupos = [[precios[0]]]
    for precio in precios[1:]:
        if precio - grupos[-1][-1] <= tol:
            grupos[-1].append(precio)
        else:
            grupos.append([precio])

    zonas = [
        {"bajo": min(g), "alto": max(g), "nivel": sum(g) / len(g), "toques": len(g)}
        for g in grupos
    ]
    # Zonas con un solo toque se ensanchan un poco para que se vean
    for z in zonas:
        if z["alto"] - z["bajo"] < tol * 0.5:
            z["bajo"], z["alto"] = z["nivel"] - tol * 0.25, z["nivel"] + tol * 0.25

    cierre = float(df["Cierre"].iat[-1])
    # Se priorizan zonas con 2+ toques; si no hay, se usa la más cercana
    def elegir(lista):
        fuertes = [z for z in lista if z["toques"] >= 2]
        return (fuertes or lista)[:max_niveles]

    soportes = elegir(sorted([z for z in zonas if z["nivel"] < cierre], key=lambda z: cierre - z["nivel"]))
    resistencias = elegir(sorted([z for z in zonas if z["nivel"] > cierre], key=lambda z: z["nivel"] - cierre))
    return soportes, resistencias
