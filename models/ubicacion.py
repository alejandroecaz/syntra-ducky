"""
============================================================
Archivo:      models/ubicacion.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Modelo de ubicaciones fisicas: estancias (salas) y los estantes de
    cada una.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

from models.db import consultar, ejecutar


def listar_estancias():
    """
    Descripcion:
        Lista las estancias (salas) de la biblioteca en orden de registro.

    Parametros:
        Ninguno.

    Salida:
        list[sqlite3.Row]: estancias con id, nombre y descripcion.
    """
    return consultar(
        "SELECT id, nombre, descripcion FROM estancias ORDER BY id"
    )


def obtener_estancia(estancia_id):
    """
    Descripcion:
        Busca una estancia por su id.

    Parametros:
        estancia_id (int): id de la estancia.

    Salida:
        sqlite3.Row o None si no existe.
    """
    return consultar(
        "SELECT id, nombre FROM estancias WHERE id = ?",
        (estancia_id,),
        uno=True,
    )


def obtener_o_crear_estante(estancia_id, clave):
    """
    Descripcion:
        Busca el estante con esa clave dentro de la estancia y si no existe lo
        registra.

    Parametros:
        estancia_id (int): id de la estancia.
        clave (str): clave del estante, por ejemplo A-1.

    Salida:
        int: id del estante.

    Excepciones:
        sqlite3.IntegrityError si la estancia no existe.
    """
    # Buscamos el estante dentro de la estancia.
    fila = consultar(
        "SELECT id FROM estantes WHERE estancia_id = ? AND clave = ?",
        (estancia_id, clave),
        uno=True,
    )
    if fila:
        return fila["id"]

    # No existe: lo registramos en esa estancia.
    return ejecutar(
        "INSERT INTO estantes (estancia_id, clave) VALUES (?, ?)",
        (estancia_id, clave),
    )
