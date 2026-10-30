# ============================================================
# Archivo: controllers/movil_controller.py
# Proyecto: Sistema Ducky de Gestión Bibliotecaria
# Syntra Technologies - Equipo 1 - Sprint 1
# Materia: Ingeniería de Software
# Autores:
#   - Melissa Silva Vázquez                #624352
#   - Tomás Zapata Pérez                   #629048
#   - Alejandro Evaristo Cazares Escobedo  #626337
# Descripción: Controlador del portal móvil para alumnos (/movil).
# ============================================================
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

# Blueprint para las rutas del portal móvil
movil_bp = Blueprint("movil", __name__, url_prefix="/movil")


def _acceso_movil(vista):
    """Sin sesión manda a /movil/login; sin el permiso responde 403 con la vista móvil."""
    return permiso_requerido(config.PERMISO_MOVIL, login="movil.login")(vista)


@movil_bp.errorhandler(403)
def acceso_no_autorizado(_error):
    """HU-01-01 · Acceso sin autorización en el portal móvil (por ejemplo, un profesor)."""
    return render_template("movil/acceso_denegado.html", mensaje=config.MENSAJES["login_solo_alumnos"]), 403


@movil_bp.errorhandler(404)
def no_encontrado(_error):
    """El libro no existe o ya fue dado de baja."""
    return render_template("movil/no_encontrado.html"), 404


@movil_bp.route("/login", methods=["GET", "POST"])
def login():
    """HU-01-01 (móvil): Inicio de sesión del portal, solo para alumnos."""
    # GET: si ya tiene el permiso va directo a buscar
    if request.method == "GET":
        if tiene_permiso(config.PERMISO_MOVIL):
            return redirect(url_for("movil.buscar"))
        return render_template("movil/login.html", valores={}, errores={})

    # POST: mismas reglas que la web más el permiso movil.acceder
    try:
        datos = auth_servicio.autenticar_portal_movil(request.form.get("cuenta"), request.form.get("contrasena"))
    except ErrorValidacion as error:
        session.clear()
        return render_template("movil/login.html", valores=error.valores, errores=error.errores,
                               error_general=error.mensaje), error.codigo

    # Guardamos la sesión y vamos a la búsqueda
    iniciar_sesion(datos["usuario"], datos["perfil"], datos["permisos"])
    return redirect(url_for("movil.buscar"))


@movil_bp.route("")
@_acceso_movil
def buscar():
    """HU-01-12 y HU-01-13 (móvil): Inicio del portal, catálogo completo o resultados de búsqueda."""
    # Sin búsqueda muestra el resumen y "Disponibles ahora"; con búsqueda, los resultados
    buscando = "buscar" in request.args
    ver_catalogo = request.args.get("ver") == "catalogo"
    contexto = {"buscando": buscando, "ver_catalogo": ver_catalogo,
                "campo": catalogo_servicio.campo_valido(request.args.get("campo")), "texto": "",
                "libros": [], "error": None}

    # HU-01-13: búsqueda con el mismo servicio que la web
    if buscando:
        contexto.update(catalogo_servicio.buscar_libros(request.args.get("campo"), request.args.get("q")))
        # Si el texto venía vacío se conserva lo que escribió (solo espacios)
        contexto["texto"] = contexto["texto"] or request.args.get("q", "")
    # HU-01-12 · Mostrar catálogo
    elif ver_catalogo:
        contexto["libros"] = catalogo_servicio.listar_catalogo()
    # Pantalla de inicio: resumen y libros disponibles
    else:
        contexto["libros"] = catalogo_servicio.destacados()
        contexto["resumen"] = catalogo_servicio.resumen()

    return render_template("movil/buscar.html", **contexto)


@movil_bp.route("/libros/<int:libro_id>")
@_acceso_movil
def detalle(libro_id):
    """HU-01-12, HU-01-14 y HU-01-15 (móvil): Ficha del libro con ubicación y disponibilidad."""
    # Misma ficha que la web; los libros dados de baja no se muestran
    ficha = catalogo_servicio.ficha(libro_id)
    if ficha is None:
        return no_encontrado(None)

    # Para que "Volver" regrese a la misma búsqueda
    volver = {clave: request.args[clave] for clave in ("campo", "q", "buscar", "ver") if clave in request.args}
    return render_template("movil/detalle.html", **ficha, volver=volver)


@movil_bp.route("/logout")
def logout():
    """Cierra la sesión y regresa al login del portal."""
    session.clear()
    flash("Cerraste sesión correctamente.", "info")
    return redirect(url_for("movil.login"))
