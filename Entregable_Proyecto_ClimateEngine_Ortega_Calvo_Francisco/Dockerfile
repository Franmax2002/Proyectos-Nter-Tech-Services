# Climate Engine - imagen de despliegue en contenedores.
# Incluye el kernel de Jupyter necesario para ejecutar los notebooks de
# climate_engine/ (via nbclient) desde el CLI y para poder abrirlos
# tambien de forma interactiva con Jupyter dentro del contenedor.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m ipykernel install --name climate_engine --display-name "Python (climate_engine)"

COPY . .

RUN mkdir -p data/bronze data/silver data/gold logs output

ENV PYTHONUNBUFFERED=1

# Por defecto, ejecuta el pipeline completo. Vease docker-compose.yml
# para el servicio del cuadro de mando (Streamlit) y para pasar otras
# fases/opciones al CLI (--fase, --ciudad, --forzar-particiones).
ENTRYPOINT ["python", "cli.py"]
CMD ["--fase", "all"]
