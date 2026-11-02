"""
============================================================
Archivo:      config.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Configuracion y constantes del sistema.

    Aqui viven los valores que el codigo usa como reglas (permisos,
    estados, limites y mensajes compartidos entre la web y el portal
    movil) para no dejar valores magicos regados.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

import os
import secrets

from dotenv import load_dotenv

# ============================================================
# SERVIDOR Y BASE DE DATOS
# Rutas, clave secreta, direccion y puerto del servidor.
# ============================================================
# Carpeta del proyecto y variables de entorno de .env.
DIRECTORIO_BASE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(DIRECTORIO_BASE, ".env"))

# Se lee de .env; si no existe se usa una clave aleatoria.
CLAVE_SECRETA = os.environ.get("CLAVE_SECRETA") or secrets.token_hex(32)

# Ruta del archivo de base de datos SQLite.
RUTA_BASE_DATOS = os.path.join(DIRECTORIO_BASE, "syntra.db")

# 0.0.0.0 para poder abrir el sistema desde el celular en la misma red.
# Se usa el 5050 porque en macOS el 5000 lo ocupa AirPlay.
DIRECCION_SERVIDOR = "0.0.0.0"
PUERTO = 5050

# Nombres que se muestran en pantallas y documentos.
NOMBRE_SISTEMA = "Syntra"
NOMBRE_CLIENTE = "Biblioteca Universidad Ducky"

# ============================================================
# PERMISOS
# Catalogo de permisos; el acceso siempre se revisa por permiso.
# ============================================================
# Permisos que el codigo revisa por su clave (nunca por el nombre del perfil).
PERMISO_SISTEMA = "sistema.acceder"
PERMISO_MOVIL = "movil.acceder"

# Catalogo de permisos: (codigo, descripcion, grupo). init_db.py los guarda en
# la tabla permisos.
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
    (
        "catalogo.consultar",
        "Consultar catálogo, ubicación y disponibilidad",
        "Catálogo",
    ),
    ("libros.alta", "Dar de alta libros", "Catálogo"),
    ("libros.editar", "Actualizar libros y ejemplares", "Catálogo"),
    ("libros.baja", "Dar de baja libros", "Catálogo"),
    ("reportes.pdf", "Generar listado de libros en PDF", "Reportes"),
    ("reportes.imprimir", "Imprimir listado de libros", "Reportes"),
    ("compras.orden", "Generar órdenes de compra", "Compras"),
]

# Quien tenga alguno de estos permisos es personal de biblioteca (puede ver
# libros dados de baja).
PERMISOS_PERSONAL = ("libros.alta", "libros.editar", "libros.baja")

# ============================================================
# REGLAS DE NEGOCIO
# Estados, limites y formatos que usan los servicios.
# ============================================================
# Cuentas de usuario (HU-01-02 a HU-01-06).
ESTADO_HABILITADA = "Habilitada"
ESTADO_DESHABILITADA = "Deshabilitada"
ESTADOS_CUENTA = [ESTADO_HABILITADA, ESTADO_DESHABILITADA]
LONGITUD_MINIMA_CONTRASENA = 6
PATRON_EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
PATRON_TELEFONO = r"^[0-9 +()-]{7,20}$"

# Libros y ejemplares (HU-01-09 a HU-01-11, HU-01-14 y HU-01-15).
ESTADO_DISPONIBLE = "Disponible"
ESTADOS_EJEMPLAR = [
    ESTADO_DISPONIBLE,
    "Prestado",
    "Reservado",
    "Perdido",
    "Dañado",
    "Fuera de servicio",
]
# Si hay ejemplares en estos estados no se puede dar de baja el libro.
ESTADOS_OPERACION_VIGENTE = ["Prestado", "Reservado"]
TIPOS_ACCESO = ["Circulante", "Reservado", "Consulta externa"]
ANIO_MINIMO_PUBLICACION = 1400
# En el formulario se capturan varios autores separados por este caracter.
SEPARADOR_AUTORES = ";"
PREFIJO_EJEMPLAR = "EJ-"

# Busqueda de libros (HU-01-13).
CAMPOS_BUSQUEDA = [
    ("titulo", "Título"),
    ("autor", "Autor"),
    ("tema", "Tema"),
    ("editorial", "Editorial"),
    ("clave", "Clave"),
]
CAMPO_BUSQUEDA_PREDETERMINADO = "titulo"
# Que libros ve el personal en el catalogo: activos, dados de baja o todos.
VISTAS_CATALOGO = ("activos", "baja", "todos")

# Ordenes de compra (HU-01-18).
CANTIDAD_MAXIMA_POR_LIBRO = 500
ESTADO_ORDEN_REGISTRADA = "Registrada"
ESTADOS_ORDEN = [ESTADO_ORDEN_REGISTRADA, "Cancelada"]

# Portal movil: cuantos libros mostrar en "Disponibles ahora".
MOVIL_LIBROS_DESTACADOS = 4

# ============================================================
# MENSAJES Y DISPOSITIVOS
# Textos compartidos por la web y el portal movil, e impresoras.
# ============================================================
# Mensajes de los criterios de aceptacion que la web y el portal movil muestran
# igual.
MENSAJES = {
    "login_campos_vacios": "Completa los campos obligatorios para iniciar "
    "sesión.",
    "login_credenciales": "Cuenta o contraseña incorrecta",
    "login_deshabilitada": "La cuenta no está habilitada. Comunícate con el "
    "administrador de la biblioteca.",
    "login_sin_acceso": "Tu perfil de usuario no tiene autorización para "
    "acceder al sistema.",
    "login_solo_alumnos": "Acceso no autorizado: el portal móvil es solo "
    "para alumnos",
    "busqueda_vacia": "Captura un criterio de búsqueda",
    "busqueda_sin_resultados": "No se encontraron libros",
    "ubicacion_no_registrada": "Ubicación no registrada",
    "libro_sin_ejemplares": "Este libro no tiene ejemplares registrados",
}

# La de sala de lectura esta apagada a proposito para probar el error de
# HU-01-17.
IMPRESORAS = [
    {
        "id": "recepcion",
        "nombre": "HP LaserJet Pro · Recepción",
        "disponible": True,
    },
    {
        "id": "catalogacion",
        "nombre": "Epson EcoTank · Oficina de catalogación",
        "disponible": True,
    },
    {
        "id": "sala",
        "nombre": "Brother HL · Sala de lectura",
        "disponible": False,
    },
]
