"""
Servidor HTTP local que simula la API de Open-Meteo (mismo esquema JSON
publico y documentado que https://api.open-meteo.com/v1/forecast).

Uso:
- En los tests de pytest (ver conftest.py), como fixture para probar la
  logica de extraccion, bronce, plata y oro SIN depender de una conexion
  real a internet (buena practica: los tests unitarios deben ser
  deterministas y no dependen de red).
- Como utilidad de desarrollo en entornos sin salida a internet: se puede
  levantar manualmente con `python tests/mock_openmeteo_server.py <puerto>`
  y apuntar el pipeline a el con la variable de entorno
  CLIMATE_ENGINE_API_URL_OVERRIDE=http://127.0.0.1:<puerto>/v1/forecast

IMPORTANTE: los valores que sirve este servidor son sinteticos (generados
con una funcion deterministica, no aleatorios ni descargados), pensados
unicamente para validar la MECANICA del pipeline (esquemas, particionado,
calculo de metricas, idempotencia). No deben interpretarse como un
pronostico meteorologico real. Para datos reales, el pipeline debe
ejecutarse sin esta variable de entorno, contra la API oficial de
Open-Meteo, desde un entorno con salida a internet.
"""
import json
import math
import sys
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

FORECAST_DAYS_DEFECTO = 14


def _temperatura_base(lat):
    """Aproxima una temperatura base plausible segun la latitud (mas fria
    cuanto mas al norte), solo para dar forma realista a los datos de
    prueba deterministas."""
    return 26.0 - (lat - 37.0) * 0.9


def generar_cuerpo_openmeteo(lat, lon, forecast_days=FORECAST_DAYS_DEFECTO):
    """Genera un cuerpo JSON con la misma forma que la respuesta real de
    Open-Meteo (ver hourly_units / hourly), con series deterministas
    (variacion diurna senoidal + ligera variacion por hora, sin aleatoriedad)
    para que las pruebas sean reproducibles.
    """
    horas = forecast_days * 24
    inicio = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    tiempos = [(inicio + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M") for i in range(horas)]

    base_temp = _temperatura_base(float(lat))
    temperaturas = [
        round(base_temp + 6.0 * math.sin((i % 24) / 24 * 2 * math.pi - math.pi / 2) + (i // 24) * 0.05, 1)
        for i in range(horas)
    ]
    humedad = [
        round(60 + 20 * math.cos((i % 24) / 24 * 2 * math.pi), 1)
        for i in range(horas)
    ]
    precipitacion = [round(max(0.0, math.sin(i / 17.0)) * 0.8, 2) for i in range(horas)]
    viento = [round(8 + 4 * math.sin(i / 11.0) ** 2, 1) for i in range(horas)]
    presion = [round(1015 + 3 * math.sin(i / 29.0), 1) for i in range(horas)]

    return {
        "latitude": float(lat),
        "longitude": float(lon),
        "generationtime_ms": 0.15,
        "utc_offset_seconds": 0,
        "timezone": "GMT",
        "timezone_abbreviation": "GMT",
        "elevation": 650.0,
        "hourly_units": {
            "time": "iso8601",
            "temperature_2m": "°C",
            "relative_humidity_2m": "%",
            "precipitation": "mm",
            "wind_speed_10m": "km/h",
            "surface_pressure": "hPa",
        },
        "hourly": {
            "time": tiempos,
            "temperature_2m": temperaturas,
            "relative_humidity_2m": humedad,
            "precipitation": precipitacion,
            "wind_speed_10m": viento,
            "surface_pressure": presion,
        },
    }


class HandlerOpenMeteoMock(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # silencia el log de acceso HTTP por defecto

    def do_GET(self):
        parsed = urlparse(self.path)
        if not parsed.path.endswith("/forecast"):
            self.send_response(404)
            self.end_headers()
            return
        qs = parse_qs(parsed.query)
        try:
            lat = qs["latitude"][0]
            lon = qs["longitude"][0]
        except (KeyError, IndexError):
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error": true, "reason": "faltan latitude/longitude"}')
            return
        forecast_days = int(qs.get("forecast_days", [FORECAST_DAYS_DEFECTO])[0])
        cuerpo = generar_cuerpo_openmeteo(lat, lon, forecast_days)
        payload = json.dumps(cuerpo).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def iniciar_servidor(puerto=0):
    servidor = HTTPServer(("127.0.0.1", puerto), HandlerOpenMeteoMock)
    return servidor


if __name__ == "__main__":
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    servidor = iniciar_servidor(puerto)
    print(f"Servidor mock de Open-Meteo escuchando en http://127.0.0.1:{puerto}/v1/forecast")
    servidor.serve_forever()
