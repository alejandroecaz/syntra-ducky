# ============================================================
# Archivo: models/proveedor.py
# Proyecto: Sistema Ducky de Gestión Bibliotecaria
# Syntra Technologies - Equipo 1 - Sprint 1
# Materia: Ingeniería de Software
# Autores:
#   - Melissa Silva Vázquez                #624352
#   - Tomás Zapata Pérez                   #629048
#   - Alejandro Evaristo Cazares Escobedo  #626337
# Descripción: Modelo de proveedores de libros.
# ============================================================
"""Modelo de proveedores de libros."""
from models.db import consultar, ejecutar, normalizar


def listar_nombres():
    """Nombres de los proveedores en orden alfabético."""
    return [fila["nombre"] for fila in consultar("SELECT nombre FROM proveedores ORDER BY nombre")]


def obtener_o_crear(nombre):
    """Id del proveedor con ese nombre (sin importar acentos ni mayúsculas); si no existe lo registra."""
    # Buscamos el proveedor comparando sin acentos ni mayúsculas
    fila = consultar("SELECT id FROM proveedores WHERE normalizar(nombre) = ?", (normalizar(nombre),), uno=True)
    if fila:
        return fila["id"]

    # No existe: lo registramos
    return ejecutar("INSERT INTO proveedores (nombre) VALUES (?)", (nombre,))
