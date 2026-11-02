"""
============================================================
Archivo:      controllers/cuenta_controller.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Controlador de la cuenta propia: cambio de contrasena (HU-01-06).

    Papel en MVC: recibe el formulario y delega la validacion a
    services/auth_servicio.py.

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
from utils.seguridad import permiso_requerido

# Blueprint para las rutas de la cuenta propia.
cuenta_bp = Blueprint("cuenta", __name__, url_prefix="/cuenta")


@cuenta_bp.route("/contrasena", methods=["GET", "POST"])
@permiso_requerido("cuenta.contrasena")
def cambiar_contrasena():
    """
    Descripcion:
        HU-01-06: Muestra el formulario (GET) y cambia la contrasena de la
        cuenta en sesion (POST). Si algo falla se conserva la anterior.

    Parametros:
        Ninguno.

    Salida:
        str: pagina HTML de la vista del formulario con su codigo HTTP, o
        flask.Response: redireccion al panel.

    Excepciones:
        Responde 403 (werkzeug.exceptions.Forbidden) si el perfil no tiene el
        permiso; sin sesion redirige al login.
    """
    # GET: formulario vacio.
    if request.method == "GET":
        return render_template("cuenta/contrasena.html", errores={})

    # POST: si algo falla se conserva la contrasena anterior.
    try:
        mensaje = auth_servicio.cambiar_contrasena(
            session["usuario_id"],
            request.form.get("actual", ""),
            request.form.get("nueva", ""),
            request.form.get("confirmacion", ""),
        )
    except ErrorValidacion as error:
        return render_template(
            "cuenta/contrasena.html",
            errores=error.errores,
            error_general=error.mensaje,
        ), error.codigo

    # HU-01-06 · Contrasena actualizada: volvemos al panel.
    flash(mensaje, "exito")
    return redirect(url_for("inicio.mostrar_panel"))
