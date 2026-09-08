-- ============================================================================
-- DDL - Base de datos destino: db_fashionshop_dw (PostgreSQL)
-- Proyecto: Migración a Data Warehouse - Fashion Shop S.A.
-- Autor: Francisco Máximo Ortega Calvo
--
-- Diseño: modelo relacional normalizado (3FN) que recoge únicamente las
-- entidades necesarias para cubrir los requerimientos funcionales RF-01 a
-- RF-06. Las tablas de dimensión (clientes, productos, categorías,
-- vendedores, ubicaciones) conservan el identificador de origen de SQL
-- Server como clave primaria: como el ETL vuelca SIEMPRE la extracción
-- completa del origen (no incremental), reutilizar ese identificador es lo
-- que permite implementar la idempotencia de RF-06 mediante UPSERT
-- (INSERT ... ON CONFLICT).
--
-- Este script es idempotente a nivel de estructura: puede ejecutarse varias
-- veces sin fallar gracias a los "IF NOT EXISTS".
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. TABLAS DE DIMENSIÓN
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dim_categorias (
    categoria_id        INTEGER PRIMARY KEY,      -- CategoriaID de origen
    nombre_categoria    VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_productos (
    producto_id         INTEGER PRIMARY KEY,      -- ProductoID de origen
    nombre_producto     VARCHAR(200) NOT NULL,
    categoria_id        INTEGER NOT NULL REFERENCES dim_categorias(categoria_id),
    precio_compra_eur   DECIMAL(10,2) NOT NULL CHECK (precio_compra_eur >= 0),
    precio_venta_eur    DECIMAL(10,2) NOT NULL CHECK (precio_venta_eur >= 0),
    stock               INTEGER NOT NULL DEFAULT 0,
    fecha_actualizacion TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dim_clientes (
    cliente_id          INTEGER PRIMARY KEY,      -- ClienteID de origen
    nombre              VARCHAR(150) NOT NULL,
    apellidos           VARCHAR(150) NOT NULL,
    dni                 VARCHAR(9)  NOT NULL,
    email               VARCHAR(150),
    pais                VARCHAR(100),
    fecha_actualizacion TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_dim_clientes_dni UNIQUE (dni)
);

CREATE TABLE IF NOT EXISTS dim_vendedores (
    vendedor_id          INTEGER PRIMARY KEY,     -- VendedorID de origen
    nombre_vendedor       VARCHAR(100) NOT NULL,
    pais                  VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS dim_ubicaciones (
    ubicacion_id         INTEGER PRIMARY KEY,     -- UbicacionID de origen
    ciudad               VARCHAR(100) NOT NULL,
    pais                 VARCHAR(100)
);

-- ----------------------------------------------------------------------------
-- 2. TABLA DE HECHOS
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS fact_ventas (
    venta_id             SERIAL PRIMARY KEY,           -- clave técnica interna
    venta_id_origen      INTEGER NOT NULL,             -- VentaID de SQL Server (clave de negocio)
    fecha                DATE NOT NULL,
    producto_id          INTEGER NOT NULL REFERENCES dim_productos(producto_id),
    vendedor_id          INTEGER NOT NULL REFERENCES dim_vendedores(vendedor_id),
    cliente_id           INTEGER NOT NULL REFERENCES dim_clientes(cliente_id),
    ubicacion_id          INTEGER NOT NULL REFERENCES dim_ubicaciones(ubicacion_id),
    cantidad              INTEGER NOT NULL CHECK (cantidad > 0),
    monto_total_eur       DECIMAL(10,2) NOT NULL CHECK (monto_total_eur >= 0),
    fecha_carga_etl        TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_fact_ventas_origen UNIQUE (venta_id_origen)  -- clave de idempotencia (RF-06)
);

CREATE INDEX IF NOT EXISTS ix_fact_ventas_fecha ON fact_ventas(fecha);
CREATE INDEX IF NOT EXISTS ix_fact_ventas_producto ON fact_ventas(producto_id);

-- ----------------------------------------------------------------------------
-- 3. CUARENTENA DE CALIDAD DE DATOS (RF-04)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS tb_errores_migracion (
    error_id             SERIAL PRIMARY KEY,
    tabla_origen         VARCHAR(50)  NOT NULL,
    datos_raw            TEXT         NOT NULL,
    motivo_rechazo       VARCHAR(255) NOT NULL,
    fecha_deteccion       DATE NOT NULL,
    -- Evita duplicar el mismo error en cada re-ejecución del ETL (RF-06):
    -- si el dato origen sigue siendo inválido, el registro ya está guardado.
    CONSTRAINT uq_tb_errores_migracion UNIQUE (tabla_origen, datos_raw, motivo_rechazo)
);

-- ----------------------------------------------------------------------------
-- 4. AUDITORÍA DE EJECUCIONES DEL ETL (RF-05)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS tb_ejecuciones_etl (
    id                   SERIAL PRIMARY KEY,
    fecha_inicio         TIMESTAMP NOT NULL,
    fecha_fin            TIMESTAMP,
    registros_leidos     INTEGER NOT NULL DEFAULT 0,
    registros_insertados INTEGER NOT NULL DEFAULT 0,
    registros_error      INTEGER NOT NULL DEFAULT 0
);

-- ----------------------------------------------------------------------------
-- 5. TABLAS DE AUDITORÍA (INSERT/UPDATE/DELETE) - RF-05
-- ----------------------------------------------------------------------------
-- Cada tabla de auditoría guarda una fila por cada operación de escritura
-- realizada sobre su tabla de negocio asociada, junto con el estado anterior
-- y posterior de la fila en formato JSONB (independiente del número de
-- columnas, no hay que tocar el trigger si el modelo cambia).

CREATE TABLE IF NOT EXISTS auditoria_clientes (
    audit_id      SERIAL PRIMARY KEY,
    operacion     VARCHAR(10) NOT NULL,   -- INSERT / UPDATE / DELETE
    cliente_id    INTEGER,
    datos_anteriores JSONB,
    datos_nuevos     JSONB,
    usuario_bd       VARCHAR(100) NOT NULL DEFAULT CURRENT_USER,
    fecha_operacion  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS auditoria_productos (
    audit_id      SERIAL PRIMARY KEY,
    operacion     VARCHAR(10) NOT NULL,
    producto_id   INTEGER,
    datos_anteriores JSONB,
    datos_nuevos     JSONB,
    usuario_bd       VARCHAR(100) NOT NULL DEFAULT CURRENT_USER,
    fecha_operacion  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS auditoria_ventas (
    audit_id      SERIAL PRIMARY KEY,
    operacion     VARCHAR(10) NOT NULL,
    venta_id      INTEGER,
    datos_anteriores JSONB,
    datos_nuevos     JSONB,
    usuario_bd       VARCHAR(100) NOT NULL DEFAULT CURRENT_USER,
    fecha_operacion  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 6. FUNCIONES Y TRIGGERS DE AUDITORÍA (RF-05)
-- ----------------------------------------------------------------------------
-- Una única función genérica por tabla que reacciona a TG_OP y guarda
-- row_to_json(OLD)/row_to_json(NEW) según corresponda. Se registran en
-- INSERT, UPDATE y DELETE tal y como exige el requerimiento.

CREATE OR REPLACE FUNCTION fn_auditoria_clientes() RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO auditoria_clientes(operacion, cliente_id, datos_anteriores, datos_nuevos)
        VALUES ('INSERT', NEW.cliente_id, NULL, row_to_json(NEW));
        RETURN NEW;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO auditoria_clientes(operacion, cliente_id, datos_anteriores, datos_nuevos)
        VALUES ('UPDATE', NEW.cliente_id, row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        INSERT INTO auditoria_clientes(operacion, cliente_id, datos_anteriores, datos_nuevos)
        VALUES ('DELETE', OLD.cliente_id, row_to_json(OLD), NULL);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_auditoria_productos() RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO auditoria_productos(operacion, producto_id, datos_anteriores, datos_nuevos)
        VALUES ('INSERT', NEW.producto_id, NULL, row_to_json(NEW));
        RETURN NEW;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO auditoria_productos(operacion, producto_id, datos_anteriores, datos_nuevos)
        VALUES ('UPDATE', NEW.producto_id, row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        INSERT INTO auditoria_productos(operacion, producto_id, datos_anteriores, datos_nuevos)
        VALUES ('DELETE', OLD.producto_id, row_to_json(OLD), NULL);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fn_auditoria_ventas() RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO auditoria_ventas(operacion, venta_id, datos_anteriores, datos_nuevos)
        VALUES ('INSERT', NEW.venta_id, NULL, row_to_json(NEW));
        RETURN NEW;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO auditoria_ventas(operacion, venta_id, datos_anteriores, datos_nuevos)
        VALUES ('UPDATE', NEW.venta_id, row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        INSERT INTO auditoria_ventas(operacion, venta_id, datos_anteriores, datos_nuevos)
        VALUES ('DELETE', OLD.venta_id, row_to_json(OLD), NULL);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_auditoria_clientes ON dim_clientes;
CREATE TRIGGER trg_auditoria_clientes
    AFTER INSERT OR UPDATE OR DELETE ON dim_clientes
    FOR EACH ROW EXECUTE FUNCTION fn_auditoria_clientes();

DROP TRIGGER IF EXISTS trg_auditoria_productos ON dim_productos;
CREATE TRIGGER trg_auditoria_productos
    AFTER INSERT OR UPDATE OR DELETE ON dim_productos
    FOR EACH ROW EXECUTE FUNCTION fn_auditoria_productos();

DROP TRIGGER IF EXISTS trg_auditoria_ventas ON fact_ventas;
CREATE TRIGGER trg_auditoria_ventas
    AFTER INSERT OR UPDATE OR DELETE ON fact_ventas
    FOR EACH ROW EXECUTE FUNCTION fn_auditoria_ventas();

-- ============================================================================
-- Fin del script DDL
-- ============================================================================
