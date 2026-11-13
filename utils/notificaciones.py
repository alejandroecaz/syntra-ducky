"""
============================================================
Archivo:      utils/notificaciones.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Envio por correo y por WhatsApp de la boleta de prestamo (HU-02-04) y
    de los avisos de lista de espera (HU-02-06).

    Correo: se manda por SMTP con la cuenta de .env (CORREO_USUARIO y
    CORREO_CONTRASENA). Si no hay cuenta configurada, el correo se guarda
    como archivo .eml en CARPETA_BOLETAS (modo demostracion) para poder
    abrirlo y revisarlo.

    WhatsApp: si hay datos de Twilio en .env se manda por su API; si no,
    se arma un enlace wa.me que abre WhatsApp con el mensaje ya escrito.

    La configuracion se lee de current_app.config para que las pruebas
    puedan cambiarla sin enviar nada de verdad.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    13/11/2026
============================================================
"""

import base64
import json
import os
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr
from urllib import error as url_error
from urllib import parse, request

from flask import current_app

import config

# Segundos que se espera al servidor de correo o a Twilio.
TIEMPO_ESPERA = 15

# Direccion de la API de Twilio para mandar mensajes.
URL_TWILIO = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"


class ErrorEnvio(Exception):
    """El servidor de correo o la API de WhatsApp rechazaron el envio."""


# ============================================================
# CORREO
# ============================================================


def verificar_correo_configurado():
    """
    Descripcion:
        Revisa si hay una cuenta de correo en .env para enviar de verdad.

    Parametros:
        Ninguno.

    Salida:
        bool: True si hay usuario y contrasena de correo.
    """
    return bool(
        current_app.config.get("CORREO_USUARIO")
        and current_app.config.get("CORREO_CONTRASENA")
    )


def obtener_correo_tesoreria():
    """
    Descripcion:
        HU-02-08: Correo de Tesoreria al que se mandan las multas.

    Parametros:
        Ninguno.

    Salida:
        str: correo de .env (TESORERIA_CORREO) o el de config.py.
    """
    return (
        current_app.config.get("TESORERIA_CORREO") or config.TESORERIA_CORREO
    )


def armar_correo(destino, asunto, texto, adjunto_nombre=None, adjunto=None):
    """
    Descripcion:
        Arma el correo con el texto y, si se da, el PDF adjunto.

    Parametros:
        destino (str): correo de quien recibe.
        asunto (str): asunto del correo.
        texto (str): cuerpo en texto plano.
        adjunto_nombre (str o None): nombre del archivo PDF.
        adjunto (bytes o None): contenido del PDF.

    Salida:
        email.message.EmailMessage: correo listo para enviar.
    """
    remitente = (
        current_app.config.get("CORREO_REMITENTE")
        or current_app.config.get("CORREO_USUARIO")
        or "biblioteca@ducky.edu.mx"
    )
    mensaje = EmailMessage()
    mensaje["Subject"] = asunto
    mensaje["From"] = formataddr((config.NOMBRE_CLIENTE, remitente))
    mensaje["To"] = destino
    mensaje.set_content(texto)
    if adjunto:
        mensaje.add_attachment(
            adjunto,
            maintype="application",
            subtype="pdf",
            filename=adjunto_nombre,
        )
    return mensaje


def guardar_correo_demostracion(mensaje, nombre_base):
    """
    Descripcion:
        Modo demostracion: guarda el correo como archivo .eml (se abre con
        Mail u Outlook) en CARPETA_BOLETAS.

    Parametros:
        mensaje (email.message.EmailMessage): correo armado.
        nombre_base (str): inicio del nombre del archivo (el folio).

    Salida:
        str: ruta del archivo guardado.
    """
    carpeta = current_app.config.get("CARPETA_BOLETAS")
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(
        carpeta, f"{nombre_base}_{datetime.now():%Y%m%d_%H%M%S}.eml"
    )
    with open(ruta, "wb") as archivo:
        archivo.write(mensaje.as_bytes())
    return ruta


def enviar_correo(
    destino, asunto, texto, adjunto_nombre=None, adjunto=None, nombre="aviso"
):
    """
    Descripcion:
        HU-02-04 y HU-02-06: Envia un correo (la boleta con el PDF adjunto o
        un aviso). Sin cuenta configurada lo guarda como .eml (modo
        demostracion).

    Parametros:
        destino (str): correo de quien recibe.
        asunto (str): asunto del correo.
        texto (str): cuerpo en texto plano.
        adjunto_nombre (str o None): nombre del archivo PDF.
        adjunto (bytes o None): contenido del PDF.
        nombre (str): inicio del nombre del .eml en modo demostracion.

    Salida:
        str o None: ruta del .eml en modo demostracion, o None si se envio
        de verdad.

    Excepciones:
        ErrorEnvio si el servidor de correo rechaza la cuenta o no responde.
    """
    mensaje = armar_correo(destino, asunto, texto, adjunto_nombre, adjunto)

    # Sin cuenta de correo: modo demostracion.
    if not verificar_correo_configurado():
        return guardar_correo_demostracion(mensaje, nombre)

    # Con cuenta: lo mandamos por SMTP con conexion cifrada (STARTTLS).
    datos = current_app.config
    try:
        with smtplib.SMTP(
            datos["CORREO_SERVIDOR"],
            int(datos["CORREO_PUERTO"]),
            timeout=TIEMPO_ESPERA,
        ) as servidor:
            servidor.starttls(context=ssl.create_default_context())
            servidor.login(datos["CORREO_USUARIO"], datos["CORREO_CONTRASENA"])
            servidor.send_message(mensaje)
    except smtplib.SMTPAuthenticationError as error:
        raise ErrorEnvio(
            "El servidor de correo rechazó la cuenta configurada. Revisa "
            "CORREO_USUARIO y CORREO_CONTRASENA en el archivo .env."
        ) from error
    except (smtplib.SMTPException, OSError) as error:
        raise ErrorEnvio(
            "No se pudo conectar con el servidor de correo. Revisa la "
            "conexión a internet e inténtalo de nuevo."
        ) from error
    return None


# ============================================================
# WHATSAPP
# ============================================================


def verificar_whatsapp_api_configurada():
    """
    Descripcion:
        Revisa si hay datos de Twilio en .env para mandar WhatsApp por API.

    Parametros:
        Ninguno.

    Salida:
        bool: True si hay SID y token de Twilio.
    """
    return bool(
        current_app.config.get("TWILIO_SID")
        and current_app.config.get("TWILIO_TOKEN")
    )


def crear_enlace_whatsapp(numero, texto):
    """
    Descripcion:
        Arma el enlace wa.me que abre el chat con el numero y el mensaje ya
        escrito (WhatsApp Web o la app del celular).

    Parametros:
        numero (str): numero con lada de pais, solo digitos (528112345678).
        texto (str): mensaje.

    Salida:
        str: enlace https://wa.me/...
    """
    return f"https://wa.me/{numero}?text={parse.quote(texto)}"


def enviar_whatsapp(numero, texto):
    """
    Descripcion:
        HU-02-04: Manda el mensaje de WhatsApp con la API de Twilio.

    Parametros:
        numero (str): numero con lada de pais, solo digitos.
        texto (str): mensaje.

    Salida:
        Ninguna.

    Excepciones:
        ErrorEnvio si Twilio rechaza el mensaje o no responde.
    """
    datos = current_app.config
    origen = datos["TWILIO_WHATSAPP_ORIGEN"]
    cuerpo = parse.urlencode(
        {
            "From": f"whatsapp:{origen}",
            "To": f"whatsapp:+{numero}",
            "Body": texto,
        }
    ).encode()
    credenciales = base64.b64encode(
        f"{datos['TWILIO_SID']}:{datos['TWILIO_TOKEN']}".encode()
    ).decode()
    peticion = request.Request(
        URL_TWILIO.format(sid=datos["TWILIO_SID"]),
        data=cuerpo,
        headers={"Authorization": f"Basic {credenciales}"},
        method="POST",
    )
    try:
        with request.urlopen(peticion, timeout=TIEMPO_ESPERA):
            pass
    except url_error.HTTPError as error:
        # Twilio explica el problema en el campo "message" de su respuesta.
        try:
            detalle = json.loads(error.read().decode()).get("message", "")
        except ValueError:
            detalle = ""
        raise ErrorEnvio(
            f"WhatsApp rechazó el mensaje. {detalle}".strip()
        ) from error
    except (url_error.URLError, OSError) as error:
        raise ErrorEnvio(
            "No se pudo conectar con el servicio de WhatsApp. Revisa la "
            "conexión a internet e inténtalo de nuevo."
        ) from error
