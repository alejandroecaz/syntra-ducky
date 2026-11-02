"""
============================================================
Archivo:      controllers/catalogo_controller.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Controlador del catalogo web: consulta, busqueda, ficha, libros y
    ejemplares (HU-01-09 a HU-01-15).

    Papel en MVC: lee la peticion, llama a services/catalogo_servicio.py y
    regresa la vista de views/catalogo/. No tiene SQL ni reglas de
    negocio.

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

import config
from services import catalogo_servicio
from services.errores import ErrorValidacion
from utils.seguridad import permiso_requerido

# Blueprint para las rutas del catalogo.
catalogo_bp = Blueprint("catalogo", __name__, url_prefix="/catalogo")


def _verificar_personal():
    """
    Descripcion:
        Revisa si el perfil en sesion es personal de biblioteca (puede ver
        libros dados de baja).

    Parametros:
        Ninguno.

    Salida:
        bool: True si es personal.
    """
    return catalogo_servicio.verificar_personal(session.get("permisos", []))


def _obtener_libro_o_404(libro_id, permitir_baja=False):
    """
    Descripcion:
        Busca el libro o responde 404 si no existe.

    Parametros:
        libro_id (int): id del libro (viene en la URL).
        permitir_baja (bool): True para incluir libros dados de baja.

    Salida:
        sqlite3.Row: el libro.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si el libro no existe.
    """
    libro = catalogo_servicio.obtener_libro(libro_id, permitir_baja)
    if libro is None:
        abort(404)
    return libro


def _mostrar_formulario_libro(
    modo, valores, errores, libro=None, error_general=None, codigo=200
):
    """
    Descripcion:
        Pinta el formulario de libro en modo nuevo o editar con sus listas de
        opciones.

    Parametros:
        modo (str): 'nuevo' o 'editar'.
        valores (dict): valores de los campos.
        errores (dict): errores por campo.
        libro (sqlite3.Row o None): libro que se edita.
        error_general (str o None): mensaje del aviso.
        codigo (int): codigo HTTP de la respuesta.

    Salida:
        tuple[str, int]: pagina HTML y codigo HTTP.
    """
    return render_template(
        "catalogo/form_libro.html",
        modo=modo,
        libro=libro,
        valores=valores,
        errores=errores,
        error_general=error_general,
        **catalogo_servicio.obtener_opciones_libro(),
    ), codigo


# ============================================================
# CONSULTA Y BUSQUEDA (HU-01-12 Y HU-01-13)
# Muestran el catalogo, los resultados de busqueda y la ficha del libro.
# ============================================================


@catalogo_bp.route("")
@permiso_requerido("catalogo.consultar")
def listar():
    """
    Descripcion:
        HU-01-12 y HU-01-13: Muestra el catalogo completo o los resultados de
        la busqueda por filtros. Solo el personal puede elegir la vista de
        dados de baja.

    Parametros:
        Ninguno.

    Salida:
        str: pagina HTML de la vista catalogo/lista.html.

    Excepciones:
        Responde 403 (werkzeug.exceptions.Forbidden) si el perfil no tiene el
        permiso; sin sesion redirige al login.
    """
    # Solo el personal puede elegir la vista de dados de baja.
    personal = _verificar_personal()
    vista = catalogo_servicio.obtener_vista_permitida(
        request.args.get("ver", "activos"), personal
    )
    buscando = "buscar" in request.args

    # HU-01-13: con busqueda se filtra; HU-01-12: sin busqueda se muestra todo
    # el catalogo.
    if buscando:
        busqueda = catalogo_servicio.buscar_libros(
            request.args.get("campo"), request.args.get("q"), vista
        )
    else:
        busqueda = {
            "campo": catalogo_servicio.validar_campo(
                request.args.get("campo")
            ),
            "texto": "",
            "libros": catalogo_servicio.listar_catalogo(vista),
            "error": None,
        }

    # Mandamos todo a la vista.
    return render_template(
        "catalogo/lista.html",
        libros=busqueda["libros"],
        campo=busqueda["campo"],
        texto=busqueda["texto"],
        buscando=buscando,
        error_busqueda=busqueda["error"],
        vista=vista,
        hay_catalogo=catalogo_servicio.verificar_catalogo(vista),
        es_personal=personal,
        resaltar=request.args.get("resaltar", type=int),
    )


@catalogo_bp.route("/<int:libro_id>")
@permiso_requerido("catalogo.consultar")
def mostrar_detalle(libro_id):
    """
    Descripcion:
        HU-01-12 · Abrir detalle de libro, con su ubicacion (HU-01-14) y
        disponibilidad (HU-01-15).

    Parametros:
        libro_id (int): id del libro (viene en la URL).

    Salida:
        str: pagina HTML de la vista catalogo/detalle.html, o flask.Response:
        redireccion si se cancelo una edicion.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si el libro no existe. Responde 403
        (werkzeug.exceptions.Forbidden) si el perfil no tiene el permiso; sin
        sesion redirige al login.
    """
    # Buscamos la ficha; si no existe respondemos 404.
    ficha = catalogo_servicio.obtener_ficha(
        libro_id, permitir_baja=_verificar_personal()
    )
    if ficha is None:
        abort(404)

    # HU-01-11 · Cancelar edicion: avisamos y limpiamos la URL.
    if request.args.get("cancelado"):
        flash(
            "Se descartaron los cambios. El libro conserva sus datos "
            "anteriores.",
            "informacion",
        )
        return redirect(url_for("catalogo.mostrar_detalle", libro_id=libro_id))

    # Pintamos la ficha con los formularios de ejemplares.
    return render_template(
        "catalogo/detalle.html",
        **ficha,
        es_personal=_verificar_personal(),
        **catalogo_servicio.obtener_opciones_ejemplar(),
    )


# ============================================================
# ALTA DE LIBROS (HU-01-09)
# Formulario de alta y registro de un libro nuevo.
# ============================================================


@catalogo_bp.route("/nuevo", methods=["GET", "POST"])
@permiso_requerido("libros.alta")
def registrar():
    """
    Descripcion:
        HU-01-09: Muestra el formulario de alta (GET) y registra el libro
        (POST).

    Parametros:
        Ninguno.

    Salida:
        str: pagina HTML de la vista del formulario con su codigo HTTP, o
        flask.Response: redireccion a la ficha del libro nuevo.

    Excepciones:
        Responde 403 (werkzeug.exceptions.Forbidden) si el perfil no tiene el
        permiso; sin sesion redirige al login.
    """
    # GET: formulario vacio con el tipo de acceso predeterminado.
    if request.method == "GET":
        return _mostrar_formulario_libro(
            "nuevo", {"tipo_acceso": config.TIPOS_ACCESO[0]}, {}
        )

    # POST: si no pasa la validacion regresamos al formulario con lo capturado.
    try:
        libro_id, mensaje = catalogo_servicio.registrar_libro(request.form)
    except ErrorValidacion as error:
        return _mostrar_formulario_libro(
            "nuevo",
            error.valores,
            error.errores,
            error_general=error.mensaje,
            codigo=error.codigo,
        )

    # HU-01-09 · Alta exitosa: vamos a la ficha del libro nuevo.
    flash(mensaje, "exito")
    return redirect(url_for("catalogo.mostrar_detalle", libro_id=libro_id))


# ============================================================
# ACTUALIZACION DE LIBROS (HU-01-11)
# Carga los datos del libro y guarda la correccion.
# ============================================================


@catalogo_bp.route("/<int:libro_id>/editar", methods=["GET", "POST"])
@permiso_requerido("libros.editar")
def editar(libro_id):
    """
    Descripcion:
        HU-01-11: Carga el formulario con los datos del libro (GET) y guarda la
        correccion (POST).

    Parametros:
        libro_id (int): id del libro (viene en la URL).

    Salida:
        str: pagina HTML de la vista del formulario con su codigo HTTP, o
        flask.Response: redireccion a la ficha.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si el libro no existe. Responde 403
        (werkzeug.exceptions.Forbidden) si el perfil no tiene el permiso; sin
        sesion redirige al login.
    """
    # GET: formulario con los datos actuales.
    libro = _obtener_libro_o_404(libro_id, permitir_baja=True)
    if request.method == "GET":
        return _mostrar_formulario_libro(
            "editar",
            catalogo_servicio.obtener_valores_edicion(libro),
            {},
            libro=libro,
        )

    # POST: HU-01-11 · Edicion incompleta regresa al formulario sin guardar.
    try:
        mensaje = catalogo_servicio.actualizar_libro(libro, request.form)
    except ErrorValidacion as error:
        return _mostrar_formulario_libro(
            "editar",
            error.valores,
            error.errores,
            libro=libro,
            error_general=error.mensaje,
            codigo=error.codigo,
        )

    # HU-01-11 · Correccion exitosa: volvemos a la ficha.
    flash(mensaje, "exito")
    return redirect(url_for("catalogo.mostrar_detalle", libro_id=libro_id))


# ============================================================
# BAJA DE LIBROS (HU-01-10)
# Baja logica del libro confirmada desde un modal.
# ============================================================


@catalogo_bp.route("/<int:libro_id>/baja", methods=["POST"])
@permiso_requerido("libros.baja")
def dar_baja(libro_id):
    """
    Descripcion:
        HU-01-10: Da de baja el libro; la confirmacion se hace en un modal de
        la ficha.

    Parametros:
        libro_id (int): id del libro (viene en la URL).

    Salida:
        flask.Response: redireccion al catalogo si se dio de baja, o a la ficha
        si no se pudo.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si el libro no existe. Responde 403
        (werkzeug.exceptions.Forbidden) si el perfil no tiene el permiso; sin
        sesion redirige al login.
    """
    # El servicio decide si se puede dar de baja.
    libro = _obtener_libro_o_404(libro_id, permitir_baja=True)
    dado_de_baja, categoria, mensaje = catalogo_servicio.dar_baja(libro)
    flash(mensaje, categoria)

    # Si se dio de baja vamos al catalogo; si no, nos quedamos en la ficha.
    if dado_de_baja:
        return redirect(url_for("catalogo.listar"))
    return redirect(url_for("catalogo.mostrar_detalle", libro_id=libro_id))


# ============================================================
# EJEMPLARES (HU-01-14 Y HU-01-15)
# Agregan ejemplares y cambian su ubicacion y estado.
# ============================================================


@catalogo_bp.route("/<int:libro_id>/ejemplares", methods=["POST"])
@permiso_requerido("libros.editar")
def agregar_ejemplar(libro_id):
    """
    Descripcion:
        HU-01-14 y HU-01-15: Agrega un ejemplar al libro con su ubicacion y
        estado.

    Parametros:
        libro_id (int): id del libro (viene en la URL).

    Salida:
        flask.Response: redireccion a la ficha del libro.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si el libro no existe. Responde 403
        (werkzeug.exceptions.Forbidden) si el perfil no tiene el permiso; sin
        sesion redirige al login.
    """
    _obtener_libro_o_404(libro_id)
    categoria, mensaje = catalogo_servicio.agregar_ejemplar(
        libro_id, request.form
    )
    flash(mensaje, categoria)
    return redirect(url_for("catalogo.mostrar_detalle", libro_id=libro_id))


@catalogo_bp.route("/ejemplares/<int:ejemplar_id>", methods=["POST"])
@permiso_requerido("libros.editar")
def actualizar_ejemplar(ejemplar_id):
    """
    Descripcion:
        HU-01-15 · Disponibilidad actualizada: cambia la ubicacion y el estado
        de un ejemplar.

    Parametros:
        ejemplar_id (int): id del ejemplar (viene en la URL).

    Salida:
        flask.Response: redireccion a la ficha del libro.

    Excepciones:
        werkzeug.exceptions.NotFound (404) si el ejemplar no existe. Responde
        403 (werkzeug.exceptions.Forbidden) si el perfil no tiene el permiso;
        sin sesion redirige al login.
    """
    # Buscamos el ejemplar; si no existe respondemos 404.
    ejemplar = catalogo_servicio.obtener_ejemplar(ejemplar_id)
    if ejemplar is None:
        abort(404)

    # Guardamos el cambio y volvemos a la ficha del libro.
    categoria, mensaje = catalogo_servicio.actualizar_ejemplar(
        ejemplar, request.form
    )
    flash(mensaje, categoria)
    return redirect(
        url_for("catalogo.mostrar_detalle", libro_id=ejemplar["libro_id"])
    )
