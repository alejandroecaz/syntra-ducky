"""
============================================================
Archivo:      services/prestamo_servicio.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Servicio de prestamos (Sprint 2, Prestar libros):
        HU-02-01 Validacion del solicitante
        HU-02-02 Validacion del libro
        HU-02-03 Registro del prestamo
        HU-02-04 Boleta de prestamo (correo, WhatsApp e impresion)
        HU-02-05 Renovacion de prestamo

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    13/11/2026
============================================================
"""

import os
import re
from datetime import date, datetime, timedelta

import config
from models import ejemplar as ejemplar_modelo
from models import lista_espera as espera_modelo
from models import prestamo as prestamo_modelo
from services.errores import ErrorValidacion
from utils import notificaciones, pdf

# Nota que llevan la boleta, el correo y el mensaje de WhatsApp.
NOTA_BOLETA = (
    "Conserva esta boleta y preséntala al devolver el libro. Si lo "
    "entregas después de la fecha de devolución se genera una multa por "
    "cada día de retraso."
)

# ============================================================
# CONSULTAS
# ============================================================


def obtener_vista(vista):
    """
    Descripcion:
        Regresa la vista de la lista de prestamos si es valida.

    Parametros:
        vista (str o None): "activos", "vencidos" o "todos".

    Salida:
        str: la vista pedida o "activos".
    """
    return vista if vista in config.VISTAS_PRESTAMOS else "activos"


def listar(vista):
    """
    Descripcion:
        HU-02-03: Lista los prestamos de la vista elegida.

    Parametros:
        vista (str): "activos", "vencidos" o "todos".

    Salida:
        list[sqlite3.Row]: prestamos.
    """
    return prestamo_modelo.listar(obtener_vista(vista))


def obtener(prestamo_id):
    """
    Descripcion:
        HU-02-04: Obtiene el prestamo con las boletas que se han emitido.

    Parametros:
        prestamo_id (int): id del prestamo.

    Salida:
        tuple[sqlite3.Row, list[sqlite3.Row]] o None si no existe.
    """
    prestamo = prestamo_modelo.obtener(prestamo_id)
    if prestamo is None:
        return None
    return prestamo, prestamo_modelo.listar_comprobantes(prestamo_id)


def verificar_vencido(prestamo):
    """
    Descripcion:
        Revisa si el prestamo sigue activo y ya paso su fecha de devolucion.

    Parametros:
        prestamo (sqlite3.Row): prestamo.

    Salida:
        bool: True si esta vencido.
    """
    return (
        prestamo["estado"] == config.ESTADO_PRESTAMO_ACTIVO
        and prestamo["fecha_vencimiento"] < date.today().isoformat()
    )


def obtener_opciones_formulario():
    """
    Descripcion:
        HU-02-03: Usuarios y ejemplares disponibles para las sugerencias del
        formulario.

    Parametros:
        Ninguno.

    Salida:
        dict: solicitantes y ejemplares.
    """
    return {
        "solicitantes": prestamo_modelo.listar_solicitantes(),
        "ejemplares": ejemplar_modelo.listar_disponibles_para_prestamo(),
    }


# ============================================================
# VALIDACION Y REGISTRO DEL PRESTAMO (HU-02-01 A HU-02-03)
# ============================================================


def _validar_solicitante(texto):
    """
    Descripcion:
        HU-02-01: Revisa que el usuario exista, este habilitado, su perfil
        tenga prestamos, no tenga prestamos vencidos y no haya llegado a su
        limite.

    Parametros:
        texto (str): matricula o cuenta capturada.

    Salida:
        tuple[sqlite3.Row o None, str o None]: el usuario y el error (si hay).
    """
    if not texto:
        return None, "Captura la matrícula o la cuenta del usuario."

    usuario = prestamo_modelo.obtener_solicitante(texto)
    if usuario is None:
        return None, (
            "No hay ningún usuario registrado con esa matrícula o cuenta."
        )
    # HU-02-01 · Cuenta deshabilitada.
    if usuario["estado"] != config.ESTADO_HABILITADA:
        return usuario, (
            "La cuenta de este usuario está deshabilitada; no se le puede "
            "prestar."
        )
    # HU-02-01 · Perfil sin prestamos.
    if not usuario["max_prestamos"]:
        return usuario, (
            f"El perfil {usuario['perfil'] or 'del usuario'} no tiene "
            "préstamos a domicilio autorizados."
        )
    # HU-02-01 · Prestamos vencidos y limite de prestamos.
    totales = prestamo_modelo.contar_activos_de_usuario(usuario["id"])
    if totales["vencidos"]:
        return usuario, (
            f"{usuario['nombre_completo']} tiene {totales['vencidos']} "
            "préstamo(s) vencido(s). Debe devolverlos antes de llevarse otro "
            "libro."
        )
    if totales["activos"] >= usuario["max_prestamos"]:
        return usuario, (
            f"{usuario['nombre_completo']} ya tiene {totales['activos']} "
            "préstamo(s) activo(s), el máximo para el perfil "
            f"{usuario['perfil']}."
        )
    return usuario, None


def _validar_ejemplar(codigo, usuario):
    """
    Descripcion:
        HU-02-02: Revisa que el ejemplar exista, su libro este activo y se
        pueda prestar, este disponible y que el usuario no tenga ya otro
        ejemplar del mismo libro.

    Parametros:
        codigo (str): codigo del ejemplar capturado.
        usuario (sqlite3.Row o None): usuario ya validado, si lo hay.

    Salida:
        tuple[sqlite3.Row o None, str o None]: el ejemplar y el error.
    """
    if not codigo:
        return None, "Captura el código del ejemplar (por ejemplo EJ-0001)."

    ejemplar = ejemplar_modelo.obtener_por_codigo(codigo)
    if ejemplar is None:
        return None, f"No existe un ejemplar con el código {codigo}."
    # HU-02-02 · Libro dado de baja o de acceso reservado.
    if not ejemplar["libro_activo"]:
        return ejemplar, "El libro de este ejemplar está dado de baja."
    if ejemplar["tipo_acceso"] in config.TIPOS_ACCESO_SIN_PRESTAMO:
        return ejemplar, (
            f"«{ejemplar['titulo']}» es de acceso "
            f"{ejemplar['tipo_acceso'].lower()}: solo se consulta dentro de "
            "la biblioteca."
        )
    # HU-02-02 · Ejemplar no disponible.
    if ejemplar["estado"] != config.ESTADO_DISPONIBLE:
        return ejemplar, (
            f"El ejemplar {ejemplar['codigo']} no está disponible (estado: "
            f"{ejemplar['estado']})."
        )
    if not usuario:
        return ejemplar, None
    # HU-02-02 · El usuario ya tiene este libro.
    if prestamo_modelo.verificar_libro_prestado_a_usuario(
        usuario["id"], ejemplar["libro_id"]
    ):
        return ejemplar, (
            "El usuario ya tiene prestado un ejemplar de "
            f"«{ejemplar['titulo']}»."
        )
    # HU-02-06 · Turno de la lista de espera: los ejemplares disponibles son
    # primero para quienes llevan mas tiempo esperando.
    cola = espera_modelo.contar_antes(ejemplar["libro_id"], usuario["id"])
    disponibles = espera_modelo.obtener_libro(ejemplar["libro_clave"])[
        "disponibles"
    ]
    if cola["antes"] >= disponibles:
        return ejemplar, (
            f"«{ejemplar['titulo']}» tiene {cola['antes']} persona(s) antes "
            f"en la lista de espera y {disponibles} ejemplar(es) "
            "disponible(s): le toca primero a quien lleva más tiempo "
            "esperando."
        )
    return ejemplar, None


def validar(formulario):
    """
    Descripcion:
        HU-02-01 y HU-02-02: Valida al solicitante y al ejemplar antes de
        registrar el prestamo y calcula la fecha de devolucion con los dias
        de prestamo del perfil.

    Parametros:
        formulario (werkzeug.datastructures.MultiDict o dict): usuario
            (matricula o cuenta) y ejemplar (codigo).

    Salida:
        dict: borrador con usuario_id, ejemplar_id, los textos capturados y
        fecha_vencimiento (aaaa-mm-dd).

    Excepciones:
        ErrorValidacion con el error de cada campo y lo capturado.
    """
    valores = {
        "usuario": (formulario.get("usuario") or "").strip(),
        "ejemplar": (formulario.get("ejemplar") or "").strip().upper(),
    }

    # Validamos los dos campos para mostrar todos los errores a la vez.
    errores = {}
    usuario, errores["usuario"] = _validar_solicitante(valores["usuario"])
    ejemplar, errores["ejemplar"] = _validar_ejemplar(
        valores["ejemplar"], usuario if not errores["usuario"] else None
    )
    errores = {campo: texto for campo, texto in errores.items() if texto}
    if errores:
        raise ErrorValidacion(
            "No se puede registrar el préstamo. Revisa los datos marcados.",
            errores,
            valores,
            codigo=422,
        )

    # La fecha de devolucion depende del perfil.
    vencimiento = date.today() + timedelta(days=usuario["dias_prestamo"])
    return {
        **valores,
        "usuario_id": usuario["id"],
        "ejemplar_id": ejemplar["id"],
        "fecha_vencimiento": vencimiento.isoformat(),
    }


def resolver_borrador(borrador):
    """
    Descripcion:
        HU-02-03: Junta los datos del usuario y del ejemplar para la pantalla
        de confirmacion.

    Parametros:
        borrador (dict): borrador validado.

    Salida:
        dict: usuario, ejemplar y fecha de devolucion (date).
    """
    return {
        "usuario": prestamo_modelo.obtener_solicitante(borrador["usuario"]),
        "ejemplar": ejemplar_modelo.obtener_por_codigo(borrador["ejemplar"]),
        "vencimiento": date.fromisoformat(borrador["fecha_vencimiento"]),
    }


def registrar(borrador, bibliotecario_id):
    """
    Descripcion:
        HU-02-03: Vuelve a validar (por si algo cambio desde la captura) y
        registra el prestamo; el ejemplar queda como "Prestado".

    Parametros:
        borrador (dict): borrador de la captura.
        bibliotecario_id (int): id de quien registra.

    Salida:
        tuple[int, str]: id del prestamo y mensaje con su folio.

    Excepciones:
        ErrorValidacion si ya no se cumple alguna condicion.
    """
    vigente = validar(borrador)
    resultado = prestamo_modelo.registrar(
        vigente["ejemplar_id"],
        vigente["usuario_id"],
        bibliotecario_id,
        vigente["fecha_vencimiento"],
    )
    if resultado is None:
        raise ErrorValidacion(
            "El ejemplar se acaba de prestar a alguien más. Elige otro.",
            {"ejemplar": "El ejemplar ya no está disponible."},
            vigente,
            codigo=409,
        )
    prestamo_id, folio = resultado

    # HU-02-06: si el usuario estaba en la lista de espera, ya se atendio.
    libro = ejemplar_modelo.obtener(vigente["ejemplar_id"])
    espera_modelo.marcar_atendida(libro["libro_id"], vigente["usuario_id"])
    return (
        prestamo_id,
        f"Préstamo {folio} registrado. Ahora envía o imprime la boleta.",
    )


# ============================================================
# RENOVACION DEL PRESTAMO (HU-02-05)
# ============================================================


def listar_renovaciones(prestamo_id):
    """
    Descripcion:
        HU-02-05: Historial de renovaciones del prestamo.

    Parametros:
        prestamo_id (int): id del prestamo.

    Salida:
        list[sqlite3.Row]: renovaciones en orden.
    """
    return prestamo_modelo.listar_renovaciones(prestamo_id)


def revisar_renovacion(prestamo):
    """
    Descripcion:
        HU-02-05: Revisa si el prestamo se puede renovar y calcula la nueva
        fecha de devolucion (la actual mas los dias de prestamo del perfil).
        No se renueva si el prestamo no esta activo, la cuenta esta
        deshabilitada, ya vencio, se acabaron las renovaciones del perfil o
        alguien espera el libro.

    Parametros:
        prestamo (sqlite3.Row): prestamo de prestamo_modelo.obtener().

    Salida:
        dict: permitida (bool), motivo (str o None), numero, maximo y
        vencimiento_nuevo (date).
    """
    maximo = prestamo["max_renovaciones"] or 0
    usadas = prestamo["renovaciones"]
    vencimiento_nuevo = date.fromisoformat(
        prestamo["fecha_vencimiento"]
    ) + timedelta(days=prestamo["dias_prestamo"] or 0)

    motivo = None
    if prestamo["estado"] != config.ESTADO_PRESTAMO_ACTIVO:
        motivo = "Este préstamo ya no está activo."
    elif prestamo["usuario_estado"] != config.ESTADO_HABILITADA:
        motivo = "La cuenta del usuario está deshabilitada."
    # HU-02-05 · Prestamo vencido.
    elif verificar_vencido(prestamo):
        motivo = (
            "El préstamo está vencido: el libro se debe devolver y no se "
            "puede renovar."
        )
    # HU-02-05 · Limite de renovaciones.
    elif usadas >= maximo:
        motivo = (
            f"Ya se usaron las {maximo} renovaciones que permite el perfil "
            f"{prestamo['perfil']}."
            if maximo
            else f"El perfil {prestamo['perfil']} no permite renovaciones."
        )
    # HU-02-05 · Libro con lista de espera.
    else:
        en_espera = espera_modelo.obtener_libro(prestamo["libro_clave"])[
            "en_espera"
        ]
        if en_espera:
            motivo = (
                f"Hay {en_espera} persona(s) en la lista de espera de este "
                "libro; se debe devolver en la fecha acordada."
            )
    return {
        "permitida": motivo is None,
        "motivo": motivo,
        "numero": usadas + 1,
        "maximo": maximo,
        "vencimiento_nuevo": vencimiento_nuevo,
    }


def renovar(prestamo):
    """
    Descripcion:
        HU-02-05: Renueva el prestamo si se cumplen las condiciones y guarda
        la renovacion en el historial.

    Parametros:
        prestamo (sqlite3.Row): prestamo.

    Salida:
        str: mensaje con la nueva fecha de devolucion.

    Excepciones:
        ErrorValidacion (422) con el motivo si no se puede renovar.
    """
    revision = revisar_renovacion(prestamo)
    if not revision["permitida"]:
        raise ErrorValidacion(revision["motivo"], codigo=422)
    prestamo_modelo.renovar(
        prestamo["id"],
        revision["numero"],
        prestamo["fecha_vencimiento"],
        revision["vencimiento_nuevo"].isoformat(),
    )
    return (
        f"Préstamo {prestamo['folio']} renovado hasta el "
        f"{revision['vencimiento_nuevo']:%d/%m/%Y} (renovación "
        f"{revision['numero']} de {revision['maximo']}). Envía la boleta "
        "actualizada al usuario."
    )


# ============================================================
# BOLETA DE PRESTAMO (HU-02-04)
# ============================================================


def _formatear_fecha(valor, con_hora=False):
    """
    Descripcion:
        Muestra una fecha de SQLite como dd/mm/aaaa (y la hora si se pide).

    Parametros:
        valor (str): fecha aaaa-mm-dd o aaaa-mm-dd hh:mm:ss.
        con_hora (bool): True para agregar la hora.

    Salida:
        str: fecha con formato.
    """
    if len(valor) > 10:
        fecha = datetime.strptime(valor, "%Y-%m-%d %H:%M:%S")
    else:
        fecha = datetime.strptime(valor, "%Y-%m-%d")
    return fecha.strftime("%d/%m/%Y %H:%M" if con_hora else "%d/%m/%Y")


def armar_datos_boleta(prestamo):
    """
    Descripcion:
        HU-02-04: Arma los datos de la boleta en el orden en que se muestran;
        los usan el PDF, el correo y el mensaje de WhatsApp.

    Parametros:
        prestamo (sqlite3.Row): prestamo de prestamo_modelo.obtener().

    Salida:
        list[tuple[str, str]]: (etiqueta, valor) de cada dato.
    """
    ubicacion = (
        f"{prestamo['estancia']} · Estante {prestamo['estante']} · "
        f"Posición {prestamo['posicion']}"
        if prestamo["estancia"]
        else config.MENSAJES["ubicacion_no_registrada"]
    )
    multa = prestamo["multa_diaria"] or 0
    return [
        (
            "Usuario",
            f"{prestamo['usuario_nombre']} "
            f"({prestamo['usuario_identificador']})",
        ),
        ("Perfil", prestamo["perfil"] or "—"),
        ("Libro", prestamo["titulo"]),
        ("Autores", prestamo["autores"] or "—"),
        ("Clave del libro", prestamo["libro_clave"]),
        ("Ejemplar", prestamo["ejemplar_codigo"]),
        ("Ubicación", ubicacion),
        (
            "Fecha de préstamo",
            _formatear_fecha(prestamo["fecha_prestamo"], con_hora=True),
        ),
        (
            "Fecha de devolución",
            _formatear_fecha(prestamo["fecha_vencimiento"]),
        ),
        (
            "Renovaciones",
            f"{prestamo['renovaciones']} de "
            f"{prestamo['max_renovaciones'] or 0}",
        ),
        ("Multa por día de retraso", f"${multa:,.2f} MXN"),
        ("Atendió", prestamo["bibliotecario"]),
    ]


def armar_texto_boleta(prestamo):
    """
    Descripcion:
        HU-02-04: Texto de la boleta para el correo y WhatsApp.

    Parametros:
        prestamo (sqlite3.Row): prestamo.

    Salida:
        str: boleta en texto plano.
    """
    renglones = [
        f"Boleta de préstamo {prestamo['folio']}",
        config.NOMBRE_CLIENTE,
        "",
    ]
    renglones += [
        f"{etiqueta}: {valor}"
        for etiqueta, valor in armar_datos_boleta(prestamo)
    ]
    renglones += ["", NOTA_BOLETA]
    return "\n".join(renglones)


def generar_pdf_boleta(prestamo):
    """
    Descripcion:
        HU-02-04: Genera la boleta en PDF.

    Parametros:
        prestamo (sqlite3.Row): prestamo.

    Salida:
        tuple[bytes, str]: contenido del PDF y nombre del archivo.
    """
    contenido = pdf.generar_boleta(
        prestamo["folio"], armar_datos_boleta(prestamo), NOTA_BOLETA
    )
    return contenido, f"boleta_{prestamo['folio']}.pdf"


def enviar_por_correo(prestamo, correo):
    """
    Descripcion:
        HU-02-04 · Envio por correo: valida el correo, envia la boleta con el
        PDF adjunto y registra el comprobante.

    Parametros:
        prestamo (sqlite3.Row): prestamo.
        correo (str): correo capturado.

    Salida:
        tuple[str, str]: (tono, mensaje) para el aviso.

    Excepciones:
        ErrorValidacion si el correo no es valido (400) o el envio falla
        (502).
    """
    correo = (correo or "").strip()
    if not re.match(config.PATRON_EMAIL, correo):
        raise ErrorValidacion(
            "Escribe un correo válido para enviar la boleta.",
            {
                "correo": "Escribe un correo válido, por ejemplo "
                "nombre@ducky.edu.mx."
            },
            {"correo": correo},
        )

    # Enviamos (o guardamos en modo demostracion) y registramos la boleta.
    contenido, nombre = generar_pdf_boleta(prestamo)
    try:
        ruta_demo = notificaciones.enviar_correo(
            correo,
            f"Boleta de préstamo {prestamo['folio']} · "
            f"{config.NOMBRE_CLIENTE}",
            armar_texto_boleta(prestamo),
            nombre,
            contenido,
            nombre=f"boleta_{prestamo['folio']}",
        )
    except notificaciones.ErrorEnvio as error:
        raise ErrorValidacion(
            str(error), {"correo": str(error)}, {"correo": correo}, codigo=502
        ) from error
    prestamo_modelo.registrar_comprobante(
        prestamo["id"], config.MEDIO_CORREO, correo
    )

    if ruta_demo:
        return (
            "advertencia",
            "Modo demostración: no hay una cuenta de correo configurada, "
            f"así que el correo para {correo} se guardó en la carpeta "
            f"boletas_enviadas ({os.path.basename(ruta_demo)}). Configura "
            "el correo en el archivo .env para enviarlo de verdad.",
        )
    return "exito", f"Boleta {prestamo['folio']} enviada a {correo}."


def normalizar_telefono(telefono):
    """
    Descripcion:
        Deja el telefono solo con digitos y con lada de pais; a los numeros
        de 10 digitos les agrega la de Mexico (config.LADA_WHATSAPP).

    Parametros:
        telefono (str): telefono capturado, por ejemplo 81 1234 5678.

    Salida:
        str o None: numero listo para WhatsApp, o None si no es valido.
    """
    digitos = re.sub(r"\D", "", telefono or "")
    if len(digitos) == 10:
        return config.LADA_WHATSAPP + digitos
    if 11 <= len(digitos) <= 15:
        return digitos
    return None


def enviar_por_whatsapp(prestamo, telefono):
    """
    Descripcion:
        HU-02-04 · Envio por WhatsApp: valida el telefono, manda la boleta por
        la API de Twilio (si esta configurada) o arma el enlace wa.me, y
        registra el comprobante.

    Parametros:
        prestamo (sqlite3.Row): prestamo.
        telefono (str): telefono capturado.

    Salida:
        tuple[str, str]: ("enlace", url de wa.me) o ("exito", mensaje).

    Excepciones:
        ErrorValidacion si el telefono no es valido (400) o Twilio falla
        (502).
    """
    numero = normalizar_telefono(telefono)
    if numero is None:
        raise ErrorValidacion(
            "Escribe un teléfono válido para enviar la boleta.",
            {
                "telefono": "Escribe un celular de 10 dígitos, por ejemplo "
                "81 1234 5678."
            },
            {"telefono": (telefono or "").strip()},
        )

    texto = armar_texto_boleta(prestamo)
    if notificaciones.verificar_whatsapp_api_configurada():
        try:
            notificaciones.enviar_whatsapp(numero, texto)
        except notificaciones.ErrorEnvio as error:
            raise ErrorValidacion(
                str(error),
                {"telefono": str(error)},
                {"telefono": telefono},
                codigo=502,
            ) from error
        prestamo_modelo.registrar_comprobante(
            prestamo["id"], config.MEDIO_WHATSAPP, f"+{numero}"
        )
        return (
            "exito",
            f"Boleta {prestamo['folio']} enviada por WhatsApp a +{numero}.",
        )

    # Sin API: se abre WhatsApp con el mensaje listo para enviar.
    prestamo_modelo.registrar_comprobante(
        prestamo["id"], config.MEDIO_WHATSAPP, f"+{numero}"
    )
    return "enlace", notificaciones.crear_enlace_whatsapp(numero, texto)


def imprimir(prestamo, impresora_id):
    """
    Descripcion:
        HU-02-04 · Boleta impresa: revisa la impresora elegida (simulada en
        config.IMPRESORAS) y registra el comprobante.

    Parametros:
        prestamo (sqlite3.Row): prestamo.
        impresora_id (str): id de la impresora elegida.

    Salida:
        tuple[tuple[str, str], int]: (tono, mensaje) del aviso y codigo HTTP.
    """
    impresora = next(
        (
            opcion
            for opcion in config.IMPRESORAS
            if opcion["id"] == impresora_id
        ),
        None,
    )
    if impresora is None:
        return (
            "error",
            "Selecciona una impresora para imprimir la boleta.",
        ), 400
    if not impresora["disponible"]:
        return (
            "error",
            f"La impresora {impresora['nombre']} no está disponible. Elige "
            "otra.",
        ), 503

    prestamo_modelo.registrar_comprobante(
        prestamo["id"], config.MEDIO_IMPRESION, impresora["nombre"]
    )
    return (
        "exito",
        f"Boleta {prestamo['folio']} enviada a {impresora['nombre']}.",
    ), 200
