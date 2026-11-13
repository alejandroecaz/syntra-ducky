"""
============================================================
Archivo:      utils/claude.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Conexion con la API de Claude (Anthropic) para el chatbot (HU-02-09).
    La llave se lee de .env (ANTHROPIC_API_KEY); el modelo, el nivel de
    esfuerzo y los limites estan en config.py. Los errores de la API se
    convierten en ErrorClaude con un mensaje en espanol.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    13/11/2026
============================================================
"""

import anthropic
from flask import current_app

import config


class ErrorClaude(Exception):
    """La API de Claude no respondio o rechazo la peticion."""


def verificar_configurado():
    """
    Descripcion:
        Revisa si hay llave de la API de Claude en .env.

    Parametros:
        Ninguno.

    Salida:
        bool: True si hay llave.
    """
    return bool(current_app.config.get("ANTHROPIC_API_KEY"))


def pedir_respuesta(system, mensajes, herramientas):
    """
    Descripcion:
        HU-02-09: Pide la siguiente respuesta del modelo con las
        instrucciones, la conversacion y las herramientas del chatbot.

    Parametros:
        system (list[dict]): bloques de instrucciones.
        mensajes (list[dict]): conversacion (user / assistant).
        herramientas (list[dict]): definicion de las herramientas.

    Salida:
        anthropic.types.Message: respuesta del modelo.

    Excepciones:
        ErrorClaude con el motivo en espanol si la API falla.
    """
    cliente = anthropic.Anthropic(
        api_key=current_app.config.get("ANTHROPIC_API_KEY"),
        timeout=config.CHATBOT_TIEMPO_ESPERA,
        max_retries=1,
    )
    try:
        return cliente.messages.create(
            model=config.CHATBOT_MODELO,
            max_tokens=config.CHATBOT_MAX_TOKENS,
            output_config={"effort": config.CHATBOT_ESFUERZO},
            system=system,
            tools=herramientas,
            messages=mensajes,
        )
    except anthropic.AuthenticationError as error:
        raise ErrorClaude(
            "La llave de la API de Claude no es válida. Revisa "
            "ANTHROPIC_API_KEY en el archivo .env."
        ) from error
    except anthropic.PermissionDeniedError as error:
        raise ErrorClaude(
            "La llave de la API de Claude no tiene permiso para usar el "
            "modelo."
        ) from error
    except anthropic.RateLimitError as error:
        raise ErrorClaude(
            "La API de Claude recibió demasiadas preguntas seguidas. "
            "Intenta en un momento."
        ) from error
    except anthropic.BadRequestError as error:
        # Sin credito la API responde 400 con un mensaje sobre el saldo.
        if "credit" in str(error.message).lower():
            raise ErrorClaude(
                "La cuenta de la API de Claude no tiene crédito. Carga "
                "saldo en platform.claude.com."
            ) from error
        raise ErrorClaude("La API de Claude rechazó la pregunta.") from error
    except anthropic.APIStatusError as error:
        raise ErrorClaude(
            f"La API de Claude respondió con un error ({error.status_code})."
        ) from error
    except anthropic.APIConnectionError as error:
        raise ErrorClaude(
            "No hay conexión con la API de Claude. Revisa el internet."
        ) from error
