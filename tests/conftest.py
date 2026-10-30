# ============================================================
# Archivo: tests/conftest.py
# Proyecto: Sistema Ducky de Gestión Bibliotecaria
# Syntra Technologies - Equipo 1 - Sprint 1
# Materia: Ingeniería de Software
# Autores:
#   - Melissa Silva Vázquez                #624352
#   - Tomás Zapata Pérez                   #629048
#   - Alejandro Evaristo Cazares Escobedo  #626337
# Descripción: Fixtures compartidas: cada prueba usa su propia copia de la base de datos de demostración.
# ============================================================
"""Fixtures compartidas: cada prueba usa su propia copia de la base de datos de demostración."""
import shutil

import pytest

import init_db
from app import crear_aplicacion
from models.db import consultar


@pytest.fixture(scope="session")
def bd_plantilla(tmp_path_factory):
    """Base de datos de demostración que se crea una sola vez por sesión de pruebas."""
    ruta = tmp_path_factory.mktemp("bd") / "plantilla.db"
    init_db.inicializar(str(ruta))
    return ruta


@pytest.fixture
def app(bd_plantilla, tmp_path):
    """Aplicación de prueba con su propia copia de la base de datos."""
    ruta = tmp_path / "prueba.db"
    shutil.copy(bd_plantilla, ruta)
    return crear_aplicacion({"DATABASE_PATH": str(ruta), "TESTING": True})


@pytest.fixture
def cliente(app):
    """Cliente HTTP de Flask para hacer peticiones a la app de prueba."""
    return app.test_client()


@pytest.fixture
def contexto(app):
    """Contexto de la app para llamar directo a servicios y modelos."""
    with app.app_context():
        yield


def entrar(cliente, cuenta, contrasena, ruta="/login"):
    """Envía el formulario de inicio de sesión y regresa la respuesta."""
    return cliente.post(ruta, data={"cuenta": cuenta, "contrasena": contrasena})


def id_libro(app, clave):
    """Id del libro con esa clave."""
    with app.app_context():
        return consultar("SELECT id FROM libros WHERE clave = ?", (clave,), uno=True)["id"]
