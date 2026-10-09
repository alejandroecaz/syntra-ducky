import os
import secrets

from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Se lee de .env; si no existe se usa una clave aleatoria
SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

DATABASE_PATH = os.path.join(BASE_DIR, "syntra.db")

NOMBRE_SISTEMA = "Syntra"
NOMBRE_CLIENTE = "Biblioteca Universidad Ducky"

# (codigo, descripcion, grupo)
PERMISOS = [
    ("sistema.acceder", "Acceder al sistema", "General"),
    ("cuenta.contrasena", "Cambiar su propia contraseña", "General"),
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

PERMISOS_DESCRIPCION = {codigo: desc for codigo, desc, _ in PERMISOS}

ESTADOS_EJEMPLAR = [
    "Disponible",
    "Prestado",
    "Reservado",
    "Perdido",
    "Dañado",
    "Fuera de servicio",
]

# Si hay ejemplares en estos estados no se puede dar de baja el libro
ESTADOS_OPERACION_VIGENTE = ["Prestado", "Reservado"]

ESTANCIAS = [
    "Sala General",
    "Sala de Lectura",
    "Hemeroteca",
    "Acervo Reservado",
]

CAMPOS_BUSQUEDA = [
    ("titulo", "Título"),
    ("autor", "Autor"),
    ("tema", "Tema"),
    ("editorial", "Editorial"),
    ("clave", "Clave"),
]

# La de sala de lectura esta apagada a proposito para probar el error
IMPRESORAS = [
    {"id": "recepcion", "nombre": "HP LaserJet Pro · Recepción", "disponible": True},
    {"id": "catalogacion", "nombre": "Epson EcoTank · Oficina de catalogación", "disponible": True},
    {"id": "sala", "nombre": "Brother HL · Sala de lectura", "disponible": False},
]
