-- ============================================================================
-- DDL - Base de datos destino: db_mundial2026_dw (PostgreSQL)
-- Proyecto: ETL Mundial 2026 (FIFA) - goleadores y asistentes
-- Autor: Francisco Máximo Ortega Calvo
--
-- Diseño: esquema en estrella normalizado (3FN) con únicamente las tablas
-- necesarias para cubrir RF-01 a RF-07. Las dimensiones usan clave
-- subrogada (SERIAL) porque el origen (CSV) no trae ningún identificador
-- propio; la idempotencia (RF-06) se apoya en restricciones UNIQUE sobre
-- las claves de negocio reales (nombre+país del jugador; equipos+fecha del
-- partido; jugador+partido en los hechos).
--
-- Este script es idempotente a nivel de estructura (CREATE TABLE IF NOT
-- EXISTS): puede ejecutarse varias veces sin fallar ni destruir datos.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. TABLAS DE DIMENSIÓN
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dim_jugadores (
    jugador_id       SERIAL PRIMARY KEY,
    nombre_jugador   VARCHAR(150) NOT NULL,
    pais             VARCHAR(100) NOT NULL,   -- normalizado (RF-02): "Brasil", no "BRASIL"/"brasil"
    CONSTRAINT uq_dim_jugadores UNIQUE (nombre_jugador, pais)
);

CREATE TABLE IF NOT EXISTS dim_partidos (
    partido_id        SERIAL PRIMARY KEY,
    equipo_local       VARCHAR(100) NOT NULL,
    equipo_visitante    VARCHAR(100) NOT NULL,
    fecha_partido        DATE NOT NULL,          -- estandarizada a partir de RF-04
    CONSTRAINT uq_dim_partidos UNIQUE (equipo_local, equipo_visitante, fecha_partido)
);

-- ----------------------------------------------------------------------------
-- 2. TABLA DE HECHOS
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS fact_estadisticas (
    estadistica_id     SERIAL PRIMARY KEY,
    jugador_id          INTEGER NOT NULL REFERENCES dim_jugadores(jugador_id),
    partido_id           INTEGER NOT NULL REFERENCES dim_partidos(partido_id),
    goles                 INTEGER NOT NULL DEFAULT 0 CHECK (goles >= 0),
    asistencias            INTEGER NOT NULL DEFAULT 0 CHECK (asistencias >= 0),
    fecha_carga_etl          TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_fact_estadisticas UNIQUE (jugador_id, partido_id)  -- clave de idempotencia (RF-06)
);

CREATE INDEX IF NOT EXISTS ix_fact_estadisticas_jugador ON fact_estadisticas(jugador_id);
CREATE INDEX IF NOT EXISTS ix_fact_estadisticas_partido ON fact_estadisticas(partido_id);

-- ----------------------------------------------------------------------------
-- 3. CUARENTENA DE CALIDAD DE DATOS (RF-05)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS tb_errores_migracion (
    error_id           SERIAL PRIMARY KEY,
    tabla_origen         VARCHAR(100) NOT NULL,
    datos_raw              TEXT NOT NULL,
    motivo_rechazo           VARCHAR(255) NOT NULL,
    fecha_deteccion            DATE NOT NULL,
    CONSTRAINT uq_tb_errores_migracion UNIQUE (tabla_origen, datos_raw, motivo_rechazo)
);

-- ----------------------------------------------------------------------------
-- 4. AUDITORÍA DE EJECUCIONES DEL ETL (RF-05, tabla tb_ejecuciones_etl)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS tb_ejecuciones_etl (
    id                    SERIAL PRIMARY KEY,
    fecha_inicio            TIMESTAMP NOT NULL,
    fecha_fin                 TIMESTAMP,
    registros_leidos           INTEGER NOT NULL DEFAULT 0,
    registros_insertados         INTEGER NOT NULL DEFAULT 0,
    registros_error                INTEGER NOT NULL DEFAULT 0
);

-- ----------------------------------------------------------------------------
-- 5. TABLAS STAGING (destino intermedio de la Data Flow Task de SSIS)
-- ----------------------------------------------------------------------------
-- SSIS vuelca aquí los datos ya limpios (o rechazados) fila a fila. Después,
-- unos Execute SQL Task hacen el UPSERT hacia las tablas definitivas
-- (INSERT ... ON CONFLICT ... DO UPDATE) y vacían estas tablas para la
-- siguiente ejecución. Mantenerlas en el mismo esquema simplifica el
-- desarrollo del paquete SSIS (una única conexión ODBC para todo).

CREATE TABLE IF NOT EXISTS stg_estadisticas (
    nombre_jugador     VARCHAR(150),
    pais                 VARCHAR(100),
    equipo_local           VARCHAR(100),
    equipo_visitante         VARCHAR(100),
    fecha_partido               DATE,
    goles                          INTEGER,
    asistencias                      INTEGER
);

CREATE TABLE IF NOT EXISTS stg_errores (
    tabla_origen     VARCHAR(100),
    datos_raw          TEXT,
    motivo_rechazo        VARCHAR(255),
    fecha_deteccion         DATE
);

-- ============================================================================
-- Fin del script DDL
-- ============================================================================
