"""Servicio de reportes: listado de libros en PDF (HU-01-16) e impresión (HU-01-17)."""
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


def consultar(filtros):
    """Libros que cumplen los filtros."""
    return libro_modelo.listar(
        campo=filtros["campo"], texto=filtros["q"], tema=filtros["tema"] or None,
        editorial=filtros["editorial"] or None, estado=filtros["estado"],
    )


def describir_filtros(filtros):
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
    return " · ".join(partes)


def opciones_filtros():
    """Temas y editoriales para los filtros del listado."""
    return {"temas": tema_modelo.listar_nombres(), "editoriales": editorial_modelo.listar_nombres()}


def generar_pdf(filtros, generado_por):
    """Genera el PDF con los libros filtrados. Regresa (bytes, total) o lanza ErrorValidacion."""
    libros = consultar(filtros)
    if not libros:
        raise ErrorValidacion("No existen registros disponibles para el listado. No se generó el documento.",
                              codigo=422)
    try:
        contenido = generar_listado(libros, describir_filtros(filtros), generado_por)
    except Exception as error:
        raise ErrorValidacion("El documento no pudo generarse. El listado sigue disponible para "
                              "intentarlo de nuevo.", codigo=500) from error
    return contenido, len(libros)


def enviar_a_impresion(filtros, impresora_id):
    """Simula el envío a impresión. Regresa ((tono, mensaje), código HTTP)."""
    libros = consultar(filtros)
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
