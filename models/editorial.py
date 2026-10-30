# ============================================================
# Archivo: models/editorial.py
# Proyecto: Sistema Ducky de Gestión Bibliotecaria
# Syntra Technologies - Equipo 1 - Sprint 1
# Materia: Ingeniería de Software
# Autores:
#   - Melissa Silva Vázquez                #624352
#   - Tomás Zapata Pérez                   #629048
#   - Alejandro Evaristo Cazares Escobedo  #626337
# Descripción: Modelo de editoriales.
# ============================================================
"""Modelo de editoriales."""
from models.db import consultar, ejecutar, normalizar


def listar_nombres():
    """Nombres de las editoriales en orden alfabético."""
    return [fila["nombre"] for fila in consultar("SELECT nombre FROM editoriales ORDER BY nombre")]


def obtener_o_crear(nombre):
    """Id de la editorial con ese nombre (sin importar acentos ni mayúsculas); si no existe la registra."""
    # Buscamos la editorial comparando sin acentos ni mayúsculas
    fila = consultar("SELECT id FROM editoriales WHERE normalizar(nombre) = ?", (normalizar(nombre),), uno=True)
    if fila:
        return fila["id"]

    # No existe: la registramos
    return ejecutar("INSERT INTO editoriales (nombre) VALUES (?)", (nombre,))
