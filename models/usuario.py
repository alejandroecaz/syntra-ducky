"""
============================================================
Archivo:      models/usuario.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Modelo de usuarios: cuentas con nombre, apellidos, contacto, perfil y
    estado.

    La contrasena llega ya cifrada desde los servicios; aqui solo se
    guarda y se lee.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

from models.db import consultar, crear_patron_contiene, ejecutar

# Nombre completo armado con nombre y apellidos (el materno es opcional).
NOMBRE_COMPLETO = (
    "u.nombre || ' ' || u.apellido_paterno || COALESCE(' ' || "
    "u.apellido_materno, '')"
)

# No incluye la contrasena.
SELECT_USUARIO = f"""
    SELECT u.id, u.identificador, u.nombre, u.apellido_paterno,
           u.apellido_materno, {NOMBRE_COMPLETO} AS nombre_completo,
           u.cuenta, u.email, u.telefono, u.estado,
           u.perfil_id, u.fecha_registro, u.fecha_actualizacion,
           p.nombre AS perfil_nombre
    FROM usuarios u
    LEFT JOIN perfiles p ON p.id = u.perfil_id
"""


def obtener_por_id(usuario_id):
    """
    Descripcion:
        Busca un usuario por su id, sin la contrasena.

    Parametros:
        usuario_id (int): id del usuario.

    Salida:
        sqlite3.Row o None si no existe.
    """
    return consultar(
        SELECT_USUARIO + " WHERE u.id = ?", (usuario_id,), uno=True
    )


def obtener_para_login(cuenta):
    """
    Descripcion:
        Busca el usuario por su cuenta con el hash de su contrasena. Solo se
        usa para validar el inicio de sesion.

    Parametros:
        cuenta (str): nombre de la cuenta.

    Salida:
        sqlite3.Row o None si la cuenta no existe.
    """
    return consultar(
        f"SELECT u.*, {NOMBRE_COMPLETO} AS nombre_completo FROM usuarios u "
        "WHERE u.cuenta = ?",
        (cuenta,),
        uno=True,
    )


def obtener_hash(usuario_id):
    """
    Descripcion:
        Obtiene el hash de la contrasena guardada.

    Parametros:
        usuario_id (int): id del usuario.

    Salida:
        str o None si el usuario no existe.
    """
    fila = consultar(
        "SELECT contrasena FROM usuarios WHERE id = ?", (usuario_id,), uno=True
    )
    return fila["contrasena"] if fila else None


def listar():
    """
    Descripcion:
        Lista todos los usuarios ordenados por nombre.

    Parametros:
        Ninguno.

    Salida:
        list[sqlite3.Row]: usuarios sin contrasena.
    """
    return consultar(SELECT_USUARIO + " ORDER BY nombre_completo")


def buscar(criterio, valor):
    """
    Descripcion:
        Busca usuarios por identificador (exacto) o por nombre completo
        (contiene, sin acentos ni mayusculas).

    Parametros:
        criterio (str): 'identificador' o 'nombre'.
        valor (str): texto a buscar.

    Salida:
        list[sqlite3.Row]: usuarios encontrados.
    """
    # El identificador institucional se busca exacto.
    if criterio == "identificador":
        return consultar(
            SELECT_USUARIO + " WHERE u.identificador = ?", (valor,)
        )

    # El nombre se busca por coincidencia, sin acentos ni mayusculas.
    return consultar(
        SELECT_USUARIO
        + f" WHERE normalizar({NOMBRE_COMPLETO}) LIKE ? ESCAPE '\\' ORDER BY "
        "nombre_completo",
        (crear_patron_contiene(valor),),
    )


def verificar_identificador_existente(identificador):
    """
    Descripcion:
        Revisa si el identificador institucional ya esta registrado.

    Parametros:
        identificador (str): identificador institucional.

    Salida:
        bool: True si ya existe.
    """
    return (
        consultar(
            "SELECT id FROM usuarios WHERE identificador = ?",
            (identificador,),
            uno=True,
        )
        is not None
    )


def verificar_cuenta_en_uso(cuenta, excluir_id=None):
    """
    Descripcion:
        Revisa si otra persona ya usa esa cuenta. excluir_id evita contar al
        mismo usuario al editar.

    Parametros:
        cuenta (str): nombre de la cuenta.
        excluir_id (int o None): id del usuario que se edita.

    Salida:
        bool: True si otra persona ya usa la cuenta.
    """
    fila = consultar(
        "SELECT id FROM usuarios WHERE cuenta = ?", (cuenta,), uno=True
    )
    return fila is not None and fila["id"] != excluir_id


def verificar_email_en_uso(email, excluir_id=None):
    """
    Descripcion:
        Revisa si otra persona ya registro ese correo.

    Parametros:
        email (str): correo electronico.
        excluir_id (int o None): id del usuario que se edita.

    Salida:
        bool: True si otra persona ya usa el correo.
    """
    fila = consultar(
        "SELECT id FROM usuarios WHERE email = ?", (email,), uno=True
    )
    return fila is not None and fila["id"] != excluir_id


def crear(datos, contrasena_cifrada, perfil_id):
    """
    Descripcion:
        Registra la cuenta de un usuario.

    Parametros:
        datos (dict): identificador, nombre, apellidos, cuenta, email y
            telefono.
        contrasena_cifrada (str): hash de la contrasena.
        perfil_id (int): id del perfil asignado.

    Salida:
        int: id del usuario registrado.

    Excepciones:
        sqlite3.IntegrityError si el identificador, la cuenta o el correo ya
        existen.
    """
    return ejecutar(
        "INSERT INTO usuarios (identificador, nombre, apellido_paterno, "
        "apellido_materno, cuenta, email, "
        "telefono, contrasena, perfil_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            datos["identificador"],
            datos["nombre"],
            datos["apellido_paterno"],
            datos["apellido_materno"],
            datos["cuenta"],
            datos["email"],
            datos["telefono"],
            contrasena_cifrada,
            perfil_id,
        ),
    )


def actualizar_datos(usuario_id, datos):
    """
    Descripcion:
        Actualiza nombre, apellidos, cuenta y contacto. El identificador, el
        perfil y el estado no cambian.

    Parametros:
        usuario_id (int): id del usuario.
        datos (dict): nombre, apellidos, cuenta, email y telefono.

    Salida:
        Ninguna.

    Excepciones:
        sqlite3.IntegrityError si la cuenta o el correo ya los usa otra
        persona.
    """
    ejecutar(
        "UPDATE usuarios SET nombre = ?, apellido_paterno = ?, "
        "apellido_materno = ?, cuenta = ?, email = ?, "
        "telefono = ?, fecha_actualizacion = CURRENT_TIMESTAMP WHERE id = ?",
        (
            datos["nombre"],
            datos["apellido_paterno"],
            datos["apellido_materno"],
            datos["cuenta"],
            datos["email"],
            datos["telefono"],
            usuario_id,
        ),
    )


def cambiar_estado(usuario_id, estado):
    """
    Descripcion:
        Habilita o deshabilita la cuenta (baja logica).

    Parametros:
        usuario_id (int): id del usuario.
        estado (str): uno de config.ESTADOS_CUENTA.

    Salida:
        Ninguna.

    Excepciones:
        sqlite3.IntegrityError si el estado no es valido.
    """
    ejecutar(
        "UPDATE usuarios SET estado = ?, fecha_actualizacion = "
        "CURRENT_TIMESTAMP WHERE id = ?",
        (estado, usuario_id),
    )


def asignar_perfil(usuario_id, perfil_id):
    """
    Descripcion:
        Sustituye el perfil de la cuenta.

    Parametros:
        usuario_id (int): id del usuario.
        perfil_id (int): id del perfil nuevo.

    Salida:
        Ninguna.
    """
    ejecutar(
        "UPDATE usuarios SET perfil_id = ?, fecha_actualizacion = "
        "CURRENT_TIMESTAMP WHERE id = ?",
        (perfil_id, usuario_id),
    )


def cambiar_contrasena(usuario_id, contrasena_cifrada):
    """
    Descripcion:
        Guarda el nuevo hash de la contrasena.

    Parametros:
        usuario_id (int): id del usuario.
        contrasena_cifrada (str): hash de la contrasena nueva.

    Salida:
        Ninguna.
    """
    ejecutar(
        "UPDATE usuarios SET contrasena = ?, fecha_actualizacion = "
        "CURRENT_TIMESTAMP WHERE id = ?",
        (contrasena_cifrada, usuario_id),
    )


def contar_por_estado():
    """
    Descripcion:
        Cuenta las cuentas por estado.

    Parametros:
        Ninguno.

    Salida:
        dict[str, int]: numero de cuentas por estado.
    """
    filas = consultar(
        "SELECT estado, COUNT(*) AS total FROM usuarios GROUP BY estado"
    )
    return {fila["estado"]: fila["total"] for fila in filas}
