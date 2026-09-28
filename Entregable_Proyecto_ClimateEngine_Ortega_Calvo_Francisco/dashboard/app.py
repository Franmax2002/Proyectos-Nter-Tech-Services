"""
dashboard/app.py - Cuadro de mando interactivo de Climate Engine (Streamlit).

DECISION DE DISENO: este fichero es deliberadamente minimo y autocontenido.
`streamlit run` necesita un script .py que se re-ejecuta de arriba a abajo
en cada interaccion del usuario (cada clic, cada cambio de ciudad); usar
un notebook o invocar un kernel de Jupyter en cada rerun (como hace
`cli.py` con `nbclient`) seria demasiado lento para un panel interactivo.
Ademas, `climate_engine/visualize_dashboard.ipynb` (donde esta la misma
logica documentada paso a paso) usa `%run` para encadenar `config.ipynb`,
una magia de linea de IPython que la libreria `importnb` no puede
convertir a Python valido fuera de un kernel real.

Por ambos motivos, este script reutiliza `config.ipynb` via `importnb`
(que si es importable, al no tener celdas `%run`) para las rutas de
datos, y reimplementa aqui las mismas consultas DuckDB y figuras Plotly
que estan documentadas y probadas en `visualize_dashboard.ipynb`. Ambos
ficheros se mantienen sincronizados manualmente.

Puesta en marcha: `streamlit run dashboard/app.py` desde la raiz del
entregable (ver README.md).
"""
import sys
from pathlib import Path

import duckdb
import plotly.graph_objects as go
import streamlit as st

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_PROYECTO / "climate_engine"))

from importnb import Notebook  # noqa: E402

with Notebook():
    import config  # climate_engine/config.ipynb (sin celdas %run: importable directamente)

RUTA_GOLD = config.RUTA_GOLD


@st.cache_data(ttl=60)
def _leer_tabla_gold(nombre_tabla):
    """Lee una tabla Gold completa reconstruyendo 'ciudad' desde el
    particionado Hive de las carpetas (ciudad=<Nombre>). Misma consulta
    que `visualize_dashboard.cargar_*` (ver ese notebook para el detalle
    documentado)."""
    patron = str(RUTA_GOLD / nombre_tabla / "ciudad=*" / "datos.parquet")
    con = duckdb.connect(database=":memory:")
    return con.execute(f"SELECT * FROM read_parquet('{patron}', hive_partitioning=1)").fetchdf()


def construir_figura_temperatura(df_media_movil, ciudad):
    datos_ciudad = df_media_movil[df_media_movil["ciudad"] == ciudad].sort_values("fecha_hora_utc")
    figura = go.Figure()
    figura.add_trace(go.Scatter(
        x=datos_ciudad["fecha_hora_utc"], y=datos_ciudad["temperature_2m"],
        mode="lines", name="Temperatura horaria (C)", line=dict(width=1),
    ))
    figura.add_trace(go.Scatter(
        x=datos_ciudad["fecha_hora_utc"], y=datos_ciudad["media_movil_24h_c"],
        mode="lines", name="Media movil 24h (C)", line=dict(width=3),
    ))
    figura.update_layout(
        title=f"Temperatura horaria y media movil 24h - {ciudad}",
        xaxis_title="Fecha y hora (UTC)", yaxis_title="Temperatura (C)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return figura


def construir_figura_zscore(df_zscore, ciudad):
    datos_ciudad = df_zscore[df_zscore["ciudad"] == ciudad].sort_values("fecha_hora_utc")
    figura = go.Figure()
    figura.add_trace(go.Scatter(
        x=datos_ciudad["fecha_hora_utc"], y=datos_ciudad["z_score_temperatura"],
        mode="lines", name="Z-Score temperatura",
    ))
    figura.add_hline(y=2, line_dash="dash", line_color="red")
    figura.add_hline(y=-2, line_dash="dash", line_color="red")
    figura.update_layout(
        title=f"Z-Score horario de temperatura frente al historico - {ciudad}",
        xaxis_title="Fecha y hora (UTC)", yaxis_title="Z-Score",
    )
    return figura


def calcular_kpis(df_resumen_diario, ciudad):
    datos_ciudad = df_resumen_diario[df_resumen_diario["ciudad"] == ciudad].sort_values("fecha")
    if datos_ciudad.empty:
        return None
    ultimo_dia = datos_ciudad.iloc[-1]
    return {
        "fecha": ultimo_dia["fecha"],
        "temperatura_media_c": ultimo_dia["temperatura_media_c"],
        "temperatura_minima_c": ultimo_dia["temperatura_minima_c"],
        "temperatura_maxima_c": ultimo_dia["temperatura_maxima_c"],
        "precipitacion_total_mm": ultimo_dia["precipitacion_total_mm"],
        "viento_medio_kmh": ultimo_dia["viento_medio_kmh"],
    }


st.set_page_config(page_title="Climate Engine - Cuadro de mando", layout="wide")
st.title("Climate Engine - Cuadro de mando meteorologico")
st.caption(
    "Prueba tecnica individual - Data & BI - Francisco Maximo Ortega Calvo. "
    "Datos: capa Gold del pipeline (Open-Meteo, prediccion horaria a 14 dias)."
)

try:
    df_resumen_diario = _leer_tabla_gold("resumen_diario")
    df_media_movil = _leer_tabla_gold("media_movil_temp")
    df_zscore = _leer_tabla_gold("zscore_horario")
except Exception as error:  # noqa: BLE001
    st.error(
        "No se han encontrado datos en la capa Gold. Ejecuta antes el pipeline "
        f"(main.ipynb o `python cli.py --fase all`). Detalle: {error}"
    )
    st.stop()

if df_resumen_diario.empty:
    st.warning("La capa Gold esta vacia. Ejecuta el pipeline antes de abrir el dashboard.")
    st.stop()

ciudades = sorted(df_resumen_diario["ciudad"].unique().tolist())
ciudad_seleccionada = st.sidebar.selectbox("Ciudad", ciudades)

kpis = calcular_kpis(df_resumen_diario, ciudad_seleccionada)
if kpis:
    columnas_kpi = st.columns(5)
    columnas_kpi[0].metric("Temp. media (ultimo dia)", f"{kpis['temperatura_media_c']:.1f} C")
    columnas_kpi[1].metric("Temp. minima", f"{kpis['temperatura_minima_c']:.1f} C")
    columnas_kpi[2].metric("Temp. maxima", f"{kpis['temperatura_maxima_c']:.1f} C")
    columnas_kpi[3].metric("Precipitacion total", f"{kpis['precipitacion_total_mm']:.1f} mm")
    columnas_kpi[4].metric("Viento medio", f"{kpis['viento_medio_kmh']:.1f} km/h")

st.plotly_chart(construir_figura_temperatura(df_media_movil, ciudad_seleccionada), use_container_width=True)
st.plotly_chart(construir_figura_zscore(df_zscore, ciudad_seleccionada), use_container_width=True)

with st.expander("Resumen diario completo (todas las ciudades)"):
    st.dataframe(df_resumen_diario, use_container_width=True)
