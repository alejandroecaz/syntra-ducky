"""
============================================================
Archivo:      tests/test_isbn.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Pruebas de la busqueda de datos por ISBN en Open Library para el alta
    de libros (HU-01-09).

    Ninguna prueba sale a internet: se reemplaza la peticion a Open
    Library por respuestas guardadas aqui.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    13/11/2026
============================================================
"""

from urllib import error as url_error

import pytest

from models.db import ejecutar
from tests.conftest import entrar
from utils import open_library

# Respuesta de la edicion de Codigo limpio (Anaya).
EDICION_CODIGO_LIMPIO = {
    "ISBN:9788441532106": {
        "title": "Código Limpio",
        "subtitle": "Manual de estilo para el desarrollo ágil de software",
        "authors": [{"name": "Robert C. Martin"}],
        "publishers": [{"name": " ANAYA MULTIMEDIA"}],
        "publish_date": "Jan 01, 2012",
    }
}

# Edicion editada con datos basura: sin autores.
EDICION_SIN_AUTORES = {
    "ISBN:9780262033848": {
        "title": "Fomo App Referral Code",
        "publishers": [{"name": "Fomo App Referral Code"}],
        "publish_date": "2026",
    }
}

# Busqueda general de la obra.
OBRA_CORMEN = {
    "docs": [
        {
            "title": "Introduction to Algorithms",
            "author_name": ["Thomas H. Cormen", "Charles E. Leiserson"],
        }
    ]
}


@pytest.fixture
def biblio(cliente):
    """
    Descripcion:
        Fixture: cliente con la sesion del bibliotecario iniciada.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba.

    Salida:
        flask.testing.FlaskClient: cliente con sesion.
    """
    entrar(cliente, "biblio", "Biblio123")
    return cliente


def simular_open_library(monkeypatch, edicion, busqueda=None):
    """
    Descripcion:
        Reemplaza la peticion a Open Library por respuestas fijas y guarda
        las direcciones que se pidieron.

    Parametros:
        monkeypatch (pytest.MonkeyPatch): reemplaza la funcion.
        edicion (dict): respuesta de la edicion.
        busqueda (dict o None): respuesta de la busqueda general.

    Salida:
        list[str]: direcciones pedidas.
    """
    pedidas = []

    def responder(url):
        pedidas.append(url)
        if "search.json" in url:
            return busqueda or {"docs": []}
        return edicion

    monkeypatch.setattr(open_library, "_pedir_json", responder)
    return pedidas


def test_formulario_de_alta_ofrece_buscar_por_isbn(biblio):
    """
    Descripcion:
        Prueba: HU-01-09 · El alta de libros tiene el boton Buscar por ISBN;
        la edicion no.

    Parametros:
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    alta = biblio.get("/catalogo/nuevo").get_data(as_text=True)
    assert "Buscar por ISBN" in alta
    assert 'data-buscar-isbn="/catalogo/isbn"' in alta
    edicion = biblio.get("/catalogo/1/editar").get_data(as_text=True)
    assert "data-buscar-isbn" not in edicion


def test_isbn_encontrado_llena_la_ficha(biblio, monkeypatch):
    """
    Descripcion:
        Prueba: HU-01-09 · ISBN encontrado (con guiones): regresa titulo con
        subtitulo, autores, editorial sin espacios y el ano de la fecha.

    Parametros:
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.
        monkeypatch (pytest.MonkeyPatch): simula Open Library.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    pedidas = simular_open_library(monkeypatch, EDICION_CODIGO_LIMPIO)
    respuesta = biblio.get("/catalogo/isbn?isbn=978-84-415-3210-6")
    assert respuesta.status_code == 200
    assert respuesta.json["tono"] == "exito"
    assert respuesta.json["datos"] == {
        "isbn": "9788441532106",
        "titulo": "Código Limpio: Manual de estilo para el desarrollo ágil "
        "de software",
        "autores": "Robert C. Martin",
        "editorial": "ANAYA MULTIMEDIA",
        "anio": "2012",
    }
    # Con autores en la edicion no hace falta la busqueda general.
    assert len(pedidas) == 1


def test_edicion_sin_autores_usa_la_obra(biblio, monkeypatch):
    """
    Descripcion:
        Prueba: HU-01-09 · Edicion con datos dudosos (sin autores): se toman
        titulo y autores de la obra y se avisa que hay que revisar.

    Parametros:
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.
        monkeypatch (pytest.MonkeyPatch): simula Open Library.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    simular_open_library(monkeypatch, EDICION_SIN_AUTORES, OBRA_CORMEN)
    respuesta = biblio.get("/catalogo/isbn?isbn=9780262033848")
    assert respuesta.status_code == 200
    assert respuesta.json["tono"] == "advertencia"
    assert respuesta.json["datos"]["titulo"] == "Introduction to Algorithms"
    assert respuesta.json["datos"]["autores"] == (
        "Thomas H. Cormen; Charles E. Leiserson"
    )
    assert respuesta.json["datos"]["editorial"] == ""


def test_isbn_que_open_library_no_tiene(biblio, monkeypatch):
    """
    Descripcion:
        Prueba: HU-01-09 · ISBN sin datos en Open Library: se pide capturar
        la ficha a mano.

    Parametros:
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.
        monkeypatch (pytest.MonkeyPatch): simula Open Library.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    simular_open_library(monkeypatch, {})
    respuesta = biblio.get("/catalogo/isbn?isbn=9780000000019")
    assert respuesta.status_code == 404
    assert "no tiene datos de ese ISBN" in respuesta.json["mensaje"]


@pytest.mark.parametrize("isbn", ["", "12345", "97884415321XX"])
def test_isbn_invalido_no_consulta(biblio, monkeypatch, isbn):
    """
    Descripcion:
        Prueba: HU-01-09 · ISBN con formato invalido: no se consulta Open
        Library.

    Parametros:
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.
        monkeypatch (pytest.MonkeyPatch): simula Open Library.
        isbn (str): ISBN capturado.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    pedidas = simular_open_library(monkeypatch, EDICION_CODIGO_LIMPIO)
    respuesta = biblio.get("/catalogo/isbn", query_string={"isbn": isbn})
    assert respuesta.status_code == 422
    assert respuesta.json["mensaje"] == "Escribe un ISBN de 10 o 13 dígitos."
    assert pedidas == []


def test_isbn_ya_registrado(app, biblio, monkeypatch):
    """
    Descripcion:
        Prueba: HU-01-09 · ISBN que ya tiene otro libro del catalogo: se
        avisa sin consultar Open Library.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.
        monkeypatch (pytest.MonkeyPatch): simula Open Library.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    with app.app_context():
        ejecutar(
            "UPDATE libros SET isbn = '9788441532106' WHERE clave = 'LIB-004'"
        )
    pedidas = simular_open_library(monkeypatch, EDICION_CODIGO_LIMPIO)
    respuesta = biblio.get("/catalogo/isbn?isbn=9788441532106")
    assert respuesta.status_code == 409
    assert "ya pertenece a un libro del catálogo" in respuesta.json["mensaje"]
    assert pedidas == []


def test_open_library_sin_conexion(biblio, monkeypatch):
    """
    Descripcion:
        Prueba: HU-01-09 · Sin internet o sin respuesta de Open Library: se
        avisa que se capture a mano.

    Parametros:
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.
        monkeypatch (pytest.MonkeyPatch): simula la falta de conexion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """

    def fallar(*_args, **_kwargs):
        raise url_error.URLError("sin conexion")

    monkeypatch.setattr(open_library.request, "urlopen", fallar)
    respuesta = biblio.get("/catalogo/isbn?isbn=9788441532106")
    assert respuesta.status_code == 502
    assert "No se pudo consultar Open Library" in respuesta.json["mensaje"]


def test_buscar_isbn_sin_permiso(cliente):
    """
    Descripcion:
        Prueba: Acceso sin autorizacion: el profesor no puede usar la
        busqueda por ISBN.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    entrar(cliente, "profesor", "Profe123")
    respuesta = cliente.get("/catalogo/isbn?isbn=9788441532106")
    assert respuesta.status_code == 403
