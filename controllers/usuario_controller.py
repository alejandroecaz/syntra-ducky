# ============================================================
# Archivo: controllers/usuario_controller.py
# Proyecto: Sistema Ducky de Gestión Bibliotecaria
# Syntra Technologies - Equipo 1 - Sprint 1
# Materia: Ingeniería de Software
# Autores:
#   - Melissa Silva Vázquez                #624352
#   - Tomás Zapata Pérez                   #629048
#   - Alejandro Evaristo Cazares Escobedo  #626337
# Descripción: Controlador de usuarios: consulta, registro, edición, baja lógica y asignación de perfil.
# ============================================================
"""Controlador de usuarios: consulta, registro, edición, baja lógica y asignación de perfil.

Cubre HU-01-02 a HU-01-05 y HU-01-08. Papel en MVC: recibe la petición, llama a
services/usuario_servicio.py y regresa la vista de views/usuarios/.
"""
from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from services import perfil_servicio, usuario_servicio
from services.errores import ErrorValidacion
from utils.seguridad import permiso_requerido

# Blueprint para las rutas de usuarios
usuario_bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


def _usuario_o_404(usuario_id):
    """El usuario o responde 404 si no existe."""
    usuario = usuario_servicio.obtener(usuario_id)
    if usuario is None:
        abort(404)
    return usuario


# HU-01-05: consulta de usuarios

@usuario_bp.route("")
@permiso_requerido("usuarios.consultar")
def lista():
    """HU-01-05: Lista de usuarios o resultados por identificador o nombre."""
    # Leemos el criterio y el texto de la búsqueda
    criterio = request.args.get("criterio", "nombre")
    texto = request.args.get("q", "").strip()
    buscando = "buscar" in request.args

    # El servicio decide si lista todo o busca
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
    """HU-01-05: Datos, perfil, permisos y estado de una cuenta."""
    usuario = _usuario_o_404(usuario_id)
    return render_template("usuarios/detalle.html", usuario=usuario, permisos=usuario_servicio.permisos_de(usuario),
                           descripciones=perfil_servicio.descripciones())


# HU-01-02: registro de usuarios

@usuario_bp.route("/nuevo", methods=["GET", "POST"])
@permiso_requerido("usuarios.registrar")
def nuevo():
    """HU-01-02: Muestra el formulario de registro y crea la cuenta."""
    # GET: formulario vacío con los perfiles disponibles
    perfiles = usuario_servicio.perfiles()
    if request.method == "GET":
        return render_template("usuarios/form.html", modo="nuevo", valores={}, errores={}, perfiles=perfiles)

    # POST: HU-01-02 · Usuario duplicado / Registro incompleto regresan al formulario
    try:
        nuevo_id, mensaje = usuario_servicio.registrar(request.form)
    except ErrorValidacion as error:
        return render_template("usuarios/form.html", modo="nuevo", valores=error.valores, errores=error.errores,
                               perfiles=perfiles, error_general=error.mensaje), error.codigo

    # HU-01-02 · Registro exitoso: se muestra en la consulta, resaltado
    flash(mensaje, "success")
    return redirect(url_for("usuarios.lista", resaltar=nuevo_id))


# HU-01-04: actualizar datos

@usuario_bp.route("/<int:usuario_id>/editar", methods=["GET", "POST"])
@permiso_requerido("usuarios.editar")
def editar(usuario_id):
    """HU-01-04: Carga el formulario con los datos de la cuenta y guarda los cambios."""
    # GET: formulario con los datos actuales
    usuario = _usuario_o_404(usuario_id)
    if request.method == "GET":
        return render_template("usuarios/form.html", modo="editar", usuario=usuario,
                               valores=usuario_servicio.valores_edicion(usuario), errores={})

    # POST: HU-01-04 · Cuenta asignada a otra persona / Nombre obligatorio omitido
    try:
        datos = usuario_servicio.actualizar(usuario, request.form)
    except ErrorValidacion as error:
        return render_template("usuarios/form.html", modo="editar", usuario=usuario, valores=error.valores,
                               errores=error.errores, error_general=error.mensaje), error.codigo

    # Si editó su propia cuenta, actualizamos el nombre y la cuenta de la sesión
    if usuario_id == session.get("usuario_id"):
        session["nombre"], session["cuenta"] = datos["nombre_completo"], datos["cuenta"]

    # HU-01-04 · Actualización exitosa
    flash("Datos del usuario actualizados correctamente.", "success")
    return redirect(url_for("usuarios.detalle", usuario_id=usuario_id))


# HU-01-03: habilitar / deshabilitar cuenta

@usuario_bp.route("/<int:usuario_id>/estado", methods=["POST"])
@permiso_requerido("usuarios.baja")
def cambiar_estado(usuario_id):
    """HU-01-03: Deshabilita o habilita la cuenta (la confirmación se hace en un modal)."""
    # Solo se regresa a rutas internas
    usuario = _usuario_o_404(usuario_id)
    volver = request.form.get("volver", "")
    destino = volver if volver.startswith("/") and not volver.startswith("//") else None

    # HU-01-03 · Baja lógica exitosa
    categoria, mensaje = usuario_servicio.cambiar_estado(usuario, request.form.get("accion"),
                                                         session.get("usuario_id"))
    flash(mensaje, categoria)
    return redirect(destino or url_for("usuarios.detalle", usuario_id=usuario_id))


# HU-01-08: asignar perfil

@usuario_bp.route("/<int:usuario_id>/perfil", methods=["GET", "POST"])
@permiso_requerido("perfiles.asignar")
def asignar_perfil(usuario_id):
    """HU-01-08: Muestra los perfiles disponibles y asigna o cambia el de la cuenta."""
    # Datos que usan el GET y el POST
    usuario = _usuario_o_404(usuario_id)
    contexto = dict(usuario=usuario, perfiles=usuario_servicio.perfiles(),
                    permisos=perfil_servicio.permisos_por_perfil())
    if request.method == "GET":
        return render_template("usuarios/asignar_perfil.html", **contexto, seleccionado="", errores={})

    # POST: HU-01-08 · Perfil sin seleccionar / inexistente regresan al formulario
    seleccionado = request.form.get("perfil_id", "")
    try:
        categoria, mensaje = usuario_servicio.asignar_perfil(usuario, seleccionado)
    except ErrorValidacion as error:
        return render_template("usuarios/asignar_perfil.html", **contexto, seleccionado=seleccionado,
                               errores=error.errores, error_general=error.mensaje), error.codigo

    # HU-01-08 · Asignar perfil / Modificar perfil de usuario
    flash(mensaje, categoria)
    return redirect(url_for("usuarios.detalle", usuario_id=usuario_id))
