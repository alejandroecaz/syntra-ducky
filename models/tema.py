"""Modelo de temas (categorías del catálogo)."""
from models.db import consultar, ejecutar, normalizar


def listar_nombres():
    """Nombres de los temas en orden alfabético."""
    return [fila["nombre"] for fila in consultar("SELECT nombre FROM temas ORDER BY nombre")]


def obtener_o_crear(nombre):
    """Id del tema con ese nombre (sin importar acentos ni mayúsculas); si no existe lo registra."""
    fila = consultar("SELECT id FROM temas WHERE normalizar(nombre) = ?", (normalizar(nombre),), uno=True)
    if fila:
        return fila["id"]
    return ejecutar("INSERT INTO temas (nombre) VALUES (?)", (nombre,))
