"""
============================================================
Archivo:      tests/test_devoluciones.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Pruebas de devoluciones (Sprint 2):
        HU-02-07 Registro de devolucion
        HU-02-08 Generacion de multas por entrega extemporanea, dano y
                 perdida

    Datos de prueba que se usan: EJ-0002 (alumno, a tiempo, LIB-001 en
    pesos), EJ-0019 (jlopez, vencido hace 3 dias, LIB-010 en dolares),
    EJ-0006 (profesor, a tiempo), EJ-0027 (pmartinez, LIB-015 sin precio)
    y EJ-0021 (profesor, LIB-011 con lista de espera).

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


def devolver(cliente, ejemplar, **datos):
    """
    Descripcion:
        Envia el formulario de la devolucion.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente con sesion.
        ejemplar (str): codigo del ejemplar.
        **datos (dict): resultado, observaciones, monto_dano y
            monto_reposicion.

    Salida:
        flask.Response: respuesta del registro.
    """
    return cliente.post(
        "/devoluciones/registrar", data={"ejemplar": ejemplar, **datos}
    )


def leer_cierre(app, ejemplar):
    """
    Descripcion:
        Lee como quedo el ultimo prestamo del ejemplar, el ejemplar, su
        devolucion y sus multas.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        ejemplar (str): codigo del ejemplar.

    Salida:
        dict: estado_prestamo, estado_ejemplar, condicion (o None) y multas
        [(motivo, monto, descripcion, enviada)].
    """
    with app.app_context():
        fila = consultar(
            """
            SELECT p.id, p.estado AS estado_prestamo,
                   e.estado AS estado_ejemplar, d.condicion
            FROM prestamos p
            JOIN ejemplares e ON e.id = p.ejemplar_id
            LEFT JOIN devoluciones d ON d.prestamo_id = p.id
            WHERE e.codigo = ? ORDER BY p.id DESC LIMIT 1
            """,
            (ejemplar,),
            uno=True,
        )
        multas = consultar(
            "SELECT m.motivo, m.monto, m.descripcion, (SELECT COUNT(*) FROM "
            "envios_tesoreria en WHERE en.multa_id = m.id) AS envios "
            "FROM multas m WHERE m.prestamo_id = ? ORDER BY m.id",
            (fila["id"],),
        )
        return {
            "estado_prestamo": fila["estado_prestamo"],
            "estado_ejemplar": fila["estado_ejemplar"],
            "condicion": fila["condicion"],
            "multas": [
                (m["motivo"], m["monto"], m["descripcion"], m["envios"])
                for m in multas
            ],
        }


# ============================================================
# HU-02-07 REGISTRO DE DEVOLUCION
# ============================================================


@pytest.mark.parametrize(
    "ejemplar, codigo, mensaje",
    [
        ("", 400, "Captura el código del ejemplar"),
        ("EJ-0099", 404, "No existe un ejemplar con el código EJ-0099"),
        (
            "EJ-0001",
            409,
            "El ejemplar EJ-0001 no tiene un préstamo activo (estado: "
            "Disponible)",
        ),
    ],
)
def test_ejemplar_sin_prestamo(biblio, ejemplar, codigo, mensaje):
    """
    Descripcion:
        Prueba: HU-02-07 · Ejemplar inexistente o sin prestamo activo: no se
        puede registrar la devolucion.

    Parametros:
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.
        ejemplar (str): codigo capturado.
        codigo (int): codigo HTTP esperado.
        mensaje (str): texto esperado.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = biblio.get(
        "/devoluciones", query_string={"ejemplar": ejemplar}
    )
    assert respuesta.status_code == codigo
    assert mensaje in respuesta.get_data(as_text=True)


def test_captura_muestra_prestamo_y_multas(biblio):
    """
    Descripcion:
        Prueba: HU-02-07 · Al buscar el ejemplar (en minusculas tambien) se
        ve el prestamo, los dias de retraso y la multa que se generaria.

    Parametros:
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    pagina = biblio.get("/devoluciones?ejemplar=ej-0019").get_data(
        as_text=True
    )
    assert "Introducción a los algoritmos" in pagina
    assert "Vencido hace 3 día(s)" in pagina
    assert "$15.00 MXN" in pagina
    # Reposicion: 95.00 USD x 18.27 (tipo de cambio mas reciente).
    assert "$1,735.65 MXN" in pagina


def test_devolucion_a_tiempo_sin_multas(app, biblio):
    """
    Descripcion:
        Prueba: HU-02-07 · Devolucion en buen estado y a tiempo: el prestamo
        queda Devuelto, el ejemplar Disponible y no hay multas.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = devolver(biblio, "EJ-0002", resultado="bueno")
    assert respuesta.status_code == 302
    assert respuesta.location.endswith("/devoluciones/1")
    pagina = biblio.get(respuesta.location).get_data(as_text=True)
    assert "registrada sin multas" in pagina
    assert leer_cierre(app, "EJ-0002") == {
        "estado_prestamo": "Devuelto",
        "estado_ejemplar": "Disponible",
        "condicion": "Bueno",
        "multas": [],
    }


def test_devolucion_ya_registrada(biblio):
    """
    Descripcion:
        Prueba: HU-02-07 · Si la devolucion ya se registro, el ejemplar ya no
        tiene prestamo activo y no se registra dos veces.

    Parametros:
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    assert devolver(biblio, "EJ-0002", resultado="bueno").status_code == 302
    respuesta = devolver(biblio, "EJ-0002", resultado="bueno")
    assert respuesta.status_code == 409
    assert "no tiene un préstamo activo" in respuesta.get_data(as_text=True)


def test_devolucion_libera_turno_de_lista_de_espera(biblio):
    """
    Descripcion:
        Prueba: HU-02-07 y HU-02-06 · Si el libro tiene lista de espera, al
        devolverlo se avisa que el ejemplar es para el turno 1.

    Parametros:
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = devolver(biblio, "EJ-0021", resultado="bueno")
    pagina = biblio.get(respuesta.location).get_data(as_text=True)
    assert "Este libro tiene lista de espera" in pagina
    assert "Hay 2 persona(s) esperando" in pagina
    espera = biblio.get("/espera").get_data(as_text=True)
    assert "Ejemplar disponible" in espera


def test_devoluciones_sin_permiso(cliente):
    """
    Descripcion:
        Prueba: Acceso sin autorizacion: el profesor no registra devoluciones
        ni ve las multas.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    entrar(cliente, "profesor", "Profe123")
    assert cliente.get("/devoluciones").status_code == 403
    assert devolver(cliente, "EJ-0002", resultado="bueno").status_code == 403
    assert cliente.get("/multas").status_code == 403


# ============================================================
# HU-02-08 GENERACION DE MULTAS
# ============================================================


def test_entrega_extemporanea_genera_multa_y_la_envia(app, biblio):
    """
    Descripcion:
        Prueba: HU-02-08 · Entrega extemporanea: 3 dias de retraso por $5.00
        del perfil Alumno; la multa se manda a Tesoreria (en modo
        demostracion queda el .eml).

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = devolver(biblio, "EJ-0019", resultado="bueno")
    pagina = biblio.get(respuesta.location).get_data(as_text=True)
    assert "Se generó 1 multa(s) por $15.00 MXN" in pagina
    assert "tesoreria@ducky.edu.mx" in pagina
    assert leer_cierre(app, "EJ-0019")["multas"] == [
        ("Retraso", 15, "3 día(s) de retraso × $5.00 por día", 1)
    ]
    carpeta = app.config["CARPETA_BOLETAS"]
    assert any(
        nombre.startswith("aviso_multa_PR-") for nombre in os.listdir(carpeta)
    )


def test_devolucion_con_dano(app, biblio):
    """
    Descripcion:
        Prueba: HU-02-08 · Dano: el ejemplar queda Danado y se genera la
        multa con el monto capturado (acepta $ y comas).

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = devolver(
        biblio,
        "EJ-0006",
        resultado="danado",
        observaciones="Portada rota",
        monto_dano="$1,150.50",
    )
    assert respuesta.status_code == 302
    assert leer_cierre(app, "EJ-0006") == {
        "estado_prestamo": "Devuelto",
        "estado_ejemplar": "Dañado",
        "condicion": "Dañado",
        "multas": [("Daño", 1150.5, "Daño: Portada rota", 1)],
    }


@pytest.mark.parametrize(
    "datos, campo_mensaje",
    [
        ({"resultado": ""}, "Elige qué pasó con el libro."),
        (
            {"resultado": "danado", "monto_dano": "150"},
            "Describe el daño que tiene el libro.",
        ),
        (
            {"resultado": "danado", "observaciones": "Rayado"},
            "Captura el monto por el daño",
        ),
        (
            {
                "resultado": "danado",
                "observaciones": "Rayado",
                "monto_dano": "-5",
            },
            "Captura el monto por el daño",
        ),
        (
            {"resultado": "bueno", "observaciones": "x" * 256},
            "Las observaciones admiten hasta 255 caracteres.",
        ),
    ],
)
def test_devolucion_con_datos_incompletos(app, biblio, datos, campo_mensaje):
    """
    Descripcion:
        Prueba: HU-02-07 y HU-02-08 · Datos incompletos: no se registra nada
        y se marca el campo.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.
        datos (dict): lo capturado.
        campo_mensaje (str): mensaje esperado.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = devolver(biblio, "EJ-0006", **datos)
    assert respuesta.status_code == 422
    assert campo_mensaje in respuesta.get_data(as_text=True)
    assert leer_cierre(app, "EJ-0006")["estado_prestamo"] == "Activo"


def test_perdida_con_precio_en_pesos(app, biblio):
    """
    Descripcion:
        Prueba: HU-02-08 · Perdida: se cobra el ultimo precio del libro
        ($429.00, no el anterior de $389.00); el prestamo y el ejemplar
        quedan como Perdido y no hay registro de devolucion.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = devolver(biblio, "EJ-0002", resultado="perdido")
    pagina = biblio.get(respuesta.location).get_data(as_text=True)
    assert "Pérdida del préstamo" in pagina
    cierre = leer_cierre(app, "EJ-0002")
    assert cierre["estado_prestamo"] == "Perdido"
    assert cierre["estado_ejemplar"] == "Perdido"
    assert cierre["condicion"] is None
    assert [(m[0], m[1]) for m in cierre["multas"]] == [("Pérdida", 429)]


def test_perdida_en_dolares_y_vencida(app, biblio):
    """
    Descripcion:
        Prueba: HU-02-08 · Perdida de un libro con precio en dolares y ya
        vencido: se cobra el retraso y la reposicion con el tipo de cambio
        vigente.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    devolver(biblio, "EJ-0019", resultado="perdido")
    multas = leer_cierre(app, "EJ-0019")["multas"]
    assert [(m[0], m[1]) for m in multas] == [
        ("Retraso", 15),
        ("Pérdida", 1735.65),
    ]
    assert "95.00 USD × $18.2700" in multas[1][2]


def test_perdida_sin_precio_pide_el_costo(app, biblio):
    """
    Descripcion:
        Prueba: HU-02-08 · Libro sin precio registrado: se pide capturar el
        costo de reposicion.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente del bibliotecario.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = devolver(biblio, "EJ-0027", resultado="perdido")
    assert respuesta.status_code == 422
    assert "El libro no tiene precio registrado. Captura el costo" in (
        respuesta.get_data(as_text=True)
    )

    devolver(biblio, "EJ-0027", resultado="perdido", monto_reposicion="600")
    assert leer_cierre(app, "EJ-0027")["multas"] == [
        ("Pérdida", 600, "Reposición: costo capturado por el bibliotecario", 1)
    ]
