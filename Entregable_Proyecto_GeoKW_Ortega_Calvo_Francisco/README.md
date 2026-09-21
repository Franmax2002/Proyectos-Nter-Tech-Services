# Proyecto GeoKW - Indice de Oportunidad de Inversion (IOI) en Sevilla

Sistema modular de Ingenieria de Datos Espaciales que integra los 11 distritos de Sevilla (geometria), los puntos de recarga de vehiculo electrico (API REST) y variables socioeconomicas oficiales (INE / Ayuntamiento), calcula el **Indice de Oportunidad de Inversion (IOI)** por distrito y lo representa en un visor cartografico interactivo.

Prueba tecnica individual - Data & BI - **Francisco Maximo Ortega Calvo**

---

## Estructura del proyecto

Mismo patron que el proyecto GeoStat: un paquete de **notebooks-modulo** dentro de `geokw_etl/` (uno por responsabilidad, documentado en markdown y con sus propias celdas de prueba), con `main.ipynb` como punto de entrada que los encadena con `%run` y ejecuta el pipeline completo.

```
Entregable_Proyecto_GeoKW_Ortega_Calvo_Francisco/
|-- Memoria_Tecnica.docx
|-- requirements.txt               Dependencias Python del entorno virtual
|-- main.ipynb                     Punto de entrada: encadena los modulos (%run) y ejecuta el pipeline
|-- geokw_etl/                     Notebooks-modulo del pipeline
|   |-- config.ipynb               Parametros, rutas y tabla maestra socioeconomica (data seeding)
|   |-- logging_config.ipynb       Configuracion centralizada del logging
|   |-- extract_distritos.ipynb    Carga y validacion del GeoJSON de distritos (IDE Sevilla)
|   |-- extract_socioeconomico.ipynb  Tabla maestra de poblacion y renta por distrito
|   |-- extract_cargadores.ipynb   Extraccion resiliente de puntos de recarga (Open Charge Map + fallback)
|   |-- transform_geoprocessing.ipynb Spatial join puntos-distritos y agregacion de potencia
|   |-- transform_kpis.ipynb       Densidad energetica, normalizacion min-max, IOI
|   |-- visualize_mapa.ipynb       Visor cartografico Folium (los 5 requisitos UX/UI)
|   `-- pipeline.ipynb             Orquestador ejecutar_pipeline()
|-- data/
|   |-- distritos_sevilla.geojson  Poligonos de los 11 distritos (descarga directa, portal IDE Sevilla)
|   `-- 31205.xlsx                 Excel oficial del INE (Atlas de Distribucion de Renta), fuente de RENTA_DISTRITOS
|-- output/
|   |-- mapa_sevilla.html          Visor cartografico generado por el pipeline
|   `-- estaciones_carga.csv       Tabla de todas las estaciones (validas + cuarentena), con distrito y estado
|-- logs/
|   `-- ejecucion_etl.log          Log de la ultima ejecucion (se sobreescribe cada corrida; sin tildes a proposito)
`-- .venv/                         Entorno virtual Python
```

No hay base de datos en este proyecto (a diferencia de GeoStat): todo el procesamiento ocurre en memoria con GeoPandas/Pandas y el resultado final es el propio mapa HTML - no hace falta Docker.

## Requisitos previos

- **Python 3.10+**
- **VS Code** con las extensiones Python + Jupyter (o Jupyter Notebook/Lab)
- Conexion a internet para la llamada real a la API de Open Charge Map (opcional - sin ella, el pipeline usa el dataset de respaldo interno y funciona igual)

## Puesta en marcha

### 1. Entorno virtual Python

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Clave de la API de Open Charge Map - ya configurada

Open Charge Map **exige** clave cuando se piden mas de 250 resultados (aqui se piden hasta 1000, `API_MAX_RESULTADOS` en `config.ipynb`). El proyecto ya trae una clave real y funcional como valor por defecto, directamente en el codigo - no hace falta hacer nada para que funcione:

```python
# geokw_etl/config.ipynb
API_KEY_OPENCHARGEMAP = os.environ.get("OCM_API_KEY", "b42f5cc2-f5b2-43a2-b17d-e4b85ea166cb")
```

Si prefieres usar tu propia clave (gratuita, en https://openchargemap.org/site/profile/applications), tienes dos opciones: cambiar directamente ese valor por defecto, o sobreescribirla con una variable de entorno **antes de arrancar el kernel de Jupyter** - ver la tabla de problemas frecuentes, es facil hacerlo mal sin darse cuenta.

### 3. Ejecutar el pipeline

1. Abre `main.ipynb` en VS Code (raiz del proyecto, al mismo nivel que `geokw_etl/`).
2. Selecciona como kernel el interprete de `.venv`.
3. *Kernel -> Restart* y despues *Run All*.

La seccion 1 encadena los 9 notebooks-modulo con `%run` - veras la salida de la prueba interna de cada uno (normalizacion de nombres de distrito, la llamada real a la API, el spatial join sobre datos reales...). Luego el pipeline se ejecuta de verdad y genera el mapa.

### 4. Ver el resultado

Abre `output/mapa_sevilla.html` en cualquier navegador. La seccion 4 de `main.ipynb` tambien verifica automaticamente que los 5 requisitos de diseno del visor estan presentes en el HTML generado.

Ademas del mapa, `main.ipynb` genera `output/estaciones_carga.csv`: una tabla plana con las 533 estaciones (nombre, distrito, lat, lon, potencia_kw, estado), incluyendo tanto las 352 validas (con su distrito real) como las 181 en cuarentena (marcadas como "Fuera de distrito") - util para revisar el detalle completo en Excel sin depender del mapa.

## Resultado con la API en vivo (estado definitivo del proyecto)

Con la clave real integrada, la ultima ejecucion completa obtuvo, dentro del radio de 20 km de Sevilla:

| Concepto | Cantidad |
|---|---|
| Puntos de recarga totales devueltos por la API | 533 |
| Puntos dentro de los 11 distritos oficiales (validos) | 352 |
| Puntos fuera de los 11 distritos (cuarentena espacial) | 181 |

Los 181 puntos en cuarentena (municipios colindantes como Dos Hermanas, Alcala de Guadaira, San Juan de Aznalfarache, Tomares, o la Isla de la Cartuja) **no se dibujan en el mapa**: el visor solo representa los 352 puntos dentro del ambito de decision comercial (los 11 distritos), aunque los 181 quedan registrados en el log y en el DataFrame de cuarentena para trazabilidad. Sin clave o sin internet, el pipeline usa el dataset de respaldo interno (31 puntos reales conocidos, solo dentro de la capital, sin necesidad de cuarentena en la practica).

## Diagnosticar diferencias en el numero de estaciones entre ejecuciones

Open Charge Map es una base de datos colaborativa en vivo (altas, bajas y verificaciones de puntos ocurren todos los dias), asi que dos ejecuciones en fechas distintas pueden devolver totales distintos de forma legitima - eso no es un fallo del pipeline. Cada punto trae un campo `DateCreated` con la fecha exacta de alta en la base de datos, que se puede consultar asi:

```python
import pandas as pd

respuesta = requests.get(API_OPENCHARGEMAP_URL, params={
    "output": "json", "countrycode": "ES",
    "latitude": SEVILLA_CENTRO_LAT, "longitude": SEVILLA_CENTRO_LON,
    "distance": RADIO_KM, "distanceunit": "KM",
    "maxresults": API_MAX_RESULTADOS, "compact": "true", "verbose": "false",
    "key": API_KEY_OPENCHARGEMAP,
}, headers={"User-Agent": USER_AGENT_API, "Accept": "application/json"})

cuerpo = respuesta.json()
fechas = pd.DataFrame([
    {"nombre": (poi.get("AddressInfo") or {}).get("Title"), "fecha_creacion": poi.get("DateCreated")}
    for poi in cuerpo
])
fechas["fecha_creacion"] = pd.to_datetime(fechas["fecha_creacion"])

recientes = fechas[fechas["fecha_creacion"] >= pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=4)]
print(f"Estaciones dadas de alta en los ultimos 4 dias: {len(recientes)}")
print(recientes.sort_values("fecha_creacion", ascending=False).to_string(index=False))
```

Esto es un script de diagnostico puntual, no forma parte del pipeline (`extract_cargadores.ipynb` no guarda `DateCreated` en `ESTACIONES_FALLBACK` ni en el resultado final, solo nombre/lat/lon/potencia_kw).

**Importante para interpretar el resultado**: sirve para explicar diferencias *pequenas* (unas pocas estaciones) entre ejecuciones cercanas en el tiempo. Una diferencia de decenas o cientos de estaciones entre dos ejecuciones (p. ej. 350 frente a 533) casi nunca se debe a altas reales en la base de datos - ese ritmo no es realista para una sola ciudad en pocos dias. Lo primero que hay que revisar en ese caso es la configuracion: si `API_KEY_OPENCHARGEMAP` estaba realmente cargada (ver la fila de la variable de entorno en la tabla de problemas frecuentes) y el valor de `API_MAX_RESULTADOS`, no la fecha de alta de las estaciones.

## Notas importantes

- **Los tres KPIs**: Densidad Energetica (`(potencia_total_kw / poblacion) * 10.000`), normalizacion min-max de renta y densidad (`[0,1]` sobre los 11 distritos), e IOI (`(renta_norm * (1 - densidad_norm)) * 100`, `[0,100]`) - implementados en `transform_kpis.ipynb`, cada formula con su celda de prueba.
- **Resiliencia de la API**: `extract_cargadores.ipynb` reintenta la conexion a Open Charge Map hasta 3 veces; si falla (o el cuerpo de la respuesta no tiene el formato esperado), activa automaticamente `ESTACIONES_FALLBACK` sin detener el pipeline - mismo patron que la API de demografia en GeoStat. Envia un `User-Agent` propio (`USER_AGENT_API`) porque Open Charge Map bloquea con `403` los User-Agent genericos de libreria.
- **Cuarentena espacial**: el *spatial join* separa los puntos dentro y fuera de los 11 distritos - igual que `tb_cuarentena_geodatos` en GeoStat, pero aqui los puntos en cuarentena no se representan visualmente en el mapa (ver tabla de arriba).
- **Los mensajes del log van sin tildes a proposito**, igual que en GeoStat, para evitar problemas de codificacion entre entornos.
- **Datos socioeconomicos reales, no estimados**: la poblacion (697.233 hab., suma exacta del Padron) sale del *Informe Socioeconomico de Sevilla 2023* del Ayuntamiento; la renta media neta por persona sale directamente del Excel oficial del INE incluido en `data/31205.xlsx` (tabla `31205`, *Atlas de Distribucion de Renta de los Hogares*, ano 2023), filtrado a los 11 distritos - el proceso de filtrado esta documentado y reproducido en `extract_socioeconomico.ipynb`.

## Reejecutar desde cero

El pipeline no tiene estado persistente entre corridas (no hay base de datos): basta con volver a ejecutar `main.ipynb`. Cada ejecucion sobrescribe `output/mapa_sevilla.html`, `output/estaciones_carga.csv` y `logs/ejecucion_etl.log`.

## Resolucion de problemas frecuentes

| Sintoma | Causa habitual | Solucion |
|---|---|---|
| El origen sale `FALLBACK` aunque hayas puesto `$env:OCM_API_KEY = "..."` en una terminal | El kernel de Jupyter no hereda variables de entorno puestas *despues* de que VS Code ya estuviera abierto - son procesos distintos | Usa el valor por defecto ya puesto en `config.ipynb` (mas fiable), o cierra VS Code del todo, pon la variable en la terminal, y *luego* abre VS Code desde esa misma terminal |
| `401` / `"You must specify an API key"` en el log | `API_MAX_RESULTADOS` (config.ipynb) es mayor de 250 y no esta llegando ninguna clave a la peticion | Comprueba que `API_KEY_OPENCHARGEMAP` no este vacia |
| `403 Forbidden` en el log, con clave puesta correctamente | El User-Agent por defecto de `requests` (`python-requests/x.x`) esta bloqueado por Open Charge Map | Ya solucionado en este proyecto (`USER_AGENT_API` en `config.ipynb`); si vuelve a pasar, prueba pegando la URL exacta del log en el navegador - si ahi si funciona, es un tema de red/VPN, no de la API |
| `ModuleNotFoundError` en el notebook (p. ej. `geopandas`) | El kernel seleccionado no es el del `.venv` | Comprueba con `import sys; print(sys.executable)`; selecciona el kernel correcto y haz *Restart* |
| `FileNotFoundError` al cargar el GeoJSON o el Excel | El notebook no se esta ejecutando desde la raiz del proyecto | Asegurate de que `main.ipynb` esta al mismo nivel que `data/`, `geokw_etl/` y `output/` |
| Instalacion de `geopandas` falla en Windows (dependencias GDAL/Fiona) | `geopandas` tiene dependencias binarias nativas | Instala primero con `conda install -c conda-forge geopandas` si `pip install` falla, o usa `pip install geopandas --only-binary :all:` |
| El mapa se abre pero no se ve el mosaico base | Sin conexion a internet no cargan los tiles de Esri (son un servicio remoto) | Comprueba la conexion; la coropleta, la leyenda y los marcadores si funcionan offline, solo el mosaico de fondo necesita red |
