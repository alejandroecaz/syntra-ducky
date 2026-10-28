"""Controlador de usuarios: consulta, registro, edición, baja lógica y asignación de perfil.

Cubre HU-01-02 a HU-01-05 y HU-01-08. Papel en MVC: recibe la petición, llama a
services/usuario_servicio.py y regresa la vista de views/usuarios/.
"""
from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from services import perfil_servicio, usuario_servicio
from services.errores import ErrorValidacion
from utils.seguridad import permiso_requerido

usuario_bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


def _usuario_o_404(usuario_id):
    usuario = usuario_servicio.obtener(usuario_id)
    if usuario is None:
        abort(404)
    return usuario


# HU-01-05: consulta de usuarios

@usuario_bp.route("")
@permiso_requerido("usuarios.consultar")
def lista():
    criterio = request.args.get("criterio", "nombre")
    texto = request.args.get("q", "").strip()
    buscando = "buscar" in request.args
    usuarios, error_busqueda = usuario_servicio.buscar(criterio, texto, buscando)
    return render_template(
        "usuarios/lista.html",
        usuarios=usuarios,
        criterio=criterio,
        texto=texto,
        buscando=buscando,
        error_busqueda=error_busqueda,
        resaltar=request.args.get("resaltar", type=int),
    )


@usuario_bp.route("/<int:usuario_id>")
@permiso_requerido("usuarios.consultar")
def detalle(usuario_id):
    usuario = _usuario_o_404(usuario_id)
    return render_template("usuarios/detalle.html", usuario=usuario, permisos=usuario_servicio.permisos_de(usuario),
                           descripciones=perfil_servicio.descripciones())


# HU-01-02: registro de usuarios

@usuario_bp.route("/nuevo", methods=["GET", "POST"])
@permiso_requerido("usuarios.registrar")
def nuevo():
    perfiles = usuario_servicio.perfiles()
    if request.method == "GET":
        return render_template("usuarios/form.html", modo="nuevo", valores={}, errores={}, perfiles=perfiles)
    try:
        nuevo_id, mensaje = usuario_servicio.registrar(request.form)
    except ErrorValidacion as error:
        return render_template("usuarios/form.html", modo="nuevo", valores=error.valores, errores=error.errores,
                               perfiles=perfiles, error_general=error.mensaje), error.codigo
    flash(mensaje, "success")
    return redirect(url_for("usuarios.lista", resaltar=nuevo_id))


# HU-01-04: actualizar datos

@usuario_bp.route("/<int:usuario_id>/editar", methods=["GET", "POST"])
@permiso_requerido("usuarios.editar")
def editar(usuario_id):
    usuario = _usuario_o_404(usuario_id)
    if request.method == "GET":
        return render_template("usuarios/form.html", modo="editar", usuario=usuario,
                               valores=usuario_servicio.valores_edicion(usuario), errores={})
    try:
        datos = usuario_servicio.actualizar(usuario, request.form)
    except ErrorValidacion as error:
        return render_template("usuarios/form.html", modo="editar", usuario=usuario, valores=error.valores,
                               errores=error.errores, error_general=error.mensaje), error.codigo

    if usuario_id == session.get("usuario_id"):
        session["nombre"], session["cuenta"] = datos["nombre_completo"], datos["cuenta"]
    flash("Datos del usuario actualizados correctamente.", "success")
    return redirect(url_for("usuarios.detalle", usuario_id=usuario_id))


# HU-01-03: habilitar / deshabilitar cuenta

@usuario_bp.route("/<int:usuario_id>/estado", methods=["POST"])
@permiso_requerido("usuarios.baja")
def cambiar_estado(usuario_id):
    usuario = _usuario_o_404(usuario_id)
    volver = request.form.get("volver", "")
    destino = volver if volver.startswith("/") and not volver.startswith("//") else None
    categoria, mensaje = usuario_servicio.cambiar_estado(usuario, request.form.get("accion"),
                                                         session.get("usuario_id"))
    flash(mensaje, categoria)
    return redirect(destino or url_for("usuarios.detalle", usuario_id=usuario_id))


# HU-01-08: asignar perfil

@usuario_bp.route("/<int:usuario_id>/perfil", methods=["GET", "POST"])
@permiso_requerido("perfiles.asignar")
def asignar_perfil(usuario_id):
    usuario = _usuario_o_404(usuario_id)
    contexto = dict(usuario=usuario, perfiles=usuario_servicio.perfiles(),
                    permisos=perfil_servicio.permisos_por_perfil())
    if request.method == "GET":
        return render_template("usuarios/asignar_perfil.html", **contexto, seleccionado="", errores={})

    seleccionado = request.form.get("perfil_id", "")
    try:
        categoria, mensaje = usuario_servicio.asignar_perfil(usuario, seleccionado)
    except ErrorValidacion as error:
        return render_template("usuarios/asignar_perfil.html", **contexto, seleccionado=seleccionado,
                               errores=error.errores, error_general=error.mensaje), error.codigo
    flash(mensaje, categoria)
    return redirect(url_for("usuarios.detalle", usuario_id=usuario_id))
