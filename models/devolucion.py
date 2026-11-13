"""
============================================================
Archivo:      models/devolucion.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Modelo de devoluciones (tabla devoluciones, HU-02-07).

    Cerrar el prestamo, cambiar el estado del ejemplar, guardar la
    devolucion y sus multas se hace en una sola transaccion.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    13/11/2026
============================================================
"""

from datetime import datetime

import config
from models.db import consultar, obtener_conexion
from models.prestamo import SELECT_PRESTAMO
from models.usuario import NOMBRE_COMPLETO


def obtener_prestamo_activo(codigo):
    """
    Descripcion:
        HU-02-07: Busca el prestamo activo del ejemplar.

    Parametros:
        codigo (str): codigo del ejemplar, por ejemplo EJ-0019.

    Salida:
        sqlite3.Row con los datos del prestamo, o None si el ejemplar no
        esta prestado.
    """
    return consultar(
        SELECT_PRESTAMO + " WHERE e.codigo = ? AND p.estado = ?",
        (codigo, config.ESTADO_PRESTAMO_ACTIVO),
        uno=True,
    )


def listar_prestados():
    """
    Descripcion:
        HU-02-07: Lista los ejemplares prestados para las sugerencias del
        formulario.

    Parametros:
        Ninguno.

    Salida:
        list[sqlite3.Row]: codigo del ejemplar, titulo y usuario.
    """
    return consultar(
        f"""
        SELECT e.codigo, l.titulo, {NOMBRE_COMPLETO} AS usuario_nombre
        FROM prestamos p
        JOIN ejemplares e ON e.id = p.ejemplar_id
        JOIN libros l ON l.id = e.libro_id
        JOIN usuarios u ON u.id = p.usuario_id
        WHERE p.estado = ?
        ORDER BY e.codigo
        """,
        (config.ESTADO_PRESTAMO_ACTIVO,),
    )


def obtener(prestamo_id):
    """
    Descripcion:
        HU-02-07: Busca la devolucion del prestamo con quien la recibio.

    Parametros:
        prestamo_id (int): id del prestamo.

    Salida:
        sqlite3.Row o None si el libro no se devolvio (sigue prestado o se
        perdio).
    """
    return consultar(
        """
        SELECT d.*, b.nombre || ' ' || b.apellido_paterno AS bibliotecario
        FROM devoluciones d
        JOIN usuarios b ON b.id = d.bibliotecario_id
        WHERE d.prestamo_id = ?
        """,
        (prestamo_id,),
        uno=True,
    )


def listar_recientes(limite=20):
    """
    Descripcion:
        HU-02-07: Lista los ultimos prestamos cerrados (devueltos o
        perdidos) con el total de multas que generaron.

    Parametros:
        limite (int): cuantos mostrar.

    Salida:
        list[sqlite3.Row]: prestamos cerrados, el mas reciente primero.
    """
    return consultar(
        f"""
        SELECT p.id, p.folio, p.estado, p.fecha_vencimiento,
               {NOMBRE_COMPLETO} AS usuario_nombre,
               u.identificador AS usuario_identificador,
               e.codigo AS ejemplar_codigo, l.titulo, l.clave AS libro_clave,
               d.condicion,
               COALESCE(d.fecha_devolucion,
                        (SELECT MIN(m.fecha_generacion) FROM multas m
                         WHERE m.prestamo_id = p.id)) AS fecha_cierre,
               (SELECT COALESCE(SUM(m.monto), 0) FROM multas m
                WHERE m.prestamo_id = p.id) AS total_multas
        FROM prestamos p
        JOIN usuarios u ON u.id = p.usuario_id
        JOIN ejemplares e ON e.id = p.ejemplar_id
        JOIN libros l ON l.id = e.libro_id
        LEFT JOIN devoluciones d ON d.prestamo_id = p.id
        WHERE p.estado IN (?, ?)
        ORDER BY fecha_cierre DESC, p.id DESC
        LIMIT ?
        """,
        (
            config.ESTADO_PRESTAMO_DEVUELTO,
            config.ESTADO_PRESTAMO_PERDIDO,
            limite,
        ),
    )


def registrar(prestamo, bibliotecario_id, cierre, multas):
    """
    Descripcion:
        HU-02-07 y HU-02-08: Cierra el prestamo, cambia el estado del
        ejemplar, guarda la devolucion (si el libro regreso) y las multas en
        una sola transaccion. Solo cierra el prestamo si sigue activo, por
        si alguien mas registro la devolucion al mismo tiempo.

    Parametros:
        prestamo (sqlite3.Row): prestamo activo.
        bibliotecario_id (int): id de quien recibe el libro.
        cierre (dict): estado_prestamo, estado_ejemplar, condicion (None si
            el libro se perdio) y observaciones.
        multas (list[dict]): motivo, monto y descripcion de cada multa.

    Salida:
        list[int] con el id de cada multa guardada, o None si el prestamo ya
        no estaba activo (no se guarda nada).
    """
    conexion = obtener_conexion()
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Primero cerramos el prestamo; si ya no estaba activo no se hace nada.
    cursor = conexion.execute(
        "UPDATE prestamos SET estado = ? WHERE id = ? AND estado = ?",
        (
            cierre["estado_prestamo"],
            prestamo["id"],
            config.ESTADO_PRESTAMO_ACTIVO,
        ),
    )
    if cursor.rowcount == 0:
        conexion.rollback()
        return None

    # El ejemplar queda disponible, danado o perdido.
    conexion.execute(
        "UPDATE ejemplares SET estado = ?, "
        "fecha_actualizacion = CURRENT_TIMESTAMP WHERE id = ?",
        (cierre["estado_ejemplar"], prestamo["ejemplar_id"]),
    )

    # La devolucion solo existe si el libro regreso.
    if cierre["condicion"]:
        conexion.execute(
            "INSERT INTO devoluciones (prestamo_id, bibliotecario_id, "
            "fecha_devolucion, condicion, observaciones) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                prestamo["id"],
                bibliotecario_id,
                ahora,
                cierre["condicion"],
                cierre["observaciones"] or None,
            ),
        )

    # Las multas quedan pendientes de cobro.
    ids = []
    for multa in multas:
        cursor = conexion.execute(
            "INSERT INTO multas (prestamo_id, motivo, monto, descripcion, "
            "fecha_generacion) VALUES (?, ?, ?, ?, ?)",
            (
                prestamo["id"],
                multa["motivo"],
                multa["monto"],
                multa["descripcion"],
                ahora,
            ),
        )
        ids.append(cursor.lastrowid)
    conexion.commit()
    return ids
