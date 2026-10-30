# ============================================================
# Archivo: controllers/cuenta_controller.py
# Proyecto: Sistema Ducky de Gestión Bibliotecaria
# Syntra Technologies - Equipo 1 - Sprint 1
# Materia: Ingeniería de Software
# Autores:
#   - Melissa Silva Vázquez                #624352
#   - Tomás Zapata Pérez                   #629048
#   - Alejandro Evaristo Cazares Escobedo  #626337
# Descripción: Controlador de la cuenta propia: cambio de contraseña (HU-01-06).
# ============================================================
"""Controlador de la cuenta propia: cambio de contraseña (HU-01-06).

Papel en MVC: recibe el formulario y delega la validación a services/auth_servicio.py.
"""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from services import auth_servicio
from services.errores import ErrorValidacion
from utils.seguridad import permiso_requerido

# Blueprint para las rutas de la cuenta propia
cuenta_bp = Blueprint("cuenta", __name__, url_prefix="/cuenta")


@cuenta_bp.route("/contrasena", methods=["GET", "POST"])
@permiso_requerido("cuenta.contrasena")
def contrasena():
    """HU-01-06: Muestra el formulario y cambia la contraseña de la cuenta en sesión."""
    # GET: formulario vacío
    if request.method == "GET":
        return render_template("cuenta/contrasena.html", errores={})

    # POST: si algo falla se conserva la contraseña anterior
    try:
        mensaje = auth_servicio.cambiar_contrasena(
            session["usuario_id"], request.form.get("actual", ""), request.form.get("nueva", ""),
            request.form.get("confirmacion", ""),
        )
    except ErrorValidacion as error:
        return render_template("cuenta/contrasena.html", errores=error.errores,
                               error_general=error.mensaje), error.codigo

    # HU-01-06 · Contraseña actualizada: volvemos al panel
    flash(mensaje, "success")
    return redirect(url_for("inicio.panel"))
