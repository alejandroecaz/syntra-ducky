"""
============================================================
Archivo:      models/orden_compra.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Modelo de ordenes de compra y sus renglones (tablas ordenes_compra y
    orden_items).

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

from datetime import date

from models.db import consultar, obtener_conexion
from models.libro import AUTORES_DEL_LIBRO
from models.usuario import NOMBRE_COMPLETO


def listar():
    """
    Descripcion:
        Lista las ordenes registradas, la mas reciente primero, con proveedor,
        solicitante y totales.

    Parametros:
        Ninguno.

    Salida:
        list[sqlite3.Row]: ordenes de compra.
    """
    return consultar(
        f"""
        SELECT o.*, pr.nombre AS proveedor, {NOMBRE_COMPLETO} AS solicitante,
               COUNT(i.id) AS total_titulos,
               COALESCE(SUM(i.cantidad), 0) AS total_ejemplares
        FROM ordenes_compra o
        JOIN proveedores pr ON pr.id = o.proveedor_id
        LEFT JOIN usuarios u ON u.id = o.usuario_id
        LEFT JOIN orden_items i ON i.orden_id = o.id
        GROUP BY o.id
        ORDER BY o.id DESC
        """
    )


def obtener(orden_id):
    """
    Descripcion:
        Busca una orden con el nombre del proveedor y del solicitante.

    Parametros:
        orden_id (int): id de la orden.

    Salida:
        sqlite3.Row o None si no existe.
    """
    return consultar(
        f"""
        SELECT o.*, pr.nombre AS proveedor, {NOMBRE_COMPLETO} AS solicitante,
               u.identificador AS solicitante_id
        FROM ordenes_compra o
        JOIN proveedores pr ON pr.id = o.proveedor_id
        LEFT JOIN usuarios u ON u.id = o.usuario_id
        WHERE o.id = ?
        """,
        (orden_id,),
        uno=True,
    )


def listar_items(orden_id):
    """
    Descripcion:
        Lista los renglones de la orden con los datos de cada libro.

    Parametros:
        orden_id (int): id de la orden.

    Salida:
        list[sqlite3.Row]: renglones ordenados por clave.
    """
    return consultar(
        f"""
        SELECT i.cantidad, l.id AS libro_id, l.clave, l.titulo,
               {AUTORES_DEL_LIBRO} AS autores, ed.nombre AS editorial
        FROM orden_items i
        JOIN libros l ON l.id = i.libro_id
        JOIN editoriales ed ON ed.id = l.editorial_id
        WHERE i.orden_id = ? ORDER BY l.clave
        """,
        (orden_id,),
    )


def generar_siguiente_folio():
    """
    Descripcion:
        Genera el folio consecutivo del anio, por ejemplo OC-2026-0001.

    Parametros:
        Ninguno.

    Salida:
        str: folio de la siguiente orden.
    """
    # Tomamos el ultimo id y le sumamos uno.
    fila = consultar("SELECT MAX(id) AS ultimo FROM ordenes_compra", uno=True)
    return f"OC-{date.today().year}-{(fila['ultimo'] or 0) + 1:04d}"


def registrar(proveedor_id, fecha_requerida, justificacion, usuario_id, items):
    """
    Descripcion:
        Registra la orden y sus renglones en una sola transaccion.

    Parametros:
        proveedor_id (int): id del proveedor.
        fecha_requerida (str): fecha en formato aaaa-mm-dd.
        justificacion (str): motivo de la compra (opcional).
        usuario_id (int): id de quien solicita.
        items (list[dict]): renglones con libro_id y cantidad.

    Salida:
        tuple[int, str]: id y folio de la orden.

    Excepciones:
        sqlite3.IntegrityError si un libro o el proveedor no existen.
    """
    # Insertamos el encabezado de la orden con su folio.
    conexion = obtener_conexion()
    folio = generar_siguiente_folio()
    cursor = conexion.execute(
        "INSERT INTO ordenes_compra (folio, proveedor_id, fecha_requerida, "
        "justificacion, usuario_id) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            folio,
            proveedor_id,
            fecha_requerida,
            justificacion or None,
            usuario_id,
        ),
    )
    orden_id = cursor.lastrowid

    # Insertamos los renglones y confirmamos todo junto.
    conexion.executemany(
        "INSERT INTO orden_items (orden_id, libro_id, cantidad) VALUES (?, "
        "?, ?)",
        [(orden_id, item["libro_id"], item["cantidad"]) for item in items],
    )
    conexion.commit()
    return orden_id, folio


def contar():
    """
    Descripcion:
        Cuenta las ordenes registradas.

    Parametros:
        Ninguno.

    Salida:
        int: numero de ordenes.
    """
    fila = consultar("SELECT COUNT(*) AS total FROM ordenes_compra", uno=True)
    return fila["total"]
