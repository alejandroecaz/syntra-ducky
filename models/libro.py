"""
============================================================
Archivo:      models/libro.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Modelo de libros: tabla libros con su editorial, tema y autores
    (libro_autores).

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

import config
from models.db import (
    consultar,
    crear_patron_contiene,
    ejecutar,
    obtener_conexion,
)

# Nombre completo del autor, igual en todas las consultas.
NOMBRE_AUTOR = "a.nombre || COALESCE(' ' || a.apellidos, '')"

# Autores del libro "l" en su orden, separados por coma.
AUTORES_DEL_LIBRO = f"""
    (SELECT GROUP_CONCAT(nombre_completo, ', ') FROM (
        SELECT {NOMBRE_AUTOR} AS nombre_completo
        FROM libro_autores la JOIN autores a ON a.id = la.autor_id
        WHERE la.libro_id = l.id ORDER BY la.orden))
"""

# Libro con editorial, tema, autores, total de ejemplares y cuantos estan
# disponibles.
# El primer parametro siempre es el estado "Disponible".
SELECT_LIBRO = f"""
    SELECT l.*, ed.nombre AS editorial, t.nombre AS tema,
           {AUTORES_DEL_LIBRO} AS autores,
           COUNT(e.id) AS total_ejemplares,
           COALESCE(SUM(CASE WHEN e.estado = ? THEN 1 ELSE 0 END), 0)
               AS disponibles
    FROM libros l
    JOIN editoriales ed ON ed.id = l.editorial_id
    JOIN temas t ON t.id = l.tema_id
    LEFT JOIN ejemplares e ON e.libro_id = l.id
"""

# Condicion de busqueda para cada campo (la clave se busca exacta).
FILTROS_TEXTO = {
    "titulo": "normalizar(l.titulo) LIKE ? ESCAPE '\\'",
    "tema": "normalizar(t.nombre) LIKE ? ESCAPE '\\'",
    "editorial": "normalizar(ed.nombre) LIKE ? ESCAPE '\\'",
    "autor": f"""EXISTS (
        SELECT 1 FROM libro_autores la JOIN autores a ON a.id = la.autor_id
        WHERE la.libro_id = l.id
          AND normalizar({NOMBRE_AUTOR}) LIKE ? ESCAPE '\\')""",
    "clave": "l.clave = ?",
}

# Condicion para cada vista del catalogo ("todos" no filtra).
CONDICION_VISTA = {
    "activos": "l.activo = 1",
    "baja": "l.activo = 0",
    "todos": None,
}


def listar(
    campo=None, texto=None, tema=None, editorial=None, estado="activos"
):
    """
    Descripcion:
        Lista los libros que cumplen los filtros, con editorial, tema, autores
        y disponibles. La clave se busca exacta y los demas campos por
        coincidencia sin acentos.

    Parametros:
        campo (str o None): campo de busqueda (titulo, autor, tema, editorial o
            clave).
        texto (str o None): texto a buscar en el campo.
        tema (str o None): nombre exacto del tema.
        editorial (str o None): nombre exacto de la editorial.
        estado (str): vista: 'activos', 'baja' o 'todos'.

    Salida:
        list[sqlite3.Row]: libros ordenados por clave.
    """
    # El primer parametro es el estado "Disponible" que usa SELECT_LIBRO.
    condiciones, parametros = [], [config.ESTADO_DISPONIBLE]

    # Filtro por vista: activos, dados de baja o todos.
    if CONDICION_VISTA.get(estado):
        condiciones.append(CONDICION_VISTA[estado])

    # Filtro por texto en el campo elegido (la clave va exacta, lo demas con
    # LIKE).
    if campo in FILTROS_TEXTO and texto:
        condiciones.append(FILTROS_TEXTO[campo])
        parametros.append(
            texto if campo == "clave" else crear_patron_contiene(texto)
        )

    # Filtros exactos por tema y editorial (los usa el listado de reportes).
    if tema:
        condiciones.append("t.nombre = ?")
        parametros.append(tema)
    if editorial:
        condiciones.append("ed.nombre = ?")
        parametros.append(editorial)

    # Armamos la consulta final con las condiciones que hayan aplicado.
    sql = SELECT_LIBRO
    if condiciones:
        sql += " WHERE " + " AND ".join(condiciones)
    sql += " GROUP BY l.id ORDER BY l.clave"
    return consultar(sql, parametros)


def listar_destacados(limite):
    """
    Descripcion:
        Lista libros activos con ejemplares disponibles, los de mas copias
        primero.

    Parametros:
        limite (int): numero maximo de libros.

    Salida:
        list[sqlite3.Row]: libros destacados.
    """
    return consultar(
        SELECT_LIBRO
        + " WHERE l.activo = 1 GROUP BY l.id HAVING disponibles > 0 "
        "ORDER BY disponibles DESC, l.titulo LIMIT ?",
        (config.ESTADO_DISPONIBLE, limite),
    )


def obtener_por_id(libro_id):
    """
    Descripcion:
        Busca un libro por su id con sus datos completos.

    Parametros:
        libro_id (int): id del libro.

    Salida:
        sqlite3.Row o None si no existe.
    """
    return consultar(
        SELECT_LIBRO + " WHERE l.id = ? GROUP BY l.id",
        (config.ESTADO_DISPONIBLE, libro_id),
        uno=True,
    )


def verificar_clave_existente(clave):
    """
    Descripcion:
        Revisa si la clave ya pertenece a un libro.

    Parametros:
        clave (str): clave del libro, por ejemplo LIB-001.

    Salida:
        bool: True si la clave ya existe.
    """
    return (
        consultar("SELECT id FROM libros WHERE clave = ?", (clave,), uno=True)
        is not None
    )


def verificar_isbn_en_uso(isbn, excluir_id=None):
    """
    Descripcion:
        Revisa si otro libro ya tiene ese ISBN. excluir_id evita que el libro
        que se edita choque consigo mismo.

    Parametros:
        isbn (str): ISBN a revisar.
        excluir_id (int o None): id del libro que se esta editando.

    Salida:
        bool: True si otro libro ya usa el ISBN.
    """
    # excluir_id evita que el libro que se edita choque consigo mismo.
    fila = consultar("SELECT id FROM libros WHERE isbn = ?", (isbn,), uno=True)
    return fila is not None and fila["id"] != excluir_id


def obtener_nombres_autores(libro_id):
    """
    Descripcion:
        Obtiene los nombres completos de los autores del libro en su orden.

    Parametros:
        libro_id (int): id del libro.

    Salida:
        list[str]: nombres de los autores.
    """
    filas = consultar(
        f"SELECT {NOMBRE_AUTOR} AS nombre FROM libro_autores la JOIN autores "
        "a ON a.id = la.autor_id "
        "WHERE la.libro_id = ? ORDER BY la.orden",
        (libro_id,),
    )
    return [fila["nombre"] for fila in filas]


def _guardar_autores(conexion, libro_id, autores_ids):
    """
    Descripcion:
        Reemplaza los autores del libro respetando el orden en que se
        capturaron. No confirma la transaccion; la confirma quien la llama.

    Parametros:
        conexion (sqlite3.Connection): conexion de la transaccion.
        libro_id (int): id del libro.
        autores_ids (list[int]): ids de los autores en orden.

    Salida:
        Ninguna.
    """
    # Borramos la relacion anterior y la volvemos a insertar con su orden.
    conexion.execute(
        "DELETE FROM libro_autores WHERE libro_id = ?", (libro_id,)
    )
    conexion.executemany(
        "INSERT INTO libro_autores (libro_id, autor_id, orden) VALUES (?, ?, "
        "?)",
        [
            (libro_id, autor_id, orden)
            for orden, autor_id in enumerate(autores_ids, start=1)
        ],
    )


def crear(datos, autores_ids):
    """
    Descripcion:
        Inserta el libro y su relacion con autores en una sola transaccion.

    Parametros:
        datos (dict): clave, titulo, editorial_id, tema_id, anio, isbn,
            edicion, sinopsis y tipo_acceso.
        autores_ids (list[int]): ids de los autores en orden.

    Salida:
        int: id del libro registrado.

    Excepciones:
        sqlite3.IntegrityError si la clave o el ISBN ya existen.
    """
    # Insertamos el libro.
    conexion = obtener_conexion()
    cursor = conexion.execute(
        "INSERT INTO libros (clave, titulo, editorial_id, tema_id, anio, "
        "isbn, edicion, sinopsis, tipo_acceso) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            datos["clave"],
            datos["titulo"],
            datos["editorial_id"],
            datos["tema_id"],
            datos["anio"],
            datos["isbn"],
            datos["edicion"],
            datos["sinopsis"],
            datos["tipo_acceso"],
        ),
    )
    libro_id = cursor.lastrowid

    # Guardamos sus autores y confirmamos todo junto.
    _guardar_autores(conexion, libro_id, autores_ids)
    conexion.commit()
    return libro_id


def actualizar(libro_id, datos, autores_ids):
    """
    Descripcion:
        Actualiza los datos bibliograficos y los autores del libro. La clave y
        los ejemplares no cambian.

    Parametros:
        libro_id (int): id del libro.
        datos (dict): titulo, editorial_id, tema_id, anio, isbn, edicion,
            sinopsis y tipo_acceso.
        autores_ids (list[int]): ids de los autores en orden.

    Salida:
        Ninguna.

    Excepciones:
        sqlite3.IntegrityError si el ISBN ya lo usa otro libro.
    """
    # Actualizamos los datos del libro.
    conexion = obtener_conexion()
    conexion.execute(
        "UPDATE libros SET titulo = ?, editorial_id = ?, tema_id = ?, anio = "
        "?, isbn = ?, edicion = ?, "
        "sinopsis = ?, tipo_acceso = ? WHERE id = ?",
        (
            datos["titulo"],
            datos["editorial_id"],
            datos["tema_id"],
            datos["anio"],
            datos["isbn"],
            datos["edicion"],
            datos["sinopsis"],
            datos["tipo_acceso"],
            libro_id,
        ),
    )

    # Reemplazamos sus autores y confirmamos todo junto.
    _guardar_autores(conexion, libro_id, autores_ids)
    conexion.commit()


def dar_baja(libro_id):
    """
    Descripcion:
        Da de baja el libro de forma logica: no se borra, solo se marca como
        inactivo con la fecha de baja.

    Parametros:
        libro_id (int): id del libro.

    Salida:
        Ninguna.
    """
    ejecutar(
        "UPDATE libros SET activo = 0, fecha_baja = CURRENT_TIMESTAMP WHERE "
        "id = ?",
        (libro_id,),
    )


def contar():
    """
    Descripcion:
        Cuenta los totales para el panel de inicio: libros activos, ejemplares
        y disponibles.

    Parametros:
        Ninguno.

    Salida:
        sqlite3.Row: libros_activos, ejemplares y disponibles.
    """
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
