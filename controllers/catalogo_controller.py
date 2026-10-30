# ============================================================
# Archivo: controllers/catalogo_controller.py
# Proyecto: Sistema Ducky de Gestión Bibliotecaria
# Syntra Technologies - Equipo 1 - Sprint 1
# Materia: Ingeniería de Software
# Autores:
#   - Melissa Silva Vázquez                #624352
#   - Tomás Zapata Pérez                   #629048
#   - Alejandro Evaristo Cazares Escobedo  #626337
# Descripción: Controlador del catálogo web: consulta, búsqueda, ficha, libros y ejemplares (HU-01-09 a
#              HU-01-15).
# ============================================================
"""Controlador del catálogo web: consulta, búsqueda, ficha, libros y ejemplares (HU-01-09 a HU-01-15).

Papel en MVC: lee la petición, llama a services/catalogo_servicio.py y regresa la vista
de views/catalogo/. No tiene SQL ni reglas de negocio.
"""
from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

import config
from services import catalogo_servicio
from services.errores import ErrorValidacion
from utils.seguridad import permiso_requerido

# Blueprint para las rutas del catálogo
catalogo_bp = Blueprint("catalogo", __name__, url_prefix="/catalogo")


def _es_personal():
    """True si el perfil en sesión es personal de biblioteca (puede ver libros dados de baja)."""
    return catalogo_servicio.es_personal(session.get("permisos", []))


def _libro_o_404(libro_id, permitir_baja=False):
    """El libro o responde 404 si no existe."""
    libro = catalogo_servicio.obtener_libro(libro_id, permitir_baja)
    if libro is None:
        abort(404)
    return libro


def _form_libro(modo, valores, errores, libro=None, error_general=None, codigo=200):
    """Pinta el formulario de libro en modo "nuevo" o "editar" con sus listas de opciones."""
    return render_template(
        "catalogo/form_libro.html", modo=modo, libro=libro, valores=valores, errores=errores,
        error_general=error_general, **catalogo_servicio.opciones_libro(),
    ), codigo


# HU-01-12 y HU-01-13: consulta y búsqueda

@catalogo_bp.route("")
@permiso_requerido("catalogo.consultar")
def lista():
    """HU-01-12 y HU-01-13: Muestra el catálogo o los resultados de la búsqueda por filtros."""
    # Solo el personal puede elegir la vista de dados de baja
    personal = _es_personal()
    vista = catalogo_servicio.vista_permitida(request.args.get("ver", "activos"), personal)
    buscando = "buscar" in request.args

    # HU-01-13: con búsqueda se filtra; HU-01-12: sin búsqueda se muestra todo el catálogo
    if buscando:
        busqueda = catalogo_servicio.buscar_libros(request.args.get("campo"), request.args.get("q"), vista)
    else:
        busqueda = {"campo": catalogo_servicio.campo_valido(request.args.get("campo")), "texto": "",
                    "libros": catalogo_servicio.listar_catalogo(vista), "error": None}

    # Mandamos todo a la vista
    return render_template(
        "catalogo/lista.html",
        libros=busqueda["libros"],
        campo=busqueda["campo"],
        texto=busqueda["texto"],
        buscando=buscando,
        error_busqueda=busqueda["error"],
        vista=vista,
        hay_catalogo=catalogo_servicio.hay_catalogo(vista),
        es_personal=personal,
        resaltar=request.args.get("resaltar", type=int),
    )


@catalogo_bp.route("/<int:libro_id>")
@permiso_requerido("catalogo.consultar")
def detalle(libro_id):
    """HU-01-12 · Abrir detalle de libro, con ubicación (HU-01-14) y disponibilidad (HU-01-15)."""
    # Buscamos la ficha; si no existe respondemos 404
    ficha = catalogo_servicio.ficha(libro_id, permitir_baja=_es_personal())
    if ficha is None:
        abort(404)

    # HU-01-11 · Cancelar edición: avisamos y limpiamos la URL
    if request.args.get("cancelado"):
        flash("Se descartaron los cambios. El libro conserva sus datos anteriores.", "info")
        return redirect(url_for("catalogo.detalle", libro_id=libro_id))

    # Pintamos la ficha con los formularios de ejemplares
    return render_template("catalogo/detalle.html", **ficha, es_personal=_es_personal(),
                           **catalogo_servicio.opciones_ejemplar())


# HU-01-09: alta de libros

@catalogo_bp.route("/nuevo", methods=["GET", "POST"])
@permiso_requerido("libros.alta")
def nuevo():
    """HU-01-09: Muestra el formulario de alta y registra el libro."""
    # GET: formulario vacío con el tipo de acceso predeterminado
    if request.method == "GET":
        return _form_libro("nuevo", {"tipo_acceso": config.TIPOS_ACCESO[0]}, {})

    # POST: si no pasa la validación regresamos al formulario con lo capturado
    try:
        libro_id, mensaje = catalogo_servicio.registrar_libro(request.form)
    except ErrorValidacion as error:
        return _form_libro("nuevo", error.valores, error.errores, error_general=error.mensaje, codigo=error.codigo)

    # HU-01-09 · Alta exitosa: vamos a la ficha del libro nuevo
    flash(mensaje, "success")
    return redirect(url_for("catalogo.detalle", libro_id=libro_id))


# HU-01-11: actualizar libros

@catalogo_bp.route("/<int:libro_id>/editar", methods=["GET", "POST"])
@permiso_requerido("libros.editar")
def editar(libro_id):
    """HU-01-11: Carga el formulario con los datos del libro y guarda la corrección."""
    # GET: formulario con los datos actuales
    libro = _libro_o_404(libro_id, permitir_baja=True)
    if request.method == "GET":
        return _form_libro("editar", catalogo_servicio.valores_edicion(libro), {}, libro=libro)

    # POST: HU-01-11 · Edición incompleta regresa al formulario sin guardar
    try:
        mensaje = catalogo_servicio.actualizar_libro(libro, request.form)
    except ErrorValidacion as error:
        return _form_libro("editar", error.valores, error.errores, libro=libro, error_general=error.mensaje,
                           codigo=error.codigo)

    # HU-01-11 · Corrección exitosa: volvemos a la ficha
    flash(mensaje, "success")
    return redirect(url_for("catalogo.detalle", libro_id=libro_id))


# HU-01-10: baja de libros

@catalogo_bp.route("/<int:libro_id>/baja", methods=["POST"])
@permiso_requerido("libros.baja")
def baja(libro_id):
    """HU-01-10: Da de baja el libro (la confirmación se hace en un modal de la ficha)."""
    # El servicio decide si se puede dar de baja
    libro = _libro_o_404(libro_id, permitir_baja=True)
    dado_de_baja, categoria, mensaje = catalogo_servicio.dar_baja(libro)
    flash(mensaje, categoria)

    # Si se dio de baja vamos al catálogo; si no, nos quedamos en la ficha
    if dado_de_baja:
        return redirect(url_for("catalogo.lista"))
    return redirect(url_for("catalogo.detalle", libro_id=libro_id))


# HU-01-14 y HU-01-15: ejemplares

@catalogo_bp.route("/<int:libro_id>/ejemplares", methods=["POST"])
@permiso_requerido("libros.editar")
def agregar_ejemplar(libro_id):
    """HU-01-14 y HU-01-15: Agrega un ejemplar con su ubicación y estado."""
    _libro_o_404(libro_id)
    categoria, mensaje = catalogo_servicio.agregar_ejemplar(libro_id, request.form)
    flash(mensaje, categoria)
    return redirect(url_for("catalogo.detalle", libro_id=libro_id))


@catalogo_bp.route("/ejemplares/<int:ejemplar_id>", methods=["POST"])
@permiso_requerido("libros.editar")
def actualizar_ejemplar(ejemplar_id):
    """HU-01-15 · Disponibilidad actualizada: cambia ubicación y estado de un ejemplar."""
    # Buscamos el ejemplar; si no existe respondemos 404
    ejemplar = catalogo_servicio.obtener_ejemplar(ejemplar_id)
    if ejemplar is None:
        abort(404)

    # Guardamos el cambio y volvemos a la ficha del libro
    categoria, mensaje = catalogo_servicio.actualizar_ejemplar(ejemplar, request.form)
    flash(mensaje, categoria)
    return redirect(url_for("catalogo.detalle", libro_id=ejemplar["libro_id"]))
