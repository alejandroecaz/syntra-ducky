"""Servicio del panel de inicio: funciones e indicadores según los permisos del perfil (HU-01-01)."""
import config
from models import libro as libro_modelo
from models import orden_compra as orden_modelo
from models import usuario as usuario_modelo

# (permisos, icono, titulo, descripcion, endpoint)
ACCIONES = [
    (("catalogo.consultar",), "search", "Buscar libros",
     "Consulta el catálogo por título, autor, tema, clave o editorial.", "catalogo.lista"),
    (("libros.alta",), "plus", "Registrar libro",
     "Da de alta la ficha bibliográfica de un nuevo libro.", "catalogo.nuevo"),
    (("reportes.pdf", "reportes.imprimir"), "file", "Listado de libros",
     "Genera el listado en PDF o envíalo a impresión.", "reportes.listado"),
    (("compras.orden",), "cart", "Órdenes de compra",
     "Solicita la adquisición de títulos para la biblioteca.", "compras.lista"),
    (("usuarios.consultar",), "users", "Usuarios",
     "Consulta, registra y administra las cuentas.", "usuarios.lista"),
    (("usuarios.registrar",), "user-plus", "Registrar usuario",
     "Crea la cuenta de un alumno, profesor o colaborador.", "usuarios.nuevo"),
    (("perfiles.crear", "perfiles.asignar"), "shield", "Perfiles y permisos",
     "Define perfiles y controla el acceso a las funciones.", "perfiles.lista"),
    (("cuenta.contrasena",), "key", "Cambiar contraseña",
     "Mantén seguras tus credenciales de acceso.", "cuenta.contrasena"),
]


def _tiene(permisos, *requeridos):
    return any(permiso in permisos for permiso in requeridos)


def acciones_para(permisos):
    """Solo las funciones que el perfil tiene autorizadas."""
    return [accion for accion in ACCIONES if _tiene(permisos, *accion[0])]


def indicadores_para(permisos):
    """Indicadores del panel: (icono, etiqueta, valor, endpoint)."""
    indicadores = []
    if _tiene(permisos, "catalogo.consultar"):
        totales = libro_modelo.contar()
        indicadores.append(("library", "Libros en catálogo", totales["libros_activos"], "catalogo.lista"))
        indicadores.append(("check-circle", "Ejemplares disponibles",
                            f"{totales['disponibles']} / {totales['ejemplares']}", "catalogo.lista"))
    if _tiene(permisos, "usuarios.consultar"):
        estados = usuario_modelo.contar_por_estado()
        indicadores.append(("user-check", "Cuentas habilitadas", estados.get(config.ESTADO_HABILITADA, 0),
                            "usuarios.lista"))
    if _tiene(permisos, "compras.orden"):
        indicadores.append(("clipboard", "Órdenes de compra", orden_modelo.contar(), "compras.lista"))
    return indicadores
