"""
Pruebas de consistencia matematica de las metricas de la capa Gold
(climate_engine/gold_analytics.ipynb).

Cubren el requisito del enunciado: "la consistencia matematica de las
metricas generadas" (resumen diario, media movil de 24h y Z-Score
horario), comparando el resultado de las funciones reales del modulo
contra un calculo manual de referencia sobre una serie sintetica de
valores conocidos.

La serie de prueba se escribe temporalmente en una ciudad ficticia
("_CiudadPruebaPytest") dentro de la propia capa Silver real, se consulta
con las funciones reales de Gold, y se elimina al finalizar el test
(no debe quedar rastro en el entregable final).
"""
from notebook_test_utils import ejecutar_notebook_con_celdas_extra

NOTEBOOK = "climate_engine/gold_analytics.ipynb"

PREPARAR_SERIE_SINTETICA = '''
import shutil
import pandas as pd

CIUDAD_PRUEBA_PYTEST = "_CiudadPruebaPytest"

horas = pd.date_range("2026-02-01", periods=48, freq="h")
temperaturas = [10.0 + (i % 24) * 0.5 for i in range(48)]  # patron conocido y determinista

df_prueba = pd.DataFrame({
    "ciudad": CIUDAD_PRUEBA_PYTEST,
    "fecha_hora_utc": horas,
    "temperature_2m": temperaturas,
    "relative_humidity_2m": 50.0,
    "precipitation": 1.0,
    "wind_speed_10m": 5.0,
    "surface_pressure": 1013.0,
    "id_lote": "test_pytest",
    "origen": "API",
    "timestamp_ingesta_utc": "2026-02-01T00:00:00+00:00",
})

_directorio_prueba = RUTA_SILVER / f"ciudad={CIUDAD_PRUEBA_PYTEST}" / "anio=2026" / "mes=02"
_directorio_prueba.mkdir(parents=True, exist_ok=True)
df_prueba.to_parquet(_directorio_prueba / "datos.parquet", index=False)
'''

LIMPIAR_SERIE_SINTETICA = (
    "shutil.rmtree(RUTA_SILVER / f'ciudad={CIUDAD_PRUEBA_PYTEST}', ignore_errors=True)"
)


def test_resumen_diario_coincide_con_calculo_manual():
    ejecutar_notebook_con_celdas_extra(NOTEBOOK, [
        PREPARAR_SERIE_SINTETICA,
        (
            "try:\n"
            "    resumen = calcular_resumen_diario()\n"
            "    fila = resumen[resumen['ciudad'] == CIUDAD_PRUEBA_PYTEST].sort_values('fecha')\n"
            "    assert len(fila) == 2, f'Se esperaban 2 dias completos, hay {len(fila)}'\n"
            "    esperado_dia1 = sum(temperaturas[:24]) / 24\n"
            "    obtenido_dia1 = fila.iloc[0]['temperatura_media_c']\n"
            "    assert abs(obtenido_dia1 - esperado_dia1) < 1e-9, (obtenido_dia1, esperado_dia1)\n"
            "    assert fila.iloc[0]['temperatura_minima_c'] == min(temperaturas[:24])\n"
            "    assert fila.iloc[0]['temperatura_maxima_c'] == max(temperaturas[:24])\n"
            "    assert abs(fila.iloc[0]['precipitacion_total_mm'] - 24.0) < 1e-9\n"
            "finally:\n"
            f"    {LIMPIAR_SERIE_SINTETICA}"
        ),
    ])


def test_media_movil_24h_coincide_con_pandas_rolling():
    ejecutar_notebook_con_celdas_extra(NOTEBOOK, [
        PREPARAR_SERIE_SINTETICA,
        (
            "try:\n"
            "    media_movil = calcular_media_movil_temperatura()\n"
            "    serie = media_movil[media_movil['ciudad'] == CIUDAD_PRUEBA_PYTEST].sort_values('fecha_hora_utc')\n"
            "    manual = pd.Series(temperaturas).rolling(window=24, min_periods=1).mean()\n"
            "    obtenido = serie['media_movil_24h_c'].reset_index(drop=True)\n"
            "    assert (obtenido.round(6) == manual.round(6)).all(), (\n"
            "        list(zip(obtenido.round(6), manual.round(6)))\n"
            "    )\n"
            "finally:\n"
            f"    {LIMPIAR_SERIE_SINTETICA}"
        ),
    ])


def test_zscore_tiene_media_cero_y_desviacion_uno_sobre_su_propio_historico():
    ejecutar_notebook_con_celdas_extra(NOTEBOOK, [
        PREPARAR_SERIE_SINTETICA,
        (
            "try:\n"
            "    zscore = calcular_zscore_horario()\n"
            "    serie = zscore[zscore['ciudad'] == CIUDAD_PRUEBA_PYTEST]\n"
            "    media_z = serie['z_score_temperatura'].mean()\n"
            "    std_z = serie['z_score_temperatura'].std(ddof=0)\n"
            "    assert abs(media_z) < 1e-9, f'Media del z-score deberia ser ~0, es {media_z}'\n"
            "    assert abs(std_z - 1.0) < 1e-6, f'Desviacion del z-score deberia ser ~1, es {std_z}'\n"
            "    fila_mas_fria = serie.loc[serie['temperature_2m'].idxmin()]\n"
            "    assert fila_mas_fria['z_score_temperatura'] < 0, 'La hora mas fria debe tener z-score negativo'\n"
            "finally:\n"
            f"    {LIMPIAR_SERIE_SINTETICA}"
        ),
    ])
