"""Controlador de reportes: listado, PDF (HU-01-16) e impresión (HU-01-17).

Papel en MVC: lee los filtros y los libros elegidos de la petición, llama a
services/reporte_servicio.py y regresa la vista o el archivo PDF.
"""
from datetime import datetime
from io import BytesIO

from flask import Blueprint, flash, jsonify, redirect, render_template, request, send_file, session, url_for

import config
from services import catalogo_servicio, reporte_servicio
from services.errores import ErrorValidacion
from utils.seguridad import permiso_requerido

reporte_bp = Blueprint("reportes", __name__, url_prefix="/reportes")


def _es_personal():
    return catalogo_servicio.es_personal(session.get("permisos", []))


def _quiere_json():
    # El botón "Generar PDF" pide el archivo con fetch y espera JSON si hay error
    return request.headers.get("X-Requested-With") == "fetch"


@reporte_bp.route("/libros")
@permiso_requerido("reportes.pdf", "reportes.imprimir")
def listado():
    filtros = reporte_servicio.leer_filtros(request.args, _es_personal())
    return render_template(
        "reportes/listado.html",
        libros=reporte_servicio.consultar(filtros),
        filtros=filtros,
        filtros_texto=reporte_servicio.describir_filtros(filtros),
        seleccion=reporte_servicio.leer_seleccion(request.args),
        **reporte_servicio.opciones_filtros(),
    )


# HU-01-16: listado en PDF

@reporte_bp.route("/libros/pdf")
@permiso_requerido("reportes.pdf")
def pdf():
    documento = reporte_servicio.preparar_documento(request.args, _es_personal())
    try:
        contenido, total = reporte_servicio.generar_pdf(documento, session.get("nombre", ""))
    except ErrorValidacion as error:
        if _quiere_json():
            return jsonify({"ok": False, "mensaje": error.mensaje}), error.codigo
        flash(error.mensaje, "error" if error.codigo >= 500 else "warning")
        return redirect(url_for("reportes.listado", **documento["parametros"]))

    respuesta = send_file(
        BytesIO(contenido),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"listado_libros_{datetime.now():%Y%m%d_%H%M}.pdf",
    )
    respuesta.headers["X-Total-Registros"] = str(total)
    return respuesta


# HU-01-17: imprimir listado

@reporte_bp.route("/libros/imprimir", methods=["GET", "POST"])
@permiso_requerido("reportes.imprimir")
def imprimir():
    origen = request.form if request.method == "POST" else request.args
    documento = reporte_servicio.preparar_documento(origen, _es_personal())
    contexto = dict(
        **documento,
        impresoras=config.IMPRESORAS,
        seleccionada=origen.get("impresora", ""),
        ahora=datetime.now(),
    )
    if request.method == "GET":
        return render_template("reportes/imprimir.html", **contexto)

    resultado, codigo = reporte_servicio.enviar_a_impresion(documento, contexto["seleccionada"])
    contexto["resultado"] = resultado
    contexto["imprimir_ahora"] = resultado[0] == "success"
    return render_template("reportes/imprimir.html", **contexto), codigo
