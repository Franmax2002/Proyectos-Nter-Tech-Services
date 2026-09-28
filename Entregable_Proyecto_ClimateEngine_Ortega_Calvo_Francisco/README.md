# Climate Engine

Plataforma de procesamiento y analitica meteorologica (Open-Meteo -> Bronze -> Silver -> Gold -> Dashboard). Prueba tecnica individual - Data & BI - Francisco Maximo Ortega Calvo.

## 1. Estructura del proyecto

```
Entregable_Proyecto_ClimateEngine_Ortega_Calvo_Francisco/
├── Memoria_Tecnica.docx        Memoria tecnica (formato corporativo Nter)
├── docker-compose.yml          Despliegue en contenedores (pipeline + dashboard)
├── Dockerfile                  Imagen de la aplicacion
├── requirements.txt            Dependencias del entorno virtual
├── config.yaml                 Configuracion centralizada (ciudades, API, umbrales, rutas)
├── pytest.ini                  Configuracion de pytest
├── cli.py                      Orquestador CLI (fases, ciudades, forzado de particiones)
├── README.md                   Este documento
├── climate_engine/             Modulos del pipeline, en notebooks .ipynb documentados
│   ├── main.ipynb                 Orquestador: encadena todos los modulos con %run
│   ├── config.ipynb               Configuracion centralizada (lee config.yaml)
│   ├── logging_config.ipynb       Configuracion del logger
│   ├── utils_catalogo.ipynb       Utilidades del catalogo de ciudades
│   ├── extract_openmeteo.ipynb    Extraccion resiliente de la API de Open-Meteo
│   ├── bronze_ingest.ipynb        Capa Bronze (persistencia cruda inmutable)
│   ├── silver_clean.ipynb         Capa Silver (esquema, calidad, particionado)
│   ├── gold_analytics.ipynb       Capa Gold (metricas analiticas con DuckDB)
│   └── visualize_dashboard.ipynb  Logica documentada del cuadro de mando
├── dashboard/
│   └── app.py                  Cuadro de mando Streamlit (entrypoint minimo, ver notas)
├── tests/                      Pruebas unitarias (pytest)
│   ├── conftest.py                 Arranca el servidor mock de Open-Meteo para los tests
│   ├── mock_openmeteo_server.py    Servidor HTTP local con el esquema real de Open-Meteo
│   ├── notebook_test_utils.py      Utilidad para ejecutar los notebooks reales en los tests
│   ├── test_catalogo.py
│   ├── test_schema_silver.py
│   ├── test_metricas_gold.py
│   └── test_extract_resiliencia.py
├── data/                        Almacenamiento por capas (se genera al ejecutar)
│   ├── bronze/ciudad=<Nombre>/fecha_ingesta=<AAAA-MM-DD>/lote_<id>.json
│   ├── silver/ciudad=<Nombre>/anio=<AAAA>/mes=<MM>/datos.parquet
│   │   └── _cuarentena/cuarentena.parquet   (acumulativo, nunca se trunca)
│   └── gold/{resumen_diario,media_movil_temp,zscore_horario}/ciudad=<Nombre>/datos.parquet
├── logs/
│   └── ejecucion_etl.log        Log de la ultima ejecucion (se sobreescribe)
└── .venv/                       Entorno virtual Python (no se versiona / no se entrega)
```

## 2. Requisitos previos

- Python 3.10 o superior (probado con 3.11).
- Docker y Docker Compose (opcional, para despliegue en contenedores).
- VS Code con la extension de Jupyter (recomendado, para abrir los `.ipynb` de forma interactiva).

## 3. Puesta en marcha

1) Crear el entorno virtual e instalar dependencias:

```
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m ipykernel install --user --name climate_engine --display-name "Python (climate_engine)"
```

2) Ejecutar el pipeline completo. Dos formas equivalentes:

   - Interactiva: abrir `climate_engine/main.ipynb` en VS Code/Jupyter, elegir el kernel "Python (climate_engine)" y "Restart + Run All".
   - Por linea de comandos:
     ```
     python cli.py --fase all
     ```

3) Verificar el resultado:
   - `logs/ejecucion_etl.log` debe terminar con "EJECUCION FINALIZADA CORRECTAMENTE."
   - Deben existir ficheros `.parquet` en `data/gold/resumen_diario/`, `data/gold/media_movil_temp/` y `data/gold/zscore_horario/`, uno por ciudad.
   - Con la API real de Open-Meteo, cada ciudad debe tener 336 registros horarios (14 dias x 24 horas).

4) Abrir el cuadro de mando:

```
streamlit run dashboard/app.py
```

y visitar http://localhost:8501

## 4. Uso del CLI (ejecucion selectiva)

```
python cli.py --fase all                                   # pipeline completo, todas las ciudades
python cli.py --fase bronze --ciudad Madrid --ciudad Sevilla  # solo extraccion+Bronze, ciudades concretas
python cli.py --fase silver                                 # solo Silver, sobre el ultimo Bronze ya existente
python cli.py --fase silver --forzar-particiones             # Silver, reescribiendo particiones desde cero
python cli.py --fase gold                                    # solo recalculo de las tablas Gold
python cli.py --help                                          # ayuda completa de opciones
```

## 5. Despliegue en contenedores

```
docker compose run --rm pipeline                              # pipeline completo
docker compose run --rm pipeline --fase bronze --ciudad Madrid  # fase/ciudad concretas
docker compose up dashboard                                    # cuadro de mando en http://localhost:8501
```

## 6. Notas importantes

- **Entorno de desarrollo sin salida a internet**: este proyecto se ha desarrollado en un entorno sandbox sin acceso a la red publica (el proxy de red bloquea `api.open-meteo.com`). Todo el codigo esta escrito para funcionar contra la API real sin ningun cambio; para las pruebas y la ejecucion de demostracion incluidas en este entregable se ha usado `tests/mock_openmeteo_server.py`, un servidor HTTP local que sirve el mismo esquema JSON publico y documentado de Open-Meteo, con datos sinteticos deterministas (nunca aleatorios). `config.ipynb` respeta la variable de entorno `CLIMATE_ENGINE_API_URL_OVERRIDE` precisamente para esto; en un entorno con salida a internet normal, el pipeline funciona igual sin definir esa variable, contra `https://api.open-meteo.com/v1/forecast`. Los datos ya presentes en `data/` en este entregable, y las cifras impresas en las celdas de "Prueba rapida" de los notebooks, proceden de ese mock de desarrollo, no de un pronostico real; para obtener datos reales, borrar `data/`, `logs/ejecucion_etl.log` y ejecutar el pipeline en un entorno con conexion a internet (ver seccion 7).
- **FALLBACK sin datos inventados**: si la API no responde tras los reintentos, el pipeline usa como respaldo el ultimo lote Bronze REAL guardado para esa ciudad (nunca un valor sintetico). Si tampoco existe ningun lote previo, la ciudad se omite en esa ejecucion y queda registrado como error en el log.
- **"Historico cargado" del Z-Score**: Open-Meteo `/v1/forecast` sirve prediccion, no un registro historico externo verificable sin conexion. El Z-Score se calcula frente a toda la serie ya acumulada en Silver para esa ciudad (crece con cada ejecucion real). Ver la celda de decision de diseno en `gold_analytics.ipynb`.
- **Repeticion de las "pruebas rapidas" al encadenar modulos**: siguiendo la convencion de que cada notebook es autocontenible y ejecutable de forma independiente, cada modulo, al ser encadenado con `%run` por otro modulo o por `main.ipynb`/`cli.py`, ejecuta tambien su propia celda de "Prueba rapida" (con el catalogo completo de ciudades). Esto es intencional y es la razon por la que una ejecucion de `main.ipynb` puede generar varios lotes Bronze en la misma corrida: no afecta al resultado final (la capa Silver es idempotente) y queda todo trazado en el log.
- **`cli.py` y `dashboard/app.py` son ficheros `.py`, no `.ipynb`**: son las dos unicas excepciones a "todo el codigo va en notebooks", y son tecnicas, no de diseño: `argparse`/`click` necesitan leer `sys.argv` de una invocacion real de terminal, y `streamlit run` necesita un script que se re-ejecuta de arriba a abajo en cada interaccion del usuario. Ambos son envoltorios minimos; la logica de negocio esta documentada en los notebooks de `climate_engine/`. Ver la celda de decision de diseno al inicio de `main.ipynb` y de `visualize_dashboard.ipynb`.
- **Rango de `surface_pressure`**: el enunciado no fija un rango explicito. Se usa `[850.0, 1085.0] hPa` (configurable en `config.yaml`), con margen suficiente para la Peninsula Iberica.

## 7. Reiniciar desde cero

```
rm -rf data/bronze/* data/silver/* data/gold/* logs/*.log
docker compose down -v          # si se ha usado Docker
```

y volver a ejecutar el pipeline (paso 2 de la seccion 3), sin definir `CLIMATE_ENGINE_API_URL_OVERRIDE`, en un entorno con salida a internet real.

## 8. Resolucion de problemas frecuentes

| Sintoma | Causa habitual | Solucion |
|---|---|---|
| El pipeline registra `SIN_DATOS` para todas las ciudades | No hay salida a internet y no existe ningun lote Bronze previo | Comprobar la conexion, o definir `CLIMATE_ENGINE_API_URL_OVERRIDE` apuntando a `tests/mock_openmeteo_server.py` para probar la mecanica del pipeline sin red |
| `jupyter-nbconvert: command not found` o error al ejecutar `%run` | Falta el kernel `climate_engine` o falta `nbclient`/`ipykernel` en el entorno | Reinstalar `requirements.txt` y volver a registrar el kernel: `python -m ipykernel install --user --name climate_engine` |
| `pytest` falla al arrancar con `PluginValidationError` sobre `importnb` | La libreria `importnb` (usada solo por `dashboard/app.py`) registra un plugin de pytest incompatible con la version de pytest instalada | Ya mitigado en `pytest.ini` (`addopts = -p no:importnb`); si persiste, ejecutar `pytest -p no:importnb` |
| El dashboard muestra "No se han encontrado datos en la capa Gold" | Todavia no se ha ejecutado el pipeline | Ejecutar `python cli.py --fase all` (o `main.ipynb`) antes de abrir el dashboard |
| Cifras ligeramente distintas entre ejecuciones sucesivas en el mismo dia | El mock de desarrollo genera la ventana horaria a partir de la hora actual; con la API real, Open-Meteo actualiza su prediccion de forma similar | Comportamiento esperado; la idempotencia se mide en filas por `(ciudad, fecha_hora_utc)`, no en que el valor de un pronostico no cambie de una hora a otra |
| `docker build` falla por falta de red | El entorno de build no tiene salida a internet (para descargar la imagen base o las dependencias) | Ejecutar el build en un entorno con conexion a internet normal |
