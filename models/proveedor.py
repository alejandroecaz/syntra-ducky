"""Modelo de proveedores de libros."""
from models.db import consultar, ejecutar, normalizar


def listar_nombres():
    """Nombres de los proveedores en orden alfabético."""
    return [fila["nombre"] for fila in consultar("SELECT nombre FROM proveedores ORDER BY nombre")]


def obtener_o_crear(nombre):
    """Id del proveedor con ese nombre (sin importar acentos ni mayúsculas); si no existe lo registra."""
    fila = consultar("SELECT id FROM proveedores WHERE normalizar(nombre) = ?", (normalizar(nombre),), uno=True)
    if fila:
        return fila["id"]
    return ejecutar("INSERT INTO proveedores (nombre) VALUES (?)", (nombre,))
