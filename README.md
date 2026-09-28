# Proyectos-Nter-

Repositorio con mis ejercicios prácticos de **Data & BI** — pipelines ETL, modelado de datos y dashboards — desarrollados durante mi formación en Nter.

## 📊 Power BI Service

Mis informes y dashboards también están publicados en Power BI:

👉 **[Ver mis informes en Power BI Service](https://app.powerbi.com/home?redirectedFromSignup=1&ScenarioId=Signup&redirectedWaitSimple=1&experience=power-bi)**

## 📁 Proyectos

| Proyecto | Descripción | Tecnologías |
|---|---|---|
| [Migración Fashion Shop S.A.](./Entregable_Proyecto_Tienda_Ropa) | ETL Python (SQL Server -> PostgreSQL), limpieza por reglas de negocio, cuarentena, UPSERT, triggers de auditoría. | `Python` `Pandas` `SQLAlchemy` `PostgreSQL` `Docker` `Jupyter` |
| [ETL Mundial 2026](./Entregable_Proyecto_Mundial2026) | Pipeline SSIS, CSV -> PostgreSQL, carga COPY, cuarentena de errores, dashboard de rendimiento en Power BI. | `SSIS` `PostgreSQL` `Docker` `Power BI` `DAX` |
| Análisis y Predicción de Churn en Telco | Ciencia de datos end-to-end, EDA, análisis multivariante, modelado predictivo (Regresión Logística, Random Forest, Gradient Boosting, AUC ≈ 0,90), K-Means + PCA, Power BI. | `Python` `Pandas` `Scikit-learn` `Statsmodels` `Power BI` `Jupyter` |
| [ETL GeoStat](./Entregable_Proyecto_GeoStat) | Python modular, SQLite legacy (20.000 registros) + API REST de datos demográficos -> modelo analítico en PostgreSQL, extracción resiliente con reintentos/fallback, consolidación por mediana (44 países), carga idempotente. | `Python` `Pandas` `Requests` `PostgreSQL` `Docker` `Jupyter` |
| GeoKW - Índice de Oportunidad de Inversión (Sevilla) | Ingeniería de datos espaciales: cruce de GeoJSON de distritos, datos socioeconómicos reales (INE/Ayuntamiento) y API REST de puntos de recarga eléctrica, cálculo de un índice IOI por distrito, spatial join con cuarentena geográfica, mapa interactivo en Folium. | `Python` `GeoPandas` `Folium` `Requests` `Jupyter` |
| [Climate Engine — Analítica Meteorológica ETL](./Entregable_Proyecto_ClimateEngine_Ortega_Calvo_Francisco) | Pipeline ETL meteorológico (Open-Meteo, 5 ciudades, previsión horaria a 14 días) con arquitectura Bronze/Silver/Gold, ingesta resiliente con fallback, contrato de calidad con Pandera (lazy validation) y métricas analíticas en DuckDB (media móvil, Z-Score) expuestas en un dashboard Streamlit en vivo. | `Python` `Pandera` `DuckDB` `Streamlit` `Plotly` `PyArrow` `Docker` `Jupyter` `pytest` |

Cada carpeta incluye su propia documentación técnica (memoria técnica, notebooks comentados, etc.) y, según el proyecto, el script DDL, el `docker-compose.yml` o el fichero `.pbix` correspondiente.

## 🛠️ Stack habitual

- **ETL / Data Wrangling**: Python (Pandas, SQLAlchemy) · Pandera · SSIS (Visual Studio)
- **Análisis y Machine Learning**: Scikit-learn · Statsmodels · Matplotlib/Seaborn
- **Análisis geoespacial**: GeoPandas · Shapely · Folium
- **Bases de datos**: PostgreSQL · SQL Server · DuckDB
- **Infraestructura**: Docker
- **Visualización**: Power BI (DAX, modelado de datos) · Streamlit · Plotly
- **Herramientas**: DBeaver · Jupyter · Visual Studio · pytest

## 👤 Autor

**Francisco Máximo Ortega Calvo** — Data & BI

