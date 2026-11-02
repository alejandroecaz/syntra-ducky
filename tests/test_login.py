"""
============================================================
Archivo:      tests/test_login.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Inicio de sesion web (HU-01-01) y control de acceso por permisos.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

import pytest

from models.db import consultar
from services import auth_servicio
from services.errores import ErrorValidacion
from tests.conftest import entrar


def test_login_exitoso(cliente):
    """
    Descripcion:
        Prueba: HU-01-01 · Inicio de sesion exitoso.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba sin sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = entrar(cliente, "alumno", "Alumno123")
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/inicio")
    with cliente.session_transaction() as sesion:
        assert sesion["perfil"] == "Alumno"
        assert "catalogo.consultar" in sesion["permisos"]


@pytest.mark.parametrize("ruta", ["/login", "/movil/login"])
def test_login_sin_cuentas_de_demostracion(cliente, ruta):
    """
    Descripcion:
        Prueba: Las pantallas de acceso (web y movil) no muestran las cuentas
        de demostracion.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba sin sesion.
        ruta (str): ruta a revisar (parametrizada).

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    contenido_html = cliente.get(ruta).get_data(as_text=True)
    assert "Cuentas de demostración" not in contenido_html
    assert "Admin123" not in contenido_html


def test_login_muestra_solo_funciones_del_perfil(cliente):
    """
    Descripcion:
        Prueba: HU-01-01 · Inicio de sesion exitoso: solo se ven las funciones
        del perfil.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba sin sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    entrar(cliente, "alumno", "Alumno123")
    contenido_html = cliente.get("/inicio").get_data(as_text=True)
    assert "Buscar libros" in contenido_html
    assert "Registrar usuario" not in contenido_html


@pytest.mark.parametrize(
    "cuenta, contrasena", [("alumno", "incorrecta"), ("noexiste", "Alumno123")]
)
def test_credenciales_incorrectas(cliente, cuenta, contrasena):
    """
    Descripcion:
        Prueba: HU-01-01 · Credenciales incorrectas (contrasena mala o cuenta
        inexistente).

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba sin sesion.
        cuenta (str): cuenta capturada (parametrizado).
        contrasena (str): contrasena capturada (parametrizado).

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = entrar(cliente, cuenta, contrasena)
    assert respuesta.status_code == 400
    assert "Cuenta o contraseña incorrecta" in respuesta.get_data(as_text=True)
    with cliente.session_transaction() as sesion:
        assert "usuario_id" not in sesion


def test_campos_vacios(cliente):
    """
    Descripcion:
        Prueba: HU-01-01 · Campos obligatorios vacios.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba sin sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = entrar(cliente, "", "")
    contenido_html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 400
    assert "Completa los campos obligatorios" in contenido_html
    assert "Captura tu cuenta." in contenido_html


def test_cuenta_deshabilitada(cliente):
    """
    Descripcion:
        Prueba: HU-01-01 · Cuenta deshabilitada.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba sin sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = entrar(cliente, "deshabilitado", "Demo123")
    assert respuesta.status_code == 400
    assert "La cuenta no está habilitada" in respuesta.get_data(as_text=True)


def test_perfil_sin_acceso(cliente):
    """
    Descripcion:
        Prueba: HU-01-01 · Perfil de usuario sin acceso al sistema.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba sin sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = entrar(cliente, "visitante", "Demo123")
    assert respuesta.status_code == 400
    assert (
        "no tiene autorización para acceder al sistema"
        in respuesta.get_data(as_text=True)
    )


def test_servicio_rechaza_perfil_sin_acceso(contexto):
    """
    Descripcion:
        Prueba: HU-01-01 · Perfil sin acceso, probado directo en el servicio.

    Parametros:
        contexto (None): contexto de la app abierto.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    with pytest.raises(ErrorValidacion) as error:
        auth_servicio.autenticar("visitante", "Demo123")
    assert (
        error.value.mensaje
        == "Tu perfil de usuario no tiene autorización para acceder al "
        "sistema."
    )


def test_contrasenas_guardadas_con_hash(contexto):
    """
    Descripcion:
        Prueba: Las contrasenas se guardan cifradas, nunca en texto plano.

    Parametros:
        contexto (None): contexto de la app abierto.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    for fila in consultar("SELECT contrasena FROM usuarios"):
        assert fila["contrasena"].startswith("pbkdf2:sha256:")


def test_sin_sesion_pide_iniciar_sesion(cliente):
    """
    Descripcion:
        Prueba: Sin sesion, cualquier pantalla protegida manda al login.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba sin sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = cliente.get("/usuarios")
    assert respuesta.status_code == 302
    assert "/login" in respuesta.headers["Location"]


def test_perfil_sin_permiso_ve_acceso_no_autorizado(cliente):
    """
    Descripcion:
        Prueba: Criterio Acceso sin autorizacion: con sesion pero sin el
        permiso responde 403.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba sin sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    entrar(cliente, "alumno", "Alumno123")
    respuesta = cliente.get("/usuarios")
    assert respuesta.status_code == 403
    assert "Acceso no autorizado" in respuesta.get_data(as_text=True)
