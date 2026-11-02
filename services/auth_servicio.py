"""
============================================================
Archivo:      services/auth_servicio.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Servicio de autenticacion: inicio de sesion (HU-01-01) y cambio de
    contrasena (HU-01-06).

    Lo usan el login web y el login del portal movil, asi ambos aplican
    las mismas reglas y muestran los mismos mensajes.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

from werkzeug.security import check_password_hash, generate_password_hash

import config
from models import perfil as perfil_modelo
from models import usuario as usuario_modelo
from services.errores import ErrorValidacion

# Mensajes de los criterios de aceptacion (compartidos con el portal movil).
MENSAJES = config.MENSAJES


def cifrar_contrasena(contrasena):
    """
    Descripcion:
        Cifra la contrasena con PBKDF2; nunca se guarda en texto plano.

    Parametros:
        contrasena (str): contrasena en texto plano.

    Salida:
        str: hash de la contrasena.
    """
    return generate_password_hash(contrasena, method="pbkdf2:sha256")


def autenticar(cuenta, contrasena):
    """
    Descripcion:
        HU-01-01: Valida cuenta, contrasena, estado de la cuenta y perfil para
        iniciar la sesion.

    Parametros:
        cuenta (str): cuenta capturada.
        contrasena (str): contrasena capturada.

    Salida:
        dict: usuario, perfil, permisos y mensaje de bienvenida para iniciar la
        sesion.

    Excepciones:
        ErrorValidacion con el mensaje del criterio de aceptacion que no se
        cumplio: campos vacios, credenciales incorrectas, cuenta deshabilitada
        o perfil sin acceso.
    """
    # Limpiamos lo capturado; la contrasena no se recorta.
    cuenta = (cuenta or "").strip()
    contrasena = contrasena or ""
    valores = {"cuenta": cuenta}

    # HU-01-01 · Campos obligatorios vacios: se piden y la sesion sigue
    # cerrada.
    errores = {}
    if not cuenta:
        errores["cuenta"] = "Captura tu cuenta."
    if not contrasena:
        errores["contrasena"] = "Captura tu contraseña."
    if errores:
        raise ErrorValidacion(
            MENSAJES["login_campos_vacios"], errores, valores
        )

    # HU-01-01 · Credenciales incorrectas: mismo mensaje si falla la cuenta o
    # la contrasena.
    usuario = usuario_modelo.obtener_para_login(cuenta)
    if usuario is None or not check_password_hash(
        usuario["contrasena"], contrasena
    ):
        raise ErrorValidacion(MENSAJES["login_credenciales"], valores=valores)

    # HU-01-01 · Cuenta deshabilitada.
    if usuario["estado"] != config.ESTADO_HABILITADA:
        raise ErrorValidacion(MENSAJES["login_deshabilitada"], valores=valores)

    # HU-01-01 · Perfil de usuario sin acceso al sistema (sin perfil, no
    # disponible o sin el permiso).
    perfil = (
        perfil_modelo.obtener_por_id(usuario["perfil_id"])
        if usuario["perfil_id"]
        else None
    )
    permisos = perfil_modelo.listar_permisos(perfil["id"]) if perfil else []
    if (
        perfil is None
        or not perfil["disponible"]
        or config.PERMISO_SISTEMA not in permisos
    ):
        raise ErrorValidacion(MENSAJES["login_sin_acceso"], valores=valores)

    # HU-01-01 · Inicio de sesion exitoso: datos para la sesion y el saludo.
    return {
        "usuario": usuario,
        "perfil": perfil["nombre"],
        "permisos": permisos,
        "bienvenida": f"Bienvenido(a), {usuario['nombre'].split()[0]}. "
        f"Sesión iniciada como {perfil['nombre']}.",
    }


def autenticar_portal_movil(cuenta, contrasena):
    """
    Descripcion:
        HU-01-01 (movil): aplica las mismas reglas que autenticar() y ademas
        exige el permiso del portal movil.

    Parametros:
        cuenta (str): cuenta capturada.
        contrasena (str): contrasena capturada.

    Salida:
        dict: los mismos datos que regresa autenticar().

    Excepciones:
        ErrorValidacion con los mensajes de autenticar(), o con codigo 403 si
        el perfil no es de alumno.
    """
    # Aplicamos las mismas reglas que en la web.
    datos = autenticar(cuenta, contrasena)

    # Solo entran los perfiles con el permiso movil.acceder (alumnos).
    if config.PERMISO_MOVIL not in datos["permisos"]:
        raise ErrorValidacion(
            MENSAJES["login_solo_alumnos"],
            valores={"cuenta": datos["usuario"]["cuenta"]},
            codigo=403,
        )
    return datos


def cambiar_contrasena(usuario_id, actual, nueva, confirmacion):
    """
    Descripcion:
        HU-01-06: Cambia la contrasena propia. Si algo falla se conserva la
        contrasena anterior.

    Parametros:
        usuario_id (int): id del usuario en sesion.
        actual (str): contrasena actual.
        nueva (str): contrasena nueva.
        confirmacion (str): confirmacion de la nueva.

    Salida:
        str: mensaje de contrasena actualizada.

    Excepciones:
        ErrorValidacion si faltan campos, la actual no es valida, la
        confirmacion no coincide o la nueva es igual a la actual.
    """
    # Revisamos que vengan los tres campos y que la nueva tenga la longitud
    # minima.
    errores = {}
    if not actual:
        errores["actual"] = "Captura tu contraseña actual."
    if not nueva:
        errores["nueva"] = "Captura la nueva contraseña."
    elif len(nueva) < config.LONGITUD_MINIMA_CONTRASENA:
        errores["nueva"] = (
            "La nueva contraseña debe tener al menos "
            f"{config.LONGITUD_MINIMA_CONTRASENA} caracteres."
        )
    if not confirmacion:
        errores["confirmacion"] = "Confirma la nueva contraseña."
    if errores:
        raise ErrorValidacion(
            "Completa los campos marcados. Tu contraseña no cambió.", errores
        )

    # HU-01-06 · Contrasena actual incorrecta.
    guardada = usuario_modelo.obtener_hash(usuario_id)
    if not guardada or not check_password_hash(guardada, actual):
        raise ErrorValidacion(
            "La contraseña actual no es válida. Se conserva tu contraseña "
            "anterior.",
            {"actual": "La contraseña actual no es válida."},
        )

    # HU-01-06 · Confirmacion no coincidente.
    if nueva != confirmacion:
        raise ErrorValidacion(
            "La nueva contraseña y su confirmación deben coincidir. Tu "
            "contraseña no cambió.",
            {"confirmacion": "Las contraseñas no coinciden."},
        )

    # La nueva debe ser distinta a la actual.
    if nueva == actual:
        raise ErrorValidacion(
            "La nueva contraseña debe ser distinta a la actual.",
            {"nueva": "Elige una contraseña distinta a la actual."},
        )

    # HU-01-06 · Contrasena actualizada: se guarda cifrada.
    usuario_modelo.cambiar_contrasena(usuario_id, cifrar_contrasena(nueva))
    return (
        "Contraseña actualizada. A partir de tu siguiente inicio de "
        "sesión usa la nueva contraseña."
    )
