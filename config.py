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
# ENVIO DE BOLETAS (HU-02-04)
# Se leen de .env. Sin cuenta de correo, la boleta se guarda como archivo
# .eml en CARPETA_BOLETAS (modo demostracion). Sin Twilio, WhatsApp se
# abre con un enlace wa.me y el mensaje ya escrito.
# ============================================================
# Correo por SMTP (por ejemplo Gmail con una contrasena de aplicacion).
CORREO_SERVIDOR = os.environ.get("CORREO_SERVIDOR", "smtp.gmail.com")
CORREO_PUERTO = int(os.environ.get("CORREO_PUERTO", "587"))
CORREO_USUARIO = os.environ.get("CORREO_USUARIO", "")
CORREO_CONTRASENA = os.environ.get("CORREO_CONTRASENA", "")
CORREO_REMITENTE = os.environ.get("CORREO_REMITENTE") or CORREO_USUARIO

# WhatsApp por la API de Twilio (opcional).
TWILIO_SID = os.environ.get("TWILIO_SID", "")
TWILIO_TOKEN = os.environ.get("TWILIO_TOKEN", "")
TWILIO_WHATSAPP_ORIGEN = os.environ.get(
    "TWILIO_WHATSAPP_ORIGEN", "+14155238886"
)

# Carpeta donde se guardan los correos en modo demostracion.
CARPETA_BOLETAS = os.path.join(DIRECTORIO_BASE, "boletas_enviadas")

# Correo de Tesoreria al que se mandan las multas para su cobro (HU-02-08).
TESORERIA_CORREO = os.environ.get("TESORERIA_CORREO", "tesoreria@ducky.edu.mx")

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
    (
        "prestamos.registrar",
        "Registrar préstamos y emitir boletas",
        "Préstamos",
    ),
    ("prestamos.renovar", "Renovar préstamos", "Préstamos"),
    ("espera.gestionar", "Gestionar la lista de espera", "Préstamos"),
    ("devoluciones.registrar", "Registrar devoluciones", "Préstamos"),
    (
        "multas.gestionar",
        "Enviar multas a Tesorería y registrar sus pagos",
        "Multas",
    ),
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

# Prestamos (HU-02-01 a HU-02-05).
ESTADO_PRESTAMO_ACTIVO = "Activo"
ESTADO_PRESTAMO_DEVUELTO = "Devuelto"
ESTADO_PRESTAMO_PERDIDO = "Perdido"
ESTADOS_PRESTAMO = [
    ESTADO_PRESTAMO_ACTIVO,
    ESTADO_PRESTAMO_DEVUELTO,
    "Vencido",
    ESTADO_PRESTAMO_PERDIDO,
]
# Libros con este tipo de acceso solo se consultan dentro de la biblioteca.
TIPOS_ACCESO_SIN_PRESTAMO = ["Reservado"]
PREFIJO_PRESTAMO = "PR"
# Que prestamos se ven en la lista: activos, vencidos o todos.
VISTAS_PRESTAMOS = ("activos", "vencidos", "todos")

# Lista de espera (HU-02-06). Las solicitudes "vigentes" siguen esperando
# turno; al prestarle el libro al usuario su solicitud queda "Atendido".
ESTADO_ESPERA = "En espera"
ESTADO_ESPERA_NOTIFICADO = "Notificado"
ESTADO_ESPERA_ATENDIDO = "Atendido"
ESTADO_ESPERA_CANCELADO = "Cancelado"
ESTADOS_ESPERA = [
    ESTADO_ESPERA,
    ESTADO_ESPERA_NOTIFICADO,
    ESTADO_ESPERA_ATENDIDO,
    ESTADO_ESPERA_CANCELADO,
]
ESTADOS_ESPERA_VIGENTE = [ESTADO_ESPERA, ESTADO_ESPERA_NOTIFICADO]

# Devoluciones (HU-02-07). El bibliotecario elige el resultado: el libro
# regresa bien, regresa danado o el usuario reporta que lo perdio. Cada
# resultado deja la devolucion con su condicion, el prestamo con su estado y
# el ejemplar con su nuevo estado.
RESULTADO_BUENO = "bueno"
RESULTADO_DANADO = "danado"
RESULTADO_PERDIDO = "perdido"
RESULTADOS_DEVOLUCION = [
    (RESULTADO_BUENO, "Lo devuelve en buen estado"),
    (RESULTADO_DANADO, "Lo devuelve dañado"),
    (RESULTADO_PERDIDO, "Reporta que lo perdió"),
]
CONDICION_BUENO = "Bueno"
CONDICION_DANADO = "Dañado"
CONDICIONES_DEVOLUCION = [CONDICION_BUENO, CONDICION_DANADO]
ESTADO_EJEMPLAR_DANADO = "Dañado"
ESTADO_EJEMPLAR_PERDIDO = "Perdido"
LONGITUD_MAXIMA_OBSERVACIONES = 255

# Multas (HU-02-08): por retraso (dias x multa diaria del perfil), por dano
# (monto que captura el bibliotecario) y por perdida (ultimo precio del
# libro; si esta en dolares se aplica el tipo de cambio vigente).
MOTIVO_RETRASO = "Retraso"
MOTIVO_DANO = "Daño"
MOTIVO_PERDIDA = "Pérdida"
MOTIVOS_MULTA = [MOTIVO_RETRASO, MOTIVO_DANO, MOTIVO_PERDIDA]
ESTADO_MULTA_PENDIENTE = "Pendiente"
ESTADO_MULTA_PAGADA = "Pagada"
ESTADOS_MULTA = [ESTADO_MULTA_PENDIENTE, ESTADO_MULTA_PAGADA, "Cancelada"]
# Que multas se ven en la lista: pendientes, pagadas o todas.
VISTAS_MULTAS = ("pendientes", "pagadas", "todas")
MONTO_MAXIMO_MULTA = 100000
METODO_EFECTIVO = "Efectivo"
METODOS_PAGO = [METODO_EFECTIVO, "Tarjeta", "Transferencia"]
MONEDA_LOCAL = "MXN"
MONEDAS = [MONEDA_LOCAL, "USD"]

# Avisos a los usuarios (tabla avisos).
TIPO_AVISO_ESPERA = "Lista de espera"
TIPOS_AVISO = ["Vencimiento", "Adeudo", TIPO_AVISO_ESPERA]
MEDIOS_AVISO = ["Email", "WhatsApp", "Sistema"]

# Boleta de prestamo (HU-02-04): medios de envio (tabla
# comprobantes_prestamo).
MEDIO_CORREO = "Email"
MEDIO_WHATSAPP = "WhatsApp"
MEDIO_IMPRESION = "Impresión"
MEDIOS_BOLETA = [MEDIO_CORREO, MEDIO_WHATSAPP, MEDIO_IMPRESION]
# Lada que se agrega a los telefonos de 10 digitos para WhatsApp (Mexico).
LADA_WHATSAPP = "52"

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
