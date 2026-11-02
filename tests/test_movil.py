"""
============================================================
Archivo:      tests/test_movil.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Portal movil para alumnos (/movil).

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

import re

from models.db import consultar
from tests.conftest import entrar, obtener_id_libro

SOLO_ALUMNOS = "Acceso no autorizado: el portal móvil es solo para alumnos"


def entrar_movil(cliente, cuenta="alumno", contrasena="Alumno123"):
    """
    Descripcion:
        Envia el formulario de acceso del portal movil.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba.
        cuenta (str): cuenta (alumno por omision).
        contrasena (str): contrasena.

    Salida:
        flask.Response: respuesta del login.
    """
    return entrar(cliente, cuenta, contrasena, ruta="/movil/login")


def test_alumno_entra(cliente):
    """
    Descripcion:
        Prueba: HU-01-01 (movil) · Inicio de sesion exitoso de un alumno.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba sin sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = entrar_movil(cliente)
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/movil")
    assert "Hola, Mariana" in cliente.get("/movil").get_data(as_text=True)


def test_profesor_rechazado(cliente):
    """
    Descripcion:
        Prueba: HU-01-01 (movil): un profesor no puede entrar al portal (solo
        alumnos).

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba sin sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = entrar_movil(cliente, "profesor", "Profe123")
    assert respuesta.status_code == 403
    assert SOLO_ALUMNOS in respuesta.get_data(as_text=True)
    with cliente.session_transaction() as sesion:
        assert "usuario_id" not in sesion


def test_profesor_con_sesion_web_no_entra_al_portal(cliente):
    """
    Descripcion:
        Prueba: Un profesor con sesion web abierta recibe Acceso no autorizado
        en /movil.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba sin sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    entrar(cliente, "profesor", "Profe123")
    respuesta = cliente.get("/movil")
    assert respuesta.status_code == 403
    assert SOLO_ALUMNOS in respuesta.get_data(as_text=True)


def test_mismos_mensajes_que_la_web(cliente):
    """
    Descripcion:
        Prueba: HU-01-01 (movil): los mensajes de error son los mismos que en
        la web.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba sin sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    assert "La cuenta no está habilitada" in entrar_movil(
        cliente, "deshabilitado", "Demo123"
    ).get_data(as_text=True)
    assert "no tiene autorización para acceder" in entrar_movil(
        cliente, "visitante", "Demo123"
    ).get_data(as_text=True)
    assert "Cuenta o contraseña incorrecta" in entrar_movil(
        cliente, "alumno", "mala"
    ).get_data(as_text=True)


def test_sin_sesion_manda_al_login_movil(cliente):
    """
    Descripcion:
        Prueba: Sin sesion, el portal movil manda a su propio login.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba sin sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = cliente.get("/movil")
    assert respuesta.status_code == 302
    assert "/movil/login" in respuesta.headers["Location"]


def test_busqueda_vacia(cliente):
    """
    Descripcion:
        Prueba: HU-01-13 (movil) · Criterio vacio.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba sin sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    entrar_movil(cliente)
    contenido_html = cliente.get(
        "/movil?buscar=1&campo=autor&q=%20%20"
    ).get_data(as_text=True)
    assert "Captura un criterio de búsqueda" in contenido_html
    # Conserva el campo que se habia elegido.
    assert re.search(r'value="autor"\s+checked', contenido_html)


def test_busqueda_sin_resultados(cliente):
    """
    Descripcion:
        Prueba: HU-01-13 (movil) · Sin coincidencias.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba sin sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    entrar_movil(cliente)
    contenido_html = cliente.get(
        "/movil?buscar=1&campo=titulo&q=zzzz"
    ).get_data(as_text=True)
    assert "No se encontraron libros" in contenido_html
    assert "m-libro-titulo" not in contenido_html


def test_login_movil_sin_aviso_de_solo_alumnos(cliente):
    """
    Descripcion:
        Prueba: El login movil ya no muestra el aviso de solo alumnos.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba sin sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    assert "Solo para alumnos." not in cliente.get("/movil/login").get_data(
        as_text=True
    )


def test_despues_de_buscar_se_puede_limpiar(cliente):
    """
    Descripcion:
        Prueba: Despues de buscar aparece el boton para limpiar la busqueda.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba sin sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    entrar_movil(cliente)
    contenido_html = cliente.get(
        "/movil?buscar=1&campo=titulo&q=asdasd"
    ).get_data(as_text=True)
    assert (
        '<a href="/movil" class="boton boton-secundario boton-grande">'
        in contenido_html
    )
    assert "Nueva búsqueda" in contenido_html
    # En la pantalla inicial no hay nada que limpiar.
    assert "<span>Limpiar</span>" not in cliente.get("/movil").get_data(
        as_text=True
    )


def test_busqueda_con_resultados_en_tarjetas(cliente):
    """
    Descripcion:
        Prueba: HU-01-13 (movil): los resultados se muestran en tarjetas.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba sin sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    entrar_movil(cliente)
    contenido_html = cliente.get(
        "/movil?buscar=1&campo=autor&q=kernighan"
    ).get_data(as_text=True)
    assert "El lenguaje de programación C" in contenido_html
    assert "Brian W. Kernighan, Dennis M. Ritchie" in contenido_html
    assert "1 de 1 disponibles" in contenido_html


def test_detalle_sin_ubicacion(app, cliente):
    """
    Descripcion:
        Prueba: HU-01-14 (movil) · Ubicacion pendiente: se muestra "Ubicacion
        no registrada".

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        cliente (flask.testing.FlaskClient): cliente de prueba sin sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    entrar_movil(cliente)
    contenido_html = cliente.get(
        f"/movil/libros/{obtener_id_libro(app, 'LIB-002')}"
    ).get_data(as_text=True)
    assert "EJ-0005" in contenido_html
    assert "Ubicación no registrada" in contenido_html
    assert "Sala General · Estante A-2 · Posición 7" in contenido_html


def test_detalle_libro_sin_ejemplares(app, cliente):
    """
    Descripcion:
        Prueba: HU-01-15 (movil) · Libro sin ejemplares.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        cliente (flask.testing.FlaskClient): cliente de prueba sin sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    entrar_movil(cliente)
    contenido_html = cliente.get(
        f"/movil/libros/{obtener_id_libro(app, 'LIB-008')}"
    ).get_data(as_text=True)
    assert "Este libro no tiene ejemplares registrados" in contenido_html


def test_estados_no_disponibles_no_se_muestran_como_disponible(app, cliente):
    """
    Descripcion:
        Prueba: HU-01-15 (movil) · Ejemplar no disponible.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        cliente (flask.testing.FlaskClient): cliente de prueba sin sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    entrar_movil(cliente)
    contenido_html = cliente.get(
        f"/movil/libros/{obtener_id_libro(app, 'LIB-006')}"
    ).get_data(as_text=True)
    assert (
        "Perdido" in contenido_html and "Fuera de servicio" in contenido_html
    )
    assert "etiqueta-exito" not in contenido_html


def test_libro_inexistente(cliente):
    """
    Descripcion:
        Prueba: El portal movil responde 404 con su propia vista si el libro no
        existe.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba sin sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    entrar_movil(cliente)
    respuesta = cliente.get("/movil/libros/9999")
    assert respuesta.status_code == 404
    assert "No encontramos ese libro" in respuesta.get_data(as_text=True)


def test_permiso_movil_solo_en_perfil_alumno(contexto):
    """
    Descripcion:
        Prueba: El permiso movil.acceder solo lo tiene el perfil Alumno.

    Parametros:
        contexto (None): contexto de la app abierto.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    filas = consultar(
        "SELECT p.nombre FROM perfil_permisos pp JOIN perfiles p ON p.id = "
        "pp.perfil_id "
        "JOIN permisos pe ON pe.id = pp.permiso_id WHERE pe.codigo = "
        "'movil.acceder'"
    )
    assert [fila["nombre"] for fila in filas] == ["Alumno"]


def test_permiso_movil_visible_en_perfiles(cliente):
    """
    Descripcion:
        Prueba: HU-01-07: el permiso del portal movil se ve en Perfiles y
        permisos.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba sin sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    entrar(cliente, "admin", "Admin123")
    assert "Acceder al portal móvil" in cliente.get("/perfiles").get_data(
        as_text=True
    )


def test_manifest_para_pantalla_de_inicio(cliente):
    """
    Descripcion:
        Prueba: El manifest permite agregar el portal a la pantalla de inicio
        del celular.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba sin sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    manifest = cliente.get("/static/manifest.json").get_json()
    assert manifest["start_url"] == "/movil"
    assert manifest["display"] == "standalone"
