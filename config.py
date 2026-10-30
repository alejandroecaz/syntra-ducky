# ============================================================
# Archivo: config.py
# Proyecto: Sistema Ducky de Gestión Bibliotecaria
# Syntra Technologies - Equipo 1 - Sprint 1
# Materia: Ingeniería de Software
# Autores:
#   - Melissa Silva Vázquez                #624352
#   - Tomás Zapata Pérez                   #629048
#   - Alejandro Evaristo Cazares Escobedo  #626337
# Descripción: Configuración y constantes del sistema.
# ============================================================
"""Configuración y constantes del sistema.

Aquí viven los valores que el código usa como reglas (permisos, estados, límites y mensajes
compartidos entre la web y el portal móvil) para no dejar valores mágicos regados.
"""
import os
import secrets

from dotenv import load_dotenv

# Carpeta del proyecto y variables de entorno de .env
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Se lee de .env; si no existe se usa una clave aleatoria
SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

# Ruta del archivo de base de datos SQLite
DATABASE_PATH = os.path.join(BASE_DIR, "syntra.db")

# 0.0.0.0 para poder abrir el sistema desde el celular en la misma red.
# Se usa el 5050 porque en macOS el 5000 lo ocupa AirPlay.
HOST = "0.0.0.0"
PUERTO = 5050

# Nombres que se muestran en pantallas y documentos
NOMBRE_SISTEMA = "Syntra"
NOMBRE_CLIENTE = "Biblioteca Universidad Ducky"

# Permisos que el código revisa por su clave (nunca por el nombre del perfil)
PERMISO_SISTEMA = "sistema.acceder"
PERMISO_MOVIL = "movil.acceder"

# Catálogo de permisos: (codigo, descripcion, grupo). init_db.py los guarda en la tabla permisos.
PERMISOS = [
    ("sistema.acceder", "Acceder al sistema", "General"),
    ("cuenta.contrasena", "Cambiar su propia contraseña", "General"),
    ("movil.acceder", "Acceder al portal móvil", "General"),
    ("usuarios.consultar", "Consultar usuarios", "Usuarios"),
    ("usuarios.registrar", "Registrar usuarios", "Usuarios"),
    ("usuarios.editar", "Actualizar datos de usuarios", "Usuarios"),
    ("usuarios.baja", "Habilitar o deshabilitar cuentas", "Usuarios"),
    ("perfiles.crear", "Crear perfiles de usuario", "Perfiles"),
    ("perfiles.asignar", "Asignar perfiles a las cuentas", "Perfiles"),
    ("catalogo.consultar", "Consultar catálogo, ubicación y disponibilidad", "Catálogo"),
    ("libros.alta", "Dar de alta libros", "Catálogo"),
    ("libros.editar", "Actualizar libros y ejemplares", "Catálogo"),
    ("libros.baja", "Dar de baja libros", "Catálogo"),
    ("reportes.pdf", "Generar listado de libros en PDF", "Reportes"),
    ("reportes.imprimir", "Imprimir listado de libros", "Reportes"),
    ("compras.orden", "Generar órdenes de compra", "Compras"),
]

# Quien tenga alguno de estos permisos es personal de biblioteca (puede ver libros dados de baja)
PERMISOS_PERSONAL = ("libros.alta", "libros.editar", "libros.baja")

# Cuentas de usuario (HU-01-02 a HU-01-06)
ESTADO_HABILITADA = "Habilitada"
ESTADO_DESHABILITADA = "Deshabilitada"
ESTADOS_CUENTA = [ESTADO_HABILITADA, ESTADO_DESHABILITADA]
LONGITUD_MINIMA_CONTRASENA = 6
PATRON_EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
PATRON_TELEFONO = r"^[0-9 +()-]{7,20}$"

# Libros y ejemplares (HU-01-09 a HU-01-11, HU-01-14 y HU-01-15)
ESTADO_DISPONIBLE = "Disponible"
ESTADOS_EJEMPLAR = [
    ESTADO_DISPONIBLE,
    "Prestado",
    "Reservado",
    "Perdido",
    "Dañado",
    "Fuera de servicio",
]
# Si hay ejemplares en estos estados no se puede dar de baja el libro
ESTADOS_OPERACION_VIGENTE = ["Prestado", "Reservado"]
TIPOS_ACCESO = ["Circulante", "Reservado", "Consulta externa"]
ANIO_MINIMO_PUBLICACION = 1400
# En el formulario se capturan varios autores separados por este caracter
SEPARADOR_AUTORES = ";"
PREFIJO_EJEMPLAR = "EJ-"

# Búsqueda de libros (HU-01-13)
CAMPOS_BUSQUEDA = [
    ("titulo", "Título"),
    ("autor", "Autor"),
    ("tema", "Tema"),
    ("editorial", "Editorial"),
    ("clave", "Clave"),
]
CAMPO_BUSQUEDA_PREDETERMINADO = "titulo"
# Qué libros ve el personal en el catálogo: activos, dados de baja o todos
VISTAS_CATALOGO = ("activos", "baja", "todos")

# Órdenes de compra (HU-01-18)
CANTIDAD_MAXIMA_POR_LIBRO = 500
ESTADO_ORDEN_REGISTRADA = "Registrada"
ESTADOS_ORDEN = [ESTADO_ORDEN_REGISTRADA, "Cancelada"]

# Portal móvil: cuántos libros mostrar en "Disponibles ahora"
MOVIL_LIBROS_DESTACADOS = 4

# Mensajes de los criterios de aceptación que la web y el portal móvil muestran igual
MENSAJES = {
    "login_campos_vacios": "Completa los campos obligatorios para iniciar sesión.",
    "login_credenciales": "Cuenta o contraseña incorrecta",
    "login_deshabilitada": "La cuenta no está habilitada. Comunícate con el administrador de la biblioteca.",
    "login_sin_acceso": "Tu perfil de usuario no tiene autorización para acceder al sistema.",
    "login_solo_alumnos": "Acceso no autorizado: el portal móvil es solo para alumnos",
    "busqueda_vacia": "Captura un criterio de búsqueda",
    "busqueda_sin_resultados": "No se encontraron libros",
    "ubicacion_no_registrada": "Ubicación no registrada",
    "libro_sin_ejemplares": "Este libro no tiene ejemplares registrados",
}

# La de sala de lectura está apagada a propósito para probar el error de HU-01-17
IMPRESORAS = [
    {"id": "recepcion", "nombre": "HP LaserJet Pro · Recepción", "disponible": True},
    {"id": "catalogacion", "nombre": "Epson EcoTank · Oficina de catalogación", "disponible": True},
    {"id": "sala", "nombre": "Brother HL · Sala de lectura", "disponible": False},
]
