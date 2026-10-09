from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from models import perfil as perfil_modelo
from models import usuario as usuario_modelo
from utils.seguridad import iniciar_sesion

auth_bp = Blueprint("auth", __name__)

# Cuentas de prueba que se muestran en el login
CUENTAS_DEMO = [
    ("admin", "Admin123", "Administrador", "Acceso total"),
    ("biblio", "Biblio123", "Bibliotecario", "Catálogo y compras"),
    ("profesor", "Profe123", "Profesor", "Consulta y reportes"),
    ("alumno", "Alumno123", "Alumno", "Solo consulta"),
    ("deshabilitado", "Demo123", "Alumno", "Cuenta deshabilitada"),
    ("visitante", "Demo123", "Visitante", "Perfil sin acceso"),
]


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

    cuenta = request.form.get("cuenta", "").strip()
    contrasena = request.form.get("contrasena", "")
    siguiente = request.form.get("siguiente", "")
    valores = {"cuenta": cuenta}

    def rechazar(mensaje, errores=None):
        session.clear()
        return render_template(
            "auth/login.html",
            valores=valores,
            errores=errores or {},
            error_general=mensaje,
            cuentas_demo=CUENTAS_DEMO,
            siguiente=siguiente,
        ), 400

    errores = {}
    if not cuenta:
        errores["cuenta"] = "Captura tu cuenta."
    if not contrasena:
        errores["contrasena"] = "Captura tu contraseña."
    if errores:
        return rechazar("Completa los campos obligatorios para iniciar sesión.", errores)

    usuario = usuario_modelo.obtener_para_login(cuenta)
    if usuario is None or not check_password_hash(usuario["contrasena"], contrasena):
        return rechazar("Cuenta o contraseña incorrecta")

    if usuario["estado"] != "Habilitada":
        return rechazar("La cuenta no está habilitada. Comunícate con el administrador de la biblioteca.")

    perfil = perfil_modelo.obtener_por_id(usuario["perfil_id"]) if usuario["perfil_id"] else None
    permisos = perfil_modelo.permisos_de(perfil["id"]) if perfil else []
    if perfil is None or not perfil["disponible"] or "sistema.acceder" not in permisos:
        return rechazar("Tu perfil de usuario no tiene autorización para acceder al sistema.")

    iniciar_sesion(usuario, perfil["nombre"], permisos)
    flash(f"Bienvenido(a), {usuario['nombre'].split()[0]}. Sesión iniciada como {perfil['nombre']}.", "success")
    if siguiente.startswith("/") and not siguiente.startswith("//"):
        return redirect(siguiente)
    return redirect(url_for("inicio.panel"))


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Cerraste sesión correctamente.", "info")
    return redirect(url_for("auth.login"))
