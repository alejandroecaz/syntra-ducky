"""
============================================================
Archivo:      tests/test_prestamos.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Pruebas de prestamos (Sprint 2):
        HU-02-01 Validacion del solicitante
        HU-02-02 Validacion del libro
        HU-02-03 Registro del prestamo
        HU-02-04 Boleta de prestamo (correo, WhatsApp e impresion)
        HU-02-05 Renovacion de prestamo

    conftest.py deja vacia la cuenta de correo y Twilio, asi que ninguna
    prueba envia nada real: el correo se guarda como .eml en una carpeta
    temporal y WhatsApp regresa el enlace wa.me.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    13/11/2026
============================================================
"""

import os
from datetime import date, timedelta
from urllib.parse import unquote

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


def capturar(cliente, usuario, ejemplar):
    """
    Descripcion:
        Envia el formulario de captura del prestamo.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente con sesion.
        usuario (str): matricula o cuenta.
        ejemplar (str): codigo del ejemplar.

    Salida:
        flask.Response: respuesta de la captura.
    """
    return cliente.post(
        "/prestamos/nuevo", data={"usuario": usuario, "ejemplar": ejemplar}
    )


def prestar(cliente, usuario, ejemplar):
    """
    Descripcion:
        Captura y confirma un prestamo.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente con sesion.
        usuario (str): matricula o cuenta.
        ejemplar (str): codigo del ejemplar.

    Salida:
        flask.Response: respuesta de la confirmacion (redireccion a la
        boleta).
    """
    assert capturar(cliente, usuario, ejemplar).status_code == 302
    return cliente.post("/prestamos/confirmar")


def obtener_estado_ejemplar(app, codigo):
    """
    Descripcion:
        Lee el estado del ejemplar en la base de datos.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        codigo (str): codigo del ejemplar.

    Salida:
        str: estado del ejemplar.
    """
    with app.app_context():
        return consultar(
            "SELECT estado FROM ejemplares WHERE codigo = ?",
            (codigo,),
            uno=True,
        )["estado"]


def listar_comprobantes(app, prestamo_id):
    """
    Descripcion:
        Lee las boletas emitidas de un prestamo.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        prestamo_id (int): id del prestamo.

    Salida:
        list[tuple[str, str]]: (medio, destino) de cada boleta.
    """
    with app.app_context():
        return [
            (fila["medio"], fila["destino"])
            for fila in consultar(
                "SELECT medio, destino FROM comprobantes_prestamo "
                "WHERE prestamo_id = ? ORDER BY id",
                (prestamo_id,),
            )
        ]


# ============================================================
# HU-02-01 VALIDACION DEL SOLICITANTE
# ============================================================


@pytest.mark.parametrize(
    "usuario, mensaje",
    [
        ("", "Captura la matrícula o la cuenta del usuario."),
        ("999999", "No hay ningún usuario registrado"),
        ("deshabilitado", "está deshabilitada"),
        ("visitante", "no tiene préstamos a domicilio autorizados"),
        ("jlopez", "préstamo(s) vencido(s)"),
    ],
)
def test_solicitante_que_no_puede_pedir_prestado(biblio, usuario, mensaje):
    """
    Descripcion:
        Prueba: HU-02-01 · Usuario vacio, inexistente, deshabilitado, con
        perfil sin prestamos o con prestamos vencidos.

    Parametros:
        biblio (flask.testing.FlaskClient): cliente con sesion.
        usuario (str): usuario capturado (parametrizado).
        mensaje (str): texto esperado del error (parametrizado).

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = capturar(biblio, usuario, "EJ-0011")
    assert respuesta.status_code == 422
    assert mensaje in respuesta.get_data(as_text=True)


def test_limite_de_prestamos_del_perfil(biblio):
    """
    Descripcion:
        Prueba: HU-02-01 · Limite de prestamos: el alumno puede tener 3 a la
        vez (ya tiene 1 de los datos de prueba).

    Parametros:
        biblio (flask.testing.FlaskClient): cliente con sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    assert prestar(biblio, "600101", "EJ-0011").status_code == 302
    assert prestar(biblio, "600101", "EJ-0017").status_code == 302
    respuesta = capturar(biblio, "600101", "EJ-0023")
    assert respuesta.status_code == 422
    assert "el máximo para el perfil Alumno" in respuesta.get_data(
        as_text=True
    )


# ============================================================
# HU-02-02 VALIDACION DEL LIBRO
# ============================================================


@pytest.mark.parametrize(
    "ejemplar, mensaje",
    [
        ("", "Captura el código del ejemplar"),
        ("EJ-9999", "No existe un ejemplar con el código EJ-9999"),
        ("EJ-0003", "ya tiene prestado un ejemplar de"),
        ("EJ-0006", "no está disponible (estado: Prestado)"),
        ("EJ-0013", "no está disponible (estado: Perdido)"),
        ("EJ-0022", "solo se consulta dentro de la biblioteca"),
        ("EJ-0025", "está dado de baja"),
    ],
)
def test_ejemplar_que_no_se_puede_prestar(biblio, ejemplar, mensaje):
    """
    Descripcion:
        Prueba: HU-02-02 · Ejemplar vacio, inexistente, ya prestado,
        perdido, de acceso reservado, de un libro dado de baja o de un libro
        que el usuario ya tiene (Mariana tiene EJ-0002 de LIB-001).

    Parametros:
        biblio (flask.testing.FlaskClient): cliente con sesion.
        ejemplar (str): codigo capturado (parametrizado).
        mensaje (str): texto esperado del error (parametrizado).

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = capturar(biblio, "600101", ejemplar)
    assert respuesta.status_code == 422
    assert mensaje in respuesta.get_data(as_text=True)


# ============================================================
# HU-02-03 REGISTRO DEL PRESTAMO
# ============================================================


def test_registro_del_prestamo(app, biblio):
    """
    Descripcion:
        Prueba: HU-02-03 · Registro exitoso: se pide confirmacion, se asigna
        folio, la fecha de devolucion usa los dias del perfil y el ejemplar
        queda como Prestado.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente con sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    # La captura en minusculas tambien encuentra el ejemplar.
    assert capturar(biblio, "alumno", "ej-0011").status_code == 302
    confirmacion = biblio.get("/prestamos/confirmar").get_data(as_text=True)
    vencimiento = (date.today() + timedelta(days=7)).strftime("%d/%m/%Y")
    assert "Cálculo de una variable" in confirmacion
    assert vencimiento in confirmacion
    # Antes de confirmar el ejemplar sigue disponible.
    assert obtener_estado_ejemplar(app, "EJ-0011") == "Disponible"

    respuesta = biblio.post("/prestamos/confirmar")
    assert respuesta.status_code == 302
    assert respuesta.location.endswith("/prestamos/6")
    assert obtener_estado_ejemplar(app, "EJ-0011") == "Prestado"
    boleta = biblio.get(respuesta.location).get_data(as_text=True)
    assert f"Préstamo PR-{date.today().year}-0006 registrado" in boleta
    assert vencimiento in boleta


def test_confirmar_sin_captura(biblio):
    """
    Descripcion:
        Prueba: HU-02-03 · Confirmar sin un prestamo en captura regresa al
        formulario.

    Parametros:
        biblio (flask.testing.FlaskClient): cliente con sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = biblio.post("/prestamos/confirmar")
    assert respuesta.status_code == 302
    assert respuesta.location.endswith("/prestamos/nuevo")


def test_ficha_del_libro_ofrece_prestar(app, biblio):
    """
    Descripcion:
        Prueba: HU-02-03 · La ficha del libro tiene el boton Prestar en los
        ejemplares disponibles y lleva el codigo al formulario.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente con sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    with app.app_context():
        libro_id = consultar(
            "SELECT id FROM libros WHERE clave = 'LIB-001'", uno=True
        )["id"]
    ficha = biblio.get(f"/catalogo/{libro_id}").get_data(as_text=True)
    assert "/prestamos/nuevo?ejemplar=EJ-0001" in ficha
    # EJ-0002 esta prestado: no se ofrece.
    assert "/prestamos/nuevo?ejemplar=EJ-0002" not in ficha
    formulario = biblio.get("/prestamos/nuevo?ejemplar=EJ-0001")
    assert 'value="EJ-0001"' in formulario.get_data(as_text=True)


@pytest.mark.parametrize("cuenta, contrasena", [("alumno", "Alumno123")])
def test_prestamos_sin_permiso(cliente, cuenta, contrasena):
    """
    Descripcion:
        Prueba: Acceso sin autorizacion: un alumno no puede registrar
        prestamos ni ver boletas.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba.
        cuenta (str): cuenta (parametrizada).
        contrasena (str): contrasena (parametrizada).

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    entrar(cliente, cuenta, contrasena)
    for ruta in ("/prestamos", "/prestamos/nuevo", "/prestamos/1"):
        assert cliente.get(ruta).status_code == 403


# ============================================================
# HU-02-04 BOLETA DE PRESTAMO
# ============================================================


def test_boleta_en_pdf(biblio):
    """
    Descripcion:
        Prueba: HU-02-04 · Descarga de la boleta en PDF.

    Parametros:
        biblio (flask.testing.FlaskClient): cliente con sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = biblio.get("/prestamos/1/boleta.pdf")
    assert respuesta.status_code == 200
    assert respuesta.mimetype == "application/pdf"
    assert respuesta.data.startswith(b"%PDF")
    assert "boleta_PR-" in respuesta.headers["Content-Disposition"]


def test_boleta_por_correo_en_modo_demostracion(app, biblio):
    """
    Descripcion:
        Prueba: HU-02-04 · Envio por correo: sin cuenta configurada el correo
        se guarda como .eml con el PDF adjunto y se registra la boleta.

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
        "/prestamos/1/boleta/correo", data={"correo": "mariana@gmail.com"}
    )
    assert respuesta.status_code == 302
    assert "Modo demostración" in biblio.get(respuesta.location).get_data(
        as_text=True
    )

    carpeta = app.config["CARPETA_BOLETAS"]
    archivos = os.listdir(carpeta)
    assert len(archivos) == 1 and archivos[0].endswith(".eml")
    with open(os.path.join(carpeta, archivos[0]), encoding="utf-8") as eml:
        contenido = eml.read()
    assert "To: mariana@gmail.com" in contenido
    assert "application/pdf" in contenido
    assert listar_comprobantes(app, 1) == [("Email", "mariana@gmail.com")]


def test_boleta_por_correo_invalido(app, biblio):
    """
    Descripcion:
        Prueba: HU-02-04 · Correo invalido: no se envia ni se registra nada.

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
        "/prestamos/1/boleta/correo", data={"correo": "mariana"}
    )
    assert respuesta.status_code == 400
    assert "Escribe un correo válido" in respuesta.get_data(as_text=True)
    assert listar_comprobantes(app, 1) == []


def test_boleta_por_whatsapp_con_enlace(app, biblio):
    """
    Descripcion:
        Prueba: HU-02-04 · Envio por WhatsApp sin API: abre wa.me con la lada
        de Mexico y la boleta escrita, y registra la boleta.

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
        "/prestamos/1/boleta/whatsapp", data={"telefono": "81 1234-5678"}
    )
    assert respuesta.status_code == 302
    assert respuesta.location.startswith("https://wa.me/528112345678?text=")
    mensaje = unquote(respuesta.location)
    assert "Boleta de préstamo PR-" in mensaje
    assert "Cien años de soledad" in mensaje
    assert listar_comprobantes(app, 1) == [("WhatsApp", "+528112345678")]


def test_boleta_por_whatsapp_telefono_invalido(app, biblio):
    """
    Descripcion:
        Prueba: HU-02-04 · Telefono invalido: no se abre WhatsApp ni se
        registra nada.

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
        "/prestamos/1/boleta/whatsapp", data={"telefono": "12345"}
    )
    assert respuesta.status_code == 400
    assert "celular de 10 dígitos" in respuesta.get_data(as_text=True)
    assert listar_comprobantes(app, 1) == []


@pytest.mark.parametrize(
    "impresora, codigo, medios",
    [
        ("recepcion", 200, [("Impresión", "HP LaserJet Pro · Recepción")]),
        ("sala", 503, []),
        ("", 400, []),
    ],
)
def test_boleta_impresa(app, biblio, impresora, codigo, medios):
    """
    Descripcion:
        Prueba: HU-02-04 · Boleta impresa en una impresora en linea,
        impresora fuera de linea y sin elegir impresora.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente con sesion.
        impresora (str): id de la impresora (parametrizado).
        codigo (int): codigo HTTP esperado (parametrizado).
        medios (list): boletas que deben quedar registradas (parametrizado).

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    respuesta = biblio.post(
        "/prestamos/1/boleta/imprimir", data={"impresora": impresora}
    )
    assert respuesta.status_code == codigo
    imprime = "data-imprimir-al-cargar" in respuesta.get_data(as_text=True)
    assert imprime == (codigo == 200)
    assert listar_comprobantes(app, 1) == medios


# ============================================================
# HU-02-05 RENOVACION DE PRESTAMO
# ============================================================


def leer_prestamo(app, prestamo_id):
    """
    Descripcion:
        Lee la fecha de devolucion y las renovaciones del prestamo.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        prestamo_id (int): id del prestamo.

    Salida:
        tuple[str, int]: fecha de devolucion y numero de renovaciones.
    """
    with app.app_context():
        fila = consultar(
            "SELECT fecha_vencimiento, (SELECT COUNT(*) FROM renovaciones "
            "WHERE prestamo_id = p.id) AS renovaciones FROM prestamos p "
            "WHERE id = ?",
            (prestamo_id,),
            uno=True,
        )
        return fila["fecha_vencimiento"], fila["renovaciones"]


def test_renovacion_exitosa(app, biblio):
    """
    Descripcion:
        Prueba: HU-02-05 · Renovacion exitosa: la devolucion se recorre los
        dias del perfil (7 para alumno), queda en el historial y la boleta
        muestra la renovacion usada.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente con sesion.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    anterior, _ = leer_prestamo(app, 1)
    nueva = date.fromisoformat(anterior) + timedelta(days=7)

    respuesta = biblio.post("/prestamos/1/renovar")
    assert respuesta.status_code == 302
    assert leer_prestamo(app, 1) == (nueva.isoformat(), 1)
    boleta = biblio.get(respuesta.location).get_data(as_text=True)
    assert f"renovado hasta el {nueva:%d/%m/%Y}" in boleta
    assert "1 de 2" in boleta


@pytest.mark.parametrize(
    "prestamo_id, mensaje",
    [
        (2, "en la lista de espera de este libro"),
        (3, "El préstamo está vencido"),
        (4, "Ya se usaron las 2 renovaciones"),
    ],
)
def test_renovacion_rechazada(app, biblio, prestamo_id, mensaje):
    """
    Descripcion:
        Prueba: HU-02-05 · No se renueva un libro con lista de espera
        (LIB-003), un prestamo vencido (jlopez) ni uno sin renovaciones
        disponibles (pmartinez ya uso 2 de 2).

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        biblio (flask.testing.FlaskClient): cliente con sesion.
        prestamo_id (int): prestamo (parametrizado).
        mensaje (str): motivo esperado (parametrizado).

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    antes = leer_prestamo(app, prestamo_id)
    respuesta = biblio.post(f"/prestamos/{prestamo_id}/renovar")
    assert respuesta.status_code == 422
    assert mensaje in respuesta.get_data(as_text=True)
    assert leer_prestamo(app, prestamo_id) == antes


def test_renovacion_sin_permiso(cliente):
    """
    Descripcion:
        Prueba: Acceso sin autorizacion: un profesor no puede renovar.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    entrar(cliente, "profesor", "Profe123")
    assert cliente.post("/prestamos/1/renovar").status_code == 403
