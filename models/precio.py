"""
============================================================
Archivo:      models/precio.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Modelo de precios de los libros y tipos de cambio (tablas
    precios_libro y tipos_cambio). Se usan para cobrar la reposicion de
    un libro perdido (HU-02-08).

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    13/11/2026
============================================================
"""

from datetime import date

from models.db import consultar


def obtener_ultimo(libro_id):
    """
    Descripcion:
        HU-02-08: Busca el ultimo precio registrado del libro.

    Parametros:
        libro_id (int): id del libro.

    Salida:
        sqlite3.Row (precio, moneda, fecha_registro) o None si el libro no
        tiene precio.
    """
    return consultar(
        "SELECT precio, moneda, fecha_registro FROM precios_libro "
        "WHERE libro_id = ? ORDER BY fecha_registro DESC, id DESC LIMIT 1",
        (libro_id,),
        uno=True,
    )


def obtener_tipo_cambio_vigente(moneda):
    """
    Descripcion:
        HU-02-08: Busca el tipo de cambio mas reciente de la moneda, sin
        contar fechas futuras.

    Parametros:
        moneda (str): moneda extranjera, por ejemplo USD.

    Salida:
        sqlite3.Row (fecha, valor_mxn) o None si no hay ninguno.
    """
    return consultar(
        "SELECT fecha, valor_mxn FROM tipos_cambio "
        "WHERE moneda = ? AND fecha <= ? ORDER BY fecha DESC LIMIT 1",
        (moneda, date.today().isoformat()),
        uno=True,
    )
