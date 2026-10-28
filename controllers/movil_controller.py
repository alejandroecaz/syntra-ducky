"""Controlador del portal móvil para alumnos (/movil).

Papel en MVC: es otro controlador sobre el MISMO modelo y los MISMOS servicios que la web.
Solo cambia la vista (views/movil/ con su layout para celular). El acceso se controla con el
permiso "movil.acceder", que solo tiene el perfil Alumno.
"""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

import config
from services import auth_servicio, catalogo_servicio
from services.errores import ErrorValidacion
from utils.seguridad import iniciar_sesion, permiso_requerido, tiene_permiso

movil_bp = Blueprint("movil", __name__, url_prefix="/movil")


def _acceso_movil(vista):
    # Sin sesión manda a /movil/login; sin el permiso responde 403 con la vista móvil
    return permiso_requerido(config.PERMISO_MOVIL, login="movil.login")(vista)


@movil_bp.errorhandler(403)
def acceso_no_autorizado(_error):
    return render_template("movil/acceso_denegado.html", mensaje=config.MENSAJES["login_solo_alumnos"]), 403


@movil_bp.errorhandler(404)
def no_encontrado(_error):
    return render_template("movil/no_encontrado.html"), 404


@movil_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if tiene_permiso(config.PERMISO_MOVIL):
            return redirect(url_for("movil.buscar"))
        return render_template("movil/login.html", valores={}, errores={})

    try:
        datos = auth_servicio.autenticar_portal_movil(request.form.get("cuenta"), request.form.get("contrasena"))
    except ErrorValidacion as error:
        session.clear()
        return render_template("movil/login.html", valores=error.valores, errores=error.errores,
                               error_general=error.mensaje), error.codigo

    iniciar_sesion(datos["usuario"], datos["perfil"], datos["permisos"])
    return redirect(url_for("movil.buscar"))


@movil_bp.route("")
@_acceso_movil
def buscar():
    # Sin búsqueda muestra el resumen y "Disponibles ahora"; con búsqueda, los resultados
    buscando = "buscar" in request.args
    ver_catalogo = request.args.get("ver") == "catalogo"
    contexto = {"buscando": buscando, "ver_catalogo": ver_catalogo,
                "campo": catalogo_servicio.campo_valido(request.args.get("campo")), "texto": "",
                "libros": [], "error": None}

    if buscando:
        contexto.update(catalogo_servicio.buscar_libros(request.args.get("campo"), request.args.get("q")))
        # Si el texto venía vacío se conserva lo que escribió (solo espacios)
        contexto["texto"] = contexto["texto"] or request.args.get("q", "")
    elif ver_catalogo:
        contexto["libros"] = catalogo_servicio.listar_catalogo()
    else:
        contexto["libros"] = catalogo_servicio.destacados()
        contexto["resumen"] = catalogo_servicio.resumen()

    return render_template("movil/buscar.html", **contexto)


@movil_bp.route("/libros/<int:libro_id>")
@_acceso_movil
def detalle(libro_id):
    ficha = catalogo_servicio.ficha(libro_id)
    if ficha is None:
        return no_encontrado(None)
    # Para que "Volver" regrese a la misma búsqueda
    volver = {clave: request.args[clave] for clave in ("campo", "q", "buscar", "ver") if clave in request.args}
    return render_template("movil/detalle.html", **ficha, volver=volver)


@movil_bp.route("/logout")
def logout():
    session.clear()
    flash("Cerraste sesión correctamente.", "info")
    return redirect(url_for("movil.login"))
