"""
============================================================
Archivo:      controllers/usuario_controller.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Controlador de usuarios: consulta, registro, edicion, baja logica y
    asignacion de perfil.

    Cubre HU-01-02 a HU-01-05 y HU-01-08. Papel en MVC: recibe la
    peticion, llama a services/usuario_servicio.py y regresa la vista de
    views/usuarios/.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from services import perfil_servicio, usuario_servicio
from services.errores import ErrorValidacion
from utils.seguridad import permiso_requerido

# Blueprint para las rutas de usuarios.
usuario_bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


def _obtener_usuario_o_404(usuario_id):
    """
    Descripcion:
        Busca el usuario o responde 404 si no existe.

    Parametros:
        usuario_id (int): id del usuario (viene en la URL).

    Salida:
        sqlite3.Row: el usuario.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si el usuario no existe.
    """
    usuario = usuario_servicio.obtener(usuario_id)
    if usuario is None:
        abort(404)
    return usuario


# ============================================================
# CONSULTA DE USUARIOS (HU-01-05)
# Lista, busqueda y detalle de las cuentas.
# ============================================================


@usuario_bp.route("")
@permiso_requerido("usuarios.consultar")
def listar():
    """
    Descripcion:
        HU-01-05: Muestra la lista de usuarios o los resultados por
        identificador o nombre.

    Parametros:
        Ninguno.

    Salida:
        str: pagina HTML de la vista usuarios/lista.html.

    Excepciones:
        Responde 403 (werkzeug.exceptions.Forbidden) si el perfil no tiene el
        permiso; sin sesion redirige al login.
    """
    # Leemos el criterio y el texto de la busqueda.
    criterio = request.args.get("criterio", "nombre")
    texto = request.args.get("q", "").strip()
    buscando = "buscar" in request.args

    # El servicio decide si lista todo o busca.
    usuarios, error_busqueda = usuario_servicio.buscar(
        criterio, texto, buscando
    )
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
def mostrar_detalle(usuario_id):
    """
    Descripcion:
        HU-01-05: Muestra los datos, perfil, permisos y estado de una cuenta.

    Parametros:
        usuario_id (int): id del usuario (viene en la URL).

    Salida:
        str: pagina HTML de la vista usuarios/detalle.html.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si el usuario no existe. Responde
        403 (werkzeug.exceptions.Forbidden) si el perfil no tiene el permiso;
        sin sesion redirige al login.
    """
    usuario = _obtener_usuario_o_404(usuario_id)
    return render_template(
        "usuarios/detalle.html",
        usuario=usuario,
        permisos=usuario_servicio.listar_permisos(usuario),
        descripciones=perfil_servicio.obtener_descripciones(),
    )


# ============================================================
# REGISTRO DE USUARIOS (HU-01-02)
# Formulario de registro y alta de la cuenta.
# ============================================================


@usuario_bp.route("/nuevo", methods=["GET", "POST"])
@permiso_requerido("usuarios.registrar")
def registrar():
    """
    Descripcion:
        HU-01-02: Muestra el formulario de registro (GET) y crea la cuenta
        (POST).

    Parametros:
        Ninguno.

    Salida:
        str: pagina HTML de la vista del formulario con su codigo HTTP, o
        flask.Response: redireccion a la lista con el usuario nuevo resaltado.

    Excepciones:
        Responde 403 (werkzeug.exceptions.Forbidden) si el perfil no tiene el
        permiso; sin sesion redirige al login.
    """
    # GET: formulario vacio con los perfiles disponibles.
    perfiles = usuario_servicio.listar_perfiles()
    if request.method == "GET":
        return render_template(
            "usuarios/form.html",
            modo="nuevo",
            valores={},
            errores={},
            perfiles=perfiles,
        )

    # POST: HU-01-02 · Usuario duplicado / Registro incompleto regresan al
    # formulario.
    try:
        nuevo_id, mensaje = usuario_servicio.registrar(request.form)
    except ErrorValidacion as error:
        return render_template(
            "usuarios/form.html",
            modo="nuevo",
            valores=error.valores,
            errores=error.errores,
            perfiles=perfiles,
            error_general=error.mensaje,
        ), error.codigo

    # HU-01-02 · Registro exitoso: se muestra en la consulta, resaltado.
    flash(mensaje, "exito")
    return redirect(url_for("usuarios.listar", resaltar=nuevo_id))


# ============================================================
# ACTUALIZACION DE DATOS (HU-01-04)
# Carga los datos de la cuenta y guarda los cambios.
# ============================================================


@usuario_bp.route("/<int:usuario_id>/editar", methods=["GET", "POST"])
@permiso_requerido("usuarios.editar")
def editar(usuario_id):
    """
    Descripcion:
        HU-01-04: Carga el formulario con los datos de la cuenta (GET) y guarda
        los cambios (POST). Si edito su propia cuenta se actualiza la sesion.

    Parametros:
        usuario_id (int): id del usuario (viene en la URL).

    Salida:
        str: pagina HTML de la vista del formulario con su codigo HTTP, o
        flask.Response: redireccion al detalle.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si el usuario no existe. Responde
        403 (werkzeug.exceptions.Forbidden) si el perfil no tiene el permiso;
        sin sesion redirige al login.
    """
    # GET: formulario con los datos actuales.
    usuario = _obtener_usuario_o_404(usuario_id)
    if request.method == "GET":
        return render_template(
            "usuarios/form.html",
            modo="editar",
            usuario=usuario,
            valores=usuario_servicio.obtener_valores_edicion(usuario),
            errores={},
        )

    # POST: HU-01-04 · Cuenta asignada a otra persona / Nombre obligatorio
    # omitido.
    try:
        datos = usuario_servicio.actualizar(usuario, request.form)
    except ErrorValidacion as error:
        return render_template(
            "usuarios/form.html",
            modo="editar",
            usuario=usuario,
            valores=error.valores,
            errores=error.errores,
            error_general=error.mensaje,
        ), error.codigo

    # Si edito su propia cuenta, actualizamos el nombre y la cuenta de la
    # sesion.
    if usuario_id == session.get("usuario_id"):
        session["nombre"], session["cuenta"] = (
            datos["nombre_completo"],
            datos["cuenta"],
        )

    # HU-01-04 · Actualizacion exitosa.
    flash("Datos del usuario actualizados correctamente.", "exito")
    return redirect(url_for("usuarios.mostrar_detalle", usuario_id=usuario_id))


# ============================================================
# HABILITAR O DESHABILITAR CUENTA (HU-01-03)
# Baja logica de la cuenta confirmada desde un modal.
# ============================================================


@usuario_bp.route("/<int:usuario_id>/estado", methods=["POST"])
@permiso_requerido("usuarios.baja")
def cambiar_estado(usuario_id):
    """
    Descripcion:
        HU-01-03: Deshabilita o habilita la cuenta; la confirmacion se hace en
        un modal. Solo regresa a rutas internas.

    Parametros:
        usuario_id (int): id del usuario (viene en la URL).

    Salida:
        flask.Response: redireccion a la pantalla de origen o al detalle.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si el usuario no existe. Responde
        403 (werkzeug.exceptions.Forbidden) si el perfil no tiene el permiso;
        sin sesion redirige al login.
    """
    # Solo se regresa a rutas internas.
    usuario = _obtener_usuario_o_404(usuario_id)
    volver = request.form.get("volver", "")
    destino = (
        volver
        if volver.startswith("/") and not volver.startswith("//")
        else None
    )

    # HU-01-03 · Baja logica exitosa.
    categoria, mensaje = usuario_servicio.cambiar_estado(
        usuario, request.form.get("accion"), session.get("usuario_id")
    )
    flash(mensaje, categoria)
    return redirect(
        destino or url_for("usuarios.mostrar_detalle", usuario_id=usuario_id)
    )


# ============================================================
# ASIGNACION DE PERFIL (HU-01-08)
# Muestra los perfiles disponibles y cambia el de la cuenta.
# ============================================================


@usuario_bp.route("/<int:usuario_id>/perfil", methods=["GET", "POST"])
@permiso_requerido("perfiles.asignar")
def asignar_perfil(usuario_id):
    """
    Descripcion:
        HU-01-08: Muestra los perfiles disponibles (GET) y asigna o cambia el
        de la cuenta (POST).

    Parametros:
        usuario_id (int): id del usuario (viene en la URL).

    Salida:
        str: pagina HTML de la vista usuarios/asignar_perfil.html con su codigo
        HTTP, o flask.Response: redireccion al detalle.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si el usuario no existe. Responde
        403 (werkzeug.exceptions.Forbidden) si el perfil no tiene el permiso;
        sin sesion redirige al login.
    """
    # Datos que usan el GET y el POST.
    usuario = _obtener_usuario_o_404(usuario_id)
    contexto = dict(
        usuario=usuario,
        perfiles=usuario_servicio.listar_perfiles(),
        permisos=perfil_servicio.listar_permisos_por_perfil(),
    )
    if request.method == "GET":
        return render_template(
            "usuarios/asignar_perfil.html",
            **contexto,
            seleccionado="",
            errores={},
        )

    # POST: HU-01-08 · Perfil sin seleccionar / inexistente regresan al
    # formulario.
    seleccionado = request.form.get("perfil_id", "")
    try:
        categoria, mensaje = usuario_servicio.asignar_perfil(
            usuario, seleccionado
        )
    except ErrorValidacion as error:
        return render_template(
            "usuarios/asignar_perfil.html",
            **contexto,
            seleccionado=seleccionado,
            errores=error.errores,
            error_general=error.mensaje,
        ), error.codigo

    # HU-01-08 · Asignar perfil / Modificar perfil de usuario.
    flash(mensaje, categoria)
    return redirect(url_for("usuarios.mostrar_detalle", usuario_id=usuario_id))
