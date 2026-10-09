from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from models import usuario as usuario_modelo
from utils.seguridad import permiso_requerido

cuenta_bp = Blueprint("cuenta", __name__, url_prefix="/cuenta")


@cuenta_bp.route("/contrasena", methods=["GET", "POST"])
@permiso_requerido("cuenta.contrasena")
def contrasena():
    if request.method == "GET":
        return render_template("cuenta/contrasena.html", errores={})

    actual = request.form.get("actual", "")
    nueva = request.form.get("nueva", "")
    confirmacion = request.form.get("confirmacion", "")
    errores = {}

    if not actual:
        errores["actual"] = "Captura tu contraseña actual."
    if not nueva:
        errores["nueva"] = "Captura la nueva contraseña."
    elif len(nueva) < 6:
        errores["nueva"] = "La nueva contraseña debe tener al menos 6 caracteres."
    if not confirmacion:
        errores["confirmacion"] = "Confirma la nueva contraseña."

    def rechazar(mensaje):
        return render_template("cuenta/contrasena.html", errores=errores, error_general=mensaje), 400

    if errores:
        return rechazar("Completa los campos marcados. Tu contraseña no cambió.")

    if not usuario_modelo.validar_contrasena(session["usuario_id"], actual):
        errores["actual"] = "La contraseña actual no es válida."
        return rechazar("La contraseña actual no es válida. Se conserva tu contraseña anterior.")

    if nueva != confirmacion:
        errores["confirmacion"] = "Las contraseñas no coinciden."
        return rechazar("La nueva contraseña y su confirmación deben coincidir. Tu contraseña no cambió.")

    if nueva == actual:
        errores["nueva"] = "Elige una contraseña distinta a la actual."
        return rechazar("La nueva contraseña debe ser distinta a la actual.")

    usuario_modelo.cambiar_contrasena(session["usuario_id"], nueva)
    flash("Contraseña actualizada. A partir de tu siguiente inicio de sesión usa la nueva contraseña.", "success")
    return redirect(url_for("inicio.panel"))
