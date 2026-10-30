# ============================================================
# Archivo: models/ejemplar.py
# Proyecto: Sistema Ducky de Gestión Bibliotecaria
# Syntra Technologies - Equipo 1 - Sprint 1
# Materia: Ingeniería de Software
# Autores:
#   - Melissa Silva Vázquez                #624352
#   - Tomás Zapata Pérez                   #629048
#   - Alejandro Evaristo Cazares Escobedo  #626337
# Descripción: Modelo de ejemplares: copias físicas de cada libro con su ubicación (estancia → estante) y
#              estado.
# ============================================================
"""Modelo de ejemplares: copias físicas de cada libro con su ubicación (estancia → estante) y estado."""
import config
from models.db import consultar, ejecutar

# Ejemplar con el nombre de su estancia y la clave de su estante (None si la ubicación está pendiente)
SELECT_EJEMPLAR = """
    SELECT e.id, e.codigo, e.libro_id, e.estante_id, e.posicion, e.estado, e.fecha_alta,
           COALESCE(e.fecha_actualizacion, e.fecha_alta) AS fecha_actualizacion,
           es.clave AS estante, ea.id AS estancia_id, ea.nombre AS estancia
    FROM ejemplares e
    LEFT JOIN estantes es ON es.id = e.estante_id
    LEFT JOIN estancias ea ON ea.id = es.estancia_id
"""


def de_libro(libro_id):
    """Ejemplares de un libro ordenados por código."""
    return consultar(SELECT_EJEMPLAR + " WHERE e.libro_id = ? ORDER BY e.codigo", (libro_id,))


def obtener(ejemplar_id):
    """Un ejemplar o None."""
    return consultar(SELECT_EJEMPLAR + " WHERE e.id = ?", (ejemplar_id,), uno=True)


def operaciones_vigentes(libro_id):
    """Ejemplares del libro que están prestados o reservados."""
    # Un "?" por cada estado de operación vigente
    marcadores = ",".join("?" for _ in config.ESTADOS_OPERACION_VIGENTE)
    return consultar(
        f"SELECT codigo, estado FROM ejemplares WHERE libro_id = ? AND estado IN ({marcadores}) ORDER BY codigo",
        (libro_id, *config.ESTADOS_OPERACION_VIGENTE),
    )


def siguiente_codigo():
    """Código consecutivo para un ejemplar nuevo (EJ-0001, EJ-0002...)."""
    # Tomamos el último id y le sumamos uno
    fila = consultar("SELECT MAX(id) AS ultimo FROM ejemplares", uno=True)
    return f"{config.PREFIJO_EJEMPLAR}{(fila['ultimo'] or 0) + 1:04d}"


def agregar(libro_id, estante_id, posicion, estado):
    """Registra un ejemplar y regresa su código."""
    # Generamos el código y guardamos el ejemplar
    codigo = siguiente_codigo()
    ejecutar(
        "INSERT INTO ejemplares (codigo, libro_id, estante_id, posicion, estado, fecha_actualizacion) "
        "VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
        (codigo, libro_id, estante_id, posicion, estado),
    )
    return codigo


def actualizar(ejemplar_id, estante_id, posicion, estado):
    """Cambia la ubicación y el estado de un ejemplar."""
    ejecutar(
        "UPDATE ejemplares SET estante_id = ?, posicion = ?, estado = ?, fecha_actualizacion = CURRENT_TIMESTAMP "
        "WHERE id = ?",
        (estante_id, posicion, estado, ejemplar_id),
    )
