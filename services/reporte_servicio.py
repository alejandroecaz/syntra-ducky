"""
============================================================
Archivo:      services/reporte_servicio.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Servicio de reportes: listado de libros en PDF (HU-01-16) e impresion
    (HU-01-17).

    El documento incluye los libros que cumplen los filtros; ademas el
    usuario puede elegir cuales de ellos entran (seleccion manual con
    casillas en el listado).

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

import config
from models import editorial as editorial_modelo
from models import libro as libro_modelo
from models import tema as tema_modelo
from services.errores import ErrorValidacion
from utils.pdf import generar_listado

# Texto de cada vista para el encabezado del documento.
DESCRIPCION_VISTA = {
    "activos": "Solo libros activos",
    "baja": "Solo dados de baja",
    "todos": "Activos y dados de baja",
}
MENSAJE_SIN_SELECCION = "Selecciona al menos un libro del listado."


def leer_filtros(origen, personal):
    """
    Descripcion:
        HU-01-16 y HU-01-17 · con filtros: lee los filtros de la peticion. Solo
        el personal puede incluir libros dados de baja.

    Parametros:
        origen (werkzeug.datastructures.MultiDict): parametros de la peticion.
        personal (bool): True si es personal de biblioteca.

    Salida:
        dict: campo, q, tema, editorial y estado.
    """
    # Leemos los filtros de la peticion con sus valores predeterminados.
    filtros = {
        "campo": origen.get("campo", config.CAMPO_BUSQUEDA_PREDETERMINADO),
        "q": (origen.get("q") or "").strip(),
        "tema": origen.get("tema", ""),
        "editorial": origen.get("editorial", ""),
        "estado": origen.get("estado", config.VISTAS_CATALOGO[0]),
    }

    # Quien no es personal (o manda una vista invalida) solo ve libros activos.
    if not personal or filtros["estado"] not in config.VISTAS_CATALOGO:
        filtros["estado"] = config.VISTAS_CATALOGO[0]
    return filtros


def leer_seleccion(origen):
    """
    Descripcion:
        Lee los ids de los libros elegidos con las casillas.

    Parametros:
        origen (werkzeug.datastructures.MultiDict): parametros de la peticion.

    Salida:
        set[int] o None si no hubo seleccion (entran todos).
    """
    if not origen.get("seleccion"):
        return None
    return {
        int(libro_id)
        for libro_id in origen.getlist("libro")
        if libro_id.isdigit()
    }


def obtener_parametros_seleccion(seleccion):
    """
    Descripcion:
        Arma los parametros de URL para conservar la seleccion al ir y volver
        entre pantallas.

    Parametros:
        seleccion (set[int] o None): ids elegidos.

    Salida:
        dict: parametros seleccion y libro, o vacio.
    """
    if seleccion is None:
        return {}
    return {"seleccion": 1, "libro": sorted(seleccion)}


def consultar(filtros, seleccion=None):
    """
    Descripcion:
        Consulta los libros que cumplen los filtros y, si hay seleccion, solo
        los elegidos.

    Parametros:
        filtros (dict): filtros leidos.
        seleccion (set[int] o None): ids elegidos.

    Salida:
        list[sqlite3.Row]: libros del documento.
    """
    # Libros que cumplen los filtros.
    libros = libro_modelo.listar(
        campo=filtros["campo"],
        texto=filtros["q"],
        tema=filtros["tema"] or None,
        editorial=filtros["editorial"] or None,
        estado=filtros["estado"],
    )

    # Si hubo seleccion con casillas, solo quedan los marcados.
    if seleccion is None:
        return libros
    return [libro for libro in libros if libro["id"] in seleccion]


def describir_filtros(filtros, seleccionados=None):
    """
    Descripcion:
        Arma el texto de los filtros aplicados para el encabezado del
        documento.

    Parametros:
        filtros (dict): filtros leidos.
        seleccionados (int o None): cuantos libros se eligieron a mano.

    Salida:
        str: filtros separados por ·.
    """
    # Agregamos una parte por cada filtro aplicado.
    partes = []
    if filtros["q"]:
        etiqueta = dict(config.CAMPOS_BUSQUEDA).get(filtros["campo"], "Texto")
        partes.append(f'{etiqueta} contiene "{filtros["q"]}"')
    if filtros["tema"]:
        partes.append(f"Tema: {filtros['tema']}")
    if filtros["editorial"]:
        partes.append(f"Editorial: {filtros['editorial']}")
    partes.append(DESCRIPCION_VISTA[filtros["estado"]])

    # Si hubo seleccion manual se dice cuantos libros se eligieron.
    if seleccionados is not None:
        plural = "" if seleccionados == 1 else "s"
        partes.append(f"{seleccionados} libro{plural} seleccionado{plural}")
    return " · ".join(partes)


def preparar_documento(origen, personal):
    """
    Descripcion:
        Junta filtros, seleccion y libros que entran al PDF o a la impresion.

    Parametros:
        origen (werkzeug.datastructures.MultiDict): parametros de la peticion.
        personal (bool): True si es personal de biblioteca.

    Salida:
        dict: filtros, seleccion, libros, filtros_texto y parametros para los
        enlaces.
    """
    # Leemos filtros y seleccion y consultamos los libros.
    filtros = leer_filtros(origen, personal)
    seleccion = leer_seleccion(origen)
    libros = consultar(filtros, seleccion)

    # Todo lo que necesitan la vista, el PDF y la impresion.
    return {
        "filtros": filtros,
        "seleccion": seleccion,
        "libros": libros,
        "filtros_texto": describir_filtros(
            filtros, len(libros) if seleccion is not None else None
        ),
        # Para los enlaces y formularios que deben conservar filtros y
        # seleccion.
        "parametros": {**filtros, **obtener_parametros_seleccion(seleccion)},
    }


def obtener_opciones_filtros():
    """
    Descripcion:
        Obtiene los temas y editoriales para los filtros del listado.

    Parametros:
        Ninguno.

    Salida:
        dict: temas y editoriales.
    """
    return {
        "temas": tema_modelo.listar_nombres(),
        "editoriales": editorial_modelo.listar_nombres(),
    }


def generar_pdf(documento, generado_por):
    """
    Descripcion:
        HU-01-16: Genera el PDF con los libros del documento.

    Parametros:
        documento (dict): documento de preparar_documento().
        generado_por (str): nombre de quien lo genera.

    Salida:
        tuple[bytes, int]: contenido del PDF y numero de registros.

    Excepciones:
        ErrorValidacion con codigo 422 si no hay libros o no se marco ninguno,
        y con codigo 500 si falla la generacion.
    """
    # Se eligio con casillas pero no se marco ningun libro.
    if documento["seleccion"] is not None and not documento["libros"]:
        raise ErrorValidacion(
            f"{MENSAJE_SIN_SELECCION} No se generó el documento.", codigo=422
        )

    # HU-01-16 · Catalogo sin registros.
    if not documento["libros"]:
        raise ErrorValidacion(
            "No existen registros disponibles para el listado. No se generó "
            "el documento.",
            codigo=422,
        )

    # HU-01-16 · Generacion satisfactoria / Error durante la generacion.
    try:
        contenido = generar_listado(
            documento["libros"], documento["filtros_texto"], generado_por
        )
    except Exception as error:
        raise ErrorValidacion(
            "El documento no pudo generarse. El listado sigue disponible para "
            "intentarlo de nuevo.",
            codigo=500,
        ) from error
    return contenido, len(documento["libros"])


def enviar_a_impresion(documento, impresora_id):
    """
    Descripcion:
        HU-01-17: Simula el envio del listado a impresion.

    Parametros:
        documento (dict): documento de preparar_documento().
        impresora_id (str): id de la impresora elegida.

    Salida:
        tuple[tuple[str, str], int]: (tono, mensaje) del aviso y codigo HTTP.
    """
    # Se eligio con casillas pero no se marco ningun libro, o no hay registros.
    libros = documento["libros"]
    if documento["seleccion"] is not None and not libros:
        return (
            "advertencia",
            f"{MENSAJE_SIN_SELECCION} No se envió nada a impresión.",
        ), 422
    if not libros:
        return (
            "advertencia",
            "No hay registros que imprimir con los filtros seleccionados.",
        ), 422

    # Buscamos la impresora elegida.
    impresora = next(
        (
            opcion
            for opcion in config.IMPRESORAS
            if opcion["id"] == impresora_id
        ),
        None,
    )
    if impresora is None:
        return (
            "error",
            "Selecciona una impresora para enviar el listado.",
        ), 400

    # HU-01-17 · Impresora no disponible.
    if not impresora["disponible"]:
        return (
            "error",
            "No fue posible enviar el documento a impresión: "
            f'"{impresora["nombre"]}" no está '
            "disponible. Selecciona otra impresora o cancela la operación.",
        ), 503

    # HU-01-17 · Impresion satisfactoria.
    return (
        "exito",
        f"Solicitud de impresión procesada: {len(libros)} registros enviados "
        "a "
        f'"{impresora["nombre"]}".',
    ), 200
