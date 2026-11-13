"""
============================================================
Archivo:      controllers/espera_controller.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Controlador de la lista de espera (HU-02-06).

    Papel en MVC: recibe el formulario y las acciones de la lista
    (avisar y cancelar); las reglas estan en services/espera_servicio.py.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    13/11/2026
============================================================
"""

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from services import espera_servicio
from services.errores import ErrorValidacion
from utils import notificaciones
from utils.seguridad import permiso_requerido

# Blueprint para las rutas de la lista de espera.
espera_bp = Blueprint("espera", __name__, url_prefix="/espera")

# Permiso de todas las pantallas de la lista de espera.
PERMISO = "espera.gestionar"


def _mostrar_lista(valores=None, errores=None, resultado=None, codigo=200):
    """
    Descripcion:
        Pinta la lista de espera con el formulario para agregar usuarios.

    Parametros:
        valores (dict o None): usuario y libro capturados.
        errores (dict o None): errores por campo.
        resultado (tuple[str, str] o None): (tono, mensaje) del aviso.
        codigo (int): codigo HTTP de la respuesta.

    Salida:
        tuple[str, int]: pagina HTML y codigo HTTP.
    """
    ver = request.args.get("ver", "vigentes")
    return render_template(
        "espera/lista.html",
        solicitudes=espera_servicio.listar(ver),
        ver="todas" if ver == "todas" else "vigentes",
        valores=valores or {"libro": request.args.get("libro", "")},
        errores=errores or {},
        resultado=resultado,
        verificar_turno=espera_servicio.verificar_turno,
        whatsapp_api=notificaciones.verificar_whatsapp_api_configurada(),
        **espera_servicio.obtener_opciones_formulario(),
    ), codigo


def _obtener_o_404(solicitud_id):
    """
    Descripcion:
        Busca la solicitud o responde 404.

    Parametros:
        solicitud_id (int): id de la solicitud.

    Salida:
        sqlite3.Row: solicitud.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si no existe.
    """
    solicitud = espera_servicio.obtener(solicitud_id)
    if solicitud is None:
        abort(404)
    return solicitud


@espera_bp.route("", methods=["GET", "POST"])
@permiso_requerido(PERMISO)
def listar():
    """
    Descripcion:
        HU-02-06: Muestra la lista de espera (GET) y agrega a un usuario
        (POST).

    Parametros:
        Ninguno.

    Salida:
        str: pagina HTML con su codigo HTTP, o flask.Response: redireccion
        despues de agregar.

    Excepciones:
        Responde 403 (werkzeug.exceptions.Forbidden) si el perfil no tiene el
        permiso; sin sesion redirige al login.
    """
    if request.method == "GET":
        return _mostrar_lista()

    # POST: HU-02-06 · Registro en la lista de espera.
    try:
        mensaje = espera_servicio.registrar(request.form)
    except ErrorValidacion as error:
        return _mostrar_lista(
            error.valores,
            error.errores,
            ("error", error.mensaje),
            error.codigo,
        )
    flash(mensaje, "exito")
    return redirect(url_for("espera.listar"))


@espera_bp.route("/<int:solicitud_id>/avisar", methods=["POST"])
@permiso_requerido(PERMISO)
def avisar(solicitud_id):
    """
    Descripcion:
        HU-02-06: Avisa al usuario por correo o WhatsApp que su libro ya esta
        disponible.

    Parametros:
        solicitud_id (int): id de la solicitud.

    Salida:
        flask.Response: redireccion a la lista o a WhatsApp, o la lista con
        el error.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si no existe.
    """
    solicitud = _obtener_o_404(solicitud_id)
    try:
        tono, valor = espera_servicio.avisar(
            solicitud, request.form.get("medio", "correo")
        )
    except ErrorValidacion as error:
        return _mostrar_lista(
            resultado=("error", error.mensaje), codigo=error.codigo
        )
    if tono == "enlace":
        return redirect(valor)
    flash(valor, tono)
    return redirect(url_for("espera.listar"))


@espera_bp.route("/<int:solicitud_id>/cancelar", methods=["POST"])
@permiso_requerido(PERMISO)
def cancelar(solicitud_id):
    """
    Descripcion:
        HU-02-06: Cancela la solicitud de un usuario.

    Parametros:
        solicitud_id (int): id de la solicitud.

    Salida:
        flask.Response: redireccion a la lista con el aviso.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si no existe.
    """
    solicitud = _obtener_o_404(solicitud_id)
    try:
        flash(espera_servicio.cancelar(solicitud), "exito")
    except ErrorValidacion as error:
        flash(error.mensaje, "advertencia")
    return redirect(url_for("espera.listar"))
