# ============================================================
# Archivo: controllers/auth_controller.py
# Proyecto: Sistema Ducky de Gestión Bibliotecaria
# Syntra Technologies - Equipo 1 - Sprint 1
# Materia: Ingeniería de Software
# Autores:
#   - Melissa Silva Vázquez                #624352
#   - Tomás Zapata Pérez                   #629048
#   - Alejandro Evaristo Cazares Escobedo  #626337
# Descripción: Controlador de acceso web (HU-01-01): inicio y cierre de sesión.
# ============================================================
"""Controlador de acceso web (HU-01-01): inicio y cierre de sesión.

Papel en MVC: recibe el formulario, le pide al servicio de autenticación que valide
y decide qué vista mostrar. Las reglas viven en services/auth_servicio.py.
"""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from services import auth_servicio
from services.errores import ErrorValidacion
from utils.seguridad import iniciar_sesion

# Blueprint para las rutas de acceso
auth_bp = Blueprint("auth", __name__)


def _destino_seguro(siguiente):
    """Regresa la ruta a la que se quería entrar solo si es interna, para no redirigir a otro sitio."""
    return siguiente if siguiente.startswith("/") and not siguiente.startswith("//") else None


@auth_bp.route("/")
def raiz():
    """Manda al panel si hay sesión; si no, a la pantalla de acceso."""
    if "usuario_id" in session:
        return redirect(url_for("inicio.panel"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """HU-01-01: Muestra la pantalla de acceso y procesa el inicio de sesión."""
    # GET: si ya hay sesión va al panel; si no, formulario vacío
    if request.method == "GET":
        if "usuario_id" in session:
            return redirect(url_for("inicio.panel"))
        return render_template("auth/login.html", valores={}, errores={})

    # POST: el servicio valida cuenta, contraseña, estado y perfil
    siguiente = request.form.get("siguiente", "")
    try:
        datos = auth_servicio.autenticar(request.form.get("cuenta"), request.form.get("contrasena"))
    except ErrorValidacion as error:
        # HU-01-01: cualquier criterio no cumplido deja la sesión cerrada y muestra su mensaje
        session.clear()
        return render_template(
            "auth/login.html", valores=error.valores, errores=error.errores, error_general=error.mensaje,
            siguiente=siguiente,
        ), error.codigo

    # HU-01-01 · Inicio de sesión exitoso: guardamos la sesión y vamos al panel (o a donde quería entrar)
    iniciar_sesion(datos["usuario"], datos["perfil"], datos["permisos"])
    flash(datos["bienvenida"], "success")
    return redirect(_destino_seguro(siguiente) or url_for("inicio.panel"))


@auth_bp.route("/logout")
def logout():
    """Cierra la sesión y regresa a la pantalla de acceso."""
    session.clear()
    flash("Cerraste sesión correctamente.", "info")
    return redirect(url_for("auth.login"))
