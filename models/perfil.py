from models.db import consultar, ejecutar, obtener_conexion


def listar():
    return consultar(
        """
        SELECT p.*,
               (SELECT COUNT(*) FROM perfil_permisos pp WHERE pp.perfil_id = p.id) AS total_permisos,
               (SELECT COUNT(*) FROM usuarios u WHERE u.perfil_id = p.id) AS total_usuarios
        FROM perfiles p
        ORDER BY p.disponible DESC, p.nombre
        """
    )


def obtener_por_id(perfil_id):
    return consultar("SELECT * FROM perfiles WHERE id = ?", (perfil_id,), uno=True)


def existe_nombre(nombre):
    # No distingue mayusculas, 'alumno' y 'Alumno' cuentan como el mismo
    return consultar("SELECT id FROM perfiles WHERE nombre = ?", (nombre,), uno=True) is not None


def permisos_de(perfil_id):
    filas = consultar("SELECT permiso FROM perfil_permisos WHERE perfil_id = ?", (perfil_id,))
    return [fila["permiso"] for fila in filas]


def permisos_por_perfil():
    resultado = {}
    for fila in consultar("SELECT perfil_id, permiso FROM perfil_permisos"):
        resultado.setdefault(fila["perfil_id"], []).append(fila["permiso"])
    return resultado


def crear(nombre, descripcion, permisos):
    conexion = obtener_conexion()
    cursor = conexion.execute(
        "INSERT INTO perfiles (nombre, descripcion) VALUES (?, ?)", (nombre, descripcion)
    )
    perfil_id = cursor.lastrowid
    conexion.executemany(
        "INSERT INTO perfil_permisos (perfil_id, permiso) VALUES (?, ?)",
        [(perfil_id, permiso) for permiso in permisos],
    )
    conexion.commit()
    return perfil_id

