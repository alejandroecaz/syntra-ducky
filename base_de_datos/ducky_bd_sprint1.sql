-- ============================================================
-- Sistema Ducky de Gestión Bibliotecaria - Syntra Technologies (Equipo 1)
-- Base de datos PRIMERA ENTREGA (Sprint 1) - MySQL 8
-- ============================================================
DROP DATABASE IF EXISTS ducky_biblioteca_sprint1;
CREATE DATABASE ducky_biblioteca_sprint1 CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci;
USE ducky_biblioteca_sprint1;

-- Perfiles de usuario (Administrador, Bibliotecario, Profesor, Alumno...)
CREATE TABLE perfiles (
    id                     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nombre                 VARCHAR(60) NOT NULL UNIQUE,
    descripcion            VARCHAR(255),
    disponible             BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_registro         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_perfiles PRIMARY KEY (id)
) ENGINE=InnoDB;

-- Catálogo de permisos del sistema (ej. libros.alta)
CREATE TABLE permisos (
    id                     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    codigo                 VARCHAR(60) NOT NULL UNIQUE,
    descripcion            VARCHAR(150) NOT NULL,
    grupo                  VARCHAR(40) NOT NULL,
    CONSTRAINT pk_permisos PRIMARY KEY (id)
) ENGINE=InnoDB;

-- Relación N:M entre perfiles y permisos
CREATE TABLE perfil_permisos (
    perfil_id              INT UNSIGNED NOT NULL,
    permiso_id             INT UNSIGNED NOT NULL,
    CONSTRAINT pk_perfil_permisos PRIMARY KEY (perfil_id, permiso_id),
    CONSTRAINT fk_perfil_permisos_perfil FOREIGN KEY (perfil_id) REFERENCES perfiles(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_perfil_permisos_permiso FOREIGN KEY (permiso_id) REFERENCES permisos(id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

-- Cuentas de alumnos, profesores y personal
CREATE TABLE usuarios (
    id                     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    identificador          VARCHAR(20) NOT NULL UNIQUE,
    nombre                 VARCHAR(60) NOT NULL,
    apellido_paterno       VARCHAR(60) NOT NULL,
    apellido_materno       VARCHAR(60),
    cuenta                 VARCHAR(50) NOT NULL UNIQUE,
    email                  VARCHAR(150) UNIQUE,
    telefono               VARCHAR(20),
    contrasena             VARCHAR(255) NOT NULL,
    perfil_id              INT UNSIGNED,
    estado                 ENUM('Habilitada','Deshabilitada') NOT NULL DEFAULT 'Habilitada',
    fecha_registro         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion    DATETIME,
    CONSTRAINT pk_usuarios PRIMARY KEY (id),
    CONSTRAINT fk_usuarios_perfil FOREIGN KEY (perfil_id) REFERENCES perfiles(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Editoriales de los libros
CREATE TABLE editoriales (
    id                     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nombre                 VARCHAR(150) NOT NULL UNIQUE,
    pais                   VARCHAR(60),
    CONSTRAINT pk_editoriales PRIMARY KEY (id)
) ENGINE=InnoDB;

-- Autores
CREATE TABLE autores (
    id                     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nombre                 VARCHAR(100) NOT NULL,
    apellidos              VARCHAR(100),
    nacionalidad           VARCHAR(60),
    CONSTRAINT pk_autores PRIMARY KEY (id)
) ENGINE=InnoDB;

-- Temas o categorías del catálogo
CREATE TABLE temas (
    id                     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nombre                 VARCHAR(120) NOT NULL UNIQUE,
    descripcion            VARCHAR(255),
    CONSTRAINT pk_temas PRIMARY KEY (id)
) ENGINE=InnoDB;

-- Ficha bibliográfica de cada título
CREATE TABLE libros (
    id                     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    clave                  VARCHAR(20) NOT NULL UNIQUE,
    isbn                   VARCHAR(20) UNIQUE,
    titulo                 VARCHAR(255) NOT NULL,
    editorial_id           INT UNSIGNED NOT NULL,
    tema_id                INT UNSIGNED NOT NULL,
    anio                   SMALLINT,
    edicion                VARCHAR(30),
    sinopsis               TEXT,
    activo                 BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_registro         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_baja             DATETIME,
    CONSTRAINT pk_libros PRIMARY KEY (id),
    CONSTRAINT fk_libros_editorial FOREIGN KEY (editorial_id) REFERENCES editoriales(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_libros_tema FOREIGN KEY (tema_id) REFERENCES temas(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Relación N:M entre libros y autores
CREATE TABLE libro_autores (
    libro_id               INT UNSIGNED NOT NULL,
    autor_id               INT UNSIGNED NOT NULL,
    orden                  TINYINT UNSIGNED NOT NULL DEFAULT 1,
    CONSTRAINT pk_libro_autores PRIMARY KEY (libro_id, autor_id),
    CONSTRAINT fk_libro_autores_libro FOREIGN KEY (libro_id) REFERENCES libros(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_libro_autores_autor FOREIGN KEY (autor_id) REFERENCES autores(id)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB;

-- Salas de la biblioteca (Sala General, Hemeroteca...)
CREATE TABLE estancias (
    id                     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nombre                 VARCHAR(60) NOT NULL UNIQUE,
    descripcion            VARCHAR(255),
    CONSTRAINT pk_estancias PRIMARY KEY (id)
) ENGINE=InnoDB;

-- Estantes dentro de cada estancia
CREATE TABLE estantes (
    id                     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    estancia_id            INT UNSIGNED NOT NULL,
    clave                  VARCHAR(20) NOT NULL,
    CONSTRAINT pk_estantes PRIMARY KEY (id),
    CONSTRAINT uq_estantes_estancia_id_clave UNIQUE (estancia_id, clave),
    CONSTRAINT fk_estantes_estancia FOREIGN KEY (estancia_id) REFERENCES estancias(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Copias físicas de cada libro, con ubicación y estado
CREATE TABLE ejemplares (
    id                     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    codigo                 VARCHAR(20) NOT NULL UNIQUE,
    libro_id               INT UNSIGNED NOT NULL,
    estante_id             INT UNSIGNED,
    posicion               VARCHAR(20),
    estado                 ENUM('Disponible','Prestado','Reservado','Perdido','Dañado','Fuera de servicio') NOT NULL DEFAULT 'Disponible',
    fecha_alta             DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion    DATETIME,
    CONSTRAINT pk_ejemplares PRIMARY KEY (id),
    CONSTRAINT fk_ejemplares_libro FOREIGN KEY (libro_id) REFERENCES libros(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_ejemplares_estante FOREIGN KEY (estante_id) REFERENCES estantes(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Proveedores de libros
CREATE TABLE proveedores (
    id                     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nombre                 VARCHAR(150) NOT NULL,
    rfc                    VARCHAR(13) UNIQUE,
    telefono               VARCHAR(20),
    email                  VARCHAR(150),
    CONSTRAINT pk_proveedores PRIMARY KEY (id)
) ENGINE=InnoDB;

-- Órdenes de compra generadas por el bibliotecario
CREATE TABLE ordenes_compra (
    id                     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    folio                  VARCHAR(20) NOT NULL UNIQUE,
    proveedor_id           INT UNSIGNED NOT NULL,
    usuario_id             INT UNSIGNED NOT NULL,
    fecha_requerida        DATE NOT NULL,
    justificacion          TEXT,
    estado                 ENUM('Registrada','Cancelada') NOT NULL DEFAULT 'Registrada',
    fecha_registro         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_ordenes_compra PRIMARY KEY (id),
    CONSTRAINT fk_ordenes_compra_proveedor FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_ordenes_compra_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Renglones (libros y cantidades) de cada orden
CREATE TABLE orden_items (
    id                     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    orden_id               INT UNSIGNED NOT NULL,
    libro_id               INT UNSIGNED NOT NULL,
    cantidad               SMALLINT UNSIGNED NOT NULL,
    CONSTRAINT pk_orden_items PRIMARY KEY (id),
    CONSTRAINT uq_orden_items_orden_id_libro_id UNIQUE (orden_id, libro_id),
    CONSTRAINT ck_orden_items_1 CHECK (cantidad > 0),
    CONSTRAINT fk_orden_items_orden FOREIGN KEY (orden_id) REFERENCES ordenes_compra(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_orden_items_libro FOREIGN KEY (libro_id) REFERENCES libros(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Índices para búsquedas del catálogo
CREATE INDEX idx_libros_titulo ON libros (titulo);
CREATE INDEX idx_autores_nombre ON autores (apellidos, nombre);
CREATE INDEX idx_usuarios_nombre ON usuarios (apellido_paterno, nombre);
CREATE INDEX idx_ejemplares_estado ON ejemplares (estado);

