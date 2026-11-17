"""
============================================================
Archivo:      tests/test_chatbot.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Pruebas del chatbot (HU-02-09): preguntas por defecto y abiertas,
    conversacion guardada, consultas del usuario en sesion, respuestas con
    IA y modo de respaldo.

    Ninguna prueba usa la API de Claude: conftest.py deja vacia la llave
    (modo de respaldo) y las pruebas con IA reemplazan la peticion por
    respuestas simuladas.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    13/11/2026
============================================================
"""

import json
from types import SimpleNamespace

import anthropic
import httpx
import pytest

from models.db import consultar
from services import chatbot_servicio
from tests.conftest import entrar, obtener_id_libro
from utils import claude


def preguntar(cliente, texto):
    """
    Descripcion:
        Manda una pregunta al chatbot.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente con sesion.
        texto (str): pregunta.

    Salida:
        flask.Response: respuesta JSON.
    """
    return cliente.post("/chatbot/mensajes", json={"mensaje": texto})


def leer_mensajes(app):
    """
    Descripcion:
        Lee los mensajes guardados de todas las conversaciones.

    Parametros:
        app (flask.Flask): aplicacion de prueba.

    Salida:
        list[tuple]: (conversacion, emisor, intencion, libro_id).
    """
    with app.app_context():
        return [
            tuple(fila)
            for fila in consultar(
                "SELECT conversacion_id, emisor, intencion, libro_id "
                "FROM chatbot_mensajes ORDER BY id"
            )
        ]


def bloque_texto(texto):
    """
    Descripcion:
        Bloque de texto simulado de la respuesta del modelo.

    Parametros:
        texto (str): texto.

    Salida:
        types.SimpleNamespace: bloque.
    """
    return SimpleNamespace(type="text", text=texto)


def bloque_herramienta(nombre, entrada, identificador="toolu_1"):
    """
    Descripcion:
        Bloque simulado en el que el modelo pide usar una herramienta.

    Parametros:
        nombre (str): herramienta.
        entrada (dict): parametros.
        identificador (str): id del bloque.

    Salida:
        types.SimpleNamespace: bloque.
    """
    return SimpleNamespace(
        type="tool_use", name=nombre, input=entrada, id=identificador
    )


def simular_claude(monkeypatch, respuestas):
    """
    Descripcion:
        Activa el modo con IA y reemplaza la peticion a Claude por
        respuestas fijas, en orden. Guarda lo que se le mando.

    Parametros:
        monkeypatch (pytest.MonkeyPatch): reemplaza funciones.
        respuestas (list): SimpleNamespace(stop_reason, content) o una
            excepcion para lanzar.

    Salida:
        list[dict]: system, mensajes y herramientas de cada peticion.
    """
    llamadas = []
    pendientes = list(respuestas)

    def responder(system, mensajes, herramientas):
        llamadas.append(
            {
                "system": system,
                "mensajes": list(mensajes),
                "herramientas": herramientas,
            }
        )
        siguiente = pendientes.pop(0)
        if isinstance(siguiente, Exception):
            raise siguiente
        return siguiente

    monkeypatch.setattr(claude, "verificar_configurado", lambda: True)
    monkeypatch.setattr(claude, "pedir_respuesta", responder)
    return llamadas


# ============================================================
# VENTANA DE CHAT Y PREGUNTAS POR DEFECTO
# ============================================================


def test_chat_en_todas_las_pantallas(cliente):
    """
    Descripcion:
        Prueba: HU-02-09 · El boton del chat aparece en la app para quien
        inicio sesion, y no en el inicio de sesion.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    assert "data-chatbot" not in cliente.get("/login").get_data(as_text=True)
    entrar(cliente, "alumno", "Alumno123")
    pagina = cliente.get("/inicio").get_data(as_text=True)
    assert "data-chatbot" in pagina
    assert "Pregúntale a Ducky" in pagina


def test_preguntas_sugeridas_y_modo_de_respaldo(cliente):
    """
    Descripcion:
        Prueba: HU-02-09 · Sin llave de la API, el chat dice que esta en modo
        de respaldo y ofrece las preguntas por defecto.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    entrar(cliente, "alumno", "Alumno123")
    datos = cliente.get("/chatbot/mensajes").json
    assert datos["modo"] == "respaldo"
    assert datos["mensajes"] == []
    assert "¿Para qué sirve el sistema?" in datos["sugerencias"]


def test_chat_sin_sesion(cliente):
    """
    Descripcion:
        Prueba: HU-02-09 · Sin sesion no se puede usar el chat.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    assert cliente.get("/chatbot/mensajes").status_code == 302
    assert preguntar(cliente, "hola").status_code == 302


# ============================================================
# MODO DE RESPALDO (SIN IA)
# ============================================================


@pytest.mark.parametrize(
    "pregunta, esperado, intencion",
    [
        (
            "¿Para qué sirve el sistema?",
            "en una sola plataforma",
            "orientacion",
        ),
        ("¿Qué incluye el sistema?", "devoluciones y multas", "orientacion"),
        ("¿En qué plataformas funciona?", "portal móvil", "orientacion"),
        (
            "¿Cuántos libros puedo pedir y por cuántos días?",
            "Con tu perfil Profesor puedes llevarte hasta 5 libros por 14 "
            "días",
            "orientacion",
        ),
        ("¿Cómo renuevo un libro?", "La renovación la hace", "orientacion"),
        ("¿Qué préstamos tengo?", "Patrones de diseño", "consultar_prestamo"),
        (
            "¿Cuándo debo devolver el libro?",
            "Patrones de diseño",
            "consultar_prestamo",
        ),
        (
            "¿Tengo multas?",
            "Tienes multas pendientes por $30.00 MXN",
            "consultar_multa",
        ),
        (
            "¿Tienen Cien años de soledad?",
            "Cien años de soledad (LIB-001): 2 de 3 ejemplar(es) "
            "disponible(s) en Sala General",
            "buscar_libro",
        ),
        (
            "cuantos ejemplares de cien años de soledad hay",
            "Cien años de soledad (LIB-001): 2 de 3 ejemplar(es)",
            "buscar_libro",
        ),
        (
            "¿Hay algo de García Márquez?",
            "Cien años de soledad (LIB-001)",
            "buscar_libro",
        ),
        (
            "¿Qué onda?",
            "No encontré respuesta para eso en modo básico. Puedo contarte",
            None,
        ),
    ],
)
def test_respuestas_de_respaldo(app, cliente, pregunta, esperado, intencion):
    """
    Descripcion:
        Prueba: HU-02-09 · Modo de respaldo: reconoce la pregunta y contesta
        con la informacion del sistema y los datos de pmartinez.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        cliente (flask.testing.FlaskClient): cliente de prueba.
        pregunta (str): pregunta.
        esperado (str): texto que debe traer la respuesta.
        intencion (str o None): intencion guardada (None = orientacion).

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    entrar(cliente, "pmartinez", "Profe123")
    respuesta = preguntar(cliente, pregunta)
    assert respuesta.status_code == 200
    assert respuesta.json["modo"] == "respaldo"
    assert esperado in respuesta.json["respuesta"]
    assert leer_mensajes(app)[-1][2] == (intencion or "orientacion")


def test_solo_ve_sus_propios_datos(cliente):
    """
    Descripcion:
        Prueba: HU-02-09 · Cada usuario solo ve sus prestamos y multas: la
        alumna no ve la multa de pmartinez.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    entrar(cliente, "alumno", "Alumno123")
    multas = preguntar(cliente, "¿Tengo multas?").json["respuesta"]
    assert "No tienes multas pendientes" in multas
    prestamos = preguntar(cliente, "¿Qué préstamos tengo?").json["respuesta"]
    assert "Cien años de soledad" in prestamos
    assert "Patrones de diseño" not in prestamos


@pytest.mark.parametrize("texto", ["", "   ", "x" * 501])
def test_pregunta_vacia_o_muy_larga(app, cliente, texto):
    """
    Descripcion:
        Prueba: HU-02-09 · Pregunta vacia o de mas de 500 caracteres: no se
        guarda nada.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        cliente (flask.testing.FlaskClient): cliente de prueba.
        texto (str): pregunta.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    entrar(cliente, "alumno", "Alumno123")
    respuesta = preguntar(cliente, texto)
    assert respuesta.status_code == 422
    assert leer_mensajes(app) == []


def test_conversacion_guardada_y_nueva(app, cliente):
    """
    Descripcion:
        Prueba: HU-02-09 · Las preguntas y respuestas se guardan en la
        conversacion, se recuperan al abrir el chat en otra pantalla y
        "Nueva conversacion" la cierra.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        cliente (flask.testing.FlaskClient): cliente de prueba.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    entrar(cliente, "alumno", "Alumno123")
    preguntar(cliente, "¿Para qué sirve el sistema?")
    preguntar(cliente, "¿Tienen Cien años de soledad?")
    datos = cliente.get("/chatbot/mensajes").json
    assert [m["emisor"] for m in datos["mensajes"]] == [
        "Usuario",
        "Chatbot",
        "Usuario",
        "Chatbot",
    ]
    libro = obtener_id_libro(app, "LIB-001")
    assert leer_mensajes(app)[-1] == (1, "Chatbot", "buscar_libro", libro)

    assert cliente.post("/chatbot/nueva").status_code == 200
    assert cliente.get("/chatbot/mensajes").json["mensajes"] == []
    with app.app_context():
        conversacion = consultar(
            "SELECT estado, fecha_fin FROM chatbot_conversaciones",
            uno=True,
        )
    assert conversacion["estado"] == "Cerrada"
    assert conversacion["fecha_fin"]

    preguntar(cliente, "hola")
    assert leer_mensajes(app)[-1][0] == 2


# ============================================================
# RESPUESTAS CON IA (SIMULADAS)
# ============================================================


def test_respuesta_con_ia_consulta_el_catalogo(app, cliente, monkeypatch):
    """
    Descripcion:
        Prueba: HU-02-09 · Con IA: el modelo pide buscar el libro, recibe el
        resultado del catalogo y contesta; se guarda la intencion y el
        libro.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        cliente (flask.testing.FlaskClient): cliente de prueba.
        monkeypatch (pytest.MonkeyPatch): simula Claude.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    llamadas = simular_claude(
        monkeypatch,
        [
            SimpleNamespace(
                stop_reason="tool_use",
                content=[
                    bloque_herramienta("buscar_libros", {"texto": "soledad"})
                ],
            ),
            SimpleNamespace(
                stop_reason="end_turn",
                content=[
                    bloque_texto("Sí, hay 2 ejemplares en Sala General.")
                ],
            ),
        ],
    )
    entrar(cliente, "alumno", "Alumno123")
    respuesta = preguntar(cliente, "¿Tienen el de García Márquez?")
    assert respuesta.json == {
        "respuesta": "Sí, hay 2 ejemplares en Sala General.",
        "modo": "ia",
        "aviso": None,
    }

    # Instrucciones: lo fijo va en cache y al final el usuario en sesion.
    system = llamadas[0]["system"]
    assert "Objetivo:" in system[0]["text"]
    assert "Alumno: hasta 3 libros por 7 días" in system[0]["text"]
    assert system[0]["cache_control"] == {"type": "ephemeral"}
    assert "Mariana López Hernández (perfil Alumno)" in system[1]["text"]
    assert all(h["strict"] for h in llamadas[0]["herramientas"])

    # El resultado de la herramienta trae el libro con su ubicacion.
    resultado = llamadas[1]["mensajes"][-1]["content"][0]
    assert resultado["tool_use_id"] == "toolu_1"
    libros = json.loads(resultado["content"])
    assert libros[0]["clave"] == "LIB-001"
    assert libros[0]["ubicaciones_disponibles"]
    libro = obtener_id_libro(app, "LIB-001")
    assert leer_mensajes(app)[-1] == (1, "Chatbot", "buscar_libro", libro)


def test_ia_consulta_solo_al_usuario_en_sesion(cliente, monkeypatch):
    """
    Descripcion:
        Prueba: HU-02-09 · Las multas que recibe el modelo son las del
        usuario en sesion.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba.
        monkeypatch (pytest.MonkeyPatch): simula Claude.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    llamadas = simular_claude(
        monkeypatch,
        [
            SimpleNamespace(
                stop_reason="tool_use",
                content=[bloque_herramienta("consultar_mis_multas", {})],
            ),
            SimpleNamespace(
                stop_reason="end_turn",
                content=[bloque_texto("Debes $30.00 MXN.")],
            ),
        ],
    )
    entrar(cliente, "pmartinez", "Profe123")
    preguntar(cliente, "¿Cuánto debo?")
    resultado = json.loads(
        llamadas[1]["mensajes"][-1]["content"][0]["content"]
    )
    assert resultado["total"] == "$30.00 MXN"
    assert resultado["multas"][0]["libro"] == "Sapiens: de animales a dioses"


def test_ia_recuerda_la_conversacion(cliente, monkeypatch):
    """
    Descripcion:
        Prueba: HU-02-09 · En la segunda pregunta se le manda al modelo lo
        que ya se platico.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba.
        monkeypatch (pytest.MonkeyPatch): simula Claude.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    llamadas = simular_claude(
        monkeypatch,
        [
            SimpleNamespace(
                stop_reason="end_turn",
                content=[bloque_texto("Hola, Mariana.")],
            ),
            SimpleNamespace(
                stop_reason="end_turn", content=[bloque_texto("Claro.")]
            ),
        ],
    )
    entrar(cliente, "alumno", "Alumno123")
    preguntar(cliente, "Hola")
    preguntar(cliente, "¿Me ayudas?")
    assert llamadas[1]["mensajes"] == [
        {"role": "user", "content": "Hola"},
        {"role": "assistant", "content": "Hola, Mariana."},
        {"role": "user", "content": "¿Me ayudas?"},
    ]


@pytest.mark.parametrize(
    "texto, limpio",
    [
        (
            "Sí tenemos *Cien años de soledad* (LIB-001).",
            "Sí tenemos Cien años de soledad (LIB-001).",
        ),
        (
            "**Importante:** trae tu credencial.",
            "Importante: trae tu credencial.",
        ),
        ("## Préstamos\n- Alumno: 3 libros", "Préstamos\n- Alumno: 3 libros"),
        ("Usa _buscar_ y listo.", "Usa buscar y listo."),
        ("Cuesta 3 * 5 = 15 pesos.", "Cuesta 3 * 5 = 15 pesos."),
        ("La clave es LIB_001.", "La clave es LIB_001."),
    ],
)
def test_quitar_markdown(texto, limpio):
    """
    Descripcion:
        Prueba: HU-02-09 · Las marcas de Markdown del modelo se quitan sin
        tocar los asteriscos de una operacion ni los guiones bajos de una
        clave.

    Parametros:
        texto (str): respuesta del modelo.
        limpio (str): texto esperado.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    assert chatbot_servicio.quitar_markdown(texto) == limpio


def test_ia_rechaza_la_pregunta(cliente, monkeypatch):
    """
    Descripcion:
        Prueba: HU-02-09 · Si el modelo se niega, se contesta con un mensaje
        amable.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba.
        monkeypatch (pytest.MonkeyPatch): simula Claude.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    simular_claude(
        monkeypatch, [SimpleNamespace(stop_reason="refusal", content=[])]
    )
    entrar(cliente, "alumno", "Alumno123")
    respuesta = preguntar(cliente, "algo fuera de lugar").json
    assert respuesta["respuesta"].startswith("No puedo ayudarte con eso")
    assert respuesta["modo"] == "ia"


def test_si_la_ia_falla_contesta_en_respaldo(cliente, monkeypatch):
    """
    Descripcion:
        Prueba: HU-02-09 · Si la API de Claude falla, contesta en modo de
        respaldo y avisa el motivo.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba.
        monkeypatch (pytest.MonkeyPatch): simula Claude.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    simular_claude(monkeypatch, [claude.ErrorClaude("No hay conexión.")])
    entrar(cliente, "alumno", "Alumno123")
    respuesta = preguntar(cliente, "¿Para qué sirve el sistema?").json
    assert respuesta["modo"] == "respaldo"
    assert "en una sola plataforma" in respuesta["respuesta"]
    assert respuesta["aviso"] == "No hay conexión. Te contesto en modo básico."


# ============================================================
# CONSULTAS DEL PERSONAL DE BIBLIOTECA
# ============================================================


@pytest.mark.parametrize(
    "cuenta, contrasena, esperadas",
    [
        (
            "biblio",
            "Biblio123",
            {"consultar_prestamos_biblioteca", "consultar_multas_biblioteca"},
        ),
        ("alumno", "Alumno123", set()),
        ("profesor", "Profe123", set()),
    ],
)
def test_herramientas_del_personal_segun_permiso(
    cliente, monkeypatch, cuenta, contrasena, esperadas
):
    """
    Descripcion:
        Prueba: HU-02-09 · Solo el personal con permiso recibe las consultas
        de toda la biblioteca.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba.
        monkeypatch (pytest.MonkeyPatch): simula Claude.
        cuenta (str): cuenta.
        contrasena (str): contrasena.
        esperadas (set[str]): herramientas del personal que debe tener.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    llamadas = simular_claude(
        monkeypatch,
        [
            SimpleNamespace(
                stop_reason="end_turn", content=[bloque_texto("Ok")]
            )
        ],
    )
    entrar(cliente, cuenta, contrasena)
    preguntar(cliente, "Hola")
    nombres = {h["name"] for h in llamadas[0]["herramientas"]}
    assert (
        nombres
        & {
            "consultar_prestamos_biblioteca",
            "consultar_multas_biblioteca",
        }
        == esperadas
    )
    assert {"buscar_libros", "consultar_mis_prestamos"} <= nombres


def test_ia_del_personal_ve_los_prestamos_vencidos(cliente, monkeypatch):
    """
    Descripcion:
        Prueba: HU-02-09 · El bibliotecario pregunta en general y el modelo
        recibe los prestamos vencidos de todos los usuarios.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba.
        monkeypatch (pytest.MonkeyPatch): simula Claude.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    llamadas = simular_claude(
        monkeypatch,
        [
            SimpleNamespace(
                stop_reason="tool_use",
                content=[
                    bloque_herramienta(
                        "consultar_prestamos_biblioteca", {"vista": "vencidos"}
                    )
                ],
            ),
            SimpleNamespace(
                stop_reason="end_turn",
                content=[bloque_texto("José López tiene uno vencido.")],
            ),
        ],
    )
    entrar(cliente, "biblio", "Biblio123")
    preguntar(cliente, "¿Qué préstamos están vencidos?")
    resultado = json.loads(
        llamadas[1]["mensajes"][-1]["content"][0]["content"]
    )
    assert resultado["total"] == 1
    assert resultado["prestamos"][0]["usuario"] == (
        "José López Martínez (600102)"
    )
    assert resultado["prestamos"][0]["dias_de_retraso"] == 3


def test_alumno_no_puede_usar_consultas_del_personal(cliente, monkeypatch):
    """
    Descripcion:
        Prueba: HU-02-09 · Aunque el modelo intentara usar una consulta del
        personal con un alumno, se rechaza por permiso.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba.
        monkeypatch (pytest.MonkeyPatch): simula Claude.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    llamadas = simular_claude(
        monkeypatch,
        [
            SimpleNamespace(
                stop_reason="tool_use",
                content=[
                    bloque_herramienta("consultar_multas_biblioteca", {})
                ],
            ),
            SimpleNamespace(
                stop_reason="end_turn",
                content=[bloque_texto("Solo puedo ver tus datos.")],
            ),
        ],
    )
    entrar(cliente, "alumno", "Alumno123")
    preguntar(cliente, "¿Quién debe multas?")
    resultado = json.loads(
        llamadas[1]["mensajes"][-1]["content"][0]["content"]
    )
    assert resultado == {
        "error": "El perfil del usuario no tiene ese permiso."
    }


@pytest.mark.parametrize(
    "cuenta, contrasena, pregunta, esperado",
    [
        (
            "biblio",
            "Biblio123",
            "¿Qué libros están prestados en general?",
            "Hay 5 préstamo(s) activos",
        ),
        (
            "biblio",
            "Biblio123",
            "¿Quiénes tienen préstamos vencidos?",
            "José López Martínez (600102), devolver el",
        ),
        (
            "admin",
            "Admin123",
            "¿Quién debe multas?",
            "Pedro Martínez Soto (N20500): retraso de $30.00 MXN",
        ),
        (
            "biblio",
            "Biblio123",
            "¿Tengo préstamos vencidos?",
            "No tienes préstamos activos",
        ),
    ],
)
def test_respaldo_del_personal(
    cliente, cuenta, contrasena, pregunta, esperado
):
    """
    Descripcion:
        Prueba: HU-02-09 · Modo de respaldo: el personal ve los prestamos y
        multas de toda la biblioteca cuando pregunta en general, y los suyos
        cuando pregunta por los propios.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba.
        cuenta (str): cuenta.
        contrasena (str): contrasena.
        pregunta (str): pregunta.
        esperado (str): texto que debe traer la respuesta.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    entrar(cliente, cuenta, contrasena)
    assert esperado in preguntar(cliente, pregunta).json["respuesta"]


def test_respaldo_alumno_no_ve_los_de_todos(cliente):
    """
    Descripcion:
        Prueba: HU-02-09 · Un alumno que pregunta en general no recibe los
        prestamos de los demas.

    Parametros:
        cliente (flask.testing.FlaskClient): cliente de prueba.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """
    entrar(cliente, "alumno", "Alumno123")
    respuesta = preguntar(
        cliente, "¿Qué libros están prestados en general?"
    ).json["respuesta"]
    assert "José López" not in respuesta
    assert "préstamo(s) activos" not in respuesta


# ============================================================
# ERRORES DE LA API DE CLAUDE
# ============================================================


def _crear_error(clase, codigo, mensaje):
    """
    Descripcion:
        Crea un error de la API como los que lanza el SDK de Anthropic.

    Parametros:
        clase (type): clase del error del SDK.
        codigo (int): codigo HTTP.
        mensaje (str): mensaje de la API.

    Salida:
        anthropic.APIStatusError: error.
    """
    peticion = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    return clase(
        message=mensaje,
        response=httpx.Response(codigo, request=peticion),
        body=None,
    )


@pytest.mark.parametrize(
    "error, mensaje",
    [
        (
            _crear_error(
                anthropic.AuthenticationError, 401, "invalid x-api-key"
            ),
            "La llave de la API de Claude no es válida.",
        ),
        (
            _crear_error(
                anthropic.BadRequestError,
                400,
                "Your credit balance is too low to access the API.",
            ),
            "La cuenta de la API de Claude no tiene crédito.",
        ),
        (
            anthropic.APIConnectionError(
                request=httpx.Request("POST", "https://api.anthropic.com")
            ),
            "No hay conexión con la API de Claude.",
        ),
    ],
)
def test_errores_de_la_api_en_espanol(app, monkeypatch, error, mensaje):
    """
    Descripcion:
        Prueba: HU-02-09 · Los errores del SDK se convierten en mensajes en
        espanol.

    Parametros:
        app (flask.Flask): aplicacion de prueba.
        monkeypatch (pytest.MonkeyPatch): simula el SDK.
        error (Exception): error que lanza el SDK.
        mensaje (str): inicio del mensaje esperado.

    Salida:
        Ninguna.

    Excepciones:
        AssertionError si el comportamiento no cumple el criterio de
        aceptacion.
    """

    class ClienteFalso:
        def __init__(self, **_kwargs):
            self.messages = SimpleNamespace(create=self.crear)

        def crear(self, **_kwargs):
            raise error

    monkeypatch.setattr(claude.anthropic, "Anthropic", ClienteFalso)
    with app.app_context(), pytest.raises(claude.ErrorClaude) as capturado:
        claude.pedir_respuesta([], [], [])
    assert str(capturado.value).startswith(mensaje)
