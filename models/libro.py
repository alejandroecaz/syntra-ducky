import config
from models.db import consultar, ejecutar, normalizar

# Trae el libro con su total de ejemplares y cuantos estan disponibles
SELECT_LIBRO = """
    SELECT l.*,
           COUNT(e.id) AS total_ejemplares,
           COALESCE(SUM(CASE WHEN e.estado = 'Disponible' THEN 1 ELSE 0 END), 0) AS disponibles
    FROM libros l
    LEFT JOIN ejemplares e ON e.libro_id = l.id
"""

# Solo se puede buscar por estos campos
CAMPOS_VALIDOS = {campo for campo, _ in config.CAMPOS_BUSQUEDA}


def listar(campo=None, texto=None, tema=None, editorial=None, estado="activos"):
    # La clave se busca exacta, lo demas por coincidencia
    condiciones, parametros = [], []

    if estado == "activos":
        condiciones.append("l.activo = 1")
    elif estado == "baja":
        condiciones.append("l.activo = 0")

    if campo in CAMPOS_VALIDOS and texto:
        if campo == "clave":
            condiciones.append("l.clave = ?")
            parametros.append(texto)
        else:
            condiciones.append(f"normalizar(l.{campo}) LIKE ?")
            parametros.append(f"%{normalizar(texto)}%")

    if tema:
        condiciones.append("l.tema = ?")
        parametros.append(tema)
    if editorial:
        condiciones.append("l.editorial = ?")
        parametros.append(editorial)

    sql = SELECT_LIBRO
    if condiciones:
        sql += " WHERE " + " AND ".join(condiciones)
    sql += " GROUP BY l.id ORDER BY l.clave"
    return consultar(sql, parametros)


def obtener_por_id(libro_id):
    return consultar(SELECT_LIBRO + " WHERE l.id = ? GROUP BY l.id", (libro_id,), uno=True)


def existe_clave(clave):
    return consultar("SELECT id FROM libros WHERE clave = ?", (clave,), uno=True) is not None


def valores_distintos(columna):
    if columna not in ("tema", "editorial"):
        return []
    filas = consultar(f"SELECT DISTINCT {columna} AS valor FROM libros ORDER BY {columna}")
    return [fila["valor"] for fila in filas]


def crear(clave, titulo, autor, tema, editorial, anio):
    return ejecutar(
        "INSERT INTO libros (clave, titulo, autor, tema, editorial, anio) VALUES (?, ?, ?, ?, ?, ?)",
        (clave, titulo, autor, tema, editorial, anio),
    )


def actualizar(libro_id, titulo, autor, tema, editorial, anio):
    ejecutar(
        "UPDATE libros SET titulo = ?, autor = ?, tema = ?, editorial = ?, anio = ? WHERE id = ?",
        (titulo, autor, tema, editorial, anio, libro_id),
    )


def operaciones_vigentes(libro_id):
    # Ejemplares prestados o reservados
    marcadores = ",".join("?" for _ in config.ESTADOS_OPERACION_VIGENTE)
    return consultar(
        f"SELECT codigo, estado FROM ejemplares WHERE libro_id = ? AND estado IN ({marcadores})",
        (libro_id, *config.ESTADOS_OPERACION_VIGENTE),
    )


def dar_baja(libro_id):
    # No se borra, solo se marca como inactivo
    ejecutar(
        "UPDATE libros SET activo = 0, fecha_baja = CURRENT_TIMESTAMP WHERE id = ?", (libro_id,)
    )


def contar():
    return consultar(
        """
        SELECT
          (SELECT COUNT(*) FROM libros WHERE activo = 1) AS libros_activos,
          (SELECT COUNT(*) FROM ejemplares e JOIN libros l ON l.id = e.libro_id
             WHERE l.activo = 1) AS ejemplares,
          (SELECT COUNT(*) FROM ejemplares e JOIN libros l ON l.id = e.libro_id
             WHERE l.activo = 1 AND e.estado = 'Disponible') AS disponibles
        """,
        uno=True,
    )


# Ejemplares

def ejemplares_de(libro_id):
    return consultar(
        "SELECT * FROM ejemplares WHERE libro_id = ? ORDER BY codigo", (libro_id,)
    )


def obtener_ejemplar(ejemplar_id):
    return consultar("SELECT * FROM ejemplares WHERE id = ?", (ejemplar_id,), uno=True)


def siguiente_codigo_ejemplar():
    fila = consultar("SELECT MAX(id) AS ultimo FROM ejemplares", uno=True)
    return f"EJ-{(fila['ultimo'] or 0) + 1:04d}"


def agregar_ejemplar(libro_id, estancia, estante, posicion, estado):
    codigo = siguiente_codigo_ejemplar()
    ejecutar(
        "INSERT INTO ejemplares (codigo, libro_id, estancia, estante, posicion, estado) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (codigo, libro_id, estancia, estante, posicion, estado),
    )
    return codigo


def actualizar_ejemplar(ejemplar_id, estancia, estante, posicion, estado):
    ejecutar(
        "UPDATE ejemplares SET estancia = ?, estante = ?, posicion = ?, estado = ?, "
        "fecha_actualizacion = CURRENT_TIMESTAMP WHERE id = ?",
        (estancia, estante, posicion, estado, ejemplar_id),
    )
