# ============================================================
# Archivo: models/orden_compra.py
# Proyecto: Sistema Ducky de Gestión Bibliotecaria
# Syntra Technologies - Equipo 1 - Sprint 1
# Materia: Ingeniería de Software
# Autores:
#   - Melissa Silva Vázquez                #624352
#   - Tomás Zapata Pérez                   #629048
#   - Alejandro Evaristo Cazares Escobedo  #626337
# Descripción: Modelo de órdenes de compra y sus renglones (tablas ordenes_compra y orden_items).
# ============================================================
"""Modelo de órdenes de compra y sus renglones (tablas ordenes_compra y orden_items)."""
from datetime import date

from models.db import consultar, obtener_conexion
from models.libro import AUTORES_DEL_LIBRO
from models.usuario import NOMBRE_COMPLETO


def listar():
    """Órdenes registradas, la más reciente primero, con totales."""
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
    """Una orden con el nombre del proveedor y del solicitante, o None."""
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


def items_de(orden_id):
    """Renglones de la orden con los datos de cada libro."""
    return consultar(
        f"""
        SELECT i.cantidad, l.id AS libro_id, l.clave, l.titulo, {AUTORES_DEL_LIBRO} AS autores,
               ed.nombre AS editorial
        FROM orden_items i
        JOIN libros l ON l.id = i.libro_id
        JOIN editoriales ed ON ed.id = l.editorial_id
        WHERE i.orden_id = ? ORDER BY l.clave
        """,
        (orden_id,),
    )


def siguiente_folio():
    """Folio consecutivo del año: OC-2026-0001."""
    # Tomamos el último id y le sumamos uno
    fila = consultar("SELECT MAX(id) AS ultimo FROM ordenes_compra", uno=True)
    return f"OC-{date.today().year}-{(fila['ultimo'] or 0) + 1:04d}"


def registrar(proveedor_id, fecha_requerida, justificacion, usuario_id, items):
    """Registra la orden y sus renglones en una sola transacción. Regresa (id, folio)."""
    # Insertamos el encabezado de la orden con su folio
    conexion = obtener_conexion()
    folio = siguiente_folio()
    cursor = conexion.execute(
        "INSERT INTO ordenes_compra (folio, proveedor_id, fecha_requerida, justificacion, usuario_id) "
        "VALUES (?, ?, ?, ?, ?)",
        (folio, proveedor_id, fecha_requerida, justificacion or None, usuario_id),
    )
    orden_id = cursor.lastrowid

    # Insertamos los renglones y confirmamos todo junto
    conexion.executemany(
        "INSERT INTO orden_items (orden_id, libro_id, cantidad) VALUES (?, ?, ?)",
        [(orden_id, item["libro_id"], item["cantidad"]) for item in items],
    )
    conexion.commit()
    return orden_id, folio


def contar():
    """Número de órdenes registradas."""
    fila = consultar("SELECT COUNT(*) AS total FROM ordenes_compra", uno=True)
    return fila["total"]
