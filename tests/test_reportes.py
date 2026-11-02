"""
============================================================
Archivo:      tests/test_reportes.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Listado de libros: PDF (HU-01-16) e impresion (HU-01-17) solo con los
    libros marcados.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

import re

import pytest

from tests.conftest import entrar, obtener_id_libro


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


def marcar_libros(app, *claves):
    """
    Descripcion:
        Arma los parametros que manda el listado cuando el usuario marca esos
        libros.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        *claves (str): claves de los libros marcados.

    Salida:
        dict: parametros seleccion y libro.
    """
    return {
        "seleccion": "1",
        "libro": [str(obtener_id_libro(app, clave)) for clave in claves],
    }


def contar_casillas_marcadas(contenido_html):
    """
    Descripcion:
        Cuenta las casillas marcadas en el HTML del listado.

    Parametros:
        contenido_html (str): HTML de la respuesta.

    Salida:
        int: numero de casillas marcadas.
    """
    return len(
        re.findall(r"data-seleccion-libro[^>]*checked>", contenido_html)
    )


def test_listado_muestra_todos_marcados(biblio):
    """
    Descripcion:
        Prueba: HU-01-16 y HU-01-17: al abrir el listado todos los libros
        vienen marcados.

    Parametros:
        biblio (flask.testing.FlaskClient): cliente con sesion de
            bibliotecario.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    contenido_html = biblio.get("/reportes/libros").get_data(as_text=True)
    assert contenido_html.count("data-seleccion-libro") == 15
    assert contar_casillas_marcadas(contenido_html) == 15


def test_listado_conserva_la_seleccion_al_regresar(app, biblio):
    """
    Descripcion:
        Prueba: La seleccion de libros se conserva al regresar al listado.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente con sesion de
            bibliotecario.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    contenido_html = biblio.get(
        "/reportes/libros", query_string=marcar_libros(app, "LIB-001")
    ).get_data(as_text=True)
    assert contar_casillas_marcadas(contenido_html) == 1


def test_pdf_solo_con_libros_marcados(app, biblio):
    """
    Descripcion:
        Prueba: HU-01-16 · Generacion del PDF con filtros: solo entran los
        libros marcados.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente con sesion de
            bibliotecario.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = biblio.get(
        "/reportes/libros/pdf",
        query_string=marcar_libros(app, "LIB-001", "LIB-002"),
    )
    assert respuesta.mimetype == "application/pdf"
    assert respuesta.headers["X-Total-Registros"] == "2"


def test_pdf_sin_seleccion_incluye_todos_los_filtrados(biblio):
    """
    Descripcion:
        Prueba: HU-01-16 · Generacion satisfactoria del PDF con todos los
        libros filtrados.

    Parametros:
        biblio (flask.testing.FlaskClient): cliente con sesion de
            bibliotecario.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = biblio.get("/reportes/libros/pdf?campo=tema&q=programacion")
    assert respuesta.headers["X-Total-Registros"] == "3"


def test_seleccion_respeta_los_filtros(app, biblio):
    """
    Descripcion:
        Prueba: HU-01-16: la seleccion no puede meter libros que no cumplen los
        filtros.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente con sesion de
            bibliotecario.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    parametros = {
        "campo": "autor",
        "q": "garcia",
        **marcar_libros(app, "LIB-001", "LIB-002"),
    }
    respuesta = biblio.get("/reportes/libros/pdf", query_string=parametros)
    assert respuesta.headers["X-Total-Registros"] == "1"


def test_pdf_sin_libros_marcados(biblio):
    """
    Descripcion:
        Prueba: HU-01-16: sin libros marcados no se genera el PDF.

    Parametros:
        biblio (flask.testing.FlaskClient): cliente con sesion de
            bibliotecario.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = biblio.get(
        "/reportes/libros/pdf",
        query_string={"seleccion": "1"},
        headers={"X-Requested-With": "fetch"},
    )
    assert respuesta.status_code == 422
    assert "Selecciona al menos un libro" in respuesta.get_json()["mensaje"]


def test_vista_previa_solo_con_libros_marcados(app, biblio):
    """
    Descripcion:
        Prueba: HU-01-17 · Vista previa de impresion con los libros marcados.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente con sesion de
            bibliotecario.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    contenido_html = biblio.get(
        "/reportes/libros/imprimir", query_string=marcar_libros(app, "LIB-003")
    ).get_data(as_text=True)
    assert "Ingeniería de software" in contenido_html
    assert "Pedro Páramo" not in contenido_html
    assert "1 libro seleccionado" in contenido_html


def test_impresion_con_libros_marcados(app, biblio):
    """
    Descripcion:
        Prueba: HU-01-17 · Impresion con filtros: solo los libros marcados.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente con sesion de
            bibliotecario.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    datos = {
        "impresora": "recepcion",
        **marcar_libros(app, "LIB-001", "LIB-004"),
    }
    contenido_html = biblio.post(
        "/reportes/libros/imprimir", data=datos
    ).get_data(as_text=True)
    assert "2 registros enviados" in contenido_html


def test_impresion_sin_libros_marcados(biblio):
    """
    Descripcion:
        Prueba: HU-01-17: sin libros marcados no se envia nada a impresion.

    Parametros:
        biblio (flask.testing.FlaskClient): cliente con sesion de
            bibliotecario.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = biblio.post(
        "/reportes/libros/imprimir",
        data={"impresora": "recepcion", "seleccion": "1"},
    )
    assert respuesta.status_code == 422
    assert "Selecciona al menos un libro" in respuesta.get_data(as_text=True)
