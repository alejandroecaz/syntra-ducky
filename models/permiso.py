"""
============================================================
Archivo:      models/permiso.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Modelo del catalogo de permisos (tabla permisos).

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

from models.db import consultar


def listar():
    """
    Descripcion:
        Lista los permisos con codigo, descripcion y grupo, en el orden en que
        se registraron.

    Parametros:
        Ninguno.

    Salida:
        list[sqlite3.Row]: permisos.
    """
    return consultar(
        "SELECT id, codigo, descripcion, grupo FROM permisos ORDER BY id"
    )


def obtener_descripciones():
    """
    Descripcion:
        Arma un diccionario codigo -> descripcion para mostrar los permisos en
        pantalla.

    Parametros:
        Ninguno.

    Salida:
        dict[str, str]: descripcion de cada codigo de permiso.
    """
    return {fila["codigo"]: fila["descripcion"] for fila in listar()}
