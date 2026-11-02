"""
============================================================
Archivo:      controllers/movil_controller.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Controlador del portal movil para alumnos (/movil).

    Papel en MVC: es otro controlador sobre el MISMO modelo y los MISMOS
    servicios que la web. Solo cambia la vista (views/movil/ con su layout
    para celular). El acceso se controla con el permiso "movil.acceder",
    que solo tiene el perfil Alumno.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

import config
from services import auth_servicio, catalogo_servicio
from services.errores import ErrorValidacion
from utils.seguridad import (
    iniciar_sesion,
    permiso_requerido,
    verificar_permiso,
)

# Blueprint para las rutas del portal movil.
movil_bp = Blueprint("movil", __name__, url_prefix="/movil")


def _acceso_movil_requerido(vista):
    """
    Descripcion:
        Decorador del portal movil: sin sesion manda a /movil/login y sin el
        permiso movil.acceder responde 403 con la vista movil.

    Parametros:
        vista (function): funcion de la vista a proteger.

    Salida:
        function: la vista protegida.
    """
    return permiso_requerido(
        config.PERMISO_MOVIL, vista_login="movil.ingresar"
    )(vista)


@movil_bp.errorhandler(403)
def mostrar_acceso_no_autorizado(_error):
    """
    Descripcion:
        HU-01-01 · Acceso sin autorizacion en el portal movil, por ejemplo un
        profesor.

    Parametros:
        _error (Exception): error 403 (no se usa).

    Salida:
        tuple[str, int]: pagina movil/acceso_denegado.html y 403.
    """
    return render_template(
        "movil/acceso_denegado.html",
        mensaje=config.MENSAJES["login_solo_alumnos"],
    ), 403


@movil_bp.errorhandler(404)
def mostrar_no_encontrado(_error):
    """
    Descripcion:
        Muestra el aviso de libro inexistente o dado de baja en el portal
        movil.

    Parametros:
        _error (Exception o None): error 404 (no se usa).

    Salida:
        tuple[str, int]: pagina movil/no_encontrado.html y 404.
    """
    return render_template("movil/no_encontrado.html"), 404


@movil_bp.route("/login", methods=["GET", "POST"])
def ingresar():
    """
    Descripcion:
        HU-01-01 (movil): Inicio de sesion del portal, solo para alumnos.
        Aplica las mismas reglas y mensajes que la web.

    Parametros:
        Ninguno.

    Salida:
        str: pagina HTML de la vista movil/login.html con su codigo HTTP, o
        flask.Response: redireccion a la busqueda.
    """
    # GET: si ya tiene el permiso va directo a buscar.
    if request.method == "GET":
        if verificar_permiso(config.PERMISO_MOVIL):
            return redirect(url_for("movil.buscar"))
        return render_template("movil/login.html", valores={}, errores={})

    # POST: mismas reglas que la web mas el permiso movil.acceder.
    try:
        datos = auth_servicio.autenticar_portal_movil(
            request.form.get("cuenta"), request.form.get("contrasena")
        )
    except ErrorValidacion as error:
        session.clear()
        return render_template(
            "movil/login.html",
            valores=error.valores,
            errores=error.errores,
            error_general=error.mensaje,
        ), error.codigo

    # Guardamos la sesion y vamos a la busqueda.
    iniciar_sesion(datos["usuario"], datos["perfil"], datos["permisos"])
    return redirect(url_for("movil.buscar"))


@movil_bp.route("")
@_acceso_movil_requerido
def buscar():
    """
    Descripcion:
        HU-01-12 y HU-01-13 (movil): Inicio del portal con el resumen, el
        catalogo completo o los resultados de busqueda. Usa el mismo servicio
        que la web.

    Parametros:
        Ninguno.

    Salida:
        str: pagina HTML de la vista movil/buscar.html.

    Excepciones:
        Sin sesion redirige a /movil/login; sin el permiso responde 403.
    """
    # Sin busqueda muestra el resumen y "Disponibles ahora"; con busqueda, los
    # resultados.
    buscando = "buscar" in request.args
    ver_catalogo = request.args.get("ver") == "catalogo"
    contexto = {
        "buscando": buscando,
        "ver_catalogo": ver_catalogo,
        "campo": catalogo_servicio.validar_campo(request.args.get("campo")),
        "texto": "",
        "libros": [],
        "error": None,
    }

    # HU-01-13: busqueda con el mismo servicio que la web.
    if buscando:
        contexto.update(
            catalogo_servicio.buscar_libros(
                request.args.get("campo"), request.args.get("q")
            )
        )
        # Si el texto venia vacio se conserva lo que escribio (solo espacios).
        contexto["texto"] = contexto["texto"] or request.args.get("q", "")
    # HU-01-12 · Mostrar catalogo.
    elif ver_catalogo:
        contexto["libros"] = catalogo_servicio.listar_catalogo()
    # Pantalla de inicio: resumen y libros disponibles.
    else:
        contexto["libros"] = catalogo_servicio.listar_destacados()
        contexto["resumen"] = catalogo_servicio.obtener_resumen()

    return render_template("movil/buscar.html", **contexto)


@movil_bp.route("/libros/<int:libro_id>")
@_acceso_movil_requerido
def mostrar_detalle(libro_id):
    """
    Descripcion:
        HU-01-12, HU-01-14 y HU-01-15 (movil): Ficha del libro con su ubicacion
        y disponibilidad. Los libros dados de baja no se muestran.

    Parametros:
        libro_id (int): id del libro (viene en la URL).

    Salida:
        str: pagina HTML de la vista movil/detalle.html, o la pagina de no
        encontrado con 404.

    Excepciones:
        Sin sesion redirige a /movil/login; sin el permiso responde 403.
    """
    # Misma ficha que la web; los libros dados de baja no se muestran.
    ficha = catalogo_servicio.obtener_ficha(libro_id)
    if ficha is None:
        return mostrar_no_encontrado(None)

    # Para que "Volver" regrese a la misma busqueda.
    volver = {
        clave: request.args[clave]
        for clave in ("campo", "q", "buscar", "ver")
        if clave in request.args
    }
    return render_template("movil/detalle.html", **ficha, volver=volver)


@movil_bp.route("/logout")
def salir():
    """
    Descripcion:
        Cierra la sesion y regresa al login del portal movil.

    Parametros:
        Ninguno.

    Salida:
        flask.Response: redireccion a /movil/login.
    """
    session.clear()
    flash("Cerraste sesión correctamente.", "informacion")
    return redirect(url_for("movil.ingresar"))
