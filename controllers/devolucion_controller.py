"""
============================================================
Archivo:      controllers/devolucion_controller.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Controlador de devoluciones (HU-02-07 y HU-02-08).

    Papel en MVC: maneja el flujo buscar el ejemplar → capturar que paso
    con el libro → resultado con las multas; el calculo de las multas y
    el envio a Tesoreria estan en services/devolucion_servicio.py.

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
    session,
    url_for,
)

import config
from services import devolucion_servicio
from services.errores import ErrorValidacion
from utils import notificaciones
from utils.seguridad import permiso_requerido, verificar_permiso

# Blueprint para las rutas de devoluciones.
devolucion_bp = Blueprint("devoluciones", __name__, url_prefix="/devoluciones")

# Permiso de todas las pantallas de devoluciones.
PERMISO = "devoluciones.registrar"


def _mostrar_lista(valores=None, errores=None, error_general=None, codigo=200):
    """
    Descripcion:
        Pinta la busqueda del ejemplar con las ultimas devoluciones.

    Parametros:
        valores (dict o None): ejemplar capturado.
        errores (dict o None): errores por campo.
        error_general (str o None): mensaje del aviso.
        codigo (int): codigo HTTP de la respuesta.

    Salida:
        tuple[str, int]: pagina HTML y codigo HTTP.
    """
    return render_template(
        "devoluciones/lista.html",
        valores=valores or {},
        errores=errores or {},
        error_general=error_general,
        recientes=devolucion_servicio.listar_recientes(),
        **devolucion_servicio.obtener_opciones_formulario(),
    ), codigo


def _mostrar_formulario(prestamo, valores=None, errores=None, codigo=200):
    """
    Descripcion:
        Pinta la captura de la devolucion del prestamo con las multas que se
        generarian.

    Parametros:
        prestamo (sqlite3.Row): prestamo activo.
        valores (dict o None): lo capturado.
        errores (dict o None): errores por campo.
        codigo (int): codigo HTTP de la respuesta.

    Salida:
        tuple[str, int]: pagina HTML y codigo HTTP.
    """
    return render_template(
        "devoluciones/form.html",
        prestamo=prestamo,
        valores=valores or {"resultado": config.RESULTADO_BUENO},
        errores=errores or {},
        resultados=config.RESULTADOS_DEVOLUCION,
        correo_tesoreria=notificaciones.obtener_correo_tesoreria(),
        **devolucion_servicio.preparar(prestamo),
    ), codigo


# ============================================================
# REGISTRO DE LA DEVOLUCION (HU-02-07 Y HU-02-08)
# ============================================================


@devolucion_bp.route("")
@permiso_requerido(PERMISO)
def buscar():
    """
    Descripcion:
        HU-02-07: Busqueda del ejemplar que se devuelve. Si viene el codigo
        (?ejemplar=EJ-0019) y tiene un prestamo activo, muestra la captura
        de la devolucion.

    Parametros:
        Ninguno.

    Salida:
        tuple[str, int]: pagina HTML de la busqueda o de la captura.

    Excepciones:
        Responde 403 (werkzeug.exceptions.Forbidden) si el perfil no tiene el
        permiso; sin sesion redirige al login.
    """
    if "ejemplar" not in request.args:
        return _mostrar_lista()
    try:
        prestamo = devolucion_servicio.buscar_prestamo(
            request.args.get("ejemplar")
        )
    except ErrorValidacion as error:
        return _mostrar_lista(
            error.valores, error.errores, error.mensaje, error.codigo
        )
    return _mostrar_formulario(prestamo)


@devolucion_bp.route("/registrar", methods=["POST"])
@permiso_requerido(PERMISO)
def registrar():
    """
    Descripcion:
        HU-02-07 y HU-02-08: Registra la devolucion (o la perdida), genera
        las multas y las manda a Tesoreria.

    Parametros:
        Ninguno.

    Salida:
        flask.Response: redireccion al resultado, o la captura con los
        errores.

    Excepciones:
        Responde 403 (werkzeug.exceptions.Forbidden) si el perfil no tiene el
        permiso; sin sesion redirige al login.
    """
    codigo = request.form.get("ejemplar")
    try:
        prestamo_id, avisos = devolucion_servicio.registrar(
            codigo, request.form, session["usuario_id"]
        )
    except ErrorValidacion as error:
        # Si fallo un dato se regresa a la captura; si el prestamo ya no
        # esta activo, a la busqueda con el motivo.
        if error.codigo == 422:
            prestamo = devolucion_servicio.buscar_prestamo(codigo)
            return _mostrar_formulario(
                prestamo, error.valores, error.errores, error.codigo
            )
        return _mostrar_lista(
            {"ejemplar": codigo}, error.errores, error.mensaje, error.codigo
        )
    for tono, mensaje in avisos:
        flash(mensaje, tono)
    return redirect(
        url_for("devoluciones.mostrar_resultado", prestamo_id=prestamo_id)
    )


@devolucion_bp.route("/<int:prestamo_id>")
@permiso_requerido(PERMISO)
def mostrar_resultado(prestamo_id):
    """
    Descripcion:
        HU-02-07 y HU-02-08: Muestra como se cerro el prestamo y las multas
        que genero, con su envio a Tesoreria.

    Parametros:
        prestamo_id (int): id del prestamo.

    Salida:
        str: pagina HTML de la vista devoluciones/detalle.html.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si el prestamo no existe o sigue
        activo.
    """
    resultado = devolucion_servicio.obtener_resultado(prestamo_id)
    if resultado is None:
        abort(404)
    return render_template(
        "devoluciones/detalle.html",
        puede_ver_multas=verificar_permiso("multas.gestionar"),
        puede_ver_prestamo=verificar_permiso("prestamos.registrar"),
        **resultado,
    )
