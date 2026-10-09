from werkzeug.security import check_password_hash, generate_password_hash

from models.db import consultar, ejecutar, normalizar

# No incluye la contraseña
SELECT_USUARIO = """
    SELECT u.id, u.identificador, u.nombre, u.cuenta, u.estado,
           u.perfil_id, u.fecha_registro, u.fecha_actualizacion,
           p.nombre AS perfil_nombre
    FROM usuarios u
    LEFT JOIN perfiles p ON p.id = u.perfil_id
"""


def obtener_por_id(usuario_id):
    return consultar(SELECT_USUARIO + " WHERE u.id = ?", (usuario_id,), uno=True)


def obtener_para_login(cuenta):
    # Aqui si se trae la contraseña para validar el login
    return consultar("SELECT * FROM usuarios WHERE cuenta = ?", (cuenta,), uno=True)


def validar_contrasena(usuario_id, contrasena):
    fila = consultar("SELECT contrasena FROM usuarios WHERE id = ?", (usuario_id,), uno=True)
    return bool(fila) and check_password_hash(fila["contrasena"], contrasena)


def listar():
    return consultar(SELECT_USUARIO + " ORDER BY u.nombre")


def buscar(criterio, valor):
    if criterio == "identificador":
        return consultar(SELECT_USUARIO + " WHERE u.identificador = ?", (valor,))
    return consultar(
        SELECT_USUARIO + " WHERE normalizar(u.nombre) LIKE ? ORDER BY u.nombre",
        (f"%{normalizar(valor)}%",),
    )


def existe_identificador(identificador):
    return consultar(
        "SELECT id FROM usuarios WHERE identificador = ?", (identificador,), uno=True
    ) is not None


def cuenta_en_uso(cuenta, excluir_id=None):
    # excluir_id es para no contar al mismo usuario cuando se edita
    fila = consultar("SELECT id FROM usuarios WHERE cuenta = ?", (cuenta,), uno=True)
    return fila is not None and fila["id"] != excluir_id


def crear(identificador, nombre, cuenta, contrasena, perfil_id):
    return ejecutar(
        "INSERT INTO usuarios (identificador, nombre, cuenta, contrasena, perfil_id) "
        "VALUES (?, ?, ?, ?, ?)",
        (identificador, nombre, cuenta, generate_password_hash(contrasena, method="pbkdf2:sha256"), perfil_id),
    )


def actualizar_datos(usuario_id, nombre, cuenta):
    ejecutar(
        "UPDATE usuarios SET nombre = ?, cuenta = ?, fecha_actualizacion = CURRENT_TIMESTAMP "
        "WHERE id = ?",
        (nombre, cuenta, usuario_id),
    )


def cambiar_estado(usuario_id, estado):
    ejecutar(
        "UPDATE usuarios SET estado = ?, fecha_actualizacion = CURRENT_TIMESTAMP WHERE id = ?",
        (estado, usuario_id),
    )


def asignar_perfil(usuario_id, perfil_id):
    ejecutar(
        "UPDATE usuarios SET perfil_id = ?, fecha_actualizacion = CURRENT_TIMESTAMP WHERE id = ?",
        (perfil_id, usuario_id),
    )


def cambiar_contrasena(usuario_id, nueva):
    ejecutar(
        "UPDATE usuarios SET contrasena = ?, fecha_actualizacion = CURRENT_TIMESTAMP WHERE id = ?",
        (generate_password_hash(nueva, method="pbkdf2:sha256"), usuario_id),
    )


def contar_por_estado():
    filas = consultar("SELECT estado, COUNT(*) AS total FROM usuarios GROUP BY estado")
    return {fila["estado"]: fila["total"] for fila in filas}
