#!/usr/bin/env python3
"""
cli.py - Orquestador por linea de comandos de Climate Engine.

Punto de entrada unico exigido por el enunciado: "Un orquestador central
ejecutable por linea de comandos (CLI) que permita tanto la ejecucion
integral de la plataforma como la seleccion selectiva de fases de
calculo, localizaciones o forzado de particiones."

DECISION DE DISENO: este fichero es deliberadamente un envoltorio minimo.
Parsea los argumentos de la terminal y ejecuta los notebooks .ipynb reales
de climate_engine/ con nbclient (el mismo motor de ejecucion que usa
Jupyter/nbconvert), respetando sus celdas `%run` de encadenado tal y como
estan documentadas en cada modulo. Ninguna logica de negocio vive aqui:
toda esta en los notebooks, con su markdown explicativo paso a paso, como
pide la convencion de entregables ETL de Nter. Este script existe en
formato .py, y no .ipynb, por una razon puramente tecnica: leer
argumentos de linea de comandos (sys.argv) requiere un proceso Python
ejecutado desde la terminal, algo que un notebook no puede hacer por si
mismo.

NOTA: cada modulo, al encadenarse via %run, ejecuta tambien su propia
celda de "Prueba rapida" interna (con el catalogo completo de ciudades
por defecto), tal y como exige la plantilla de notebook de las
convenciones Nter. Esto es intencional: no interfiere con el resultado
final solicitado por este CLI, que se ejecuta explicitamente a
continuacion con los parametros indicados (--ciudad, --forzar-particiones),
pero puede generar de forma inocua lotes Bronze adicionales para el
catalogo completo. Ver README.md, seccion "Notas importantes".

Ejemplos:
    python cli.py --fase all
    python cli.py --fase bronze --ciudad Madrid --ciudad Sevilla
    python cli.py --fase silver --forzar-particiones
    python cli.py --fase gold
"""
import sys
from pathlib import Path

import click
import nbformat
from nbclient import NotebookClient

RAIZ_PROYECTO = Path(__file__).resolve().parent
KERNEL_NAME = "climate_engine"


def _celda(codigo):
    return nbformat.v4.new_code_cell(codigo)


def _construir_notebook_ejecucion(fases, ciudades, forzar_particiones):
    """Construye en memoria un notebook que encadena, con %run, los
    modulos de climate_engine/ necesarios segun las fases pedidas por
    linea de comandos, y llama a sus funciones principales con los
    parametros recibidos (ciudades, forzar_particiones).
    """
    nb = nbformat.v4.new_notebook()
    nb["metadata"] = {
        "kernelspec": {"name": KERNEL_NAME, "display_name": KERNEL_NAME, "language": "python"}
    }
    celdas = [_celda(
        "%run climate_engine/config.ipynb\n"
        "%run climate_engine/logging_config.ipynb\n"
        "%run climate_engine/utils_catalogo.ipynb\n"
        "validar_catalogo_minimo()"
    )]

    fases = set(fases)
    todas = "all" in fases
    necesita_bronze = todas or "bronze" in fases
    necesita_silver = todas or "silver" in fases
    necesita_gold = todas or "gold" in fases

    ciudades_repr = repr(list(ciudades)) if ciudades else "None"

    if necesita_bronze:
        celdas.append(_celda(
            "%run climate_engine/extract_openmeteo.ipynb\n"
            "%run climate_engine/bronze_ingest.ipynb"
        ))
        celdas.append(_celda(
            f"_ciudades_cli = {ciudades_repr}\n"
            "_ubicaciones_cli = {c: UBICACIONES[c] for c in _ciudades_cli} if _ciudades_cli else None\n"
            "resumen_bronze_cli = ejecutar_ingesta_bronze(_ubicaciones_cli)\n"
            "print('RESUMEN_BRONZE:', resumen_bronze_cli)"
        ))
    elif necesita_silver:
        # Fase 'silver' sin 'bronze': se reutiliza el ultimo lote Bronze
        # ya existente en disco para las ciudades indicadas (o todo el
        # catalogo), sin volver a llamar a la API.
        celdas.append(_celda(
            "%run climate_engine/extract_openmeteo.ipynb\n"
            "%run climate_engine/bronze_ingest.ipynb"
        ))
        celdas.append(_celda(
            f"_ciudades_cli = {ciudades_repr}\n"
            "resumen_bronze_cli = construir_resumen_desde_bronze_existente(_ciudades_cli)\n"
            "print('RESUMEN_BRONZE (desde disco):', resumen_bronze_cli)"
        ))

    if necesita_silver:
        celdas.append(_celda("%run climate_engine/silver_clean.ipynb"))
        celdas.append(_celda(
            f"resumen_silver_cli = procesar_silver(resumen_bronze_cli, forzar_particiones={forzar_particiones})\n"
            "print('RESUMEN_SILVER:', resumen_silver_cli)"
        ))

    if necesita_gold:
        celdas.append(_celda("%run climate_engine/gold_analytics.ipynb"))
        celdas.append(_celda(
            "resumen_gold_cli = procesar_gold()\n"
            "print('RESUMEN_GOLD:', resumen_gold_cli)"
        ))

    nb["cells"] = celdas
    return nb


def _volcar_salidas(nb):
    """Imprime en stdout el texto de salida de cada celda ejecutada, para
    que el CLI se comporte como cualquier script de terminal."""
    for celda in nb["cells"]:
        for salida in celda.get("outputs", []):
            if "text" in salida:
                sys.stdout.write(salida["text"])
            elif salida.get("output_type") == "error":
                sys.stderr.write("\n".join(salida.get("traceback", [])) + "\n")


@click.command()
@click.option(
    "--fase", "fases", multiple=True,
    type=click.Choice(["bronze", "silver", "gold", "all"], case_sensitive=False),
    default=("all",),
    help="Fase(s) a ejecutar. 'bronze' incluye la extraccion (la extraccion sin "
         "persistir en Bronze no tiene sentido). Se puede repetir la opcion.",
)
@click.option(
    "--ciudad", "ciudades", multiple=True,
    help="Nombre de una ciudad del catalogo a procesar (repetible). Por defecto, todas.",
)
@click.option(
    "--forzar-particiones", "forzar_particiones", is_flag=True, default=False,
    help="En la fase 'silver', reescribe las particiones afectadas desde cero "
         "en lugar de combinarlas con lo ya existente.",
)
def main(fases, ciudades, forzar_particiones):
    """Orquestador CLI de Climate Engine: ejecucion integral o selectiva
    por fases/ciudades/particiones sobre los notebooks de climate_engine/.
    """
    notebook_ejecucion = _construir_notebook_ejecucion(fases, ciudades, forzar_particiones)
    cliente = NotebookClient(
        notebook_ejecucion,
        timeout=180,
        kernel_name=KERNEL_NAME,
        resources={"metadata": {"path": str(RAIZ_PROYECTO)}},
    )
    click.echo(f"Climate Engine CLI - fases={list(fases)} ciudades={list(ciudades) or 'todas'} "
               f"forzar_particiones={forzar_particiones}")
    cliente.execute()
    _volcar_salidas(notebook_ejecucion)
    click.echo("Ejecucion del CLI finalizada. Ver logs/ejecucion_etl.log para el detalle completo.")


if __name__ == "__main__":
    main()
