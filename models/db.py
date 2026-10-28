"""Conexión a SQLite y funciones comunes de acceso a datos (capa Modelo del MVC).

Todos los modelos usan consultar() y ejecutar() con SQL parametrizado (con ?),
nunca con texto del usuario pegado dentro del SQL.
"""
import sqlite3
import unicodedata

from flask import current_app, g


def obtener_conexion():
    """Regresa la conexión de la petición actual (una por petición, con llaves foráneas activas)."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        # Para poder usar normalizar() dentro del SQL
        g.db.create_function("normalizar", 1, normalizar, deterministic=True)
    return g.db


def normalizar(texto):
    """Quita acentos y mayúsculas: 'Páramo' -> 'paramo'."""
    if texto is None:
        return None
    descompuesto = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in descompuesto if not unicodedata.combining(c)).lower()


def patron_contiene(texto):
    """Patrón para LIKE ... ESCAPE '\\' que busca el texto en cualquier parte (sin acentos)."""
    limpio = normalizar(texto).replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{limpio}%"


def cerrar_conexion(_error=None):
    """Cierra la conexión al terminar la petición."""
    conexion = g.pop("db", None)
    if conexion is not None:
        conexion.close()


def consultar(sql, parametros=(), uno=False):
    """Ejecuta un SELECT. Con uno=True regresa la primera fila o None."""
    cursor = obtener_conexion().execute(sql, parametros)
    filas = cursor.fetchall()
    cursor.close()
    if uno:
        return filas[0] if filas else None
    return filas


def ejecutar(sql, parametros=()):
    """Ejecuta un INSERT, UPDATE o DELETE, confirma el cambio y regresa el último id insertado."""
    conexion = obtener_conexion()
    cursor = conexion.execute(sql, parametros)
    conexion.commit()
    ultimo_id = cursor.lastrowid
    cursor.close()
    return ultimo_id
