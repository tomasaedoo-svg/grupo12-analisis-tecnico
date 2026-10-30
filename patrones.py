"""Detección de patrones de velas. Responsable sugerido: Martín Moraga.

Solo se usan los patrones de la imagen que indicó el profesor (Patterns-2):
Morning Star, Evening Star, Bullish/Bearish Engulfing, Bullish/Bearish Harami,
Hammer, Inverse Hammer, Hanging Man, Dragonfly Doji, Gravestone Doji, Double Doji,
Three White Soldiers, Three Black Crows, Dark Cloud Cover, Piercing Line,
Rising/Falling Three Methods, Bullish/Bearish Marubozu.

Cada regla usa el cuerpo y las sombras de la vela, y para los patrones de
giro exige la tendencia previa correcta (por ejemplo, un Hammer solo cuenta
después de una caída). Los umbrales están arriba para poder ajustarlos.
"""
import pandas as pd

DOJI_MAX = 0.10        # cuerpo <= 10% del rango = doji
SOMBRA_LARGA = 2.0     # sombra >= 2 veces el cuerpo
SOMBRA_CORTA = 0.15    # sombra <= 15% del rango
MARUBOZU_MIN = 0.90    # cuerpo >= 90% del rango
CUERPO_LARGO = 1.2     # cuerpo >= 1,2 veces el cuerpo promedio de 20 velas
VELAS_PREVIAS = 5      # velas usadas para medir la tendencia previa


def _medidas(df):
    m = pd.DataFrame(index=df.index)
    m["o"], m["h"], m["l"], m["c"] = df["Apertura"], df["Maximo"], df["Minimo"], df["Cierre"]
    m["cuerpo"] = (m["c"] - m["o"]).abs()
    m["rango"] = (m["h"] - m["l"]).replace(0, 1e-9)
    m["sup"] = m["h"] - m[["o", "c"]].max(axis=1)
    m["inf"] = m[["o", "c"]].min(axis=1) - m["l"]
    m["alcista"] = m["c"] > m["o"]
    m["bajista"] = m["c"] < m["o"]
    m["cuerpo_prom"] = m["cuerpo"].rolling(20, min_periods=5).mean()
    return m


def _previa(m, i):
    """Tendencia de corto plazo antes de la vela i: 'baja', 'sube' o None."""
    if i - VELAS_PREVIAS - 1 < 0:
        return None
    cambio = m["c"].iat[i - 1] - m["c"].iat[i - VELAS_PREVIAS - 1]
    umbral = m["cuerpo_prom"].iat[i] or 0
    if cambio < -umbral:
        return "baja"
    if cambio > umbral:
        return "sube"
    return None


def detectar(df):
    """Devuelve una lista de dicts {i, fecha, patron, sesgo, velas, explicacion}."""
    m = _medidas(df)
    hallazgos = []

    def agregar(i, patron, sesgo, velas, explicacion):
        hallazgos.append({
            "i": i, "fecha": df["Fecha"].iat[i], "patron": patron, "sesgo": sesgo,
            "velas": velas, "explicacion": explicacion,
            "precio": float(m["l"].iat[i] if sesgo == "alcista" else m["h"].iat[i]),
        })

    for i in range(len(m)):
        v = m.iloc[i]
        largo = lambda k: m["cuerpo"].iat[k] >= CUERPO_LARGO * (m["cuerpo_prom"].iat[k] or 0)
        previa = _previa(m, i)
        es_doji = v.cuerpo <= DOJI_MAX * v.rango

        # ---- Una vela ----
        if es_doji:
            if v.sup <= SOMBRA_CORTA * v.rango and v.inf >= 0.6 * v.rango:
                agregar(i, "Dragonfly Doji", "alcista" if previa == "baja" else "neutral", 1,
                        "Doji con sombra inferior larga y sin sombra superior: los compradores rechazaron precios bajos.")
            elif v.inf <= SOMBRA_CORTA * v.rango and v.sup >= 0.6 * v.rango:
                agregar(i, "Gravestone Doji", "bajista" if previa == "sube" else "neutral", 1,
                        "Doji con sombra superior larga y sin sombra inferior: los vendedores rechazaron precios altos.")
            elif i >= 1 and m["cuerpo"].iat[i - 1] <= DOJI_MAX * m["rango"].iat[i - 1]:
                agregar(i, "Double Doji", "neutral", 2,
                        "Dos doji seguidos: indecisión; suele anticipar un movimiento fuerte, sin dirección definida.")
        else:
            cuerpo_chico = v.cuerpo <= 0.35 * v.rango
            if cuerpo_chico and v.inf >= SOMBRA_LARGA * v.cuerpo and v.sup <= SOMBRA_CORTA * v.rango:
                if previa == "baja":
                    agregar(i, "Hammer", "alcista", 1,
                            "Cuerpo pequeño arriba y sombra inferior larga tras una caída: posible rechazo de la baja.")
                elif previa == "sube":
                    agregar(i, "Hanging Man", "bajista", 1,
                            "Misma forma del Hammer pero tras una subida: advierte presión vendedora.")
            if cuerpo_chico and v.sup >= SOMBRA_LARGA * v.cuerpo and v.inf <= SOMBRA_CORTA * v.rango and previa == "baja":
                agregar(i, "Inverse Hammer", "alcista", 1,
                        "Cuerpo pequeño abajo y sombra superior larga tras una caída: compradores intentan subir.")
            if v.cuerpo >= MARUBOZU_MIN * v.rango and largo(i):
                if v.alcista:
                    agregar(i, "Bullish Marubozu", "alcista", 1, "Vela alcista larga casi sin sombras: dominio comprador.")
                else:
                    agregar(i, "Bearish Marubozu", "bajista", 1, "Vela bajista larga casi sin sombras: dominio vendedor.")

        # ---- Dos velas ----
        if i >= 1:
            a = m.iloc[i - 1]
            if a.bajista and v.alcista and v.o <= a.c and v.c >= a.o and v.cuerpo > a.cuerpo and previa == "baja":
                agregar(i, "Bullish Engulfing", "alcista", 2,
                        "Vela alcista cuyo cuerpo envuelve por completo al cuerpo bajista anterior, tras una caída.")
            if a.alcista and v.bajista and v.o >= a.c and v.c <= a.o and v.cuerpo > a.cuerpo and previa == "sube":
                agregar(i, "Bearish Engulfing", "bajista", 2,
                        "Vela bajista cuyo cuerpo envuelve por completo al cuerpo alcista anterior, tras una subida.")
            dentro = max(v.o, v.c) <= max(a.o, a.c) and min(v.o, v.c) >= min(a.o, a.c) and v.cuerpo < 0.6 * a.cuerpo
            if dentro and largo(i - 1):
                if a.bajista and v.alcista and previa == "baja":
                    agregar(i, "Bullish Harami", "alcista", 2,
                            "Vela alcista pequeña dentro del cuerpo de una bajista larga: la caída pierde fuerza.")
                if a.alcista and v.bajista and previa == "sube":
                    agregar(i, "Bearish Harami", "bajista", 2,
                            "Vela bajista pequeña dentro del cuerpo de una alcista larga: la subida pierde fuerza.")
            medio = (a.o + a.c) / 2
            if a.bajista and largo(i - 1) and v.alcista and v.o < a.c and medio < v.c < a.o and previa == "baja":
                agregar(i, "Piercing Line", "alcista", 2,
                        "Abre bajo el cierre anterior y cierra sobre la mitad del cuerpo bajista previo.")
            if a.alcista and largo(i - 1) and v.bajista and v.o > a.c and a.o < v.c < medio and previa == "sube":
                agregar(i, "Dark Cloud Cover", "bajista", 2,
                        "Abre sobre el cierre anterior y cierra bajo la mitad del cuerpo alcista previo.")

        # ---- Tres velas ----
        if i >= 2:
            a, b = m.iloc[i - 2], m.iloc[i - 1]
            previa3 = _previa(m, i - 2)
            estrella = b.cuerpo <= 0.3 * a.cuerpo
            if a.bajista and largo(i - 2) and estrella and v.alcista and v.c > (a.o + a.c) / 2 and previa3 == "baja":
                agregar(i, "Morning Star", "alcista", 3,
                        "Bajista larga, vela pequeña de indecisión y alcista que cierra sobre la mitad de la primera.")
            if a.alcista and largo(i - 2) and estrella and v.bajista and v.c < (a.o + a.c) / 2 and previa3 == "sube":
                agregar(i, "Evening Star", "bajista", 3,
                        "Alcista larga, vela pequeña de indecisión y bajista que cierra bajo la mitad de la primera.")
            tres = [m.iloc[k] for k in (i - 2, i - 1, i)]
            if all(x.alcista and x.cuerpo >= 0.5 * x.rango for x in tres) and tres[0].c < tres[1].c < tres[2].c \
                    and all(tres[k - 1].o <= tres[k].o <= tres[k - 1].c for k in (1, 2)):
                agregar(i, "Three White Soldiers", "alcista", 3, "Tres velas alcistas firmes, cada una cerrando más arriba.")
            if all(x.bajista and x.cuerpo >= 0.5 * x.rango for x in tres) and tres[0].c > tres[1].c > tres[2].c \
                    and all(tres[k - 1].c <= tres[k].o <= tres[k - 1].o for k in (1, 2)):
                agregar(i, "Three Black Crows", "bajista", 3, "Tres velas bajistas firmes, cada una cerrando más abajo.")

        # ---- Cinco velas (continuación) ----
        if i >= 4:
            p, medias, u = m.iloc[i - 4], [m.iloc[k] for k in (i - 3, i - 2, i - 1)], v
            chicas = all(x.cuerpo < 0.5 * p.cuerpo for x in medias)
            if p.alcista and largo(i - 4) and chicas and all(x.h <= p.h and x.l >= p.l for x in medias) \
                    and u.alcista and u.c > p.c:
                agregar(i, "Rising Three Methods", "alcista", 5,
                        "Alcista larga, tres velas pequeñas que no rompen su rango y nueva alcista que cierra más arriba: continuación.")
            if p.bajista and largo(i - 4) and chicas and all(x.h <= p.h and x.l >= p.l for x in medias) \
                    and u.bajista and u.c < p.c:
                agregar(i, "Falling Three Methods", "bajista", 5,
                        "Bajista larga, tres velas pequeñas que no rompen su rango y nueva bajista que cierra más abajo: continuación.")
    return hallazgos


def recientes(hallazgos, df, ultimas=20):
    """Solo los patrones de las últimas `ultimas` velas, que son los relevantes para el diagnóstico."""
    limite = len(df) - ultimas
    return [h for h in hallazgos if h["i"] >= limite]


def ubicar(hallazgos, df, soportes, resistencias, holgura):
    """Agrega a cada patrón dónde ocurrió: en un soporte, en una resistencia o
    en ninguna zona. Un patrón de giro en una zona relevante pesa más.
    `holgura` es cuánto puede alejarse la vela de la zona (en precio)."""
    for h in hallazgos:
        bajo, alto = float(df["Minimo"].iat[h["i"]]), float(df["Maximo"].iat[h["i"]])
        h["ubicacion"] = "fuera de zonas clave"
        for zonas, nombre in [(soportes, "soporte"), (resistencias, "resistencia")]:
            for z in zonas:
                if bajo <= z["alto"] + holgura and alto >= z["bajo"] - holgura:
                    h["ubicacion"] = f'en {nombre} {z["nivel"]:,.2f}'
                    break
            if h["ubicacion"] != "fuera de zonas clave":
                break
    return hallazgos
