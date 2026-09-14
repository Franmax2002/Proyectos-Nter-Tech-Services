# Proyecto ETL GeoStat S.L.

Pipeline ETL en Python que integra datos económicos Legacy (SQLite) y datos demográficos en vivo (API REST) en un modelo analítico relacional en PostgreSQL 15.

Prueba técnica individual — Data & BI · **Francisco Máximo Ortega Calvo**

---

## Estructura del proyecto

El pipeline está organizado como un conjunto de **notebooks-módulo** dentro de `geostat_etl/` (uno por responsabilidad, cada uno documentado en markdown y con sus propias celdas de prueba), con `main.ipynb` como punto de entrada que los encadena y ejecuta el pipeline completo.

> **Por qué `%run` y no `import`**: un `.ipynb` es un fichero JSON, no un módulo Python — no se puede hacer `import geostat_etl.config` directamente. `main.ipynb` usa la magia `%run geostat_etl/xxx.ipynb` para cargar cada módulo en su propio namespace, en el orden correcto de dependencias. Es el mismo mecanismo que ya usabas en la primera versión de este proyecto (`config.ipynb` + `transform.ipynb` + `etl_main.ipynb`).

```
Entregable_Proyecto_GeoStat_Ortega_Calvo_Francisco/
├── Memoria_Tecnica.docx
├── docker-compose.yml            Despliegue de PostgreSQL 15 (puerto 5433)
├── requirements.txt              Dependencias Python del entorno virtual
├── datos_economicos_locales.db   Fuente Legacy (SQLite, 20.000 filas)
├── main.ipynb                    Punto de entrada: encadena los módulos (%run) y ejecuta el pipeline
├── geostat_etl/                  Notebooks-módulo del pipeline
│   ├── config.ipynb              Credenciales, rutas y reglas de negocio parametrizadas
│   ├── logging_config.ipynb      Configuración centralizada del logging
│   ├── transform.ipynb           Limpieza, normalización y validación
│   ├── demografia.ipynb          Extracción resiliente de la API REST (+ fallback interno)
│   ├── db.ipynb                  Conexión a PostgreSQL y auditoría
│   ├── extract.ipynb             Extracción y limpieza de la fuente Legacy SQLite
│   ├── consolidate.ipynb         Consolidación estadística y cálculo de indicadores
│   ├── load.ipynb                Carga idempotente en PostgreSQL (UPSERT) + cuarentena
│   └── pipeline.ipynb            Orquestador ejecutar_pipeline()
├── sql/
│   └── ddl_destino_postgresql.sql   DDL de las 3 tablas destino (auto-ejecutado por Docker)
├── logs/
│   └── ejecucion_etl.log         Log de la última ejecución (se sobreescribe cada corrida; sin tildes a propósito)
└── .venv/                        Entorno virtual Python (reutiliza el tuyo si ya lo tenías)
```

Cada notebook-módulo, además de definir sus funciones, incluye una o varias celdas de **prueba rápida** que se pueden ejecutar de forma aislada (abriendo ese `.ipynb` suelto en VS Code) para comprobar que esa pieza funciona por sí sola, sin depender del resto del pipeline:

| Módulo | Qué prueba su celda de prueba |
|---|---|
| `transform.ipynb` | Normalización de nombres, conversión de unidades/divisas, caso de divisa no soportada, reglas de cuarentena |
| `demografia.ipynb` | Llamada real a la API (verás los `WARNING` y la activación del fallback si aplica) |
| `db.ipynb` | Conexión a PostgreSQL (`SELECT version();`), sin tocar tablas |
| `extract.ipynb` | Extracción completa contra la SQLite real (20.000 filas) |
| `consolidate.ipynb` | Mediana e indicadores sobre un DataFrame de ejemplo (Mónaco/Francia) |
| `load.ipynb` y `pipeline.ipynb` | No tienen prueba aislada a propósito — escriben en las tablas destino / disparan el pipeline completo, así que se prueban de forma íntegra en `main.ipynb` |

## Requisitos previos

- **Docker Desktop** (o Docker Engine + plugin Compose)
- **Python 3.10+**
- **VS Code** con las extensiones Python + Jupyter (o Jupyter Notebook/Lab si prefieres ejecutarlo fuera de VS Code)
- Opcional: **DBeaver** o **pgAdmin** para inspeccionar la base de datos visualmente

## Puesta en marcha

### 1. Levantar PostgreSQL

```powershell
docker compose up -d
docker ps
```

El contenedor `pg_geostat_dw` debe aparecer como `healthy`. Las 3 tablas destino se crean automáticamente al arrancar, porque `./sql` está montado como script de inicialización.

Si ya tenías las tablas creadas por una versión anterior del proyecto (con las columnas `pais`, `poblacion`, `pib_eur`), bórralas antes de levantar el contenedor de nuevo — el `ddl_destino_postgresql.sql` de esta versión usa `nombre_pais`, `poblacion_total` y `pib_total_eur`. `docker compose down -v` seguido de `docker compose up -d` recrea todo desde cero.

**Conexión** (para DBeaver/pgAdmin o para el propio pipeline):

| Parámetro | Valor |
|---|---|
| Host | `localhost` |
| Puerto | **`5433`** (no 5432 — es el puerto estándar de Postgres, pero aquí está remapeado) |
| Base de datos | `db_geostat_dw` |
| Usuario | `geostat_user` |
| Contraseña | `geostat_pass` |

### 2. Entorno virtual Python

Si ya tenías un `.venv` de una versión anterior del proyecto, cópialo a la raíz de este proyecto — las dependencias (`requirements.txt`) no han cambiado, no hace falta reinstalar nada.

Si prefieres crear uno nuevo:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Ejecutar el pipeline

1. Abre `main.ipynb` en VS Code (raíz del proyecto, al mismo nivel que `geostat_etl/`).
2. Selecciona como kernel el intérprete de `.venv`.
3. *Kernel -> Restart* y después *Run All*.

La sección 1 encadena los 9 notebooks-módulo con `%run` — verás en la salida, uno detrás de otro, todas sus pruebas internas (incluida la llamada real a la API de demografía). Luego el pipeline se ejecuta y se verifica.

Si en algún momento quieres inspeccionar o probar un módulo por separado, puedes abrir directamente su `.ipynb` dentro de `geostat_etl/` y darle a *Run All* ahí — cada uno es autocontenido siempre que se ejecute con la raíz del proyecto como directorio de trabajo (porque usa rutas como `./datos_economicos_locales.db`).

### 4. Verificar el resultado

La sección 4 de `main.ipynb` (*Verificación final en PostgreSQL*) consulta la base de datos directamente y muestra el total de países (debe ser **44**), el top 10 por PIB per cápita, el desglose de la cuarentena y la última fila de auditoría.

## Notas importantes

- **Nombres de columnas**: `tb_indicadores_europa` usa `id`, `nombre_pais`, `poblacion_total`, `superficie_km2`, `pib_total_eur`, `densidad_poblacional`, `pib_per_capita_eur`, `fuente_poblacion`, `fecha_actualizacion`.
- **Los mensajes del log van sin tildes a propósito** (p. ej. "Extraccion", "poblacion", "Validos"), para evitar problemas de codificación al leer el fichero en distintos entornos/terminales. La documentación en markdown y los comentarios del código sí mantienen la ortografía normal con tildes.
- **La API de demografía (`restcountries.com/v3.1/...`) está deprecada por el proveedor.** Es normal y esperado ver varios intentos fallidos antes de que se active el fallback interno.
- **La carga es idempotente**: puedes ejecutar `main.ipynb` las veces que quieras sin duplicar los 44 países.
- La celda de "reinicio limpio del logging" (justo después de los 9 `%run`) existe porque la prueba de `logging_config.ipynb` deja una línea de prueba en el log; se vuelve a llamar a `configurar_logging()` para que el log de la ejecución real quede limpio.

## Reiniciar desde cero

```powershell
docker compose down -v
docker compose up -d
```

## Resolución de problemas frecuentes

| Síntoma | Causa habitual | Solución |
|---|---|---|
| `permission denied for table tb_ejecuciones_etl` | Las tablas se crearon con otro usuario/rol | `docker compose down -v && docker compose up -d` |
| `relation "tb_indicadores_europa" already exists` con columnas antiguas (`pais`, `poblacion`) | Quedan tablas de una versión anterior del proyecto | `docker compose down -v` antes de levantar el contenedor de nuevo |
| `Connection refused` en DBeaver/pgAdmin a `localhost:5432` | La conexión apunta al puerto por defecto en vez del remapeado | Cambia el puerto de la conexión a **5433** |
| `FileNotFoundError` al abrir un `.ipynb` de `geostat_etl/` suelto | Las rutas de `config.ipynb` son relativas a la raíz del proyecto | Asegúrate de que el directorio de trabajo del kernel es la raíz del proyecto, no `geostat_etl/` |
| `NameError` al ejecutar una celda de un módulo por separado | Ese módulo depende de constantes/funciones de otro que no se ha cargado antes | Ejecuta primero `%run geostat_etl/config.ipynb` (y los módulos previos según la tabla de dependencias) en la misma sesión de kernel |
| Falla la activación de `Activate.ps1` en PowerShell | Política de ejecución restringida | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, o `.venv\Scripts\activate.bat` desde `cmd.exe` |
