"""Inicio de sesión web (HU-01-01) y control de acceso por permisos."""
import pytest

from models.db import consultar
from services import auth_servicio
from services.errores import ErrorValidacion
from tests.conftest import entrar


def test_login_exitoso(cliente):
    respuesta = entrar(cliente, "alumno", "Alumno123")
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/inicio")
    with cliente.session_transaction() as sesion:
        assert sesion["perfil"] == "Alumno"
        assert "catalogo.consultar" in sesion["permisos"]


@pytest.mark.parametrize("ruta", ["/login", "/movil/login"])
def test_login_sin_cuentas_de_demostracion(cliente, ruta):
    html = cliente.get(ruta).get_data(as_text=True)
    assert "Cuentas de demostración" not in html
    assert "Admin123" not in html


def test_login_muestra_solo_funciones_del_perfil(cliente):
    entrar(cliente, "alumno", "Alumno123")
    html = cliente.get("/inicio").get_data(as_text=True)
    assert "Buscar libros" in html
    assert "Registrar usuario" not in html


@pytest.mark.parametrize("cuenta, contrasena", [("alumno", "incorrecta"), ("noexiste", "Alumno123")])
def test_credenciales_incorrectas(cliente, cuenta, contrasena):
    respuesta = entrar(cliente, cuenta, contrasena)
    assert respuesta.status_code == 400
    assert "Cuenta o contraseña incorrecta" in respuesta.get_data(as_text=True)
    with cliente.session_transaction() as sesion:
        assert "usuario_id" not in sesion


def test_campos_vacios(cliente):
    respuesta = entrar(cliente, "", "")
    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 400
    assert "Completa los campos obligatorios" in html
    assert "Captura tu cuenta." in html


def test_cuenta_deshabilitada(cliente):
    respuesta = entrar(cliente, "deshabilitado", "Demo123")
    assert respuesta.status_code == 400
    assert "La cuenta no está habilitada" in respuesta.get_data(as_text=True)


def test_perfil_sin_acceso(cliente):
    respuesta = entrar(cliente, "visitante", "Demo123")
    assert respuesta.status_code == 400
    assert "no tiene autorización para acceder al sistema" in respuesta.get_data(as_text=True)


def test_servicio_rechaza_perfil_sin_acceso(contexto):
    with pytest.raises(ErrorValidacion) as error:
        auth_servicio.autenticar("visitante", "Demo123")
    assert error.value.mensaje == "Tu perfil de usuario no tiene autorización para acceder al sistema."


def test_contrasenas_guardadas_con_hash(contexto):
    for fila in consultar("SELECT contrasena FROM usuarios"):
        assert fila["contrasena"].startswith("pbkdf2:sha256:")


def test_sin_sesion_pide_iniciar_sesion(cliente):
    respuesta = cliente.get("/usuarios")
    assert respuesta.status_code == 302
    assert "/login" in respuesta.headers["Location"]


def test_perfil_sin_permiso_ve_acceso_no_autorizado(cliente):
    entrar(cliente, "alumno", "Alumno123")
    respuesta = cliente.get("/usuarios")
    assert respuesta.status_code == 403
    assert "Acceso no autorizado" in respuesta.get_data(as_text=True)
