"""
============================================================
Archivo:      tests/test_multas.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Pruebas de multas (Sprint 2):
        HU-02-08 Envio de multas a Tesoreria y registro del pago
        HU-02-01 y HU-02-05 El usuario con multas pendientes no puede
                 pedir prestado ni renovar

    Datos de prueba: la multa 1 es de pmartinez ($30.00, pendiente y ya
    enviada); las multas 2 y 3 son del profesor y ya estan pagadas.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    13/11/2026
============================================================
"""

import pytest

from models.db import consultar
from tests.conftest import entrar
from utils import notificaciones


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


def leer_multa(app, multa_id):
    """
    Descripcion:
        Lee el estado de la multa, cuantas veces se envio y su pago.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        multa_id (int): id de la multa.

    Salida:
        dict: estado, envios y metodo de pago (o None).
    """
    with app.app_context():
        fila = consultar(
            """
            SELECT m.estado,
                   (SELECT COUNT(*) FROM envios_tesoreria en
                    WHERE en.multa_id = m.id) AS envios,
                   (SELECT pg.metodo FROM pagos_multa pg
                    WHERE pg.multa_id = m.id) AS metodo
            FROM multas m WHERE m.id = ?
            """,
            (multa_id,),
            uno=True,
        )
        return dict(fila)


# ============================================================
# LISTA Y ENVIO A TESORERIA
# ============================================================


def test_lista_de_multas(biblio):
    """
    Descripcion:
        Prueba: HU-02-08 · La lista muestra las pendientes con su envio a
        Tesoreria, y las pagadas en su propia vista.

    Parametros:
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    pendientes = biblio.get("/multas").get_data(as_text=True)
    assert "1 multa pendiente de pago" in pendientes
    assert "Pedro Martínez Soto" in pendientes
    assert "$30.00 MXN" in pendientes
    assert "Enviada" in pendientes

    pagadas = biblio.get("/multas?ver=pagadas").get_data(as_text=True)
    assert "2 multas pagadas" in pagadas
    assert "Daño: Pasta desprendida y hojas manchadas." in pagadas


def test_panel_muestra_multas_pendientes(biblio):
    """
    Descripcion:
        Prueba: HU-02-08 · El panel de inicio muestra las multas pendientes
        y el acceso a devoluciones.

    Parametros:
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    inicio = biblio.get("/inicio").get_data(as_text=True)
    assert "Multas pendientes ($30.00 MXN)" in inicio
    assert "Registrar devolución" in inicio


def test_aviso_de_multa_en_pdf(biblio):
    """
    Descripcion:
        Prueba: HU-02-08 · El aviso para Tesoreria se descarga en PDF.

    Parametros:
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = biblio.get("/multas/1/aviso.pdf")
    assert respuesta.status_code == 200
    assert respuesta.mimetype == "application/pdf"
    assert respuesta.data.startswith(b"%PDF")


def test_volver_a_enviar_a_tesoreria(app, biblio):
    """
    Descripcion:
        Prueba: HU-02-08 · Una multa pendiente se puede volver a mandar a
        Tesoreria; queda el historial de envios.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = biblio.post("/multas/1/tesoreria")
    assert respuesta.status_code == 302
    pagina = biblio.get(respuesta.location).get_data(as_text=True)
    assert "Modo demostración: el aviso de $30.00 MXN" in pagina
    assert leer_multa(app, 1)["envios"] == 2


def test_no_se_envia_multa_pagada(app, biblio):
    """
    Descripcion:
        Prueba: HU-02-08 · Una multa pagada ya no se manda a Tesoreria.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = biblio.post("/multas/2/tesoreria")
    assert respuesta.status_code == 409
    assert leer_multa(app, 2)["envios"] == 1


def test_falla_del_correo_y_envio_pendiente(app, biblio, monkeypatch):
    """
    Descripcion:
        Prueba: HU-02-08 · Si el correo falla al devolver, la devolucion se
        registra y la multa queda sin enviar; despues se mandan todas las
        pendientes desde la lista.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.
        monkeypatch (pytest.MonkeyPatch): reemplaza el envio de correo.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    enviar_de_verdad = notificaciones.enviar_correo

    def fallar(*_args, **_kwargs):
        raise notificaciones.ErrorEnvio("No se pudo conectar.")

    monkeypatch.setattr(notificaciones, "enviar_correo", fallar)
    respuesta = biblio.post(
        "/devoluciones/registrar",
        data={"ejemplar": "EJ-0019", "resultado": "bueno"},
    )
    pagina = biblio.get(respuesta.location).get_data(as_text=True)
    assert "No se pudo enviar a Tesorería" in pagina
    assert "Sin enviar" in pagina
    assert leer_multa(app, 4)["envios"] == 0

    # Ya con correo, se mandan desde la lista.
    monkeypatch.setattr(notificaciones, "enviar_correo", enviar_de_verdad)
    lista = biblio.get("/multas").get_data(as_text=True)
    assert "Enviar 1 a Tesorería" in lista
    respuesta = biblio.post("/multas/tesoreria")
    pagina = biblio.get(respuesta.location).get_data(as_text=True)
    assert "1 aviso(s) de 1 multa(s)" in pagina
    assert leer_multa(app, 4)["envios"] == 1
    respuesta = biblio.post("/multas/tesoreria")
    assert "ya se mandaron a Tesorería" in biblio.get(
        respuesta.location
    ).get_data(as_text=True)


# ============================================================
# PAGO Y ADEUDO DEL USUARIO
# ============================================================


def test_usuario_con_multa_no_puede_pedir_prestado(biblio):
    """
    Descripcion:
        Prueba: HU-02-01 · Usuario con multas pendientes: no se le presta.

    Parametros:
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = biblio.post(
        "/prestamos/nuevo", data={"usuario": "N20500", "ejemplar": "EJ-0011"}
    )
    assert respuesta.status_code == 422
    assert (
        "Pedro Martínez Soto tiene 1 multa(s) pendiente(s) por $30.00 MXN"
        in respuesta.get_data(as_text=True)
    )


def test_usuario_con_multa_no_puede_renovar(biblio):
    """
    Descripcion:
        Prueba: HU-02-05 · Si el usuario devuelve un libro danado, queda con
        multa pendiente y ya no puede renovar sus otros prestamos.

    Parametros:
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    # El alumno se lleva otro libro (prestamo 8) y devuelve danado el 1.
    biblio.post(
        "/prestamos/nuevo", data={"usuario": "600101", "ejemplar": "EJ-0011"}
    )
    assert biblio.post("/prestamos/confirmar").location.endswith(
        "/prestamos/8"
    )
    biblio.post(
        "/devoluciones/registrar",
        data={
            "ejemplar": "EJ-0002",
            "resultado": "danado",
            "observaciones": "Hojas arrancadas",
            "monto_dano": "200",
        },
    )
    respuesta = biblio.post("/prestamos/8/renovar")
    assert respuesta.status_code == 422
    assert "multa(s) pendiente(s) por $200.00 MXN" in respuesta.get_data(
        as_text=True
    )


@pytest.mark.parametrize(
    "datos, mensaje",
    [
        ({}, "Elige cómo se pagó la multa."),
        (
            {"metodo": "Transferencia"},
            "Captura el folio del ticket o de la transferencia.",
        ),
        (
            {"metodo": "Tarjeta", "referencia": "x" * 51},
            "La referencia admite hasta 50 caracteres.",
        ),
    ],
)
def test_pago_con_datos_incompletos(app, biblio, datos, mensaje):
    """
    Descripcion:
        Prueba: Registro del pago con datos incompletos: la multa sigue
        pendiente.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.
        datos (dict): lo capturado.
        mensaje (str): mensaje esperado.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = biblio.post("/multas/1/pago", data=datos)
    assert respuesta.status_code == 422
    assert mensaje in respuesta.get_data(as_text=True)
    assert leer_multa(app, 1)["estado"] == "Pendiente"


def test_pago_libera_el_adeudo(app, biblio):
    """
    Descripcion:
        Prueba: Al registrar el pago la multa queda Pagada y el usuario ya
        puede pedir prestado; no se puede pagar dos veces.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = biblio.post("/multas/1/pago", data={"metodo": "Efectivo"})
    assert respuesta.status_code == 302
    pagina = biblio.get(respuesta.location).get_data(as_text=True)
    assert "Pago de $30.00 MXN registrado para Pedro Martínez Soto." in pagina
    assert leer_multa(app, 1) == {
        "estado": "Pagada",
        "envios": 1,
        "metodo": "Efectivo",
    }
    assert (
        biblio.post("/multas/1/pago", data={"metodo": "Efectivo"}).status_code
        == 409
    )

    respuesta = biblio.post(
        "/prestamos/nuevo", data={"usuario": "N20500", "ejemplar": "EJ-0011"}
    )
    assert respuesta.status_code == 302
