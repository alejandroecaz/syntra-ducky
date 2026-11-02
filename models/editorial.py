"""
============================================================
Archivo:      models/editorial.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Modelo de editoriales.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

from models.db import consultar, ejecutar, normalizar


def listar_nombres():
    """
    Descripcion:
        Lista los nombres de las editoriales en orden alfabetico.

    Parametros:
        Ninguno.

    Salida:
        list[str]: nombres de las editoriales.
    """
    return [
        fila["nombre"]
        for fila in consultar("SELECT nombre FROM editoriales ORDER BY nombre")
    ]


def obtener_o_crear(nombre):
    """
    Descripcion:
        Busca la editorial por nombre, sin importar acentos ni mayusculas, y si
        no existe la registra.

    Parametros:
        nombre (str): nombre de la editorial.

    Salida:
        int: id de la editorial encontrada o registrada.
    """
    # Buscamos la editorial comparando sin acentos ni mayusculas.
    fila = consultar(
        "SELECT id FROM editoriales WHERE normalizar(nombre) = ?",
        (normalizar(nombre),),
        uno=True,
    )
    if fila:
        return fila["id"]

    # No existe: la registramos.
    return ejecutar("INSERT INTO editoriales (nombre) VALUES (?)", (nombre,))
