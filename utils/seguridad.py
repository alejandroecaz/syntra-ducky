from functools import wraps

from flask import abort, flash, redirect, request, session, url_for


def usuario_actual():
    if "usuario_id" not in session:
        return None
    return {
        "id": session["usuario_id"],
        "nombre": session.get("nombre"),
        "cuenta": session.get("cuenta"),
        "perfil": session.get("perfil"),
    }


def tiene_permiso(*permisos):
    # Basta con tener uno de los permisos
    otorgados = session.get("permisos", [])
    return any(permiso in otorgados for permiso in permisos)


def iniciar_sesion(usuario, perfil_nombre, permisos):
    session.clear()
    session["usuario_id"] = usuario["id"]
    session["nombre"] = usuario["nombre"]
    session["cuenta"] = usuario["cuenta"]
    session["perfil"] = perfil_nombre
    session["permisos"] = permisos


def login_requerido(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Inicia sesión para continuar.", "warning")
            return redirect(url_for("auth.login", siguiente=request.path))
        return vista(*args, **kwargs)

    return envoltura


def permiso_requerido(*permisos):
    # Sin sesion manda al login y sin permiso marca error 403
    def decorador(vista):
        @wraps(vista)
        @login_requerido
        def envoltura(*args, **kwargs):
            if not tiene_permiso(*permisos):
                abort(403)
            return vista(*args, **kwargs)

        return envoltura

    return decorador
