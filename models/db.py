"""
============================================================
Archivo:      models/db.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Conexion a SQLite y funciones comunes de acceso a datos (capa Modelo
    del MVC).

    Todos los modelos usan consultar() y ejecutar() con SQL parametrizado
    (con ?), nunca con texto del usuario pegado dentro del SQL.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

import sqlite3
import unicodedata

from flask import current_app, g


def obtener_conexion():
    """
    Descripcion:
        Regresa la conexion a SQLite de la peticion actual. Se abre una sola
        vez por peticion, con las filas como diccionario, las llaves foraneas
        activas y la funcion normalizar() disponible dentro del SQL.

    Parametros:
        Ninguno.

    Salida:
        sqlite3.Connection: conexion guardada en flask.g.

    Excepciones:
        sqlite3.Error si no se puede abrir el archivo de la base de datos. Solo
        funciona dentro de un contexto de aplicacion de Flask.
    """
    # Abrimos la conexion solo la primera vez que se pide en la peticion.
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["RUTA_BASE_DATOS"])
        # Filas como diccionario (fila["titulo"]) y llaves foraneas activas.
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        # Para poder usar normalizar() dentro del SQL.
        g.db.create_function("normalizar", 1, normalizar, deterministic=True)
    return g.db


def normalizar(texto):
    """
    Descripcion:
        Quita acentos y mayusculas para comparar textos, por ejemplo 'Paramo'
        -> 'paramo'.

    Parametros:
        texto (str o None): texto a normalizar.

    Salida:
        str o None: el texto sin acentos y en minusculas, o None si texto es
        None.
    """
    if texto is None:
        return None
    # Separamos cada letra de su acento y nos quedamos solo con la letra.
    descompuesto = unicodedata.normalize("NFKD", str(texto))
    return "".join(
        letra for letra in descompuesto if not unicodedata.combining(letra)
    ).lower()


def crear_patron_contiene(texto):
    """
    Descripcion:
        Arma el patron para LIKE ... ESCAPE '\\' que busca el texto en
        cualquier parte, sin acentos. Escapa \\, % y _ para que el usuario
        no pueda usar comodines.

    Parametros:
        texto (str): texto que capturo el usuario.

    Salida:
        str: patron con la forma %texto%.
    """
    # Escapamos \, % y _ para que el usuario no pueda meter comodines.
    limpio = (
        normalizar(texto)
        .replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )
    return f"%{limpio}%"


def cerrar_conexion(_error=None):
    """
    Descripcion:
        Cierra la conexion de la peticion al terminar. Flask la llama sola con
        teardown_appcontext.

    Parametros:
        _error (Exception o None): error de la peticion, si hubo (no se usa).

    Salida:
        Ninguna.
    """
    conexion = g.pop("db", None)
    if conexion is not None:
        conexion.close()


def consultar(sql, parametros=(), uno=False):
    """
    Descripcion:
        Ejecuta un SELECT con parametros (nunca con texto pegado en el SQL).

    Parametros:
        sql (str): consulta con ? en lugar de los valores.
        parametros (tuple o list): valores de los ?.
        uno (bool): True para regresar solo la primera fila.

    Salida:
        list[sqlite3.Row] con todas las filas, o con uno=True la primera fila
        (sqlite3.Row) o None.

    Excepciones:
        sqlite3.Error si el SQL esta mal escrito o no coincide el numero de
        parametros.
    """
    # Ejecutamos la consulta con parametros y cerramos el cursor.
    cursor = obtener_conexion().execute(sql, parametros)
    filas = cursor.fetchall()
    cursor.close()

    # Regresamos una sola fila o la lista completa.
    if uno:
        return filas[0] if filas else None
    return filas


def ejecutar(sql, parametros=()):
    """
    Descripcion:
        Ejecuta un INSERT, UPDATE o DELETE con parametros y confirma el cambio.

    Parametros:
        sql (str): sentencia con ? en lugar de los valores.
        parametros (tuple o list): valores de los ?.

    Salida:
        int: id del ultimo registro insertado (en UPDATE y DELETE no tiene
        uso).

    Excepciones:
        sqlite3.IntegrityError si se viola una llave foranea, un UNIQUE o un
        CHECK.
    """
    # Ejecutamos y guardamos los cambios.
    conexion = obtener_conexion()
    cursor = conexion.execute(sql, parametros)
    conexion.commit()

    # Regresamos el id del registro insertado (si aplica).
    ultimo_id = cursor.lastrowid
    cursor.close()
    return ultimo_id
