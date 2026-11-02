"""
============================================================
Archivo:      models/autor.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Modelo de autores.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

from models.db import consultar, ejecutar, normalizar

# Nombre completo del autor tal como se compara en las busquedas.
NOMBRE_COMPLETO = "nombre || COALESCE(' ' || apellidos, '')"


def obtener_o_crear(nombre_completo):
    """
    Descripcion:
        Busca el autor por su nombre completo, sin importar acentos ni
        mayusculas, y si no existe lo registra. Al registrarlo, la primera
        palabra se guarda como nombre y el resto como apellidos.

    Parametros:
        nombre_completo (str): nombre y apellidos del autor.

    Salida:
        int: id del autor encontrado o registrado.
    """
    # Buscamos el autor comparando sin acentos ni mayusculas.
    fila = consultar(
        f"SELECT id FROM autores WHERE normalizar({NOMBRE_COMPLETO}) = ?",
        (normalizar(nombre_completo),),
        uno=True,
    )
    if fila:
        return fila["id"]

    # No existe: separamos nombre y apellidos y lo registramos.
    nombre, _, apellidos = nombre_completo.partition(" ")
    return ejecutar(
        "INSERT INTO autores (nombre, apellidos) VALUES (?, ?)",
        (nombre, apellidos or None),
    )
