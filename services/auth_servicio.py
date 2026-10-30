# ============================================================
# Archivo: services/auth_servicio.py
# Proyecto: Sistema Ducky de Gestión Bibliotecaria
# Syntra Technologies - Equipo 1 - Sprint 1
# Materia: Ingeniería de Software
# Autores:
#   - Melissa Silva Vázquez                #624352
#   - Tomás Zapata Pérez                   #629048
#   - Alejandro Evaristo Cazares Escobedo  #626337
# Descripción: Servicio de autenticación: inicio de sesión (HU-01-01) y cambio de contraseña (HU-01-06).
# ============================================================
"""Servicio de autenticación: inicio de sesión (HU-01-01) y cambio de contraseña (HU-01-06).

Lo usan el login web y el login del portal móvil, así ambos aplican las mismas reglas
y muestran los mismos mensajes.
"""
from werkzeug.security import check_password_hash, generate_password_hash

import config
from models import perfil as perfil_modelo
from models import usuario as usuario_modelo
from services.errores import ErrorValidacion

# Mensajes de los criterios de aceptación (compartidos con el portal móvil)
MENSAJES = config.MENSAJES


def cifrar_contrasena(contrasena):
    """Hash PBKDF2 de la contraseña; nunca se guarda en texto plano."""
    return generate_password_hash(contrasena, method="pbkdf2:sha256")


def autenticar(cuenta, contrasena):
    """HU-01-01: Valida cuenta, contraseña, estado y perfil.

    Regresa {"usuario", "perfil", "permisos", "bienvenida"} para iniciar la sesión,
    o lanza ErrorValidacion con el mensaje del criterio de aceptación que no se cumplió.
    """
    # Limpiamos lo capturado; la contraseña no se recorta
    cuenta = (cuenta or "").strip()
    contrasena = contrasena or ""
    valores = {"cuenta": cuenta}

    # HU-01-01 · Campos obligatorios vacíos: se piden y la sesión sigue cerrada
    errores = {}
    if not cuenta:
        errores["cuenta"] = "Captura tu cuenta."
    if not contrasena:
        errores["contrasena"] = "Captura tu contraseña."
    if errores:
        raise ErrorValidacion(MENSAJES["login_campos_vacios"], errores, valores)

    # HU-01-01 · Credenciales incorrectas: mismo mensaje si falla la cuenta o la contraseña
    usuario = usuario_modelo.obtener_para_login(cuenta)
    if usuario is None or not check_password_hash(usuario["contrasena"], contrasena):
        raise ErrorValidacion(MENSAJES["login_credenciales"], valores=valores)

    # HU-01-01 · Cuenta deshabilitada
    if usuario["estado"] != config.ESTADO_HABILITADA:
        raise ErrorValidacion(MENSAJES["login_deshabilitada"], valores=valores)

    # HU-01-01 · Perfil de usuario sin acceso al sistema (sin perfil, no disponible o sin el permiso)
    perfil = perfil_modelo.obtener_por_id(usuario["perfil_id"]) if usuario["perfil_id"] else None
    permisos = perfil_modelo.permisos_de(perfil["id"]) if perfil else []
    if perfil is None or not perfil["disponible"] or config.PERMISO_SISTEMA not in permisos:
        raise ErrorValidacion(MENSAJES["login_sin_acceso"], valores=valores)

    # HU-01-01 · Inicio de sesión exitoso: datos para la sesión y el saludo
    return {
        "usuario": usuario,
        "perfil": perfil["nombre"],
        "permisos": permisos,
        "bienvenida": f"Bienvenido(a), {usuario['nombre'].split()[0]}. Sesión iniciada como {perfil['nombre']}.",
    }


def autenticar_portal_movil(cuenta, contrasena):
    """HU-01-01 (móvil): Mismas reglas que autenticar() y además exige el permiso del portal móvil."""
    # Aplicamos las mismas reglas que en la web
    datos = autenticar(cuenta, contrasena)

    # Solo entran los perfiles con el permiso movil.acceder (alumnos)
    if config.PERMISO_MOVIL not in datos["permisos"]:
        raise ErrorValidacion(MENSAJES["login_solo_alumnos"], valores={"cuenta": datos["usuario"]["cuenta"]},
                              codigo=403)
    return datos


def cambiar_contrasena(usuario_id, actual, nueva, confirmacion):
    """HU-01-06: Cambia la contraseña propia o lanza ErrorValidacion; la anterior se conserva si algo falla."""
    # Revisamos que vengan los tres campos y que la nueva tenga la longitud mínima
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

    # HU-01-06 · Contraseña actual incorrecta
    guardada = usuario_modelo.obtener_hash(usuario_id)
    if not guardada or not check_password_hash(guardada, actual):
        raise ErrorValidacion("La contraseña actual no es válida. Se conserva tu contraseña anterior.",
                              {"actual": "La contraseña actual no es válida."})

    # HU-01-06 · Confirmación no coincidente
    if nueva != confirmacion:
        raise ErrorValidacion("La nueva contraseña y su confirmación deben coincidir. Tu contraseña no cambió.",
                              {"confirmacion": "Las contraseñas no coinciden."})

    # La nueva debe ser distinta a la actual
    if nueva == actual:
        raise ErrorValidacion("La nueva contraseña debe ser distinta a la actual.",
                              {"nueva": "Elige una contraseña distinta a la actual."})

    # HU-01-06 · Contraseña actualizada: se guarda cifrada
    usuario_modelo.cambiar_contrasena(usuario_id, cifrar_contrasena(nueva))
    return "Contraseña actualizada. A partir de tu siguiente inicio de sesión usa la nueva contraseña."
