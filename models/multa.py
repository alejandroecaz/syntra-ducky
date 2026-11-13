"""
============================================================
Archivo:      models/multa.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Modelo de multas, de sus envios a Tesoreria y de sus pagos (tablas
    multas, envios_tesoreria y pagos_multa, HU-02-08).

    Registrar el pago y marcar la multa como "Pagada" se hace en una sola
    transaccion.

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
from models.db import consultar, ejecutar, obtener_conexion
from models.usuario import NOMBRE_COMPLETO

# Multa con el prestamo, el usuario, el libro y su ultimo envio a
# Tesoreria.
SELECT_MULTA = f"""
    SELECT m.*,
           p.folio, p.fecha_vencimiento, p.estado AS estado_prestamo,
           p.usuario_id,
           {NOMBRE_COMPLETO} AS usuario_nombre,
           u.identificador AS usuario_identificador, u.email AS usuario_email,
           pf.nombre AS perfil,
           e.codigo AS ejemplar_codigo, l.titulo, l.clave AS libro_clave,
           (SELECT MAX(en.fecha_envio) FROM envios_tesoreria en
            WHERE en.multa_id = m.id) AS fecha_envio_tesoreria
    FROM multas m
    JOIN prestamos p ON p.id = m.prestamo_id
    JOIN usuarios u ON u.id = p.usuario_id
    LEFT JOIN perfiles pf ON pf.id = u.perfil_id
    JOIN ejemplares e ON e.id = p.ejemplar_id
    JOIN libros l ON l.id = e.libro_id
"""


def listar(vista="pendientes"):
    """
    Descripcion:
        HU-02-08: Lista las multas, la mas reciente primero.

    Parametros:
        vista (str): "pendientes", "pagadas" o "todas"
            (config.VISTAS_MULTAS).

    Salida:
        list[sqlite3.Row]: multas con sus datos.
    """
    condiciones = {
        "pendientes": ("WHERE m.estado = ?", (config.ESTADO_MULTA_PENDIENTE,)),
        "pagadas": ("WHERE m.estado = ?", (config.ESTADO_MULTA_PAGADA,)),
        "todas": ("", ()),
    }
    condicion, parametros = condiciones.get(vista, condiciones["pendientes"])
    return consultar(
        SELECT_MULTA + f" {condicion} ORDER BY m.fecha_generacion DESC, m.id "
        "DESC",
        parametros,
    )


def obtener(multa_id):
    """
    Descripcion:
        HU-02-08: Busca una multa con todos sus datos.

    Parametros:
        multa_id (int): id de la multa.

    Salida:
        sqlite3.Row o None si no existe.
    """
    return consultar(SELECT_MULTA + " WHERE m.id = ?", (multa_id,), uno=True)


def listar_de_prestamo(prestamo_id):
    """
    Descripcion:
        HU-02-08: Lista las multas que genero un prestamo.

    Parametros:
        prestamo_id (int): id del prestamo.

    Salida:
        list[sqlite3.Row]: multas en el orden en que se generaron.
    """
    return consultar(
        SELECT_MULTA + " WHERE m.prestamo_id = ? ORDER BY m.id",
        (prestamo_id,),
    )


def listar_pendientes_sin_enviar():
    """
    Descripcion:
        HU-02-08: Lista las multas pendientes que todavia no se mandan a
        Tesoreria.

    Parametros:
        Ninguno.

    Salida:
        list[sqlite3.Row]: multas en el orden en que se generaron.
    """
    return consultar(
        SELECT_MULTA + " WHERE m.estado = ? AND NOT EXISTS (SELECT 1 FROM "
        "envios_tesoreria en WHERE en.multa_id = m.id) ORDER BY m.id",
        (config.ESTADO_MULTA_PENDIENTE,),
    )


def sumar_pendientes_de_usuario(usuario_id):
    """
    Descripcion:
        HU-02-01: Cuenta las multas pendientes del usuario y suma su monto.

    Parametros:
        usuario_id (int): id del usuario.

    Salida:
        dict: cantidad y total.
    """
    fila = consultar(
        """
        SELECT COUNT(*) AS cantidad, COALESCE(SUM(m.monto), 0) AS total
        FROM multas m
        JOIN prestamos p ON p.id = m.prestamo_id
        WHERE p.usuario_id = ? AND m.estado = ?
        """,
        (usuario_id, config.ESTADO_MULTA_PENDIENTE),
        uno=True,
    )
    return {"cantidad": fila["cantidad"], "total": fila["total"]}


def contar_pendientes():
    """
    Descripcion:
        Cuenta las multas pendientes y suma su monto para el panel de inicio.

    Parametros:
        Ninguno.

    Salida:
        dict: cantidad y total.
    """
    fila = consultar(
        "SELECT COUNT(*) AS cantidad, COALESCE(SUM(monto), 0) AS total "
        "FROM multas WHERE estado = ?",
        (config.ESTADO_MULTA_PENDIENTE,),
        uno=True,
    )
    return {"cantidad": fila["cantidad"], "total": fila["total"]}


def registrar_envio(multa_id, destino):
    """
    Descripcion:
        HU-02-08: Guarda que la multa se mando a Tesoreria.

    Parametros:
        multa_id (int): id de la multa.
        destino (str): correo de Tesoreria.

    Salida:
        int: id del envio.
    """
    return ejecutar(
        "INSERT INTO envios_tesoreria (multa_id, destino, fecha_envio) "
        "VALUES (?, ?, ?)",
        (multa_id, destino, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )


def listar_envios(multa_id):
    """
    Descripcion:
        HU-02-08: Lista los envios de la multa a Tesoreria, el mas reciente
        primero.

    Parametros:
        multa_id (int): id de la multa.

    Salida:
        list[sqlite3.Row]: destino y fecha de cada envio.
    """
    return consultar(
        "SELECT destino, fecha_envio FROM envios_tesoreria "
        "WHERE multa_id = ? ORDER BY id DESC",
        (multa_id,),
    )


def obtener_pago(multa_id):
    """
    Descripcion:
        Busca el pago de la multa con quien lo registro.

    Parametros:
        multa_id (int): id de la multa.

    Salida:
        sqlite3.Row o None si no se ha pagado.
    """
    return consultar(
        """
        SELECT pg.*, b.nombre || ' ' || b.apellido_paterno AS bibliotecario
        FROM pagos_multa pg
        JOIN usuarios b ON b.id = pg.bibliotecario_id
        WHERE pg.multa_id = ? ORDER BY pg.id DESC LIMIT 1
        """,
        (multa_id,),
        uno=True,
    )


def registrar_pago(multa, bibliotecario_id, metodo, referencia):
    """
    Descripcion:
        Guarda el pago completo de la multa y la marca como "Pagada" en una
        sola transaccion. Solo la cambia si sigue pendiente, por si alguien
        mas registro el pago al mismo tiempo.

    Parametros:
        multa (sqlite3.Row): multa pendiente.
        bibliotecario_id (int): id de quien registra el pago.
        metodo (str): uno de config.METODOS_PAGO.
        referencia (str o None): folio del ticket o de la transferencia.

    Salida:
        bool: True si se guardo; False si la multa ya no estaba pendiente.
    """
    conexion = obtener_conexion()
    cursor = conexion.execute(
        "UPDATE multas SET estado = ? WHERE id = ? AND estado = ?",
        (
            config.ESTADO_MULTA_PAGADA,
            multa["id"],
            config.ESTADO_MULTA_PENDIENTE,
        ),
    )
    if cursor.rowcount == 0:
        conexion.rollback()
        return False
    conexion.execute(
        "INSERT INTO pagos_multa (multa_id, bibliotecario_id, monto, metodo, "
        "referencia, fecha_pago) VALUES (?, ?, ?, ?, ?, ?)",
        (
            multa["id"],
            bibliotecario_id,
            multa["monto"],
            metodo,
            referencia or None,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    conexion.commit()
    return True
