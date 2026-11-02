"""
============================================================
Archivo:      services/compra_servicio.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Servicio de ordenes de compra (HU-01-18).

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

from datetime import date

import config
from models import libro as libro_modelo
from models import orden_compra as orden_modelo
from models import proveedor as proveedor_modelo
from services.errores import ErrorValidacion


def listar():
    """
    Descripcion:
        HU-01-18: Lista las ordenes de compra registradas.

    Parametros:
        Ninguno.

    Salida:
        list[sqlite3.Row]: ordenes.
    """
    return orden_modelo.listar()


def obtener(orden_id):
    """
    Descripcion:
        HU-01-18 · Orden de compra registrada: obtiene la orden con sus
        renglones.

    Parametros:
        orden_id (int): id de la orden.

    Salida:
        tuple[sqlite3.Row, list[sqlite3.Row]] con la orden y sus renglones, o
        None si no existe.
    """
    orden = orden_modelo.obtener(orden_id)
    if orden is None:
        return None
    return orden, orden_modelo.listar_items(orden_id)


def listar_libros_disponibles():
    """
    Descripcion:
        Lista los libros activos que se pueden pedir.

    Parametros:
        Ninguno.

    Salida:
        list[sqlite3.Row]: libros activos.
    """
    return libro_modelo.listar(estado="activos")


def listar_proveedores():
    """
    Descripcion:
        Lista los nombres de los proveedores registrados para las sugerencias
        del formulario.

    Parametros:
        Ninguno.

    Salida:
        list[str]: nombres de proveedores.
    """
    return proveedor_modelo.listar_nombres()


def obtener_renglones(borrador):
    """
    Descripcion:
        HU-01-18 · Modificacion de la orden: convierte los renglones del
        borrador al formato del formulario.

    Parametros:
        borrador (dict): borrador guardado en la sesion.

    Salida:
        list[dict]: libro_id y cantidad como texto.
    """
    return [
        {"libro_id": str(item["libro_id"]), "cantidad": str(item["cantidad"])}
        for item in borrador["items"]
    ]


def validar(formulario):
    """
    Descripcion:
        HU-01-18: Valida la captura de la orden: proveedor, fecha no anterior a
        hoy y al menos un renglon con libro y cantidad validos. Si un libro se
        repite se suman las cantidades.

    Parametros:
        formulario (werkzeug.datastructures.MultiDict): datos capturados de la
            orden.

    Salida:
        dict: borrador con proveedor, fecha_requerida, justificacion e items.

    Excepciones:
        ErrorValidacion con los errores por campo; en valores trae el borrador
        y los renglones tal cual se capturaron.
    """
    # Leemos los datos generales de la orden.
    borrador = {
        "proveedor": (formulario.get("proveedor") or "").strip(),
        "fecha_requerida": (formulario.get("fecha_requerida") or "").strip(),
        "justificacion": (formulario.get("justificacion") or "").strip(),
    }

    # HU-01-18 · Datos incompletos de la orden: proveedor y fecha (no anterior
    # a hoy).
    errores = {}
    if not borrador["proveedor"]:
        errores["proveedor"] = "Indica el proveedor."
    if not borrador["fecha_requerida"]:
        errores["fecha_requerida"] = (
            "Indica la fecha en que se requieren los libros."
        )
    else:
        try:
            if date.fromisoformat(borrador["fecha_requerida"]) < date.today():
                errores["fecha_requerida"] = (
                    "La fecha requerida no puede ser anterior a hoy."
                )
        except ValueError:
            errores["fecha_requerida"] = "Escribe una fecha válida."

    # Juntamos cada libro con su cantidad y los libros activos que se pueden
    # pedir.
    renglones = [
        {"libro_id": libro_id, "cantidad": cantidad}
        for libro_id, cantidad in zip(
            formulario.getlist("libro_id"), formulario.getlist("cantidad")
        )
    ]
    activos = {str(libro["id"]) for libro in listar_libros_disponibles()}

    # Validamos renglon por renglon (los vacios se ignoran).
    errores_renglones = []
    acumulado = {}
    for numero, renglon in enumerate(renglones, start=1):
        if not renglon["libro_id"] and not renglon["cantidad"]:
            continue
        if renglon["libro_id"] not in activos:
            errores_renglones.append(
                f"Selecciona el libro del renglón {numero}."
            )
            continue
        cantidad = renglon["cantidad"]
        if (
            not cantidad.isdigit()
            or not 1 <= int(cantidad) <= config.CANTIDAD_MAXIMA_POR_LIBRO
        ):
            errores_renglones.append(
                "Indica una cantidad entre 1 y "
                f"{config.CANTIDAD_MAXIMA_POR_LIBRO} en el renglón {numero}."
            )
            continue
        # Si un libro se repite se suman las cantidades.
        libro_id = int(renglon["libro_id"])
        acumulado[libro_id] = acumulado.get(libro_id, 0) + int(cantidad)

    # La orden necesita al menos un renglon valido.
    if errores_renglones:
        errores["items"] = " ".join(errores_renglones)
    elif not acumulado:
        errores["items"] = "Agrega al menos un libro con su cantidad."

    # Regresamos el borrador o los errores con lo capturado para no perderlo.
    borrador["items"] = [
        {"libro_id": libro_id, "cantidad": cantidad}
        for libro_id, cantidad in acumulado.items()
    ]
    if errores:
        raise ErrorValidacion(
            "Falta información para generar la orden. Completa los campos "
            "marcados.",
            errores,
            {**borrador, "renglones": renglones},
        )
    return borrador


def resolver_items(items):
    """
    Descripcion:
        HU-01-18 · Vista previa: agrega los datos de cada libro a los renglones
        del borrador.

    Parametros:
        items (list[dict]): renglones con libro_id y cantidad.

    Salida:
        list[dict]: datos del libro con su cantidad.
    """
    resueltos = []
    for item in items:
        libro = libro_modelo.obtener_por_id(item["libro_id"])
        if libro:
            resueltos.append(
                {
                    **dict(libro),
                    "cantidad": item["cantidad"],
                    "libro_id": libro["id"],
                }
            )
    return resueltos


def registrar(borrador, usuario_id):
    """
    Descripcion:
        HU-01-18 · Orden de compra: registra la orden confirmada. El proveedor
        se registra si es nuevo.

    Parametros:
        borrador (dict): borrador validado.
        usuario_id (int): id de quien solicita.

    Salida:
        tuple[int, str]: id de la orden y mensaje con su folio.
    """
    # El proveedor se registra si es nuevo.
    proveedor_id = proveedor_modelo.obtener_o_crear(borrador["proveedor"])

    # Guardamos la orden con sus renglones y su folio.
    orden_id, folio = orden_modelo.registrar(
        proveedor_id,
        borrador["fecha_requerida"],
        borrador["justificacion"],
        usuario_id,
        borrador["items"],
    )
    return (
        orden_id,
        f"Orden de compra {folio} registrada. Puedes consultarla en "
        "cualquier momento.",
    )
