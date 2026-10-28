"""Controlador del panel de inicio web.

Papel en MVC: pide al servicio las funciones e indicadores del perfil en sesión y los
manda a la vista views/inicio.html.
"""
from flask import Blueprint, render_template, session

from services import inicio_servicio
from utils.seguridad import login_requerido

inicio_bp = Blueprint("inicio", __name__)


@inicio_bp.route("/inicio")
@login_requerido
def panel():
    permisos = session.get("permisos", [])
    return render_template(
        "inicio.html",
        acciones=inicio_servicio.acciones_para(permisos),
        indicadores=inicio_servicio.indicadores_para(permisos),
    )
