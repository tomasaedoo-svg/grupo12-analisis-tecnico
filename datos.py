"""Carga y validación de archivos OHLC (CSV o Excel).

Acepta nombres de columnas en español o inglés (incluido el formato de Yahoo Finance)
y devuelve un DataFrame con columnas estándar:
Fecha, Apertura, Maximo, Minimo, Cierre, Volumen (opcional).
"""
import unicodedata

import pandas as pd

# Nombres aceptados para cada columna (se comparan sin tildes ni mayúsculas)
SINONIMOS = {
    "Fecha": ["fecha", "date", "datetime", "time", "dia"],
    "Apertura": ["apertura", "open", "abre", "precio apertura"],
    "Maximo": ["maximo", "high", "max", "alto"],
    "Minimo": ["minimo", "low", "min", "bajo"],
    "Cierre": ["cierre", "close", "price", "precio cierre", "ultimo"],
    "Volumen": ["volumen", "volume", "vol"],
}


def _normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return texto.strip().lower().replace("_", " ").replace(".", "")


def _a_numero(serie):
    """Convierte texto a número. Soporta formato chileno (1.234,56) y anglosajón (1,234.56)."""
    if pd.api.types.is_numeric_dtype(serie):
        return serie.astype(float)
    s = serie.astype(str).str.strip().str.replace("$", "", regex=False).str.replace(" ", "")
    con_coma_decimal = s.str.contains(r",\d{1,4}$", regex=True)
    s = s.where(~con_coma_decimal, s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    s = s.where(con_coma_decimal, s.str.replace(",", "", regex=False))
    return pd.to_numeric(s, errors="coerce")


def cargar_ohlc(archivo, nombre=None):
    """Lee un CSV o Excel y devuelve (df, avisos).

    archivo: ruta o archivo subido en Streamlit.
    Lanza ValueError con un mensaje claro si faltan columnas.
    """
    nombre = (nombre or getattr(archivo, "name", str(archivo))).lower()
    if nombre.endswith((".xlsx", ".xls")):
        crudo = pd.read_excel(archivo)
    else:
        # sep=None detecta solo si el separador es coma o punto y coma
        crudo = pd.read_csv(archivo, sep=None, engine="python")

    columnas = {}
    for col in crudo.columns:
        n = _normalizar(col)
        for estandar, opciones in SINONIMOS.items():
            if estandar not in columnas and n in opciones:
                columnas[estandar] = col
    # Si hay "Adj Close" y "Close", se usa "Close" (precio real del gráfico)
    faltan = [c for c in ["Fecha", "Apertura", "Maximo", "Minimo", "Cierre"] if c not in columnas]
    if faltan:
        raise ValueError(
            "Faltan columnas: " + ", ".join(faltan)
            + ". El archivo debe tener Fecha, Apertura, Máximo, Mínimo y Cierre."
        )

    df = pd.DataFrame({estandar: crudo[original] for estandar, original in columnas.items()})
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce", dayfirst=_parece_dia_primero(df["Fecha"]))
    for col in ["Apertura", "Maximo", "Minimo", "Cierre"] + (["Volumen"] if "Volumen" in df else []):
        df[col] = _a_numero(df[col])

    avisos = []
    n_inicial = len(df)
    df = df.dropna(subset=["Fecha", "Apertura", "Maximo", "Minimo", "Cierre"])
    if len(df) < n_inicial:
        avisos.append(f"Se descartaron {n_inicial - len(df)} filas con datos vacíos o inválidos.")
    df = df.sort_values("Fecha").drop_duplicates("Fecha").reset_index(drop=True)

    # Coherencia OHLC: el máximo debe ser el mayor y el mínimo el menor
    malas = (df["Maximo"] < df[["Apertura", "Cierre"]].max(axis=1)) | (
        df["Minimo"] > df[["Apertura", "Cierre"]].min(axis=1)
    )
    if malas.any():
        avisos.append(f"{int(malas.sum())} velas tenían máximo/mínimo incoherente y se corrigieron.")
        df["Maximo"] = df[["Maximo", "Apertura", "Cierre"]].max(axis=1)
        df["Minimo"] = df[["Minimo", "Apertura", "Cierre"]].min(axis=1)

    if len(df) < 30:
        avisos.append("Hay menos de 30 velas: el análisis será poco confiable.")
    return df, avisos


def _parece_dia_primero(serie):
    """Detecta fechas tipo 25/10/2026 (día primero), comunes en Chile."""
    muestra = serie.astype(str).head(50)
    return bool(muestra.str.match(r"^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}").any())
