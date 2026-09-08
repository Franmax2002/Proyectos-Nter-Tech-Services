# Entregable_Proyecto_Tienda_Ropa_Francisco_Ortega

Migración de `BASE_DATOS_TIENDA_ROPAS_MARCAS` (SQL Server) a `db_fashionshop_dw`
(PostgreSQL) — ejercicio práctico individual, Data & BI.

## Contenido

```
Memoria_Tecnica.docx   -> documento con arquitectura, diseño y evidencias RF-01..RF-06
docker-compose.yml     -> levanta PostgreSQL 16 con las credenciales del enunciado
sql/
  ddl_destino_postgresql.sql  -> esquema destino (tablas, cuarentena, auditoría, triggers)
src/
  config.ipynb           -> parametrización y credenciales (equivalente a config.py)
  transform.ipynb        -> funciones de limpieza y regex (equivalente a transform.py)
  etl_main.ipynb          -> orquestación Extract -> Transform -> Load (equivalente a etl_main.py)
logs/
  ejecucion_etl.log      -> evidencia de una ejecución real y completa
Resultados/
  *.csv                  -> respaldo en CSV de ventas válidas/inválidas y cuarentena
sample_data/
  origen_local_demo.db, generar_replica_origen.py
```

`sample_data/` **no forma parte de los entregables**: es
una réplica local (SQLite) de `BASE_DATOS_TIENDA_ROPAS_MARCAS`, generada a partir
de `tablas_origen_sql_server_proyecto_1_tienda_ropa.sql`. El notebook la usa
*solo* como contingencia, si en el momento de ejecutarlo no logra conectar con
el SQL Server real (ver Bloque de Extracción en el propio notebook). Puede
borrarse sin problema en un entorno donde el SQL Server esté disponible.

## Cómo ejecutar

1. `docker compose up -d` — levanta PostgreSQL y aplica el DDL automáticamente.
2. Abrir `src/etl_main.ipynb` en Jupyter y ejecutar todas las celdas (arriba
   del todo carga `config.ipynb` y `transform.ipynb` automáticamente con
   `%run`, no hace falta abrirlos a mano — aunque también pueden ejecutarse
   sueltos para probarlos de forma aislada). Por defecto se conecta a
   `EM2026008667` / `BASE_DATOS_TIENDA_ROPAS_MARCAS` (SQL Server, autenticación
   integrada) y a `localhost:5432` / `db_fashionshop_dw` (PostgreSQL,
   credenciales del docker-compose).
3. Revisar `logs/ejecucion_etl.log`, `Resultados/*.csv` y las tablas en PostgreSQL
   (`tb_ejecuciones_etl`, `tb_errores_migracion`).
4. Puede volver a ejecutarse tantas veces como se quiera: el proceso es idempotente
   (RF-06).

Toda la configuración (rutas, credenciales, tasa de cambio) está parametrizada
vía variables de entorno en el Bloque 1 del notebook — no hay rutas absolutas
"hardcodeadas".
