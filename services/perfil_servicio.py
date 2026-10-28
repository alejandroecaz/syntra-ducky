"""Servicio de perfiles y permisos (HU-01-07)."""
from models import perfil as perfil_modelo
from models import permiso as permiso_modelo
from services.errores import ErrorValidacion


def listar():
    """Perfiles con sus totales."""
    return perfil_modelo.listar()


def permisos_por_perfil():
    """Diccionario perfil_id -> códigos de permiso."""
    return perfil_modelo.permisos_por_perfil()


def descripciones():
    """Diccionario código -> descripción del permiso, leído de la tabla permisos."""
    return permiso_modelo.descripciones()


def permisos_agrupados():
    """Permisos agrupados para el formulario: {grupo: [(codigo, descripcion)]}."""
    grupos = {}
    for permiso in permiso_modelo.listar():
        grupos.setdefault(permiso["grupo"], []).append((permiso["codigo"], permiso["descripcion"]))
    return grupos


def crear(form):
    """Crea un perfil con al menos un permiso. Regresa (id, mensaje) o lanza ErrorValidacion."""
    nombre = (form.get("nombre") or "").strip()
    descripcion = (form.get("descripcion") or "").strip()
    validos = {permiso["codigo"] for permiso in permiso_modelo.listar()}
    seleccionados = [codigo for codigo in form.getlist("permisos") if codigo in validos]
    valores = {"nombre": nombre, "descripcion": descripcion, "permisos": seleccionados}

    errores = {}
    if not nombre:
        errores["nombre"] = "Captura el nombre del perfil."
    if not seleccionados:
        errores["permisos"] = "Selecciona al menos un permiso."

    duplicado = bool(nombre) and perfil_modelo.existe_nombre(nombre)
    if duplicado:
        errores["nombre"] = f"Ya existe un perfil llamado \"{nombre}\"."

    if errores:
        if duplicado:
            mensaje = "El perfil de usuario ya existe. No se creó un duplicado y el perfil registrado no cambió."
        else:
            mensaje = "Completa el nombre y selecciona al menos un permiso. El perfil no se registró."
        raise ErrorValidacion(mensaje, errores, valores)

    perfil_id = perfil_modelo.crear(nombre, descripcion, seleccionados)
    mensaje = f"Perfil \"{nombre}\" creado con {len(seleccionados)} permisos. Ya está disponible para asignarse."
    return perfil_id, mensaje
