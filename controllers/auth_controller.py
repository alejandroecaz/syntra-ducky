"""Controlador de acceso web (HU-01-01): inicio y cierre de sesión.

Papel en MVC: recibe el formulario, le pide al servicio de autenticación que valide
y decide qué vista mostrar. Las reglas viven en services/auth_servicio.py.
"""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from services import auth_servicio
from services.errores import ErrorValidacion
from utils.seguridad import iniciar_sesion

auth_bp = Blueprint("auth", __name__)

# Cuentas de prueba que se muestran en el login: (cuenta, contraseña, perfil, nota)
CUENTAS_DEMO = [
    ("admin", "Admin123", "Administrador", "Acceso total"),
    ("biblio", "Biblio123", "Bibliotecario", "Catálogo y compras"),
    ("profesor", "Profe123", "Profesor", "Consulta y reportes"),
    ("alumno", "Alumno123", "Alumno", "Consulta y portal móvil"),
    ("deshabilitado", "Demo123", "Alumno", "Cuenta deshabilitada"),
    ("visitante", "Demo123", "Visitante", "Perfil sin acceso"),
]


def _destino_seguro(siguiente):
    # Solo rutas internas, para no redirigir a otro sitio
    return siguiente if siguiente.startswith("/") and not siguiente.startswith("//") else None


@auth_bp.route("/")
def raiz():
    if "usuario_id" in session:
        return redirect(url_for("inicio.panel"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if "usuario_id" in session:
            return redirect(url_for("inicio.panel"))
        return render_template("auth/login.html", valores={}, errores={}, cuentas_demo=CUENTAS_DEMO)

    siguiente = request.form.get("siguiente", "")
    try:
        datos = auth_servicio.autenticar(request.form.get("cuenta"), request.form.get("contrasena"))
    except ErrorValidacion as error:
        session.clear()
        return render_template(
            "auth/login.html", valores=error.valores, errores=error.errores, error_general=error.mensaje,
            cuentas_demo=CUENTAS_DEMO, siguiente=siguiente,
        ), error.codigo

    iniciar_sesion(datos["usuario"], datos["perfil"], datos["permisos"])
    flash(datos["bienvenida"], "success")
    return redirect(_destino_seguro(siguiente) or url_for("inicio.panel"))


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Cerraste sesión correctamente.", "info")
    return redirect(url_for("auth.login"))
