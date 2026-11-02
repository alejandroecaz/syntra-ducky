"""
============================================================
Archivo:      utils/seguridad.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Sesion y control de acceso por permisos (lo usan los controladores web
    y movil).

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

from functools import wraps

from flask import abort, flash, redirect, request, session, url_for


def obtener_usuario_actual():
    """
    Descripcion:
        Obtiene los datos de la sesion iniciada.

    Parametros:
        Ninguno.

    Salida:
        dict con id, nombre, cuenta y perfil, o None si no hay sesion.
    """
    if "usuario_id" not in session:
        return None
    return {
        "id": session["usuario_id"],
        "nombre": session.get("nombre"),
        "cuenta": session.get("cuenta"),
        "perfil": session.get("perfil"),
    }


def verificar_permiso(*permisos):
    """
    Descripcion:
        Revisa si el perfil en sesion tiene al menos uno de los permisos. El
        acceso siempre se revisa por permiso, nunca por nombre de perfil.

    Parametros:
        *permisos (str): codigos de permiso, por ejemplo catalogo.consultar.

    Salida:
        bool: True si tiene al menos uno.
    """
    otorgados = session.get("permisos", [])
    return any(permiso in otorgados for permiso in permisos)


def iniciar_sesion(usuario, perfil_nombre, permisos):
    """
    Descripcion:
        HU-01-01: Guarda en una sesion limpia los datos de la cuenta
        autenticada y los permisos de su perfil.

    Parametros:
        usuario (sqlite3.Row): usuario autenticado.
        perfil_nombre (str): nombre del perfil.
        permisos (list[str]): codigos de permiso del perfil.

    Salida:
        Ninguna.
    """
    # Empezamos una sesion limpia.
    session.clear()

    # Datos de la cuenta y permisos del perfil (el acceso se revisa por
    # permiso).
    session["usuario_id"] = usuario["id"]
    session["nombre"] = usuario["nombre_completo"]
    session["cuenta"] = usuario["cuenta"]
    session["perfil"] = perfil_nombre
    session["permisos"] = permisos


def _exigir_sesion(vista, vista_login):
    """
    Descripcion:
        Envuelve la vista para que, sin sesion, mande al login indicado
        recordando la ruta que se queria abrir.

    Parametros:
        vista (function): funcion de la vista.
        vista_login (str): endpoint del login, por ejemplo auth.ingresar.

    Salida:
        function: la vista envuelta.
    """

    @wraps(vista)
    def revisar_sesion(*args, **kwargs):
        """
        Descripcion:
            Revisa la sesion antes de ejecutar la vista.

        Parametros:
            *args (tuple): argumentos de la vista.
            **kwargs (dict): argumentos con nombre de la vista (los de la URL).

        Salida:
            flask.Response o str: lo que regresa la vista, o flask.Response:
            redireccion al login.
        """
        # Sin sesion: aviso y al login, recordando a donde se queria entrar.
        if "usuario_id" not in session:
            flash("Inicia sesión para continuar.", "advertencia")
            return redirect(url_for(vista_login, siguiente=request.path))
        return vista(*args, **kwargs)

    return revisar_sesion


def sesion_requerida(vista):
    """
    Descripcion:
        Decorador: sin sesion manda a la pantalla de acceso de la web.

    Parametros:
        vista (function): funcion de la vista.

    Salida:
        function: la vista protegida.
    """
    return _exigir_sesion(vista, "auth.ingresar")


def permiso_requerido(*permisos, vista_login="auth.ingresar"):
    """
    Descripcion:
        Decorador del criterio Acceso sin autorizacion: sin sesion manda al
        login indicado y, con sesion pero sin el permiso, responde 403.

    Parametros:
        *permisos (str): codigos de permiso; basta con tener uno.
        vista_login (str): endpoint del login al que se manda sin sesion.

    Salida:
        function: decorador para la vista.
    """

    def decorar(vista):
        """
        Descripcion:
            Aplica la revision de sesion y de permisos a la vista.

        Parametros:
            vista (function): funcion de la vista.

        Salida:
            function: la vista protegida.
        """

        @wraps(vista)
        def revisar_permiso(*args, **kwargs):
            """
            Descripcion:
                Revisa el permiso antes de ejecutar la vista.

            Parametros:
                *args (tuple): argumentos de la vista.
                **kwargs (dict): argumentos con nombre de la vista (los de la
                    URL).

            Salida:
                flask.Response o str: lo que regresa la vista.

            Excepciones:
                werkzeug.exceptions.Forbidden (403) si falta el permiso.
            """
            # Con sesion pero sin el permiso: 403 (Acceso no autorizado).
            if not verificar_permiso(*permisos):
                abort(403)
            return vista(*args, **kwargs)

        # Primero se revisa la sesion y despues el permiso.
        return _exigir_sesion(revisar_permiso, vista_login)

    return decorar
