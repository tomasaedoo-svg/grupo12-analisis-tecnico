# App de Análisis Técnico + IA · Grupo 12 (Modalidad B)

Versión 0, armada el 26-oct-2026 como punto de partida. Ya funciona de punta a punta: carga un CSV o Excel, dibuja velas, máximos y mínimos (HH/HL/LH/LL), línea de tendencia, soportes y resistencias y patrones de la lista del profe, y redacta un diagnóstico (con IA o, si no hay clave, con reglas).

## Archivos

| Archivo | Qué hace | Responsable sugerido |
|---|---|---|
| `app.py` | Página, gráfico y dibujos | Martín Tapia |
| `datos.py` | Lee y valida el CSV/Excel (columnas en español o inglés, formato Yahoo, coma decimal) | Martín Tapia |
| `estructura.py` | Pivotes, HH/HL/LH/LL, tendencia, línea de tendencia, soportes y resistencias | Tomás |
| `patrones.py` | Patrones de velas de la imagen Patterns-2 | Martín Moraga |
| `interpretacion.py` | Resumen de hallazgos e interpretación con IA (y respaldo por reglas) | Martín Moraga |
| `ejemplos/` | Dos CSV **sintéticos** (inventados) solo para probar que la app corre. Para el trabajo usen datos reales. | |

## Cómo correrla en el computador

1. Instalar Python 3.11 o más nuevo (python.org).
2. En una terminal, dentro de esta carpeta: `pip install -r requirements.txt`
3. `streamlit run app.py` (se abre en el navegador).

## Datos reales

Yahoo Finance → buscar la acción (por ejemplo SQM-B.SN, CHILE.SN, AAPL) → Historical Data → periodo 1 año, diario → Download. Ese CSV se sube tal cual.

## IA

La interpretación usa Claude (Anthropic). Se necesita una clave de API (console.anthropic.com, con unos pocos dólares de crédito alcanza). Para usarla localmente, crear `.streamlit/secrets.toml` con:

```
ANTHROPIC_API_KEY = "la-clave"
```

Nunca subir ese archivo a GitHub. En Streamlit Cloud la clave va en Settings → Secrets. Sin clave, la app igual funciona con el diagnóstico por reglas.

## Publicarla (para la demo)

1. Subir esta carpeta a un repositorio de GitHub (sin `secrets.toml`).
2. share.streamlit.io → New app → elegir el repositorio y `app.py`.
3. Agregar la clave en Secrets.

## Pendientes por persona (ideas)

- **Tomás:** revisar con criterio financiero la tendencia y los soportes y resistencias en 3 o 4 acciones reales; ajustar la sensibilidad de los pivotes y la tolerancia de las zonas; quizás dibujar un canal cuando la tendencia es lateral.
- **Martín Tapia:** que los nombres de los patrones no se tapen en el gráfico; publicar la app; probar con archivos Excel y CSV de distintas fuentes.
- **Martín Moraga:** comparar los patrones detectados con lo que se ve en el gráfico y ajustar los umbrales; probar la interpretación con IA y revisar que respete las restricciones del enunciado.
- **Los tres:** informe ejecutivo (objetivo, funcionamiento, metodología, herramientas de AT, uso de IA, limitaciones), presentación y ensayo con un CSV que no hayan visto.
