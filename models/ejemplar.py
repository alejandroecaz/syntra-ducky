"""
============================================================
Archivo:      models/ejemplar.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Modelo de ejemplares: copias fisicas de cada libro con su ubicacion
    (estancia → estante) y estado.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

import config
from models.db import consultar, ejecutar

# Ejemplar con el nombre de su estancia y la clave de su estante (None si la
# ubicacion esta pendiente).
SELECT_EJEMPLAR = """
    SELECT e.id, e.codigo, e.libro_id, e.estante_id, e.posicion, e.estado,
           e.fecha_alta,
           COALESCE(e.fecha_actualizacion, e.fecha_alta)
               AS fecha_actualizacion,
           es.clave AS estante, ea.id AS estancia_id, ea.nombre AS estancia
    FROM ejemplares e
    LEFT JOIN estantes es ON es.id = e.estante_id
    LEFT JOIN estancias ea ON ea.id = es.estancia_id
"""


def listar_de_libro(libro_id):
    """
    Descripcion:
        Lista los ejemplares de un libro con su ubicacion, ordenados por
        codigo.

    Parametros:
        libro_id (int): id del libro.

    Salida:
        list[sqlite3.Row]: ejemplares del libro.
    """
    return consultar(
        SELECT_EJEMPLAR + " WHERE e.libro_id = ? ORDER BY e.codigo",
        (libro_id,),
    )


def obtener(ejemplar_id):
    """
    Descripcion:
        Busca un ejemplar por su id, con su estancia y estante.

    Parametros:
        ejemplar_id (int): id del ejemplar.

    Salida:
        sqlite3.Row o None si no existe.
    """
    return consultar(
        SELECT_EJEMPLAR + " WHERE e.id = ?", (ejemplar_id,), uno=True
    )


def listar_operaciones_vigentes(libro_id):
    """
    Descripcion:
        Lista los ejemplares del libro que estan prestados o reservados
        (estados de config.ESTADOS_OPERACION_VIGENTE).

    Parametros:
        libro_id (int): id del libro.

    Salida:
        list[sqlite3.Row]: codigo y estado de cada ejemplar.
    """
    # Un "?" por cada estado de operacion vigente.
    marcadores = ",".join("?" for _ in config.ESTADOS_OPERACION_VIGENTE)
    return consultar(
        "SELECT codigo, estado FROM ejemplares WHERE libro_id = ? AND "
        f"estado IN ({marcadores}) ORDER BY codigo",
        (libro_id, *config.ESTADOS_OPERACION_VIGENTE),
    )


def generar_siguiente_codigo():
    """
    Descripcion:
        Genera el codigo consecutivo para un ejemplar nuevo (EJ-0001,
        EJ-0002...).

    Parametros:
        Ninguno.

    Salida:
        str: codigo del siguiente ejemplar.
    """
    # Tomamos el ultimo id y le sumamos uno.
    fila = consultar("SELECT MAX(id) AS ultimo FROM ejemplares", uno=True)
    return f"{config.PREFIJO_EJEMPLAR}{(fila['ultimo'] or 0) + 1:04d}"


def agregar(libro_id, estante_id, posicion, estado):
    """
    Descripcion:
        Registra un ejemplar nuevo de un libro con su ubicacion y estado.

    Parametros:
        libro_id (int): id del libro.
        estante_id (int o None): id del estante, None si la ubicacion esta
            pendiente.
        posicion (int o None): posicion dentro del estante.
        estado (str): estado inicial (uno de config.ESTADOS_EJEMPLAR).

    Salida:
        str: codigo asignado al ejemplar.

    Excepciones:
        sqlite3.IntegrityError si el estado no es valido o la ubicacion esta a
        medias.
    """
    # Generamos el codigo y guardamos el ejemplar.
    codigo = generar_siguiente_codigo()
    ejecutar(
        "INSERT INTO ejemplares (codigo, libro_id, estante_id, posicion, "
        "estado, fecha_actualizacion) "
        "VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
        (codigo, libro_id, estante_id, posicion, estado),
    )
    return codigo


def actualizar(ejemplar_id, estante_id, posicion, estado):
    """
    Descripcion:
        Cambia la ubicacion y el estado de un ejemplar.

    Parametros:
        ejemplar_id (int): id del ejemplar.
        estante_id (int o None): id del estante nuevo.
        posicion (int o None): posicion dentro del estante.
        estado (str): estado nuevo.

    Salida:
        Ninguna.

    Excepciones:
        sqlite3.IntegrityError si el estado no es valido o la ubicacion esta a
        medias.
    """
    ejecutar(
        "UPDATE ejemplares SET estante_id = ?, posicion = ?, estado = ?, "
        "fecha_actualizacion = CURRENT_TIMESTAMP "
        "WHERE id = ?",
        (estante_id, posicion, estado, ejemplar_id),
    )


# Ejemplar con los datos del libro que se revisan al prestarlo (HU-02-02).
SELECT_EJEMPLAR_CON_LIBRO = """
    SELECT e.id, e.codigo, e.estado, e.posicion,
           es.clave AS estante, ea.nombre AS estancia,
           l.id AS libro_id, l.clave AS libro_clave, l.titulo,
           l.activo AS libro_activo, l.tipo_acceso
    FROM ejemplares e
    JOIN libros l ON l.id = e.libro_id
    LEFT JOIN estantes es ON es.id = e.estante_id
    LEFT JOIN estancias ea ON ea.id = es.estancia_id
"""


def obtener_por_codigo(codigo):
    """
    Descripcion:
        HU-02-02: Busca un ejemplar por su codigo (EJ-0001) con los datos de
        su libro: titulo, si esta activo y su tipo de acceso.

    Parametros:
        codigo (str): codigo del ejemplar; no distingue mayusculas.

    Salida:
        sqlite3.Row o None si no existe.
    """
    return consultar(
        SELECT_EJEMPLAR_CON_LIBRO + " WHERE UPPER(e.codigo) = UPPER(?)",
        (codigo,),
        uno=True,
    )


def listar_disponibles_para_prestamo():
    """
    Descripcion:
        HU-02-03: Lista los ejemplares que se pueden prestar (disponibles, de
        libros activos y que no son de acceso reservado) para las sugerencias
        del formulario.

    Parametros:
        Ninguno.

    Salida:
        list[sqlite3.Row]: ejemplares ordenados por titulo y codigo.
    """
    marcadores = ",".join("?" for _ in config.TIPOS_ACCESO_SIN_PRESTAMO)
    return consultar(
        SELECT_EJEMPLAR_CON_LIBRO + " WHERE e.estado = ? AND l.activo = 1 "
        f"AND l.tipo_acceso NOT IN ({marcadores}) "
        "ORDER BY l.titulo, e.codigo",
        (config.ESTADO_DISPONIBLE, *config.TIPOS_ACCESO_SIN_PRESTAMO),
    )
