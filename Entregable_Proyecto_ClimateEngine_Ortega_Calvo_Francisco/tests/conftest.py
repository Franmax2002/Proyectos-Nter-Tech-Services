"""
Configuracion comun de pytest para Climate Engine.

Levanta un servidor HTTP local que simula la API de Open-Meteo (mismo
esquema JSON documentado que la API real, ver mock_openmeteo_server.py) y
apunta el pipeline hacia el para toda la sesion de tests, via la variable
de entorno CLIMATE_ENGINE_API_URL_OVERRIDE que ya soporta config.ipynb.

Esto es imprescindible porque varios notebooks (silver_clean.ipynb,
gold_analytics.ipynb) encadenan con %run a bronze_ingest.ipynb, que a su
vez ejecuta de verdad su celda de "Prueba rapida" (una ingesta real) cada
vez que se ejecutan como dependencia. Sin este mock, los tests unitarios
dependerian de tener salida a internet real, lo cual va en contra de la
buena practica exigida por el enunciado (pruebas deterministas,
reproducibles en cualquier entorno, incluido un pipeline de CI sin red).
"""
import os
import sys
import threading

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from mock_openmeteo_server import iniciar_servidor  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def servidor_mock_openmeteo():
    servidor = iniciar_servidor(0)
    puerto = servidor.server_address[1]
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()

    url = f"http://127.0.0.1:{puerto}/v1/forecast"
    valor_previo = os.environ.get("CLIMATE_ENGINE_API_URL_OVERRIDE")
    os.environ["CLIMATE_ENGINE_API_URL_OVERRIDE"] = url

    yield url

    if valor_previo is None:
        os.environ.pop("CLIMATE_ENGINE_API_URL_OVERRIDE", None)
    else:
        os.environ["CLIMATE_ENGINE_API_URL_OVERRIDE"] = valor_previo
    servidor.shutdown()
