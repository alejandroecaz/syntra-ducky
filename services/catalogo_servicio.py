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

CAMPOS_VALIDOS = {campo for campo, _ in config.CAMPOS_BUSQUEDA}
CAMPOS_LIBRO = ("clave", "titulo", "autores", "tema", "editorial", "anio", "isbn", "edicion", "tipo_acceso",
                "sinopsis")
OBLIGATORIOS_LIBRO = {
    "clave": "la clave",
    "titulo": "el título",
    "autores": "al menos un autor",
    "tema": "el tema",
    "editorial": "la editorial",
}
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
    """Búsqueda por filtros (HU-01-13).

    La clave se busca exacta; título, autor, tema y editorial por coincidencia, sin importar
    acentos ni mayúsculas. Si el texto está vacío o solo tiene espacios no se busca y se
    regresa el mensaje para pedir un criterio.
    Regresa {"campo", "texto", "libros", "error"}.
    """
    campo = campo_valido(campo)
    texto = (texto or "").strip()
    if not texto:
        return {"campo": campo, "texto": texto, "libros": [], "error": config.MENSAJES["busqueda_vacia"]}
    libros = libro_modelo.listar(campo=campo, texto=texto, estado=vista)
    return {"campo": campo, "texto": texto, "libros": libros, "error": None}


def listar_catalogo(vista="activos"):
    """Todos los libros de la vista (HU-01-12)."""
    return libro_modelo.listar(estado=vista)


def hay_catalogo(vista):
    """False solo cuando no existe ningún libro activo (para mostrar "No hay libros registrados")."""
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
    """Datos del libro con sus ejemplares y operaciones vigentes (HU-01-12, 14 y 15), o None."""
    libro = obtener_libro(libro_id, permitir_baja)
    if libro is None:
        return None
    return {
        "libro": libro,
        "ejemplares": ejemplar_modelo.de_libro(libro_id),
        "operaciones": ejemplar_modelo.operaciones_vigentes(libro_id),
    }


def estado_libro(libro):
    """Texto del estado del libro para listados y PDF."""
    if not libro["activo"]:
        return "Dado de baja"
    if libro["total_ejemplares"] == 0:
        return "Sin ejemplares"
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
    """Datos actuales del libro para llenar el formulario de edición."""
    valores = {campo: libro[campo] if libro[campo] is not None else "" for campo in CAMPOS_LIBRO
               if campo != "autores"}
    valores["autores"] = f"{config.SEPARADOR_AUTORES} ".join(libro_modelo.nombres_autores(libro["id"]))
    return valores


def separar_autores(texto):
    """'A; B; A' -> ['A', 'B'] sin vacíos ni repetidos, en el orden capturado."""
    autores = []
    for nombre in (texto or "").split(config.SEPARADOR_AUTORES):
        nombre = " ".join(nombre.split())
        if nombre and nombre.lower() not in (a.lower() for a in autores):
            autores.append(nombre)
    return autores


def _isbn_valido(isbn):
    limpio = isbn.replace("-", "").replace(" ", "").upper()
    return bool(re.fullmatch(r"\d{9}[\dX]", limpio) or re.fullmatch(r"\d{13}", limpio))


def validar_libro(form, exigir_clave, libro_id=None):
    """Regresa (valores, errores, faltan_obligatorios) sin guardar nada."""
    valores = {campo: (form.get(campo) or "").strip() for campo in CAMPOS_LIBRO}
    errores = {}

    obligatorios = OBLIGATORIOS_LIBRO if exigir_clave else {k: v for k, v in OBLIGATORIOS_LIBRO.items()
                                                            if k != "clave"}
    for campo, etiqueta in obligatorios.items():
        if not valores[campo]:
            errores[campo] = f"Captura {etiqueta}."
    if valores["autores"] and not separar_autores(valores["autores"]):
        errores["autores"] = "Captura al menos un autor."
    faltan = bool(errores)

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
    # Convierte los textos del formulario en ids de editorial, tema y autores
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
    autores_ids = []
    for nombre in separar_autores(valores["autores"]):
        autor_id = autor_modelo.obtener_o_crear(nombre)
        if autor_id not in autores_ids:
            autores_ids.append(autor_id)
    return datos, autores_ids


def registrar_libro(form):
    """Alta de libro (HU-01-09). No crea ejemplares. Regresa (id, mensaje) o lanza ErrorValidacion."""
    valores, errores, faltan = validar_libro(form, exigir_clave=True)
    clave_duplicada = bool(valores["clave"]) and libro_modelo.existe_clave(valores["clave"])
    if clave_duplicada:
        errores["clave"] = "La clave del libro ya existe"

    if errores:
        if clave_duplicada:
            mensaje = "La clave del libro ya existe. No se duplicó ni se sobrescribió el libro registrado."
        elif faltan:
            mensaje = "Faltan datos bibliográficos obligatorios. El libro no se registró."
        else:
            mensaje = "Revisa los campos marcados. El libro no se registró."
        raise ErrorValidacion(mensaje, errores, valores)

    datos, autores_ids = _datos_para_guardar(valores)
    libro_id = libro_modelo.crear(datos, autores_ids)
    mensaje = (f"Libro registrado: {datos['titulo']} ({datos['clave']}). "
               "Aún no tiene ejemplares; agrégalos desde su ficha.")
    return libro_id, mensaje


def actualizar_libro(libro, form):
    """Actualización de libro (HU-01-11). Conserva clave y ejemplares. Regresa el mensaje."""
    valores, errores, faltan = validar_libro(form, exigir_clave=False, libro_id=libro["id"])
    valores["clave"] = libro["clave"]
    if errores:
        mensaje = ("Faltan campos obligatorios. Se mantienen los datos guardados." if faltan
                   else "Revisa los campos marcados. Se mantienen los datos guardados.")
        raise ErrorValidacion(mensaje, errores, valores)

    datos, autores_ids = _datos_para_guardar(valores)
    libro_modelo.actualizar(libro["id"], datos, autores_ids)
    return "Libro actualizado correctamente. Su clave y sus ejemplares se conservan."


def dar_baja(libro):
    """Baja lógica (HU-01-10). Regresa (se_dio_de_baja, categoría, mensaje)."""
    if not libro["activo"]:
        return False, "info", "El libro ya estaba dado de baja."

    vigentes = ejemplar_modelo.operaciones_vigentes(libro["id"])
    if vigentes:
        detalle = ", ".join(f"{op['codigo']} ({op['estado'].lower()})" for op in vigentes)
        return False, "error", (f"No se puede dar de baja: existen operaciones vigentes en {detalle}. "
                                "El libro y sus ejemplares no cambiaron.")

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
    # La ubicación va completa (estancia, estante y posición) o vacía si está pendiente
    valores = {campo: (form.get(campo) or "").strip() for campo in CAMPOS_EJEMPLAR}
    errores = []
    ubicacion = [valores["estancia"], valores["estante"], valores["posicion"]]
    if any(ubicacion) and not all(ubicacion):
        errores.append("Completa estancia, estante y posición, o deja los tres vacíos si la ubicación está pendiente.")
    elif valores["estancia"]:
        estancia = ubicacion_modelo.obtener_estancia(valores["estancia"]) if valores["estancia"].isdigit() else None
        if estancia is None:
            errores.append("Selecciona una estancia válida.")
    if valores["estado"] not in config.ESTADOS_EJEMPLAR:
        errores.append("Selecciona un estado válido para el ejemplar.")
    return valores, errores


def _estante_de(valores):
    if not valores["estancia"]:
        return None
    return ubicacion_modelo.obtener_o_crear_estante(int(valores["estancia"]), valores["estante"].upper())


def agregar_ejemplar(libro_id, form):
    """Registra un ejemplar del libro. Regresa (categoría, mensaje)."""
    valores, errores = _validar_ejemplar(form)
    if errores:
        return "error", " ".join(errores) + " No se agregó el ejemplar."
    codigo = ejemplar_modelo.agregar(libro_id, _estante_de(valores), valores["posicion"] or None, valores["estado"])
    return "success", f"Ejemplar {codigo} agregado como {valores['estado']}."


def actualizar_ejemplar(ejemplar, form):
    """Cambia ubicación y estado de un ejemplar. Regresa (categoría, mensaje)."""
    valores, errores = _validar_ejemplar(form)
    if errores:
        return "error", " ".join(errores) + " El ejemplar conserva sus datos."
    ejemplar_modelo.actualizar(ejemplar["id"], _estante_de(valores), valores["posicion"] or None, valores["estado"])
    return "success", f"Ejemplar {ejemplar['codigo']} actualizado: {valores['estado']}."
