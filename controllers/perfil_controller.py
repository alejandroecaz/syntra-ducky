"""Controlador de perfiles y permisos (HU-01-07 y consulta para HU-01-08).

Papel en MVC: recibe la petición, llama a services/perfil_servicio.py y regresa la vista.
"""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from services import perfil_servicio
from services.errores import ErrorValidacion
from utils.seguridad import permiso_requerido

perfil_bp = Blueprint("perfiles", __name__, url_prefix="/perfiles")


@perfil_bp.route("")
@permiso_requerido("perfiles.crear", "perfiles.asignar")
def lista():
    return render_template(
        "perfiles/lista.html",
        perfiles=perfil_servicio.listar(),
        permisos=perfil_servicio.permisos_por_perfil(),
        descripciones=perfil_servicio.descripciones(),
        resaltar=request.args.get("resaltar", type=int),
    )


@perfil_bp.route("/nuevo", methods=["GET", "POST"])
@permiso_requerido("perfiles.crear")
def nuevo():
    grupos = perfil_servicio.permisos_agrupados()
    if request.method == "GET":
        return render_template("perfiles/form.html", grupos=grupos, valores={}, seleccionados=[], errores={})
    try:
        perfil_id, mensaje = perfil_servicio.crear(request.form)
    except ErrorValidacion as error:
        return render_template(
            "perfiles/form.html", grupos=grupos, valores=error.valores, seleccionados=error.valores["permisos"],
            errores=error.errores, error_general=error.mensaje,
        ), error.codigo
    flash(mensaje, "success")
    return redirect(url_for("perfiles.lista", resaltar=perfil_id))
