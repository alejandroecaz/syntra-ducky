"""
============================================================
Archivo:      models/chatbot.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Modelo del chatbot (tablas chatbot_conversaciones y chatbot_mensajes,
    HU-02-09): cada conversacion guarda sus mensajes con lo que pidio el
    usuario (intencion) y el libro consultado, si aplica.

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


def _ahora():
    """
    Descripcion:
        Fecha y hora local con el formato de SQLite.

    Parametros:
        Ninguno.

    Salida:
        str: aaaa-mm-dd hh:mm:ss.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def obtener_conversacion_abierta(conversacion_id, usuario_id):
    """
    Descripcion:
        Busca la conversacion si sigue abierta y es del usuario.

    Parametros:
        conversacion_id (int o None): id guardado en la sesion.
        usuario_id (int): id del usuario en sesion.

    Salida:
        sqlite3.Row o None.
    """
    if not conversacion_id:
        return None
    return consultar(
        "SELECT * FROM chatbot_conversaciones "
        "WHERE id = ? AND usuario_id = ? AND estado = ?",
        (conversacion_id, usuario_id, config.ESTADO_CONVERSACION_ABIERTA),
        uno=True,
    )


def crear_conversacion(usuario_id, canal=config.CANAL_WEB):
    """
    Descripcion:
        Abre una conversacion nueva.

    Parametros:
        usuario_id (int o None): id del usuario (None si es visitante).
        canal (str): uno de config.CANALES_CHATBOT.

    Salida:
        int: id de la conversacion.
    """
    return ejecutar(
        "INSERT INTO chatbot_conversaciones (usuario_id, canal, "
        "fecha_inicio) VALUES (?, ?, ?)",
        (usuario_id, canal, _ahora()),
    )


def cerrar_conversacion(conversacion_id):
    """
    Descripcion:
        Cierra la conversacion con la fecha de fin.

    Parametros:
        conversacion_id (int): id de la conversacion.

    Salida:
        Ninguna.
    """
    ejecutar(
        "UPDATE chatbot_conversaciones SET estado = ?, fecha_fin = ? "
        "WHERE id = ? AND estado = ?",
        (
            config.ESTADO_CONVERSACION_CERRADA,
            _ahora(),
            conversacion_id,
            config.ESTADO_CONVERSACION_ABIERTA,
        ),
    )


def guardar_mensaje(
    conversacion_id, emisor, mensaje, intencion=None, libro_id=None
):
    """
    Descripcion:
        Guarda un mensaje de la conversacion.

    Parametros:
        conversacion_id (int): id de la conversacion.
        emisor (str): uno de config.EMISORES_CHATBOT.
        mensaje (str): texto del mensaje.
        intencion (str o None): lo que pidio el usuario (buscar_libro,
            consultar_prestamo, consultar_multa u orientacion).
        libro_id (int o None): libro consultado, si fue uno solo.

    Salida:
        int: id del mensaje.
    """
    return ejecutar(
        "INSERT INTO chatbot_mensajes (conversacion_id, emisor, mensaje, "
        "intencion, libro_id, fecha_envio) VALUES (?, ?, ?, ?, ?, ?)",
        (conversacion_id, emisor, mensaje, intencion, libro_id, _ahora()),
    )


def listar_mensajes(conversacion_id, limite=None):
    """
    Descripcion:
        Lista los mensajes de la conversacion en orden; con limite, solo los
        ultimos.

    Parametros:
        conversacion_id (int): id de la conversacion.
        limite (int o None): cuantos de los ultimos regresar.

    Salida:
        list[sqlite3.Row]: emisor, mensaje e intencion, del mas viejo al mas
        nuevo.
    """
    filas = consultar(
        "SELECT id, emisor, mensaje, intencion, fecha_envio "
        "FROM chatbot_mensajes WHERE conversacion_id = ? ORDER BY id DESC "
        "LIMIT ?",
        (conversacion_id, limite or -1),
    )
    return list(reversed(filas))
