"""Servicio de órdenes de compra (HU-01-18)."""
from datetime import date

import config
from models import libro as libro_modelo
from models import orden_compra as orden_modelo
from models import proveedor as proveedor_modelo
from services.errores import ErrorValidacion


def listar():
    """Órdenes registradas."""
    return orden_modelo.listar()


def obtener(orden_id):
    """(orden, renglones) o None si no existe."""
    orden = orden_modelo.obtener(orden_id)
    if orden is None:
        return None
    return orden, orden_modelo.items_de(orden_id)


def libros_disponibles():
    """Libros activos que se pueden pedir."""
    return libro_modelo.listar(estado="activos")


def proveedores():
    """Nombres de proveedores registrados (sugerencias del formulario)."""
    return proveedor_modelo.listar_nombres()


def renglones_de(borrador):
    """Renglones del borrador en el formato del formulario."""
    return [{"libro_id": str(i["libro_id"]), "cantidad": str(i["cantidad"])} for i in borrador["items"]]


def validar(form):
    """Valida la captura. Regresa el borrador o lanza ErrorValidacion.

    En el error, valores trae el borrador y "renglones" con lo capturado tal cual para regresarlo
    al formulario.
    """
    borrador = {
        "proveedor": (form.get("proveedor") or "").strip(),
        "fecha_requerida": (form.get("fecha_requerida") or "").strip(),
        "justificacion": (form.get("justificacion") or "").strip(),
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

    renglones = [{"libro_id": libro_id, "cantidad": cantidad}
                 for libro_id, cantidad in zip(form.getlist("libro_id"), form.getlist("cantidad"))]
    activos = {str(libro["id"]) for libro in libros_disponibles()}

    errores_renglones = []
    acumulado = {}
    for numero, renglon in enumerate(renglones, start=1):
        if not renglon["libro_id"] and not renglon["cantidad"]:
            continue
        if renglon["libro_id"] not in activos:
            errores_renglones.append(f"Selecciona el libro del renglón {numero}.")
            continue
        cantidad = renglon["cantidad"]
        if not cantidad.isdigit() or not 1 <= int(cantidad) <= config.CANTIDAD_MAXIMA_POR_LIBRO:
            errores_renglones.append(
                f"Indica una cantidad entre 1 y {config.CANTIDAD_MAXIMA_POR_LIBRO} en el renglón {numero}."
            )
            continue
        # Si un libro se repite se suman las cantidades
        libro_id = int(renglon["libro_id"])
        acumulado[libro_id] = acumulado.get(libro_id, 0) + int(cantidad)

    if errores_renglones:
        errores["items"] = " ".join(errores_renglones)
    elif not acumulado:
        errores["items"] = "Agrega al menos un libro con su cantidad."

    borrador["items"] = [{"libro_id": libro_id, "cantidad": cantidad} for libro_id, cantidad in acumulado.items()]
    if errores:
        raise ErrorValidacion("Falta información para generar la orden. Completa los campos marcados.",
                              errores, {**borrador, "renglones": renglones})
    return borrador


def resolver_items(items):
    """Agrega los datos de cada libro a los renglones del borrador."""
    resueltos = []
    for item in items:
        libro = libro_modelo.obtener_por_id(item["libro_id"])
        if libro:
            resueltos.append({**dict(libro), "cantidad": item["cantidad"], "libro_id": libro["id"]})
    return resueltos


def registrar(borrador, usuario_id):
    """Registra la orden confirmada. Regresa (id, mensaje)."""
    proveedor_id = proveedor_modelo.obtener_o_crear(borrador["proveedor"])
    orden_id, folio = orden_modelo.registrar(
        proveedor_id, borrador["fecha_requerida"], borrador["justificacion"], usuario_id, borrador["items"]
    )
    return orden_id, f"Orden de compra {folio} registrada. Puedes consultarla en cualquier momento."
