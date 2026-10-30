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
:root {--azul:#7FC3EC; --azul-2:#0B4A69; --fondo:#06141F; --panel:#0C2232; --linea:#1C3A50; --texto:#E8F0F6;
  --suave:#9DB2C3; --sube:#34C77B; --baja:#F2564B; --lateral:#5AA9F0; --marca:#063952;}
html, body, [data-testid="stAppViewContainer"] {font-variant-numeric: tabular-nums;}
::selection {background:#2A5D80; color:#fff;}
html {font-size:17px;}
.block-container {padding-top:2.2rem; max-width:1280px;}
[data-testid="stSidebar"] {background:#0A1C2A; border-right:1px solid var(--linea);}
[data-testid="stLogo"], [data-testid="stSidebarLogo"], [data-testid="stHeaderLogo"] {background:#fff; border-radius:6px; padding:3px 6px; height:2.4rem !important;}
h2.seccion {font-size:1.45rem; letter-spacing:-0.01em; font-weight:700; color:var(--azul); margin:26px 0 10px 0; padding:0;}
/* Barra superior */
.barra {display:flex; align-items:center; justify-content:space-between; gap:20px; padding:4px 0 16px 0;
  border-bottom:1px solid var(--linea); margin-bottom:18px;}
.barra .marca {display:flex; align-items:center; gap:18px;}
.barra img {height:58px; background:#fff; border-radius:8px; padding:6px 10px;}
.barra .sep {width:1px; height:40px; background:var(--linea);}
.barra h1 {font-size:2.2rem; line-height:1.1; letter-spacing:-0.02em; color:#fff; margin:0; padding:0; font-weight:700;}
.barra p {color:var(--suave); margin:2px 0 0 0; font-size:0.92rem;}
.barra .grupo {text-align:right; color:var(--suave); font-size:0.85rem; line-height:1.4;}
.barra .grupo b {color:var(--texto);}
/* Franja de cotización */
.franja {background:linear-gradient(180deg,#0B3550,#082A40); border:1px solid #1F4B68; color:#fff; border-radius:10px; padding:22px 26px; display:grid;
  grid-template-columns:minmax(330px,1.7fr) repeat(4, minmax(0,1fr)); gap:22px; align-items:center; margin:6px 0 14px 0;
  box-shadow:0 8px 24px rgba(0,0,0,0.35);}
.franja .dato {display:flex; flex-direction:column; gap:3px; min-width:0;}
.franja .rot {color:#9DB9CE; font-size:0.85rem;}
.franja .val {font-size:1.6rem; font-weight:700; color:#fff; white-space:nowrap; display:flex; align-items:center; gap:6px;}
.franja .det {color:#9DB9CE; font-size:0.82rem; overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical;}
.franja .precio {font-size:3.2rem; line-height:1; letter-spacing:-0.02em;}
.franja .ficha {display:inline-block; padding:2px 10px; border-radius:5px; font-size:1.05rem; letter-spacing:0; font-weight:700; margin-left:4px;}
.franja .ficha.sube {background:rgba(52,199,123,0.18); color:#5FE09A;} .franja .ficha.baja {background:rgba(242,86,75,0.18); color:#FF8077;}
.franja .tend-Alcista {color:#5FE09A;} .franja .tend-Bajista {color:#FF8077;} .franja .tend-Lateral {color:#8CC4F5;}
.franja svg {flex:none;}
.nota-medias {color:var(--suave); font-size:0.9rem; margin:-4px 0 4px 2px;}
/* Paneles */
[data-testid="stPlotlyChart"] {background:var(--panel); border:1px solid var(--linea); border-radius:8px; padding:8px 6px 4px 6px;}
.panel {background:var(--panel); border:1px solid var(--linea); border-radius:8px; padding:6px 22px 18px 22px;
  box-shadow:0 4px 16px rgba(0,0,0,0.25); margin-bottom:14px;}
/* Pauta de evidencia */
.pauta {width:100%; border-collapse:collapse; margin:0; border:none;}
.pauta th, .pauta td {border:none !important; background:transparent !important;}
.pauta th {text-align:left; vertical-align:top; width:210px; color:var(--azul); font-weight:700; font-size:1rem; padding:12px 16px 12px 0;}
.pauta td {padding:12px 0; color:var(--texto); line-height:1.5; font-size:1.05rem;}
.pauta tr + tr th, .pauta tr + tr td {border-top:1px solid var(--linea) !important;}
.lectura {font-size:1.15rem; line-height:1.6; color:var(--texto); max-width:72ch; margin:14px 0 18px 0;}
.escala {display:flex; flex-wrap:wrap; align-items:center; gap:14px; padding-top:14px; border-top:1px solid var(--linea);}
.escala .tramos {display:flex; gap:4px;}
.escala .tramo {width:84px; padding:7px 0; text-align:center; font-size:0.95rem; font-weight:700; border-radius:5px;
  background:#132F44; color:#6F8BA0;}
.escala .tramo.on {color:#fff;}
.escala .tramo.on.baja {background:#D0453B;} .escala .tramo.on.media {background:#C98A1E;} .escala .tramo.on.alta {background:#21995B;}
.escala .razon {color:var(--suave); font-size:0.95rem; flex:1; min-width:220px;}
.fuente {color:#7F97AA; font-size:0.82rem; margin-top:12px;}
/* Estado vacío */
.vacio {background:var(--panel); border:1px solid var(--linea); border-radius:8px; padding:20px 22px; margin-top:8px;}
.vacio h3 {font-size:1.1rem; color:var(--azul); margin:0 0 6px 0; padding:0;}
.vacio p {color:var(--suave); margin:0 0 12px 0; max-width:72ch;}
.vacio table {border-collapse:collapse; font-size:0.9rem; min-width:100%;}
.vacio th {background:#132F44; color:var(--azul); text-align:right; padding:6px 12px; font-weight:700;}
.vacio th:first-child, .vacio td:first-child {text-align:left;}
.vacio td {white-space:nowrap; padding:6px 12px; text-align:right; border-top:1px solid var(--linea); color:var(--texto);}
.vacio th, .vacio td {border-left:none !important; border-right:none !important; border-bottom:none !important;}
.vacio .tabla {overflow-x:auto;}
.vacio ol {margin:14px 0 0 0; padding-left:20px; color:var(--texto);}
.vacio li {margin:3px 0;}
.pie {color:#7F97AA; font-size:0.8rem; text-align:center; margin-top:36px; padding-top:14px; border-top:1px solid var(--linea);}
@media (max-width: 900px) {
  .franja {grid-template-columns:1fr 1fr; gap:14px 16px;}
  .franja .principal {grid-column:1 / -1;}
}
@media (max-width: 640px) {
  .block-container {padding-top:3.4rem; padding-left:0.8rem; padding-right:0.8rem;}
  .barra {padding-bottom:12px; margin-bottom:12px;}
  .barra img, .barra .sep, .barra .grupo {display:none;}  /* el logo ya aparece en la barra de arriba */
  .barra p {font-size:0.82rem;}
  .franja {padding:14px 16px;}
  .franja .val {font-size:1.05rem;}
  .franja .val.precio {font-size:2.4rem;}
  .barra h1 {font-size:1.6rem;}
  .panel {padding:4px 14px 14px 14px;}
  .pauta th, .pauta td {display:block; width:auto; padding:0;}
  .pauta th {padding-top:10px;}
  .pauta td, .pauta tr + tr td {padding:2px 0 10px 0; border-top:none !important;}
  .franja {align-items:start;}
  .escala .tramo {width:62px;}
  h2.seccion {font-size:1.1rem; margin-top:20px;}
}
</style>""", unsafe_allow_html=True)

logo_html = ""
if LOGO.exists():
    logo_html = f'<img src="data:image/png;base64,{base64.b64encode(LOGO.read_bytes()).decode()}" alt="Universidad Finis Terrae"><div class="sep"></div>'
    st.logo(str(LOGO))
st.markdown(f"""<div class="barra"><div class="marca">{logo_html}<div>
<h1>Análisis Técnico + IA</h1>
<p>Detecta, dibuja e interpreta un gráfico de velas a partir de datos OHLC.</p>
</div></div>
<div class="grupo"><b>Grupo 12</b> · Análisis Técnico Bursátil<br>Prof. Leopoldo Calderón<br>Martín Tapia, Tomás Aedo y Martín Moraga</div>
</div>""", unsafe_allow_html=True)

# En el celular la barra lateral queda escondida: el archivo se sube en la página
# y los parámetros finos quedan en la barra lateral
ua = st.context.headers.get("User-Agent", "")
celular = any(m in ua for m in ("Mobi", "Android", "iPhone", "iPad"))

archivo = st.file_uploader("Archivo CSV o Excel con los datos OHLC", type=["csv", "txt", "xlsx", "xls"])
with st.sidebar:
    st.header("Parámetros")
    ventana = st.slider("Sensibilidad de máximos y mínimos (velas a cada lado)", 2, 15, 5,
                        help="Más alto = solo los pivotes más importantes.")
    ultimas = st.slider("Patrones: revisar las últimas N velas", 5, 60, 20)
    ver_todos = st.checkbox("Mostrar patrones de todo el periodo", value=False)
    usar_ia = st.checkbox("Interpretar con IA", value=True)

if archivo is None:
    st.markdown("""<div class="vacio">
<h3>Formato del archivo</h3>
<p>Una fila por vela diaria. Se aceptan nombres en español o inglés (Date, Open, High, Low, Close, Volume) y archivos de Yahoo Finance o Google Finanzas. El volumen es opcional.</p>
<div class="tabla"><table><tr><th>Fecha</th><th>Apertura</th><th>Máximo</th><th>Mínimo</th><th>Cierre</th><th>Volumen</th></tr>
<tr><td>2026-10-27</td><td>343,17</td><td>347,78</td><td>342,39</td><td>347,10</td><td>39.984.395</td></tr>
<tr><td>2026-10-28</td><td>346,92</td><td>347,18</td><td>343,52</td><td>343,83</td><td>35.714.331</td></tr>
<tr><td>2026-10-29</td><td>348,00</td><td>351,43</td><td>347,30</td><td>348,91</td><td>42.582.126</td></tr></table></div>
<ol><li><b>Detectar:</b> máximos y mínimos (HH, HL, LH, LL), tendencia, soportes, resistencias y patrones de velas.</li>
<li><b>Dibujar:</b> zonas, línea de tendencia, pivotes y patrones sobre el gráfico.</li>
<li><b>Interpretar:</b> la IA redacta el diagnóstico solo con esa evidencia e indica su nivel de confianza.</li></ol>
<p style="margin-top:12px">Los ajustes de sensibilidad están en el menú lateral (» arriba a la izquierda).</p>
</div>""", unsafe_allow_html=True)
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


SECCIONES = ["TENDENCIA", "ESTRUCTURA", "SOPORTE", "PATRÓN", "DIAGNÓSTICO", "NIVEL DE CONFIANZA"]
NIVELES = {"bajo": "baja", "baja": "baja", "medio": "media", "media": "media", "alto": "alta", "alta": "alta"}


def diagnostico_html(texto, fuente):
    """Arma el diagnóstico como pauta de evidencia (conclusión por fila) y una escala de confianza.
    Devuelve None si el texto no trae el formato pedido."""
    partes, actual = {}, None
    for linea in texto.splitlines():
        limpia = linea.replace("**", "").replace("#", "").strip()
        clave = next((k for k in SECCIONES if limpia.upper().startswith(k)), None)
        if clave and ":" in limpia:
            actual = clave
            partes[actual] = limpia.split(":", 1)[1].strip()
        elif actual and limpia:
            partes[actual] += " " + limpia
    if len(partes) < 4:
        return None
    fmt = lambda t: re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(t))
    nombres = {"TENDENCIA": "Tendencia", "ESTRUCTURA": "Estructura", "SOPORTE": "Soporte y resistencia", "PATRÓN": "Patrón"}
    filas = "".join(f"<tr><th>{nombres[k]}</th><td>{fmt(partes[k])}</td></tr>" for k in nombres if k in partes)
    lectura = f'<p class="lectura">{fmt(partes["DIAGNÓSTICO"])}</p>' if "DIAGNÓSTICO" in partes else ""
    escala = ""
    if "NIVEL DE CONFIANZA" in partes:
        txt = partes["NIVEL DE CONFIANZA"]
        nivel = next((v for k, v in NIVELES.items() if re.match(rf"\W*{k}\b", txt.lower())), None)
        razon = re.sub(r"^\W*(alt[oa]|medi[oa]|baj[oa])\b[\s,.:;-]*", "", txt, flags=re.I) or txt
        tramos = "".join(f'<span class="tramo {n}{" on" if n == nivel else ""}">{n.capitalize()}</span>'
                         for n in ["baja", "media", "alta"])
        escala = (f'<div class="escala"><b>Confianza</b><div class="tramos">{tramos}</div>'
                  f'<span class="razon">{fmt(razon[:1].upper() + razon[1:])}</span></div>')
    return (f'<div class="panel"><table class="pauta">{filas}</table>{lectura}{escala}'
            f'<div class="fuente">Fuente: {html.escape(fuente)}. No es una recomendación de inversión.</div></div>')


FLECHAS = {  # flechas dibujadas en SVG (sube, baja, lateral)
    "Alcista": '<svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 14 L14 3 M7 3 H14 V10"/></svg>',
    "Bajista": '<svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4 L14 15 M14 8 V15 H7"/></svg>',
    "Lateral": '<svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 9 H15 M10 4 L15 9 L10 14"/></svg>',
}


# ---------- Detectar ----------
puntos = estructura.pivotes(df, ventana)
tend = estructura.tendencia(puntos, df)
linea = estructura.linea_tendencia(puntos, df, tend["tendencia"])
soportes, resistencias = estructura.soportes_resistencias(df, puntos)
todos = patrones.detectar(df)
recientes = patrones.recientes(todos, df, ultimas)
patrones.ubicar(todos, df, soportes, resistencias, holgura=0.5 * float(estructura.atr(df).iat[-1]))
a_dibujar = todos if ver_todos else recientes

# ---------- Franja con los datos clave ----------
nombre_archivo = getattr(archivo, "name", "datos").rsplit(".", 1)[0]
variacion = (df["Cierre"].iat[-1] / df["Cierre"].iat[0] - 1) * 100
ult_patron = recientes[-1] if recientes else None
zona = lambda zs: (f'{zs[0]["nivel"]:,.2f}', f'{zs[0]["toques"]} toques · {abs(zs[0]["nivel"] / df["Cierre"].iat[-1] - 1) * 100:.1f}% del precio') if zs else ("—", "no identificada")
datos_franja = [
    ("Tendencia", f'<span class="tend-{tend["tendencia"]}">{FLECHAS[tend["tendencia"]]}</span>{tend["tendencia"]}', tend["estructura"]),
    ("Soporte cercano", *zona(soportes)),
    ("Resistencia cercana", *zona(resistencias)),
    ("Último patrón", html.escape(ult_patron["patron"]) if ult_patron else "Ninguno",
     f'{ult_patron["sesgo"]}, {ult_patron["ubicacion"]}' if ult_patron else f"en las últimas {ultimas} velas"),
]
celdas = "".join(f'<div class="dato"><span class="rot">{r}</span><span class="val">{v}</span><span class="det" title="{html.escape(d)}">{html.escape(d)}</span></div>'
                 for r, v, d in datos_franja)
st.markdown(f"""<div class="franja"><div class="dato principal">
<span class="rot">{html.escape(nombre_archivo)} · {df["Fecha"].iat[0]:%d-%m-%Y} a {df["Fecha"].iat[-1]:%d-%m-%Y} · {len(df)} velas</span>
<span class="val precio">{df["Cierre"].iat[-1]:,.2f}<span class="ficha {'sube' if variacion >= 0 else 'baja'}">{variacion:+.1f}%</span></span>
<span class="det">Último cierre · variación en el periodo</span></div>{celdas}</div>
<div class="nota-medias">{html.escape(tend["medias"])}</div>""", unsafe_allow_html=True)

# ---------- Dibujar ----------
st.markdown('<h2 class="seccion">Gráfico de velas</h2>', unsafe_allow_html=True)
letra = 9 if celular else 11  # tamaño de los textos del gráfico
tiene_vol = "Volumen" in df and df["Volumen"].fillna(0).sum() > 0
fig = make_subplots(rows=2 if tiene_vol else 1, cols=1, shared_xaxes=True,
                    row_heights=[0.8, 0.2] if tiene_vol else [1], vertical_spacing=0.03)
fig.add_trace(go.Candlestick(x=df["Fecha"], open=df["Apertura"], high=df["Maximo"], low=df["Minimo"],
                             close=df["Cierre"], name="Precio",
                             increasing_line_color="#34C77B", decreasing_line_color="#F2564B",
                             increasing_fillcolor="#34C77B", decreasing_fillcolor="#F2564B"), row=1, col=1)
for n, color in [(20, "#E3A73A"), (50, "#B48CF0")]:
    fig.add_trace(go.Scatter(x=df["Fecha"], y=df["Cierre"].rolling(n).mean(), name=f"Media {n}",
                             line=dict(color=color, width=1.2)), row=1, col=1)

# Zonas de soporte y resistencia
for zonas, color, nombre in [(soportes, "rgba(52,199,123,0.14)", "Soporte"), (resistencias, "rgba(242,86,75,0.14)", "Resistencia")]:
    for z in zonas:
        fig.add_hrect(y0=z["bajo"], y1=z["alto"], fillcolor=color, line_width=0, row=1, col=1)
        fig.add_annotation(x=df["Fecha"].iat[0], y=z["nivel"], text=f'{nombre[0] if celular else nombre} {z["nivel"]:,.2f}' + ("" if celular else f' ({z["toques"]} toques)'),
                           showarrow=False, xanchor="left", bgcolor="rgba(6,20,31,0.75)", font=dict(size=letra, color="#E8F0F6"), row=1, col=1)

# Tendencia lateral: se dibuja el rango entre el soporte y la resistencia más cercanos
if tend["tendencia"] == "Lateral" and soportes and resistencias:
    desde = puntos[-6]["fecha"] if len(puntos) >= 6 else df["Fecha"].iat[0]
    fig.add_shape(type="rect", x0=desde, x1=df["Fecha"].iat[-1], y0=soportes[0]["nivel"], y1=resistencias[0]["nivel"],
                  line=dict(color="#5AA9F0", width=2, dash="dot"), fillcolor="rgba(90,169,240,0.05)", row=1, col=1)
    if not celular:  # en pantalla chica el texto tapa las velas; el rectángulo basta
        fig.add_annotation(x=desde, y=resistencias[0]["nivel"], text="Rango lateral", showarrow=False, xanchor="left",
                           yanchor="bottom", font=dict(size=letra, color="#5AA9F0"), row=1, col=1)

# Último precio (línea punteada; el valor aparece en la leyenda)
ultimo = float(df["Cierre"].iat[-1])
fig.add_trace(go.Scatter(x=[df["Fecha"].iat[0], df["Fecha"].iat[-1]], y=[ultimo, ultimo], mode="lines",
                         name=f"Último cierre {ultimo:,.2f}", line=dict(color="#9DB2C3", width=1, dash="dot"),
                         hoverinfo="skip"), row=1, col=1)

# Pivotes con su etiqueta
for tipo, pos, color in [("max", "top center", "#FF8077"), ("min", "bottom center", "#5FE09A")]:
    sel = [p for p in puntos if p["tipo"] == tipo]
    fig.add_trace(go.Scatter(x=[p["fecha"] for p in sel], y=[p["precio"] for p in sel], mode="markers+text",
                             text=[p["etiqueta"] for p in sel], textposition=pos, name="Máximos" if tipo == "max" else "Mínimos",
                             marker=dict(color=color, size=6), textfont=dict(color=color, size=letra)), row=1, col=1)

# Línea de tendencia
if linea:
    fig.add_trace(go.Scatter(x=linea["x"], y=linea["y"], mode="lines", name=f'Línea de tendencia {tend["tendencia"].lower()}',
                             line=dict(color="#5AA9F0", width=2.4, dash="dash")), row=1, col=1)

# Patrones de velas: un triángulo por vela (pasando el mouse se ve el nombre)
# y el nombre escrito solo en las últimas velas con patrón, para que no se tapen
COLORES = {"alcista": "#5FE09A", "bajista": "#FF8077", "neutral": "#C2D0DB"}
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
                       ax=0, ay=((30 if celular else 45) + 28 * k) * (1 if abajo else -1), bgcolor="rgba(6,20,31,0.85)",
                       font=dict(size=letra, color=COLORES[sesgo]), arrowcolor=COLORES[sesgo], row=1, col=1)

if tiene_vol:
    fig.add_trace(go.Bar(x=df["Fecha"], y=df["Volumen"], name="Volumen", marker_color="#2B4E68"), row=2, col=1)
# Estilo común: fondo blanco, cuadrícula suave y línea guía al pasar el dedo o el mouse
fig.update_layout(template="plotly_dark", plot_bgcolor="#0C2232", hovermode="x",
                  font=dict(family="Source Sans Pro, Arial, sans-serif", color="#C9D7E2"),
                  paper_bgcolor="#0C2232", hoverlabel=dict(bgcolor="#06141F", font_color="#FFFFFF", bordercolor="#5AA9F0"))
fig.update_xaxes(showgrid=False, showspikes=True, spikemode="across", spikethickness=1, spikecolor="#5F7A8F")
if (df["Fecha"].dt.dayofweek < 5).all():  # acciones: se ocultan los fines de semana (las cripto sí operan)
    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
fig.update_yaxes(gridcolor="#173247", side="right", showspikes=True, spikethickness=1, spikecolor="#5F7A8F")
if not celular:
    fig.update_xaxes(rangeselector=dict(buttons=[dict(count=1, label="1M", step="month", stepmode="backward"),
                                                 dict(count=3, label="3M", step="month", stepmode="backward"),
                                                 dict(count=6, label="6M", step="month", stepmode="backward"),
                                                 dict(step="all", label="Todo")],
                                        bgcolor="#132F44", activecolor="#2A5D80", font=dict(color="#E8F0F6"), y=1.02, yanchor="bottom", x=1, xanchor="right"),
                     row=1, col=1)
if celular:
    # Pantalla angosta: gráfico más bajo, leyenda abajo y sin arrastre (así el dedo hace scroll en la página)
    fig.update_layout(height=520, xaxis_rangeslider_visible=False, dragmode=False,
                      legend=dict(orientation="h", y=-0.12, x=0, font=dict(size=9)),
                      margin=dict(l=0, r=0, t=10, b=10), font=dict(size=10))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False, "scrollZoom": False})
else:
    fig.update_layout(height=700, xaxis_rangeslider_visible=False, legend=dict(orientation="h", y=-0.05, yanchor="top", x=0, xanchor="left"),
                      margin=dict(l=10, r=10, t=40, b=40))
    st.plotly_chart(fig, width="stretch")

# ---------- Interpretar ----------
resumen = interpretacion.resumen(df, puntos, tend, soportes, resistencias, recientes)
st.markdown('<h2 class="seccion">Diagnóstico técnico</h2>', unsafe_allow_html=True)
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
bloque = diagnostico_html(texto, fuente)
if bloque:
    st.markdown(bloque, unsafe_allow_html=True)
else:  # si la IA no respetó el formato, se muestra el texto tal cual
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
cuerpo = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(texto)).replace("\n", "<br>")
reporte = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Análisis técnico {html.escape(nombre_archivo)}</title>
<link href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;700&display=swap" rel="stylesheet">
<style>body{{font-family:"Source Sans 3",system-ui,sans-serif;max-width:1100px;margin:24px auto;padding:0 16px;color:#16232E;font-variant-numeric:tabular-nums}} h1,h2{{color:#063952}}</style></head><body>
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
