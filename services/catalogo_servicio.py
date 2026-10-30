# ============================================================
# Archivo: services/catalogo_servicio.py
# Proyecto: Sistema Ducky de Gestión Bibliotecaria
# Syntra Technologies - Equipo 1 - Sprint 1
# Materia: Ingeniería de Software
# Autores:
#   - Melissa Silva Vázquez                #624352
#   - Tomás Zapata Pérez                   #629048
#   - Alejandro Evaristo Cazares Escobedo  #626337
# Descripción: Servicio del catálogo: búsqueda, ficha del libro, libros y ejemplares.
# ============================================================
"""Servicio del catálogo: búsqueda, ficha del libro, libros y ejemplares.

Cubre HU-01-09 a HU-01-15. Lo usan el catálogo web y el portal móvil, por eso la búsqueda
y la ficha se comportan igual en los dos.
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

# Campos por los que se puede buscar (HU-01-13)
CAMPOS_VALIDOS = {campo for campo, _ in config.CAMPOS_BUSQUEDA}

# Campos del formulario de libro y los obligatorios con su etiqueta para el mensaje (HU-01-09)
CAMPOS_LIBRO = ("clave", "titulo", "autores", "tema", "editorial", "anio", "isbn", "edicion", "tipo_acceso",
                "sinopsis")
OBLIGATORIOS_LIBRO = {
    "clave": "la clave",
    "titulo": "el título",
    "autores": "al menos un autor",
    "tema": "el tema",
    "editorial": "la editorial",
}

# Campos del formulario de ejemplar (HU-01-14 y HU-01-15)
CAMPOS_EJEMPLAR = ("estancia", "estante", "posicion", "estado")


# Búsqueda y consulta (HU-01-12 y HU-01-13)

def es_personal(permisos):
    """True si los permisos son de personal de biblioteca (puede ver libros dados de baja)."""
    return any(permiso in permisos for permiso in config.PERMISOS_PERSONAL)


def vista_permitida(vista, personal):
    """Solo el personal puede elegir ver libros dados de baja; los demás ven solo activos."""
    return vista if personal and vista in config.VISTAS_CATALOGO else config.VISTAS_CATALOGO[0]


def campo_valido(campo):
    """El campo de búsqueda si es válido; si no, el predeterminado (título)."""
    return campo if campo in CAMPOS_VALIDOS else config.CAMPO_BUSQUEDA_PREDETERMINADO


def buscar_libros(campo, texto, vista="activos"):
    """HU-01-13: Búsqueda por filtros.

    La clave se busca exacta; título, autor, tema y editorial por coincidencia, sin importar
    acentos ni mayúsculas. Si el texto está vacío o solo tiene espacios no se busca y se
    regresa el mensaje para pedir un criterio.
    Regresa {"campo", "texto", "libros", "error"}.
    """
    # Validamos el campo y limpiamos el texto
    campo = campo_valido(campo)
    texto = (texto or "").strip()

    # HU-01-13 · Criterio vacío: no se busca y se pide un criterio
    if not texto:
        return {"campo": campo, "texto": texto, "libros": [], "error": config.MENSAJES["busqueda_vacia"]}

    # HU-01-13 · Búsqueda por título, autor, tema, editorial o clave exacta (o Sin coincidencias)
    libros = libro_modelo.listar(campo=campo, texto=texto, estado=vista)
    return {"campo": campo, "texto": texto, "libros": libros, "error": None}


def listar_catalogo(vista="activos"):
    """HU-01-12 · Mostrar catálogo: todos los libros de la vista."""
    return libro_modelo.listar(estado=vista)


def hay_catalogo(vista):
    """HU-01-12 · Catálogo vacío: False solo cuando no existe ningún libro activo."""
    return bool(libro_modelo.listar(estado="activos")) or vista != "activos"


def destacados():
    """Libros con ejemplares disponibles para la pantalla de inicio del portal móvil."""
    return libro_modelo.destacados(config.MOVIL_LIBROS_DESTACADOS)


def resumen():
    """Totales de libros activos, ejemplares y disponibles."""
    return libro_modelo.contar()


def obtener_libro(libro_id, permitir_baja=False):
    """El libro o None si no existe (o está dado de baja y no se permite verlo)."""
    libro = libro_modelo.obtener_por_id(libro_id)
    if libro is None or (not libro["activo"] and not permitir_baja):
        return None
    return libro


def ficha(libro_id, permitir_baja=False):
    """HU-01-12 · Abrir detalle, HU-01-14 y HU-01-15: libro con ejemplares y operaciones vigentes, o None."""
    # Si el libro no existe (o no se puede ver) no hay ficha
    libro = obtener_libro(libro_id, permitir_baja)
    if libro is None:
        return None

    # Juntamos el libro con sus ejemplares (ubicación y estado) y sus operaciones vigentes
    return {
        "libro": libro,
        "ejemplares": ejemplar_modelo.de_libro(libro_id),
        "operaciones": ejemplar_modelo.operaciones_vigentes(libro_id),
    }


def estado_libro(libro):
    """HU-01-15: Texto del estado del libro para listados y PDF."""
    if not libro["activo"]:
        return "Dado de baja"
    # HU-01-15 · Libro sin ejemplares
    if libro["total_ejemplares"] == 0:
        return "Sin ejemplares"
    # HU-01-15 · Ejemplar no disponible / Ejemplar disponible
    if libro["disponibles"] == 0:
        return "No disponible"
    return f"Disponible ({libro['disponibles']} de {libro['total_ejemplares']})"


# Alta y actualización de libros (HU-01-09 y HU-01-11)

def opciones_libro():
    """Listas para el formulario del libro."""
    return {
        "temas": tema_modelo.listar_nombres(),
        "editoriales": editorial_modelo.listar_nombres(),
        "tipos_acceso": config.TIPOS_ACCESO,
    }


def valores_edicion(libro):
    """HU-01-11: Datos actuales del libro para llenar el formulario de edición."""
    # Copiamos los datos del libro (None se muestra como vacío)
    valores = {campo: libro[campo] if libro[campo] is not None else "" for campo in CAMPOS_LIBRO
               if campo != "autores"}
    # Los autores se muestran en un solo campo separados por el separador
    valores["autores"] = f"{config.SEPARADOR_AUTORES} ".join(libro_modelo.nombres_autores(libro["id"]))
    return valores


def separar_autores(texto):
    """'A; B; A' -> ['A', 'B'] sin vacíos ni repetidos, en el orden capturado."""
    autores = []
    for nombre in (texto or "").split(config.SEPARADOR_AUTORES):
        # Quitamos espacios de más y saltamos vacíos y repetidos
        nombre = " ".join(nombre.split())
        if nombre and nombre.lower() not in (a.lower() for a in autores):
            autores.append(nombre)
    return autores


def _isbn_valido(isbn):
    """True si el ISBN tiene 10 dígitos (el último puede ser X) o 13 dígitos, sin contar guiones."""
    limpio = isbn.replace("-", "").replace(" ", "").upper()
    return bool(re.fullmatch(r"\d{9}[\dX]", limpio) or re.fullmatch(r"\d{13}", limpio))


def validar_libro(form, exigir_clave, libro_id=None):
    """HU-01-09 y HU-01-11: Regresa (valores, errores, faltan_obligatorios) sin guardar nada."""
    # Leemos y limpiamos los campos del formulario
    valores = {campo: (form.get(campo) or "").strip() for campo in CAMPOS_LIBRO}
    errores = {}

    # HU-01-09 · Datos bibliográficos incompletos / HU-01-11 · Edición incompleta
    # (al editar, la clave no se pide porque no cambia)
    obligatorios = OBLIGATORIOS_LIBRO if exigir_clave else {k: v for k, v in OBLIGATORIOS_LIBRO.items()
                                                            if k != "clave"}
    for campo, etiqueta in obligatorios.items():
        if not valores[campo]:
            errores[campo] = f"Captura {etiqueta}."
    if valores["autores"] and not separar_autores(valores["autores"]):
        errores["autores"] = "Captura al menos un autor."
    faltan = bool(errores)

    # Formato de los campos opcionales: año, ISBN y tipo de acceso
    anio_actual = date.today().year
    if valores["anio"] and (not valores["anio"].isdigit()
                            or not config.ANIO_MINIMO_PUBLICACION <= int(valores["anio"]) <= anio_actual):
        errores["anio"] = f"Escribe un año entre {config.ANIO_MINIMO_PUBLICACION} y {anio_actual}."
    if valores["isbn"]:
        if not _isbn_valido(valores["isbn"]):
            errores["isbn"] = "Escribe un ISBN de 10 o 13 dígitos."
        elif libro_modelo.isbn_en_uso(valores["isbn"], excluir_id=libro_id):
            errores["isbn"] = "Ese ISBN ya pertenece a otro libro."
    if not valores["tipo_acceso"]:
        valores["tipo_acceso"] = config.TIPOS_ACCESO[0]
    elif valores["tipo_acceso"] not in config.TIPOS_ACCESO:
        errores["tipo_acceso"] = "Selecciona un tipo de acceso válido."
    return valores, errores, faltan


def _datos_para_guardar(valores):
    """Convierte los textos del formulario en ids de editorial, tema y autores. Regresa (datos, autores_ids)."""
    # Datos del libro; editorial y tema se registran si son nuevos
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

    # Ids de los autores en el orden capturado, sin repetir
    autores_ids = []
    for nombre in separar_autores(valores["autores"]):
        autor_id = autor_modelo.obtener_o_crear(nombre)
        if autor_id not in autores_ids:
            autores_ids.append(autor_id)
    return datos, autores_ids


def registrar_libro(form):
    """HU-01-09: Alta de libro. No crea ejemplares. Regresa (id, mensaje) o lanza ErrorValidacion."""
    # Validamos el formulario
    valores, errores, faltan = validar_libro(form, exigir_clave=True)

    # HU-01-09 · Clave duplicada
    clave_duplicada = bool(valores["clave"]) and libro_modelo.existe_clave(valores["clave"])
    if clave_duplicada:
        errores["clave"] = "La clave del libro ya existe"

    # Si algo falló no se registra nada y se explica por qué
    if errores:
        if clave_duplicada:
            mensaje = "La clave del libro ya existe. No se duplicó ni se sobrescribió el libro registrado."
        elif faltan:
            mensaje = "Faltan datos bibliográficos obligatorios. El libro no se registró."
        else:
            mensaje = "Revisa los campos marcados. El libro no se registró."
        raise ErrorValidacion(mensaje, errores, valores)

    # HU-01-09 · Alta exitosa
    datos, autores_ids = _datos_para_guardar(valores)
    libro_id = libro_modelo.crear(datos, autores_ids)
    mensaje = (f"Libro registrado: {datos['titulo']} ({datos['clave']}). "
               "Aún no tiene ejemplares; agrégalos desde su ficha.")
    return libro_id, mensaje


def actualizar_libro(libro, form):
    """HU-01-11: Actualización de libro. Conserva clave y ejemplares. Regresa el mensaje."""
    # Validamos el formulario; la clave se conserva la del libro
    valores, errores, faltan = validar_libro(form, exigir_clave=False, libro_id=libro["id"])
    valores["clave"] = libro["clave"]

    # HU-01-11 · Edición incompleta: se mantienen los datos guardados
    if errores:
        mensaje = ("Faltan campos obligatorios. Se mantienen los datos guardados." if faltan
                   else "Revisa los campos marcados. Se mantienen los datos guardados.")
        raise ErrorValidacion(mensaje, errores, valores)

    # HU-01-11 · Corrección exitosa
    datos, autores_ids = _datos_para_guardar(valores)
    libro_modelo.actualizar(libro["id"], datos, autores_ids)
    return "Libro actualizado correctamente. Su clave y sus ejemplares se conservan."


def dar_baja(libro):
    """HU-01-10: Baja lógica. Regresa (se_dio_de_baja, categoría, mensaje)."""
    # Si ya estaba dado de baja no hay nada que hacer
    if not libro["activo"]:
        return False, "info", "El libro ya estaba dado de baja."

    # HU-01-10 · Libro con operaciones vigentes: no se permite la baja
    vigentes = ejemplar_modelo.operaciones_vigentes(libro["id"])
    if vigentes:
        detalle = ", ".join(f"{op['codigo']} ({op['estado'].lower()})" for op in vigentes)
        return False, "error", (f"No se puede dar de baja: existen operaciones vigentes en {detalle}. "
                                "El libro y sus ejemplares no cambiaron.")

    # HU-01-10 · Baja lógica de libro: se marca inactivo y se conserva su información
    libro_modelo.dar_baja(libro["id"])
    return True, "success", (f"\"{libro['titulo']}\" fue dado de baja. Ya no aparece en el catálogo de usuarios "
                             "y su información se conserva para consulta administrativa.")


# Ejemplares (HU-01-14 y HU-01-15)

def opciones_ejemplar():
    """Listas para los formularios de ejemplar."""
    return {"estados": config.ESTADOS_EJEMPLAR, "estancias": ubicacion_modelo.listar_estancias()}


def obtener_ejemplar(ejemplar_id):
    """Un ejemplar o None."""
    return ejemplar_modelo.obtener(ejemplar_id)


def _validar_ejemplar(form):
    """Valida ubicación y estado del ejemplar. Regresa (valores, lista de errores)."""
    # Leemos los campos del formulario
    valores = {campo: (form.get(campo) or "").strip() for campo in CAMPOS_EJEMPLAR}
    errores = []

    # HU-01-14: la ubicación va completa (estancia, estante y posición) o vacía si está pendiente
    ubicacion = [valores["estancia"], valores["estante"], valores["posicion"]]
    if any(ubicacion) and not all(ubicacion):
        errores.append("Completa estancia, estante y posición, o deja los tres vacíos si la ubicación está pendiente.")
    elif valores["estancia"]:
        estancia = ubicacion_modelo.obtener_estancia(valores["estancia"]) if valores["estancia"].isdigit() else None
        if estancia is None:
            errores.append("Selecciona una estancia válida.")

    # HU-01-15: el estado debe ser uno de los definidos en config
    if valores["estado"] not in config.ESTADOS_EJEMPLAR:
        errores.append("Selecciona un estado válido para el ejemplar.")
    return valores, errores


def _estante_de(valores):
    """Id del estante capturado (se registra si es nuevo) o None si la ubicación está pendiente."""
    if not valores["estancia"]:
        return None
    return ubicacion_modelo.obtener_o_crear_estante(int(valores["estancia"]), valores["estante"].upper())


def agregar_ejemplar(libro_id, form):
    """HU-01-14 y HU-01-15: Registra un ejemplar del libro. Regresa (categoría, mensaje)."""
    # Validamos; si hay errores no se agrega nada
    valores, errores = _validar_ejemplar(form)
    if errores:
        return "error", " ".join(errores) + " No se agregó el ejemplar."

    # Guardamos el ejemplar con su ubicación y estado
    codigo = ejemplar_modelo.agregar(libro_id, _estante_de(valores), valores["posicion"] or None, valores["estado"])
    return "success", f"Ejemplar {codigo} agregado como {valores['estado']}."


def actualizar_ejemplar(ejemplar, form):
    """HU-01-15 · Disponibilidad actualizada: cambia ubicación y estado. Regresa (categoría, mensaje)."""
    # Validamos; si hay errores el ejemplar conserva sus datos
    valores, errores = _validar_ejemplar(form)
    if errores:
        return "error", " ".join(errores) + " El ejemplar conserva sus datos."

    # Guardamos la nueva ubicación y estado
    ejemplar_modelo.actualizar(ejemplar["id"], _estante_de(valores), valores["posicion"] or None, valores["estado"])
    return "success", f"Ejemplar {ejemplar['codigo']} actualizado: {valores['estado']}."
