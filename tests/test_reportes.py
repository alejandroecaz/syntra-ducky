"""Listado de libros: PDF (HU-01-16) e impresión (HU-01-17) solo con los libros marcados."""
import re

import pytest

from tests.conftest import entrar, id_libro


@pytest.fixture
def biblio(cliente):
    entrar(cliente, "biblio", "Biblio123")
    return cliente


def marcados(app, *claves):
    """Parámetros que manda el listado cuando el usuario marca esos libros."""
    return {"seleccion": "1", "libro": [str(id_libro(app, clave)) for clave in claves]}


def casillas_marcadas(html):
    return len(re.findall(r"data-seleccion-libro[^>]*checked>", html))


def test_listado_muestra_todos_marcados(biblio):
    html = biblio.get("/reportes/libros").get_data(as_text=True)
    assert html.count("data-seleccion-libro") == 15
    assert casillas_marcadas(html) == 15


def test_listado_conserva_la_seleccion_al_regresar(app, biblio):
    html = biblio.get("/reportes/libros", query_string=marcados(app, "LIB-001")).get_data(as_text=True)
    assert casillas_marcadas(html) == 1


def test_pdf_solo_con_libros_marcados(app, biblio):
    respuesta = biblio.get("/reportes/libros/pdf", query_string=marcados(app, "LIB-001", "LIB-002"))
    assert respuesta.mimetype == "application/pdf"
    assert respuesta.headers["X-Total-Registros"] == "2"


def test_pdf_sin_seleccion_incluye_todos_los_filtrados(biblio):
    respuesta = biblio.get("/reportes/libros/pdf?campo=tema&q=programacion")
    assert respuesta.headers["X-Total-Registros"] == "3"


def test_seleccion_respeta_los_filtros(app, biblio):
    parametros = {"campo": "autor", "q": "garcia", **marcados(app, "LIB-001", "LIB-002")}
    respuesta = biblio.get("/reportes/libros/pdf", query_string=parametros)
    assert respuesta.headers["X-Total-Registros"] == "1"


def test_pdf_sin_libros_marcados(biblio):
    respuesta = biblio.get("/reportes/libros/pdf", query_string={"seleccion": "1"},
                           headers={"X-Requested-With": "fetch"})
    assert respuesta.status_code == 422
    assert "Selecciona al menos un libro" in respuesta.get_json()["mensaje"]


def test_vista_previa_solo_con_libros_marcados(app, biblio):
    html = biblio.get("/reportes/libros/imprimir", query_string=marcados(app, "LIB-003")).get_data(as_text=True)
    assert "Ingeniería de software" in html
    assert "Pedro Páramo" not in html
    assert "1 libro seleccionado" in html


def test_impresion_con_libros_marcados(app, biblio):
    datos = {"impresora": "recepcion", **marcados(app, "LIB-001", "LIB-004")}
    html = biblio.post("/reportes/libros/imprimir", data=datos).get_data(as_text=True)
    assert "2 registros enviados" in html


def test_impresion_sin_libros_marcados(biblio):
    respuesta = biblio.post("/reportes/libros/imprimir", data={"impresora": "recepcion", "seleccion": "1"})
    assert respuesta.status_code == 422
    assert "Selecciona al menos un libro" in respuesta.get_data(as_text=True)
