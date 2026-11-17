"""
============================================================
Archivo:      services/chatbot_servicio.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Servicio del chatbot (HU-02-09 Chatbot de orientacion):
        - Platica sobre el objetivo, el alcance y la plataforma del sistema
          y sobre las politicas de la biblioteca (preguntas por defecto y
          preguntas abiertas).
        - Consulta el catalogo y los prestamos y multas del usuario en
          sesion con herramientas.

    Con llave de la API de Claude en .env contesta con IA; sin llave, o si
    la API falla, contesta en modo de respaldo con respuestas fijas por
    palabras clave. Para mejorar ("entrenar") las respuestas se edita
    CONOCIMIENTO: es lo que el chatbot sabe del sistema.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    13/11/2026
============================================================
"""

import json
import re
from datetime import date, datetime

import config
from models import chatbot as chatbot_modelo
from models import ejemplar as ejemplar_modelo
from models import libro as libro_modelo
from models import lista_espera as espera_modelo
from models import multa as multa_modelo
from models import perfil as perfil_modelo
from models import prestamo as prestamo_modelo
from models.db import normalizar
from services.errores import ErrorValidacion
from utils import claude

# Preguntas por defecto que se ofrecen como botones en el chat.
PREGUNTAS_SUGERIDAS = [
    "¿Para qué sirve el sistema?",
    "¿Qué incluye el sistema?",
    "¿En qué plataformas funciona?",
    "¿Cuántos libros puedo pedir y por cuántos días?",
    "¿Qué préstamos tengo?",
    "¿Tengo multas?",
    "¿Cómo renuevo un libro?",
    "¿Tienen Cien años de soledad?",
]

# Instrucciones de comportamiento para el modelo.
INSTRUCCIONES = f"""Eres Ducky, el asistente del Sistema Ducky de Gestión \
Bibliotecaria de la {config.NOMBRE_CLIENTE}, desarrollado por Syntra \
Technologies.

Tu trabajo es orientar a los usuarios: explicar para qué sirve el sistema, \
qué incluye, en qué plataformas funciona, cómo se hace cada trámite y cuáles \
son las políticas de la biblioteca. También consultas el catálogo y los \
préstamos y multas del usuario con las herramientas.

Reglas:
- Responde en español de México, amable y breve: de 1 a 5 oraciones o una \
lista corta con guiones.
- Escribe en texto simple, sin Markdown: sin asteriscos, almohadillas ni \
tablas.
- Usa solo la información de este mensaje y lo que regresen las \
herramientas. Si algo no está aquí (por ejemplo horarios), dilo y sugiere \
preguntar en el mostrador de la biblioteca. No inventes datos.
- Para saber si hay un libro, si está disponible o dónde está, usa \
buscar_libros. Para los préstamos o las multas del propio usuario, usa \
consultar_mis_prestamos o consultar_mis_multas.
- Si el usuario es personal de biblioteca, también tienes \
consultar_prestamos_biblioteca y consultar_multas_biblioteca para ver los de \
todos los usuarios; úsalas cuando pregunte en general (por ejemplo qué \
libros están prestados, cuáles están vencidos o quién debe multas). Si no \
tienes esas herramientas, explica que su perfil solo puede consultar sus \
propios datos.
- No haces trámites (prestar, renovar, devolver ni pagar): explica cómo se \
hacen y quién los hace.
- Si te preguntan algo que no tiene que ver con la biblioteca o el sistema, \
di amablemente que solo puedes ayudar con eso."""

# Lo que el chatbot sabe del sistema. Para mejorar sus respuestas se agrega
# o corrige informacion aqui.
CONOCIMIENTO = """Objetivo:
El Sistema Ducky de Gestión Bibliotecaria reúne en una sola plataforma lo \
que la biblioteca hacía a mano: el catálogo, los préstamos, las \
devoluciones, las renovaciones, las multas y el inventario de ejemplares. \
Así la información está al día en un solo lugar, el sistema aplica las \
reglas solo (límites de préstamo, adeudos y fechas) y cada movimiento queda \
registrado.

Alcance (lo que ya hace el sistema):
- Usuarios: inicio de sesión, alta, baja, cambio y consulta de cuentas, \
perfiles con sus permisos y cambio de contraseña.
- Libros: alta (se puede llenar con el ISBN desde Open Library), edición, \
baja, ejemplares con su ubicación física (sala, estante y posición), \
búsqueda por título, autor, tema, editorial o clave, listado en PDF e \
impresión, y órdenes de compra.
- Préstamos: revisión del usuario y del libro, registro con folio, boleta \
por correo, WhatsApp o impresa, renovación y lista de espera.
- Devoluciones y multas: registro de la devolución (a tiempo, con retraso, \
con daño o con pérdida), multas que se mandan a Tesorería y registro de su \
pago.
- Este chatbot de orientación.

Plataforma:
- App web para el personal y los usuarios, en computadora o celular.
- Portal móvil para alumnos (dirección /movil): buscar libros y ver su \
disponibilidad y ubicación. Se puede agregar a la pantalla de inicio del \
celular como app.
- Hecho en Python con Flask (patrón MVC) y base de datos SQLite.
- Desarrollado por Syntra Technologies: Melissa Silva Vázquez, Tomás Zapata \
Pérez y Alejandro Evaristo Cazares Escobedo.

Cómo se hacen los trámites:
- Préstamo: lo registra el bibliotecario con la matrícula y el código del \
ejemplar; se entrega una boleta con la fecha de devolución.
- Renovación: la hace el bibliotecario desde la boleta antes de la fecha de \
devolución. No se puede si el libro tiene lista de espera, si ya venció, si \
ya se usaron todas las renovaciones o si hay multas pendientes.
- Lista de espera: si un libro no tiene ejemplares disponibles, el \
bibliotecario te anota; cuando se libera uno se aparta para el primer turno \
y se le avisa por correo o WhatsApp.
- Devolución: se entrega el libro en la biblioteca y el bibliotecario \
registra si llegó a tiempo, dañado o si se perdió.
- Multas: por retraso se cobra la multa diaria del perfil por cada día; por \
daño, lo que cuesta repararlo; por pérdida, el último precio del libro (si \
está en dólares se convierte con el tipo de cambio vigente). Las multas se \
mandan a Tesorería, se pagan allá y la biblioteca registra el pago. Con \
multas pendientes o préstamos vencidos no se puede llevar otro libro ni \
renovar.
- Libros de acceso reservado: solo se consultan dentro de la biblioteca."""

# Herramientas para consultar el sistema.
HERRAMIENTAS = [
    {
        "name": "buscar_libros",
        "description": (
            "Busca libros del catálogo por título, autor, tema o clave y "
            "dice cuántos ejemplares hay disponibles, en qué sala, estante y "
            "posición están, y cuántas personas están en lista de espera."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "texto": {
                    "type": "string",
                    "description": (
                        "Parte del título, nombre del autor, tema o clave del "
                        "libro, por ejemplo: soledad, García Márquez, "
                        "Programación o LIB-001."
                    ),
                }
            },
            "required": ["texto"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "name": "consultar_mis_prestamos",
        "description": (
            "Lista los préstamos activos del usuario que platica contigo, "
            "con su fecha de devolución, si está vencido y sus renovaciones."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "name": "consultar_mis_multas",
        "description": (
            "Lista las multas pendientes de pago del usuario que platica "
            "contigo y su total."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
    },
]

# Herramientas solo para el personal de biblioteca, con el permiso que pide
# cada una (el mismo que la pantalla correspondiente de la app).
HERRAMIENTAS_PERSONAL = [
    (
        "prestamos.registrar",
        {
            "name": "consultar_prestamos_biblioteca",
            "description": (
                "Lista los préstamos de todos los usuarios de la biblioteca "
                "(activos o solo los vencidos), con quién tiene cada libro y "
                "cuándo lo debe devolver."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "vista": {
                        "type": "string",
                        "enum": ["activos", "vencidos"],
                        "description": (
                            "activos para todos los que no se han devuelto, "
                            "vencidos para los que ya pasaron su fecha."
                        ),
                    }
                },
                "required": ["vista"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    ),
    (
        "multas.gestionar",
        {
            "name": "consultar_multas_biblioteca",
            "description": (
                "Lista las multas pendientes de pago de todos los usuarios, "
                "con quién debe, cuánto y por qué, y el total."
            ),
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
            "strict": True,
        },
    ),
]

# Cuantos prestamos o multas de la biblioteca se regresan como maximo.
LIMITE_CONSULTA_PERSONAL = 50

# Nombre de la intencion que se guarda por cada herramienta (diseno EV8).
INTENCIONES = {
    "buscar_libros": "buscar_libro",
    "consultar_mis_prestamos": "consultar_prestamo",
    "consultar_mis_multas": "consultar_multa",
    "consultar_prestamos_biblioteca": "consultar_prestamo",
    "consultar_multas_biblioteca": "consultar_multa",
}
INTENCION_ORIENTACION = "orientacion"

# ============================================================
# CONSULTAS DEL SISTEMA (HERRAMIENTAS)
# Las usan la IA y el modo de respaldo.
# ============================================================


def _formatear_fecha(valor):
    """
    Descripcion:
        Muestra una fecha aaaa-mm-dd como dd/mm/aaaa.

    Parametros:
        valor (str): fecha de SQLite.

    Salida:
        str: fecha con formato.
    """
    return datetime.strptime(valor[:10], "%Y-%m-%d").strftime("%d/%m/%Y")


def _describir_ubicacion(ejemplar):
    """
    Descripcion:
        Ubicacion de un ejemplar en texto.

    Parametros:
        ejemplar (sqlite3.Row): ejemplar con estancia y estante.

    Salida:
        str: sala, estante y posicion, o que no esta registrada.
    """
    if not ejemplar["estancia"]:
        return config.MENSAJES["ubicacion_no_registrada"]
    return (
        f"{ejemplar['estancia']} · Estante {ejemplar['estante']} · "
        f"Posición {ejemplar['posicion']}"
    )


def buscar_libros(texto, limite=5):
    """
    Descripcion:
        HU-02-09 · Consulta de libros: busca por clave, titulo, autor y tema
        (sin acentos) y junta los resultados sin repetir.

    Parametros:
        texto (str): lo que se busca.
        limite (int): cuantos libros regresar como maximo.

    Salida:
        list[dict]: libros con disponibilidad, ubicaciones y lista de espera.
    """
    texto = (texto or "").strip()[:100]
    if not texto:
        return []
    encontrados = {}
    for campo in ("clave", "titulo", "autor", "tema"):
        valor = texto.upper() if campo == "clave" else texto
        for libro in libro_modelo.listar(campo=campo, texto=valor):
            encontrados.setdefault(libro["id"], libro)
    libros = []
    for libro in list(encontrados.values())[:limite]:
        disponibles = [
            _describir_ubicacion(ejemplar)
            for ejemplar in ejemplar_modelo.listar_de_libro(libro["id"])
            if ejemplar["estado"] == config.ESTADO_DISPONIBLE
        ]
        espera = espera_modelo.obtener_libro(libro["clave"])
        libros.append(
            {
                "id": libro["id"],
                "clave": libro["clave"],
                "titulo": libro["titulo"],
                "autores": libro["autores"] or "",
                "tema": libro["tema"],
                "editorial": libro["editorial"],
                "tipo_acceso": libro["tipo_acceso"],
                "ejemplares": libro["total_ejemplares"],
                "disponibles": libro["disponibles"],
                "ubicaciones_disponibles": disponibles,
                "en_lista_de_espera": espera["en_espera"] if espera else 0,
            }
        )
    return libros


def consultar_prestamos(usuario_id):
    """
    Descripcion:
        HU-02-09 · Consulta de prestamos del usuario en sesion.

    Parametros:
        usuario_id (int): id del usuario.

    Salida:
        list[dict]: prestamos activos.
    """
    hoy = date.today().isoformat()
    return [
        {
            "folio": prestamo["folio"],
            "libro": prestamo["titulo"],
            "ejemplar": prestamo["ejemplar_codigo"],
            "fecha_devolucion": _formatear_fecha(
                prestamo["fecha_vencimiento"]
            ),
            "vencido": prestamo["fecha_vencimiento"] < hoy,
            "renovaciones": (
                f"{prestamo['renovaciones']} de "
                f"{prestamo['max_renovaciones'] or 0}"
            ),
        }
        for prestamo in prestamo_modelo.listar_activos_de_usuario(usuario_id)
    ]


def consultar_multas(usuario_id):
    """
    Descripcion:
        HU-02-09 · Consulta de multas pendientes del usuario en sesion.

    Parametros:
        usuario_id (int): id del usuario.

    Salida:
        dict: multas (motivo, monto, detalle y prestamo) y total.
    """
    multas = multa_modelo.listar_pendientes_de_usuario(usuario_id)
    return {
        "multas": [
            {
                "motivo": multa["motivo"],
                "monto": f"${float(multa['monto']):,.2f} MXN",
                "detalle": multa["descripcion"],
                "prestamo": multa["folio"],
                "libro": multa["titulo"],
            }
            for multa in multas
        ],
        "total": f"${sum(float(m['monto']) for m in multas):,.2f} MXN",
    }


def consultar_prestamos_biblioteca(vista):
    """
    Descripcion:
        HU-02-09 · Consulta del personal: prestamos de todos los usuarios,
        activos o solo vencidos (lo mismo que la pantalla Prestamos).

    Parametros:
        vista (str): "activos" o "vencidos".

    Salida:
        dict: total, prestamos (hasta LIMITE_CONSULTA_PERSONAL) y vista.
    """
    vista = vista if vista in ("activos", "vencidos") else "activos"
    hoy = date.today()
    prestamos = prestamo_modelo.listar(vista)
    return {
        "vista": vista,
        "total": len(prestamos),
        "prestamos": [
            {
                "folio": prestamo["folio"],
                "usuario": (
                    f"{prestamo['usuario_nombre']} "
                    f"({prestamo['usuario_identificador']})"
                ),
                "libro": prestamo["titulo"],
                "ejemplar": prestamo["ejemplar_codigo"],
                "fecha_devolucion": _formatear_fecha(
                    prestamo["fecha_vencimiento"]
                ),
                "dias_de_retraso": max(
                    (
                        hoy - date.fromisoformat(prestamo["fecha_vencimiento"])
                    ).days,
                    0,
                ),
            }
            for prestamo in prestamos[:LIMITE_CONSULTA_PERSONAL]
        ],
    }


def consultar_multas_biblioteca():
    """
    Descripcion:
        HU-02-09 · Consulta del personal: multas pendientes de todos los
        usuarios (lo mismo que la pantalla Multas).

    Parametros:
        Ninguno.

    Salida:
        dict: total en pesos, cantidad y multas (hasta
        LIMITE_CONSULTA_PERSONAL).
    """
    multas = multa_modelo.listar("pendientes")
    return {
        "cantidad": len(multas),
        "total": f"${sum(float(m['monto']) for m in multas):,.2f} MXN",
        "multas": [
            {
                "usuario": (
                    f"{multa['usuario_nombre']} "
                    f"({multa['usuario_identificador']})"
                ),
                "motivo": multa["motivo"],
                "monto": f"${float(multa['monto']):,.2f} MXN",
                "detalle": multa["descripcion"],
                "prestamo": multa["folio"],
                "libro": multa["titulo"],
                "enviada_a_tesoreria": bool(multa["fecha_envio_tesoreria"]),
            }
            for multa in multas[:LIMITE_CONSULTA_PERSONAL]
        ],
    }


def obtener_herramientas(usuario):
    """
    Descripcion:
        Herramientas que puede usar el modelo con este usuario: las de todos
        y, si su perfil tiene el permiso, las del personal de biblioteca.

    Parametros:
        usuario (dict): usuario en sesion (con sus permisos).

    Salida:
        list[dict]: definicion de las herramientas.
    """
    return HERRAMIENTAS + [
        herramienta
        for permiso, herramienta in HERRAMIENTAS_PERSONAL
        if permiso in usuario["permisos"]
    ]


def _ejecutar_herramienta(nombre, entrada, usuario):
    """
    Descripcion:
        Ejecuta la herramienta que pidio el modelo. Los datos del usuario
        siempre salen de la sesion, nunca de lo que pida el modelo, y las
        consultas del personal vuelven a revisar el permiso.

    Parametros:
        nombre (str): nombre de la herramienta.
        entrada (dict): parametros que mando el modelo.
        usuario (dict): usuario en sesion (id, nombre, perfil, permisos).

    Salida:
        tuple[dict o list, int o None]: resultado y el id del libro si se
        encontro uno solo.
    """
    if nombre == "buscar_libros":
        libros = buscar_libros((entrada or {}).get("texto", ""))
        libro_id = libros[0]["id"] if len(libros) == 1 else None
        return libros, libro_id
    if nombre == "consultar_mis_prestamos":
        return consultar_prestamos(usuario["id"]), None
    if nombre == "consultar_mis_multas":
        return consultar_multas(usuario["id"]), None

    # Consultas del personal: solo con el permiso de la pantalla.
    permisos = {h["name"]: permiso for permiso, h in HERRAMIENTAS_PERSONAL}
    if nombre in permisos and permisos[nombre] not in usuario["permisos"]:
        return {"error": "El perfil del usuario no tiene ese permiso."}, None
    if nombre == "consultar_prestamos_biblioteca":
        vista = (entrada or {}).get("vista", "activos")
        return consultar_prestamos_biblioteca(vista), None
    if nombre == "consultar_multas_biblioteca":
        return consultar_multas_biblioteca(), None
    return {"error": f"No existe la herramienta {nombre}."}, None


# ============================================================
# RESPUESTA CON LA API DE CLAUDE
# ============================================================


def _armar_politicas():
    """
    Descripcion:
        Reglas de prestamo de cada perfil, tomadas de la base de datos.

    Parametros:
        Ninguno.

    Salida:
        str: una linea por perfil con prestamos.
    """
    renglones = ["Reglas de préstamo por perfil:"]
    for perfil in perfil_modelo.listar():
        if perfil["max_prestamos"]:
            renglones.append(
                f"- {perfil['nombre']}: hasta {perfil['max_prestamos']} "
                f"libros por {perfil['dias_prestamo']} días, "
                f"{perfil['max_renovaciones'] or 0} renovación(es), multa de "
                f"${float(perfil['multa_diaria'] or 0):,.2f} MXN por día de "
                "retraso."
            )
    renglones.append("Los demás perfiles no tienen préstamos a domicilio.")
    return "\n".join(renglones)


def _armar_system(usuario):
    """
    Descripcion:
        Arma las instrucciones: primero lo que no cambia (se guarda en cache)
        y al final los datos del usuario y la fecha.

    Parametros:
        usuario (dict): usuario en sesion.

    Salida:
        list[dict]: bloques de texto para system.
    """
    funciones = [
        descripcion
        for codigo, descripcion, _ in config.PERMISOS
        if codigo in usuario["permisos"]
    ]
    contexto = (
        f"Usuario que platica contigo: {usuario['nombre']} (perfil "
        f"{usuario['perfil']}).\n"
        f"Hoy es {date.today():%d/%m/%Y}.\n"
        "Lo que su perfil puede hacer en el sistema: "
        + ("; ".join(funciones) or "solo consultar")
        + "."
    )
    fijo = "\n\n".join([INSTRUCCIONES, CONOCIMIENTO, _armar_politicas()])
    return [
        {
            "type": "text",
            "text": fijo,
            "cache_control": {"type": "ephemeral"},
        },
        {"type": "text", "text": contexto},
    ]


def quitar_markdown(texto):
    """
    Descripcion:
        Quita las marcas de Markdown que a veces pone el modelo (negritas,
        cursivas y titulos), porque el chat muestra texto simple.

    Parametros:
        texto (str): respuesta del modelo.

    Salida:
        str: texto sin asteriscos, guiones bajos de enfasis ni almohadillas.
    """
    texto = re.sub(r"\*\*(.+?)\*\*", r"\1", texto)
    texto = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\1", texto)
    texto = re.sub(r"(?<!\w)__?(?!\s)(.+?)(?<!\s)__?(?!\w)", r"\1", texto)
    texto = re.sub(r"^#{1,6}\s+", "", texto, flags=re.MULTILINE)
    return texto.strip()


def _armar_mensajes(historial):
    """
    Descripcion:
        Convierte los mensajes guardados en la conversacion para el modelo;
        la primera debe ser del usuario.

    Parametros:
        historial (list[sqlite3.Row]): mensajes de la conversacion.

    Salida:
        list[dict]: mensajes con role y content.
    """
    mensajes = [
        {
            "role": "user"
            if fila["emisor"] == config.EMISOR_USUARIO
            else "assistant",
            "content": fila["mensaje"],
        }
        for fila in historial
    ]
    while mensajes and mensajes[0]["role"] != "user":
        mensajes.pop(0)
    return mensajes


def _responder_con_claude(usuario, historial):
    """
    Descripcion:
        HU-02-09: Pide la respuesta a Claude. Si el modelo pide consultar el
        sistema, se ejecutan las herramientas y se le regresan los
        resultados hasta que conteste (maximo config.CHATBOT_MAX_CONSULTAS
        veces).

    Parametros:
        usuario (dict): usuario en sesion.
        historial (list[sqlite3.Row]): mensajes de la conversacion.

    Salida:
        tuple[str, str, int o None]: respuesta, intencion y libro_id.

    Excepciones:
        claude.ErrorClaude si la API falla.
    """
    system = _armar_system(usuario)
    mensajes = _armar_mensajes(historial)
    intencion, libro_id = INTENCION_ORIENTACION, None

    for _ in range(config.CHATBOT_MAX_CONSULTAS + 1):
        respuesta = claude.pedir_respuesta(
            system, mensajes, obtener_herramientas(usuario)
        )
        if respuesta.stop_reason != "tool_use":
            break
        # Se regresa el contenido completo (incluye el razonamiento).
        mensajes.append({"role": "assistant", "content": respuesta.content})
        resultados = []
        for bloque in respuesta.content:
            if bloque.type != "tool_use":
                continue
            resultado, libro = _ejecutar_herramienta(
                bloque.name, bloque.input, usuario
            )
            intencion = INTENCIONES.get(bloque.name, intencion)
            libro_id = libro or libro_id
            resultados.append(
                {
                    "type": "tool_result",
                    "tool_use_id": bloque.id,
                    "content": json.dumps(resultado, ensure_ascii=False),
                }
            )
        mensajes.append({"role": "user", "content": resultados})

    if respuesta.stop_reason == "refusal":
        return (
            "No puedo ayudarte con eso. Pregúntame sobre la biblioteca o el "
            "sistema.",
            intencion,
            libro_id,
        )
    texto = quitar_markdown(
        "\n".join(
            bloque.text
            for bloque in respuesta.content
            if bloque.type == "text"
        )
    )
    if not texto:
        texto = (
            "No alcancé a terminar la respuesta. ¿Me lo preguntas de forma "
            "más corta?"
        )
    return texto, intencion, libro_id


# ============================================================
# RESPUESTA EN MODO DE RESPALDO (SIN IA)
# ============================================================

# Palabras que no sirven para buscar un libro.
PALABRAS_VACIAS = set(
    "a al algun alguno biblioteca busca buscar busco con de del donde el en "
    "encuentro esta este hay la las libro libros los me necesito para por "
    "puedes que quiero sobre su tiene tienen tienes un una y ubicacion "
    "disponible disponibles favor hola cuantos cuantas cuanto cuanta "
    "ejemplar ejemplares copia copias existe existen queda quedan todavia "
    "aun titulo dime sabes saber quisiera podrias ver hay".split()
)


def _contiene(texto, palabras):
    """
    Descripcion:
        Revisa si el texto (ya normalizado) trae alguna de las palabras.

    Parametros:
        texto (str): texto sin acentos y en minusculas.
        palabras (tuple[str]): palabras o frases a buscar.

    Salida:
        bool: True si encuentra alguna.
    """
    return any(palabra in texto for palabra in palabras)


def _responder_al_personal(usuario, t):
    """
    Descripcion:
        HU-02-09 · Modo de respaldo para el personal: prestamos y multas de
        toda la biblioteca, si su perfil tiene el permiso.

    Parametros:
        usuario (dict): usuario en sesion.
        t (str): mensaje sin acentos y en minusculas.

    Salida:
        tuple[str, str, None] o None si la pregunta no es de este tipo.
    """
    general = _contiene(
        t,
        (
            "en general",
            "todos los",
            "todas las",
            "de la biblioteca",
            "quien tiene",
            "quienes tienen",
            "quien debe",
            "quienes deben",
            "deudores",
            "estan prestados",
            "estan en prestamo",
            "libros prestados",
            "vencidos",
        ),
    )
    # "Mis prestamos" o "tengo" son preguntas sobre sus propios datos.
    propio = _contiene(t, ("mis ", "mi prestamo", "tengo", "debo"))
    if not general or propio:
        return None
    if "multas.gestionar" in usuario["permisos"] and _contiene(
        t, ("multa", "debe", "deudor", "adeudo")
    ):
        datos = consultar_multas_biblioteca()
        if not datos["multas"]:
            return "No hay multas pendientes.", "consultar_multa", None
        renglones = [
            f"- {m['usuario']}: {m['motivo'].lower()} de {m['monto']} "
            f"({m['libro']})"
            for m in datos["multas"]
        ]
        return (
            f"Hay {datos['cantidad']} multa(s) pendiente(s) por "
            f"{datos['total']}:\n" + "\n".join(renglones),
            "consultar_multa",
            None,
        )
    if "prestamos.registrar" in usuario["permisos"] and _contiene(
        t, ("prestamo", "prestado", "vencido", "quien tiene", "quienes tienen")
    ):
        vista = "vencidos" if "vencido" in t else "activos"
        datos = consultar_prestamos_biblioteca(vista)
        if not datos["prestamos"]:
            return f"No hay préstamos {vista}.", "consultar_prestamo", None
        renglones = [
            f"- {p['libro']} ({p['folio']}): {p['usuario']}, devolver el "
            f"{p['fecha_devolucion']}"
            + (
                f" ({p['dias_de_retraso']} día(s) de retraso)"
                if p["dias_de_retraso"]
                else ""
            )
            for p in datos["prestamos"]
        ]
        return (
            f"Hay {datos['total']} préstamo(s) {vista}:\n"
            + "\n".join(renglones),
            "consultar_prestamo",
            None,
        )
    return None


def _describir_reglas_del_perfil(nombre_perfil):
    """
    Descripcion:
        Reglas de prestamo del perfil del usuario en una oracion.

    Parametros:
        nombre_perfil (str): perfil del usuario en sesion.

    Salida:
        str: respuesta.
    """
    perfil = next(
        (p for p in perfil_modelo.listar() if p["nombre"] == nombre_perfil),
        None,
    )
    if not perfil or not perfil["max_prestamos"]:
        return (
            f"El perfil {nombre_perfil} no tiene préstamos a domicilio; los "
            "libros se consultan dentro de la biblioteca."
        )
    renovaciones = perfil["max_renovaciones"] or 0
    return (
        f"Con tu perfil {perfil['nombre']} puedes llevarte hasta "
        f"{perfil['max_prestamos']} libros por {perfil['dias_prestamo']} "
        f"días y renovar cada préstamo hasta {renovaciones} "
        f"{'vez' if renovaciones == 1 else 'veces'}. Por cada día de "
        f"retraso la multa es de ${float(perfil['multa_diaria'] or 0):,.2f} "
        "MXN."
    )


def _describir_libros(libros):
    """
    Descripcion:
        Texto con los libros encontrados, su disponibilidad y ubicacion.

    Parametros:
        libros (list[dict]): resultado de buscar_libros().

    Salida:
        str: respuesta.
    """
    renglones = []
    for libro in libros:
        if libro["disponibles"]:
            estado = (
                f"{libro['disponibles']} de {libro['ejemplares']} "
                "ejemplar(es) disponible(s) en "
                + "; ".join(libro["ubicaciones_disponibles"][:3])
            )
        elif libro["ejemplares"]:
            estado = "sin ejemplares disponibles por ahora"
            if libro["en_lista_de_espera"]:
                estado += (
                    f" ({libro['en_lista_de_espera']} en lista de espera)"
                )
        else:
            estado = "todavía no tiene ejemplares"
        renglones.append(f"- {libro['titulo']} ({libro['clave']}): {estado}.")
    return "Esto encontré en el catálogo:\n" + "\n".join(renglones)


def _buscar_por_palabras(texto_normalizado):
    """
    Descripcion:
        Busca libros con las palabras importantes del mensaje: primero todas
        juntas y luego cada una, de la mas larga a la mas corta (de 4 letras
        o mas), hasta encontrar algo.

    Parametros:
        texto_normalizado (str): mensaje sin acentos y en minusculas.

    Salida:
        list[dict]: libros encontrados.
    """
    palabras = [
        palabra
        for palabra in re.findall(r"[a-z0-9-]+", texto_normalizado)
        if palabra not in PALABRAS_VACIAS
    ]
    if not palabras:
        return []
    libros = buscar_libros(" ".join(palabras))
    for palabra in sorted(set(palabras), key=len, reverse=True):
        if libros or len(palabra) < 4:
            break
        libros = buscar_libros(palabra)
    return libros


def _responder_con_reglas(usuario, texto):
    """
    Descripcion:
        HU-02-09 · Modo de respaldo: reconoce la pregunta por palabras clave
        y contesta con respuestas fijas o con las consultas del sistema.

    Parametros:
        usuario (dict): usuario en sesion.
        texto (str): mensaje del usuario.

    Salida:
        tuple[str, str, int o None]: respuesta, intencion y libro_id.
    """
    t = normalizar(texto)

    # Consultas generales del personal de biblioteca.
    respuesta = _responder_al_personal(usuario, t)
    if respuesta:
        return respuesta

    # Multas del usuario.
    if _contiene(t, ("multa", "adeudo", "cuanto debo", "pagar", "tesoreria")):
        datos = consultar_multas(usuario["id"])
        if not datos["multas"]:
            return (
                "No tienes multas pendientes. Recuerda que por cada día de "
                "retraso se cobra la multa diaria de tu perfil.",
                "consultar_multa",
                None,
            )
        renglones = [
            f"- {m['motivo']} de {m['monto']} ({m['libro']}, préstamo "
            f"{m['prestamo']})"
            for m in datos["multas"]
        ]
        return (
            f"Tienes multas pendientes por {datos['total']}:\n"
            + "\n".join(renglones)
            + "\nSe pagan en Tesorería; mientras tanto no puedes llevarte "
            "otro libro ni renovar.",
            "consultar_multa",
            None,
        )

    # Prestamos del usuario.
    if _contiene(
        t,
        (
            "mis prestamos",
            "mi prestamo",
            "que prestamos tengo",
            "tengo prestamo",
            "tengo libros",
            "tengo prestado",
            "que libros tengo",
            "mis libros",
            "cuando devuelvo",
            "cuando entrego",
            "cuando debo devolver",
            "cuando vence",
            "fecha de devolucion",
        ),
    ):
        prestamos = consultar_prestamos(usuario["id"])
        if not prestamos:
            return (
                "No tienes préstamos activos.",
                "consultar_prestamo",
                None,
            )
        renglones = [
            f"- {p['libro']} ({p['folio']}): devolver el "
            f"{p['fecha_devolucion']}" + (" (vencido)" if p["vencido"] else "")
            for p in prestamos
        ]
        return (
            "Estos son tus préstamos activos:\n" + "\n".join(renglones),
            "consultar_prestamo",
            None,
        )

    # Politicas y tramites.
    respuestas_fijas = [
        (
            ("renov", "renuev"),
            "La renovación la hace el bibliotecario desde la boleta antes de "
            "la fecha de devolución. No se puede si el libro tiene lista de "
            "espera, si ya venció, si ya usaste todas tus renovaciones o si "
            "tienes multas pendientes.",
        ),
        (
            ("devol", "regresar el libro", "entregar el libro"),
            "Entrega el libro en la biblioteca y el bibliotecario registra "
            "la devolución. Si llega tarde se cobra la multa diaria de tu "
            "perfil por cada día; si llega dañado o se perdió también se "
            "genera una multa que se paga en Tesorería.",
        ),
        (
            ("lista de espera", "apartar", "reservar"),
            "Si un libro no tiene ejemplares disponibles, el bibliotecario "
            "te anota en la lista de espera. Cuando se libera uno se aparta "
            "para el primer turno y se le avisa por correo o WhatsApp.",
        ),
        (
            ("cuantos libros", "cuantos dias", "prestamo", "prestar"),
            _describir_reglas_del_perfil(usuario["perfil"]),
        ),
        (
            ("objetivo", "para que sirve", "proposito", "que es el sistema"),
            "El sistema reúne en una sola plataforma el catálogo, los "
            "préstamos, las devoluciones, las renovaciones, las multas y el "
            "inventario de la biblioteca, que antes se llevaban a mano. Así "
            "la información está al día y las reglas se aplican solas.",
        ),
        (
            ("incluye", "alcance", "funciones", "modulos", "que hace"),
            "Incluye: usuarios y perfiles; alta, edición y búsqueda de "
            "libros con su ubicación; listado en PDF e impresión; órdenes "
            "de compra; préstamos con boleta, renovación y lista de espera; "
            "devoluciones y multas que se mandan a Tesorería; y este "
            "chatbot.",
        ),
        (
            ("plataforma", "celular", "movil", "app", "aplicacion", "web"),
            "Funciona como app web en computadora o celular, y los alumnos "
            "tienen un portal móvil (/movil) para buscar libros y ver su "
            "ubicación, que se puede agregar a la pantalla de inicio. Está "
            "hecho en Python con Flask y SQLite.",
        ),
    ]
    for palabras, respuesta in respuestas_fijas:
        if _contiene(t, palabras):
            return respuesta, INTENCION_ORIENTACION, None

    # Busqueda de libros con las palabras importantes del mensaje.
    libros = _buscar_por_palabras(t)
    if libros:
        libro_id = libros[0]["id"] if len(libros) == 1 else None
        return _describir_libros(libros), "buscar_libro", libro_id

    if _contiene(t, ("gracias",)):
        return "¡Con gusto! Aquí estoy si tienes otra duda.", None, None
    # Saludo, o no se reconocio la pregunta.
    inicio = (
        f"Hola, {usuario['nombre'].split()[0]}."
        if _contiene(t, ("hola", "buenos dias", "buenas"))
        else "No encontré respuesta para eso en modo básico."
    )
    return (
        f"{inicio} Puedo contarte para qué sirve el sistema, qué incluye y "
        "en qué plataformas funciona, explicarte cómo pedir, renovar o "
        "devolver libros, revisar tus préstamos y multas, y buscar libros "
        "del catálogo. Por ejemplo: «¿Tienen Cien años de soledad?»",
        INTENCION_ORIENTACION,
        None,
    )


# ============================================================
# CONVERSACION (HU-02-09)
# ============================================================


def obtener_conversacion(usuario_id, conversacion_id):
    """
    Descripcion:
        HU-02-09: Mensajes de la conversacion abierta del usuario, para
        mostrarlos al abrir el chat en otra pantalla.

    Parametros:
        usuario_id (int): id del usuario en sesion.
        conversacion_id (int o None): id guardado en la sesion.

    Salida:
        dict: conversacion_id (o None), mensajes, modo y sugerencias.
    """
    conversacion = chatbot_modelo.obtener_conversacion_abierta(
        conversacion_id, usuario_id
    )
    mensajes = (
        chatbot_modelo.listar_mensajes(conversacion["id"])
        if conversacion
        else []
    )
    return {
        "conversacion_id": conversacion["id"] if conversacion else None,
        "mensajes": [
            {"emisor": fila["emisor"], "mensaje": fila["mensaje"]}
            for fila in mensajes
        ],
        "modo": "ia" if claude.verificar_configurado() else "respaldo",
        "sugerencias": PREGUNTAS_SUGERIDAS,
    }


def responder(usuario, conversacion_id, texto):
    """
    Descripcion:
        HU-02-09: Guarda la pregunta, la contesta (con IA o en modo de
        respaldo) y guarda la respuesta con su intencion.

    Parametros:
        usuario (dict): usuario en sesion (id, nombre, perfil, permisos).
        conversacion_id (int o None): conversacion abierta en la sesion.
        texto (str): pregunta del usuario.

    Salida:
        dict: conversacion_id, respuesta, modo ("ia" o "respaldo") y aviso
        (motivo si la IA fallo, o None).

    Excepciones:
        ErrorValidacion (422) si la pregunta esta vacia o es muy larga.
    """
    texto = " ".join((texto or "").split())
    if not texto:
        raise ErrorValidacion("Escribe tu pregunta.", codigo=422)
    if len(texto) > config.CHATBOT_LONGITUD_MAXIMA:
        raise ErrorValidacion(
            "La pregunta admite hasta "
            f"{config.CHATBOT_LONGITUD_MAXIMA} caracteres.",
            codigo=422,
        )

    # Abrimos la conversacion si no hay una y guardamos la pregunta.
    conversacion = chatbot_modelo.obtener_conversacion_abierta(
        conversacion_id, usuario["id"]
    )
    conversacion_id = (
        conversacion["id"]
        if conversacion
        else chatbot_modelo.crear_conversacion(usuario["id"])
    )
    chatbot_modelo.guardar_mensaje(
        conversacion_id, config.EMISOR_USUARIO, texto
    )

    # Con IA si hay llave; si falla, en modo de respaldo con el motivo.
    modo, aviso = "respaldo", None
    if claude.verificar_configurado():
        historial = chatbot_modelo.listar_mensajes(
            conversacion_id, config.CHATBOT_MENSAJES_HISTORIAL
        )
        try:
            respuesta, intencion, libro_id = _responder_con_claude(
                usuario, historial
            )
            modo = "ia"
        except claude.ErrorClaude as error:
            aviso = f"{error} Te contesto en modo básico."
    if modo == "respaldo":
        respuesta, intencion, libro_id = _responder_con_reglas(usuario, texto)

    chatbot_modelo.guardar_mensaje(
        conversacion_id, config.EMISOR_CHATBOT, respuesta, intencion, libro_id
    )
    return {
        "conversacion_id": conversacion_id,
        "respuesta": respuesta,
        "modo": modo,
        "aviso": aviso,
    }


def cerrar(usuario_id, conversacion_id):
    """
    Descripcion:
        HU-02-09: Cierra la conversacion para empezar una nueva.

    Parametros:
        usuario_id (int): id del usuario en sesion.
        conversacion_id (int o None): conversacion abierta en la sesion.

    Salida:
        Ninguna.
    """
    conversacion = chatbot_modelo.obtener_conversacion_abierta(
        conversacion_id, usuario_id
    )
    if conversacion:
        chatbot_modelo.cerrar_conversacion(conversacion["id"])
