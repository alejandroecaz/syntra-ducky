# ============================================================
# Archivo: models/libro.py
# Proyecto: Sistema Ducky de Gestión Bibliotecaria
# Syntra Technologies - Equipo 1 - Sprint 1
# Materia: Ingeniería de Software
# Autores:
#   - Melissa Silva Vázquez                #624352
#   - Tomás Zapata Pérez                   #629048
#   - Alejandro Evaristo Cazares Escobedo  #626337
# Descripción: Modelo de libros: tabla libros con su editorial, tema y autores (libro_autores).
# ============================================================
"""Modelo de libros: tabla libros con su editorial, tema y autores (libro_autores)."""
import config
from models.db import consultar, ejecutar, obtener_conexion, patron_contiene

# Nombre completo del autor, igual en todas las consultas
NOMBRE_AUTOR = "a.nombre || COALESCE(' ' || a.apellidos, '')"

# Autores del libro "l" en su orden, separados por coma
AUTORES_DEL_LIBRO = f"""
    (SELECT GROUP_CONCAT(nombre_completo, ', ') FROM (
        SELECT {NOMBRE_AUTOR} AS nombre_completo
        FROM libro_autores la JOIN autores a ON a.id = la.autor_id
        WHERE la.libro_id = l.id ORDER BY la.orden))
"""

# Libro con editorial, tema, autores, total de ejemplares y cuántos están disponibles.
# El primer parámetro siempre es el estado "Disponible".
SELECT_LIBRO = f"""
    SELECT l.*, ed.nombre AS editorial, t.nombre AS tema, {AUTORES_DEL_LIBRO} AS autores,
           COUNT(e.id) AS total_ejemplares,
           COALESCE(SUM(CASE WHEN e.estado = ? THEN 1 ELSE 0 END), 0) AS disponibles
    FROM libros l
    JOIN editoriales ed ON ed.id = l.editorial_id
    JOIN temas t ON t.id = l.tema_id
    LEFT JOIN ejemplares e ON e.libro_id = l.id
"""

# Condición de búsqueda para cada campo (la clave se busca exacta)
FILTROS_TEXTO = {
    "titulo": "normalizar(l.titulo) LIKE ? ESCAPE '\\'",
    "tema": "normalizar(t.nombre) LIKE ? ESCAPE '\\'",
    "editorial": "normalizar(ed.nombre) LIKE ? ESCAPE '\\'",
    "autor": f"""EXISTS (SELECT 1 FROM libro_autores la JOIN autores a ON a.id = la.autor_id
                 WHERE la.libro_id = l.id AND normalizar({NOMBRE_AUTOR}) LIKE ? ESCAPE '\\')""",
    "clave": "l.clave = ?",
}

# Condición para cada vista del catálogo ("todos" no filtra)
CONDICION_VISTA = {"activos": "l.activo = 1", "baja": "l.activo = 0", "todos": None}


def listar(campo=None, texto=None, tema=None, editorial=None, estado="activos"):
    """Libros que cumplen los filtros. estado: 'activos', 'baja' o 'todos'."""
    # El primer parámetro es el estado "Disponible" que usa SELECT_LIBRO
    condiciones, parametros = [], [config.ESTADO_DISPONIBLE]

    # Filtro por vista: activos, dados de baja o todos
    if CONDICION_VISTA.get(estado):
        condiciones.append(CONDICION_VISTA[estado])

    # Filtro por texto en el campo elegido (la clave va exacta, lo demás con LIKE)
    if campo in FILTROS_TEXTO and texto:
        condiciones.append(FILTROS_TEXTO[campo])
        parametros.append(texto if campo == "clave" else patron_contiene(texto))

    # Filtros exactos por tema y editorial (los usa el listado de reportes)
    if tema:
        condiciones.append("t.nombre = ?")
        parametros.append(tema)
    if editorial:
        condiciones.append("ed.nombre = ?")
        parametros.append(editorial)

    # Armamos la consulta final con las condiciones que hayan aplicado
    sql = SELECT_LIBRO
    if condiciones:
        sql += " WHERE " + " AND ".join(condiciones)
    sql += " GROUP BY l.id ORDER BY l.clave"
    return consultar(sql, parametros)


def destacados(limite):
    """Libros activos con ejemplares disponibles, los de más copias primero."""
    return consultar(
        SELECT_LIBRO + " WHERE l.activo = 1 GROUP BY l.id HAVING disponibles > 0 "
        "ORDER BY disponibles DESC, l.titulo LIMIT ?",
        (config.ESTADO_DISPONIBLE, limite),
    )


def obtener_por_id(libro_id):
    """Un libro con sus datos completos o None."""
    return consultar(
        SELECT_LIBRO + " WHERE l.id = ? GROUP BY l.id", (config.ESTADO_DISPONIBLE, libro_id), uno=True
    )


def existe_clave(clave):
    """True si la clave ya pertenece a un libro (sin importar mayúsculas)."""
    return consultar("SELECT id FROM libros WHERE clave = ?", (clave,), uno=True) is not None


def isbn_en_uso(isbn, excluir_id=None):
    """True si otro libro ya tiene ese ISBN."""
    # excluir_id evita que el libro que se edita choque consigo mismo
    fila = consultar("SELECT id FROM libros WHERE isbn = ?", (isbn,), uno=True)
    return fila is not None and fila["id"] != excluir_id


def nombres_autores(libro_id):
    """Nombres completos de los autores del libro en su orden."""
    filas = consultar(
        f"SELECT {NOMBRE_AUTOR} AS nombre FROM libro_autores la JOIN autores a ON a.id = la.autor_id "
        "WHERE la.libro_id = ? ORDER BY la.orden",
        (libro_id,),
    )
    return [fila["nombre"] for fila in filas]


def _guardar_autores(conexion, libro_id, autores_ids):
    """Reemplaza los autores del libro respetando el orden en que se capturaron (sin confirmar)."""
    # Borramos la relación anterior y la volvemos a insertar con su orden
    conexion.execute("DELETE FROM libro_autores WHERE libro_id = ?", (libro_id,))
    conexion.executemany(
        "INSERT INTO libro_autores (libro_id, autor_id, orden) VALUES (?, ?, ?)",
        [(libro_id, autor_id, orden) for orden, autor_id in enumerate(autores_ids, start=1)],
    )


def crear(datos, autores_ids):
    """Inserta el libro y su relación con autores en una sola transacción. Regresa el id."""
    # Insertamos el libro
    conexion = obtener_conexion()
    cursor = conexion.execute(
        "INSERT INTO libros (clave, titulo, editorial_id, tema_id, anio, isbn, edicion, sinopsis, tipo_acceso) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            datos["clave"], datos["titulo"], datos["editorial_id"], datos["tema_id"], datos["anio"],
            datos["isbn"], datos["edicion"], datos["sinopsis"], datos["tipo_acceso"],
        ),
    )
    libro_id = cursor.lastrowid

    # Guardamos sus autores y confirmamos todo junto
    _guardar_autores(conexion, libro_id, autores_ids)
    conexion.commit()
    return libro_id


def actualizar(libro_id, datos, autores_ids):
    """Actualiza los datos bibliográficos y los autores. La clave y los ejemplares no cambian."""
    # Actualizamos los datos del libro
    conexion = obtener_conexion()
    conexion.execute(
        "UPDATE libros SET titulo = ?, editorial_id = ?, tema_id = ?, anio = ?, isbn = ?, edicion = ?, "
        "sinopsis = ?, tipo_acceso = ? WHERE id = ?",
        (
            datos["titulo"], datos["editorial_id"], datos["tema_id"], datos["anio"], datos["isbn"],
            datos["edicion"], datos["sinopsis"], datos["tipo_acceso"], libro_id,
        ),
    )

    # Reemplazamos sus autores y confirmamos todo junto
    _guardar_autores(conexion, libro_id, autores_ids)
    conexion.commit()


def dar_baja(libro_id):
    """Baja lógica: no se borra, solo se marca como inactivo."""
    ejecutar("UPDATE libros SET activo = 0, fecha_baja = CURRENT_TIMESTAMP WHERE id = ?", (libro_id,))


def contar():
    """Totales para el panel de inicio: libros activos, ejemplares y disponibles."""
    return consultar(
        """
        SELECT
          (SELECT COUNT(*) FROM libros WHERE activo = 1) AS libros_activos,
          (SELECT COUNT(*) FROM ejemplares e JOIN libros l ON l.id = e.libro_id
             WHERE l.activo = 1) AS ejemplares,
          (SELECT COUNT(*) FROM ejemplares e JOIN libros l ON l.id = e.libro_id
             WHERE l.activo = 1 AND e.estado = ?) AS disponibles
        """,
        (config.ESTADO_DISPONIBLE,),
        uno=True,
    )
