# ============================================================
# Archivo: models/perfil.py
# Proyecto: Sistema Ducky de Gestión Bibliotecaria
# Syntra Technologies - Equipo 1 - Sprint 1
# Materia: Ingeniería de Software
# Autores:
#   - Melissa Silva Vázquez                #624352
#   - Tomás Zapata Pérez                   #629048
#   - Alejandro Evaristo Cazares Escobedo  #626337
# Descripción: Modelo de perfiles de usuario y sus permisos (tablas perfiles y perfil_permisos).
# ============================================================
"""Modelo de perfiles de usuario y sus permisos (tablas perfiles y perfil_permisos)."""
from models.db import consultar, obtener_conexion


def listar():
    """Perfiles con su número de permisos y de cuentas; primero los disponibles."""
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
    """Un perfil o None."""
    return consultar("SELECT * FROM perfiles WHERE id = ?", (perfil_id,), uno=True)


def existe_nombre(nombre):
    """True si ya hay un perfil con ese nombre ('alumno' y 'Alumno' cuentan como el mismo)."""
    return consultar("SELECT id FROM perfiles WHERE nombre = ?", (nombre,), uno=True) is not None


def permisos_de(perfil_id):
    """Códigos de los permisos del perfil."""
    filas = consultar(
        "SELECT pe.codigo FROM perfil_permisos pp JOIN permisos pe ON pe.id = pp.permiso_id "
        "WHERE pp.perfil_id = ? ORDER BY pe.id",
        (perfil_id,),
    )
    return [fila["codigo"] for fila in filas]


def permisos_por_perfil():
    """Diccionario perfil_id -> lista de códigos de permiso."""
    # Traemos todas las relaciones perfil-permiso en una sola consulta
    resultado = {}
    filas = consultar(
        "SELECT pp.perfil_id, pe.codigo FROM perfil_permisos pp JOIN permisos pe ON pe.id = pp.permiso_id "
        "ORDER BY pe.id"
    )

    # Agrupamos los códigos por perfil
    for fila in filas:
        resultado.setdefault(fila["perfil_id"], []).append(fila["codigo"])
    return resultado


def crear(nombre, descripcion, codigos):
    """Registra el perfil con sus permisos en una sola transacción. Regresa el id."""
    # Insertamos el perfil
    conexion = obtener_conexion()
    cursor = conexion.execute(
        "INSERT INTO perfiles (nombre, descripcion) VALUES (?, ?)", (nombre, descripcion or None)
    )
    perfil_id = cursor.lastrowid

    # Relacionamos sus permisos (por código) y confirmamos todo junto
    conexion.executemany(
        "INSERT INTO perfil_permisos (perfil_id, permiso_id) SELECT ?, id FROM permisos WHERE codigo = ?",
        [(perfil_id, codigo) for codigo in codigos],
    )
    conexion.commit()
    return perfil_id
