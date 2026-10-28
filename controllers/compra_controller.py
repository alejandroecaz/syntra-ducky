"""Controlador de órdenes de compra (HU-01-18).

Papel en MVC: maneja el flujo captura → vista previa → confirmación guardando el borrador
en la sesión; las validaciones y el registro están en services/compra_servicio.py.
"""
from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from services import compra_servicio
from services.errores import ErrorValidacion
from utils.seguridad import permiso_requerido

compra_bp = Blueprint("compras", __name__, url_prefix="/compras")

CLAVE_BORRADOR = "borrador_orden"
RENGLON_VACIO = {"libro_id": "", "cantidad": "1"}


def _formulario(valores, renglones, errores=None, error_general=None, codigo=200):
    return render_template(
        "compras/form.html", libros=compra_servicio.libros_disponibles(),
        proveedores=compra_servicio.proveedores(), valores=valores, items=renglones or [RENGLON_VACIO],
        errores=errores or {}, error_general=error_general, hoy=date.today().isoformat(),
    ), codigo


@compra_bp.route("")
@permiso_requerido("compras.orden")
def lista():
    return render_template("compras/lista.html", ordenes=compra_servicio.listar())


@compra_bp.route("/nueva", methods=["GET", "POST"])
@permiso_requerido("compras.orden")
def nueva():
    if request.method == "GET":
        borrador = session.get(CLAVE_BORRADOR) if request.args.get("modificar") else None
        if borrador:
            return _formulario(borrador, compra_servicio.renglones_de(borrador))
        session.pop(CLAVE_BORRADOR, None)
        return _formulario({}, [{"libro_id": request.args.get("libro", ""), "cantidad": "1"}])

    try:
        borrador = compra_servicio.validar(request.form)
    except ErrorValidacion as error:
        return _formulario(error.valores, error.valores.get("renglones"), error.errores, error.mensaje,
                           error.codigo)

    session[CLAVE_BORRADOR] = borrador
    return redirect(url_for("compras.vista_previa"))


@compra_bp.route("/vista-previa")
@permiso_requerido("compras.orden")
def vista_previa():
    borrador = session.get(CLAVE_BORRADOR)
    if not borrador:
        flash("No hay una orden en captura. Comienza una nueva.", "info")
        return redirect(url_for("compras.nueva"))
    return render_template("compras/vista_previa.html", orden=borrador,
                           items=compra_servicio.resolver_items(borrador["items"]), hoy=date.today())


@compra_bp.route("/confirmar", methods=["POST"])
@permiso_requerido("compras.orden")
def confirmar():
    borrador = session.get(CLAVE_BORRADOR)
    if not borrador or not borrador.get("items"):
        flash("La orden ya no está disponible para confirmar. Vuelve a capturarla.", "warning")
        return redirect(url_for("compras.nueva"))

    orden_id, mensaje = compra_servicio.registrar(borrador, session["usuario_id"])
    session.pop(CLAVE_BORRADOR, None)
    flash(mensaje, "success")
    return redirect(url_for("compras.detalle", orden_id=orden_id))


@compra_bp.route("/<int:orden_id>")
@permiso_requerido("compras.orden")
def detalle(orden_id):
    resultado = compra_servicio.obtener(orden_id)
    if resultado is None:
        abort(404)
    orden, items = resultado
    return render_template("compras/detalle.html", orden=orden, items=items)
