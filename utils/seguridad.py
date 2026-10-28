"""Sesión y control de acceso por permisos (lo usan los controladores web y móvil)."""
from functools import wraps

from flask import abort, flash, redirect, request, session, url_for


def usuario_actual():
    """Datos de la sesión iniciada o None."""
    if "usuario_id" not in session:
        return None
    return {
        "id": session["usuario_id"],
        "nombre": session.get("nombre"),
        "cuenta": session.get("cuenta"),
        "perfil": session.get("perfil"),
    }


def tiene_permiso(*permisos):
    """True si el perfil en sesión tiene al menos uno de los permisos."""
    otorgados = session.get("permisos", [])
    return any(permiso in otorgados for permiso in permisos)


def iniciar_sesion(usuario, perfil_nombre, permisos):
    """Guarda en la sesión los datos de la cuenta autenticada."""
    session.clear()
    session["usuario_id"] = usuario["id"]
    session["nombre"] = usuario["nombre_completo"]
    session["cuenta"] = usuario["cuenta"]
    session["perfil"] = perfil_nombre
    session["permisos"] = permisos


def _exigir_sesion(vista, endpoint_login):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Inicia sesión para continuar.", "warning")
            return redirect(url_for(endpoint_login, siguiente=request.path))
        return vista(*args, **kwargs)

    return envoltura


def login_requerido(vista):
    """Sin sesión manda a la pantalla de acceso de la web."""
    return _exigir_sesion(vista, "auth.login")


def permiso_requerido(*permisos, login="auth.login"):
    """Sin sesión manda al login indicado; sin permiso responde 403 (Acceso no autorizado)."""
    def decorador(vista):
        @wraps(vista)
        def envoltura(*args, **kwargs):
            if not tiene_permiso(*permisos):
                abort(403)
            return vista(*args, **kwargs)

        return _exigir_sesion(envoltura, login)

    return decorador
