"""
============================================================
Archivo:      controllers/compra_controller.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Controlador de ordenes de compra (HU-01-18).

    Papel en MVC: maneja el flujo captura → vista previa → confirmacion
    guardando el borrador en la sesion; las validaciones y el registro
    estan en services/compra_servicio.py.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

from datetime import date

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

from services import compra_servicio
from services.errores import ErrorValidacion
from utils.seguridad import permiso_requerido

# Blueprint para las rutas de compras.
compra_bp = Blueprint("compras", __name__, url_prefix="/compras")

# Llave de la sesion donde vive la orden en captura y renglon inicial del
# formulario.
CLAVE_BORRADOR = "borrador_orden"
RENGLON_VACIO = {"libro_id": "", "cantidad": "1"}


def _mostrar_formulario(
    valores, renglones, errores=None, error_general=None, codigo=200
):
    """
    Descripcion:
        Pinta el formulario de la orden con los libros, proveedores y renglones
        capturados.

    Parametros:
        valores (dict): datos generales de la orden.
        renglones (list[dict] o None): renglones capturados.
        errores (dict o None): errores por campo.
        error_general (str o None): mensaje del aviso.
        codigo (int): codigo HTTP de la respuesta.

    Salida:
        tuple[str, int]: pagina HTML y codigo HTTP.
    """
    return render_template(
        "compras/form.html",
        libros=compra_servicio.listar_libros_disponibles(),
        proveedores=compra_servicio.listar_proveedores(),
        valores=valores,
        items=renglones or [RENGLON_VACIO],
        errores=errores or {},
        error_general=error_general,
        hoy=date.today().isoformat(),
    ), codigo


@compra_bp.route("")
@permiso_requerido("compras.orden")
def listar():
    """
    Descripcion:
        HU-01-18: Muestra las ordenes de compra registradas.

    Parametros:
        Ninguno.

    Salida:
        str: pagina HTML de la vista compras/lista.html.

    Excepciones:
        Responde 403 (werkzeug.exceptions.Forbidden) si el perfil no tiene el
        permiso; sin sesion redirige al login.
    """
    return render_template(
        "compras/lista.html", ordenes=compra_servicio.listar()
    )


@compra_bp.route("/nueva", methods=["GET", "POST"])
@permiso_requerido("compras.orden")
def registrar():
    """
    Descripcion:
        HU-01-18: Captura de la orden (GET y POST). Si la captura es valida,
        guarda el borrador en la sesion y pasa a la vista previa.

    Parametros:
        Ninguno.

    Salida:
        str: pagina HTML de la vista del formulario con su codigo HTTP, o
        flask.Response: redireccion a la vista previa.

    Excepciones:
        Responde 403 (werkzeug.exceptions.Forbidden) si el perfil no tiene el
        permiso; sin sesion redirige al login.
    """
    if request.method == "GET":
        # HU-01-18 · Modificacion de la orden: se regresa al formulario con el
        # borrador.
        borrador = (
            session.get(CLAVE_BORRADOR)
            if request.args.get("modificar")
            else None
        )
        if borrador:
            return _mostrar_formulario(
                borrador, compra_servicio.obtener_renglones(borrador)
            )
        # Orden nueva (puede venir con un libro preseleccionado desde la
        # ficha).
        session.pop(CLAVE_BORRADOR, None)
        return _mostrar_formulario(
            {}, [{"libro_id": request.args.get("libro", ""), "cantidad": "1"}]
        )

    # POST: HU-01-18 · Datos incompletos de la orden regresa al formulario.
    try:
        borrador = compra_servicio.validar(request.form)
    except ErrorValidacion as error:
        return _mostrar_formulario(
            error.valores,
            error.valores.get("renglones"),
            error.errores,
            error.mensaje,
            error.codigo,
        )

    # Guardamos el borrador en la sesion y vamos a la vista previa.
    session[CLAVE_BORRADOR] = borrador
    return redirect(url_for("compras.mostrar_vista_previa"))


@compra_bp.route("/vista-previa")
@permiso_requerido("compras.orden")
def mostrar_vista_previa():
    """
    Descripcion:
        HU-01-18: Muestra la orden antes de confirmarla.

    Parametros:
        Ninguno.

    Salida:
        str: pagina HTML de la vista compras/vista_previa.html, o
        flask.Response: redireccion si no hay orden en captura.

    Excepciones:
        Responde 403 (werkzeug.exceptions.Forbidden) si el perfil no tiene el
        permiso; sin sesion redirige al login.
    """
    # Si no hay orden en captura se empieza una nueva.
    borrador = session.get(CLAVE_BORRADOR)
    if not borrador:
        flash(
            "No hay una orden en captura. Comienza una nueva.", "informacion"
        )
        return redirect(url_for("compras.registrar"))

    # Pintamos la vista previa con los datos de cada libro.
    return render_template(
        "compras/vista_previa.html",
        orden=borrador,
        items=compra_servicio.resolver_items(borrador["items"]),
        hoy=date.today(),
    )


@compra_bp.route("/confirmar", methods=["POST"])
@permiso_requerido("compras.orden")
def confirmar():
    """
    Descripcion:
        HU-01-18 · Orden de compra: registra la orden confirmada y limpia el
        borrador.

    Parametros:
        Ninguno.

    Salida:
        flask.Response: redireccion a la orden registrada, o a la captura si ya
        no hay borrador.

    Excepciones:
        Responde 403 (werkzeug.exceptions.Forbidden) si el perfil no tiene el
        permiso; sin sesion redirige al login.
    """
    # El borrador debe seguir en la sesion.
    borrador = session.get(CLAVE_BORRADOR)
    if not borrador or not borrador.get("items"):
        flash(
            "La orden ya no está disponible para confirmar. Vuelve a "
            "capturarla.",
            "advertencia",
        )
        return redirect(url_for("compras.registrar"))

    # Registramos, limpiamos el borrador y mostramos la orden.
    orden_id, mensaje = compra_servicio.registrar(
        borrador, session["usuario_id"]
    )
    session.pop(CLAVE_BORRADOR, None)
    flash(mensaje, "exito")
    return redirect(url_for("compras.mostrar_detalle", orden_id=orden_id))


@compra_bp.route("/<int:orden_id>")
@permiso_requerido("compras.orden")
def mostrar_detalle(orden_id):
    """
    Descripcion:
        HU-01-18 · Orden de compra registrada: muestra una orden con sus
        renglones.

    Parametros:
        orden_id (int): id de la orden (viene en la URL).

    Salida:
        str: pagina HTML de la vista compras/detalle.html.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si la orden no existe. Responde 403
        (werkzeug.exceptions.Forbidden) si el perfil no tiene el permiso; sin
        sesion redirige al login.
    """
    resultado = compra_servicio.obtener(orden_id)
    if resultado is None:
        abort(404)
    orden, items = resultado
    return render_template("compras/detalle.html", orden=orden, items=items)
