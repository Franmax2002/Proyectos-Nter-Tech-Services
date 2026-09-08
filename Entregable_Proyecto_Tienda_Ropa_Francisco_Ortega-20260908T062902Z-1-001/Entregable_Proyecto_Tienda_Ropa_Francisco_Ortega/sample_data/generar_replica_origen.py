"""
Genera una réplica local (SQLite) de la base de datos origen SQL Server
(BASE_DATOS_TIENDA_ROPAS_MARCAS), replicando EXACTAMENTE los INSERT del
script tablas_origen_sql_server_proyecto_1_tienda_ropa.sql (incluido el
bucle de generación de las 10.000 ventas "sucias").

Esto NO es parte del entregable oficial: es solo la utilidad que se usa
para poder ejecutar y validar el notebook ETL en un entorno sin acceso
al SQL Server real del alumno, y así generar evidencias de ejecución
reales para la Memoria Técnica.
"""
import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "origen_local_demo.db")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.executescript("""
CREATE TABLE Categorias (
    CategoriaID INTEGER PRIMARY KEY,
    NombreCategoria TEXT
);
CREATE TABLE Productos (
    ProductoID INTEGER PRIMARY KEY,
    NombreProducto TEXT,
    CategoriaID INTEGER,
    Precio_Compra TEXT,
    Precio_Venta TEXT,
    Stock INTEGER
);
CREATE TABLE Clientes (
    ClienteID INTEGER PRIMARY KEY,
    Cliente_Data TEXT,
    Email TEXT,
    Pais TEXT
);
CREATE TABLE Vendedores (
    VendedorID INTEGER PRIMARY KEY,
    NombreVendedor TEXT,
    Pais TEXT
);
CREATE TABLE Ubicaciones (
    UbicacionID INTEGER PRIMARY KEY,
    Ciudad TEXT,
    Pais TEXT
);
CREATE TABLE Ventas (
    VentaID INTEGER PRIMARY KEY,
    Fecha TEXT,
    ProductoID INTEGER,
    VendedorID INTEGER,
    ClienteID INTEGER,
    UbicacionID INTEGER,
    Cantidad INTEGER,
    MontoTotal_Raw TEXT
);
""")

categorias = [
    (1, 'Hamburguesas Gourmet'), (2, 'Pizzas & Pastas'), (3, 'Camisetas y Polos'),
    (4, 'Pantalones y Jeans'), (5, 'Sándwiches'), (6, 'Ropa Deportiva'),
    (7, 'Calzado y Zapatillas'), (8, 'Accesorios y Cinturones'),
]
cur.executemany("INSERT INTO Categorias VALUES (?,?)", categorias)

productos = [
    (1, 'Camisa de Algodón - Nike', 3, '25.00 €', '35,00', 1000),
    (2, "Pantalones de Mezclilla - Levi's", 4, 'USD 40.00', '65.50 €', 1500),
    (3, 'Chaqueta de Cuero - Adidas', 6, '150,00', '220.00 USD', 500),
    (4, 'Zapatos de Cuero - Clarks', 7, '100.00 €', '145,99 €', 800),
    (5, 'Cinturón de Cuero - Tommy Hilfiger', 8, '30.00', '45.00', 2000),
    (6, 'Burger Combo Doble Carne', 1, '5.00 €', '12.00 €', 0),
    (7, 'Pizza Pepperoni Familiar', 2, '8.00 €', '18.00 €', 0),
]
cur.executemany("INSERT INTO Productos VALUES (?,?,?,?,?,?)", productos)

clientes = [
    (1, 'García Pérez, Juan - 12345678Z', 'juan.garcia@gmail.com', 'España'),
    (2, 'Rodríguez, María - 87654321A', 'maria_rod@hotmail.com ', 'México'),
    (3, 'López D. Carlos - DNI_INVALIDO_999', 'carlos.lopez_SIN_AT.com', 'Colombia'),
    (4, 'Fernández, Ana', 'ana.f@yahoo.es', 'Argentina'),
    (5, 'Martínez, Pedro - 45678912B', '  pedro.m@gmail.com', 'Chile'),
    (6, ' Gómez, Sofia - 98765432C', 'sofia.gomez@outlook.com', 'Perú'),
    (7, 'UNKNOWN_USER', None, 'España'),
]
cur.executemany("INSERT INTO Clientes VALUES (?,?,?,?)", clientes)

vendedores = [
    (1, 'Roberto Castillo', 'Brasil'), (2, 'Gabriela Moreno', 'Venezuela'),
    (3, 'Pedro Rivas', 'Guatemala'), (4, 'Mónica Herrera', 'España'),
]
cur.executemany("INSERT INTO Vendedores VALUES (?,?,?)", vendedores)

ubicaciones = [
    (1, 'Madrid', 'España'), (2, 'Ciudad de México', 'México'),
    (3, 'Bogotá', 'Colombia'), (4, 'Buenos Aires', 'Argentina'),
]
cur.executemany("INSERT INTO Ubicaciones VALUES (?,?,?)", ubicaciones)

# --- Réplica del bucle T-SQL (10.000 ventas) ---
base = datetime(2026, 7, 29)
ventas = []
for i in range(1, 10001):
    mod4 = i % 4
    fecha_dt = base - timedelta(days=(i % 1000))
    if mod4 == 0:
        fecha = fecha_dt.strftime('%Y-%m-%d')
    elif mod4 == 1:
        fecha = fecha_dt.strftime('%d/%m/%Y')
    elif mod4 == 2:
        fecha = fecha_dt.strftime('%m/%d/%Y')
    else:
        fecha = 'INVALID_DATE'

    prod_id = (i % 7) + 1
    cli_id = (i % 7) + 1

    if i % 50 == 0:
        monto = '-150.00 €'
    elif i % 33 == 0:
        monto = 'NULL'
    elif i % 3 == 0:
        monto = f'{(i % 200) + 15.5} USD'
    else:
        monto = f'{(i % 150) + 20.0} €'

    ventas.append((i, fecha, prod_id, (i % 4) + 1, cli_id, (i % 4) + 1, (i % 5) + 1, monto))

cur.executemany("INSERT INTO Ventas VALUES (?,?,?,?,?,?,?,?)", ventas)
conn.commit()

print("Réplica local creada en:", DB_PATH)
for t in ["Categorias", "Productos", "Clientes", "Vendedores", "Ubicaciones", "Ventas"]:
    n = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t}: {n} filas")
conn.close()
