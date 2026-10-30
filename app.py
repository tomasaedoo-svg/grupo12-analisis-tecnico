"""App de Análisis Técnico con IA (Modalidad B: datos OHLC).
Grupo 12: Martín Tapia, Tomás Aedo, Martín Moraga.

Para correrla en el computador:  streamlit run app.py
La página y el gráfico son la parte sugerida para Martín Tapia.
"""
import base64
import html
import json
import re
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import datos
import estructura
import interpretacion
import patrones

LOGO = Path(__file__).parent / "logo.png"  # logo de la universidad (opcional)

st.set_page_config(page_title="Análisis Técnico + IA · Grupo 12", page_icon="📈", layout="wide")
st.markdown("""<style>
.encabezado {display:flex; align-items:center; gap:20px; padding:18px 24px; border-radius:12px;
  background:linear-gradient(90deg,#063952 0%,#0E5A7E 100%); color:#fff; margin-bottom:18px;}
.encabezado img {height:72px; background:#fff; border-radius:10px; padding:8px 12px;}
.encabezado h1 {color:#fff; font-size:1.9rem; margin:0; padding:0;}
.encabezado p {color:#DCE6F2; margin:4px 0 0 0; font-size:0.95rem;}
.pie {color:#8A94A6; font-size:0.8rem; text-align:center; margin-top:32px;}
.grilla {display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:12px;}
.tarjeta {border:1px solid #D5DBE3; border-radius:10px; padding:8px 10px; display:flex; flex-direction:column;}
.tarjeta span {color:#5B6676; font-size:0.75rem;}
.tarjeta b {font-size:1.15rem; color:#1D2733;}
.tarjeta small {color:#5B6676; font-size:0.7rem;}
@media (max-width: 640px) {
  .encabezado {flex-direction:column; align-items:flex-start; gap:10px; padding:14px 16px;}
  .encabezado img {display:none;}  /* el logo ya aparece arriba en la barra */
  .block-container {padding-top:3.5rem; padding-left:0.8rem; padding-right:0.8rem;}
  .encabezado h1 {font-size:1.35rem;}
  .encabezado p {font-size:0.8rem;}
  .encabezado .detalle {display:none;}
}
</style>""", unsafe_allow_html=True)

logo_html = ""
if LOGO.exists():
    logo_html = f'<img src="data:image/png;base64,{base64.b64encode(LOGO.read_bytes()).decode()}" alt="Logo">'
    st.logo(str(LOGO))
st.markdown(f"""<div class="encabezado">{logo_html}<div>
<h1>Análisis Técnico + IA</h1>
<p>Análisis Técnico Bursátil · Prof. Leopoldo Calderón · Grupo 12: Martín Tapia, Tomás Aedo y Martín Moraga</p>
<p class="detalle">Detectar · Dibujar · Interpretar — sube un archivo con Fecha, Apertura, Máximo, Mínimo y Cierre (Volumen opcional).</p>
</div></div>""", unsafe_allow_html=True)

# En el celular la barra lateral queda escondida: el archivo se sube en la página
# y los parámetros finos quedan en la barra lateral
ua = st.context.headers.get("User-Agent", "")
celular = any(m in ua for m in ("Mobi", "Android", "iPhone", "iPad"))

archivo = st.file_uploader("Archivo CSV o Excel con los datos OHLC", type=["csv", "xlsx", "xls"])
with st.sidebar:
    st.header("Parámetros")
    ventana = st.slider("Sensibilidad de máximos y mínimos (velas a cada lado)", 2, 15, 5,
                        help="Más alto = solo los pivotes más importantes.")
    ultimas = st.slider("Patrones: revisar las últimas N velas", 5, 60, 20)
    ver_todos = st.checkbox("Mostrar patrones de todo el periodo", value=False)
    usar_ia = st.checkbox("Interpretar con IA", value=True)

if archivo is None:
    st.info("Sube un archivo para empezar. Los parámetros se ajustan en el menú lateral (» arriba a la izquierda). Puedes descargar uno desde Yahoo Finance (pestaña Historical Data → Download).")
    st.stop()

try:
    df, avisos = datos.cargar_ohlc(archivo)
except ValueError as e:
    st.error(str(e))
    st.stop()
for a in avisos:
    st.warning(a)

@st.cache_data(show_spinner=False, ttl=3600)
def diagnostico_ia(resumen_json, proveedor, clave):
    """Se guarda la respuesta para no volver a llamar a la IA si nada cambió."""
    return interpretacion.interpretar_con_ia(json.loads(resumen_json), proveedor, clave)


# ---------- Detectar ----------
puntos = estructura.pivotes(df, ventana)
tend = estructura.tendencia(puntos, df)
linea = estructura.linea_tendencia(puntos, df, tend["tendencia"])
soportes, resistencias = estructura.soportes_resistencias(df, puntos)
todos = patrones.detectar(df)
recientes = patrones.recientes(todos, df, ultimas)
patrones.ubicar(todos, df, soportes, resistencias, holgura=0.5 * float(estructura.atr(df).iat[-1]))
a_dibujar = todos if ver_todos else recientes

# ---------- Dibujar ----------
letra = 9 if celular else 11  # tamaño de los textos del gráfico
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
        fig.add_annotation(x=df["Fecha"].iat[0], y=z["nivel"], text=f'{nombre[0] if celular else nombre} {z["nivel"]:,.2f}' + ("" if celular else f' ({z["toques"]} toques)'),
                           showarrow=False, xanchor="left", bgcolor="rgba(255,255,255,0.7)", font=dict(size=letra), row=1, col=1)

# Tendencia lateral: se dibuja el rango entre el soporte y la resistencia más cercanos
if tend["tendencia"] == "Lateral" and soportes and resistencias:
    desde = puntos[-6]["fecha"] if len(puntos) >= 6 else df["Fecha"].iat[0]
    fig.add_shape(type="rect", x0=desde, x1=df["Fecha"].iat[-1], y0=soportes[0]["nivel"], y1=resistencias[0]["nivel"],
                  line=dict(color="#1565c0", width=2, dash="dot"), fillcolor="rgba(21,101,192,0.04)", row=1, col=1)
    if not celular:  # en pantalla chica el texto tapa las velas; el rectángulo basta
        fig.add_annotation(x=desde, y=resistencias[0]["nivel"], text="Rango lateral", showarrow=False, xanchor="left",
                           yanchor="bottom", font=dict(size=letra, color="#1565c0"), row=1, col=1)

# Último precio (línea punteada; el valor aparece en la leyenda)
ultimo = float(df["Cierre"].iat[-1])
fig.add_trace(go.Scatter(x=[df["Fecha"].iat[0], df["Fecha"].iat[-1]], y=[ultimo, ultimo], mode="lines",
                         name=f"Último cierre {ultimo:,.2f}", line=dict(color="#455a64", width=1, dash="dot"),
                         hoverinfo="skip"), row=1, col=1)

# Pivotes con su etiqueta
for tipo, pos, color in [("max", "top center", "#c62828"), ("min", "bottom center", "#2e7d32")]:
    sel = [p for p in puntos if p["tipo"] == tipo]
    fig.add_trace(go.Scatter(x=[p["fecha"] for p in sel], y=[p["precio"] for p in sel], mode="markers+text",
                             text=[p["etiqueta"] for p in sel], textposition=pos, name="Máximos" if tipo == "max" else "Mínimos",
                             marker=dict(color=color, size=6), textfont=dict(color=color, size=letra)), row=1, col=1)

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
        hovertext=[" + ".join(h["patron"] for h in hs) + f' ({hs[0]["ubicacion"]})' for hs in sel], hoverinfo="text+x"), row=1, col=1)
for k, i in enumerate(sorted(por_vela)[-(2 if celular else 4):]):
    hs = por_vela[i]
    sesgo = hs[-1]["sesgo"]
    abajo = sesgo == "alcista"
    y = df["Minimo"].iat[i] if abajo else df["Maximo"].iat[i]
    fig.add_annotation(x=hs[0]["fecha"], y=y, text=" + ".join(h["patron"] for h in hs), showarrow=True, arrowhead=0,
                       ax=0, ay=((30 if celular else 45) + 28 * k) * (1 if abajo else -1), bgcolor="rgba(255,255,255,0.85)",
                       font=dict(size=letra, color=COLORES[sesgo]), arrowcolor=COLORES[sesgo], row=1, col=1)

if tiene_vol:
    fig.add_trace(go.Bar(x=df["Fecha"], y=df["Volumen"], name="Volumen", marker_color="#90a4ae"), row=2, col=1)
if celular:
    # Pantalla angosta: gráfico más bajo, leyenda abajo y sin arrastre (así el dedo hace scroll en la página)
    fig.update_layout(height=520, xaxis_rangeslider_visible=False, dragmode=False,
                      legend=dict(orientation="h", y=-0.12, x=0, font=dict(size=9)),
                      margin=dict(l=0, r=0, t=10, b=10), font=dict(size=10))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False, "scrollZoom": False})
else:
    fig.update_layout(height=700, xaxis_rangeslider_visible=False, legend=dict(orientation="h", y=1.05),
                      margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, width="stretch")

# ---------- Interpretar ----------
flecha = {"Alcista": "↗", "Bajista": "↘", "Lateral": "→"}[tend["tendencia"]]
variacion = (df["Cierre"].iat[-1] / df["Cierre"].iat[0] - 1) * 100
tarjetas = [
    ("Tendencia", f'{flecha} {tend["tendencia"]}', None),
    ("Último cierre", f'{df["Cierre"].iat[-1]:,.2f}', f"{variacion:+.1f}% en el periodo"),
    ("Soporte cercano", f'{soportes[0]["nivel"]:,.2f}' if soportes else "—",
     f'{soportes[0]["toques"]} toques' if soportes else None),
    ("Resistencia cercana", f'{resistencias[0]["nivel"]:,.2f}' if resistencias else "—",
     f'{resistencias[0]["toques"]} toques' if resistencias else None),
]
if celular:
    # En el celular las columnas se apilan; se usa una grilla de 2 x 2 para que quepan en una pantalla
    celdas = "".join(f'<div class="tarjeta"><span>{t}</span><b>{v}</b><small>{d or "&nbsp;"}</small></div>'
                     for t, v, d in tarjetas)
    st.markdown(f'<div class="grilla">{celdas}</div>', unsafe_allow_html=True)
else:
    for col, (titulo, valor, detalle) in zip(st.columns(4), tarjetas):
        with col.container(border=True):
            st.metric(titulo, valor, detalle, delta_color="off" if titulo != "Último cierre" else "normal")
st.write(f'**Estructura:** {tend["estructura"]}. {tend["medias"]}')

resumen = interpretacion.resumen(df, puntos, tend, soportes, resistencias, recientes)
st.subheader("Diagnóstico técnico")
proveedor, clave = interpretacion.obtener_clave()
texto, fuente = None, "reglas"
if usar_ia and clave:
    with st.spinner("La IA está redactando el diagnóstico..."):
        try:
            texto = diagnostico_ia(json.dumps(resumen, ensure_ascii=False, sort_keys=True), proveedor, clave)
            fuente = "IA (Gemini de Google)" if proveedor == "gemini" else "IA (Claude de Anthropic)"
        except Exception as e:
            st.warning(f"No se pudo usar la IA ({e}). Se muestra el diagnóstico por reglas.")
elif usar_ia:
    st.info("No hay clave de API configurada: se muestra el diagnóstico por reglas.")
if texto is None:
    texto = interpretacion.interpretar_con_reglas(resumen)
# La IA responde con negritas (**) y saltos de línea: se muestra como markdown
with st.container(border=True):
    st.markdown(texto.replace("$", "\\$").replace("\n", "  \n"))
    st.caption(f"Fuente del diagnóstico: {fuente}. No es una recomendación de inversión.")

with st.expander("Patrones detectados en las últimas velas"):
    if recientes:
        for h in reversed(recientes):
            st.write(f'**{h["fecha"]:%d-%m-%Y} · {h["patron"]}** ({h["sesgo"]}, {h["ubicacion"]}): {h["explicacion"]}')
    else:
        st.write("No hay patrones de la lista en las últimas velas.")
with st.expander("Datos que recibe la IA (evidencia)"):
    st.json(resumen)

# ---------- Descargar ----------
nombre_archivo = getattr(archivo, "name", "datos").rsplit(".", 1)[0]
cuerpo = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(texto)).replace("\n", "<br>")
reporte = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Análisis técnico {html.escape(nombre_archivo)}</title>
<style>body{{font-family:Arial,sans-serif;max-width:1100px;margin:24px auto;padding:0 16px;color:#222}}</style></head><body>
<h1>Análisis técnico · {html.escape(nombre_archivo)}</h1>
<p>Periodo: {resumen["periodo"]} · {resumen["velas"]} velas · Último cierre: {resumen["ultimo_cierre"]:,}</p>
{fig.to_html(full_html=False, include_plotlyjs="cdn")}
<h2>Diagnóstico técnico</h2><p>{cuerpo}</p>
<p style="color:#777;font-size:12px">Fuente del diagnóstico: {fuente}. No es una recomendación de inversión. Grupo 12 · Análisis Técnico Bursátil.</p>
</body></html>"""
st.download_button("Descargar análisis (gráfico + diagnóstico)", reporte, file_name=f"analisis_{nombre_archivo}.html",
                   mime="text/html", on_click="ignore")

st.markdown('<div class="pie">Grupo 12 · Análisis Técnico Bursátil · 2026 · La app apoya al analista, no reemplaza su criterio.</div>',
            unsafe_allow_html=True)
