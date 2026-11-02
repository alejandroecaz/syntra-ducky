"""
============================================================
Archivo:      tests/conftest.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Fixtures compartidas: cada prueba usa su propia copia de la base de
    datos de demostracion.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

import shutil

import pytest

import init_db
from app import crear_aplicacion
from models.db import consultar


@pytest.fixture(scope="session")
def bd_plantilla(tmp_path_factory):
    """
    Descripcion:
        Fixture: crea una sola vez por sesion de pruebas la base de datos de
        demostracion.

    Parametros:
        tmp_path_factory (pytest.TempPathFactory): fabrica de carpetas
            temporales de pytest.

    Salida:
        pathlib.Path: ruta de la base plantilla.
    """
    ruta = tmp_path_factory.mktemp("bd") / "plantilla.db"
    init_db.inicializar(str(ruta))
    return ruta


@pytest.fixture
def app(bd_plantilla, tmp_path):
    """
    Descripcion:
        Fixture: aplicacion de prueba con su propia copia de la base de datos.

    Parametros:
        bd_plantilla (pathlib.Path): base de datos plantilla.
        tmp_path (pathlib.Path): carpeta temporal de la prueba.

    Salida:
        flask.Flask: aplicacion de prueba.
    """
    ruta = tmp_path / "prueba.db"
    shutil.copy(bd_plantilla, ruta)
    return crear_aplicacion({"RUTA_BASE_DATOS": str(ruta), "TESTING": True})


@pytest.fixture
def cliente(app):
    """
    Descripcion:
        Fixture: cliente HTTP de Flask para hacer peticiones a la app de
        prueba.

    Parametros:
        app (flask.Flask): aplicacion de prueba.

    Salida:
        flask.testing.FlaskClient: cliente de prueba.
    """
    return app.test_client()


@pytest.fixture
def contexto(app):
    """
    Descripcion:
        Fixture: contexto de la app para llamar directo a servicios y modelos.

    Parametros:
        app (flask.Flask): aplicacion de prueba.

    Salida:
        Ninguna (es un generador que mantiene el contexto abierto).
    """
    with app.app_context():
        yield


def entrar(cliente, cuenta, contrasena, ruta="/login"):
    """
    Descripcion:
        Envia el formulario de inicio de sesion.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba.
        cuenta (str): cuenta.
        contrasena (str): contrasena.
        ruta (str): ruta del login (web o movil).

    Salida:
        flask.Response: respuesta del login.
    """
    return cliente.post(
        ruta, data={"cuenta": cuenta, "contrasena": contrasena}
    )


def obtener_id_libro(app, clave):
    """
    Descripcion:
        Obtiene el id del libro con esa clave.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        clave (str): clave del libro.

    Salida:
        int: id del libro.
    """
    with app.app_context():
        return consultar(
            "SELECT id FROM libros WHERE clave = ?", (clave,), uno=True
        )["id"]
