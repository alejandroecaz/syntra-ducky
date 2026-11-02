"""
============================================================
Archivo:      services/inicio_servicio.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Servicio del panel de inicio: funciones e indicadores segun los
    permisos del perfil (HU-01-01).

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

import config
from models import libro as libro_modelo
from models import orden_compra as orden_modelo
from models import usuario as usuario_modelo

# (permisos, icono, titulo, descripcion, endpoint).
ACCIONES = [
    (
        ("catalogo.consultar",),
        "search",
        "Buscar libros",
        "Consulta el catálogo por título, autor, tema, clave o editorial.",
        "catalogo.listar",
    ),
    (
        ("libros.alta",),
        "plus",
        "Registrar libro",
        "Da de alta la ficha bibliográfica de un nuevo libro.",
        "catalogo.registrar",
    ),
    (
        ("reportes.pdf", "reportes.imprimir"),
        "file",
        "Listado de libros",
        "Genera el listado en PDF o envíalo a impresión.",
        "reportes.mostrar_listado",
    ),
    (
        ("compras.orden",),
        "cart",
        "Órdenes de compra",
        "Solicita la adquisición de títulos para la biblioteca.",
        "compras.listar",
    ),
    (
        ("usuarios.consultar",),
        "users",
        "Usuarios",
        "Consulta, registra y administra las cuentas.",
        "usuarios.listar",
    ),
    (
        ("usuarios.registrar",),
        "user-plus",
        "Registrar usuario",
        "Crea la cuenta de un alumno, profesor o colaborador.",
        "usuarios.registrar",
    ),
    (
        ("perfiles.crear", "perfiles.asignar"),
        "shield",
        "Perfiles y permisos",
        "Define perfiles y controla el acceso a las funciones.",
        "perfiles.listar",
    ),
    (
        ("cuenta.contrasena",),
        "key",
        "Cambiar contraseña",
        "Mantén seguras tus credenciales de acceso.",
        "cuenta.cambiar_contrasena",
    ),
]


def _tener_alguno(permisos, *requeridos):
    """
    Descripcion:
        Revisa si en los permisos esta al menos uno de los requeridos.

    Parametros:
        permisos (list[str]): permisos del perfil.
        *requeridos (str): permisos que se buscan.

    Salida:
        bool: True si tiene al menos uno.
    """
    return any(permiso in permisos for permiso in requeridos)


def obtener_acciones(permisos):
    """
    Descripcion:
        HU-01-01: Filtra las funciones del panel para mostrar solo las que el
        perfil tiene autorizadas.

    Parametros:
        permisos (list[str]): permisos del perfil.

    Salida:
        list[tuple]: (permisos, icono, titulo, descripcion, endpoint) de cada
        funcion.
    """
    return [
        accion for accion in ACCIONES if _tener_alguno(permisos, *accion[0])
    ]


def obtener_indicadores(permisos):
    """
    Descripcion:
        Arma los indicadores del panel de inicio segun los permisos del perfil.

    Parametros:
        permisos (list[str]): permisos del perfil.

    Salida:
        list[tuple]: (icono, etiqueta, valor, endpoint) de cada indicador.
    """
    indicadores = []

    # Catalogo: libros activos y ejemplares disponibles.
    if _tener_alguno(permisos, "catalogo.consultar"):
        totales = libro_modelo.contar()
        indicadores.append(
            (
                "library",
                "Libros en catálogo",
                totales["libros_activos"],
                "catalogo.listar",
            )
        )
        indicadores.append(
            (
                "check-circle",
                "Ejemplares disponibles",
                f"{totales['disponibles']} / {totales['ejemplares']}",
                "catalogo.listar",
            )
        )

    # Usuarios: cuentas habilitadas.
    if _tener_alguno(permisos, "usuarios.consultar"):
        estados = usuario_modelo.contar_por_estado()
        indicadores.append(
            (
                "user-check",
                "Cuentas habilitadas",
                estados.get(config.ESTADO_HABILITADA, 0),
                "usuarios.listar",
            )
        )

    # Compras: ordenes registradas.
    if _tener_alguno(permisos, "compras.orden"):
        indicadores.append(
            (
                "clipboard",
                "Órdenes de compra",
                orden_modelo.contar(),
                "compras.listar",
            )
        )
    return indicadores
