"""
Prueba del patron de resiliencia e ingesta resiliente
(climate_engine/extract_openmeteo.ipynb / bronze_ingest.ipynb).

Cubre el requisito funcional 1 del enunciado ("Ingesta Resiliente") en su
vertiente de FALLBACK: si la API no responde tras los reintentos, el
pipeline debe recurrir al ultimo lote Bronze real disponible en lugar de
inventar datos o detenerse.
"""
from notebook_test_utils import ejecutar_notebook_con_celdas_extra

NOTEBOOK = "climate_engine/bronze_ingest.ipynb"


def test_fallback_usa_el_ultimo_bronze_real_cuando_la_api_no_responde():
    ejecutar_notebook_con_celdas_extra(NOTEBOOK, [
        (
            # 1) Ingesta real (contra el mock) para dejar un lote Bronze de referencia.
            "sesion_ok = crear_sesion_resiliente()\n"
            "coords = UBICACIONES['Madrid']\n"
            "cuerpo_ok, origen_ok = obtener_datos_ciudad(sesion_ok, 'Madrid', coords['lat'], coords['lon'])\n"
            "assert origen_ok == 'API', f'Se esperaba origen API con el mock activo, se obtuvo {origen_ok}'\n"
            "guardar_bronze('Madrid', cuerpo_ok, 'API', 'lote_referencia_test', '2026-01-01T00:00:00+00:00')\n"
        ),
        (
            # 2) Se simula que la API deja de responder (URL invalida) y se
            #    comprueba que se recurre al ultimo Bronze real, no a datos inventados.
            "url_original = API_URL_BASE\n"
            "try:\n"
            "    API_URL_BASE = 'http://127.0.0.1:1/v1/forecast'  # puerto sin servicio: fallo garantizado\n"
            "    cuerpo_fallback, origen_fallback = obtener_datos_ciudad(sesion_ok, 'Madrid', coords['lat'], coords['lon'])\n"
            "    assert origen_fallback == 'FALLBACK', f'Se esperaba FALLBACK, se obtuvo {origen_fallback}'\n"
            "    assert cuerpo_fallback['hourly']['time'] == cuerpo_ok['hourly']['time'], (\n"
            "        'El FALLBACK debe ser el ultimo dato REAL guardado, no uno distinto o inventado.'\n"
            "    )\n"
            "finally:\n"
            "    API_URL_BASE = url_original"
        ),
    ], timeout=60)


def test_sin_bronze_previo_y_sin_api_no_inventa_datos():
    ejecutar_notebook_con_celdas_extra(NOTEBOOK, [
        (
            "sesion_sin_datos = crear_sesion_resiliente()\n"
            "url_original = API_URL_BASE\n"
            "try:\n"
            "    API_URL_BASE = 'http://127.0.0.1:1/v1/forecast'\n"
            "    cuerpo, origen = obtener_datos_ciudad(sesion_sin_datos, 'CiudadSinHistorialPytest', -3.70, 40.42)\n"
            "    assert origen == 'SIN_DATOS'\n"
            "    assert cuerpo is None, 'Sin API y sin Bronze previo, no debe devolverse ningun dato inventado.'\n"
            "finally:\n"
            "    API_URL_BASE = url_original"
        ),
    ], timeout=60)
