from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

import config
from models import libro as libro_modelo
from utils.seguridad import permiso_requerido, tiene_permiso

catalogo_bp = Blueprint("catalogo", __name__, url_prefix="/catalogo")

CAMPOS_LIBRO = ("clave", "titulo", "autor", "tema", "editorial")
ETIQUETAS_LIBRO = {
    "clave": "la clave",
    "titulo": "el título",
    "autor": "el autor",
    "tema": "el tema",
    "editorial": "la editorial",
}


def _es_personal():
    # Bibliotecario o admin (pueden ver los libros dados de baja)
    return tiene_permiso("libros.alta", "libros.editar", "libros.baja")


def _libro_o_404(libro_id, permitir_baja=False):
    libro = libro_modelo.obtener_por_id(libro_id)
    if libro is None or (not libro["activo"] and not permitir_baja):
        abort(404)
    return libro


def _validar_libro(form, exigir_clave):
    valores = {campo: form.get(campo, "").strip() for campo in CAMPOS_LIBRO + ("anio",)}
    errores = {}
    campos = CAMPOS_LIBRO if exigir_clave else CAMPOS_LIBRO[1:]
    for campo in campos:
        if not valores[campo]:
            errores[campo] = f"Captura {ETIQUETAS_LIBRO[campo]}."
    if valores["anio"]:
        if not valores["anio"].isdigit() or not 1400 <= int(valores["anio"]) <= date.today().year:
            errores["anio"] = f"Escribe un año entre 1400 y {date.today().year}."
    return valores, errores


def _validar_ejemplar(form):
    # La ubicacion va completa o vacia
    valores = {campo: form.get(campo, "").strip() for campo in ("estancia", "estante", "posicion", "estado")}
    errores = []
    ubicacion = [valores["estancia"], valores["estante"], valores["posicion"]]
    if any(ubicacion) and not all(ubicacion):
        errores.append("Completa estancia, estante y posición, o deja los tres vacíos si la ubicación está pendiente.")
    if valores["estado"] not in config.ESTADOS_EJEMPLAR:
        errores.append("Selecciona un estado válido para el ejemplar.")
    for campo in ("estancia", "estante", "posicion"):
        valores[campo] = valores[campo] or None
    return valores, errores


# HU-01-12 y HU-01-13: consulta y busqueda

@catalogo_bp.route("")
@permiso_requerido("catalogo.consultar")
def lista():
    campo = request.args.get("campo", "titulo")
    texto = request.args.get("q", "").strip()
    buscando = "buscar" in request.args
    vista = request.args.get("ver", "activos") if _es_personal() else "activos"
    if vista not in ("activos", "baja", "todos"):
        vista = "activos"

    error_busqueda = None
    if buscando and not texto:
        error_busqueda = "Captura un criterio de búsqueda."
        libros = []
    elif buscando:
        libros = libro_modelo.listar(campo=campo, texto=texto, estado=vista)
    else:
        libros = libro_modelo.listar(estado=vista)

    hay_catalogo = bool(libro_modelo.listar(estado="activos")) or vista != "activos"

    return render_template(
        "catalogo/lista.html",
        libros=libros,
        campo=campo,
        texto=texto,
        buscando=buscando,
        error_busqueda=error_busqueda,
        vista=vista,
        hay_catalogo=hay_catalogo,
        es_personal=_es_personal(),
        resaltar=request.args.get("resaltar", type=int),
    )


@catalogo_bp.route("/<int:libro_id>")
@permiso_requerido("catalogo.consultar")
def detalle(libro_id):
    libro = _libro_o_404(libro_id, permitir_baja=_es_personal())
    if request.args.get("cancelado"):
        flash("Se descartaron los cambios. El libro conserva sus datos anteriores.", "info")
        return redirect(url_for("catalogo.detalle", libro_id=libro_id))
    return render_template(
        "catalogo/detalle.html",
        libro=libro,
        ejemplares=libro_modelo.ejemplares_de(libro_id),
        operaciones=libro_modelo.operaciones_vigentes(libro_id),
        estados=config.ESTADOS_EJEMPLAR,
        estancias=config.ESTANCIAS,
        es_personal=_es_personal(),
    )


# HU-01-09: alta de libros

@catalogo_bp.route("/nuevo", methods=["GET", "POST"])
@permiso_requerido("libros.alta")
def nuevo():
    if request.method == "GET":
        return render_template("catalogo/form_libro.html", modo="nuevo", valores={}, errores={})

    valores, errores = _validar_libro(request.form, exigir_clave=True)
    clave_duplicada = bool(valores["clave"]) and libro_modelo.existe_clave(valores["clave"])
    if clave_duplicada:
        errores["clave"] = "La clave del libro ya existe"

    if errores:
        mensaje = ("La clave del libro ya existe. No se duplicó ni se sobrescribió el libro registrado."
                   if clave_duplicada else "Faltan datos bibliográficos obligatorios. El libro no se registró.")
        return render_template("catalogo/form_libro.html", modo="nuevo", valores=valores,
                               errores=errores, error_general=mensaje), 400

    libro_id = libro_modelo.crear(
        valores["clave"].upper(), valores["titulo"], valores["autor"], valores["tema"],
        valores["editorial"], int(valores["anio"]) if valores["anio"] else None,
    )
    flash(f"Libro registrado: {valores['titulo']} ({valores['clave'].upper()}). "
          "Aún no tiene ejemplares; agrégalos desde su ficha.", "success")
    return redirect(url_for("catalogo.detalle", libro_id=libro_id))


# HU-01-11: actualizar libros

@catalogo_bp.route("/<int:libro_id>/editar", methods=["GET", "POST"])
@permiso_requerido("libros.editar")
def editar(libro_id):
    libro = _libro_o_404(libro_id, permitir_baja=True)
    if request.method == "GET":
        valores = {campo: libro[campo] for campo in CAMPOS_LIBRO}
        valores["anio"] = libro["anio"] or ""
        return render_template("catalogo/form_libro.html", modo="editar", libro=libro, valores=valores, errores={})

    valores, errores = _validar_libro(request.form, exigir_clave=False)
    valores["clave"] = libro["clave"]
    if errores:
        return render_template("catalogo/form_libro.html", modo="editar", libro=libro, valores=valores,
                               errores=errores,
                               error_general="Faltan campos obligatorios. Se mantienen los datos guardados."), 400

    libro_modelo.actualizar(libro_id, valores["titulo"], valores["autor"], valores["tema"],
                            valores["editorial"], int(valores["anio"]) if valores["anio"] else None)
    flash("Libro actualizado correctamente. Su clave y sus ejemplares se conservan.", "success")
    return redirect(url_for("catalogo.detalle", libro_id=libro_id))


# HU-01-10: baja de libros

@catalogo_bp.route("/<int:libro_id>/baja", methods=["POST"])
@permiso_requerido("libros.baja")
def baja(libro_id):
    libro = _libro_o_404(libro_id, permitir_baja=True)
    if not libro["activo"]:
        flash("El libro ya estaba dado de baja.", "info")
        return redirect(url_for("catalogo.detalle", libro_id=libro_id))

    vigentes = libro_modelo.operaciones_vigentes(libro_id)
    if vigentes:
        detalle_ops = ", ".join(f"{op['codigo']} ({op['estado'].lower()})" for op in vigentes)
        flash(f"No se puede dar de baja: existen operaciones vigentes en {detalle_ops}. "
              "El libro y sus ejemplares no cambiaron.", "error")
        return redirect(url_for("catalogo.detalle", libro_id=libro_id))

    libro_modelo.dar_baja(libro_id)
    flash(f"\"{libro['titulo']}\" fue dado de baja. Ya no aparece en el catálogo de usuarios y su "
          "información se conserva para consulta administrativa.", "success")
    return redirect(url_for("catalogo.lista"))


# HU-01-14 y HU-01-15: ejemplares

@catalogo_bp.route("/<int:libro_id>/ejemplares", methods=["POST"])
@permiso_requerido("libros.editar")
def agregar_ejemplar(libro_id):
    _libro_o_404(libro_id)
    valores, errores = _validar_ejemplar(request.form)
    if errores:
        flash(" ".join(errores) + " No se agregó el ejemplar.", "error")
    else:
        codigo = libro_modelo.agregar_ejemplar(libro_id, valores["estancia"], valores["estante"],
                                               valores["posicion"], valores["estado"])
        flash(f"Ejemplar {codigo} agregado como {valores['estado']}.", "success")
    return redirect(url_for("catalogo.detalle", libro_id=libro_id))


@catalogo_bp.route("/ejemplares/<int:ejemplar_id>", methods=["POST"])
@permiso_requerido("libros.editar")
def actualizar_ejemplar(ejemplar_id):
    ejemplar = libro_modelo.obtener_ejemplar(ejemplar_id)
    if ejemplar is None:
        abort(404)
    valores, errores = _validar_ejemplar(request.form)
    if errores:
        flash(" ".join(errores) + " El ejemplar conserva sus datos.", "error")
    else:
        libro_modelo.actualizar_ejemplar(ejemplar_id, valores["estancia"], valores["estante"],
                                         valores["posicion"], valores["estado"])
        flash(f"Ejemplar {ejemplar['codigo']} actualizado: {valores['estado']}.", "success")
    return redirect(url_for("catalogo.detalle", libro_id=ejemplar["libro_id"]))
