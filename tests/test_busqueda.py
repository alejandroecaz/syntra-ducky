"""Búsqueda de libros por filtros (HU-01-13) a través del servicio que comparten web y móvil."""
import pytest

from services.catalogo_servicio import buscar_libros
from tests.conftest import entrar

pytestmark = pytest.mark.usefixtures("contexto")


def claves(resultado):
    return sorted(libro["clave"] for libro in resultado["libros"])


def test_titulo_sin_acentos_ni_mayusculas():
    assert claves(buscar_libros("titulo", "PARAMO")) == ["LIB-002"]


def test_titulo_por_coincidencia_parcial():
    assert claves(buscar_libros("titulo", "códi")) == ["LIB-004"]


def test_autor():
    assert claves(buscar_libros("autor", "garcia marquez")) == ["LIB-001"]


def test_autor_que_no_es_el_primero_de_varios():
    assert claves(buscar_libros("autor", "ritchie")) == ["LIB-016"]
    assert claves(buscar_libros("autor", "Leiserson")) == ["LIB-010"]


def test_tema():
    assert claves(buscar_libros("tema", "programacion")) == ["LIB-004", "LIB-010", "LIB-016"]


def test_editorial():
    assert claves(buscar_libros("editorial", "mcgraw")) == ["LIB-003", "LIB-009", "LIB-012"]


def test_resultado_trae_autores_editorial_y_disponibles():
    libro = buscar_libros("clave", "LIB-010")["libros"][0]
    assert libro["autores"] == "Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, Clifford Stein"
    assert libro["editorial"] == "MIT Press"
    assert (libro["disponibles"], libro["total_ejemplares"]) == (1, 2)


def test_clave_exacta():
    assert claves(buscar_libros("clave", "LIB-001")) == ["LIB-001"]


def test_clave_parcial_no_encuentra():
    assert claves(buscar_libros("clave", "LIB-00")) == []


@pytest.mark.parametrize("texto", ["", "   "])
def test_texto_vacio_pide_criterio(texto):
    resultado = buscar_libros("titulo", texto)
    assert resultado["error"] == "Captura un criterio de búsqueda"
    assert resultado["libros"] == []
    assert resultado["campo"] == "titulo"


def test_sin_resultados():
    resultado = buscar_libros("titulo", "zzzz")
    assert resultado["libros"] == []
    assert resultado["error"] is None


def test_comodines_se_buscan_como_texto():
    assert claves(buscar_libros("titulo", "%")) == []


def test_libro_dado_de_baja_no_aparece_en_activos():
    assert claves(buscar_libros("titulo", "redaccion")) == []
    assert claves(buscar_libros("titulo", "redaccion", vista="todos")) == ["LIB-014"]


def test_campo_invalido_busca_por_titulo():
    resultado = buscar_libros("contrasena", "paramo")
    assert resultado["campo"] == "titulo"
    assert claves(resultado) == ["LIB-002"]


def test_catalogo_web_muestra_sin_resultados(cliente):
    entrar(cliente, "alumno", "Alumno123")
    respuesta = cliente.get("/catalogo?buscar=1&campo=titulo&q=zzzz")
    assert "No se encontraron libros" in respuesta.get_data(as_text=True)
