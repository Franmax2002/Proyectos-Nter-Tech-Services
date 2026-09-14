-- =====================================================================
-- Proyecto: ETL GeoStat S.L.
-- Script DDL - Modelo analítico relacional en PostgreSQL 15
-- Autor: Francisco Máximo Ortega Calvo
-- Descripción: Crea las 3 tablas requeridas por la especificación:
--   1) tb_indicadores_europa   -> tabla analítica destino (consolidada)
--   2) tb_cuarentena_geodatos  -> tabla de errores / registros rechazados
--   3) tb_ejecuciones_etl      -> tabla de auditoría de cada corrida ETL
-- Este script se ejecuta automáticamente al levantar el contenedor
-- Docker (montado en /docker-entrypoint-initdb.d), por lo que las
-- tablas ya existen antes de lanzar el pipeline en Python.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1) TABLA ANALÍTICA DESTINO
-- ---------------------------------------------------------------------
-- Un único registro consolidado por país europeo (44 registros
-- esperados). "nombre_pais" es UNIQUE para poder aplicar UPSERT
-- (ON CONFLICT DO UPDATE) y garantizar idempotencia en re-ejecuciones.
CREATE TABLE IF NOT EXISTS tb_indicadores_europa (
    id                      SERIAL PRIMARY KEY,
    nombre_pais             VARCHAR(100) NOT NULL UNIQUE,
    poblacion_total         BIGINT NOT NULL,
    superficie_km2          NUMERIC(14, 3) NOT NULL,
    pib_total_eur           NUMERIC(20, 2) NOT NULL,
    densidad_poblacional    NUMERIC(12, 4) NOT NULL,   -- habitantes/km2
    pib_per_capita_eur      NUMERIC(14, 2) NOT NULL,    -- EUR/habitante
    fuente_poblacion        VARCHAR(20) NOT NULL,       -- 'API' o 'FALLBACK'
    fecha_actualizacion     TIMESTAMP NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE tb_indicadores_europa IS
    'Indicadores socioeconómicos consolidados por país europeo (una fila por país)';
COMMENT ON COLUMN tb_indicadores_europa.fuente_poblacion IS
    'Indica si la población se obtuvo de la API REST en vivo o del mecanismo de respaldo (fallback)';

-- ---------------------------------------------------------------------
-- 2) TABLA DE CUARENTENA (ERRORES DE VALIDACIÓN)
-- ---------------------------------------------------------------------
-- Guarda el dato original (tal cual llegó de la fuente Legacy) y el
-- motivo del rechazo, para trazabilidad y auditoría de calidad de datos.
CREATE TABLE IF NOT EXISTS tb_cuarentena_geodatos (
    id_cuarentena           SERIAL PRIMARY KEY,
    pais_original           VARCHAR(150),
    superficie_valor_orig   NUMERIC(18, 4),
    superficie_unidad_orig  VARCHAR(20),
    pib_valor_orig          NUMERIC(20, 4),
    pib_divisa_orig         VARCHAR(10),
    motivo_rechazo          VARCHAR(255) NOT NULL,
    id_ejecucion            INTEGER,                    -- FK lógica a tb_ejecuciones_etl
    fecha_insercion         TIMESTAMP NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE tb_cuarentena_geodatos IS
    'Registros descartados durante la validación (PIB <= 0 o entidades no europeas)';

-- ---------------------------------------------------------------------
-- 3) TABLA DE AUDITORÍA DE EJECUCIONES ETL
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tb_ejecuciones_etl (
    id_ejecucion            SERIAL PRIMARY KEY,
    fecha_inicio            TIMESTAMP NOT NULL,
    fecha_fin               TIMESTAMP,
    registros_leidos        INTEGER NOT NULL DEFAULT 0,
    registros_insertados    INTEGER NOT NULL DEFAULT 0,
    registros_cuarentena    INTEGER NOT NULL DEFAULT 0,
    origen_datos_demografia VARCHAR(20),                -- 'API' o 'FALLBACK'
    estado                  VARCHAR(20) NOT NULL DEFAULT 'EN_PROCESO', -- EN_PROCESO / OK / ERROR
    observaciones           TEXT
);

COMMENT ON TABLE tb_ejecuciones_etl IS
    'Auditoría de cada corrida del pipeline ETL: timestamps, contadores y estado final';

-- ---------------------------------------------------------------------
-- Índices de apoyo
-- ---------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_cuarentena_ejecucion
    ON tb_cuarentena_geodatos (id_ejecucion);

CREATE INDEX IF NOT EXISTS idx_ejecuciones_fecha
    ON tb_ejecuciones_etl (fecha_inicio);
