"""
============================================================
Archivo:      services/multa_servicio.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Servicio de multas (Sprint 2, Devolver libros):
        HU-02-08 Generacion de multas y envio a Tesoreria

    Las multas se generan al registrar la devolucion
    (services/devolucion_servicio.py). Aqui se manda el aviso a
    Tesoreria por correo con el PDF adjunto y, cuando Tesoreria confirma
    el cobro, se registra el pago para liberar el adeudo del usuario.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    13/11/2026
============================================================
"""

import os
from datetime import datetime

import config
from models import multa as multa_modelo
from services.errores import ErrorValidacion
from utils import notificaciones, pdf

# Nota al pie del aviso de multa para Tesoreria.
NOTA_AVISO = (
    "Cobrar al usuario en la caja de Tesorería. Mientras la multa esté "
    "pendiente no puede llevarse libros prestados ni renovar; cuando se "
    "pague, la biblioteca registra el pago y se libera el adeudo."
)

# ============================================================
# CONSULTAS
# ============================================================


def formatear_monto(monto):
    """
    Descripcion:
        Muestra un monto en pesos, por ejemplo $1,234.50 MXN. Tambien se usa
        como filtro de Jinja.

    Parametros:
        monto (float, int o None): monto.

    Salida:
        str: monto con formato.
    """
    return f"${float(monto or 0):,.2f} {config.MONEDA_LOCAL}"


def obtener_vista(vista):
    """
    Descripcion:
        Regresa la vista de la lista de multas si es valida.

    Parametros:
        vista (str o None): "pendientes", "pagadas" o "todas".

    Salida:
        str: la vista pedida o "pendientes".
    """
    return vista if vista in config.VISTAS_MULTAS else "pendientes"


def listar(vista):
    """
    Descripcion:
        HU-02-08: Lista las multas de la vista elegida.

    Parametros:
        vista (str): "pendientes", "pagadas" o "todas".

    Salida:
        list[sqlite3.Row]: multas.
    """
    return multa_modelo.listar(obtener_vista(vista))


def obtener(multa_id):
    """
    Descripcion:
        HU-02-08: Obtiene la multa con sus envios a Tesoreria y su pago.

    Parametros:
        multa_id (int): id de la multa.

    Salida:
        dict con multa, envios y pago, o None si no existe.
    """
    multa = multa_modelo.obtener(multa_id)
    if multa is None:
        return None
    return {
        "multa": multa,
        "envios": multa_modelo.listar_envios(multa_id),
        "pago": multa_modelo.obtener_pago(multa_id),
    }


def contar_pendientes():
    """
    Descripcion:
        Multas pendientes y su total para la lista y el panel de inicio.

    Parametros:
        Ninguno.

    Salida:
        dict: cantidad, total y sin_enviar (cuantas no se mandan todavia).
    """
    totales = multa_modelo.contar_pendientes()
    totales["sin_enviar"] = len(multa_modelo.listar_pendientes_sin_enviar())
    return totales


# ============================================================
# ENVIO A TESORERIA (HU-02-08)
# ============================================================


def armar_datos_aviso(multas):
    """
    Descripcion:
        HU-02-08: Arma los datos del aviso de multa de un prestamo; los usan
        el PDF y el correo para Tesoreria.

    Parametros:
        multas (list[sqlite3.Row]): multas del mismo prestamo.

    Salida:
        list[tuple[str, str]]: (etiqueta, valor) de cada dato.
    """
    primera = multas[0]
    renglones = [
        (
            "Usuario",
            f"{primera['usuario_nombre']} "
            f"({primera['usuario_identificador']})",
        ),
        ("Perfil", primera["perfil"] or "—"),
        ("Préstamo", primera["folio"]),
        ("Libro", f"{primera['titulo']} ({primera['libro_clave']})"),
        ("Ejemplar", primera["ejemplar_codigo"]),
        (
            "Fecha de devolución acordada",
            datetime.strptime(
                primera["fecha_vencimiento"], "%Y-%m-%d"
            ).strftime("%d/%m/%Y"),
        ),
    ]
    for multa in multas:
        renglones.append(
            (
                f"Multa por {multa['motivo'].lower()}",
                f"{formatear_monto(multa['monto'])} · {multa['descripcion']}",
            )
        )
    renglones.append(
        ("Total a cobrar", formatear_monto(sum(m["monto"] for m in multas)))
    )
    return renglones


def armar_texto_aviso(multas):
    """
    Descripcion:
        HU-02-08: Texto del correo para Tesoreria.

    Parametros:
        multas (list[sqlite3.Row]): multas del mismo prestamo.

    Salida:
        str: aviso en texto plano.
    """
    renglones = [
        f"Aviso de multa · préstamo {multas[0]['folio']}",
        config.NOMBRE_CLIENTE,
        "",
    ]
    renglones += [
        f"{etiqueta}: {valor}" for etiqueta, valor in armar_datos_aviso(multas)
    ]
    renglones += ["", NOTA_AVISO]
    return "\n".join(renglones)


def generar_pdf_aviso(multas):
    """
    Descripcion:
        HU-02-08: Genera el aviso de multa en PDF.

    Parametros:
        multas (list[sqlite3.Row]): multas del mismo prestamo.

    Salida:
        tuple[bytes, str]: contenido del PDF y nombre del archivo.
    """
    folio = multas[0]["folio"]
    contenido = pdf.generar_boleta(
        folio, armar_datos_aviso(multas), NOTA_AVISO, titulo="Aviso de multa"
    )
    return contenido, f"aviso_multa_{folio}.pdf"


def enviar_a_tesoreria(multas):
    """
    Descripcion:
        HU-02-08 · Envio a Tesoreria: manda por correo el aviso con el PDF
        adjunto y guarda el envio de cada multa.

    Parametros:
        multas (list[sqlite3.Row]): multas pendientes del mismo prestamo.

    Salida:
        tuple[str, str]: (tono, mensaje) para el aviso.

    Excepciones:
        ErrorValidacion (409) si alguna multa ya esta pagada, o (502) si el
        servidor de correo falla.
    """
    if any(m["estado"] != config.ESTADO_MULTA_PENDIENTE for m in multas):
        raise ErrorValidacion(
            "Solo se mandan a Tesorería las multas pendientes de pago.",
            codigo=409,
        )
    destino = notificaciones.obtener_correo_tesoreria()
    folio = multas[0]["folio"]
    contenido, nombre = generar_pdf_aviso(multas)
    try:
        ruta_demo = notificaciones.enviar_correo(
            destino,
            f"Multa por cobrar · {folio} · {config.NOMBRE_CLIENTE}",
            armar_texto_aviso(multas),
            nombre,
            contenido,
            nombre=f"aviso_multa_{folio}",
        )
    except notificaciones.ErrorEnvio as error:
        raise ErrorValidacion(str(error), codigo=502) from error
    for multa in multas:
        multa_modelo.registrar_envio(multa["id"], destino)

    total = formatear_monto(sum(m["monto"] for m in multas))
    if ruta_demo:
        return (
            "advertencia",
            f"Modo demostración: el aviso de {total} para Tesorería "
            f"({destino}) se guardó en la carpeta boletas_enviadas "
            f"({os.path.basename(ruta_demo)}).",
        )
    return "exito", f"Aviso de {total} enviado a Tesorería ({destino})."


def enviar_pendientes():
    """
    Descripcion:
        HU-02-08: Manda a Tesoreria todas las multas pendientes que no se han
        enviado, un aviso por prestamo.

    Parametros:
        Ninguno.

    Salida:
        tuple[str, str]: (tono, mensaje) para el aviso.

    Excepciones:
        ErrorValidacion (409) si no hay nada que enviar, o (502) si el
        servidor de correo falla (lo que ya se mando queda guardado).
    """
    sin_enviar = multa_modelo.listar_pendientes_sin_enviar()
    if not sin_enviar:
        raise ErrorValidacion(
            "Todas las multas pendientes ya se mandaron a Tesorería.",
            codigo=409,
        )

    # Juntamos las multas de cada prestamo en un solo aviso.
    por_prestamo = {}
    for multa in sin_enviar:
        por_prestamo.setdefault(multa["prestamo_id"], []).append(multa)
    tono = "exito"
    for multas in por_prestamo.values():
        tono, _ = enviar_a_tesoreria(multas)

    avisos = len(por_prestamo)
    destino = notificaciones.obtener_correo_tesoreria()
    if tono == "advertencia":
        return (
            "advertencia",
            f"Modo demostración: {avisos} aviso(s) de {len(sin_enviar)} "
            "multa(s) para Tesorería se guardaron en la carpeta "
            "boletas_enviadas.",
        )
    return (
        "exito",
        f"Se enviaron {avisos} aviso(s) de {len(sin_enviar)} multa(s) a "
        f"Tesorería ({destino}).",
    )


# ============================================================
# PAGO DE LA MULTA
# ============================================================


def registrar_pago(multa, formulario, bibliotecario_id):
    """
    Descripcion:
        Registra el pago completo de la multa cuando Tesoreria confirma el
        cobro; con eso se libera el adeudo del usuario.

    Parametros:
        multa (sqlite3.Row): multa.
        formulario (werkzeug.datastructures.MultiDict o dict): metodo y
            referencia.
        bibliotecario_id (int): id de quien registra.

    Salida:
        str: mensaje de exito.

    Excepciones:
        ErrorValidacion con el error de cada campo (422), o (409) si la
        multa ya no esta pendiente.
    """
    if multa["estado"] != config.ESTADO_MULTA_PENDIENTE:
        raise ErrorValidacion("Esta multa ya no está pendiente.", codigo=409)

    valores = {
        "metodo": (formulario.get("metodo") or "").strip(),
        "referencia": (formulario.get("referencia") or "").strip(),
    }
    errores = {}
    if valores["metodo"] not in config.METODOS_PAGO:
        errores["metodo"] = "Elige cómo se pagó la multa."
    elif (
        valores["metodo"] != config.METODO_EFECTIVO
        and not (valores["referencia"])
    ):
        errores["referencia"] = (
            "Captura el folio del ticket o de la transferencia."
        )
    if len(valores["referencia"]) > 50:
        errores["referencia"] = "La referencia admite hasta 50 caracteres."
    if errores:
        raise ErrorValidacion(
            "No se puede registrar el pago. Revisa los datos marcados.",
            errores,
            valores,
            codigo=422,
        )

    if not multa_modelo.registrar_pago(
        multa, bibliotecario_id, valores["metodo"], valores["referencia"]
    ):
        raise ErrorValidacion("Esta multa ya no está pendiente.", codigo=409)
    return (
        f"Pago de {formatear_monto(multa['monto'])} registrado para "
        f"{multa['usuario_nombre']}."
    )
