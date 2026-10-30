# ============================================================
# Archivo: models/autor.py
# Proyecto: Sistema Ducky de Gestión Bibliotecaria
# Syntra Technologies - Equipo 1 - Sprint 1
# Materia: Ingeniería de Software
# Autores:
#   - Melissa Silva Vázquez                #624352
#   - Tomás Zapata Pérez                   #629048
#   - Alejandro Evaristo Cazares Escobedo  #626337
# Descripción: Modelo de autores.
# ============================================================
"""Modelo de autores."""
from models.db import consultar, ejecutar, normalizar

# Nombre completo del autor tal como se compara en las búsquedas
NOMBRE_COMPLETO = "nombre || COALESCE(' ' || apellidos, '')"


def obtener_o_crear(nombre_completo):
    """Id del autor con ese nombre (sin importar acentos ni mayúsculas); si no existe lo registra.

    Al registrarlo, la primera palabra se guarda como nombre y el resto como apellidos.
    """
    # Buscamos el autor comparando sin acentos ni mayúsculas
    fila = consultar(
        f"SELECT id FROM autores WHERE normalizar({NOMBRE_COMPLETO}) = ?", (normalizar(nombre_completo),), uno=True
    )
    if fila:
        return fila["id"]

    # No existe: separamos nombre y apellidos y lo registramos
    nombre, _, apellidos = nombre_completo.partition(" ")
    return ejecutar("INSERT INTO autores (nombre, apellidos) VALUES (?, ?)", (nombre, apellidos or None))
