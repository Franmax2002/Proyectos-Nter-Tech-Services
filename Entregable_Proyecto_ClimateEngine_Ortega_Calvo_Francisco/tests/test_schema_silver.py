"""
Pruebas del contrato de calidad de datos de la capa Silver
(climate_engine/silver_clean.ipynb).

Cubren el requisito del enunciado: "el rechazo intencionado de registros
corruptos en el esquema" y el requisito funcional 2 ("Contrato de Calidad
de Datos: no se permite la escritura en disco de registros que no pasen
la validacion estricta del esquema").
"""
from notebook_test_utils import ejecutar_notebook_con_celdas_extra

NOTEBOOK = "climate_engine/silver_clean.ipynb"

CONSTRUIR_DATAFRAME_PRUEBA = '''
import pandas as pd

def _fila_base(**overrides):
    fila = {
        "ciudad": "Madrid",
        "fecha_hora_utc": "2026-01-01T00:00",
        "temperature_2m": 20.0,
        "relative_humidity_2m": 55.0,
        "precipitation": 0.0,
        "wind_speed_10m": 12.0,
        "surface_pressure": 1013.0,
        "id_lote": "lote_test",
        "origen": "API",
        "timestamp_ingesta_utc": "2026-01-01T00:00:00+00:00",
    }
    fila.update(overrides)
    return fila
'''


def test_registros_validos_pasan_el_esquema():
    ejecutar_notebook_con_celdas_extra(NOTEBOOK, [
        CONSTRUIR_DATAFRAME_PRUEBA,
        (
            "df_prueba = pd.DataFrame([_fila_base(), _fila_base(fecha_hora_utc='2026-01-01T01:00')])\n"
            "df_validos, df_cuarentena = validar_y_separar(df_prueba)\n"
            "assert len(df_validos) == 2\n"
            "assert len(df_cuarentena) == 0"
        ),
    ])


def test_temperatura_fuera_de_rango_cae_en_cuarentena():
    ejecutar_notebook_con_celdas_extra(NOTEBOOK, [
        CONSTRUIR_DATAFRAME_PRUEBA,
        (
            "df_prueba = pd.DataFrame([_fila_base(), _fila_base(fecha_hora_utc='2026-01-01T01:00', temperature_2m=999.0)])\n"
            "df_validos, df_cuarentena = validar_y_separar(df_prueba)\n"
            "assert len(df_validos) == 1\n"
            "assert len(df_cuarentena) == 1\n"
            "assert 'temperature_2m' in df_cuarentena.iloc[0]['motivo_rechazo']"
        ),
    ])


def test_humedad_fuera_de_rango_cae_en_cuarentena():
    ejecutar_notebook_con_celdas_extra(NOTEBOOK, [
        CONSTRUIR_DATAFRAME_PRUEBA,
        (
            "df_prueba = pd.DataFrame([_fila_base(relative_humidity_2m=150.0)])\n"
            "df_validos, df_cuarentena = validar_y_separar(df_prueba)\n"
            "assert len(df_validos) == 0\n"
            "assert len(df_cuarentena) == 1"
        ),
    ])


def test_precipitacion_negativa_cae_en_cuarentena():
    ejecutar_notebook_con_celdas_extra(NOTEBOOK, [
        CONSTRUIR_DATAFRAME_PRUEBA,
        (
            "df_prueba = pd.DataFrame([_fila_base(precipitation=-1.0)])\n"
            "df_validos, df_cuarentena = validar_y_separar(df_prueba)\n"
            "assert len(df_validos) == 0\n"
            "assert len(df_cuarentena) == 1"
        ),
    ])


def test_ciudad_fuera_de_catalogo_cae_en_cuarentena():
    ejecutar_notebook_con_celdas_extra(NOTEBOOK, [
        CONSTRUIR_DATAFRAME_PRUEBA,
        (
            "df_prueba = pd.DataFrame([_fila_base(ciudad='CiudadInventada')])\n"
            "df_validos, df_cuarentena = validar_y_separar(df_prueba)\n"
            "assert len(df_validos) == 0\n"
            "assert len(df_cuarentena) == 1"
        ),
    ])


def test_registros_en_cuarentena_nunca_se_pierden_ni_se_mezclan_con_validos():
    ejecutar_notebook_con_celdas_extra(NOTEBOOK, [
        CONSTRUIR_DATAFRAME_PRUEBA,
        (
            "filas = [_fila_base(fecha_hora_utc=f'2026-01-01T{h:02d}:00') for h in range(5)]\n"
            "filas[2]['temperature_2m'] = -999.0\n"
            "filas[4]['wind_speed_10m'] = -5.0\n"
            "df_prueba = pd.DataFrame(filas)\n"
            "df_validos, df_cuarentena = validar_y_separar(df_prueba)\n"
            "assert len(df_prueba) == len(df_validos) + len(df_cuarentena), (\n"
            "    'Ningun registro debe perderse: total_entrada == validos + cuarentena'\n"
            ")\n"
            "assert len(df_cuarentena) == 2\n"
            "assert len(df_validos) == 3"
        ),
    ])
