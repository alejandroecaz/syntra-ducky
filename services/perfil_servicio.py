"""
============================================================
Archivo:      services/perfil_servicio.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Servicio de perfiles y permisos (HU-01-07).

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

from models import perfil as perfil_modelo
from models import permiso as permiso_modelo
from services.errores import ErrorValidacion


def listar():
    """
    Descripcion:
        Lista los perfiles con sus totales de permisos y cuentas.

    Parametros:
        Ninguno.

    Salida:
        list[sqlite3.Row]: perfiles.
    """
    return perfil_modelo.listar()


def listar_permisos_por_perfil():
    """
    Descripcion:
        Obtiene los codigos de permiso de cada perfil.

    Parametros:
        Ninguno.

    Salida:
        dict[int, list[str]]: codigos por id de perfil.
    """
    return perfil_modelo.listar_permisos_por_perfil()


def obtener_descripciones():
    """
    Descripcion:
        Obtiene la descripcion de cada permiso, leida de la tabla permisos.

    Parametros:
        Ninguno.

    Salida:
        dict[str, str]: descripcion por codigo.
    """
    return permiso_modelo.obtener_descripciones()


def agrupar_permisos():
    """
    Descripcion:
        Agrupa los permisos para el formulario de perfiles.

    Parametros:
        Ninguno.

    Salida:
        dict[str, list[tuple]]: (codigo, descripcion) de los permisos de cada
        grupo.
    """
    grupos = {}
    for permiso in permiso_modelo.listar():
        grupos.setdefault(permiso["grupo"], []).append(
            (permiso["codigo"], permiso["descripcion"])
        )
    return grupos


def crear(formulario):
    """
    Descripcion:
        HU-01-07: Crea un perfil con al menos un permiso. Solo se aceptan
        permisos que existan en la tabla.

    Parametros:
        formulario (werkzeug.datastructures.MultiDict): datos capturados:
            nombre, descripcion y permisos.

    Salida:
        tuple[int, str]: id del perfil y mensaje de exito.

    Excepciones:
        ErrorValidacion si falta el nombre, no se eligio ningun permiso o el
        nombre ya existe.
    """
    # Leemos lo capturado; solo se aceptan permisos que existan en la tabla.
    nombre = (formulario.get("nombre") or "").strip()
    descripcion = (formulario.get("descripcion") or "").strip()
    validos = {permiso["codigo"] for permiso in permiso_modelo.listar()}
    seleccionados = [
        codigo
        for codigo in formulario.getlist("permisos")
        if codigo in validos
    ]
    valores = {
        "nombre": nombre,
        "descripcion": descripcion,
        "permisos": seleccionados,
    }

    # HU-01-07 · Perfil incompleto: nombre y al menos un permiso.
    errores = {}
    if not nombre:
        errores["nombre"] = "Captura el nombre del perfil."
    if not seleccionados:
        errores["permisos"] = "Selecciona al menos un permiso."

    # HU-01-07 · Nombre duplicado.
    duplicado = bool(nombre) and perfil_modelo.verificar_nombre_existente(
        nombre
    )
    if duplicado:
        errores["nombre"] = f'Ya existe un perfil llamado "{nombre}".'

    # Si algo fallo no se registra nada.
    if errores:
        if duplicado:
            mensaje = (
                "El perfil de usuario ya existe. No se creó un "
                "duplicado y el perfil registrado no cambió."
            )
        else:
            mensaje = (
                "Completa el nombre y selecciona al menos un permiso. "
                "El perfil no se registró."
            )
        raise ErrorValidacion(mensaje, errores, valores)

    # HU-01-07 · Perfil creado.
    perfil_id = perfil_modelo.crear(nombre, descripcion, seleccionados)
    mensaje = (
        f'Perfil "{nombre}" creado con {len(seleccionados)} permisos. '
        "Ya está disponible para asignarse."
    )
    return perfil_id, mensaje
