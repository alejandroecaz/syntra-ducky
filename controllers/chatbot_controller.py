"""
============================================================
Archivo:      controllers/chatbot_controller.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Controlador del chatbot (HU-02-09).

    Papel en MVC: recibe los mensajes de la ventana de chat (JSON) y
    guarda en la sesion la conversacion abierta; las respuestas y las
    consultas estan en services/chatbot_servicio.py.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    13/11/2026
============================================================
"""

from flask import Blueprint, jsonify, request, session

import config
from services import chatbot_servicio
from services.errores import ErrorValidacion
from utils.seguridad import permiso_requerido

# Blueprint para las rutas del chatbot.
chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/chatbot")

# Llave de la sesion donde vive la conversacion abierta.
CLAVE_CONVERSACION = "chatbot_conversacion_id"


def _obtener_usuario():
    """
    Descripcion:
        Datos del usuario en sesion que necesita el chatbot.

    Parametros:
        Ninguno.

    Salida:
        dict: id, nombre, perfil y permisos.
    """
    return {
        "id": session["usuario_id"],
        "nombre": session.get("nombre") or "",
        "perfil": session.get("perfil") or "",
        "permisos": session.get("permisos", []),
    }


@chatbot_bp.route("/mensajes")
@permiso_requerido(config.PERMISO_SISTEMA)
def listar_mensajes():
    """
    Descripcion:
        HU-02-09: Regresa la conversacion abierta, si la hay, con las
        preguntas sugeridas.

    Parametros:
        Ninguno.

    Salida:
        flask.Response: JSON con conversacion_id, mensajes, modo y
        sugerencias.

    Excepciones:
        Responde 403 si el perfil no tiene acceso al sistema; sin sesion
        redirige al login.
    """
    return jsonify(
        chatbot_servicio.obtener_conversacion(
            session["usuario_id"], session.get(CLAVE_CONVERSACION)
        )
    )


@chatbot_bp.route("/mensajes", methods=["POST"])
@permiso_requerido(config.PERMISO_SISTEMA)
def enviar_mensaje():
    """
    Descripcion:
        HU-02-09: Recibe la pregunta ({"mensaje": "..."}) y regresa la
        respuesta del chatbot.

    Parametros:
        Ninguno.

    Salida:
        tuple[flask.Response, int]: JSON con respuesta, modo y aviso, o el
        mensaje del error con su codigo HTTP.

    Excepciones:
        Responde 403 si el perfil no tiene acceso al sistema; sin sesion
        redirige al login.
    """
    datos = request.get_json(silent=True) or {}
    try:
        resultado = chatbot_servicio.responder(
            _obtener_usuario(),
            session.get(CLAVE_CONVERSACION),
            str(datos.get("mensaje") or ""),
        )
    except ErrorValidacion as error:
        return jsonify({"mensaje": error.mensaje}), error.codigo
    session[CLAVE_CONVERSACION] = resultado.pop("conversacion_id")
    return jsonify(resultado), 200


@chatbot_bp.route("/nueva", methods=["POST"])
@permiso_requerido(config.PERMISO_SISTEMA)
def empezar_conversacion():
    """
    Descripcion:
        HU-02-09: Cierra la conversacion abierta para empezar otra.

    Parametros:
        Ninguno.

    Salida:
        flask.Response: JSON vacio.

    Excepciones:
        Responde 403 si el perfil no tiene acceso al sistema.
    """
    chatbot_servicio.cerrar(
        session["usuario_id"], session.pop(CLAVE_CONVERSACION, None)
    )
    return jsonify({}), 200
