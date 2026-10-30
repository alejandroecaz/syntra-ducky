# ============================================================
# Archivo: controllers/perfil_controller.py
# Proyecto: Sistema Ducky de Gestión Bibliotecaria
# Syntra Technologies - Equipo 1 - Sprint 1
# Materia: Ingeniería de Software
# Autores:
#   - Melissa Silva Vázquez                #624352
#   - Tomás Zapata Pérez                   #629048
#   - Alejandro Evaristo Cazares Escobedo  #626337
# Descripción: Controlador de perfiles y permisos (HU-01-07 y consulta para HU-01-08).
# ============================================================
"""Controlador de perfiles y permisos (HU-01-07 y consulta para HU-01-08).

Papel en MVC: recibe la petición, llama a services/perfil_servicio.py y regresa la vista.
"""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from services import perfil_servicio
from services.errores import ErrorValidacion
from utils.seguridad import permiso_requerido

# Blueprint para las rutas de perfiles
perfil_bp = Blueprint("perfiles", __name__, url_prefix="/perfiles")


@perfil_bp.route("")
@permiso_requerido("perfiles.crear", "perfiles.asignar")
def lista():
    """HU-01-07 y HU-01-08: Muestra los perfiles con sus permisos."""
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
    """HU-01-07: Muestra el formulario y crea el perfil con sus permisos."""
    # GET: formulario vacío con los permisos agrupados
    grupos = perfil_servicio.permisos_agrupados()
    if request.method == "GET":
        return render_template("perfiles/form.html", grupos=grupos, valores={}, seleccionados=[], errores={})

    # POST: HU-01-07 · Nombre duplicado / Perfil incompleto regresan al formulario
    try:
        perfil_id, mensaje = perfil_servicio.crear(request.form)
    except ErrorValidacion as error:
        return render_template(
            "perfiles/form.html", grupos=grupos, valores=error.valores, seleccionados=error.valores["permisos"],
            errores=error.errores, error_general=error.mensaje,
        ), error.codigo

    # HU-01-07 · Perfil creado: volvemos a la lista con el nuevo resaltado
    flash(mensaje, "success")
    return redirect(url_for("perfiles.lista", resaltar=perfil_id))
