"""
============================================================
Archivo:      controllers/auth_controller.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Controlador de acceso web (HU-01-01): inicio y cierre de sesion.

    Papel en MVC: recibe el formulario, le pide al servicio de
    autenticacion que valide y decide que vista mostrar. Las reglas viven
    en services/auth_servicio.py.

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

from services import auth_servicio
from services.errores import ErrorValidacion
from utils.seguridad import iniciar_sesion

# Blueprint para las rutas de acceso.
auth_bp = Blueprint("auth", __name__)


def _obtener_destino_seguro(siguiente):
    """
    Descripcion:
        Regresa la ruta a la que se queria entrar solo si es interna, para no
        redirigir a otro sitio.

    Parametros:
        siguiente (str): ruta recibida en el formulario.

    Salida:
        str o None si la ruta no es interna.
    """
    return (
        siguiente
        if siguiente.startswith("/") and not siguiente.startswith("//")
        else None
    )


@auth_bp.route("/")
def redirigir_raiz():
    """
    Descripcion:
        Manda al panel si hay sesion; si no, a la pantalla de acceso.

    Parametros:
        Ninguno.

    Salida:
        flask.Response: redireccion al panel o al login.
    """
    if "usuario_id" in session:
        return redirect(url_for("inicio.mostrar_panel"))
    return redirect(url_for("auth.ingresar"))


@auth_bp.route("/login", methods=["GET", "POST"])
def ingresar():
    """
    Descripcion:
        HU-01-01: Muestra la pantalla de acceso (GET) y procesa el inicio de
        sesion (POST). Si falla algun criterio la sesion queda cerrada y se
        muestra su mensaje.

    Parametros:
        Ninguno.

    Salida:
        str: pagina HTML de la vista del login con el error y su codigo HTTP, o
        flask.Response: redireccion al panel o a la ruta que se queria abrir.
    """
    # GET: si ya hay sesion va al panel; si no, formulario vacio.
    if request.method == "GET":
        if "usuario_id" in session:
            return redirect(url_for("inicio.mostrar_panel"))
        return render_template("auth/login.html", valores={}, errores={})

    # POST: el servicio valida cuenta, contrasena, estado y perfil.
    siguiente = request.form.get("siguiente", "")
    try:
        datos = auth_servicio.autenticar(
            request.form.get("cuenta"), request.form.get("contrasena")
        )
    except ErrorValidacion as error:
        # HU-01-01: cualquier criterio no cumplido deja la sesion cerrada y
        # muestra su mensaje.
        session.clear()
        return render_template(
            "auth/login.html",
            valores=error.valores,
            errores=error.errores,
            error_general=error.mensaje,
            siguiente=siguiente,
        ), error.codigo

    # HU-01-01 · Inicio de sesion exitoso: guardamos la sesion y vamos al panel
    # (o a donde queria entrar).
    iniciar_sesion(datos["usuario"], datos["perfil"], datos["permisos"])
    flash(datos["bienvenida"], "exito")
    return redirect(
        _obtener_destino_seguro(siguiente) or url_for("inicio.mostrar_panel")
    )


@auth_bp.route("/logout")
def salir():
    """
    Descripcion:
        Cierra la sesion y regresa a la pantalla de acceso.

    Parametros:
        Ninguno.

    Salida:
        flask.Response: redireccion al login.
    """
    session.clear()
    flash("Cerraste sesión correctamente.", "informacion")
    return redirect(url_for("auth.ingresar"))
