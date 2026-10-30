# ============================================================
# Archivo: models/usuario.py
# Proyecto: Sistema Ducky de Gestión Bibliotecaria
# Syntra Technologies - Equipo 1 - Sprint 1
# Materia: Ingeniería de Software
# Autores:
#   - Melissa Silva Vázquez                #624352
#   - Tomás Zapata Pérez                   #629048
#   - Alejandro Evaristo Cazares Escobedo  #626337
# Descripción: Modelo de usuarios: cuentas con nombre, apellidos, contacto, perfil y estado.
# ============================================================
"""Modelo de usuarios: cuentas con nombre, apellidos, contacto, perfil y estado.

La contraseña llega ya cifrada desde los servicios; aquí solo se guarda y se lee.
"""
from models.db import consultar, ejecutar, patron_contiene

# Nombre completo armado con nombre y apellidos (el materno es opcional)
NOMBRE_COMPLETO = "u.nombre || ' ' || u.apellido_paterno || COALESCE(' ' || u.apellido_materno, '')"

# No incluye la contraseña
SELECT_USUARIO = f"""
    SELECT u.id, u.identificador, u.nombre, u.apellido_paterno, u.apellido_materno,
           {NOMBRE_COMPLETO} AS nombre_completo, u.cuenta, u.email, u.telefono, u.estado,
           u.perfil_id, u.fecha_registro, u.fecha_actualizacion,
           p.nombre AS perfil_nombre
    FROM usuarios u
    LEFT JOIN perfiles p ON p.id = u.perfil_id
"""


def obtener_por_id(usuario_id):
    """Un usuario (sin contraseña) o None."""
    return consultar(SELECT_USUARIO + " WHERE u.id = ?", (usuario_id,), uno=True)


def obtener_para_login(cuenta):
    """Usuario con el hash de su contraseña, solo para validar el inicio de sesión."""
    return consultar(
        f"SELECT u.*, {NOMBRE_COMPLETO} AS nombre_completo FROM usuarios u WHERE u.cuenta = ?", (cuenta,), uno=True
    )


def obtener_hash(usuario_id):
    """Hash de la contraseña guardada o None."""
    fila = consultar("SELECT contrasena FROM usuarios WHERE id = ?", (usuario_id,), uno=True)
    return fila["contrasena"] if fila else None


def listar():
    """Todos los usuarios ordenados por nombre."""
    return consultar(SELECT_USUARIO + " ORDER BY nombre_completo")


def buscar(criterio, valor):
    """Por identificador (exacto) o por nombre completo (contiene, sin acentos)."""
    # El identificador institucional se busca exacto
    if criterio == "identificador":
        return consultar(SELECT_USUARIO + " WHERE u.identificador = ?", (valor,))

    # El nombre se busca por coincidencia, sin acentos ni mayúsculas
    return consultar(
        SELECT_USUARIO + f" WHERE normalizar({NOMBRE_COMPLETO}) LIKE ? ESCAPE '\\' ORDER BY nombre_completo",
        (patron_contiene(valor),),
    )


def existe_identificador(identificador):
    """True si el identificador institucional ya está registrado."""
    return consultar(
        "SELECT id FROM usuarios WHERE identificador = ?", (identificador,), uno=True
    ) is not None


def cuenta_en_uso(cuenta, excluir_id=None):
    """True si otra persona ya usa esa cuenta. excluir_id evita contar al mismo usuario al editar."""
    fila = consultar("SELECT id FROM usuarios WHERE cuenta = ?", (cuenta,), uno=True)
    return fila is not None and fila["id"] != excluir_id


def email_en_uso(email, excluir_id=None):
    """True si otra persona ya registró ese correo."""
    fila = consultar("SELECT id FROM usuarios WHERE email = ?", (email,), uno=True)
    return fila is not None and fila["id"] != excluir_id


def crear(datos, contrasena_cifrada, perfil_id):
    """Registra la cuenta y regresa su id."""
    return ejecutar(
        "INSERT INTO usuarios (identificador, nombre, apellido_paterno, apellido_materno, cuenta, email, "
        "telefono, contrasena, perfil_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            datos["identificador"], datos["nombre"], datos["apellido_paterno"], datos["apellido_materno"],
            datos["cuenta"], datos["email"], datos["telefono"], contrasena_cifrada, perfil_id,
        ),
    )


def actualizar_datos(usuario_id, datos):
    """Actualiza nombre, apellidos, cuenta y contacto. Identificador, perfil y estado no cambian."""
    ejecutar(
        "UPDATE usuarios SET nombre = ?, apellido_paterno = ?, apellido_materno = ?, cuenta = ?, email = ?, "
        "telefono = ?, fecha_actualizacion = CURRENT_TIMESTAMP WHERE id = ?",
        (
            datos["nombre"], datos["apellido_paterno"], datos["apellido_materno"], datos["cuenta"],
            datos["email"], datos["telefono"], usuario_id,
        ),
    )


def cambiar_estado(usuario_id, estado):
    """Habilita o deshabilita la cuenta (baja lógica)."""
    ejecutar(
        "UPDATE usuarios SET estado = ?, fecha_actualizacion = CURRENT_TIMESTAMP WHERE id = ?",
        (estado, usuario_id),
    )


def asignar_perfil(usuario_id, perfil_id):
    """Sustituye el perfil de la cuenta."""
    ejecutar(
        "UPDATE usuarios SET perfil_id = ?, fecha_actualizacion = CURRENT_TIMESTAMP WHERE id = ?",
        (perfil_id, usuario_id),
    )


def cambiar_contrasena(usuario_id, contrasena_cifrada):
    """Guarda el nuevo hash de la contraseña."""
    ejecutar(
        "UPDATE usuarios SET contrasena = ?, fecha_actualizacion = CURRENT_TIMESTAMP WHERE id = ?",
        (contrasena_cifrada, usuario_id),
    )


def contar_por_estado():
    """Diccionario estado -> número de cuentas."""
    filas = consultar("SELECT estado, COUNT(*) AS total FROM usuarios GROUP BY estado")
    return {fila["estado"]: fila["total"] for fila in filas}
