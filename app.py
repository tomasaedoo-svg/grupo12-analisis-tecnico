"""App de Análisis Técnico con IA (Modalidad B: datos OHLC).
Grupo 12: Martín Tapia, Tomás Aedo, Martín Moraga.

Para correrla en el computador:  streamlit run app.py
La página y el gráfico son la parte sugerida para Martín Tapia.
"""
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import datos
import estructura
import interpretacion
import patrones

st.set_page_config(page_title="App Análisis Técnico + IA", layout="wide")
st.title("Análisis Técnico + IA")
st.caption("Detectar · Dibujar · Interpretar. Sube un archivo con Fecha, Apertura, Máximo, Mínimo y Cierre (Volumen opcional).")

with st.sidebar:
    st.header("Parámetros")
    archivo = st.file_uploader("Archivo CSV o Excel", type=["csv", "xlsx", "xls"])
    ventana = st.slider("Sensibilidad de máximos y mínimos (velas a cada lado)", 2, 15, 5,
                        help="Más alto = solo los pivotes más importantes.")
    ultimas = st.slider("Patrones: revisar las últimas N velas", 5, 60, 20)
    ver_todos = st.checkbox("Mostrar patrones de todo el periodo", value=False)
    usar_ia = st.checkbox("Interpretar con IA", value=True)

if archivo is None:
    st.info("Sube un archivo para empezar. Puedes descargar uno desde Yahoo Finance (pestaña Historical Data → Download).")
    st.stop()

try:
    df, avisos = datos.cargar_ohlc(archivo)
except ValueError as e:
    st.error(str(e))
    st.stop()
for a in avisos:
    st.warning(a)

# ---------- Detectar ----------
puntos = estructura.pivotes(df, ventana)
tend = estructura.tendencia(puntos, df)
linea = estructura.linea_tendencia(puntos, df, tend["tendencia"])
soportes, resistencias = estructura.soportes_resistencias(df, puntos)
todos = patrones.detectar(df)
recientes = patrones.recientes(todos, df, ultimas)
a_dibujar = todos if ver_todos else recientes

# ---------- Dibujar ----------
tiene_vol = "Volumen" in df and df["Volumen"].fillna(0).sum() > 0
fig = make_subplots(rows=2 if tiene_vol else 1, cols=1, shared_xaxes=True,
                    row_heights=[0.8, 0.2] if tiene_vol else [1], vertical_spacing=0.03)
fig.add_trace(go.Candlestick(x=df["Fecha"], open=df["Apertura"], high=df["Maximo"], low=df["Minimo"],
                             close=df["Cierre"], name="Precio",
                             increasing_line_color="#26a69a", decreasing_line_color="#ef5350"), row=1, col=1)
for n, color in [(20, "#f9a825"), (50, "#7e57c2")]:
    fig.add_trace(go.Scatter(x=df["Fecha"], y=df["Cierre"].rolling(n).mean(), name=f"Media {n}",
                             line=dict(color=color, width=1.2)), row=1, col=1)

# Zonas de soporte y resistencia
for zonas, color, nombre in [(soportes, "rgba(38,166,154,0.18)", "Soporte"), (resistencias, "rgba(239,83,80,0.18)", "Resistencia")]:
    for z in zonas:
        fig.add_hrect(y0=z["bajo"], y1=z["alto"], fillcolor=color, line_width=0, row=1, col=1)
        fig.add_annotation(x=df["Fecha"].iat[0], y=z["nivel"], text=f'{nombre} {z["nivel"]:,.2f} ({z["toques"]} toques)',
                           showarrow=False, xanchor="left", bgcolor="rgba(255,255,255,0.7)", font=dict(size=11), row=1, col=1)

# Pivotes con su etiqueta
for tipo, pos, color in [("max", "top center", "#c62828"), ("min", "bottom center", "#2e7d32")]:
    sel = [p for p in puntos if p["tipo"] == tipo]
    fig.add_trace(go.Scatter(x=[p["fecha"] for p in sel], y=[p["precio"] for p in sel], mode="markers+text",
                             text=[p["etiqueta"] for p in sel], textposition=pos, name="Máximos" if tipo == "max" else "Mínimos",
                             marker=dict(color=color, size=6), textfont=dict(color=color, size=11)), row=1, col=1)

# Línea de tendencia
if linea:
    fig.add_trace(go.Scatter(x=linea["x"], y=linea["y"], mode="lines", name=f'Línea de tendencia {tend["tendencia"].lower()}',
                             line=dict(color="#1565c0", width=2, dash="dash")), row=1, col=1)

# Patrones de velas: un triángulo por vela (pasando el mouse se ve el nombre)
# y el nombre escrito solo en las últimas velas con patrón, para que no se tapen
COLORES = {"alcista": "#2e7d32", "bajista": "#c62828", "neutral": "#616161"}
por_vela = {}
for h in a_dibujar:
    por_vela.setdefault(h["i"], []).append(h)
for sesgo, simbolo in [("alcista", "triangle-up"), ("bajista", "triangle-down"), ("neutral", "circle")]:
    sel = [hs for hs in por_vela.values() if hs[-1]["sesgo"] == sesgo]
    if not sel:
        continue
    fig.add_trace(go.Scatter(
        x=[hs[0]["fecha"] for hs in sel],
        y=[df["Minimo"].iat[hs[0]["i"]] * 0.99 if sesgo == "alcista" else df["Maximo"].iat[hs[0]["i"]] * 1.01 for hs in sel],
        mode="markers", name=f"Patrón {sesgo}", marker=dict(symbol=simbolo, size=11, color=COLORES[sesgo]),
        hovertext=[" + ".join(h["patron"] for h in hs) for hs in sel], hoverinfo="text+x"), row=1, col=1)
for k, i in enumerate(sorted(por_vela)[-4:]):
    hs = por_vela[i]
    sesgo = hs[-1]["sesgo"]
    abajo = sesgo == "alcista"
    y = df["Minimo"].iat[i] if abajo else df["Maximo"].iat[i]
    fig.add_annotation(x=hs[0]["fecha"], y=y, text=" + ".join(h["patron"] for h in hs), showarrow=True, arrowhead=0,
                       ax=0, ay=(45 + 28 * k) * (1 if abajo else -1), bgcolor="rgba(255,255,255,0.85)",
                       font=dict(size=11, color=COLORES[sesgo]), arrowcolor=COLORES[sesgo], row=1, col=1)

if tiene_vol:
    fig.add_trace(go.Bar(x=df["Fecha"], y=df["Volumen"], name="Volumen", marker_color="#90a4ae"), row=2, col=1)
fig.update_layout(height=700, xaxis_rangeslider_visible=False, legend=dict(orientation="h", y=1.05),
                  margin=dict(l=10, r=10, t=30, b=10))
st.plotly_chart(fig, width="stretch")

# ---------- Interpretar ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Tendencia", tend["tendencia"])
c2.metric("Último cierre", f'{df["Cierre"].iat[-1]:,.2f}')
c3.metric("Soporte cercano", f'{soportes[0]["nivel"]:,.2f}' if soportes else "—")
c4.metric("Resistencia cercana", f'{resistencias[0]["nivel"]:,.2f}' if resistencias else "—")
st.write(f'**Estructura:** {tend["estructura"]}. {tend["medias"]}')

resumen = interpretacion.resumen(df, puntos, tend, soportes, resistencias, recientes)
st.subheader("Diagnóstico técnico")
proveedor, clave = interpretacion.obtener_clave()
texto, fuente = None, "reglas"
if usar_ia and clave:
    with st.spinner("La IA está redactando el diagnóstico..."):
        try:
            texto = interpretacion.interpretar_con_ia(resumen, proveedor, clave)
            fuente = "IA (Gemini de Google)" if proveedor == "gemini" else "IA (Claude de Anthropic)"
        except Exception as e:
            st.warning(f"No se pudo usar la IA ({e}). Se muestra el diagnóstico por reglas.")
elif usar_ia:
    st.info("No hay clave de API configurada: se muestra el diagnóstico por reglas.")
if texto is None:
    texto = interpretacion.interpretar_con_reglas(resumen)
# La IA responde con negritas (**) y saltos de línea: se muestra como markdown
st.markdown(texto.replace("$", "\\$").replace("\n", "  \n"))
st.caption(f"Fuente del diagnóstico: {fuente}. No es una recomendación de inversión.")

with st.expander("Patrones detectados en las últimas velas"):
    if recientes:
        for h in reversed(recientes):
            st.write(f'**{h["fecha"]:%d-%m-%Y} · {h["patron"]}** ({h["sesgo"]}): {h["explicacion"]}')
    else:
        st.write("No hay patrones de la lista en las últimas velas.")
with st.expander("Datos que recibe la IA (evidencia)"):
    st.json(resumen)
