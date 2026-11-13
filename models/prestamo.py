"""
============================================================
Archivo:      models/prestamo.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Modelo de prestamos, de las boletas emitidas y de las renovaciones
    (tablas prestamos, comprobantes_prestamo y renovaciones).

    Registrar un prestamo y marcar el ejemplar como "Prestado" se hace
    en una sola transaccion, igual que renovar y guardar su historial.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    13/11/2026
============================================================
"""

from datetime import date, datetime

import config
from models.db import consultar, ejecutar, obtener_conexion
from models.libro import AUTORES_DEL_LIBRO
from models.usuario import NOMBRE_COMPLETO

# Un prestamo esta vencido si sigue activo y ya paso su fecha de devolucion.
CONDICION_VENCIDO = "p.estado = ? AND p.fecha_vencimiento < ?"

# Prestamo con los datos del usuario, su perfil, el libro, el ejemplar y
# quien lo registro.
SELECT_PRESTAMO = f"""
    SELECT p.*,
           {NOMBRE_COMPLETO} AS usuario_nombre,
           u.identificador AS usuario_identificador, u.email AS usuario_email,
           u.telefono AS usuario_telefono, u.estado AS usuario_estado,
           pf.nombre AS perfil, pf.dias_prestamo, pf.max_renovaciones,
           pf.multa_diaria,
           (SELECT COUNT(*) FROM renovaciones r WHERE r.prestamo_id = p.id)
               AS renovaciones,
           e.codigo AS ejemplar_codigo, e.posicion,
           es.clave AS estante, ea.nombre AS estancia,
           l.id AS libro_id, l.clave AS libro_clave, l.titulo,
           {AUTORES_DEL_LIBRO} AS autores,
           b.nombre || ' ' || b.apellido_paterno AS bibliotecario
    FROM prestamos p
    JOIN usuarios u ON u.id = p.usuario_id
    LEFT JOIN perfiles pf ON pf.id = u.perfil_id
    JOIN ejemplares e ON e.id = p.ejemplar_id
    JOIN libros l ON l.id = e.libro_id
    LEFT JOIN estantes es ON es.id = e.estante_id
    LEFT JOIN estancias ea ON ea.id = es.estancia_id
    JOIN usuarios b ON b.id = p.bibliotecario_id
"""


def listar(vista="activos"):
    """
    Descripcion:
        HU-02-03: Lista los prestamos, el mas reciente primero.

    Parametros:
        vista (str): "activos", "vencidos" o "todos" (config.VISTAS_PRESTAMOS).

    Salida:
        list[sqlite3.Row]: prestamos con sus datos.
    """
    hoy = date.today().isoformat()
    condiciones = {
        "activos": ("WHERE p.estado = ?", (config.ESTADO_PRESTAMO_ACTIVO,)),
        "vencidos": (
            f"WHERE {CONDICION_VENCIDO}",
            (config.ESTADO_PRESTAMO_ACTIVO, hoy),
        ),
        "todos": ("", ()),
    }
    condicion, parametros = condiciones.get(vista, condiciones["activos"])
    return consultar(
        SELECT_PRESTAMO + f" {condicion} ORDER BY p.id DESC", parametros
    )


def obtener(prestamo_id):
    """
    Descripcion:
        HU-02-04: Busca un prestamo con todo lo que lleva la boleta.

    Parametros:
        prestamo_id (int): id del prestamo.

    Salida:
        sqlite3.Row o None si no existe.
    """
    return consultar(
        SELECT_PRESTAMO + " WHERE p.id = ?", (prestamo_id,), uno=True
    )


def obtener_solicitante(texto):
    """
    Descripcion:
        HU-02-01: Busca al usuario por matricula (identificador) o por cuenta,
        con su perfil y las reglas de prestamo del perfil.

    Parametros:
        texto (str): matricula o cuenta; no distingue mayusculas.

    Salida:
        sqlite3.Row o None si no existe.
    """
    return consultar(
        f"""
        SELECT u.id, u.identificador, u.cuenta, u.email, u.telefono,
               u.estado, {NOMBRE_COMPLETO} AS nombre_completo,
               pf.nombre AS perfil, pf.max_prestamos, pf.dias_prestamo,
               pf.max_renovaciones, pf.multa_diaria
        FROM usuarios u
        LEFT JOIN perfiles pf ON pf.id = u.perfil_id
        WHERE u.identificador = ? OR u.cuenta = ?
        """,
        (texto, texto),
        uno=True,
    )


def listar_solicitantes():
    """
    Descripcion:
        HU-02-03: Lista los usuarios habilitados cuyo perfil tiene prestamos,
        para las sugerencias del formulario.

    Parametros:
        Ninguno.

    Salida:
        list[sqlite3.Row]: identificador, nombre y perfil.
    """
    return consultar(
        f"""
        SELECT u.identificador, {NOMBRE_COMPLETO} AS nombre_completo,
               pf.nombre AS perfil
        FROM usuarios u
        JOIN perfiles pf ON pf.id = u.perfil_id
        WHERE u.estado = ? AND pf.max_prestamos > 0
        ORDER BY u.apellido_paterno, u.nombre
        """,
        (config.ESTADO_HABILITADA,),
    )


def contar_activos_de_usuario(usuario_id):
    """
    Descripcion:
        HU-02-01: Cuenta los prestamos activos del usuario y cuantos de ellos
        ya estan vencidos.

    Parametros:
        usuario_id (int): id del usuario.

    Salida:
        dict: activos y vencidos.
    """
    fila = consultar(
        """
        SELECT COUNT(*) AS activos,
               COALESCE(SUM(p.fecha_vencimiento < ?), 0) AS vencidos
        FROM prestamos p
        WHERE p.usuario_id = ? AND p.estado = ?
        """,
        (date.today().isoformat(), usuario_id, config.ESTADO_PRESTAMO_ACTIVO),
        uno=True,
    )
    return {"activos": fila["activos"], "vencidos": fila["vencidos"]}


def verificar_libro_prestado_a_usuario(usuario_id, libro_id):
    """
    Descripcion:
        HU-02-02: Revisa si el usuario ya tiene prestado algun ejemplar del
        mismo libro.

    Parametros:
        usuario_id (int): id del usuario.
        libro_id (int): id del libro.

    Salida:
        bool: True si ya tiene uno.
    """
    fila = consultar(
        """
        SELECT 1 FROM prestamos p
        JOIN ejemplares e ON e.id = p.ejemplar_id
        WHERE p.usuario_id = ? AND e.libro_id = ? AND p.estado = ?
        """,
        (usuario_id, libro_id, config.ESTADO_PRESTAMO_ACTIVO),
        uno=True,
    )
    return fila is not None


def contar():
    """
    Descripcion:
        Cuenta los prestamos activos y vencidos para el panel de inicio.

    Parametros:
        Ninguno.

    Salida:
        dict: activos y vencidos.
    """
    fila = consultar(
        """
        SELECT COUNT(*) AS activos,
               COALESCE(SUM(p.fecha_vencimiento < ?), 0) AS vencidos
        FROM prestamos p WHERE p.estado = ?
        """,
        (date.today().isoformat(), config.ESTADO_PRESTAMO_ACTIVO),
        uno=True,
    )
    return {"activos": fila["activos"], "vencidos": fila["vencidos"]}


def generar_siguiente_folio():
    """
    Descripcion:
        Genera el folio consecutivo del anio, por ejemplo PR-2026-0001.

    Parametros:
        Ninguno.

    Salida:
        str: folio del siguiente prestamo.
    """
    fila = consultar("SELECT MAX(id) AS ultimo FROM prestamos", uno=True)
    return (
        f"{config.PREFIJO_PRESTAMO}-{date.today().year}-"
        f"{(fila['ultimo'] or 0) + 1:04d}"
    )


def registrar(ejemplar_id, usuario_id, bibliotecario_id, fecha_vencimiento):
    """
    Descripcion:
        HU-02-03: Registra el prestamo y marca el ejemplar como "Prestado" en
        una sola transaccion. Solo cambia el ejemplar si sigue disponible,
        por si alguien mas lo presto al mismo tiempo.

    Parametros:
        ejemplar_id (int): id del ejemplar.
        usuario_id (int): id de quien recibe el libro.
        bibliotecario_id (int): id de quien registra el prestamo.
        fecha_vencimiento (str): fecha de devolucion aaaa-mm-dd.

    Salida:
        tuple[int, str] con el id y el folio, o None si el ejemplar ya no
        estaba disponible (no se guarda nada).
    """
    conexion = obtener_conexion()

    # Primero apartamos el ejemplar; si ya no estaba disponible no se hace
    # nada.
    cursor = conexion.execute(
        "UPDATE ejemplares SET estado = 'Prestado', "
        "fecha_actualizacion = CURRENT_TIMESTAMP "
        "WHERE id = ? AND estado = ?",
        (ejemplar_id, config.ESTADO_DISPONIBLE),
    )
    if cursor.rowcount == 0:
        conexion.rollback()
        return None

    # Guardamos el prestamo con su folio y la hora local.
    folio = generar_siguiente_folio()
    cursor = conexion.execute(
        "INSERT INTO prestamos (folio, ejemplar_id, usuario_id, "
        "bibliotecario_id, fecha_prestamo, fecha_vencimiento) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            folio,
            ejemplar_id,
            usuario_id,
            bibliotecario_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            fecha_vencimiento,
        ),
    )
    conexion.commit()
    return cursor.lastrowid, folio


def listar_renovaciones(prestamo_id):
    """
    Descripcion:
        HU-02-05: Lista las renovaciones del prestamo en orden.

    Parametros:
        prestamo_id (int): id del prestamo.

    Salida:
        list[sqlite3.Row]: numero, fecha y vencimientos de cada renovacion.
    """
    return consultar(
        "SELECT numero, fecha_renovacion, vencimiento_anterior, "
        "vencimiento_nuevo FROM renovaciones WHERE prestamo_id = ? "
        "ORDER BY numero",
        (prestamo_id,),
    )


def renovar(prestamo_id, numero, vencimiento_anterior, vencimiento_nuevo):
    """
    Descripcion:
        HU-02-05: Guarda la renovacion y cambia la fecha de devolucion del
        prestamo en una sola transaccion.

    Parametros:
        prestamo_id (int): id del prestamo.
        numero (int): numero de renovacion (1, 2...).
        vencimiento_anterior (str): fecha de devolucion actual aaaa-mm-dd.
        vencimiento_nuevo (str): fecha de devolucion nueva aaaa-mm-dd.

    Salida:
        Ninguna.

    Excepciones:
        sqlite3.IntegrityError si ese numero de renovacion ya existe.
    """
    conexion = obtener_conexion()
    conexion.execute(
        "INSERT INTO renovaciones (prestamo_id, numero, fecha_renovacion, "
        "vencimiento_anterior, vencimiento_nuevo) VALUES (?, ?, ?, ?, ?)",
        (
            prestamo_id,
            numero,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            vencimiento_anterior,
            vencimiento_nuevo,
        ),
    )
    conexion.execute(
        "UPDATE prestamos SET fecha_vencimiento = ? WHERE id = ?",
        (vencimiento_nuevo, prestamo_id),
    )
    conexion.commit()


def registrar_comprobante(prestamo_id, medio, destino):
    """
    Descripcion:
        HU-02-04: Guarda que la boleta se envio o se imprimio.

    Parametros:
        prestamo_id (int): id del prestamo.
        medio (str): uno de config.MEDIOS_BOLETA.
        destino (str): correo, telefono o impresora.

    Salida:
        int: id del comprobante.
    """
    return ejecutar(
        "INSERT INTO comprobantes_prestamo (prestamo_id, medio, destino, "
        "fecha_emision) VALUES (?, ?, ?, ?)",
        (
            prestamo_id,
            medio,
            destino,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )


def listar_comprobantes(prestamo_id):
    """
    Descripcion:
        HU-02-04: Lista las boletas emitidas de un prestamo, la mas reciente
        primero.

    Parametros:
        prestamo_id (int): id del prestamo.

    Salida:
        list[sqlite3.Row]: medio, destino y fecha de emision.
    """
    return consultar(
        "SELECT medio, destino, fecha_emision FROM comprobantes_prestamo "
        "WHERE prestamo_id = ? ORDER BY id DESC",
        (prestamo_id,),
    )
