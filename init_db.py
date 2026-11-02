"""
============================================================
Archivo:      init_db.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Crea la base de datos SQLite con el esquema del Sprint 1 y los datos
    de demostracion.

    El esquema sigue el diseno de base_de_datos/BD_Sistema_Ducky.drawio
    (version SQLite de ducky_bd_sprint1.sql). Las correcciones al diseno
    estan en docs/PRESENTACION.md.

    Uso:
        venv/bin/python init_db.py
            Borra y vuelve a crear syntra.db.
        venv/bin/python init_db.py --si-hace-falta
            Solo la crea si no existe o tiene el esquema anterior.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================

============================================================
Contenido del listado:
    Importaciones
        os, sqlite3, sys
        werkzeug.security.generate_password_hash
        config
    Esquema de la base de datos
        _formatear_lista_sql()
        ESQUEMA, TABLAS
    Datos de demostracion
        TODOS, PERFILES, USUARIOS, EDITORIALES, TEMAS, AUTORES,
        ESTANCIAS, PROVEEDORES, SINOPSIS, LIBROS, FECHA_BAJA_DEMO
    Carga de datos
        formar_nombre_autor()
        crear_tablas()
        insertar_permisos()
        insertar_perfiles()
        insertar_usuarios()
        insertar_catalogos()
        obtener_estante()
        insertar_libros()
    Creacion y revision de la base de datos
        inicializar()
        verificar_esquema_vigente()
    Ejecucion desde la terminal
        python init_db.py [--si-hace-falta]
============================================================
"""

import os
import sqlite3
import sys

from werkzeug.security import generate_password_hash

import config

# ============================================================
# ESQUEMA DE LA BASE DE DATOS
# Arma el SQL de las tablas del Sprint 1 con llaves foraneas y CHECK.
# ============================================================


def _formatear_lista_sql(valores):
    """
    Descripcion:
        Convierte una lista en texto para las restricciones CHECK, por ejemplo
        ['A', 'B'] -> "'A', 'B'".

    Parametros:
        valores (list[str]): valores permitidos.

    Salida:
        str: valores entre comillas separados por coma.
    """
    return ", ".join(f"'{valor}'" for valor in valores)


# Esquema SQLite del Sprint 1 (tablas, llaves foraneas, restricciones e
# indices).
ESQUEMA = f"""
-- Perfiles de usuario (Administrador, Bibliotecario, Profesor, Alumno...).
CREATE TABLE perfiles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          VARCHAR(60)  NOT NULL UNIQUE COLLATE NOCASE,
    descripcion     VARCHAR(255),
    disponible      INTEGER      NOT NULL DEFAULT 1,
    fecha_registro  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Catalogo de permisos del sistema (ej. libros.alta).
CREATE TABLE permisos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo          VARCHAR(60)  NOT NULL UNIQUE,
    descripcion     VARCHAR(150) NOT NULL,
    grupo           VARCHAR(40)  NOT NULL
);

-- Relacion N:M entre perfiles y permisos.
CREATE TABLE perfil_permisos (
    perfil_id       INTEGER NOT NULL
        REFERENCES perfiles(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    permiso_id      INTEGER NOT NULL
        REFERENCES permisos(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    PRIMARY KEY (perfil_id, permiso_id)
);

-- Cuentas de alumnos, profesores y personal.
CREATE TABLE usuarios (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    identificador       VARCHAR(20)  NOT NULL UNIQUE COLLATE NOCASE,
    nombre              VARCHAR(60)  NOT NULL,
    apellido_paterno    VARCHAR(60)  NOT NULL,
    apellido_materno    VARCHAR(60),
    cuenta              VARCHAR(50)  NOT NULL UNIQUE COLLATE NOCASE,
    email               VARCHAR(150) UNIQUE COLLATE NOCASE,
    telefono            VARCHAR(20),
    contrasena          VARCHAR(255) NOT NULL,
    perfil_id           INTEGER
        REFERENCES perfiles(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    estado              VARCHAR(20)  NOT NULL
        DEFAULT '{config.ESTADO_HABILITADA}'
        CHECK (estado IN ({_formatear_lista_sql(config.ESTADOS_CUENTA)})),
    fecha_registro      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion DATETIME
);

-- Editoriales de los libros.
CREATE TABLE editoriales (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          VARCHAR(150) NOT NULL UNIQUE COLLATE NOCASE,
    pais            VARCHAR(60)
);

-- Autores.
CREATE TABLE autores (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          VARCHAR(100) NOT NULL,
    apellidos       VARCHAR(100),
    nacionalidad    VARCHAR(60)
);

-- Temas o categorias del catalogo.
CREATE TABLE temas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          VARCHAR(120) NOT NULL UNIQUE COLLATE NOCASE,
    descripcion     VARCHAR(255)
);

-- Ficha bibliografica de cada titulo.
CREATE TABLE libros (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    clave           VARCHAR(20)  NOT NULL UNIQUE COLLATE NOCASE,
    isbn            VARCHAR(20)  UNIQUE,
    titulo          VARCHAR(255) NOT NULL,
    editorial_id    INTEGER      NOT NULL
        REFERENCES editoriales(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    tema_id         INTEGER      NOT NULL
        REFERENCES temas(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    anio            SMALLINT,
    edicion         VARCHAR(30),
    sinopsis        TEXT,
    tipo_acceso     VARCHAR(20)  NOT NULL DEFAULT '{config.TIPOS_ACCESO[0]}'
        CHECK (tipo_acceso IN ({_formatear_lista_sql(config.TIPOS_ACCESO)})),
    activo          INTEGER      NOT NULL DEFAULT 1,
    fecha_registro  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_baja      DATETIME
);

-- Relacion N:M entre libros y autores. "orden" indica si es primer autor,
-- segundo...
CREATE TABLE libro_autores (
    libro_id        INTEGER NOT NULL
        REFERENCES libros(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    autor_id        INTEGER NOT NULL
        REFERENCES autores(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    orden           INTEGER NOT NULL DEFAULT 1 CHECK (orden > 0),
    PRIMARY KEY (libro_id, autor_id),
    UNIQUE (libro_id, orden)
);

-- Salas de la biblioteca (Sala General, Hemeroteca...).
CREATE TABLE estancias (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          VARCHAR(60) NOT NULL UNIQUE,
    descripcion     VARCHAR(255)
);

-- Estantes dentro de cada estancia.
CREATE TABLE estantes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    estancia_id     INTEGER     NOT NULL
        REFERENCES estancias(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    clave           VARCHAR(20) NOT NULL COLLATE NOCASE,
    UNIQUE (estancia_id, clave)
);

-- Copias fisicas de cada libro, con ubicacion y estado.
-- La ubicacion va completa (estante y posicion) o vacia mientras esta
-- pendiente.
CREATE TABLE ejemplares (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo              VARCHAR(20) NOT NULL UNIQUE,
    libro_id            INTEGER     NOT NULL
        REFERENCES libros(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    estante_id          INTEGER
        REFERENCES estantes(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    posicion            VARCHAR(20),
    estado              VARCHAR(30) NOT NULL
        DEFAULT '{config.ESTADO_DISPONIBLE}'
        CHECK (estado IN ({_formatear_lista_sql(config.ESTADOS_EJEMPLAR)})),
    fecha_alta          DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion DATETIME,
    CHECK ((estante_id IS NULL) = (posicion IS NULL))
);

-- Proveedores de libros.
CREATE TABLE proveedores (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          VARCHAR(150) NOT NULL UNIQUE COLLATE NOCASE,
    rfc             VARCHAR(13)  UNIQUE,
    telefono        VARCHAR(20),
    email           VARCHAR(150)
);

-- Ordenes de compra generadas por el bibliotecario.
CREATE TABLE ordenes_compra (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    folio           VARCHAR(20) NOT NULL UNIQUE,
    proveedor_id    INTEGER     NOT NULL
        REFERENCES proveedores(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    usuario_id      INTEGER     NOT NULL
        REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    fecha_requerida DATE        NOT NULL,
    justificacion   TEXT,
    estado          VARCHAR(20) NOT NULL
        DEFAULT '{config.ESTADO_ORDEN_REGISTRADA}'
        CHECK (estado IN ({_formatear_lista_sql(config.ESTADOS_ORDEN)})),
    fecha_registro  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Renglones (libros y cantidades) de cada orden.
CREATE TABLE orden_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    orden_id        INTEGER NOT NULL
        REFERENCES ordenes_compra(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    libro_id        INTEGER NOT NULL
        REFERENCES libros(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    cantidad        INTEGER NOT NULL CHECK (cantidad > 0),
    UNIQUE (orden_id, libro_id)
);

-- Indices para las busquedas del catalogo.
CREATE INDEX idx_libros_titulo ON libros (titulo);
CREATE INDEX idx_autores_nombre ON autores (apellidos, nombre);
CREATE INDEX idx_usuarios_nombre ON usuarios (apellido_paterno, nombre);
CREATE INDEX idx_ejemplares_libro ON ejemplares (libro_id);
CREATE INDEX idx_ejemplares_estado ON ejemplares (estado);
"""

# Tablas que deben existir; sirve para detectar una syntra.db del esquema
# anterior.
TABLAS = (
    "perfiles",
    "permisos",
    "perfil_permisos",
    "usuarios",
    "editoriales",
    "autores",
    "temas",
    "libros",
    "libro_autores",
    "estancias",
    "estantes",
    "ejemplares",
    "proveedores",
    "ordenes_compra",
    "orden_items",
)

# ============================================================
# DATOS DE DEMOSTRACION
# Perfiles, cuentas, catalogos y libros para probar las historias.
# ============================================================

# El permiso del portal movil es solo para alumnos, por eso el administrador no
# lo tiene.
TODOS = [
    codigo
    for codigo, _, _ in config.PERMISOS
    if codigo != config.PERMISO_MOVIL
]

# (nombre, descripcion, disponible, permisos).
PERFILES = [
    (
        "Administrador",
        "Control total de usuarios, perfiles y catálogo.",
        1,
        TODOS,
    ),
    (
        "Bibliotecario",
        "Gestiona el catálogo, reportes y órdenes de compra.",
        1,
        [
            "sistema.acceder",
            "cuenta.contrasena",
            "catalogo.consultar",
            "libros.alta",
            "libros.editar",
            "libros.baja",
            "reportes.pdf",
            "reportes.imprimir",
            "compras.orden",
        ],
    ),
    (
        "Profesor",
        "Consulta el catálogo y genera listados.",
        1,
        [
            "sistema.acceder",
            "cuenta.contrasena",
            "catalogo.consultar",
            "reportes.pdf",
            "reportes.imprimir",
        ],
    ),
    (
        "Alumno",
        "Consulta el catálogo, ubicación y disponibilidad, también desde el "
        "portal móvil.",
        1,
        [
            "sistema.acceder",
            "cuenta.contrasena",
            "movil.acceder",
            "catalogo.consultar",
        ],
    ),
    (
        "Colaborador",
        "Personal autorizado de apoyo a la biblioteca.",
        1,
        ["sistema.acceder", "cuenta.contrasena", "catalogo.consultar"],
    ),
    # Perfil sin acceso al sistema.
    (
        "Visitante",
        "Registro de visitantes externos. Sin acceso al sistema.",
        1,
        ["catalogo.consultar"],
    ),
    # Perfil que no se puede asignar.
    (
        "Auditoría externa",
        "Perfil temporal suspendido; no disponible para asignar.",
        0,
        ["sistema.acceder", "usuarios.consultar"],
    ),
]

# (identificador, nombre, apellido_paterno, apellido_materno, cuenta, email,
# contrasena, perfil, estado).
USUARIOS = [
    (
        "A00001",
        "Laura",
        "Méndez",
        "Garza",
        "admin",
        "laura.mendez@ducky.edu.mx",
        "Admin123",
        "Administrador",
        "Habilitada",
    ),
    (
        "N10234",
        "Roberto",
        "Treviño",
        "Salinas",
        "biblio",
        "roberto.trevino@ducky.edu.mx",
        "Biblio123",
        "Bibliotecario",
        "Habilitada",
    ),
    (
        "N20456",
        "Ana Lucía",
        "Robles",
        "Cantú",
        "profesor",
        "ana.robles@ducky.edu.mx",
        "Profe123",
        "Profesor",
        "Habilitada",
    ),
    (
        "N20500",
        "Pedro",
        "Martínez",
        "Soto",
        "pmartinez",
        "pedro.martinez@ducky.edu.mx",
        "Profe123",
        "Profesor",
        "Habilitada",
    ),
    (
        "600101",
        "Mariana",
        "López",
        "Hernández",
        "alumno",
        "mariana.lopez@alumnos.ducky.edu.mx",
        "Alumno123",
        "Alumno",
        "Habilitada",
    ),
    (
        "600102",
        "José",
        "López",
        "Martínez",
        "jlopez",
        "jose.lopez@alumnos.ducky.edu.mx",
        "Alumno123",
        "Alumno",
        "Habilitada",
    ),
    (
        "600103",
        "Carlos",
        "Ramírez",
        "Ortiz",
        "deshabilitado",
        "carlos.ramirez@alumnos.ducky.edu.mx",
        "Demo123",
        "Alumno",
        "Deshabilitada",
    ),
    (
        "C30010",
        "Daniela",
        "Fuentes",
        "Leal",
        "dfuentes",
        "daniela.fuentes@ducky.edu.mx",
        "Colab123",
        "Colaborador",
        "Habilitada",
    ),
    (
        "V00001",
        "Sofía",
        "Garza",
        "Villarreal",
        "visitante",
        None,
        "Demo123",
        "Visitante",
        "Habilitada",
    ),
]

# (nombre, pais).
EDITORIALES = [
    ("Sudamericana", "Argentina"),
    ("Fondo de Cultura Económica", "México"),
    ("McGraw-Hill", "Estados Unidos"),
    ("Anaya Multimedia", "España"),
    ("Cengage Learning", "Estados Unidos"),
    ("Crítica", "España"),
    ("Debate", "España"),
    ("Salamandra", "España"),
    ("MIT Press", "Estados Unidos"),
    ("Planeta", "España"),
    ("Pearson", "Reino Unido"),
    ("Trillas", "México"),
    ("Prentice Hall", "Estados Unidos"),
]

TEMAS = [
    "Literatura",
    "Ingeniería de Software",
    "Programación",
    "Matemáticas",
    "Ciencia",
    "Historia",
    "Bases de datos",
    "Administración",
    "Lenguaje",
]

# (nombre, apellidos, nacionalidad). En los libros se usa el nombre completo.
AUTORES = [
    ("Gabriel", "García Márquez", "Colombiana"),
    ("Juan", "Rulfo", "Mexicana"),
    ("Roger S.", "Pressman", "Estadounidense"),
    ("Robert C.", "Martin", "Estadounidense"),
    ("James", "Stewart", "Canadiense"),
    ("Stephen", "Hawking", "Británica"),
    ("Yuval Noah", "Harari", "Israelí"),
    ("Antoine", "de Saint-Exupéry", "Francesa"),
    ("Abraham", "Silberschatz", "Estadounidense"),
    ("Henry F.", "Korth", "Estadounidense"),
    ("S.", "Sudarshan", None),
    ("Thomas H.", "Cormen", "Estadounidense"),
    ("Charles E.", "Leiserson", "Estadounidense"),
    ("Ronald L.", "Rivest", "Estadounidense"),
    ("Clifford", "Stein", "Estadounidense"),
    ("Carlos", "Ruiz Zafón", "Española"),
    ("Gerardo", "Guajardo Cantú", "Mexicana"),
    ("Francis W.", "Sears", "Estadounidense"),
    ("Mark W.", "Zemansky", "Estadounidense"),
    ("Varios autores", None, None),
    ("Erich", "Gamma", "Suiza"),
    ("Richard", "Helm", "Australiana"),
    ("Ralph", "Johnson", "Estadounidense"),
    ("John", "Vlissides", "Estadounidense"),
    ("Brian W.", "Kernighan", "Canadiense"),
    ("Dennis M.", "Ritchie", "Estadounidense"),
]

# (nombre, descripcion).
ESTANCIAS = [
    ("Sala General", "Acervo general de préstamo a domicilio."),
    ("Sala de Lectura", "Consulta en sala y préstamo de fin de semana."),
    ("Hemeroteca", "Revistas, periódicos y publicaciones periódicas."),
    ("Acervo Reservado", "Material de préstamo restringido."),
]

PROVEEDORES = [
    "Librería Universitaria del Norte",
    "Distribuidora Académica Regiomontana",
    "Importadora de Libros Técnicos",
]

# Datos opcionales de algunos libros.
SINOPSIS = {
    "LIB-001": "La historia de siete generaciones de la familia Buendía en "
    "el pueblo de Macondo.",
    "LIB-002": "Juan Preciado llega a Comala a buscar a su padre y encuentra "
    "un pueblo de voces y murmullos.",
    "LIB-003": "Panorama del proceso de software: requisitos, diseño, "
    "pruebas, calidad y gestión de proyectos.",
    "LIB-004": "Prácticas para escribir código legible y fácil de mantener, "
    "con ejemplos y casos de estudio.",
    "LIB-009": "Modelo relacional, SQL, diseño de bases de datos, "
    "transacciones y almacenamiento.",
    "LIB-010": "Diseño y análisis de algoritmos: ordenamiento, estructuras "
    "de datos, grafos y complejidad.",
    "LIB-015": "Catálogo de 23 patrones para resolver problemas comunes de "
    "diseño orientado a objetos.",
    "LIB-016": "Referencia clásica del lenguaje C escrita por sus creadores.",
}

# (clave, titulo, autores, tema, editorial, anio, edicion, tipo_acceso, activo,
# ejemplares)
# ejemplar = (estancia, estante, posicion, estado); None en los tres =
# ubicacion pendiente.
LIBROS = [
    (
        "LIB-001",
        "Cien años de soledad",
        ["Gabriel García Márquez"],
        "Literatura",
        "Sudamericana",
        1967,
        None,
        "Circulante",
        1,
        [
            ("Sala General", "A-1", "3", "Disponible"),
            ("Sala General", "A-1", "4", "Prestado"),
            ("Sala de Lectura", "L-2", "1", "Disponible"),
        ],
    ),
    (
        "LIB-002",
        "Pedro Páramo",
        ["Juan Rulfo"],
        "Literatura",
        "Fondo de Cultura Económica",
        1955,
        None,
        "Circulante",
        1,
        [
            ("Sala General", "A-2", "7", "Disponible"),
            (None, None, None, "Disponible"),
        ],
    ),
    (
        "LIB-003",
        "Ingeniería de software: un enfoque práctico",
        ["Roger S. Pressman"],
        "Ingeniería de Software",
        "McGraw-Hill",
        2010,
        "7.ª ed.",
        "Circulante",
        1,
        [
            ("Sala General", "C-4", "2", "Prestado"),
            ("Acervo Reservado", "R-1", "5", "Reservado"),
            ("Sala General", "C-4", "3", "Disponible"),
        ],
    ),
    (
        "LIB-004",
        "Código limpio",
        ["Robert C. Martin"],
        "Programación",
        "Anaya Multimedia",
        2012,
        None,
        "Circulante",
        1,
        [
            ("Sala General", "C-5", "1", "Disponible"),
            ("Sala General", "C-5", "2", "Dañado"),
        ],
    ),
    (
        "LIB-005",
        "Cálculo de una variable",
        ["James Stewart"],
        "Matemáticas",
        "Cengage Learning",
        2012,
        "7.ª ed.",
        "Circulante",
        1,
        [
            ("Sala General", "M-1", "4", "Disponible"),
            ("Sala General", "M-1", "5", "Disponible"),
        ],
    ),
    (
        "LIB-006",
        "Breve historia del tiempo",
        ["Stephen Hawking"],
        "Ciencia",
        "Crítica",
        1988,
        None,
        "Circulante",
        1,
        [
            ("Sala de Lectura", "L-6", "2", "Perdido"),
            ("Sala de Lectura", "L-6", "3", "Fuera de servicio"),
        ],
    ),
    (
        "LIB-007",
        "Sapiens: de animales a dioses",
        ["Yuval Noah Harari"],
        "Historia",
        "Debate",
        2014,
        None,
        "Circulante",
        1,
        [
            ("Sala General", "H-2", "1", "Disponible"),
            ("Hemeroteca", "HM-1", "8", "Disponible"),
        ],
    ),
    # Libro sin ejemplares.
    (
        "LIB-008",
        "El principito",
        ["Antoine de Saint-Exupéry"],
        "Literatura",
        "Salamandra",
        1943,
        None,
        "Circulante",
        1,
        [],
    ),
    (
        "LIB-009",
        "Fundamentos de bases de datos",
        ["Abraham Silberschatz", "Henry F. Korth", "S. Sudarshan"],
        "Bases de datos",
        "McGraw-Hill",
        2014,
        "6.ª ed.",
        "Circulante",
        1,
        [
            ("Sala General", "C-6", "1", "Disponible"),
            ("Sala General", "C-6", "2", "Disponible"),
        ],
    ),
    (
        "LIB-010",
        "Introducción a los algoritmos",
        [
            "Thomas H. Cormen",
            "Charles E. Leiserson",
            "Ronald L. Rivest",
            "Clifford Stein",
        ],
        "Programación",
        "MIT Press",
        2009,
        "3.ª ed.",
        "Circulante",
        1,
        [
            ("Sala General", "C-5", "6", "Prestado"),
            ("Sala de Lectura", "L-3", "2", "Disponible"),
        ],
    ),
    (
        "LIB-011",
        "La sombra del viento",
        ["Carlos Ruiz Zafón"],
        "Literatura",
        "Planeta",
        2001,
        None,
        "Circulante",
        1,
        [
            ("Sala General", "B-2", "5", "Disponible"),
        ],
    ),
    (
        "LIB-012",
        "Contabilidad financiera",
        ["Gerardo Guajardo Cantú"],
        "Administración",
        "McGraw-Hill",
        2014,
        None,
        "Reservado",
        1,
        [
            ("Acervo Reservado", "R-2", "1", "Reservado"),
        ],
    ),
    (
        "LIB-013",
        "Física universitaria",
        ["Francis W. Sears", "Mark W. Zemansky"],
        "Ciencia",
        "Pearson",
        2013,
        "13.ª ed.",
        "Circulante",
        1,
        [
            ("Sala General", "F-1", "2", "Disponible"),
            ("Sala General", "F-1", "3", "Disponible"),
        ],
    ),
    # Libro dado de baja.
    (
        "LIB-014",
        "Manual de redacción académica (1.ª ed.)",
        ["Varios autores"],
        "Lenguaje",
        "Trillas",
        1998,
        "1.ª ed.",
        "Circulante",
        0,
        [
            ("Acervo Reservado", "R-9", "1", "Fuera de servicio"),
        ],
    ),
    (
        "LIB-015",
        "Patrones de diseño",
        ["Erich Gamma", "Richard Helm", "Ralph Johnson", "John Vlissides"],
        "Ingeniería de Software",
        "Pearson",
        2003,
        None,
        "Circulante",
        1,
        [
            ("Sala General", "C-7", "1", "Disponible"),
            ("Sala de Lectura", "L-3", "4", "Prestado"),
        ],
    ),
    (
        "LIB-016",
        "El lenguaje de programación C",
        ["Brian W. Kernighan", "Dennis M. Ritchie"],
        "Programación",
        "Prentice Hall",
        1991,
        "2.ª ed.",
        "Circulante",
        1,
        [
            ("Sala General", "C-7", "2", "Disponible"),
        ],
    ),
]

# Fecha de baja del libro de prueba que esta dado de baja (LIB-014).
FECHA_BAJA_DEMO = "2026-09-15 10:00:00"


# ============================================================
# CARGA DE DATOS
# Insertan los datos de demostracion en orden de dependencias.
# ============================================================


def formar_nombre_autor(nombre, apellidos):
    """
    Descripcion:
        Forma el nombre completo del autor como se muestra en pantalla.

    Parametros:
        nombre (str): nombre del autor.
        apellidos (str o None): apellidos del autor.

    Salida:
        str: nombre completo.
    """
    return f"{nombre} {apellidos}" if apellidos else nombre


def crear_tablas(cursor):
    """
    Descripcion:
        Crea todas las tablas e indices del esquema.

    Parametros:
        cursor (sqlite3.Cursor): cursor de la conexion de init_db.

    Salida:
        Ninguna.

    Excepciones:
        sqlite3.Error si alguna tabla ya existe.
    """
    cursor.executescript(ESQUEMA)


def insertar_permisos(cursor):
    """
    Descripcion:
        Guarda en la tabla permisos el catalogo de permisos de config.py.

    Parametros:
        cursor (sqlite3.Cursor): cursor de la conexion de init_db.

    Salida:
        dict[str, int]: id de cada codigo de permiso.
    """
    ids = {}
    for codigo, descripcion, grupo in config.PERMISOS:
        cursor.execute(
            "INSERT INTO permisos (codigo, descripcion, grupo) VALUES (?, ?, "
            "?)",
            (codigo, descripcion, grupo),
        )
        ids[codigo] = cursor.lastrowid
    return ids


def insertar_perfiles(cursor, permisos_ids):
    """
    Descripcion:
        Guarda los perfiles de demostracion con sus permisos.

    Parametros:
        cursor (sqlite3.Cursor): cursor de la conexion de init_db.
        permisos_ids (dict[str, int]): id de cada codigo de permiso.

    Salida:
        dict[str, int]: id de cada perfil por nombre.
    """
    ids = {}
    for nombre, descripcion, disponible, permisos in PERFILES:
        # Insertamos el perfil.
        cursor.execute(
            "INSERT INTO perfiles (nombre, descripcion, disponible) VALUES "
            "(?, ?, ?)",
            (nombre, descripcion, disponible),
        )
        ids[nombre] = cursor.lastrowid
        # Relacionamos sus permisos.
        for codigo in permisos:
            cursor.execute(
                "INSERT INTO perfil_permisos (perfil_id, permiso_id) VALUES "
                "(?, ?)",
                (ids[nombre], permisos_ids[codigo]),
            )
    return ids


def insertar_usuarios(cursor, perfiles_ids):
    """
    Descripcion:
        Guarda las cuentas de demostracion con su contrasena cifrada.

    Parametros:
        cursor (sqlite3.Cursor): cursor de la conexion de init_db.
        perfiles_ids (dict[str, int]): id de cada perfil por nombre.

    Salida:
        Ninguna.
    """
    for (
        identificador,
        nombre,
        paterno,
        materno,
        cuenta,
        email,
        contrasena,
        perfil,
        estado,
    ) in USUARIOS:
        cursor.execute(
            "INSERT INTO usuarios (identificador, nombre, apellido_paterno, "
            "apellido_materno, cuenta, "
            "email, contrasena, perfil_id, estado) VALUES (?, ?, ?, ?, ?, ?, "
            "?, ?, ?)",
            (
                identificador,
                nombre,
                paterno,
                materno,
                cuenta,
                email,
                generate_password_hash(contrasena, method="pbkdf2:sha256"),
                perfiles_ids[perfil],
                estado,
            ),
        )


def insertar_catalogos(cursor):
    """
    Descripcion:
        Guarda editoriales, temas, autores, estancias y proveedores de
        demostracion.

    Parametros:
        cursor (sqlite3.Cursor): cursor de la conexion de init_db.

    Salida:
        dict: ids por nombre de editoriales, temas, autores y estancias, para
        insertar libros y ejemplares.
    """
    ids = {"editoriales": {}, "temas": {}, "autores": {}, "estancias": {}}

    # Editoriales y temas.
    for nombre, pais in EDITORIALES:
        cursor.execute(
            "INSERT INTO editoriales (nombre, pais) VALUES (?, ?)",
            (nombre, pais),
        )
        ids["editoriales"][nombre] = cursor.lastrowid
    for nombre in TEMAS:
        cursor.execute("INSERT INTO temas (nombre) VALUES (?)", (nombre,))
        ids["temas"][nombre] = cursor.lastrowid

    # Autores (la llave es su nombre completo).
    for nombre, apellidos, nacionalidad in AUTORES:
        cursor.execute(
            "INSERT INTO autores (nombre, apellidos, nacionalidad) VALUES "
            "(?, ?, ?)",
            (nombre, apellidos, nacionalidad),
        )
        ids["autores"][formar_nombre_autor(nombre, apellidos)] = (
            cursor.lastrowid
        )

    # Estancias (salas) y proveedores.
    for nombre, descripcion in ESTANCIAS:
        cursor.execute(
            "INSERT INTO estancias (nombre, descripcion) VALUES (?, ?)",
            (nombre, descripcion),
        )
        ids["estancias"][nombre] = cursor.lastrowid
    for nombre in PROVEEDORES:
        cursor.execute(
            "INSERT INTO proveedores (nombre) VALUES (?)", (nombre,)
        )
    return ids


def obtener_estante(cursor, estancia_id, clave, estantes):
    """
    Descripcion:
        Obtiene el id del estante; lo crea la primera vez que aparece en los
        datos de demostracion.

    Parametros:
        cursor (sqlite3.Cursor): cursor de la conexion de init_db.
        estancia_id (int): id de la estancia.
        clave (str): clave del estante.
        estantes (dict): estantes ya creados (se modifica).

    Salida:
        int: id del estante.
    """
    llave = (estancia_id, clave)
    if llave not in estantes:
        cursor.execute(
            "INSERT INTO estantes (estancia_id, clave) VALUES (?, ?)", llave
        )
        estantes[llave] = cursor.lastrowid
    return estantes[llave]


def insertar_libros(cursor, ids):
    """
    Descripcion:
        Guarda los libros de demostracion con sus autores en orden y sus
        ejemplares con codigo consecutivo. Un ejemplar sin estancia queda con
        la ubicacion pendiente.

    Parametros:
        cursor (sqlite3.Cursor): cursor de la conexion de init_db.
        ids (dict): ids de catalogos de insertar_catalogos().

    Salida:
        Ninguna.
    """
    consecutivo = 1
    estantes = {}
    for (
        clave,
        titulo,
        autores,
        tema,
        editorial,
        anio,
        edicion,
        tipo_acceso,
        activo,
        ejemplares,
    ) in LIBROS:
        # Insertamos el libro (los inactivos llevan fecha de baja).
        cursor.execute(
            "INSERT INTO libros (clave, titulo, editorial_id, tema_id, anio, "
            "edicion, sinopsis, "
            "tipo_acceso, activo, fecha_baja) VALUES (?, ?, ?, ?, ?, ?, ?, "
            "?, ?, ?)",
            (
                clave,
                titulo,
                ids["editoriales"][editorial],
                ids["temas"][tema],
                anio,
                edicion,
                SINOPSIS.get(clave),
                tipo_acceso,
                activo,
                None if activo else FECHA_BAJA_DEMO,
            ),
        )
        libro_id = cursor.lastrowid

        # Relacionamos sus autores en el orden capturado.
        for orden, autor in enumerate(autores, start=1):
            cursor.execute(
                "INSERT INTO libro_autores (libro_id, autor_id, orden) "
                "VALUES (?, ?, ?)",
                (libro_id, ids["autores"][autor], orden),
            )

        # Insertamos sus ejemplares con codigo consecutivo (sin estancia =
        # ubicacion pendiente).
        for estancia, estante, posicion, estado in ejemplares:
            estante_id = (
                obtener_estante(
                    cursor, ids["estancias"][estancia], estante, estantes
                )
                if estancia
                else None
            )
            cursor.execute(
                "INSERT INTO ejemplares (codigo, libro_id, estante_id, "
                "posicion, estado) VALUES (?, ?, ?, ?, ?)",
                (
                    f"{config.PREFIJO_EJEMPLAR}{consecutivo:04d}",
                    libro_id,
                    estante_id,
                    posicion,
                    estado,
                ),
            )
            consecutivo += 1


# ============================================================
# CREACION Y REVISION DE LA BASE DE DATOS
# Crean syntra.db desde cero y revisan si su esquema esta al dia.
# ============================================================


def inicializar(ruta=config.RUTA_BASE_DATOS, con_libros=True):
    """
    Descripcion:
        Borra la base de datos y la vuelve a crear con el esquema y los datos
        de demostracion, en orden de dependencias.

    Parametros:
        ruta (str): ruta del archivo SQLite.
        con_libros (bool): False para crearla sin libros ni ejemplares.

    Salida:
        Ninguna.

    Excepciones:
        OSError si no se puede borrar o escribir el archivo.
    """
    # Borramos la base anterior si existe.
    if os.path.exists(ruta):
        os.remove(ruta)

    # Abrimos la conexion con llaves foraneas activas y creamos las tablas.
    conexion = sqlite3.connect(ruta)
    conexion.execute("PRAGMA foreign_keys = ON")
    cursor = conexion.cursor()
    crear_tablas(cursor)

    # Insertamos los datos de prueba en orden de dependencias.
    permisos_ids = insertar_permisos(cursor)
    perfiles_ids = insertar_perfiles(cursor, permisos_ids)
    insertar_usuarios(cursor, perfiles_ids)
    ids = insertar_catalogos(cursor)
    if con_libros:
        insertar_libros(cursor, ids)

    # Guardamos los cambios y cerramos.
    conexion.commit()
    conexion.close()


def verificar_esquema_vigente(ruta=config.RUTA_BASE_DATOS):
    """
    Descripcion:
        Revisa que la base de datos exista y tenga todas las tablas del esquema
        actual.

    Parametros:
        ruta (str): ruta del archivo SQLite.

    Salida:
        bool: True si el esquema esta al dia.
    """
    if not os.path.exists(ruta):
        return False

    # Leemos las tablas que existen y revisamos que esten todas.
    conexion = sqlite3.connect(ruta)
    filas = conexion.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall()
    conexion.close()
    existentes = {fila[0] for fila in filas}
    return all(tabla in existentes for tabla in TABLAS)


# ============================================================
# EJECUCION DESDE LA TERMINAL
# Crea la base de datos y muestra las cuentas de demostracion.
# ============================================================

if __name__ == "__main__":
    # Con --si-hace-falta no se toca una base de datos que ya esta al dia.
    if "--si-hace-falta" in sys.argv and verificar_esquema_vigente():
        print("La base de datos ya está al día:", config.RUTA_BASE_DATOS)
        sys.exit(0)

    # Creamos la base de datos y mostramos las cuentas de demostracion.
    inicializar()
    print("Base de datos creada en:", config.RUTA_BASE_DATOS)
    print("Cuentas de demostración:")
    for (
        _,
        nombre,
        paterno,
        _,
        cuenta,
        _,
        contrasena,
        perfil,
        estado,
    ) in USUARIOS:
        print(
            f"  {cuenta:<14} {contrasena:<10} {perfil:<14} {estado:<14} "
            f"{nombre} {paterno}"
        )
