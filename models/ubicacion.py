# ============================================================
# Archivo: models/ubicacion.py
# Proyecto: Sistema Ducky de Gestión Bibliotecaria
# Syntra Technologies - Equipo 1 - Sprint 1
# Materia: Ingeniería de Software
# Autores:
#   - Melissa Silva Vázquez                #624352
#   - Tomás Zapata Pérez                   #629048
#   - Alejandro Evaristo Cazares Escobedo  #626337
# Descripción: Modelo de ubicaciones físicas: estancias (salas) y los estantes de cada una.
# ============================================================
"""Modelo de ubicaciones físicas: estancias (salas) y los estantes de cada una."""
from models.db import consultar, ejecutar


def listar_estancias():
    """Estancias de la biblioteca en orden de registro."""
    return consultar("SELECT id, nombre, descripcion FROM estancias ORDER BY id")


def obtener_estancia(estancia_id):
    """Una estancia o None."""
    return consultar("SELECT id, nombre FROM estancias WHERE id = ?", (estancia_id,), uno=True)


def obtener_o_crear_estante(estancia_id, clave):
    """Id del estante con esa clave dentro de la estancia; si no existe lo registra."""
    # Buscamos el estante dentro de la estancia
    fila = consultar("SELECT id FROM estantes WHERE estancia_id = ? AND clave = ?", (estancia_id, clave), uno=True)
    if fila:
        return fila["id"]

    # No existe: lo registramos en esa estancia
    return ejecutar("INSERT INTO estantes (estancia_id, clave) VALUES (?, ?)", (estancia_id, clave))
