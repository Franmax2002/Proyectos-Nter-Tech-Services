"""
Pruebas del catalogo de ubicaciones (climate_engine/utils_catalogo.ipynb).

Cubren el requisito del enunciado: "Cobertura minima de pruebas unitarias
que verifiquen las coordenadas del catalogo [...]".
"""
from notebook_test_utils import ejecutar_notebook_con_celdas_extra

NOTEBOOK = "climate_engine/utils_catalogo.ipynb"


def test_catalogo_incluye_las_cinco_ciudades_obligatorias():
    ejecutar_notebook_con_celdas_extra(NOTEBOOK, [
        "obligatorias = {'Madrid', 'Barcelona', 'Valencia', 'Sevilla', 'Bilbao'}\n"
        "assert obligatorias.issubset(set(UBICACIONES.keys())), (\n"
        "    f'Faltan ciudades obligatorias: {obligatorias - set(UBICACIONES.keys())}'\n"
        ")"
    ])


def test_validar_catalogo_minimo_no_lanza_excepcion():
    ejecutar_notebook_con_celdas_extra(NOTEBOOK, [
        "assert validar_catalogo_minimo() is True"
    ])


def test_coordenadas_del_catalogo_caen_en_peninsula():
    ejecutar_notebook_con_celdas_extra(NOTEBOOK, [
        "df = catalogo_como_dataframe()\n"
        "assert df['en_peninsula'].all(), (\n"
        "    f\"Ciudades del catalogo fuera de la Peninsula: {df[~df['en_peninsula']]['ciudad'].tolist()}\"\n"
        ")\n"
        "assert len(df) >= 5"
    ])


def test_coordenadas_conocidas_fuera_de_peninsula_se_detectan_como_tales():
    # Verifica que la funcion de validacion realmente distingue dentro/fuera,
    # y no siempre devuelve True (comprobacion del propio test de coordenadas). 
    ejecutar_notebook_con_celdas_extra(NOTEBOOK, [
        "assert coordenadas_en_peninsula(40.4168, -3.7038) is True   # Madrid\n"
        "assert coordenadas_en_peninsula(28.4636, -16.2518) is False  # Tenerife (Canarias)\n"
        "assert coordenadas_en_peninsula(48.8566, 2.3522) is False    # Paris"
    ])


def test_catalogo_minimo_falla_si_falta_una_ciudad_obligatoria():
    # Rechazo intencionado: un catalogo incompleto debe hacer fallar la validacion.
    ejecutar_notebook_con_celdas_extra(NOTEBOOK, [
        "catalogo_incompleto = dict(UBICACIONES)\n"
        "catalogo_incompleto.pop('Bilbao')\n"
        "fallo_detectado = False\n"
        "try:\n"
        "    validar_catalogo_minimo(catalogo_incompleto)\n"
        "except AssertionError:\n"
        "    fallo_detectado = True\n"
        "assert fallo_detectado, 'Un catalogo sin Bilbao deberia fallar la validacion minima.'"
    ])
