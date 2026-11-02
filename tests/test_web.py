"""
============================================================
Archivo:      tests/test_web.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Pruebas de humo de la app web: que lo que ya funcionaba siga
    funcionando con el esquema nuevo.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

from datetime import date, timedelta

import pytest

from tests.conftest import entrar, obtener_id_libro

PANTALLAS_ADMIN = [
    "/inicio",
    "/catalogo",
    "/catalogo?ver=todos",
    "/catalogo/nuevo",
    "/usuarios",
    "/usuarios/nuevo",
    "/usuarios/1",
    "/usuarios/5/editar",
    "/usuarios/5/perfil",
    "/perfiles",
    "/perfiles/nuevo",
    "/reportes/libros",
    "/reportes/libros/imprimir",
    "/compras",
    "/compras/nueva",
    "/cuenta/contrasena",
]


@pytest.fixture
def admin(cliente):
    """
    Descripcion:
        Fixture: cliente con la sesion del administrador iniciada.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba.

    Salida:
        flask.testing.FlaskClient: cliente con sesion.
    """
    entrar(cliente, "admin", "Admin123")
    return cliente


@pytest.mark.parametrize("ruta", PANTALLAS_ADMIN)
def test_pantallas_abren(admin, ruta):
    """
    Descripcion:
        Prueba: Todas las pantallas del administrador abren sin error.

    Parametros:
        admin (flask.testing.FlaskClient): cliente con sesion de administrador.
        ruta (str): ruta a revisar (parametrizada).

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    assert admin.get(ruta).status_code == 200


def test_ficha_muestra_autores_y_ubicaciones(app, admin):
    """
    Descripcion:
        Prueba: HU-01-12 · Abrir detalle y HU-01-14 · Varios ejemplares en
        distintas salas.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        admin (flask.testing.FlaskClient): cliente con sesion de administrador.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    contenido_html = admin.get(
        f"/catalogo/{obtener_id_libro(app, 'LIB-001')}"
    ).get_data(as_text=True)
    assert "Gabriel García Márquez" in contenido_html
    assert "Sala General · Estante A-1 · Posición 3" in contenido_html
    assert "Sala de Lectura · Estante L-2 · Posición 1" in contenido_html


def test_alta_de_libro_con_varios_autores(app, admin):
    """
    Descripcion:
        Prueba: HU-01-09 · Alta exitosa de un libro con varios autores en
        orden.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        admin (flask.testing.FlaskClient): cliente con sesion de administrador.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = admin.post(
        "/catalogo/nuevo",
        data={
            "clave": "lib-020",
            "titulo": "Estructuras de datos",
            "autores": "Ana Pérez; Luis Gómez",
            "tema": "Computación",
            "editorial": "Pearson",
            "anio": "2020",
            "tipo_acceso": "Circulante",
        },
    )
    assert respuesta.status_code == 302
    contenido_html = admin.get(respuesta.headers["Location"]).get_data(
        as_text=True
    )
    assert "Libro registrado" in contenido_html
    assert "Ana Pérez, Luis Gómez" in contenido_html
    assert "Este libro no tiene ejemplares registrados" in contenido_html


def test_alta_con_clave_duplicada(admin):
    """
    Descripcion:
        Prueba: HU-01-09 · Clave duplicada.

    Parametros:
        admin (flask.testing.FlaskClient): cliente con sesion de administrador.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = admin.post(
        "/catalogo/nuevo",
        data={
            "clave": "LIB-001",
            "titulo": "Otro",
            "autores": "Alguien",
            "tema": "Literatura",
            "editorial": "Planeta",
        },
    )
    assert respuesta.status_code == 400
    assert "La clave del libro ya existe" in respuesta.get_data(as_text=True)


def test_alta_incompleta_conserva_lo_capturado(admin):
    """
    Descripcion:
        Prueba: HU-01-09 · Datos bibliograficos incompletos: se conserva lo
        capturado.

    Parametros:
        admin (flask.testing.FlaskClient): cliente con sesion de administrador.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = admin.post(
        "/catalogo/nuevo", data={"clave": "LIB-030", "titulo": "Sin autor"}
    )
    contenido_html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 400
    assert "Faltan datos bibliográficos obligatorios" in contenido_html
    assert 'value="Sin autor"' in contenido_html


def test_edicion_conserva_clave(app, admin):
    """
    Descripcion:
        Prueba: HU-01-11 · Correccion exitosa: la clave y los ejemplares no
        cambian.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        admin (flask.testing.FlaskClient): cliente con sesion de administrador.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    libro_id = obtener_id_libro(app, "LIB-013")
    respuesta = admin.post(
        f"/catalogo/{libro_id}/editar",
        data={
            "titulo": "Física universitaria",
            "autores": "Hugh D. Young; Roger A. Freedman",
            "tema": "Ciencia",
            "editorial": "Pearson",
            "anio": "2013",
        },
    )
    assert respuesta.status_code == 302
    contenido_html = admin.get(f"/catalogo/{libro_id}").get_data(as_text=True)
    assert "Hugh D. Young, Roger A. Freedman" in contenido_html
    assert "LIB-013" in contenido_html


def test_ejemplar_con_ubicacion_incompleta_se_rechaza(app, admin):
    """
    Descripcion:
        Prueba: HU-01-14: la ubicacion va completa o vacia.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        admin (flask.testing.FlaskClient): cliente con sesion de administrador.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    libro_id = obtener_id_libro(app, "LIB-008")
    admin.post(
        f"/catalogo/{libro_id}/ejemplares",
        data={"estado": "Disponible", "estancia": "1"},
    )
    contenido_html = admin.get(f"/catalogo/{libro_id}").get_data(as_text=True)
    assert "No se agregó el ejemplar" in contenido_html


def test_ejemplar_con_estante_nuevo(app, admin):
    """
    Descripcion:
        Prueba: HU-01-14: un estante nuevo se registra al agregar el ejemplar.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        admin (flask.testing.FlaskClient): cliente con sesion de administrador.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    libro_id = obtener_id_libro(app, "LIB-008")
    admin.post(
        f"/catalogo/{libro_id}/ejemplares",
        data={
            "estado": "Disponible",
            "estancia": "1",
            "estante": "z-9",
            "posicion": "2",
        },
    )
    contenido_html = admin.get(f"/catalogo/{libro_id}").get_data(as_text=True)
    assert "Sala General · Estante Z-9 · Posición 2" in contenido_html


def test_baja_con_operaciones_vigentes(app, admin):
    """
    Descripcion:
        Prueba: HU-01-10 · Libro con operaciones vigentes: no se da de baja.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        admin (flask.testing.FlaskClient): cliente con sesion de administrador.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    libro_id = obtener_id_libro(app, "LIB-001")
    admin.post(f"/catalogo/{libro_id}/baja")
    contenido_html = admin.get(f"/catalogo/{libro_id}").get_data(as_text=True)
    assert "existen operaciones vigentes" in contenido_html


def test_registro_de_usuario_y_duplicado(admin):
    """
    Descripcion:
        Prueba: HU-01-02 · Registro exitoso y Usuario duplicado.

    Parametros:
        admin (flask.testing.FlaskClient): cliente con sesion de administrador.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    datos = {
        "identificador": "600200",
        "nombre": "Lucía",
        "apellido_paterno": "Treviño",
        "cuenta": "ltrevino",
        "email": "lucia@alumnos.ducky.edu.mx",
        "contrasena": "Lucia123",
        "perfil_id": "4",
    }
    respuesta = admin.post("/usuarios/nuevo", data=datos)
    assert respuesta.status_code == 302
    assert "Lucía Treviño" in admin.get("/usuarios").get_data(as_text=True)

    duplicado = admin.post("/usuarios/nuevo", data=datos)
    assert duplicado.status_code == 400
    assert (
        "Ya existe un usuario con identificador 600200"
        in duplicado.get_data(as_text=True)
    )


def test_orden_de_compra_con_proveedor_nuevo(app, admin):
    """
    Descripcion:
        Prueba: HU-01-18 · Orden de compra registrada con un proveedor nuevo.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        admin (flask.testing.FlaskClient): cliente con sesion de administrador.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    manana = (date.today() + timedelta(days=1)).isoformat()
    respuesta = admin.post(
        "/compras/nueva",
        data={
            "proveedor": "Proveedor de prueba",
            "fecha_requerida": manana,
            "justificacion": "Demanda alta",
            "libro_id": [
                str(obtener_id_libro(app, "LIB-003")),
                str(obtener_id_libro(app, "LIB-003")),
            ],
            "cantidad": ["2", "3"],
        },
    )
    assert respuesta.status_code == 302
    respuesta = admin.post("/compras/confirmar")
    contenido_html = admin.get(respuesta.headers["Location"]).get_data(
        as_text=True
    )
    assert "Proveedor de prueba" in contenido_html
    assert ">5<" in contenido_html


def test_pdf_del_listado(admin):
    """
    Descripcion:
        Prueba: HU-01-16 · Generacion satisfactoria del PDF.

    Parametros:
        admin (flask.testing.FlaskClient): cliente con sesion de administrador.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = admin.get("/reportes/libros/pdf?campo=autor&q=garcia")
    assert respuesta.mimetype == "application/pdf"
    assert respuesta.headers["X-Total-Registros"] == "1"
