"""
============================================================
Archivo:      controllers/reporte_controller.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Controlador de reportes: listado, PDF (HU-01-16) e impresion
    (HU-01-17).

    Papel en MVC: lee los filtros y los libros elegidos de la peticion,
    llama a services/reporte_servicio.py y regresa la vista o el archivo
    PDF.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

from datetime import datetime
from io import BytesIO

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

import config
from services import catalogo_servicio, reporte_servicio
from services.errores import ErrorValidacion
from utils.seguridad import permiso_requerido

# Blueprint para las rutas de reportes.
reporte_bp = Blueprint("reportes", __name__, url_prefix="/reportes")


def _verificar_personal():
    """
    Descripcion:
        Revisa si el perfil en sesion es personal de biblioteca (puede incluir
        libros dados de baja).

    Parametros:
        Ninguno.

    Salida:
        bool: True si es personal.
    """
    return catalogo_servicio.verificar_personal(session.get("permisos", []))


def _verificar_peticion_fetch():
    """
    Descripcion:
        Revisa si la peticion viene del boton Generar PDF, que pide el archivo
        con fetch y espera JSON si hay error.

    Parametros:
        Ninguno.

    Salida:
        bool: True si la peticion se hizo con fetch.
    """
    return request.headers.get("X-Requested-With") == "fetch"


@reporte_bp.route("/libros")
@permiso_requerido("reportes.pdf", "reportes.imprimir")
def mostrar_listado():
    """
    Descripcion:
        HU-01-16 y HU-01-17: Listado de libros con filtros y casillas para
        elegir cuales entran al documento.

    Parametros:
        Ninguno.

    Salida:
        str: pagina HTML de la vista reportes/listado.html.

    Excepciones:
        Responde 403 (werkzeug.exceptions.Forbidden) si el perfil no tiene el
        permiso; sin sesion redirige al login.
    """
    filtros = reporte_servicio.leer_filtros(
        request.args, _verificar_personal()
    )
    return render_template(
        "reportes/listado.html",
        libros=reporte_servicio.consultar(filtros),
        filtros=filtros,
        filtros_texto=reporte_servicio.describir_filtros(filtros),
        seleccion=reporte_servicio.leer_seleccion(request.args),
        **reporte_servicio.obtener_opciones_filtros(),
    )


# ============================================================
# LISTADO EN PDF (HU-01-16)
# Genera el PDF con los libros filtrados o elegidos.
# ============================================================


@reporte_bp.route("/libros/pdf")
@permiso_requerido("reportes.pdf")
def descargar_pdf():
    """
    Descripcion:
        HU-01-16: Genera y descarga el PDF del listado.

    Parametros:
        Ninguno.

    Salida:
        flask.Response con el archivo PDF; si hay error, JSON con el mensaje
        (fetch) o flask.Response: redireccion al listado.

    Excepciones:
        Responde 403 (werkzeug.exceptions.Forbidden) si el perfil no tiene el
        permiso; sin sesion redirige al login.
    """
    # Preparamos los libros que entran y generamos el PDF.
    documento = reporte_servicio.preparar_documento(
        request.args, _verificar_personal()
    )
    try:
        contenido, total = reporte_servicio.generar_pdf(
            documento, session.get("nombre", "")
        )
    except ErrorValidacion as error:
        # HU-01-16 · Catalogo sin registros / Error durante la generacion.
        if _verificar_peticion_fetch():
            return jsonify(
                {"ok": False, "mensaje": error.mensaje}
            ), error.codigo
        flash(error.mensaje, "error" if error.codigo >= 500 else "advertencia")
        return redirect(
            url_for("reportes.mostrar_listado", **documento["parametros"])
        )

    # HU-01-16 · Generacion satisfactoria: mandamos el archivo con fecha en el
    # nombre.
    respuesta = send_file(
        BytesIO(contenido),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"listado_libros_{datetime.now():%Y%m%d_%H%M}.pdf",
    )
    respuesta.headers["X-Total-Registros"] = str(total)
    return respuesta


# ============================================================
# IMPRESION DEL LISTADO (HU-01-17)
# Vista previa y envio del listado a la impresora elegida.
# ============================================================


@reporte_bp.route("/libros/imprimir", methods=["GET", "POST"])
@permiso_requerido("reportes.imprimir")
def imprimir():
    """
    Descripcion:
        HU-01-17: Vista previa de impresion (GET) y envio a la impresora
        elegida (POST).

    Parametros:
        Ninguno.

    Salida:
        str: pagina HTML de la vista reportes/imprimir.html con su codigo HTTP.

    Excepciones:
        Responde 403 (werkzeug.exceptions.Forbidden) si el perfil no tiene el
        permiso; sin sesion redirige al login.
    """
    # Los filtros llegan en la URL (GET) o en el formulario (POST).
    origen = request.form if request.method == "POST" else request.args
    documento = reporte_servicio.preparar_documento(
        origen, _verificar_personal()
    )
    contexto = dict(
        **documento,
        impresoras=config.IMPRESORAS,
        seleccionada=origen.get("impresora", ""),
        ahora=datetime.now(),
    )

    # HU-01-17 · Vista previa de impresion.
    if request.method == "GET":
        return render_template("reportes/imprimir.html", **contexto)

    # HU-01-17 · Impresion satisfactoria / Impresora no disponible.
    resultado, codigo = reporte_servicio.enviar_a_impresion(
        documento, contexto["seleccionada"]
    )
    contexto["resultado"] = resultado
    contexto["imprimir_ahora"] = resultado[0] == "exito"
    return render_template("reportes/imprimir.html", **contexto), codigo
