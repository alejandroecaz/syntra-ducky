# ============================================================
# Archivo: models/tema.py
# Proyecto: Sistema Ducky de Gestión Bibliotecaria
# Syntra Technologies - Equipo 1 - Sprint 1
# Materia: Ingeniería de Software
# Autores:
#   - Melissa Silva Vázquez                #624352
#   - Tomás Zapata Pérez                   #629048
#   - Alejandro Evaristo Cazares Escobedo  #626337
# Descripción: Modelo de temas (categorías del catálogo).
# ============================================================
"""Modelo de temas (categorías del catálogo)."""
from models.db import consultar, ejecutar, normalizar


def listar_nombres():
    """Nombres de los temas en orden alfabético."""
    return [fila["nombre"] for fila in consultar("SELECT nombre FROM temas ORDER BY nombre")]


def obtener_o_crear(nombre):
    """Id del tema con ese nombre (sin importar acentos ni mayúsculas); si no existe lo registra."""
    # Buscamos el tema comparando sin acentos ni mayúsculas
    fila = consultar("SELECT id FROM temas WHERE normalizar(nombre) = ?", (normalizar(nombre),), uno=True)
    if fila:
        return fila["id"]

    # No existe: lo registramos
    return ejecutar("INSERT INTO temas (nombre) VALUES (?)", (nombre,))
