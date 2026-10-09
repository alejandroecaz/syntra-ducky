import sqlite3
import unicodedata

from flask import g

import config


def obtener_conexion():
    if "db" not in g:
        g.db = sqlite3.connect(config.DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        # Para poder usar normalizar() dentro del SQL
        g.db.create_function("normalizar", 1, normalizar, deterministic=True)
    return g.db


def normalizar(texto):
    # Quita acentos y mayusculas: 'Páramo' -> 'paramo'
    if texto is None:
        return None
    descompuesto = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in descompuesto if not unicodedata.combining(c)).lower()


def cerrar_conexion(_error=None):
    conexion = g.pop("db", None)
    if conexion is not None:
        conexion.close()


def consultar(sql, parametros=(), uno=False):
    cursor = obtener_conexion().execute(sql, parametros)
    filas = cursor.fetchall()
    cursor.close()
    if uno:
        return filas[0] if filas else None
    return filas


def ejecutar(sql, parametros=()):
    conexion = obtener_conexion()
    cursor = conexion.execute(sql, parametros)
    conexion.commit()
    ultimo_id = cursor.lastrowid
    cursor.close()
    return ultimo_id
