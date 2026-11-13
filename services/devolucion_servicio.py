"""
============================================================
Archivo:      services/devolucion_servicio.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Servicio de devoluciones (Sprint 2, Devolver libros):
        HU-02-07 Registro de devolucion
        HU-02-08 Generacion de multas por entrega extemporanea, dano y
                 perdida (el envio a Tesoreria esta en multa_servicio.py)

    Al registrar la devolucion se identifica si hubo retraso, dano o
    perdida y se generan las multas en la misma operacion.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    13/11/2026
============================================================
"""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import config
from models import devolucion as devolucion_modelo
from models import ejemplar as ejemplar_modelo
from models import lista_espera as espera_modelo
from models import multa as multa_modelo
from models import precio as precio_modelo
from models import prestamo as prestamo_modelo
from services import multa_servicio
from services.errores import ErrorValidacion
from services.multa_servicio import formatear_monto

# Como queda cada cosa segun lo que paso con el libro.
CIERRES = {
    config.RESULTADO_BUENO: {
        "estado_prestamo": config.ESTADO_PRESTAMO_DEVUELTO,
        "estado_ejemplar": config.ESTADO_DISPONIBLE,
        "condicion": config.CONDICION_BUENO,
    },
    config.RESULTADO_DANADO: {
        "estado_prestamo": config.ESTADO_PRESTAMO_DEVUELTO,
        "estado_ejemplar": config.ESTADO_EJEMPLAR_DANADO,
        "condicion": config.CONDICION_DANADO,
    },
    config.RESULTADO_PERDIDO: {
        "estado_prestamo": config.ESTADO_PRESTAMO_PERDIDO,
        "estado_ejemplar": config.ESTADO_EJEMPLAR_PERDIDO,
        "condicion": None,
    },
}

# ============================================================
# CONSULTAS
# ============================================================


def obtener_opciones_formulario():
    """
    Descripcion:
        HU-02-07: Ejemplares prestados para las sugerencias del formulario.

    Parametros:
        Ninguno.

    Salida:
        dict: prestados.
    """
    return {"prestados": devolucion_modelo.listar_prestados()}


def listar_recientes():
    """
    Descripcion:
        HU-02-07: Ultimas devoluciones y perdidas registradas.

    Parametros:
        Ninguno.

    Salida:
        list[sqlite3.Row]: prestamos cerrados.
    """
    return devolucion_modelo.listar_recientes()


def buscar_prestamo(codigo):
    """
    Descripcion:
        HU-02-07: Busca el prestamo activo del ejemplar que se devuelve.

    Parametros:
        codigo (str): codigo del ejemplar capturado.

    Salida:
        sqlite3.Row: prestamo activo.

    Excepciones:
        ErrorValidacion si no se capturo el codigo, el ejemplar no existe o
        no esta prestado.
    """
    codigo = (codigo or "").strip().upper()
    valores = {"ejemplar": codigo}
    if not codigo:
        error = "Captura el código del ejemplar (por ejemplo EJ-0019)."
        raise ErrorValidacion(error, {"ejemplar": error}, valores)

    prestamo = devolucion_modelo.obtener_prestamo_activo(codigo)
    if prestamo is not None:
        return prestamo

    # HU-02-07 · Ejemplar inexistente o que no esta prestado.
    ejemplar = ejemplar_modelo.obtener_por_codigo(codigo)
    if ejemplar is None:
        error = f"No existe un ejemplar con el código {codigo}."
        codigo_http = 404
    else:
        error = (
            f"El ejemplar {codigo} no tiene un préstamo activo (estado: "
            f"{ejemplar['estado']})."
        )
        codigo_http = 409
    raise ErrorValidacion(error, {"ejemplar": error}, valores, codigo_http)


# ============================================================
# CALCULO DE MULTAS (HU-02-08)
# ============================================================


def calcular_retraso(prestamo, dia=None):
    """
    Descripcion:
        HU-02-08 · Entrega extemporanea: dias de retraso por la multa diaria
        del perfil del usuario.

    Parametros:
        prestamo (sqlite3.Row): prestamo.
        dia (date o None): dia de la devolucion; hoy si no se da.

    Salida:
        dict con dias, monto y descripcion, o None si no hay retraso.
    """
    dia = dia or date.today()
    dias = (dia - date.fromisoformat(prestamo["fecha_vencimiento"])).days
    multa_diaria = float(prestamo["multa_diaria"] or 0)
    if dias <= 0 or not multa_diaria:
        return None
    return {
        "dias": dias,
        "monto": round(dias * multa_diaria, 2),
        "descripcion": (
            f"{dias} día(s) de retraso × ${multa_diaria:,.2f} por día"
        ),
    }


def calcular_reposicion(prestamo):
    """
    Descripcion:
        HU-02-08 · Perdida: el usuario paga el ultimo precio registrado del
        libro; si esta en dolares se convierte con el tipo de cambio
        vigente.

    Parametros:
        prestamo (sqlite3.Row): prestamo.

    Salida:
        dict con monto y descripcion, o con monto None y el motivo cuando no
        se puede calcular (el bibliotecario captura el costo).
    """
    precio = precio_modelo.obtener_ultimo(prestamo["libro_id"])
    if precio is None:
        return {
            "monto": None,
            "motivo": "El libro no tiene precio registrado.",
        }
    valor = float(precio["precio"])
    fecha = datetime.strptime(precio["fecha_registro"], "%Y-%m-%d")
    if precio["moneda"] == config.MONEDA_LOCAL:
        return {
            "monto": round(valor, 2),
            "descripcion": (
                f"Reposición: último precio ${valor:,.2f} MXN "
                f"(registrado el {fecha:%d/%m/%Y})"
            ),
        }

    # Precio en otra moneda: aplicamos el tipo de cambio vigente.
    cambio = precio_modelo.obtener_tipo_cambio_vigente(precio["moneda"])
    if cambio is None:
        return {
            "monto": None,
            "motivo": (
                f"El precio del libro está en {precio['moneda']} y no hay "
                "tipo de cambio registrado."
            ),
        }
    tipo = float(cambio["valor_mxn"])
    fecha_cambio = datetime.strptime(cambio["fecha"], "%Y-%m-%d")
    return {
        "monto": round(valor * tipo, 2),
        "descripcion": (
            f"Reposición: último precio ${valor:,.2f} {precio['moneda']} × "
            f"${tipo:,.4f} (tipo de cambio del {fecha_cambio:%d/%m/%Y})"
        ),
    }


def preparar(prestamo):
    """
    Descripcion:
        HU-02-07: Datos para la pantalla de devolucion: la multa por retraso
        que se generaria hoy y el costo de reposicion por si se perdio.

    Parametros:
        prestamo (sqlite3.Row): prestamo activo.

    Salida:
        dict: retraso (dict o None) y reposicion (dict).
    """
    return {
        "retraso": calcular_retraso(prestamo),
        "reposicion": calcular_reposicion(prestamo),
    }


def _convertir_monto(texto):
    """
    Descripcion:
        Convierte el monto capturado (acepta $ y comas) a numero con dos
        decimales.

    Parametros:
        texto (str): monto capturado, por ejemplo $1,250.50.

    Salida:
        float o None si no es un monto valido entre 0.01 y el maximo.
    """
    limpio = (texto or "").replace("$", "").replace(",", "").strip()
    try:
        monto = Decimal(limpio).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None
    if not Decimal("0.01") <= monto <= config.MONTO_MAXIMO_MULTA:
        return None
    return float(monto)


def validar(prestamo, formulario):
    """
    Descripcion:
        HU-02-07 y HU-02-08: Valida lo que paso con el libro y arma el cierre
        del prestamo con sus multas.

    Parametros:
        prestamo (sqlite3.Row): prestamo activo.
        formulario (werkzeug.datastructures.MultiDict o dict): resultado,
            observaciones, monto_dano y monto_reposicion.

    Salida:
        tuple[dict, list[dict]]: cierre (estados, condicion y
        observaciones) y multas (motivo, monto y descripcion).

    Excepciones:
        ErrorValidacion con el error de cada campo y lo capturado.
    """
    valores = {
        campo: (formulario.get(campo) or "").strip()
        for campo in (
            "resultado",
            "observaciones",
            "monto_dano",
            "monto_reposicion",
        )
    }
    resultado = valores["resultado"]
    errores = {}
    multas = []

    if resultado not in CIERRES:
        errores["resultado"] = "Elige qué pasó con el libro."
    if len(valores["observaciones"]) > config.LONGITUD_MAXIMA_OBSERVACIONES:
        errores["observaciones"] = (
            "Las observaciones admiten hasta "
            f"{config.LONGITUD_MAXIMA_OBSERVACIONES} caracteres."
        )

    # HU-02-08 · Dano: se describe y el bibliotecario captura el monto.
    if resultado == config.RESULTADO_DANADO:
        if not valores["observaciones"]:
            errores["observaciones"] = "Describe el daño que tiene el libro."
        monto = _convertir_monto(valores["monto_dano"])
        if monto is None:
            errores["monto_dano"] = (
                "Captura el monto por el daño, por ejemplo 150.00."
            )
        elif "observaciones" not in errores:
            multas.append(
                {
                    "motivo": config.MOTIVO_DANO,
                    "monto": monto,
                    "descripcion": f"Daño: {valores['observaciones']}"[:255],
                }
            )

    # HU-02-08 · Perdida: ultimo precio del libro o costo capturado.
    if resultado == config.RESULTADO_PERDIDO:
        reposicion = calcular_reposicion(prestamo)
        if reposicion["monto"] is None:
            monto = _convertir_monto(valores["monto_reposicion"])
            if monto is None:
                errores["monto_reposicion"] = (
                    f"{reposicion['motivo']} Captura el costo de reposición."
                )
            else:
                reposicion = {
                    "monto": monto,
                    "descripcion": (
                        "Reposición: costo capturado por el bibliotecario"
                    ),
                }
        if reposicion["monto"] is not None:
            multas.append({"motivo": config.MOTIVO_PERDIDA, **reposicion})

    if errores:
        raise ErrorValidacion(
            "No se puede registrar la devolución. Revisa los datos marcados.",
            errores,
            valores,
            codigo=422,
        )

    # HU-02-08 · Entrega extemporanea (tambien si se perdio ya vencido).
    retraso = calcular_retraso(prestamo)
    if retraso:
        multas.insert(
            0,
            {
                "motivo": config.MOTIVO_RETRASO,
                "monto": retraso["monto"],
                "descripcion": retraso["descripcion"],
            },
        )
    cierre = {
        **CIERRES[resultado],
        "observaciones": valores["observaciones"],
    }
    return cierre, multas


# ============================================================
# REGISTRO DE LA DEVOLUCION (HU-02-07)
# ============================================================


def registrar(codigo, formulario, bibliotecario_id):
    """
    Descripcion:
        HU-02-07 y HU-02-08: Registra la devolucion (o la perdida), genera
        las multas y las manda a Tesoreria.

    Parametros:
        codigo (str): codigo del ejemplar.
        formulario (werkzeug.datastructures.MultiDict o dict): lo que paso
            con el libro.
        bibliotecario_id (int): id de quien recibe el libro.

    Salida:
        tuple[int, list[tuple[str, str]]]: id del prestamo y los avisos
        (tono, mensaje) para la pantalla del resultado.

    Excepciones:
        ErrorValidacion si el ejemplar ya no esta prestado o falta algun
        dato.
    """
    prestamo = buscar_prestamo(codigo)
    cierre, multas = validar(prestamo, formulario)
    ids = devolucion_modelo.registrar(
        prestamo, bibliotecario_id, cierre, multas
    )
    if ids is None:
        raise ErrorValidacion(
            "La devolución de este préstamo ya se había registrado.",
            codigo=409,
        )

    # Mensaje del registro.
    perdido = cierre["estado_prestamo"] == config.ESTADO_PRESTAMO_PERDIDO
    accion = "Pérdida" if perdido else "Devolución"
    if not multas:
        avisos = [
            (
                "exito",
                f"{accion} del préstamo {prestamo['folio']} registrada "
                "sin multas.",
            )
        ]
        return prestamo["id"], avisos
    total = formatear_monto(sum(m["monto"] for m in multas))
    avisos = [
        (
            "exito",
            f"{accion} del préstamo {prestamo['folio']} registrada. Se "
            f"generó {len(multas)} multa(s) por {total}.",
        )
    ]

    # HU-02-08 · Las multas se mandan a Tesoreria en ese momento; si falla
    # el correo quedan pendientes de envio.
    try:
        avisos.append(
            multa_servicio.enviar_a_tesoreria(
                multa_modelo.listar_de_prestamo(prestamo["id"])
            )
        )
    except ErrorValidacion as error:
        avisos.append(
            (
                "advertencia",
                f"No se pudo enviar a Tesorería: {error.mensaje} Reintenta "
                "desde Multas.",
            )
        )
    return prestamo["id"], avisos


def obtener_resultado(prestamo_id):
    """
    Descripcion:
        HU-02-07: Junta lo que se registro al cerrar el prestamo: la
        devolucion, las multas y, si el ejemplar quedo disponible, cuantas
        personas esperan el libro (HU-02-06).

    Parametros:
        prestamo_id (int): id del prestamo.

    Salida:
        dict con prestamo, devolucion, multas, total y en_espera, o None si
        el prestamo no existe o sigue activo.
    """
    prestamo = prestamo_modelo.obtener(prestamo_id)
    if prestamo is None or (
        prestamo["estado"] == config.ESTADO_PRESTAMO_ACTIVO
    ):
        return None
    devolucion = devolucion_modelo.obtener(prestamo_id)
    multas = multa_modelo.listar_de_prestamo(prestamo_id)

    # Si el ejemplar regreso en buen estado, le toca al turno 1 de la lista.
    en_espera = 0
    if devolucion and devolucion["condicion"] == config.CONDICION_BUENO:
        libro = espera_modelo.obtener_libro(prestamo["libro_clave"])
        en_espera = libro["en_espera"] if libro else 0
    return {
        "prestamo": prestamo,
        "devolucion": devolucion,
        "multas": multas,
        "total": sum(m["monto"] for m in multas),
        "pendientes": [
            m for m in multas if m["estado"] == config.ESTADO_MULTA_PENDIENTE
        ],
        "en_espera": en_espera,
    }
