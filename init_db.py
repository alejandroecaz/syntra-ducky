import os
import sqlite3

from werkzeug.security import generate_password_hash

import config


ESQUEMA = """
CREATE TABLE perfiles (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre        VARCHAR(60)  NOT NULL UNIQUE COLLATE NOCASE,
    descripcion   VARCHAR(255),
    disponible    INTEGER      NOT NULL DEFAULT 1,
    fecha_registro DATETIME    DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE perfil_permisos (
    perfil_id     INTEGER     NOT NULL REFERENCES perfiles(id),
    permiso       VARCHAR(60) NOT NULL,
    PRIMARY KEY (perfil_id, permiso)
);

CREATE TABLE usuarios (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    identificador  VARCHAR(20)  NOT NULL UNIQUE COLLATE NOCASE,
    nombre         VARCHAR(120) NOT NULL,
    cuenta         VARCHAR(50)  NOT NULL UNIQUE COLLATE NOCASE,
    contrasena     VARCHAR(255) NOT NULL,
    perfil_id      INTEGER      REFERENCES perfiles(id),
    estado         VARCHAR(20)  NOT NULL DEFAULT 'Habilitada',
    fecha_registro DATETIME     DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion DATETIME
);

CREATE TABLE libros (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    clave          VARCHAR(20)  NOT NULL UNIQUE COLLATE NOCASE,
    titulo         VARCHAR(255) NOT NULL,
    autor          VARCHAR(255) NOT NULL,
    tema           VARCHAR(120) NOT NULL,
    editorial      VARCHAR(150) NOT NULL,
    anio           INTEGER,
    activo         INTEGER      NOT NULL DEFAULT 1,
    fecha_registro DATETIME     DEFAULT CURRENT_TIMESTAMP,
    fecha_baja     DATETIME
);

CREATE TABLE ejemplares (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo         VARCHAR(20)  NOT NULL UNIQUE,
    libro_id       INTEGER      NOT NULL REFERENCES libros(id),
    estancia       VARCHAR(60),
    estante        VARCHAR(20),
    posicion       VARCHAR(20),
    estado         VARCHAR(30)  NOT NULL DEFAULT 'Disponible',
    fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ordenes_compra (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    folio           VARCHAR(20)  NOT NULL UNIQUE,
    proveedor       VARCHAR(150) NOT NULL,
    fecha_requerida DATE         NOT NULL,
    justificacion   TEXT,
    usuario_id      INTEGER      REFERENCES usuarios(id),
    estado          VARCHAR(20)  NOT NULL DEFAULT 'Registrada',
    fecha_registro  DATETIME     DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orden_items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    orden_id   INTEGER NOT NULL REFERENCES ordenes_compra(id),
    libro_id   INTEGER NOT NULL REFERENCES libros(id),
    cantidad   INTEGER NOT NULL
);

CREATE INDEX idx_libros_titulo ON libros(titulo);
CREATE INDEX idx_libros_autor ON libros(autor);
CREATE INDEX idx_usuarios_nombre ON usuarios(nombre);
"""

TODOS = [codigo for codigo, _, _ in config.PERMISOS]

# (nombre, descripcion, disponible, permisos)
PERFILES = [
    ("Administrador", "Control total de usuarios, perfiles y catálogo.", 1, TODOS),
    (
        "Bibliotecario",
        "Gestiona el catálogo, reportes y órdenes de compra.",
        1,
        [
            "sistema.acceder", "cuenta.contrasena", "catalogo.consultar",
            "libros.alta", "libros.editar", "libros.baja",
            "reportes.pdf", "reportes.imprimir", "compras.orden",
        ],
    ),
    (
        "Profesor",
        "Consulta el catálogo y genera listados.",
        1,
        ["sistema.acceder", "cuenta.contrasena", "catalogo.consultar", "reportes.pdf", "reportes.imprimir"],
    ),
    (
        "Alumno",
        "Consulta el catálogo, ubicación y disponibilidad.",
        1,
        ["sistema.acceder", "cuenta.contrasena", "catalogo.consultar"],
    ),
    (
        "Colaborador",
        "Personal autorizado de apoyo a la biblioteca.",
        1,
        ["sistema.acceder", "cuenta.contrasena", "catalogo.consultar"],
    ),
    # Perfil sin acceso al sistema
    ("Visitante", "Registro de visitantes externos. Sin acceso al sistema.", 1, ["catalogo.consultar"]),
    # Perfil que no se puede asignar
    ("Auditoría externa", "Perfil temporal suspendido; no disponible para asignar.", 0,
     ["sistema.acceder", "usuarios.consultar"]),
]

# (identificador, nombre, cuenta, contrasena, perfil, estado)
USUARIOS = [
    ("A00001", "Laura Méndez Garza", "admin", "Admin123", "Administrador", "Habilitada"),
    ("N10234", "Roberto Treviño Salinas", "biblio", "Biblio123", "Bibliotecario", "Habilitada"),
    ("N20456", "Ana Lucía Robles Cantú", "profesor", "Profe123", "Profesor", "Habilitada"),
    ("N20500", "Pedro Martínez Soto", "pmartinez", "Profe123", "Profesor", "Habilitada"),
    ("600101", "Mariana López Hernández", "alumno", "Alumno123", "Alumno", "Habilitada"),
    ("600102", "José López Martínez", "jlopez", "Alumno123", "Alumno", "Habilitada"),
    ("600103", "Carlos Ramírez Ortiz", "deshabilitado", "Demo123", "Alumno", "Deshabilitada"),
    ("C30010", "Daniela Fuentes Leal", "dfuentes", "Colab123", "Colaborador", "Habilitada"),
    ("V00001", "Sofía Garza Villarreal", "visitante", "Demo123", "Visitante", "Habilitada"),
]

# (clave, titulo, autor, tema, editorial, anio, activo, ejemplares)
# ejemplar = (estancia, estante, posicion, estado)
LIBROS = [
    ("LIB-001", "Cien años de soledad", "Gabriel García Márquez", "Literatura", "Sudamericana", 1967, 1, [
        ("Sala General", "A-1", "3", "Disponible"),
        ("Sala General", "A-1", "4", "Prestado"),
        ("Sala de Lectura", "L-2", "1", "Disponible"),
    ]),
    ("LIB-002", "Pedro Páramo", "Juan Rulfo", "Literatura", "Fondo de Cultura Económica", 1955, 1, [
        ("Sala General", "A-2", "7", "Disponible"),
        (None, None, None, "Disponible"),
    ]),
    ("LIB-003", "Ingeniería de software: un enfoque práctico", "Roger S. Pressman", "Ingeniería de Software",
     "McGraw-Hill", 2010, 1, [
        ("Sala General", "C-4", "2", "Prestado"),
        ("Acervo Reservado", "R-1", "5", "Reservado"),
        ("Sala General", "C-4", "3", "Disponible"),
    ]),
    ("LIB-004", "Código limpio", "Robert C. Martin", "Programación", "Anaya Multimedia", 2012, 1, [
        ("Sala General", "C-5", "1", "Disponible"),
        ("Sala General", "C-5", "2", "Dañado"),
    ]),
    ("LIB-005", "Cálculo de una variable", "James Stewart", "Matemáticas", "Cengage Learning", 2012, 1, [
        ("Sala General", "M-1", "4", "Disponible"),
        ("Sala General", "M-1", "5", "Disponible"),
    ]),
    ("LIB-006", "Breve historia del tiempo", "Stephen Hawking", "Ciencia", "Crítica", 1988, 1, [
        ("Sala de Lectura", "L-6", "2", "Perdido"),
        ("Sala de Lectura", "L-6", "3", "Fuera de servicio"),
    ]),
    ("LIB-007", "Sapiens: de animales a dioses", "Yuval Noah Harari", "Historia", "Debate", 2014, 1, [
        ("Sala General", "H-2", "1", "Disponible"),
        ("Hemeroteca", "HM-1", "8", "Disponible"),
    ]),
    ("LIB-008", "El principito", "Antoine de Saint-Exupéry", "Literatura", "Salamandra", 1943, 1, []),
    ("LIB-009", "Fundamentos de bases de datos", "Abraham Silberschatz", "Bases de datos", "McGraw-Hill", 2014, 1, [
        ("Sala General", "C-6", "1", "Disponible"),
        ("Sala General", "C-6", "2", "Disponible"),
    ]),
    ("LIB-010", "Introducción a los algoritmos", "Thomas H. Cormen", "Programación", "MIT Press", 2009, 1, [
        ("Sala General", "C-5", "6", "Prestado"),
        ("Sala de Lectura", "L-3", "2", "Disponible"),
    ]),
    ("LIB-011", "La sombra del viento", "Carlos Ruiz Zafón", "Literatura", "Planeta", 2001, 1, [
        ("Sala General", "B-2", "5", "Disponible"),
    ]),
    ("LIB-012", "Contabilidad financiera", "Gerardo Guajardo Cantú", "Administración", "McGraw-Hill", 2014, 1, [
        ("Acervo Reservado", "R-2", "1", "Reservado"),
    ]),
    ("LIB-013", "Física universitaria", "Sears y Zemansky", "Ciencia", "Pearson", 2013, 1, [
        ("Sala General", "F-1", "2", "Disponible"),
        ("Sala General", "F-1", "3", "Disponible"),
    ]),
    # Libro dado de baja
    ("LIB-014", "Manual de redacción académica (1.ª ed.)", "Varios autores", "Lenguaje", "Trillas", 1998, 0, [
        ("Acervo Reservado", "R-9", "1", "Fuera de servicio"),
    ]),
]


def crear_tablas(cursor):
    cursor.executescript(ESQUEMA)


def insertar_perfiles(cursor):
    ids = {}
    for nombre, descripcion, disponible, permisos in PERFILES:
        cursor.execute(
            "INSERT INTO perfiles (nombre, descripcion, disponible) VALUES (?, ?, ?)",
            (nombre, descripcion, disponible),
        )
        ids[nombre] = cursor.lastrowid
        for permiso in permisos:
            cursor.execute(
                "INSERT INTO perfil_permisos (perfil_id, permiso) VALUES (?, ?)",
                (ids[nombre], permiso),
            )
    return ids


def insertar_usuarios(cursor, perfiles_ids):
    for identificador, nombre, cuenta, contrasena, perfil, estado in USUARIOS:
        cursor.execute(
            "INSERT INTO usuarios (identificador, nombre, cuenta, contrasena, perfil_id, estado) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                identificador,
                nombre,
                cuenta,
                generate_password_hash(contrasena, method="pbkdf2:sha256"),
                perfiles_ids[perfil],
                estado,
            ),
        )


def insertar_libros(cursor):
    consecutivo = 1
    for clave, titulo, autor, tema, editorial, anio, activo, ejemplares in LIBROS:
        cursor.execute(
            "INSERT INTO libros (clave, titulo, autor, tema, editorial, anio, activo, fecha_baja) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (clave, titulo, autor, tema, editorial, anio, activo, None if activo else "2026-09-15 10:00:00"),
        )
        libro_id = cursor.lastrowid
        for estancia, estante, posicion, estado in ejemplares:
            cursor.execute(
                "INSERT INTO ejemplares (codigo, libro_id, estancia, estante, posicion, estado) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (f"EJ-{consecutivo:04d}", libro_id, estancia, estante, posicion, estado),
            )
            consecutivo += 1


def inicializar(ruta=config.DATABASE_PATH, con_libros=True):
    # Borra la base de datos y la vuelve a crear con datos de prueba
    if os.path.exists(ruta):
        os.remove(ruta)

    conexion = sqlite3.connect(ruta)
    cursor = conexion.cursor()
    crear_tablas(cursor)
    perfiles_ids = insertar_perfiles(cursor)
    insertar_usuarios(cursor, perfiles_ids)
    if con_libros:
        insertar_libros(cursor)
    conexion.commit()
    conexion.close()


if __name__ == "__main__":
    inicializar()
    print("Base de datos creada en:", config.DATABASE_PATH)
    print("Cuentas de demostracion:")
    for _, nombre, cuenta, contrasena, perfil, estado in USUARIOS:
        print(f"  {cuenta:<14} {contrasena:<10} {perfil:<14} {estado}")
