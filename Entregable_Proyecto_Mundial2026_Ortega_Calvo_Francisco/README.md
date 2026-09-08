# Entregable_Proyecto_Mundial2026_Ortega_Calvo_Francisco

ETL Mundial 2026 (FIFA) — extracción de goleadores/asistentes desde CSV,
transformación con SSIS, carga en PostgreSQL y dashboard en Power BI.

## Estado del entregable

```
Entregable_Proyecto_Mundial2026_Ortega_Calvo_Francisco/
├── Memoria_Tecnica.docx        [PENDIENTE — se genera al final]
├── docker-compose.yml          [LISTO]
├── sql/
│   └── ddl_destino_postgresql.sql   [LISTO — validado contra PostgreSQL real]
├── src/
│   ├── mundial2026_estadisticas.csv [fichero de origen, copiado de referencia]
│   └── mundial2026.zip         [PENDIENTE — lo generas tú en Visual Studio siguiendo la guía]
├── PowerBI/
│   └── Dashboard_Mundial2026.pbix   [PENDIENTE — siguiente paso tras la ETL]
└── logs/
    └── ejecucion_etl.log       [PENDIENTE — evidencia de tu primera ejecución real]
```

## Orden de trabajo acordado

1. **Levantar PostgreSQL** con `docker compose up -d` (usa el DDL ya incluido).
2. **Construir el paquete SSIS** en Visual Studio 2022 siguiendo la guía paso a
   paso — *en curso*.
3. Ejecutar el paquete, comprobar los datos en DBeaver, y guardar
   `logs/ejecucion_etl.log`.
4. Construir el dashboard en Power BI Desktop (`Dashboard_Mundial2026.pbix`).
5. Generar `Memoria_Tecnica.docx` con capturas reales de tu ejecución,
   mismo estilo Nter que el proyecto de Fashion Shop.

## Datos de conexión

- **PostgreSQL**: `localhost:5432` / base `db_mundial2026_dw` / usuario
  `admin_etl` / contraseña `Password123!`
- **Driver ODBC necesario en Windows**: PostgreSQL ODBC Driver (psqlODBC),
  ver guía de SSIS para el enlace de descarga.

## Resultados esperados de la lógica de negocio (verificados)

Sobre el `mundial2026_estadisticas.csv` proporcionado (30 filas): **22
registros válidos** y **8 en cuarentena** — 3 por RF-04 (fechas fuera de los
3 formatos aceptados: `06-20-2026`, y dos veces `2026/06/11`) y 5 por RF-03
(jugadores o partidos de Italia/Nigeria). Resultan **20 jugadores únicos**,
**9 partidos únicos** y **20 filas en fact_estadisticas** (las 2 parejas de
filas duplicadas en el CSV — Vinicius Jr y Mbappé — colapsan en una sola
fila cada una, tal y como exige la idempotencia de RF-06).
