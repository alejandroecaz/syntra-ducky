"""
============================================================
Archivo:      services/catalogo_servicio.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Servicio del catalogo: busqueda, ficha del libro, libros y ejemplares.

    Cubre HU-01-09 a HU-01-15. Lo usan el catalogo web y el portal movil,
    por eso la busqueda y la ficha se comportan igual en los dos.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================

============================================================
Contenido del listado:
    Importaciones
        re, datetime
        config
        models: autor, editorial, ejemplar, libro, tema, ubicacion
        services.errores.ErrorValidacion
    Constantes
        CAMPOS_VALIDOS, CAMPOS_LIBRO, OBLIGATORIOS_LIBRO, CAMPOS_EJEMPLAR
    Busqueda y consulta (HU-01-12 y HU-01-13)
        verificar_personal()
        obtener_vista_permitida()
        validar_campo()
        buscar_libros()
        listar_catalogo()
        verificar_catalogo()
        listar_destacados()
        obtener_resumen()
        obtener_libro()
        obtener_ficha()
        obtener_estado_libro()
    Alta, actualizacion y baja de libros (HU-01-09 a HU-01-11)
        obtener_opciones_libro()
        obtener_valores_edicion()
        separar_autores()
        _validar_isbn()
        validar_libro()
        _preparar_datos()
        registrar_libro()
        actualizar_libro()
        dar_baja()
    Ejemplares (HU-01-14 y HU-01-15)
        obtener_opciones_ejemplar()
        obtener_ejemplar()
        _validar_ejemplar()
        _obtener_estante()
        agregar_ejemplar()
        actualizar_ejemplar()
============================================================
"""

import re
from datetime import date

import config
from models import autor as autor_modelo
from models import editorial as editorial_modelo
from models import ejemplar as ejemplar_modelo
from models import libro as libro_modelo
from models import tema as tema_modelo
from models import ubicacion as ubicacion_modelo
from services.errores import ErrorValidacion

# Campos por los que se puede buscar (HU-01-13).
CAMPOS_VALIDOS = {campo for campo, _ in config.CAMPOS_BUSQUEDA}

# Campos del formulario de libro y los obligatorios con su etiqueta para el
# mensaje (HU-01-09).
CAMPOS_LIBRO = (
    "clave",
    "titulo",
    "autores",
    "tema",
    "editorial",
    "anio",
    "isbn",
    "edicion",
    "tipo_acceso",
    "sinopsis",
)
OBLIGATORIOS_LIBRO = {
    "clave": "la clave",
    "titulo": "el título",
    "autores": "al menos un autor",
    "tema": "el tema",
    "editorial": "la editorial",
}

# Campos del formulario de ejemplar (HU-01-14 y HU-01-15).
CAMPOS_EJEMPLAR = ("estancia", "estante", "posicion", "estado")


# ============================================================
# BUSQUEDA Y CONSULTA (HU-01-12 Y HU-01-13)
# Valida los criterios, busca libros y arma la ficha con sus ejemplares.
# ============================================================


def verificar_personal(permisos):
    """
    Descripcion:
        Revisa si los permisos son de personal de biblioteca, que puede ver
        libros dados de baja.

    Parametros:
        permisos (list[str]): permisos del perfil.

    Salida:
        bool: True si es personal de biblioteca.
    """
    return any(permiso in permisos for permiso in config.PERMISOS_PERSONAL)


def obtener_vista_permitida(vista, personal):
    """
    Descripcion:
        Decide que vista del catalogo se muestra: solo el personal puede ver
        libros dados de baja.

    Parametros:
        vista (str): vista pedida ('activos', 'baja' o 'todos').
        personal (bool): True si es personal de biblioteca.

    Salida:
        str: vista permitida.
    """
    return (
        vista
        if personal and vista in config.VISTAS_CATALOGO
        else config.VISTAS_CATALOGO[0]
    )


def validar_campo(campo):
    """
    Descripcion:
        Valida el campo de busqueda; si no es valido usa el predeterminado
        (titulo).

    Parametros:
        campo (str): campo pedido.

    Salida:
        str: campo valido.
    """
    return (
        campo
        if campo in CAMPOS_VALIDOS
        else config.CAMPO_BUSQUEDA_PREDETERMINADO
    )


def buscar_libros(campo, texto, vista="activos"):
    """
    Descripcion:
        HU-01-13: Busqueda por filtros. La clave se busca exacta; titulo,
        autor, tema y editorial por coincidencia, sin importar acentos ni
        mayusculas. Si el texto esta vacio o solo tiene espacios no se busca y
        se regresa el mensaje para pedir un criterio.

    Parametros:
        campo (str): campo de busqueda.
        texto (str): texto capturado.
        vista (str): vista del catalogo.

    Salida:
        dict: campo, texto, libros y error (mensaje o None).
    """
    # Validamos el campo y limpiamos el texto.
    campo = validar_campo(campo)
    texto = (texto or "").strip()

    # HU-01-13 · Criterio vacio: no se busca y se pide un criterio.
    if not texto:
        return {
            "campo": campo,
            "texto": texto,
            "libros": [],
            "error": config.MENSAJES["busqueda_vacia"],
        }

    # HU-01-13 · Busqueda por titulo, autor, tema, editorial o clave exacta (o
    # Sin coincidencias).
    libros = libro_modelo.listar(campo=campo, texto=texto, estado=vista)
    return {"campo": campo, "texto": texto, "libros": libros, "error": None}


def listar_catalogo(vista="activos"):
    """
    Descripcion:
        HU-01-12 · Mostrar catalogo: lista todos los libros de la vista.

    Parametros:
        vista (str): vista del catalogo.

    Salida:
        list[sqlite3.Row]: libros.
    """
    return libro_modelo.listar(estado=vista)


def verificar_catalogo(vista):
    """
    Descripcion:
        HU-01-12 · Catalogo vacio: revisa si hay libros que mostrar.

    Parametros:
        vista (str): vista del catalogo.

    Salida:
        bool: False solo cuando no existe ningun libro activo.
    """
    return bool(libro_modelo.listar(estado="activos")) or vista != "activos"


def listar_destacados():
    """
    Descripcion:
        Lista los libros con ejemplares disponibles para la pantalla de inicio
        del portal movil.

    Parametros:
        Ninguno.

    Salida:
        list[sqlite3.Row]: libros destacados.
    """
    return libro_modelo.listar_destacados(config.MOVIL_LIBROS_DESTACADOS)


def obtener_resumen():
    """
    Descripcion:
        Obtiene los totales de libros activos, ejemplares y disponibles.

    Parametros:
        Ninguno.

    Salida:
        sqlite3.Row: totales.
    """
    return libro_modelo.contar()


def obtener_libro(libro_id, permitir_baja=False):
    """
    Descripcion:
        Busca un libro; los dados de baja solo se regresan si se permite
        verlos.

    Parametros:
        libro_id (int): id del libro.
        permitir_baja (bool): True para incluir libros dados de baja.

    Salida:
        sqlite3.Row o None.
    """
    libro = libro_modelo.obtener_por_id(libro_id)
    if libro is None or (not libro["activo"] and not permitir_baja):
        return None
    return libro


def obtener_ficha(libro_id, permitir_baja=False):
    """
    Descripcion:
        HU-01-12 · Abrir detalle, HU-01-14 y HU-01-15: junta el libro con sus
        ejemplares (ubicacion y estado) y sus operaciones vigentes.

    Parametros:
        libro_id (int): id del libro.
        permitir_baja (bool): True para incluir libros dados de baja.

    Salida:
        dict con libro, ejemplares y operaciones, o None si no hay ficha.
    """
    # Si el libro no existe (o no se puede ver) no hay ficha.
    libro = obtener_libro(libro_id, permitir_baja)
    if libro is None:
        return None

    # Juntamos el libro con sus ejemplares (ubicacion y estado) y sus
    # operaciones vigentes.
    return {
        "libro": libro,
        "ejemplares": ejemplar_modelo.listar_de_libro(libro_id),
        "operaciones": ejemplar_modelo.listar_operaciones_vigentes(libro_id),
    }


def obtener_estado_libro(libro):
    """
    Descripcion:
        HU-01-15: Arma el texto del estado del libro para listados y PDF.

    Parametros:
        libro (sqlite3.Row): libro con activo, total_ejemplares y disponibles.

    Salida:
        str: Dado de baja, Sin ejemplares, No disponible o Disponible (n de m).
    """
    if not libro["activo"]:
        return "Dado de baja"
    # HU-01-15 · Libro sin ejemplares.
    if libro["total_ejemplares"] == 0:
        return "Sin ejemplares"
    # HU-01-15 · Ejemplar no disponible / Ejemplar disponible.
    if libro["disponibles"] == 0:
        return "No disponible"
    return (
        f"Disponible ({libro['disponibles']} de {libro['total_ejemplares']})"
    )


# ============================================================
# ALTA, ACTUALIZACION Y BAJA DE LIBROS (HU-01-09 A HU-01-11)
# Valida el formulario del libro, lo registra, lo corrige o lo da de baja.
# ============================================================


def obtener_opciones_libro():
    """
    Descripcion:
        Obtiene las listas para el formulario del libro.

    Parametros:
        Ninguno.

    Salida:
        dict: temas, editoriales y tipos_acceso.
    """
    return {
        "temas": tema_modelo.listar_nombres(),
        "editoriales": editorial_modelo.listar_nombres(),
        "tipos_acceso": config.TIPOS_ACCESO,
    }


def obtener_valores_edicion(libro):
    """
    Descripcion:
        HU-01-11: Obtiene los datos actuales del libro para llenar el
        formulario de edicion. Los autores van en un solo campo separados por
        el separador.

    Parametros:
        libro (sqlite3.Row): libro a editar.

    Salida:
        dict: valor de cada campo del formulario.
    """
    # Copiamos los datos del libro (None se muestra como vacio).
    valores = {
        campo: libro[campo] if libro[campo] is not None else ""
        for campo in CAMPOS_LIBRO
        if campo != "autores"
    }
    # Los autores se muestran en un solo campo separados por el separador.
    valores["autores"] = f"{config.SEPARADOR_AUTORES} ".join(
        libro_modelo.obtener_nombres_autores(libro["id"])
    )
    return valores


def separar_autores(texto):
    """
    Descripcion:
        Separa el texto de autores, por ejemplo 'A; B; A' -> ['A', 'B'], sin
        vacios ni repetidos y en el orden capturado.

    Parametros:
        texto (str): autores separados por config.SEPARADOR_AUTORES.

    Salida:
        list[str]: nombres de los autores.
    """
    autores = []
    for nombre in (texto or "").split(config.SEPARADOR_AUTORES):
        # Quitamos espacios de mas y saltamos vacios y repetidos.
        nombre = " ".join(nombre.split())
        if nombre and nombre.lower() not in (
            autor.lower() for autor in autores
        ):
            autores.append(nombre)
    return autores


def _validar_isbn(isbn):
    """
    Descripcion:
        Valida que el ISBN tenga 10 digitos (el ultimo puede ser X) o 13
        digitos, sin contar guiones ni espacios.

    Parametros:
        isbn (str): ISBN capturado.

    Salida:
        bool: True si el formato es valido.
    """
    limpio = isbn.replace("-", "").replace(" ", "").upper()
    return bool(
        re.fullmatch(r"\d{9}[\dX]", limpio) or re.fullmatch(r"\d{13}", limpio)
    )


def validar_libro(formulario, exigir_clave, libro_id=None):
    """
    Descripcion:
        HU-01-09 y HU-01-11: Valida el formulario del libro sin guardar nada.
        Al editar, la clave no se pide porque no cambia.

    Parametros:
        formulario (werkzeug.datastructures.MultiDict): datos capturados.
        exigir_clave (bool): True en el alta, False en la edicion.
        libro_id (int o None): id del libro que se edita.

    Salida:
        tuple[dict, dict, bool]: valores, errores por campo y si faltan
        obligatorios.
    """
    # Leemos y limpiamos los campos del formulario.
    valores = {
        campo: (formulario.get(campo) or "").strip() for campo in CAMPOS_LIBRO
    }
    errores = {}

    # HU-01-09 · Datos bibliograficos incompletos / HU-01-11 · Edicion
    # incompleta
    # (al editar, la clave no se pide porque no cambia).
    obligatorios = (
        OBLIGATORIOS_LIBRO
        if exigir_clave
        else {
            campo: etiqueta
            for campo, etiqueta in OBLIGATORIOS_LIBRO.items()
            if campo != "clave"
        }
    )
    for campo, etiqueta in obligatorios.items():
        if not valores[campo]:
            errores[campo] = f"Captura {etiqueta}."
    if valores["autores"] and not separar_autores(valores["autores"]):
        errores["autores"] = "Captura al menos un autor."
    faltan = bool(errores)

    # Formato de los campos opcionales: anio, ISBN y tipo de acceso.
    anio_actual = date.today().year
    if valores["anio"] and (
        not valores["anio"].isdigit()
        or not config.ANIO_MINIMO_PUBLICACION
        <= int(valores["anio"])
        <= anio_actual
    ):
        errores["anio"] = (
            f"Escribe un año entre {config.ANIO_MINIMO_PUBLICACION} y "
            f"{anio_actual}."
        )
    if valores["isbn"]:
        if not _validar_isbn(valores["isbn"]):
            errores["isbn"] = "Escribe un ISBN de 10 o 13 dígitos."
        elif libro_modelo.verificar_isbn_en_uso(
            valores["isbn"], excluir_id=libro_id
        ):
            errores["isbn"] = "Ese ISBN ya pertenece a otro libro."
    if not valores["tipo_acceso"]:
        valores["tipo_acceso"] = config.TIPOS_ACCESO[0]
    elif valores["tipo_acceso"] not in config.TIPOS_ACCESO:
        errores["tipo_acceso"] = "Selecciona un tipo de acceso válido."
    return valores, errores, faltan


def _preparar_datos(valores):
    """
    Descripcion:
        Convierte los textos del formulario en ids de editorial, tema y
        autores; los que son nuevos se registran.

    Parametros:
        valores (dict): valores validados del formulario.

    Salida:
        tuple[dict, list[int]]: datos del libro e ids de los autores en orden.
    """
    # Datos del libro; editorial y tema se registran si son nuevos.
    datos = {
        "clave": valores["clave"].upper(),
        "titulo": valores["titulo"],
        "editorial_id": editorial_modelo.obtener_o_crear(valores["editorial"]),
        "tema_id": tema_modelo.obtener_o_crear(valores["tema"]),
        "anio": int(valores["anio"]) if valores["anio"] else None,
        "isbn": valores["isbn"] or None,
        "edicion": valores["edicion"] or None,
        "sinopsis": valores["sinopsis"] or None,
        "tipo_acceso": valores["tipo_acceso"],
    }

    # Ids de los autores en el orden capturado, sin repetir.
    autores_ids = []
    for nombre in separar_autores(valores["autores"]):
        autor_id = autor_modelo.obtener_o_crear(nombre)
        if autor_id not in autores_ids:
            autores_ids.append(autor_id)
    return datos, autores_ids


def registrar_libro(formulario):
    """
    Descripcion:
        HU-01-09: Alta de libro. No crea ejemplares.

    Parametros:
        formulario (werkzeug.datastructures.MultiDict): datos capturados.

    Salida:
        tuple[int, str]: id del libro y mensaje de exito.

    Excepciones:
        ErrorValidacion si faltan datos obligatorios, algun formato no es
        valido o la clave ya existe.
    """
    # Validamos el formulario.
    valores, errores, faltan = validar_libro(formulario, exigir_clave=True)

    # HU-01-09 · Clave duplicada.
    clave_duplicada = bool(
        valores["clave"]
    ) and libro_modelo.verificar_clave_existente(valores["clave"])
    if clave_duplicada:
        errores["clave"] = "La clave del libro ya existe"

    # Si algo fallo no se registra nada y se explica por que.
    if errores:
        if clave_duplicada:
            mensaje = (
                "La clave del libro ya existe. No se duplicó ni se "
                "sobrescribió el libro registrado."
            )
        elif faltan:
            mensaje = (
                "Faltan datos bibliográficos obligatorios. El libro no "
                "se registró."
            )
        else:
            mensaje = "Revisa los campos marcados. El libro no se registró."
        raise ErrorValidacion(mensaje, errores, valores)

    # HU-01-09 · Alta exitosa.
    datos, autores_ids = _preparar_datos(valores)
    libro_id = libro_modelo.crear(datos, autores_ids)
    mensaje = (
        f"Libro registrado: {datos['titulo']} ({datos['clave']}). "
        "Aún no tiene ejemplares; agrégalos desde su ficha."
    )
    return libro_id, mensaje


def actualizar_libro(libro, formulario):
    """
    Descripcion:
        HU-01-11: Actualizacion de libro. Conserva la clave y los ejemplares.

    Parametros:
        libro (sqlite3.Row): libro a editar.
        formulario (werkzeug.datastructures.MultiDict): datos capturados.

    Salida:
        str: mensaje de exito.

    Excepciones:
        ErrorValidacion si faltan campos obligatorios o algun formato no es
        valido; los datos guardados no cambian.
    """
    # Validamos el formulario; la clave se conserva la del libro.
    valores, errores, faltan = validar_libro(
        formulario, exigir_clave=False, libro_id=libro["id"]
    )
    valores["clave"] = libro["clave"]

    # HU-01-11 · Edicion incompleta: se mantienen los datos guardados.
    if errores:
        mensaje = (
            "Faltan campos obligatorios. Se mantienen los datos guardados."
            if faltan
            else "Revisa los campos marcados. Se mantienen los datos "
            "guardados."
        )
        raise ErrorValidacion(mensaje, errores, valores)

    # HU-01-11 · Correccion exitosa.
    datos, autores_ids = _preparar_datos(valores)
    libro_modelo.actualizar(libro["id"], datos, autores_ids)
    return (
        "Libro actualizado correctamente. Su clave y sus ejemplares se "
        "conservan."
    )


def dar_baja(libro):
    """
    Descripcion:
        HU-01-10: Baja logica del libro. No se permite si tiene ejemplares
        prestados o reservados.

    Parametros:
        libro (sqlite3.Row): libro a dar de baja.

    Salida:
        tuple[bool, str, str]: si se dio de baja, categoria del aviso y
        mensaje.
    """
    # Si ya estaba dado de baja no hay nada que hacer.
    if not libro["activo"]:
        return False, "informacion", "El libro ya estaba dado de baja."

    # HU-01-10 · Libro con operaciones vigentes: no se permite la baja.
    vigentes = ejemplar_modelo.listar_operaciones_vigentes(libro["id"])
    if vigentes:
        detalle = ", ".join(
            f"{operacion['codigo']} ({operacion['estado'].lower()})"
            for operacion in vigentes
        )
        return (
            False,
            "error",
            (
                "No se puede dar de baja: existen operaciones vigentes en "
                f"{detalle}. "
                "El libro y sus ejemplares no cambiaron."
            ),
        )

    # HU-01-10 · Baja logica de libro: se marca inactivo y se conserva su
    # informacion.
    libro_modelo.dar_baja(libro["id"])
    return (
        True,
        "exito",
        (
            f'"{libro["titulo"]}" fue dado de baja. Ya no aparece en el '
            "catálogo de usuarios "
            "y su información se conserva para consulta administrativa."
        ),
    )


# ============================================================
# EJEMPLARES (HU-01-14 Y HU-01-15)
# Valida la ubicacion y el estado de cada ejemplar y los guarda.
# ============================================================


def obtener_opciones_ejemplar():
    """
    Descripcion:
        Obtiene las listas para los formularios de ejemplar.

    Parametros:
        Ninguno.

    Salida:
        dict: estados y estancias.
    """
    return {
        "estados": config.ESTADOS_EJEMPLAR,
        "estancias": ubicacion_modelo.listar_estancias(),
    }


def obtener_ejemplar(ejemplar_id):
    """
    Descripcion:
        Busca un ejemplar por su id.

    Parametros:
        ejemplar_id (int): id del ejemplar.

    Salida:
        sqlite3.Row o None.
    """
    return ejemplar_modelo.obtener(ejemplar_id)


def _validar_ejemplar(formulario):
    """
    Descripcion:
        Valida la ubicacion y el estado del ejemplar. La ubicacion va completa
        (estancia, estante y posicion) o vacia si esta pendiente.

    Parametros:
        formulario (werkzeug.datastructures.MultiDict): datos capturados.

    Salida:
        tuple[dict, list[str]]: valores y mensajes de error.
    """
    # Leemos los campos del formulario.
    valores = {
        campo: (formulario.get(campo) or "").strip()
        for campo in CAMPOS_EJEMPLAR
    }
    errores = []

    # HU-01-14: la ubicacion va completa (estancia, estante y posicion) o vacia
    # si esta pendiente.
    ubicacion = [valores["estancia"], valores["estante"], valores["posicion"]]
    if any(ubicacion) and not all(ubicacion):
        errores.append(
            "Completa estancia, estante y posición, o deja los tres vacíos "
            "si la ubicación está pendiente."
        )
    elif valores["estancia"]:
        estancia = (
            ubicacion_modelo.obtener_estancia(valores["estancia"])
            if valores["estancia"].isdigit()
            else None
        )
        if estancia is None:
            errores.append("Selecciona una estancia válida.")

    # HU-01-15: el estado debe ser uno de los definidos en config.
    if valores["estado"] not in config.ESTADOS_EJEMPLAR:
        errores.append("Selecciona un estado válido para el ejemplar.")
    return valores, errores


def _obtener_estante(valores):
    """
    Descripcion:
        Obtiene el id del estante capturado; si es nuevo lo registra.

    Parametros:
        valores (dict): valores validados del ejemplar.

    Salida:
        int o None si la ubicacion esta pendiente.
    """
    if not valores["estancia"]:
        return None
    return ubicacion_modelo.obtener_o_crear_estante(
        int(valores["estancia"]), valores["estante"].upper()
    )


def agregar_ejemplar(libro_id, formulario):
    """
    Descripcion:
        HU-01-14 y HU-01-15: Registra un ejemplar del libro con su ubicacion y
        estado.

    Parametros:
        libro_id (int): id del libro.
        formulario (werkzeug.datastructures.MultiDict): datos capturados.

    Salida:
        tuple[str, str]: categoria del aviso y mensaje.
    """
    # Validamos; si hay errores no se agrega nada.
    valores, errores = _validar_ejemplar(formulario)
    if errores:
        return "error", " ".join(errores) + " No se agregó el ejemplar."

    # Guardamos el ejemplar con su ubicacion y estado.
    codigo = ejemplar_modelo.agregar(
        libro_id,
        _obtener_estante(valores),
        valores["posicion"] or None,
        valores["estado"],
    )
    return "exito", f"Ejemplar {codigo} agregado como {valores['estado']}."


def actualizar_ejemplar(ejemplar, formulario):
    """
    Descripcion:
        HU-01-15 · Disponibilidad actualizada: cambia la ubicacion y el estado
        del ejemplar.

    Parametros:
        ejemplar (sqlite3.Row): ejemplar a cambiar.
        formulario (werkzeug.datastructures.MultiDict): datos capturados.

    Salida:
        tuple[str, str]: categoria del aviso y mensaje.
    """
    # Validamos; si hay errores el ejemplar conserva sus datos.
    valores, errores = _validar_ejemplar(formulario)
    if errores:
        return "error", " ".join(errores) + " El ejemplar conserva sus datos."

    # Guardamos la nueva ubicacion y estado.
    ejemplar_modelo.actualizar(
        ejemplar["id"],
        _obtener_estante(valores),
        valores["posicion"] or None,
        valores["estado"],
    )
    return (
        "exito",
        f"Ejemplar {ejemplar['codigo']} actualizado: {valores['estado']}.",
    )
