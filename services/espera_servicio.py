"""
============================================================
Archivo:      services/espera_servicio.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Servicio de la lista de espera (HU-02-06 Registro de lista de
    espera): registrar al usuario cuando el libro no tiene ejemplares
    disponibles, avisarle cuando le toca y cancelar su solicitud.

    El turno se respeta al prestar: prestamo_servicio no deja prestar un
    ejemplar disponible a otra persona mientras haya alguien antes en la
    lista.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    13/11/2026
============================================================
"""

import os

import config
from models import lista_espera as espera_modelo
from models import prestamo as prestamo_modelo
from services.errores import ErrorValidacion
from services.prestamo_servicio import normalizar_telefono
from utils import notificaciones

# ============================================================
# CONSULTAS
# ============================================================


def listar(ver):
    """
    Descripcion:
        HU-02-06: Lista las solicitudes vigentes o todas.

    Parametros:
        ver (str o None): "todas" para incluir atendidas y canceladas.

    Salida:
        list[sqlite3.Row]: solicitudes con turno y disponibilidad.
    """
    return espera_modelo.listar(solo_vigentes=ver != "todas")


def obtener(solicitud_id):
    """
    Descripcion:
        HU-02-06: Busca una solicitud.

    Parametros:
        solicitud_id (int): id de la solicitud.

    Salida:
        sqlite3.Row o None si no existe.
    """
    return espera_modelo.obtener(solicitud_id)


def verificar_turno(solicitud):
    """
    Descripcion:
        HU-02-06: Revisa si a la solicitud ya le toca un ejemplar: esta
        vigente y hay tantos disponibles como su turno.

    Parametros:
        solicitud (sqlite3.Row): solicitud de espera_modelo.

    Salida:
        bool: True si ya hay un ejemplar para el usuario.
    """
    return bool(
        solicitud["turno"] and solicitud["turno"] <= solicitud["disponibles"]
    )


def obtener_opciones_formulario():
    """
    Descripcion:
        HU-02-06: Usuarios y libros sin ejemplares disponibles para las
        sugerencias del formulario.

    Parametros:
        Ninguno.

    Salida:
        dict: solicitantes y libros.
    """
    return {
        "solicitantes": prestamo_modelo.listar_solicitantes(),
        "libros": espera_modelo.listar_libros_sin_disponibles(),
    }


def contar_vigentes():
    """
    Descripcion:
        Cuenta las solicitudes que siguen esperando turno (panel de inicio).

    Parametros:
        Ninguno.

    Salida:
        int: numero de solicitudes vigentes.
    """
    return espera_modelo.contar_vigentes()


# ============================================================
# REGISTRO EN LA LISTA DE ESPERA (HU-02-06)
# ============================================================


def _validar_usuario(texto):
    """
    Descripcion:
        HU-02-06: El usuario debe existir, estar habilitado y su perfil tener
        prestamos.

    Parametros:
        texto (str): matricula o cuenta capturada.

    Salida:
        tuple[sqlite3.Row o None, str o None]: el usuario y el error.
    """
    if not texto:
        return None, "Captura la matrícula o la cuenta del usuario."
    usuario = prestamo_modelo.obtener_solicitante(texto)
    if usuario is None:
        return None, (
            "No hay ningún usuario registrado con esa matrícula o cuenta."
        )
    if usuario["estado"] != config.ESTADO_HABILITADA:
        return usuario, "La cuenta de este usuario está deshabilitada."
    if not usuario["max_prestamos"]:
        return usuario, (
            f"El perfil {usuario['perfil'] or 'del usuario'} no tiene "
            "préstamos a domicilio autorizados."
        )
    return usuario, None


def _validar_libro(clave, usuario):
    """
    Descripcion:
        HU-02-06: El libro debe existir, estar activo, prestarse a domicilio y
        no tener ejemplares disponibles para el usuario. El usuario no puede
        tenerlo prestado ni estar ya en su lista.

    Parametros:
        clave (str): clave del libro capturada.
        usuario (sqlite3.Row o None): usuario ya validado, si lo hay.

    Salida:
        tuple[sqlite3.Row o None, str o None]: el libro y el error.
    """
    if not clave:
        return None, "Captura la clave del libro (por ejemplo LIB-011)."
    libro = espera_modelo.obtener_libro(clave)
    if libro is None:
        return None, f"No existe un libro con la clave {clave}."
    if not libro["activo"]:
        return libro, "El libro está dado de baja."
    if libro["tipo_acceso"] in config.TIPOS_ACCESO_SIN_PRESTAMO:
        return libro, (
            f"«{libro['titulo']}» es de acceso "
            f"{libro['tipo_acceso'].lower()}: no se presta a domicilio."
        )
    # HU-02-06 · Libro con ejemplares disponibles: se presta directo.
    if libro["disponibles"] > libro["en_espera"]:
        return libro, (
            f"«{libro['titulo']}» tiene ejemplares disponibles; registra el "
            "préstamo directamente."
        )
    if not usuario:
        return libro, None
    if prestamo_modelo.verificar_libro_prestado_a_usuario(
        usuario["id"], libro["id"]
    ):
        return libro, (
            f"El usuario ya tiene prestado un ejemplar de «{libro['titulo']}»."
        )
    # HU-02-06 · Solicitud repetida.
    turno = espera_modelo.contar_antes(libro["id"], usuario["id"])["turno"]
    if turno:
        return libro, (
            f"El usuario ya está en la lista de espera de este libro (turno "
            f"{turno})."
        )
    return libro, None


def registrar(formulario):
    """
    Descripcion:
        HU-02-06: Valida y agrega al usuario a la lista de espera del libro.

    Parametros:
        formulario (werkzeug.datastructures.MultiDict o dict): usuario
            (matricula o cuenta) y libro (clave).

    Salida:
        str: mensaje con el turno asignado.

    Excepciones:
        ErrorValidacion (422) con los errores por campo y lo capturado.
    """
    valores = {
        "usuario": (formulario.get("usuario") or "").strip(),
        "libro": (formulario.get("libro") or "").strip().upper(),
    }
    errores = {}
    usuario, errores["usuario"] = _validar_usuario(valores["usuario"])
    libro, errores["libro"] = _validar_libro(
        valores["libro"], usuario if not errores["usuario"] else None
    )
    errores = {campo: texto for campo, texto in errores.items() if texto}
    if errores:
        raise ErrorValidacion(
            "No se puede agregar a la lista de espera. Revisa los datos "
            "marcados.",
            errores,
            valores,
            codigo=422,
        )

    espera_modelo.registrar(libro["id"], usuario["id"])
    return (
        f"{usuario['nombre_completo']} quedó en la lista de espera de "
        f"«{libro['titulo']}» con el turno {libro['en_espera'] + 1}."
    )


def cancelar(solicitud):
    """
    Descripcion:
        HU-02-06: Cancela una solicitud vigente.

    Parametros:
        solicitud (sqlite3.Row): solicitud.

    Salida:
        str: mensaje de confirmacion.

    Excepciones:
        ErrorValidacion (409) si la solicitud ya no esta vigente.
    """
    if solicitud["estado"] not in config.ESTADOS_ESPERA_VIGENTE:
        raise ErrorValidacion(
            "La solicitud ya estaba atendida o cancelada.", codigo=409
        )
    espera_modelo.cambiar_estado(
        solicitud["id"], config.ESTADO_ESPERA_CANCELADO
    )
    return (
        f"Se canceló la solicitud de {solicitud['usuario_nombre']} para "
        f"«{solicitud['titulo']}»."
    )


# ============================================================
# AVISO AL USUARIO (HU-02-06)
# ============================================================


def armar_texto_aviso(solicitud):
    """
    Descripcion:
        HU-02-06: Texto del aviso de que el libro ya esta disponible.

    Parametros:
        solicitud (sqlite3.Row): solicitud.

    Salida:
        str: aviso en texto plano.
    """
    return (
        f"Hola, {solicitud['usuario_nombre']}.\n\n"
        f"Ya hay un ejemplar disponible de «{solicitud['titulo']}» "
        f"({solicitud['libro_clave']}), el libro que pediste en la lista de "
        "espera. Está apartado para ti: pasa a la biblioteca con tu "
        "credencial para llevártelo.\n\n"
        f"{config.NOMBRE_CLIENTE}"
    )


def avisar(solicitud, medio):
    """
    Descripcion:
        HU-02-06: Avisa al usuario por correo o WhatsApp que ya le toca un
        ejemplar; la solicitud queda "Notificado" y el aviso se guarda.

    Parametros:
        solicitud (sqlite3.Row): solicitud.
        medio (str): "correo" o "whatsapp".

    Salida:
        tuple[str, str]: (tono, mensaje) del aviso, o ("enlace", url de
        wa.me) si WhatsApp se abre en el navegador.

    Excepciones:
        ErrorValidacion si todavia no le toca, le falta el correo o celular,
        o el envio falla.
    """
    if not verificar_turno(solicitud):
        raise ErrorValidacion(
            "Todavía no hay un ejemplar disponible para este turno.",
            codigo=409,
        )
    texto = armar_texto_aviso(solicitud)

    if medio == "correo":
        if not solicitud["usuario_email"]:
            raise ErrorValidacion(
                "El usuario no tiene correo registrado. Agrégalo en "
                "Usuarios → Editar datos.",
                codigo=400,
            )
        try:
            ruta_demo = notificaciones.enviar_correo(
                solicitud["usuario_email"],
                f"Tu libro ya está disponible · {config.NOMBRE_CLIENTE}",
                texto,
                nombre=f"aviso_espera_{solicitud['id']}",
            )
        except notificaciones.ErrorEnvio as error:
            raise ErrorValidacion(str(error), codigo=502) from error
        resultado = (
            (
                "advertencia",
                "Modo demostración: el aviso para "
                f"{solicitud['usuario_email']} se guardó en la carpeta "
                f"boletas_enviadas ({os.path.basename(ruta_demo)}).",
            )
            if ruta_demo
            else (
                "exito",
                f"Se avisó a {solicitud['usuario_nombre']} por correo.",
            )
        )
        medio_aviso = config.MEDIO_CORREO
    else:
        numero = normalizar_telefono(solicitud["usuario_telefono"])
        if numero is None:
            raise ErrorValidacion(
                "El usuario no tiene un celular registrado. Agrégalo en "
                "Usuarios → Editar datos.",
                codigo=400,
            )
        if notificaciones.verificar_whatsapp_api_configurada():
            try:
                notificaciones.enviar_whatsapp(numero, texto)
            except notificaciones.ErrorEnvio as error:
                raise ErrorValidacion(str(error), codigo=502) from error
            resultado = (
                "exito",
                f"Se avisó a {solicitud['usuario_nombre']} por WhatsApp.",
            )
        else:
            resultado = (
                "enlace",
                notificaciones.crear_enlace_whatsapp(numero, texto),
            )
        medio_aviso = config.MEDIO_WHATSAPP

    # Guardamos el aviso y la solicitud queda como notificada.
    espera_modelo.registrar_aviso(solicitud["usuario_id"], medio_aviso, texto)
    espera_modelo.cambiar_estado(
        solicitud["id"], config.ESTADO_ESPERA_NOTIFICADO
    )
    return resultado
