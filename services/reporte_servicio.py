"""Servicio de reportes: listado de libros en PDF (HU-01-16) e impresión (HU-01-17).

El documento incluye los libros que cumplen los filtros; además el usuario puede elegir
cuáles de ellos entran (selección manual con casillas en el listado).
"""
import config
from models import editorial as editorial_modelo
from models import libro as libro_modelo
from models import tema as tema_modelo
from services.errores import ErrorValidacion
from utils.pdf import generar_listado

DESCRIPCION_VISTA = {
    "activos": "Solo libros activos",
    "baja": "Solo dados de baja",
    "todos": "Activos y dados de baja",
}
MENSAJE_SIN_SELECCION = "Selecciona al menos un libro del listado."


def leer_filtros(origen, personal):
    """Filtros del listado. Solo el personal puede incluir libros dados de baja."""
    filtros = {
        "campo": origen.get("campo", config.CAMPO_BUSQUEDA_PREDETERMINADO),
        "q": (origen.get("q") or "").strip(),
        "tema": origen.get("tema", ""),
        "editorial": origen.get("editorial", ""),
        "estado": origen.get("estado", config.VISTAS_CATALOGO[0]),
    }
    if not personal or filtros["estado"] not in config.VISTAS_CATALOGO:
        filtros["estado"] = config.VISTAS_CATALOGO[0]
    return filtros


def leer_seleccion(origen):
    """Ids de los libros elegidos con las casillas, o None si no hubo selección (entran todos)."""
    if not origen.get("seleccion"):
        return None
    return {int(libro_id) for libro_id in origen.getlist("libro") if libro_id.isdigit()}


def parametros_seleccion(seleccion):
    """Parámetros de URL para conservar la selección al ir y volver entre pantallas."""
    if seleccion is None:
        return {}
    return {"seleccion": 1, "libro": sorted(seleccion)}


def consultar(filtros, seleccion=None):
    """Libros que cumplen los filtros y, si hay selección, solo los elegidos."""
    libros = libro_modelo.listar(
        campo=filtros["campo"], texto=filtros["q"], tema=filtros["tema"] or None,
        editorial=filtros["editorial"] or None, estado=filtros["estado"],
    )
    if seleccion is None:
        return libros
    return [libro for libro in libros if libro["id"] in seleccion]


def describir_filtros(filtros, seleccionados=None):
    """Texto de los filtros aplicados para el encabezado del documento."""
    partes = []
    if filtros["q"]:
        etiqueta = dict(config.CAMPOS_BUSQUEDA).get(filtros["campo"], "Texto")
        partes.append(f"{etiqueta} contiene \"{filtros['q']}\"")
    if filtros["tema"]:
        partes.append(f"Tema: {filtros['tema']}")
    if filtros["editorial"]:
        partes.append(f"Editorial: {filtros['editorial']}")
    partes.append(DESCRIPCION_VISTA[filtros["estado"]])
    if seleccionados is not None:
        plural = "" if seleccionados == 1 else "s"
        partes.append(f"{seleccionados} libro{plural} seleccionado{plural}")
    return " · ".join(partes)


def preparar_documento(origen, personal):
    """Filtros, selección y libros que entran al PDF o a la impresión."""
    filtros = leer_filtros(origen, personal)
    seleccion = leer_seleccion(origen)
    libros = consultar(filtros, seleccion)
    return {
        "filtros": filtros,
        "seleccion": seleccion,
        "libros": libros,
        "filtros_texto": describir_filtros(filtros, len(libros) if seleccion is not None else None),
        # Para los enlaces y formularios que deben conservar filtros y selección
        "parametros": {**filtros, **parametros_seleccion(seleccion)},
    }


def opciones_filtros():
    """Temas y editoriales para los filtros del listado."""
    return {"temas": tema_modelo.listar_nombres(), "editoriales": editorial_modelo.listar_nombres()}


def generar_pdf(documento, generado_por):
    """Genera el PDF con los libros del documento. Regresa (bytes, total) o lanza ErrorValidacion."""
    if documento["seleccion"] is not None and not documento["libros"]:
        raise ErrorValidacion(f"{MENSAJE_SIN_SELECCION} No se generó el documento.", codigo=422)
    if not documento["libros"]:
        raise ErrorValidacion("No existen registros disponibles para el listado. No se generó el documento.",
                              codigo=422)
    try:
        contenido = generar_listado(documento["libros"], documento["filtros_texto"], generado_por)
    except Exception as error:
        raise ErrorValidacion("El documento no pudo generarse. El listado sigue disponible para "
                              "intentarlo de nuevo.", codigo=500) from error
    return contenido, len(documento["libros"])


def enviar_a_impresion(documento, impresora_id):
    """Simula el envío a impresión. Regresa ((tono, mensaje), código HTTP)."""
    libros = documento["libros"]
    if documento["seleccion"] is not None and not libros:
        return ("warning", f"{MENSAJE_SIN_SELECCION} No se envió nada a impresión."), 422
    if not libros:
        return ("warning", "No hay registros que imprimir con los filtros seleccionados."), 422

    impresora = next((i for i in config.IMPRESORAS if i["id"] == impresora_id), None)
    if impresora is None:
        return ("error", "Selecciona una impresora para enviar el listado."), 400

    if not impresora["disponible"]:
        return ("error", f"No fue posible enviar el documento a impresión: \"{impresora['nombre']}\" no está "
                         "disponible. Selecciona otra impresora o cancela la operación."), 503

    return ("success", f"Solicitud de impresión procesada: {len(libros)} registros enviados a "
                       f"\"{impresora['nombre']}\"."), 200
