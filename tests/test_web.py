# ============================================================
# Archivo: tests/test_web.py
# Proyecto: Sistema Ducky de Gestión Bibliotecaria
# Syntra Technologies - Equipo 1 - Sprint 1
# Materia: Ingeniería de Software
# Autores:
#   - Melissa Silva Vázquez                #624352
#   - Tomás Zapata Pérez                   #629048
#   - Alejandro Evaristo Cazares Escobedo  #626337
# Descripción: Pruebas de humo de la app web: que lo que ya funcionaba siga funcionando con el esquema nuevo.
# ============================================================
"""Pruebas de humo de la app web: que lo que ya funcionaba siga funcionando con el esquema nuevo."""
from datetime import date, timedelta

import pytest

from tests.conftest import entrar, id_libro

PANTALLAS_ADMIN = [
    "/inicio", "/catalogo", "/catalogo?ver=todos", "/catalogo/nuevo", "/usuarios", "/usuarios/nuevo",
    "/usuarios/1", "/usuarios/5/editar", "/usuarios/5/perfil", "/perfiles", "/perfiles/nuevo",
    "/reportes/libros", "/reportes/libros/imprimir", "/compras", "/compras/nueva", "/cuenta/contrasena",
]


@pytest.fixture
def admin(cliente):
    """Cliente con la sesión del administrador iniciada."""
    entrar(cliente, "admin", "Admin123")
    return cliente


@pytest.mark.parametrize("ruta", PANTALLAS_ADMIN)
def test_pantallas_abren(admin, ruta):
    """Todas las pantallas del administrador abren sin error."""
    assert admin.get(ruta).status_code == 200


def test_ficha_muestra_autores_y_ubicaciones(app, admin):
    """HU-01-12 · Abrir detalle y HU-01-14 · Varios ejemplares en distintas salas."""
    html = admin.get(f"/catalogo/{id_libro(app, 'LIB-001')}").get_data(as_text=True)
    assert "Gabriel García Márquez" in html
    assert "Sala General · Estante A-1 · Posición 3" in html
    assert "Sala de Lectura · Estante L-2 · Posición 1" in html


def test_alta_de_libro_con_varios_autores(app, admin):
    """HU-01-09 · Alta exitosa de un libro con varios autores en orden."""
    respuesta = admin.post("/catalogo/nuevo", data={
        "clave": "lib-020", "titulo": "Estructuras de datos", "autores": "Ana Pérez; Luis Gómez",
        "tema": "Computación", "editorial": "Pearson", "anio": "2020", "tipo_acceso": "Circulante",
    })
    assert respuesta.status_code == 302
    html = admin.get(respuesta.headers["Location"]).get_data(as_text=True)
    assert "Libro registrado" in html
    assert "Ana Pérez, Luis Gómez" in html
    assert "Este libro no tiene ejemplares registrados" in html


def test_alta_con_clave_duplicada(admin):
    """HU-01-09 · Clave duplicada."""
    respuesta = admin.post("/catalogo/nuevo", data={
        "clave": "LIB-001", "titulo": "Otro", "autores": "Alguien", "tema": "Literatura", "editorial": "Planeta",
    })
    assert respuesta.status_code == 400
    assert "La clave del libro ya existe" in respuesta.get_data(as_text=True)


def test_alta_incompleta_conserva_lo_capturado(admin):
    """HU-01-09 · Datos bibliográficos incompletos: se conserva lo capturado."""
    respuesta = admin.post("/catalogo/nuevo", data={"clave": "LIB-030", "titulo": "Sin autor"})
    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 400
    assert "Faltan datos bibliográficos obligatorios" in html
    assert 'value="Sin autor"' in html


def test_edicion_conserva_clave(app, admin):
    """HU-01-11 · Corrección exitosa: la clave y los ejemplares no cambian."""
    libro_id = id_libro(app, "LIB-013")
    respuesta = admin.post(f"/catalogo/{libro_id}/editar", data={
        "titulo": "Física universitaria", "autores": "Hugh D. Young; Roger A. Freedman", "tema": "Ciencia",
        "editorial": "Pearson", "anio": "2013",
    })
    assert respuesta.status_code == 302
    html = admin.get(f"/catalogo/{libro_id}").get_data(as_text=True)
    assert "Hugh D. Young, Roger A. Freedman" in html
    assert "LIB-013" in html


def test_ejemplar_con_ubicacion_incompleta_se_rechaza(app, admin):
    """HU-01-14: la ubicación va completa o vacía."""
    libro_id = id_libro(app, "LIB-008")
    admin.post(f"/catalogo/{libro_id}/ejemplares", data={"estado": "Disponible", "estancia": "1"})
    html = admin.get(f"/catalogo/{libro_id}").get_data(as_text=True)
    assert "No se agregó el ejemplar" in html


def test_ejemplar_con_estante_nuevo(app, admin):
    """HU-01-14: un estante nuevo se registra al agregar el ejemplar."""
    libro_id = id_libro(app, "LIB-008")
    admin.post(f"/catalogo/{libro_id}/ejemplares",
               data={"estado": "Disponible", "estancia": "1", "estante": "z-9", "posicion": "2"})
    html = admin.get(f"/catalogo/{libro_id}").get_data(as_text=True)
    assert "Sala General · Estante Z-9 · Posición 2" in html


def test_baja_con_operaciones_vigentes(app, admin):
    """HU-01-10 · Libro con operaciones vigentes: no se da de baja."""
    libro_id = id_libro(app, "LIB-001")
    admin.post(f"/catalogo/{libro_id}/baja")
    html = admin.get(f"/catalogo/{libro_id}").get_data(as_text=True)
    assert "existen operaciones vigentes" in html


def test_registro_de_usuario_y_duplicado(admin):
    """HU-01-02 · Registro exitoso y Usuario duplicado."""
    datos = {"identificador": "600200", "nombre": "Lucía", "apellido_paterno": "Treviño", "cuenta": "ltrevino",
             "email": "lucia@alumnos.ducky.edu.mx", "contrasena": "Lucia123", "perfil_id": "4"}
    respuesta = admin.post("/usuarios/nuevo", data=datos)
    assert respuesta.status_code == 302
    assert "Lucía Treviño" in admin.get("/usuarios").get_data(as_text=True)

    duplicado = admin.post("/usuarios/nuevo", data=datos)
    assert duplicado.status_code == 400
    assert "Ya existe un usuario con identificador 600200" in duplicado.get_data(as_text=True)


def test_orden_de_compra_con_proveedor_nuevo(app, admin):
    """HU-01-18 · Orden de compra registrada con un proveedor nuevo."""
    manana = (date.today() + timedelta(days=1)).isoformat()
    respuesta = admin.post("/compras/nueva", data={
        "proveedor": "Proveedor de prueba", "fecha_requerida": manana, "justificacion": "Demanda alta",
        "libro_id": [str(id_libro(app, "LIB-003")), str(id_libro(app, "LIB-003"))], "cantidad": ["2", "3"],
    })
    assert respuesta.status_code == 302
    respuesta = admin.post("/compras/confirmar")
    html = admin.get(respuesta.headers["Location"]).get_data(as_text=True)
    assert "Proveedor de prueba" in html
    assert ">5<" in html


def test_pdf_del_listado(admin):
    """HU-01-16 · Generación satisfactoria del PDF."""
    respuesta = admin.get("/reportes/libros/pdf?campo=autor&q=garcia")
    assert respuesta.mimetype == "application/pdf"
    assert respuesta.headers["X-Total-Registros"] == "1"
