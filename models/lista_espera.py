"""
============================================================
Archivo:      models/lista_espera.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Modelo de la lista de espera y de los avisos a los usuarios (tablas
    lista_espera y avisos).

    El turno de cada solicitud vigente se calcula por libro, en orden de
    fecha de solicitud.

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
from models.db import consultar, ejecutar
from models.usuario import NOMBRE_COMPLETO

# Un "?" por cada estado vigente (En espera, Notificado).
_VIGENTES = ",".join("?" for _ in config.ESTADOS_ESPERA_VIGENTE)

# Solicitud con el usuario, el libro, su turno y los ejemplares disponibles.
# El turno solo aplica a las vigentes: cuantas vigentes del mismo libro se
# pidieron antes, mas uno.
SELECT_SOLICITUD = f"""
    SELECT le.*, {NOMBRE_COMPLETO} AS usuario_nombre,
           u.identificador AS usuario_identificador, u.email AS usuario_email,
           u.telefono AS usuario_telefono,
           l.clave AS libro_clave, l.titulo,
           CASE WHEN le.estado IN ({_VIGENTES}) THEN
               (SELECT COUNT(*) FROM lista_espera x
                WHERE x.libro_id = le.libro_id AND x.estado IN ({_VIGENTES})
                  AND (x.fecha_solicitud < le.fecha_solicitud
                       OR (x.fecha_solicitud = le.fecha_solicitud
                           AND x.id < le.id))) + 1
           END AS turno,
           (SELECT COUNT(*) FROM ejemplares e
            WHERE e.libro_id = le.libro_id AND e.estado = ?) AS disponibles,
           (SELECT MIN(e.codigo) FROM ejemplares e
            WHERE e.libro_id = le.libro_id AND e.estado = ?)
               AS ejemplar_disponible
    FROM lista_espera le
    JOIN usuarios u ON u.id = le.usuario_id
    JOIN libros l ON l.id = le.libro_id
"""

# Parametros de los "?" de SELECT_SOLICITUD, en orden.
_PARAMETROS_SELECT = (
    *config.ESTADOS_ESPERA_VIGENTE,
    *config.ESTADOS_ESPERA_VIGENTE,
    config.ESTADO_DISPONIBLE,
    config.ESTADO_DISPONIBLE,
)


def listar(solo_vigentes=True):
    """
    Descripcion:
        HU-02-06: Lista las solicitudes por libro y en orden de turno.

    Parametros:
        solo_vigentes (bool): False para incluir atendidas y canceladas.

    Salida:
        list[sqlite3.Row]: solicitudes con turno y disponibilidad.
    """
    condicion = f" WHERE le.estado IN ({_VIGENTES})" if solo_vigentes else ""
    parametros = config.ESTADOS_ESPERA_VIGENTE if solo_vigentes else []
    return consultar(
        SELECT_SOLICITUD
        + condicion
        + " ORDER BY l.titulo, le.fecha_solicitud, le.id",
        (*_PARAMETROS_SELECT, *parametros),
    )


def obtener(solicitud_id):
    """
    Descripcion:
        HU-02-06: Busca una solicitud con su turno.

    Parametros:
        solicitud_id (int): id de la solicitud.

    Salida:
        sqlite3.Row o None si no existe.
    """
    return consultar(
        SELECT_SOLICITUD + " WHERE le.id = ?",
        (*_PARAMETROS_SELECT, solicitud_id),
        uno=True,
    )


def obtener_libro(clave):
    """
    Descripcion:
        HU-02-06: Busca un libro por su clave con cuantos ejemplares tiene
        disponibles y cuantas personas lo esperan.

    Parametros:
        clave (str): clave del libro; no distingue mayusculas.

    Salida:
        sqlite3.Row o None si no existe.
    """
    return consultar(
        f"""
        SELECT l.id, l.clave, l.titulo, l.activo, l.tipo_acceso,
               (SELECT COUNT(*) FROM ejemplares e
                WHERE e.libro_id = l.id AND e.estado = ?) AS disponibles,
               (SELECT COUNT(*) FROM lista_espera le
                WHERE le.libro_id = l.id AND le.estado IN ({_VIGENTES}))
                   AS en_espera
        FROM libros l WHERE l.clave = ?
        """,
        (config.ESTADO_DISPONIBLE, *config.ESTADOS_ESPERA_VIGENTE, clave),
        uno=True,
    )


def listar_libros_sin_disponibles():
    """
    Descripcion:
        HU-02-06: Lista los libros activos que se prestan y no tienen
        ejemplares disponibles, para las sugerencias del formulario.

    Parametros:
        Ninguno.

    Salida:
        list[sqlite3.Row]: clave y titulo.
    """
    marcadores = ",".join("?" for _ in config.TIPOS_ACCESO_SIN_PRESTAMO)
    return consultar(
        f"""
        SELECT l.clave, l.titulo FROM libros l
        WHERE l.activo = 1 AND l.tipo_acceso NOT IN ({marcadores})
          AND NOT EXISTS (SELECT 1 FROM ejemplares e
                          WHERE e.libro_id = l.id AND e.estado = ?)
        ORDER BY l.titulo
        """,
        (*config.TIPOS_ACCESO_SIN_PRESTAMO, config.ESTADO_DISPONIBLE),
    )


def contar_antes(libro_id, usuario_id):
    """
    Descripcion:
        HU-02-06: Cuenta cuantas personas estan antes que el usuario en la
        lista de espera del libro. Si el usuario no esta en la lista, son
        todas las solicitudes vigentes.

    Parametros:
        libro_id (int): id del libro.
        usuario_id (int): id del usuario.

    Salida:
        dict: antes (int) y turno (int o None si no esta en la lista).
    """
    vigentes = consultar(
        f"""
        SELECT usuario_id FROM lista_espera
        WHERE libro_id = ? AND estado IN ({_VIGENTES})
        ORDER BY fecha_solicitud, id
        """,
        (libro_id, *config.ESTADOS_ESPERA_VIGENTE),
    )
    usuarios = [fila["usuario_id"] for fila in vigentes]
    if usuario_id in usuarios:
        posicion = usuarios.index(usuario_id)
        return {"antes": posicion, "turno": posicion + 1}
    return {"antes": len(usuarios), "turno": None}


def contar_vigentes():
    """
    Descripcion:
        Cuenta las solicitudes que siguen esperando turno.

    Parametros:
        Ninguno.

    Salida:
        int: numero de solicitudes vigentes.
    """
    fila = consultar(
        "SELECT COUNT(*) AS total FROM lista_espera "
        f"WHERE estado IN ({_VIGENTES})",
        config.ESTADOS_ESPERA_VIGENTE,
        uno=True,
    )
    return fila["total"]


def registrar(libro_id, usuario_id):
    """
    Descripcion:
        HU-02-06: Agrega al usuario a la lista de espera del libro.

    Parametros:
        libro_id (int): id del libro.
        usuario_id (int): id del usuario.

    Salida:
        int: id de la solicitud.
    """
    return ejecutar(
        "INSERT INTO lista_espera (libro_id, usuario_id, fecha_solicitud) "
        "VALUES (?, ?, ?)",
        (libro_id, usuario_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )


def cambiar_estado(solicitud_id, estado):
    """
    Descripcion:
        HU-02-06: Cambia el estado de una solicitud (Notificado, Atendido o
        Cancelado).

    Parametros:
        solicitud_id (int): id de la solicitud.
        estado (str): uno de config.ESTADOS_ESPERA.

    Salida:
        Ninguna.
    """
    ejecutar(
        "UPDATE lista_espera SET estado = ? WHERE id = ?",
        (estado, solicitud_id),
    )


def marcar_atendida(libro_id, usuario_id):
    """
    Descripcion:
        HU-02-06: Al prestarle el libro al usuario, su solicitud vigente
        queda como atendida.

    Parametros:
        libro_id (int): id del libro.
        usuario_id (int): id del usuario.

    Salida:
        Ninguna.
    """
    ejecutar(
        "UPDATE lista_espera SET estado = ? "
        f"WHERE libro_id = ? AND usuario_id = ? AND estado IN ({_VIGENTES})",
        (
            config.ESTADO_ESPERA_ATENDIDO,
            libro_id,
            usuario_id,
            *config.ESTADOS_ESPERA_VIGENTE,
        ),
    )


def registrar_aviso(usuario_id, medio, mensaje):
    """
    Descripcion:
        HU-02-06: Guarda el aviso de lista de espera que se le mando al
        usuario (tabla avisos).

    Parametros:
        usuario_id (int): id del usuario.
        medio (str): Email o WhatsApp (config.MEDIOS_AVISO).
        mensaje (str): texto del aviso.

    Salida:
        int: id del aviso.
    """
    return ejecutar(
        "INSERT INTO avisos (usuario_id, tipo, medio, mensaje, fecha_envio) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            usuario_id,
            config.TIPO_AVISO_ESPERA,
            medio,
            mensaje[:500],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
