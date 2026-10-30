# ============================================================
# Archivo: tests/test_busqueda.py
# Proyecto: Sistema Ducky de Gestión Bibliotecaria
# Syntra Technologies - Equipo 1 - Sprint 1
# Materia: Ingeniería de Software
# Autores:
#   - Melissa Silva Vázquez                #624352
#   - Tomás Zapata Pérez                   #629048
#   - Alejandro Evaristo Cazares Escobedo  #626337
# Descripción: Búsqueda de libros por filtros (HU-01-13) a través del servicio que comparten web y móvil.
# ============================================================
"""Búsqueda de libros por filtros (HU-01-13) a través del servicio que comparten web y móvil."""
import pytest

from services.catalogo_servicio import buscar_libros
from tests.conftest import entrar

pytestmark = pytest.mark.usefixtures("contexto")


def claves(resultado):
    """Claves ordenadas de los libros que regresó la búsqueda."""
    return sorted(libro["clave"] for libro in resultado["libros"])


def test_titulo_sin_acentos_ni_mayusculas():
    """HU-01-13 · Búsqueda por título sin importar acentos ni mayúsculas."""
    assert claves(buscar_libros("titulo", "PARAMO")) == ["LIB-002"]


def test_titulo_por_coincidencia_parcial():
    """HU-01-13 · Búsqueda por título con una parte del texto."""
    assert claves(buscar_libros("titulo", "códi")) == ["LIB-004"]


def test_autor():
    """HU-01-13 · Búsqueda por autor."""
    assert claves(buscar_libros("autor", "garcia marquez")) == ["LIB-001"]


def test_autor_que_no_es_el_primero_de_varios():
    """HU-01-13 · Encuentra libros de varios autores por cualquiera de ellos."""
    assert claves(buscar_libros("autor", "ritchie")) == ["LIB-016"]
    assert claves(buscar_libros("autor", "Leiserson")) == ["LIB-010"]


def test_tema():
    """HU-01-13 · Búsqueda por tema."""
    assert claves(buscar_libros("tema", "programacion")) == ["LIB-004", "LIB-010", "LIB-016"]


def test_editorial():
    """HU-01-13 · Búsqueda por editorial."""
    assert claves(buscar_libros("editorial", "mcgraw")) == ["LIB-003", "LIB-009", "LIB-012"]


def test_resultado_trae_autores_editorial_y_disponibles():
    """HU-01-13: cada resultado trae autores, editorial y ejemplares disponibles."""
    libro = buscar_libros("clave", "LIB-010")["libros"][0]
    assert libro["autores"] == "Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, Clifford Stein"
    assert libro["editorial"] == "MIT Press"
    assert (libro["disponibles"], libro["total_ejemplares"]) == (1, 2)


def test_clave_exacta():
    """HU-01-13 · Búsqueda por clave exacta."""
    assert claves(buscar_libros("clave", "LIB-001")) == ["LIB-001"]


def test_clave_parcial_no_encuentra():
    """HU-01-13 · La clave no se busca por coincidencia parcial."""
    assert claves(buscar_libros("clave", "LIB-00")) == []


@pytest.mark.parametrize("texto", ["", "   "])
def test_texto_vacio_pide_criterio(texto):
    """HU-01-13 · Criterio vacío (o solo espacios): se pide un criterio."""
    resultado = buscar_libros("titulo", texto)
    assert resultado["error"] == "Captura un criterio de búsqueda"
    assert resultado["libros"] == []
    assert resultado["campo"] == "titulo"


def test_sin_resultados():
    """HU-01-13 · Sin coincidencias."""
    resultado = buscar_libros("titulo", "zzzz")
    assert resultado["libros"] == []
    assert resultado["error"] is None


def test_comodines_se_buscan_como_texto():
    """HU-01-13: % y _ se buscan como texto, no como comodines de SQL."""
    assert claves(buscar_libros("titulo", "%")) == []


def test_libro_dado_de_baja_no_aparece_en_activos():
    """HU-01-10: un libro dado de baja no aparece en la búsqueda de activos."""
    assert claves(buscar_libros("titulo", "redaccion")) == []
    assert claves(buscar_libros("titulo", "redaccion", vista="todos")) == ["LIB-014"]


def test_campo_invalido_busca_por_titulo():
    """HU-01-13: un campo de búsqueda inválido se cambia por título."""
    resultado = buscar_libros("contrasena", "paramo")
    assert resultado["campo"] == "titulo"
    assert claves(resultado) == ["LIB-002"]


def test_catalogo_web_muestra_sin_resultados(cliente):
    """HU-01-13 · Sin coincidencias: el catálogo web muestra el mensaje."""
    entrar(cliente, "alumno", "Alumno123")
    respuesta = cliente.get("/catalogo?buscar=1&campo=titulo&q=zzzz")
    assert "No se encontraron libros" in respuesta.get_data(as_text=True)
