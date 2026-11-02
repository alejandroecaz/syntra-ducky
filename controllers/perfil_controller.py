"""
============================================================
Archivo:      controllers/perfil_controller.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Controlador de perfiles y permisos (HU-01-07 y consulta para
    HU-01-08).

    Papel en MVC: recibe la peticion, llama a services/perfil_servicio.py
    y regresa la vista.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for

from services import perfil_servicio
from services.errores import ErrorValidacion
from utils.seguridad import permiso_requerido

# Blueprint para las rutas de perfiles.
perfil_bp = Blueprint("perfiles", __name__, url_prefix="/perfiles")


@perfil_bp.route("")
@permiso_requerido("perfiles.crear", "perfiles.asignar")
def listar():
    """
    Descripcion:
        HU-01-07 y HU-01-08: Muestra los perfiles con sus permisos.

    Parametros:
        Ninguno.

    Salida:
        str: pagina HTML de la vista perfiles/lista.html.

    Excepciones:
        Responde 403 (werkzeug.exceptions.Forbidden) si el perfil no tiene el
        permiso; sin sesion redirige al login.
    """
    return render_template(
        "perfiles/lista.html",
        perfiles=perfil_servicio.listar(),
        permisos=perfil_servicio.listar_permisos_por_perfil(),
        descripciones=perfil_servicio.obtener_descripciones(),
        resaltar=request.args.get("resaltar", type=int),
    )


@perfil_bp.route("/nuevo", methods=["GET", "POST"])
@permiso_requerido("perfiles.crear")
def registrar():
    """
    Descripcion:
        HU-01-07: Muestra el formulario (GET) y crea el perfil con sus permisos
        (POST).

    Parametros:
        Ninguno.

    Salida:
        str: pagina HTML de la vista del formulario con su codigo HTTP, o
        flask.Response: redireccion a la lista con el perfil nuevo resaltado.

    Excepciones:
        Responde 403 (werkzeug.exceptions.Forbidden) si el perfil no tiene el
        permiso; sin sesion redirige al login.
    """
    # GET: formulario vacio con los permisos agrupados.
    grupos = perfil_servicio.agrupar_permisos()
    if request.method == "GET":
        return render_template(
            "perfiles/form.html",
            grupos=grupos,
            valores={},
            seleccionados=[],
            errores={},
        )

    # POST: HU-01-07 · Nombre duplicado / Perfil incompleto regresan al
    # formulario.
    try:
        perfil_id, mensaje = perfil_servicio.crear(request.form)
    except ErrorValidacion as error:
        return render_template(
            "perfiles/form.html",
            grupos=grupos,
            valores=error.valores,
            seleccionados=error.valores["permisos"],
            errores=error.errores,
            error_general=error.mensaje,
        ), error.codigo

    # HU-01-07 · Perfil creado: volvemos a la lista con el nuevo resaltado.
    flash(mensaje, "exito")
    return redirect(url_for("perfiles.listar", resaltar=perfil_id))
