from datetime import datetime
from io import BytesIO

from flask import (Blueprint, flash, jsonify, redirect, render_template, request, send_file,
                   session, url_for)

import config
from models import libro as libro_modelo
from utils.pdf import generar_listado
from utils.seguridad import permiso_requerido, tiene_permiso

reporte_bp = Blueprint("reportes", __name__, url_prefix="/reportes")


def _leer_filtros(origen):
    filtros = {
        "campo": origen.get("campo", "titulo"),
        "q": origen.get("q", "").strip(),
        "tema": origen.get("tema", ""),
        "editorial": origen.get("editorial", ""),
        "estado": origen.get("estado", "activos"),
    }
    # Solo el personal puede ver los libros dados de baja
    if not tiene_permiso("libros.alta", "libros.editar", "libros.baja") or filtros["estado"] not in (
        "activos", "baja", "todos"
    ):
        filtros["estado"] = "activos"
    return filtros


def _consultar(filtros):
    return libro_modelo.listar(
        campo=filtros["campo"], texto=filtros["q"], tema=filtros["tema"] or None,
        editorial=filtros["editorial"] or None, estado=filtros["estado"],
    )


def describir_filtros(filtros):
    partes = []
    if filtros["q"]:
        etiqueta = dict(config.CAMPOS_BUSQUEDA).get(filtros["campo"], "Texto")
        partes.append(f"{etiqueta} contiene \"{filtros['q']}\"")
    if filtros["tema"]:
        partes.append(f"Tema: {filtros['tema']}")
    if filtros["editorial"]:
        partes.append(f"Editorial: {filtros['editorial']}")
    partes.append({"activos": "Solo libros activos", "baja": "Solo dados de baja",
                   "todos": "Activos y dados de baja"}[filtros["estado"]])
    return " · ".join(partes)


def _quiere_json():
    return request.headers.get("X-Requested-With") == "fetch"


@reporte_bp.route("/libros")
@permiso_requerido("reportes.pdf", "reportes.imprimir")
def listado():
    filtros = _leer_filtros(request.args)
    return render_template(
        "reportes/listado.html",
        libros=_consultar(filtros),
        filtros=filtros,
        filtros_texto=describir_filtros(filtros),
        temas=libro_modelo.valores_distintos("tema"),
        editoriales=libro_modelo.valores_distintos("editorial"),
    )


# HU-01-16: listado en PDF

@reporte_bp.route("/libros/pdf")
@permiso_requerido("reportes.pdf")
def pdf():
    filtros = _leer_filtros(request.args)
    libros = _consultar(filtros)

    def responder_error(mensaje, codigo):
        if _quiere_json():
            return jsonify({"ok": False, "mensaje": mensaje}), codigo
        flash(mensaje, "error" if codigo >= 500 else "warning")
        return redirect(url_for("reportes.listado", **filtros))

    if not libros:
        return responder_error("No existen registros disponibles para el listado. No se generó el documento.", 422)

    try:
        contenido = generar_listado(libros, describir_filtros(filtros), session.get("nombre", ""))
    except Exception:
        return responder_error("El documento no pudo generarse. El listado sigue disponible para "
                               "intentarlo de nuevo.", 500)

    respuesta = send_file(
        BytesIO(contenido),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"listado_libros_{datetime.now():%Y%m%d_%H%M}.pdf",
    )
    respuesta.headers["X-Total-Registros"] = str(len(libros))
    return respuesta


# HU-01-17: imprimir listado

@reporte_bp.route("/libros/imprimir", methods=["GET", "POST"])
@permiso_requerido("reportes.imprimir")
def imprimir():
    origen = request.form if request.method == "POST" else request.args
    filtros = _leer_filtros(origen)
    libros = _consultar(filtros)
    contexto = dict(
        libros=libros,
        filtros=filtros,
        filtros_texto=describir_filtros(filtros),
        impresoras=config.IMPRESORAS,
        seleccionada=origen.get("impresora", ""),
        ahora=datetime.now(),
    )

    if request.method == "GET":
        return render_template("reportes/imprimir.html", **contexto)

    if not libros:
        contexto["resultado"] = ("warning", "No hay registros que imprimir con los filtros seleccionados.")
        return render_template("reportes/imprimir.html", **contexto), 422

    impresora = next((i for i in config.IMPRESORAS if i["id"] == contexto["seleccionada"]), None)
    if impresora is None:
        contexto["resultado"] = ("error", "Selecciona una impresora para enviar el listado.")
        return render_template("reportes/imprimir.html", **contexto), 400

    if not impresora["disponible"]:
        contexto["resultado"] = (
            "error",
            f"No fue posible enviar el documento a impresión: \"{impresora['nombre']}\" no está disponible. "
            "Selecciona otra impresora o cancela la operación.",
        )
        return render_template("reportes/imprimir.html", **contexto), 503

    contexto["resultado"] = (
        "success",
        f"Solicitud de impresión procesada: {len(libros)} registros enviados a \"{impresora['nombre']}\".",
    )
    contexto["imprimir_ahora"] = True
    return render_template("reportes/imprimir.html", **contexto)
