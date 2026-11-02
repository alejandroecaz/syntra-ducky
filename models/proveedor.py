"""
============================================================
Archivo:      models/proveedor.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Modelo de proveedores de libros.

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
        Lista los nombres de los proveedores en orden alfabetico.

    Parametros:
        Ninguno.

    Salida:
        list[str]: nombres de los proveedores.
    """
    return [
        fila["nombre"]
        for fila in consultar("SELECT nombre FROM proveedores ORDER BY nombre")
    ]


def obtener_o_crear(nombre):
    """
    Descripcion:
        Busca el proveedor por nombre, sin importar acentos ni mayusculas, y si
        no existe lo registra.

    Parametros:
        nombre (str): nombre del proveedor.

    Salida:
        int: id del proveedor encontrado o registrado.
    """
    # Buscamos el proveedor comparando sin acentos ni mayusculas.
    fila = consultar(
        "SELECT id FROM proveedores WHERE normalizar(nombre) = ?",
        (normalizar(nombre),),
        uno=True,
    )
    if fila:
        return fila["id"]

    # No existe: lo registramos.
    return ejecutar("INSERT INTO proveedores (nombre) VALUES (?)", (nombre,))
