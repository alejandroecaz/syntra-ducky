"""Modelo de autores."""
from models.db import consultar, ejecutar, normalizar

NOMBRE_COMPLETO = "nombre || COALESCE(' ' || apellidos, '')"


def obtener_o_crear(nombre_completo):
    """Id del autor con ese nombre (sin importar acentos ni mayúsculas); si no existe lo registra.

    Al registrarlo, la primera palabra se guarda como nombre y el resto como apellidos.
    """
    fila = consultar(
        f"SELECT id FROM autores WHERE normalizar({NOMBRE_COMPLETO}) = ?", (normalizar(nombre_completo),), uno=True
    )
    if fila:
        return fila["id"]
    nombre, _, apellidos = nombre_completo.partition(" ")
    return ejecutar("INSERT INTO autores (nombre, apellidos) VALUES (?, ?)", (nombre, apellidos or None))
