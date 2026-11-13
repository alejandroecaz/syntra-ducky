"""
============================================================
Archivo:      utils/open_library.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Consulta de los datos de un libro por su ISBN en la API publica de
    Open Library (openlibrary.org), para llenar la ficha bibliografica al
    dar de alta un libro (HU-01-09). No necesita llave ni cuenta.

    Primero se pide la edicion que corresponde al ISBN (titulo, autores,
    editorial y fecha de esa edicion). Como los datos de Open Library los
    edita la comunidad, si la edicion no trae autores se toman el titulo
    y los autores de la obra con la busqueda general, y se marca como
    incompleto para que el bibliotecario lo revise.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    13/11/2026
============================================================
"""

import json
from urllib import error as url_error
from urllib import parse, request

# Edicion del ISBN con los nombres de autores y editoriales.
URL_EDICION = "https://openlibrary.org/api/books?{parametros}"

# Busqueda general: datos de la obra (titulo y autores).
URL_BUSQUEDA = "https://openlibrary.org/search.json?{parametros}"

# Segundos que se espera a Open Library.
TIEMPO_ESPERA = 10

# Open Library pide que cada aplicacion se identifique.
AGENTE = "Syntra-Biblioteca-Ducky/1.0 (prototipo escolar)"


class ErrorConsulta(Exception):
    """Open Library no respondio o regreso algo que no se pudo leer."""


def _pedir_json(url):
    """
    Descripcion:
        Hace la peticion GET y regresa la respuesta como diccionario.

    Parametros:
        url (str): direccion completa.

    Salida:
        dict: respuesta de Open Library.

    Excepciones:
        ErrorConsulta si no hay conexion, tarda demasiado o la respuesta no
        es JSON.
    """
    peticion = request.Request(
        url, headers={"User-Agent": AGENTE, "Accept": "application/json"}
    )
    try:
        with request.urlopen(peticion, timeout=TIEMPO_ESPERA) as respuesta:
            return json.loads(respuesta.read().decode("utf-8"))
    except (url_error.URLError, TimeoutError, ValueError) as error:
        raise ErrorConsulta(
            "No se pudo consultar Open Library. Revisa la conexión a "
            "internet o captura los datos a mano."
        ) from error


def _limpiar(texto):
    """
    Descripcion:
        Quita espacios sobrantes de un texto de Open Library.

    Parametros:
        texto (str o None): texto.

    Salida:
        str: texto limpio o cadena vacia.
    """
    return " ".join((texto or "").split())


def _buscar_obra(isbn):
    """
    Descripcion:
        Busca la obra del ISBN con la busqueda general de Open Library.

    Parametros:
        isbn (str): ISBN de 10 o 13 digitos.

    Salida:
        dict con titulo y autores, o None si no la encuentra.
    """
    parametros = parse.urlencode(
        {"isbn": isbn, "fields": "title,author_name", "limit": 1}
    )
    obras = _pedir_json(URL_BUSQUEDA.format(parametros=parametros)).get("docs")
    if not obras or not obras[0].get("title"):
        return None
    return {
        "titulo": _limpiar(obras[0]["title"]),
        "autores": [_limpiar(a) for a in obras[0].get("author_name") or []],
    }


def buscar_por_isbn(isbn):
    """
    Descripcion:
        HU-01-09: Busca los datos del libro por su ISBN.

    Parametros:
        isbn (str): ISBN de 10 o 13 digitos, sin guiones.

    Salida:
        dict con titulo, subtitulo, autores (list), editorial, fecha (texto
        como lo da Open Library) y completo (False si se tuvo que completar
        con la obra), o None si Open Library no tiene ese ISBN.

    Excepciones:
        ErrorConsulta si Open Library no responde.
    """
    # Datos de la edicion de ese ISBN.
    llave = f"ISBN:{isbn}"
    parametros = parse.urlencode(
        {"bibkeys": llave, "format": "json", "jscmd": "data"}
    )
    edicion = _pedir_json(URL_EDICION.format(parametros=parametros)).get(llave)
    datos = None
    if edicion and edicion.get("title"):
        datos = {
            "titulo": _limpiar(edicion["title"]),
            "subtitulo": _limpiar(edicion.get("subtitle")),
            "autores": [
                _limpiar(autor.get("name"))
                for autor in edicion.get("authors") or []
                if autor.get("name")
            ],
            "editorial": next(
                (
                    _limpiar(editorial.get("name"))
                    for editorial in edicion.get("publishers") or []
                    if _limpiar(editorial.get("name"))
                ),
                "",
            ),
            "fecha": _limpiar(edicion.get("publish_date")),
            "completo": True,
        }
    if datos and datos["autores"]:
        return datos

    # Edicion sin autores (o sin edicion): no es confiable; usamos la obra.
    obra = _buscar_obra(isbn)
    if obra is None:
        if datos:
            datos["completo"] = False
        return datos
    return {
        "titulo": obra["titulo"],
        "subtitulo": "",
        "autores": obra["autores"],
        "editorial": "",
        "fecha": "",
        "completo": False,
    }
