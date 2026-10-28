"""Modelo de editoriales."""
from models.db import consultar, ejecutar, normalizar


def listar_nombres():
    """Nombres de las editoriales en orden alfabético."""
    return [fila["nombre"] for fila in consultar("SELECT nombre FROM editoriales ORDER BY nombre")]


def obtener_o_crear(nombre):
    """Id de la editorial con ese nombre (sin importar acentos ni mayúsculas); si no existe la registra."""
    fila = consultar("SELECT id FROM editoriales WHERE normalizar(nombre) = ?", (normalizar(nombre),), uno=True)
    if fila:
        return fila["id"]
    return ejecutar("INSERT INTO editoriales (nombre) VALUES (?)", (nombre,))
