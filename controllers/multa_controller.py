"""
============================================================
Archivo:      controllers/multa_controller.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Controlador de multas (HU-02-08).

    Papel en MVC: recibe la lista, el envio a Tesoreria, la descarga del
    aviso y el registro del pago; las reglas estan en
    services/multa_servicio.py.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    13/11/2026
============================================================
"""

from io import BytesIO

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

import config
from services import multa_servicio
from services.errores import ErrorValidacion
from utils import notificaciones
from utils.seguridad import permiso_requerido

# Blueprint para las rutas de multas.
multa_bp = Blueprint("multas", __name__, url_prefix="/multas")

# Permiso de todas las pantallas de multas.
PERMISO = "multas.gestionar"


def _obtener_o_404(multa_id):
    """
    Descripcion:
        Busca la multa con sus envios y su pago o responde 404.

    Parametros:
        multa_id (int): id de la multa.

    Salida:
        dict: multa, envios y pago.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si no existe.
    """
    datos = multa_servicio.obtener(multa_id)
    if datos is None:
        abort(404)
    return datos


def _mostrar_detalle(multa_id, codigo=200, **extra):
    """
    Descripcion:
        Pinta la multa con su envio a Tesoreria y el registro del pago; extra
        lleva errores, valores capturados o el resultado de una accion.

    Parametros:
        multa_id (int): id de la multa.
        codigo (int): codigo HTTP de la respuesta.
        **extra (dict): datos adicionales para la vista.

    Salida:
        tuple[str, int]: pagina HTML y codigo HTTP.
    """
    datos = _obtener_o_404(multa_id)
    contexto = {"errores": {}, "valores": {}, "resultado": None}
    contexto.update(extra)
    return render_template(
        "multas/detalle.html",
        datos_aviso=multa_servicio.armar_datos_aviso([datos["multa"]]),
        nota_aviso=multa_servicio.NOTA_AVISO,
        metodos=[(metodo, metodo) for metodo in config.METODOS_PAGO],
        correo_tesoreria=notificaciones.obtener_correo_tesoreria(),
        correo_configurado=notificaciones.verificar_correo_configurado(),
        **datos,
        **contexto,
    ), codigo


# ============================================================
# LISTA Y ENVIO A TESORERIA (HU-02-08)
# ============================================================


@multa_bp.route("")
@permiso_requerido(PERMISO)
def listar():
    """
    Descripcion:
        HU-02-08: Muestra las multas pendientes, pagadas o todas.

    Parametros:
        Ninguno.

    Salida:
        str: pagina HTML de la vista multas/lista.html.

    Excepciones:
        Responde 403 (werkzeug.exceptions.Forbidden) si el perfil no tiene el
        permiso; sin sesion redirige al login.
    """
    vista = multa_servicio.obtener_vista(request.args.get("ver"))
    return render_template(
        "multas/lista.html",
        multas=multa_servicio.listar(vista),
        vista=vista,
        totales=multa_servicio.contar_pendientes(),
        correo_tesoreria=notificaciones.obtener_correo_tesoreria(),
    )


@multa_bp.route("/tesoreria", methods=["POST"])
@permiso_requerido(PERMISO)
def enviar_pendientes():
    """
    Descripcion:
        HU-02-08: Manda a Tesoreria todas las multas pendientes que no se han
        enviado.

    Parametros:
        Ninguno.

    Salida:
        flask.Response: redireccion a la lista con el aviso.

    Excepciones:
        Responde 403 si el perfil no tiene el permiso.
    """
    try:
        tono, mensaje = multa_servicio.enviar_pendientes()
    except ErrorValidacion as error:
        tono, mensaje = "error", error.mensaje
    flash(mensaje, tono)
    return redirect(url_for("multas.listar"))


@multa_bp.route("/<int:multa_id>")
@permiso_requerido(PERMISO)
def mostrar_detalle(multa_id):
    """
    Descripcion:
        HU-02-08: Muestra la multa, sus envios a Tesoreria y su pago.

    Parametros:
        multa_id (int): id de la multa.

    Salida:
        tuple[str, int]: pagina HTML de la vista multas/detalle.html.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si no existe.
    """
    return _mostrar_detalle(multa_id)


@multa_bp.route("/<int:multa_id>/tesoreria", methods=["POST"])
@permiso_requerido(PERMISO)
def enviar_a_tesoreria(multa_id):
    """
    Descripcion:
        HU-02-08: Manda (o vuelve a mandar) la multa a Tesoreria.

    Parametros:
        multa_id (int): id de la multa.

    Salida:
        flask.Response: redireccion a la multa, o la multa con el error.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si no existe.
    """
    multa = _obtener_o_404(multa_id)["multa"]
    try:
        tono, mensaje = multa_servicio.enviar_a_tesoreria([multa])
    except ErrorValidacion as error:
        return _mostrar_detalle(
            multa_id, error.codigo, resultado=("error", error.mensaje)
        )
    flash(mensaje, tono)
    return redirect(url_for("multas.mostrar_detalle", multa_id=multa_id))


@multa_bp.route("/<int:multa_id>/aviso.pdf")
@permiso_requerido(PERMISO)
def descargar_aviso(multa_id):
    """
    Descripcion:
        HU-02-08: Descarga el aviso de multa en PDF.

    Parametros:
        multa_id (int): id de la multa.

    Salida:
        flask.Response con el archivo PDF.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si no existe.
    """
    multa = _obtener_o_404(multa_id)["multa"]
    contenido, nombre = multa_servicio.generar_pdf_aviso([multa])
    return send_file(
        BytesIO(contenido),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=nombre,
    )


# ============================================================
# PAGO DE LA MULTA
# ============================================================


@multa_bp.route("/<int:multa_id>/pago", methods=["POST"])
@permiso_requerido(PERMISO)
def registrar_pago(multa_id):
    """
    Descripcion:
        Registra el pago que Tesoreria confirmo; con eso se libera el adeudo
        del usuario.

    Parametros:
        multa_id (int): id de la multa.

    Salida:
        flask.Response: redireccion a la multa, o la multa con los errores.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si no existe.
    """
    multa = _obtener_o_404(multa_id)["multa"]
    try:
        mensaje = multa_servicio.registrar_pago(
            multa, request.form, session["usuario_id"]
        )
    except ErrorValidacion as error:
        return _mostrar_detalle(
            multa_id,
            error.codigo,
            errores=error.errores,
            valores=error.valores,
            resultado=("error", error.mensaje),
        )
    flash(mensaje, "exito")
    return redirect(url_for("multas.mostrar_detalle", multa_id=multa_id))
