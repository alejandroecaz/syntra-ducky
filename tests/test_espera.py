"""
============================================================
Archivo:      tests/test_espera.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Pruebas de la lista de espera (HU-02-06 Registro de lista de
    espera).

    Datos de prueba: LIB-011 no tiene ejemplares disponibles y lo esperan
    Mariana (turno 1) y Pedro Martinez (turno 2); en LIB-003 el unico
    ejemplar disponible (EJ-0008) le toca a Daniela Fuentes (turno 1).

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    13/11/2026
============================================================
"""

import os

import pytest

from models import lista_espera as espera_modelo
from models.db import consultar
from tests.conftest import entrar


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


def leer_solicitudes(app):
    """
    Descripcion:
        Lee las solicitudes de la lista de espera.

    Parametros:
        app (flask.Flask): aplicacion de prueba.

    Salida:
        list[tuple[str, str, str]]: (clave del libro, cuenta, estado).
    """
    with app.app_context():
        return [
            tuple(fila)
            for fila in consultar(
                "SELECT l.clave, u.cuenta, le.estado FROM lista_espera le "
                "JOIN libros l ON l.id = le.libro_id "
                "JOIN usuarios u ON u.id = le.usuario_id ORDER BY le.id"
            )
        ]


def test_lista_muestra_turnos(biblio):
    """
    Descripcion:
        Prueba: HU-02-06 · La lista muestra las solicitudes con su turno y
        avisa cuando ya hay un ejemplar para el turno.

    Parametros:
        biblio (flask.testing.FlaskClient): cliente con sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    contenido_html = biblio.get("/espera").get_data(as_text=True)
    assert "3 solicitudes esperando turno" in contenido_html
    assert "La sombra del viento" in contenido_html
    assert "Ejemplar disponible" in contenido_html
    assert "usuario=C30010&amp;ejemplar=EJ-0008" in contenido_html


def test_registro_en_lista_de_espera(app, biblio):
    """
    Descripcion:
        Prueba: HU-02-06 · Registro exitoso con el siguiente turno.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente con sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = biblio.post(
        "/espera", data={"usuario": "600102", "libro": "lib-011"}
    )
    assert respuesta.status_code == 302
    assert "con el turno 3" in biblio.get("/espera").get_data(as_text=True)
    assert leer_solicitudes(app)[-1] == ("LIB-011", "jlopez", "En espera")


@pytest.mark.parametrize(
    "usuario, libro, campo_mensaje",
    [
        ("", "LIB-011", "Captura la matrícula o la cuenta"),
        ("deshabilitado", "LIB-011", "está deshabilitada"),
        ("visitante", "LIB-011", "no tiene préstamos a domicilio"),
        ("600102", "", "Captura la clave del libro"),
        ("600102", "LIB-999", "No existe un libro con la clave LIB-999"),
        ("600102", "LIB-014", "está dado de baja"),
        ("600102", "LIB-012", "no se presta a domicilio"),
        ("600102", "LIB-005", "registra el préstamo directamente"),
        ("profesor", "LIB-011", "ya tiene prestado un ejemplar"),
        ("600101", "LIB-011", "ya está en la lista de espera de este libro"),
    ],
)
def test_registro_rechazado(app, biblio, usuario, libro, campo_mensaje):
    """
    Descripcion:
        Prueba: HU-02-06 · No se registra con datos vacios, usuario sin
        prestamos, libro inexistente, dado de baja, de acceso reservado o con
        ejemplares disponibles, si el usuario ya tiene el libro o ya esta en
        la lista.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente con sesion.
        usuario (str): usuario capturado (parametrizado).
        libro (str): clave capturada (parametrizado).
        campo_mensaje (str): error esperado (parametrizado).

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    antes = leer_solicitudes(app)
    respuesta = biblio.post(
        "/espera", data={"usuario": usuario, "libro": libro}
    )
    assert respuesta.status_code == 422
    assert campo_mensaje in respuesta.get_data(as_text=True)
    assert leer_solicitudes(app) == antes


def test_prestamo_respeta_el_turno(app, biblio):
    """
    Descripcion:
        Prueba: HU-02-06 · El ejemplar disponible de LIB-003 es para el turno
        1: no se le presta a otra persona, si a quien le toca, y su solicitud
        queda atendida.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente con sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    otra = biblio.post(
        "/prestamos/nuevo", data={"usuario": "600101", "ejemplar": "EJ-0008"}
    )
    assert otra.status_code == 422
    assert "le toca primero" in otra.get_data(as_text=True)

    turno = biblio.post(
        "/prestamos/nuevo", data={"usuario": "C30010", "ejemplar": "EJ-0008"}
    )
    assert turno.status_code == 302
    assert biblio.post("/prestamos/confirmar").status_code == 302
    assert ("LIB-003", "dfuentes", "Atendido") in leer_solicitudes(app)


def test_aviso_por_correo(app, biblio):
    """
    Descripcion:
        Prueba: HU-02-06 · Aviso por correo a quien ya le toca: se guarda el
        aviso y la solicitud queda notificada.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente con sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = biblio.post("/espera/3/avisar", data={"medio": "correo"})
    assert respuesta.status_code == 302
    assert ("LIB-003", "dfuentes", "Notificado") in leer_solicitudes(app)
    archivos = os.listdir(app.config["CARPETA_BOLETAS"])
    assert archivos and archivos[0].startswith("aviso_espera_3")
    with app.app_context():
        aviso = consultar("SELECT tipo, medio FROM avisos", uno=True)
    assert tuple(aviso) == ("Lista de espera", "Email")


@pytest.mark.parametrize(
    "solicitud, medio, codigo, mensaje",
    [
        (1, "correo", 409, "Todavía no hay un ejemplar disponible"),
        (3, "whatsapp", 400, "no tiene un celular registrado"),
    ],
)
def test_aviso_rechazado(app, biblio, solicitud, medio, codigo, mensaje):
    """
    Descripcion:
        Prueba: HU-02-06 · No se avisa si todavia no le toca un ejemplar ni
        por WhatsApp si el usuario no tiene celular.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente con sesion.
        solicitud (int): id de la solicitud (parametrizado).
        medio (str): correo o whatsapp (parametrizado).
        codigo (int): codigo HTTP esperado (parametrizado).
        mensaje (str): error esperado (parametrizado).

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    antes = leer_solicitudes(app)
    respuesta = biblio.post(
        f"/espera/{solicitud}/avisar", data={"medio": medio}
    )
    assert respuesta.status_code == codigo
    assert mensaje in respuesta.get_data(as_text=True)
    assert leer_solicitudes(app) == antes


def test_cancelar_solicitud(app, biblio):
    """
    Descripcion:
        Prueba: HU-02-06 · Cancelar una solicitud recorre los turnos.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente con sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    assert biblio.post("/espera/1/cancelar").status_code == 302
    assert leer_solicitudes(app)[0] == ("LIB-011", "alumno", "Cancelado")
    with app.app_context():
        assert espera_modelo.obtener(2)["turno"] == 1


def test_ficha_ofrece_lista_de_espera(biblio):
    """
    Descripcion:
        Prueba: HU-02-06 · La ficha de un libro sin disponibles lleva a la
        lista de espera con la clave capturada.

    Parametros:
        biblio (flask.testing.FlaskClient): cliente con sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    assert "/espera?libro=LIB-011" in biblio.get("/catalogo/11").get_data(
        as_text=True
    )
    formulario = biblio.get("/espera?libro=LIB-011").get_data(as_text=True)
    assert 'value="LIB-011"' in formulario


def test_lista_de_espera_sin_permiso(cliente):
    """
    Descripcion:
        Prueba: Acceso sin autorizacion: un alumno no ve la lista de espera.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    entrar(cliente, "alumno", "Alumno123")
    assert cliente.get("/espera").status_code == 403
    assert cliente.post("/espera/1/cancelar").status_code == 403
