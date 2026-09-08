# Proyectos-Nter-Tech-Services

Repositorio con mis ejercicios prácticos de **Data & BI** — pipelines ETL, modelado de datos, análisis estadístico, machine learning y dashboards — desarrollados durante mi estancia en Nter.

## 📊 Power BI Service

Mis informes y dashboards también están publicados en Power BI:

👉 **[Ver mis informes en Power BI Service](https://app.powerbi.com/home?redirectedFromSignup=1&ScenarioId=Signup&redirectedWaitSimple=1&experience=power-bi)**

## 📁 Proyectos

| Proyecto | Descripción | Tecnologías |
|---|---|---|
| [Migración Fashion Shop S.A.](./Entregable_Proyecto_Tienda_Ropa_Francisco_Ortega) | ETL en Python que migra un sistema transaccional heterogéneo y sucio (SQL Server) a un Data Warehouse normalizado en PostgreSQL. Incluye limpieza y validación por reglas de negocio, cuarentena de registros erróneos, carga idempotente (UPSERT) y triggers de auditoría. | `Python` `Pandas` `SQLAlchemy` `PostgreSQL` `Docker` `Jupyter` |
| [ETL Mundial 2026](./Entregable_Proyecto_Mundial2026_Ortega_Calvo_Francisco) | Pipeline ETL en SSIS que consolida estadísticas de goleadores y asistentes del Mundial 2026 (CSV) en un Data Warehouse en PostgreSQL, con carga por lotes (COPY), cuarentena de errores y un dashboard de rendimiento en Power BI. | `SSIS` `PostgreSQL` `Docker` `Power BI` `DAX` |
| [Análisis y Predicción de Churn en Telco](./Proyecto_Churn_Telco) | Proyecto de ciencia de datos end-to-end: EDA e integración (ETL) de 5 tablas en un único dataset de 7.043 clientes, análisis multivariante (Pearson, VIF, Cramér's V), modelado predictivo comparando Regresión Logística, Random Forest y Gradient Boosting (AUC ≈ 0,90), segmentación con K-Means + PCA, y dashboard en Power BI. | `Python` `Pandas` `Scikit-learn` `Statsmodels` `Power BI` `Jupyter` |

Cada carpeta incluye su propia documentación técnica (memoria técnica, notebooks comentados, etc.) y, según el proyecto, el script DDL, el `docker-compose.yml` o el fichero `.pbix` correspondiente.

## 🛠️ Stack habitual

- **ETL / Data Wrangling**: Python (Pandas, SQLAlchemy) · SSIS (Visual Studio)
- **Análisis y Machine Learning**: Scikit-learn · Statsmodels · Matplotlib/Seaborn
- **Bases de datos**: PostgreSQL · SQL Server
- **Infraestructura**: Docker
- **Visualización**: Power BI (DAX, modelado de datos)
- **Herramientas**: DBeaver · Jupyter · Visual Studio

## 👤 Autor

**Francisco Máximo Ortega Calvo** — Data & BI
