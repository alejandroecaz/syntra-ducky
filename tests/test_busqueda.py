"""
============================================================
Archivo:      tests/test_busqueda.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Busqueda de libros por filtros (HU-01-13) a traves del servicio que
    comparten web y movil.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

import pytest

from services.catalogo_servicio import buscar_libros
from tests.conftest import entrar

pytestmark = pytest.mark.usefixtures("contexto")


def obtener_claves(resultado):
    """
    Descripcion:
        Obtiene las claves ordenadas de los libros que regreso la busqueda.

    Parametros:
        resultado (dict): resultado de buscar_libros().

    Salida:
        list[str]: claves ordenadas.
    """
    return sorted(libro["clave"] for libro in resultado["libros"])


def test_titulo_sin_acentos_ni_mayusculas():
    """
    Descripcion:
        Prueba: HU-01-13 · Busqueda por titulo sin importar acentos ni
        mayusculas.

    Parametros:
        Ninguno.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    assert obtener_claves(buscar_libros("titulo", "PARAMO")) == ["LIB-002"]


def test_titulo_por_coincidencia_parcial():
    """
    Descripcion:
        Prueba: HU-01-13 · Busqueda por titulo con una parte del texto.

    Parametros:
        Ninguno.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    assert obtener_claves(buscar_libros("titulo", "códi")) == ["LIB-004"]


def test_autor():
    """
    Descripcion:
        Prueba: HU-01-13 · Busqueda por autor.

    Parametros:
        Ninguno.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    assert obtener_claves(buscar_libros("autor", "garcia marquez")) == [
        "LIB-001"
    ]


def test_autor_que_no_es_el_primero_de_varios():
    """
    Descripcion:
        Prueba: HU-01-13 · Encuentra libros de varios autores por cualquiera de
        ellos.

    Parametros:
        Ninguno.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    assert obtener_claves(buscar_libros("autor", "ritchie")) == ["LIB-016"]
    assert obtener_claves(buscar_libros("autor", "Leiserson")) == ["LIB-010"]


def test_tema():
    """
    Descripcion:
        Prueba: HU-01-13 · Busqueda por tema.

    Parametros:
        Ninguno.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    assert obtener_claves(buscar_libros("tema", "programacion")) == [
        "LIB-004",
        "LIB-010",
        "LIB-016",
    ]


def test_editorial():
    """
    Descripcion:
        Prueba: HU-01-13 · Busqueda por editorial.

    Parametros:
        Ninguno.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    assert obtener_claves(buscar_libros("editorial", "mcgraw")) == [
        "LIB-003",
        "LIB-009",
        "LIB-012",
    ]


def test_resultado_trae_autores_editorial_y_disponibles():
    """
    Descripcion:
        Prueba: HU-01-13: cada resultado trae autores, editorial y ejemplares
        disponibles.

    Parametros:
        Ninguno.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    libro = buscar_libros("clave", "LIB-010")["libros"][0]
    assert (
        libro["autores"]
        == "Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, "
        "Clifford Stein"
    )
    assert libro["editorial"] == "MIT Press"
    assert (libro["disponibles"], libro["total_ejemplares"]) == (1, 2)


def test_clave_exacta():
    """
    Descripcion:
        Prueba: HU-01-13 · Busqueda por clave exacta.

    Parametros:
        Ninguno.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    assert obtener_claves(buscar_libros("clave", "LIB-001")) == ["LIB-001"]


def test_clave_parcial_no_encuentra():
    """
    Descripcion:
        Prueba: HU-01-13 · La clave no se busca por coincidencia parcial.

    Parametros:
        Ninguno.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    assert obtener_claves(buscar_libros("clave", "LIB-00")) == []


@pytest.mark.parametrize("texto", ["", "   "])
def test_texto_vacio_pide_criterio(texto):
    """
    Descripcion:
        Prueba: HU-01-13 · Criterio vacio (o solo espacios): se pide un
        criterio.

    Parametros:
        texto (str): texto a buscar (parametrizado).

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    resultado = buscar_libros("titulo", texto)
    assert resultado["error"] == "Captura un criterio de búsqueda"
    assert resultado["libros"] == []
    assert resultado["campo"] == "titulo"


def test_sin_resultados():
    """
    Descripcion:
        Prueba: HU-01-13 · Sin coincidencias.

    Parametros:
        Ninguno.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    resultado = buscar_libros("titulo", "zzzz")
    assert resultado["libros"] == []
    assert resultado["error"] is None


def test_comodines_se_buscan_como_texto():
    """
    Descripcion:
        Prueba: HU-01-13: % y _ se buscan como texto, no como comodines de SQL.

    Parametros:
        Ninguno.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    assert obtener_claves(buscar_libros("titulo", "%")) == []


def test_libro_dado_de_baja_no_aparece_en_activos():
    """
    Descripcion:
        Prueba: HU-01-10: un libro dado de baja no aparece en la busqueda de
        activos.

    Parametros:
        Ninguno.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    assert obtener_claves(buscar_libros("titulo", "redaccion")) == []
    assert obtener_claves(
        buscar_libros("titulo", "redaccion", vista="todos")
    ) == ["LIB-014"]


def test_campo_invalido_busca_por_titulo():
    """
    Descripcion:
        Prueba: HU-01-13: un campo de busqueda invalido se cambia por titulo.

    Parametros:
        Ninguno.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    resultado = buscar_libros("contrasena", "paramo")
    assert resultado["campo"] == "titulo"
    assert obtener_claves(resultado) == ["LIB-002"]


def test_catalogo_web_muestra_sin_resultados(cliente):
    """
    Descripcion:
        Prueba: HU-01-13 · Sin coincidencias: el catalogo web muestra el
        mensaje.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba sin sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    entrar(cliente, "alumno", "Alumno123")
    respuesta = cliente.get("/catalogo?buscar=1&campo=titulo&q=zzzz")
    assert "No se encontraron libros" in respuesta.get_data(as_text=True)
