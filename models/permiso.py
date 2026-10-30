# ============================================================
# Archivo: models/permiso.py
# Proyecto: Sistema Ducky de Gestión Bibliotecaria
# Syntra Technologies - Equipo 1 - Sprint 1
# Materia: Ingeniería de Software
# Autores:
#   - Melissa Silva Vázquez                #624352
#   - Tomás Zapata Pérez                   #629048
#   - Alejandro Evaristo Cazares Escobedo  #626337
# Descripción: Modelo del catálogo de permisos (tabla permisos).
# ============================================================
"""Modelo del catálogo de permisos (tabla permisos)."""
from models.db import consultar


def listar():
    """Permisos con código, descripción y grupo, en el orden en que se registraron."""
    return consultar("SELECT id, codigo, descripcion, grupo FROM permisos ORDER BY id")


def descripciones():
    """Diccionario código -> descripción para mostrar los permisos en pantalla."""
    return {fila["codigo"]: fila["descripcion"] for fila in listar()}
