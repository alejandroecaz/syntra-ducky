"""
============================================================
Archivo:      controllers/inicio_controller.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Controlador del panel de inicio web.

    Papel en MVC: pide al servicio las funciones e indicadores del perfil
    en sesion y los manda a la vista views/inicio.html.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

from flask import Blueprint, render_template, session

from services import inicio_servicio
from utils.seguridad import sesion_requerida

# Blueprint para el panel de inicio.
inicio_bp = Blueprint("inicio", __name__)


@inicio_bp.route("/inicio")
@sesion_requerida
def mostrar_panel():
    """
    Descripcion:
        HU-01-01: Muestra el panel de inicio con solo las funciones e
        indicadores que permite el perfil.

    Parametros:
        Ninguno.

    Salida:
        str: pagina HTML de la vista inicio.html.

    Excepciones:
        Sin sesion redirige al login.
    """
    permisos = session.get("permisos", [])
    return render_template(
        "inicio.html",
        acciones=inicio_servicio.obtener_acciones(permisos),
        indicadores=inicio_servicio.obtener_indicadores(permisos),
    )
