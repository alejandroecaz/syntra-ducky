# ============================================================
# Archivo: controllers/inicio_controller.py
# Proyecto: Sistema Ducky de Gestión Bibliotecaria
# Syntra Technologies - Equipo 1 - Sprint 1
# Materia: Ingeniería de Software
# Autores:
#   - Melissa Silva Vázquez                #624352
#   - Tomás Zapata Pérez                   #629048
#   - Alejandro Evaristo Cazares Escobedo  #626337
# Descripción: Controlador del panel de inicio web.
# ============================================================
"""Controlador del panel de inicio web.

Papel en MVC: pide al servicio las funciones e indicadores del perfil en sesión y los
manda a la vista views/inicio.html.
"""
from flask import Blueprint, render_template, session

from services import inicio_servicio
from utils.seguridad import login_requerido

# Blueprint para el panel de inicio
inicio_bp = Blueprint("inicio", __name__)


@inicio_bp.route("/inicio")
@login_requerido
def panel():
    """HU-01-01: Panel con solo las funciones e indicadores que permite el perfil."""
    permisos = session.get("permisos", [])
    return render_template(
        "inicio.html",
        acciones=inicio_servicio.acciones_para(permisos),
        indicadores=inicio_servicio.indicadores_para(permisos),
    )
