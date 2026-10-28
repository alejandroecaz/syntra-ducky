"""Servicio de autenticación: inicio de sesión (HU-01-01) y cambio de contraseña (HU-01-06).

Lo usan el login web y el login del portal móvil, así ambos aplican las mismas reglas
y muestran los mismos mensajes.
"""
from werkzeug.security import check_password_hash, generate_password_hash

import config
from models import perfil as perfil_modelo
from models import usuario as usuario_modelo
from services.errores import ErrorValidacion

MENSAJES = config.MENSAJES


def cifrar_contrasena(contrasena):
    """Hash PBKDF2 de la contraseña; nunca se guarda en texto plano."""
    return generate_password_hash(contrasena, method="pbkdf2:sha256")


def autenticar(cuenta, contrasena):
    """Valida cuenta, contraseña, estado y perfil.

    Regresa {"usuario", "perfil", "permisos", "bienvenida"} para iniciar la sesión,
    o lanza ErrorValidacion con el mensaje del criterio de aceptación que no se cumplió.
    """
    cuenta = (cuenta or "").strip()
    contrasena = contrasena or ""
    valores = {"cuenta": cuenta}

    errores = {}
    if not cuenta:
        errores["cuenta"] = "Captura tu cuenta."
    if not contrasena:
        errores["contrasena"] = "Captura tu contraseña."
    if errores:
        raise ErrorValidacion(MENSAJES["login_campos_vacios"], errores, valores)

    usuario = usuario_modelo.obtener_para_login(cuenta)
    if usuario is None or not check_password_hash(usuario["contrasena"], contrasena):
        raise ErrorValidacion(MENSAJES["login_credenciales"], valores=valores)

    if usuario["estado"] != config.ESTADO_HABILITADA:
        raise ErrorValidacion(MENSAJES["login_deshabilitada"], valores=valores)

    perfil = perfil_modelo.obtener_por_id(usuario["perfil_id"]) if usuario["perfil_id"] else None
    permisos = perfil_modelo.permisos_de(perfil["id"]) if perfil else []
    if perfil is None or not perfil["disponible"] or config.PERMISO_SISTEMA not in permisos:
        raise ErrorValidacion(MENSAJES["login_sin_acceso"], valores=valores)

    return {
        "usuario": usuario,
        "perfil": perfil["nombre"],
        "permisos": permisos,
        "bienvenida": f"Bienvenido(a), {usuario['nombre'].split()[0]}. Sesión iniciada como {perfil['nombre']}.",
    }


def autenticar_portal_movil(cuenta, contrasena):
    """Mismas reglas que autenticar() y además exige el permiso del portal móvil (solo alumnos)."""
    datos = autenticar(cuenta, contrasena)
    if config.PERMISO_MOVIL not in datos["permisos"]:
        raise ErrorValidacion(MENSAJES["login_solo_alumnos"], valores={"cuenta": datos["usuario"]["cuenta"]},
                              codigo=403)
    return datos


def cambiar_contrasena(usuario_id, actual, nueva, confirmacion):
    """Cambia la contraseña propia o lanza ErrorValidacion; la anterior se conserva si algo falla."""
    errores = {}
    if not actual:
        errores["actual"] = "Captura tu contraseña actual."
    if not nueva:
        errores["nueva"] = "Captura la nueva contraseña."
    elif len(nueva) < config.LONGITUD_MINIMA_CONTRASENA:
        errores["nueva"] = f"La nueva contraseña debe tener al menos {config.LONGITUD_MINIMA_CONTRASENA} caracteres."
    if not confirmacion:
        errores["confirmacion"] = "Confirma la nueva contraseña."
    if errores:
        raise ErrorValidacion("Completa los campos marcados. Tu contraseña no cambió.", errores)

    guardada = usuario_modelo.obtener_hash(usuario_id)
    if not guardada or not check_password_hash(guardada, actual):
        raise ErrorValidacion("La contraseña actual no es válida. Se conserva tu contraseña anterior.",
                              {"actual": "La contraseña actual no es válida."})

    if nueva != confirmacion:
        raise ErrorValidacion("La nueva contraseña y su confirmación deben coincidir. Tu contraseña no cambió.",
                              {"confirmacion": "Las contraseñas no coinciden."})

    if nueva == actual:
        raise ErrorValidacion("La nueva contraseña debe ser distinta a la actual.",
                              {"nueva": "Elige una contraseña distinta a la actual."})

    usuario_modelo.cambiar_contrasena(usuario_id, cifrar_contrasena(nueva))
    return "Contraseña actualizada. A partir de tu siguiente inicio de sesión usa la nueva contraseña."
