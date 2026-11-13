"""
============================================================
Archivo:      controllers/prestamo_controller.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Controlador de prestamos (HU-02-01 a HU-02-05).

    Papel en MVC: maneja el flujo captura → confirmacion → boleta,
    guardando el borrador en la sesion; las validaciones, el registro y
    el envio de la boleta estan en services/prestamo_servicio.py.

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
from services import prestamo_servicio
from services.errores import ErrorValidacion
from utils import notificaciones
from utils.seguridad import permiso_requerido, verificar_permiso

# Blueprint para las rutas de prestamos.
prestamo_bp = Blueprint("prestamos", __name__, url_prefix="/prestamos")

# Llave de la sesion donde vive el prestamo en captura.
CLAVE_BORRADOR = "borrador_prestamo"

# Permiso de todas las pantallas de prestamos.
PERMISO = "prestamos.registrar"


def _mostrar_formulario(valores, errores=None, error_general=None, codigo=200):
    """
    Descripcion:
        Pinta el formulario del prestamo con las sugerencias de usuarios y
        ejemplares.

    Parametros:
        valores (dict): usuario y ejemplar capturados.
        errores (dict o None): errores por campo.
        error_general (str o None): mensaje del aviso.
        codigo (int): codigo HTTP de la respuesta.

    Salida:
        tuple[str, int]: pagina HTML y codigo HTTP.
    """
    return render_template(
        "prestamos/form.html",
        valores=valores,
        errores=errores or {},
        error_general=error_general,
        **prestamo_servicio.obtener_opciones_formulario(),
    ), codigo


def _obtener_o_404(prestamo_id):
    """
    Descripcion:
        Busca el prestamo con sus boletas o responde 404.

    Parametros:
        prestamo_id (int): id del prestamo.

    Salida:
        tuple[sqlite3.Row, list[sqlite3.Row]]: prestamo y boletas emitidas.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si no existe.
    """
    resultado = prestamo_servicio.obtener(prestamo_id)
    if resultado is None:
        abort(404)
    return resultado


def _mostrar_detalle(prestamo_id, codigo=200, **extra):
    """
    Descripcion:
        Pinta la boleta con las opciones de envio; extra lleva errores,
        valores capturados o el resultado de la impresion.

    Parametros:
        prestamo_id (int): id del prestamo.
        codigo (int): codigo HTTP de la respuesta.
        **extra (dict): datos adicionales para la vista.

    Salida:
        tuple[str, int]: pagina HTML y codigo HTTP.
    """
    prestamo, comprobantes = _obtener_o_404(prestamo_id)
    contexto = {
        "errores": {},
        "valores": {},
        "resultado": None,
        "imprimir_ahora": False,
        "impresora_elegida": "",
    }
    contexto.update(extra)
    return render_template(
        "prestamos/detalle.html",
        prestamo=prestamo,
        comprobantes=comprobantes,
        datos_boleta=prestamo_servicio.armar_datos_boleta(prestamo),
        renovacion=prestamo_servicio.revisar_renovacion(prestamo),
        renovaciones=prestamo_servicio.listar_renovaciones(prestamo_id),
        puede_renovar=verificar_permiso("prestamos.renovar"),
        nota_boleta=prestamo_servicio.NOTA_BOLETA,
        vencido=prestamo_servicio.verificar_vencido(prestamo),
        impresoras=config.IMPRESORAS,
        correo_configurado=notificaciones.verificar_correo_configurado(),
        whatsapp_api=notificaciones.verificar_whatsapp_api_configurada(),
        **contexto,
    ), codigo


# ============================================================
# LISTA Y REGISTRO DEL PRESTAMO (HU-02-01 A HU-02-03)
# ============================================================


@prestamo_bp.route("")
@permiso_requerido(PERMISO)
def listar():
    """
    Descripcion:
        HU-02-03: Muestra los prestamos activos, vencidos o todos.

    Parametros:
        Ninguno.

    Salida:
        str: pagina HTML de la vista prestamos/lista.html.

    Excepciones:
        Responde 403 (werkzeug.exceptions.Forbidden) si el perfil no tiene el
        permiso; sin sesion redirige al login.
    """
    vista = prestamo_servicio.obtener_vista(request.args.get("ver"))
    return render_template(
        "prestamos/lista.html",
        prestamos=prestamo_servicio.listar(vista),
        vista=vista,
        verificar_vencido=prestamo_servicio.verificar_vencido,
    )


@prestamo_bp.route("/nuevo", methods=["GET", "POST"])
@permiso_requerido(PERMISO)
def registrar():
    """
    Descripcion:
        HU-02-01 y HU-02-02: Captura del prestamo (GET y POST). Si el usuario
        y el ejemplar cumplen las condiciones, guarda el borrador y pasa a la
        confirmacion.

    Parametros:
        Ninguno.

    Salida:
        str: pagina HTML del formulario con su codigo HTTP, o
        flask.Response: redireccion a la confirmacion.

    Excepciones:
        Responde 403 (werkzeug.exceptions.Forbidden) si el perfil no tiene el
        permiso; sin sesion redirige al login.
    """
    if request.method == "GET":
        # Puede venir con el ejemplar elegido desde la ficha del libro o con
        # la captura anterior para corregirla.
        borrador = (
            session.get(CLAVE_BORRADOR)
            if request.args.get("modificar")
            else None
        )
        if not borrador:
            session.pop(CLAVE_BORRADOR, None)
            borrador = {
                "usuario": request.args.get("usuario", ""),
                "ejemplar": request.args.get("ejemplar", ""),
            }
        return _mostrar_formulario(borrador)

    # POST: HU-02-01 y HU-02-02 · condiciones del solicitante y del libro.
    try:
        borrador = prestamo_servicio.validar(request.form)
    except ErrorValidacion as error:
        return _mostrar_formulario(
            error.valores, error.errores, error.mensaje, error.codigo
        )
    session[CLAVE_BORRADOR] = borrador
    return redirect(url_for("prestamos.confirmar"))


@prestamo_bp.route("/confirmar", methods=["GET", "POST"])
@permiso_requerido(PERMISO)
def confirmar():
    """
    Descripcion:
        HU-02-03: Muestra el resumen del prestamo (GET) y lo registra al
        confirmar (POST).

    Parametros:
        Ninguno.

    Salida:
        str: pagina HTML de la confirmacion, o flask.Response: redireccion a
        la boleta o a la captura.

    Excepciones:
        Responde 403 (werkzeug.exceptions.Forbidden) si el perfil no tiene el
        permiso; sin sesion redirige al login.
    """
    borrador = session.get(CLAVE_BORRADOR)
    if not borrador:
        flash(
            "No hay un préstamo en captura. Comienza uno nuevo.",
            "informacion",
        )
        return redirect(url_for("prestamos.registrar"))

    if request.method == "GET":
        return render_template(
            "prestamos/confirmar.html",
            **prestamo_servicio.resolver_borrador(borrador),
        )

    # POST: registramos; si algo cambio desde la captura se regresa al
    # formulario con el motivo.
    try:
        prestamo_id, mensaje = prestamo_servicio.registrar(
            borrador, session["usuario_id"]
        )
    except ErrorValidacion as error:
        session.pop(CLAVE_BORRADOR, None)
        return _mostrar_formulario(
            {
                "usuario": borrador.get("usuario", ""),
                "ejemplar": borrador.get("ejemplar", ""),
            },
            error.errores,
            error.mensaje,
            error.codigo,
        )
    session.pop(CLAVE_BORRADOR, None)
    flash(mensaje, "exito")
    return redirect(
        url_for("prestamos.mostrar_detalle", prestamo_id=prestamo_id)
    )


# ============================================================
# RENOVACION DEL PRESTAMO (HU-02-05)
# ============================================================


@prestamo_bp.route("/<int:prestamo_id>/renovar", methods=["POST"])
@permiso_requerido("prestamos.renovar")
def renovar(prestamo_id):
    """
    Descripcion:
        HU-02-05: Renueva el prestamo si se cumplen las condiciones.

    Parametros:
        prestamo_id (int): id del prestamo.

    Salida:
        flask.Response: redireccion a la boleta con la nueva fecha, o la
        boleta con el motivo por el que no se renovo.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si no existe. Responde 403 si el
        perfil no tiene el permiso.
    """
    prestamo, _ = _obtener_o_404(prestamo_id)
    try:
        mensaje = prestamo_servicio.renovar(prestamo)
    except ErrorValidacion as error:
        # El motivo ya se muestra en la tarjeta de renovacion.
        return _mostrar_detalle(prestamo_id, error.codigo)
    flash(mensaje, "exito")
    return redirect(
        url_for("prestamos.mostrar_detalle", prestamo_id=prestamo_id)
    )


# ============================================================
# BOLETA DE PRESTAMO (HU-02-04)
# ============================================================


@prestamo_bp.route("/<int:prestamo_id>")
@permiso_requerido(PERMISO)
def mostrar_detalle(prestamo_id):
    """
    Descripcion:
        HU-02-04: Muestra la boleta del prestamo con las opciones para
        enviarla por correo, WhatsApp o imprimirla.

    Parametros:
        prestamo_id (int): id del prestamo (viene en la URL).

    Salida:
        tuple[str, int]: pagina HTML de la vista prestamos/detalle.html.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si no existe. Responde 403 si el
        perfil no tiene el permiso; sin sesion redirige al login.
    """
    return _mostrar_detalle(prestamo_id)


@prestamo_bp.route("/<int:prestamo_id>/boleta.pdf")
@permiso_requerido(PERMISO)
def descargar_boleta(prestamo_id):
    """
    Descripcion:
        HU-02-04: Descarga la boleta en PDF.

    Parametros:
        prestamo_id (int): id del prestamo.

    Salida:
        flask.Response con el archivo PDF.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si no existe.
    """
    prestamo, _ = _obtener_o_404(prestamo_id)
    contenido, nombre = prestamo_servicio.generar_pdf_boleta(prestamo)
    return send_file(
        BytesIO(contenido),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=nombre,
    )


@prestamo_bp.route("/<int:prestamo_id>/boleta/correo", methods=["POST"])
@permiso_requerido(PERMISO)
def enviar_correo(prestamo_id):
    """
    Descripcion:
        HU-02-04 · Envio por correo: manda la boleta con el PDF adjunto.

    Parametros:
        prestamo_id (int): id del prestamo.

    Salida:
        flask.Response: redireccion a la boleta con el aviso, o la boleta con
        el error del correo.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si no existe.
    """
    prestamo, _ = _obtener_o_404(prestamo_id)
    try:
        tono, mensaje = prestamo_servicio.enviar_por_correo(
            prestamo, request.form.get("correo")
        )
    except ErrorValidacion as error:
        return _mostrar_detalle(
            prestamo_id,
            error.codigo,
            errores=error.errores,
            valores=error.valores,
            resultado=("error", error.mensaje),
        )
    flash(mensaje, tono)
    return redirect(
        url_for("prestamos.mostrar_detalle", prestamo_id=prestamo_id)
    )


@prestamo_bp.route("/<int:prestamo_id>/boleta/whatsapp", methods=["POST"])
@permiso_requerido(PERMISO)
def enviar_whatsapp(prestamo_id):
    """
    Descripcion:
        HU-02-04 · Envio por WhatsApp: con API manda el mensaje; sin API abre
        WhatsApp con la boleta escrita (enlace wa.me).

    Parametros:
        prestamo_id (int): id del prestamo.

    Salida:
        flask.Response: redireccion a WhatsApp o a la boleta, o la boleta con
        el error del telefono.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si no existe.
    """
    prestamo, _ = _obtener_o_404(prestamo_id)
    try:
        tipo, valor = prestamo_servicio.enviar_por_whatsapp(
            prestamo, request.form.get("telefono")
        )
    except ErrorValidacion as error:
        return _mostrar_detalle(
            prestamo_id,
            error.codigo,
            errores=error.errores,
            valores=error.valores,
            resultado=("error", error.mensaje),
        )
    if tipo == "enlace":
        return redirect(valor)
    flash(valor, tipo)
    return redirect(
        url_for("prestamos.mostrar_detalle", prestamo_id=prestamo_id)
    )


@prestamo_bp.route("/<int:prestamo_id>/boleta/imprimir", methods=["POST"])
@permiso_requerido(PERMISO)
def imprimir_boleta(prestamo_id):
    """
    Descripcion:
        HU-02-04 · Boleta impresa: revisa la impresora y abre el dialogo de
        impresion con la boleta.

    Parametros:
        prestamo_id (int): id del prestamo.

    Salida:
        tuple[str, int]: la boleta con el resultado de la impresion.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si no existe.
    """
    prestamo, _ = _obtener_o_404(prestamo_id)
    impresora = request.form.get("impresora", "")
    resultado, codigo = prestamo_servicio.imprimir(prestamo, impresora)
    return _mostrar_detalle(
        prestamo_id,
        codigo,
        resultado=resultado,
        imprimir_ahora=resultado[0] == "exito",
        impresora_elegida=impresora,
    )
