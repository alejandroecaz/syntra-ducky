from flask import Blueprint, flash, redirect, render_template, request, url_for

import config
from models import perfil as perfil_modelo
from utils.seguridad import permiso_requerido

perfil_bp = Blueprint("perfiles", __name__, url_prefix="/perfiles")


def _permisos_agrupados():
    # Agrupa los permisos para mostrarlos en el formulario
    grupos = {}
    for codigo, descripcion, grupo in config.PERMISOS:
        grupos.setdefault(grupo, []).append((codigo, descripcion))
    return grupos


@perfil_bp.route("")
@permiso_requerido("perfiles.crear", "perfiles.asignar")
def lista():
    return render_template(
        "perfiles/lista.html",
        perfiles=perfil_modelo.listar(),
        permisos=perfil_modelo.permisos_por_perfil(),
        resaltar=request.args.get("resaltar", type=int),
    )


@perfil_bp.route("/nuevo", methods=["GET", "POST"])
@permiso_requerido("perfiles.crear")
def nuevo():
    grupos = _permisos_agrupados()
    if request.method == "GET":
        return render_template("perfiles/form.html", grupos=grupos, valores={}, seleccionados=[], errores={})

    nombre = request.form.get("nombre", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    validos = {codigo for codigo, _, _ in config.PERMISOS}
    seleccionados = [p for p in request.form.getlist("permisos") if p in validos]
    valores = {"nombre": nombre, "descripcion": descripcion}
    errores = {}

    if not nombre:
        errores["nombre"] = "Captura el nombre del perfil."
    if not seleccionados:
        errores["permisos"] = "Selecciona al menos un permiso."

    if nombre and perfil_modelo.existe_nombre(nombre):
        errores["nombre"] = f"Ya existe un perfil llamado \"{nombre}\"."

    if errores:
        if nombre and perfil_modelo.existe_nombre(nombre):
            mensaje = "El perfil de usuario ya existe. No se creó un duplicado y el perfil registrado no cambió."
        else:
            mensaje = "Completa el nombre y selecciona al menos un permiso. El perfil no se registró."
        return render_template("perfiles/form.html", grupos=grupos, valores=valores,
                               seleccionados=seleccionados, errores=errores, error_general=mensaje), 400

    perfil_id = perfil_modelo.crear(nombre, descripcion, seleccionados)
    flash(f"Perfil \"{nombre}\" creado con {len(seleccionados)} permisos. Ya está disponible para asignarse.",
          "success")
    return redirect(url_for("perfiles.lista", resaltar=perfil_id))
