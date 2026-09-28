"""
Utilidades comunes para probar con pytest la logica real definida en los
notebooks .ipynb de climate_engine/.

Los notebooks de este proyecto encadenan sus dependencias con `%run`, una
magia de linea de IPython que solo es valida dentro de un kernel real de
Jupyter (no es Python "importable" de forma estatica). Por eso, en lugar
de intentar `import` un notebook como si fuera un modulo .py, estas
utilidades cargan el notebook real, le anaden las celdas de codigo de la
aserche a probar, y lo ejecutan de principio a fin con el mismo motor que
usa Jupyter (`nbclient`, con el kernel "climate_engine" registrado en el
entorno). Si cualquier celda -la logica real del modulo o la aserche
anadida por el test- lanza una excepcion, nbclient interrumpe la
ejecucion y la propaga como CellExecutionError, haciendo fallar el test
de pytest de forma natural. Esto prueba la logica autentica de cada
modulo, sin duplicarla ni tener que forzar su importacion estatica.
"""
from pathlib import Path

import nbformat
from nbclient import NotebookClient

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
KERNEL_NAME = "climate_engine"


def ejecutar_notebook_con_celdas_extra(ruta_relativa_notebook, celdas_codigo_extra, timeout=180):
    """Ejecuta un notebook real del proyecto anadiendole celdas de codigo
    adicionales al final (tipicamente, aserciones `assert` de un test).

    ruta_relativa_notebook: ruta del notebook relativa a la raiz del
        entregable (p.ej. "climate_engine/utils_catalogo.ipynb").
    celdas_codigo_extra: lista de strings, cada uno el codigo de una celda
        adicional a ejecutar tras el contenido original del notebook.

    Devuelve: el objeto notebook ya ejecutado (por si el test quiere
    inspeccionar las salidas impresas de alguna celda).
    """
    ruta = RAIZ_PROYECTO / ruta_relativa_notebook
    nb = nbformat.read(ruta, as_version=4)
    for codigo in celdas_codigo_extra:
        nb["cells"].append(nbformat.v4.new_code_cell(codigo))

    cliente = NotebookClient(
        nb,
        timeout=timeout,
        kernel_name=KERNEL_NAME,
        resources={"metadata": {"path": str(RAIZ_PROYECTO)}},
    )
    cliente.execute()
    return nb


def texto_de_salidas(nb):
    """Concatena todo el texto de salida (stdout) de un notebook ya
    ejecutado, util para comprobar mensajes concretos con un test."""
    partes = []
    for celda in nb["cells"]:
        for salida in celda.get("outputs", []):
            if "text" in salida:
                partes.append(salida["text"])
    return "\n".join(partes)
