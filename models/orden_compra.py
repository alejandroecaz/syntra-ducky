from datetime import date

from models.db import consultar, obtener_conexion


def listar():
    return consultar(
        """
        SELECT o.*, u.nombre AS solicitante,
               COUNT(i.id) AS total_titulos,
               COALESCE(SUM(i.cantidad), 0) AS total_ejemplares
        FROM ordenes_compra o
        LEFT JOIN usuarios u ON u.id = o.usuario_id
        LEFT JOIN orden_items i ON i.orden_id = o.id
        GROUP BY o.id
        ORDER BY o.id DESC
        """
    )


def obtener(orden_id):
    return consultar(
        """
        SELECT o.*, u.nombre AS solicitante, u.identificador AS solicitante_id
        FROM ordenes_compra o LEFT JOIN usuarios u ON u.id = o.usuario_id
        WHERE o.id = ?
        """,
        (orden_id,),
        uno=True,
    )


def items_de(orden_id):
    return consultar(
        """
        SELECT i.cantidad, l.id AS libro_id, l.clave, l.titulo, l.autor, l.editorial
        FROM orden_items i JOIN libros l ON l.id = i.libro_id
        WHERE i.orden_id = ? ORDER BY l.clave
        """,
        (orden_id,),
    )


def siguiente_folio():
    fila = consultar("SELECT MAX(id) AS ultimo FROM ordenes_compra", uno=True)
    return f"OC-{date.today().year}-{(fila['ultimo'] or 0) + 1:04d}"


def registrar(proveedor, fecha_requerida, justificacion, usuario_id, items):
    conexion = obtener_conexion()
    folio = siguiente_folio()
    cursor = conexion.execute(
        "INSERT INTO ordenes_compra (folio, proveedor, fecha_requerida, justificacion, usuario_id) "
        "VALUES (?, ?, ?, ?, ?)",
        (folio, proveedor, fecha_requerida, justificacion, usuario_id),
    )
    orden_id = cursor.lastrowid
    conexion.executemany(
        "INSERT INTO orden_items (orden_id, libro_id, cantidad) VALUES (?, ?, ?)",
        [(orden_id, item["libro_id"], item["cantidad"]) for item in items],
    )
    conexion.commit()
    return orden_id, folio


def contar():
    fila = consultar("SELECT COUNT(*) AS total FROM ordenes_compra", uno=True)
    return fila["total"]
