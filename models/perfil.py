"""
============================================================
Archivo:      models/perfil.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Modelo de perfiles de usuario y sus permisos (tablas perfiles y
    perfil_permisos).

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

from models.db import consultar, obtener_conexion


def listar():
    """
    Descripcion:
        Lista los perfiles con su numero de permisos y de cuentas; primero los
        disponibles.

    Parametros:
        Ninguno.

    Salida:
        list[sqlite3.Row]: perfiles.
    """
    return consultar(
        """
        SELECT p.*,
               (SELECT COUNT(*) FROM perfil_permisos pp
                 WHERE pp.perfil_id = p.id) AS total_permisos,
               (SELECT COUNT(*) FROM usuarios u
                 WHERE u.perfil_id = p.id) AS total_usuarios
        FROM perfiles p
        ORDER BY p.disponible DESC, p.nombre
        """
    )


def obtener_por_id(perfil_id):
    """
    Descripcion:
        Busca un perfil por su id.

    Parametros:
        perfil_id (int): id del perfil.

    Salida:
        sqlite3.Row o None si no existe.
    """
    return consultar(
        "SELECT * FROM perfiles WHERE id = ?", (perfil_id,), uno=True
    )


def verificar_nombre_existente(nombre):
    """
    Descripcion:
        Revisa si ya hay un perfil con ese nombre ('alumno' y 'Alumno' cuentan
        como el mismo).

    Parametros:
        nombre (str): nombre del perfil.

    Salida:
        bool: True si el nombre ya existe.
    """
    return (
        consultar(
            "SELECT id FROM perfiles WHERE nombre = ?", (nombre,), uno=True
        )
        is not None
    )


def listar_permisos(perfil_id):
    """
    Descripcion:
        Lista los codigos de los permisos del perfil.

    Parametros:
        perfil_id (int): id del perfil.

    Salida:
        list[str]: codigos de permiso.
    """
    filas = consultar(
        "SELECT pe.codigo FROM perfil_permisos pp JOIN permisos pe ON pe.id "
        "= pp.permiso_id "
        "WHERE pp.perfil_id = ? ORDER BY pe.id",
        (perfil_id,),
    )
    return [fila["codigo"] for fila in filas]


def listar_permisos_por_perfil():
    """
    Descripcion:
        Agrupa en una sola consulta los codigos de permiso de cada perfil.

    Parametros:
        Ninguno.

    Salida:
        dict[int, list[str]]: codigos de permiso por id de perfil.
    """
    # Traemos todas las relaciones perfil-permiso en una sola consulta.
    resultado = {}
    filas = consultar(
        "SELECT pp.perfil_id, pe.codigo FROM perfil_permisos pp JOIN "
        "permisos pe ON pe.id = pp.permiso_id "
        "ORDER BY pe.id"
    )

    # Agrupamos los codigos por perfil.
    for fila in filas:
        resultado.setdefault(fila["perfil_id"], []).append(fila["codigo"])
    return resultado


def crear(nombre, descripcion, codigos):
    """
    Descripcion:
        Registra el perfil con sus permisos en una sola transaccion.

    Parametros:
        nombre (str): nombre del perfil.
        descripcion (str): descripcion (opcional).
        codigos (list[str]): codigos de los permisos.

    Salida:
        int: id del perfil registrado.

    Excepciones:
        sqlite3.IntegrityError si el nombre ya existe.
    """
    # Insertamos el perfil.
    conexion = obtener_conexion()
    cursor = conexion.execute(
        "INSERT INTO perfiles (nombre, descripcion) VALUES (?, ?)",
        (nombre, descripcion or None),
    )
    perfil_id = cursor.lastrowid

    # Relacionamos sus permisos (por codigo) y confirmamos todo junto.
    conexion.executemany(
        "INSERT INTO perfil_permisos (perfil_id, permiso_id) SELECT ?, id "
        "FROM permisos WHERE codigo = ?",
        [(perfil_id, codigo) for codigo in codigos],
    )
    conexion.commit()
    return perfil_id
