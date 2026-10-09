from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from models import libro as libro_modelo
from models import orden_compra as orden_modelo
from utils.seguridad import permiso_requerido

compra_bp = Blueprint("compras", __name__, url_prefix="/compras")

CLAVE_BORRADOR = "borrador_orden"


def _libros_disponibles():
    return libro_modelo.listar(estado="activos")


def _validar(form):
    borrador = {
        "proveedor": form.get("proveedor", "").strip(),
        "fecha_requerida": form.get("fecha_requerida", "").strip(),
        "justificacion": form.get("justificacion", "").strip(),
    }
    errores = {}
    if not borrador["proveedor"]:
        errores["proveedor"] = "Indica el proveedor."
    if not borrador["fecha_requerida"]:
        errores["fecha_requerida"] = "Indica la fecha en que se requieren los libros."
    else:
        try:
            if date.fromisoformat(borrador["fecha_requerida"]) < date.today():
                errores["fecha_requerida"] = "La fecha requerida no puede ser anterior a hoy."
        except ValueError:
            errores["fecha_requerida"] = "Escribe una fecha válida."

    # Se guardan tal cual para regresarlos al formulario si hay error
    libros_ids = form.getlist("libro_id")
    cantidades = form.getlist("cantidad")
    items_formulario = [{"libro_id": l, "cantidad": c} for l, c in zip(libros_ids, cantidades)]
    activos = {str(libro["id"]) for libro in _libros_disponibles()}

    errores_items = []
    acumulado = {}
    for numero, item in enumerate(items_formulario, start=1):
        if not item["libro_id"] and not item["cantidad"]:
            continue
        if item["libro_id"] not in activos:
            errores_items.append(f"Selecciona el libro del renglón {numero}.")
            continue
        if not item["cantidad"].isdigit() or not 1 <= int(item["cantidad"]) <= 500:
            errores_items.append(f"Indica una cantidad entre 1 y 500 en el renglón {numero}.")
            continue
        # Si un libro se repite se suman las cantidades
        acumulado[int(item["libro_id"])] = acumulado.get(int(item["libro_id"]), 0) + int(item["cantidad"])

    if errores_items:
        errores["items"] = " ".join(errores_items)
    elif not acumulado:
        errores["items"] = "Agrega al menos un libro con su cantidad."

    borrador["items"] = [{"libro_id": k, "cantidad": v} for k, v in acumulado.items()]
    return borrador, errores, items_formulario


def _resolver_items(items):
    # Agrega los datos de cada libro a los renglones
    resueltos = []
    for item in items:
        libro = libro_modelo.obtener_por_id(item["libro_id"])
        if libro:
            resueltos.append({**dict(libro), "cantidad": item["cantidad"], "libro_id": libro["id"]})
    return resueltos


@compra_bp.route("")
@permiso_requerido("compras.orden")
def lista():
    return render_template("compras/lista.html", ordenes=orden_modelo.listar())


@compra_bp.route("/nueva", methods=["GET", "POST"])
@permiso_requerido("compras.orden")
def nueva():
    libros = _libros_disponibles()

    if request.method == "GET":
        borrador = session.get(CLAVE_BORRADOR) if request.args.get("modificar") else None
        if borrador:
            items = [{"libro_id": str(i["libro_id"]), "cantidad": str(i["cantidad"])} for i in borrador["items"]]
        else:
            session.pop(CLAVE_BORRADOR, None)
            borrador = {}
            libro_inicial = request.args.get("libro", "")
            items = [{"libro_id": libro_inicial, "cantidad": "1"}]
        return render_template("compras/form.html", libros=libros, valores=borrador, items=items,
                               errores={}, hoy=date.today().isoformat())

    borrador, errores, items_formulario = _validar(request.form)
    if errores:
        return render_template("compras/form.html", libros=libros, valores=borrador,
                               items=items_formulario or [{"libro_id": "", "cantidad": "1"}],
                               errores=errores, hoy=date.today().isoformat(),
                               error_general="Falta información para generar la orden. Completa los campos "
                                             "marcados."), 400

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
                           items=_resolver_items(borrador["items"]), hoy=date.today())


@compra_bp.route("/confirmar", methods=["POST"])
@permiso_requerido("compras.orden")
def confirmar():
    borrador = session.get(CLAVE_BORRADOR)
    if not borrador or not borrador.get("items"):
        flash("La orden ya no está disponible para confirmar. Vuelve a capturarla.", "warning")
        return redirect(url_for("compras.nueva"))

    orden_id, folio = orden_modelo.registrar(
        borrador["proveedor"], borrador["fecha_requerida"], borrador["justificacion"],
        session["usuario_id"], borrador["items"],
    )
    session.pop(CLAVE_BORRADOR, None)
    flash(f"Orden de compra {folio} registrada. Puedes consultarla en cualquier momento.", "success")
    return redirect(url_for("compras.detalle", orden_id=orden_id))


@compra_bp.route("/<int:orden_id>")
@permiso_requerido("compras.orden")
def detalle(orden_id):
    orden = orden_modelo.obtener(orden_id)
    if orden is None:
        abort(404)
    return render_template("compras/detalle.html", orden=orden, items=orden_modelo.items_de(orden_id))
