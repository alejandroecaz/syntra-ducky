-- ============================================================
-- Sistema Ducky de Gestión Bibliotecaria - Syntra Technologies (Equipo 1)
-- Base de datos COMPLETA (Sprints 1-4) - MySQL 8
-- ============================================================
DROP DATABASE IF EXISTS ducky_biblioteca;
CREATE DATABASE ducky_biblioteca CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish_ci;
USE ducky_biblioteca;

-- Perfiles de usuario (Administrador, Bibliotecario, Profesor, Alumno...) y sus reglas de préstamo
CREATE TABLE perfiles (
    id                     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    nombre                 VARCHAR(60) NOT NULL UNIQUE,
    descripcion            VARCHAR(255),
    disponible             BOOLEAN NOT NULL DEFAULT TRUE,
    max_prestamos          TINYINT UNSIGNED,
    dias_prestamo          TINYINT UNSIGNED,
    max_renovaciones       TINYINT UNSIGNED,
    multa_diaria           DECIMAL(8,2),
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
    tipo_acceso            ENUM('Circulante','Reservado','Consulta externa') NOT NULL DEFAULT 'Circulante',
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

-- Historial de precios (para calcular reposición por pérdida)
CREATE TABLE precios_libro (
    id                     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    libro_id               INT UNSIGNED NOT NULL,
    precio                 DECIMAL(10,2) NOT NULL,
    moneda                 ENUM('MXN','USD') NOT NULL DEFAULT 'MXN',
    fecha_registro         DATE NOT NULL,
    CONSTRAINT pk_precios_libro PRIMARY KEY (id),
    CONSTRAINT ck_precios_libro_1 CHECK (precio > 0),
    CONSTRAINT fk_precios_libro_libro FOREIGN KEY (libro_id) REFERENCES libros(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Tipo de cambio vigente por fecha
CREATE TABLE tipos_cambio (
    id                     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    moneda                 ENUM('USD') NOT NULL DEFAULT 'USD',
    fecha                  DATE NOT NULL,
    valor_mxn              DECIMAL(10,4) NOT NULL,
    CONSTRAINT pk_tipos_cambio PRIMARY KEY (id),
    CONSTRAINT uq_tipos_cambio_moneda_fecha UNIQUE (moneda, fecha),
    CONSTRAINT ck_tipos_cambio_1 CHECK (valor_mxn > 0)
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
    estado                 ENUM('Registrada','Enviada','Recibida','Cancelada') NOT NULL DEFAULT 'Registrada',
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
    precio_unitario        DECIMAL(10,2),
    moneda                 ENUM('MXN','USD') NOT NULL DEFAULT 'MXN',
    cantidad_recibida      SMALLINT UNSIGNED NOT NULL DEFAULT 0,
    CONSTRAINT pk_orden_items PRIMARY KEY (id),
    CONSTRAINT uq_orden_items_orden_id_libro_id UNIQUE (orden_id, libro_id),
    CONSTRAINT ck_orden_items_1 CHECK (cantidad > 0),
    CONSTRAINT fk_orden_items_orden FOREIGN KEY (orden_id) REFERENCES ordenes_compra(id)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_orden_items_libro FOREIGN KEY (libro_id) REFERENCES libros(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Retiro de ejemplares perdidos, robados, dañados u obsoletos
CREATE TABLE bajas_ejemplar (
    id                     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    ejemplar_id            INT UNSIGNED NOT NULL UNIQUE,
    usuario_id             INT UNSIGNED NOT NULL,
    motivo                 ENUM('Perdido','Robado','Dañado','Obsoleto') NOT NULL,
    fecha_baja             DATE NOT NULL,
    observaciones          VARCHAR(255),
    CONSTRAINT pk_bajas_ejemplar PRIMARY KEY (id),
    CONSTRAINT fk_bajas_ejemplar_ejemplar FOREIGN KEY (ejemplar_id) REFERENCES ejemplares(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_bajas_ejemplar_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Préstamo de un ejemplar a un usuario
CREATE TABLE prestamos (
    id                     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    ejemplar_id            INT UNSIGNED NOT NULL,
    usuario_id             INT UNSIGNED NOT NULL,
    bibliotecario_id       INT UNSIGNED NOT NULL,
    fecha_prestamo         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_vencimiento      DATE NOT NULL,
    estado                 ENUM('Activo','Devuelto','Vencido','Perdido') NOT NULL DEFAULT 'Activo',
    CONSTRAINT pk_prestamos PRIMARY KEY (id),
    CONSTRAINT fk_prestamos_ejemplar FOREIGN KEY (ejemplar_id) REFERENCES ejemplares(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_prestamos_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_prestamos_bibliotecario FOREIGN KEY (bibliotecario_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Historial de renovaciones de cada préstamo
CREATE TABLE renovaciones (
    id                     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    prestamo_id            INT UNSIGNED NOT NULL,
    numero                 TINYINT UNSIGNED NOT NULL,
    fecha_renovacion       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    vencimiento_anterior   DATE NOT NULL,
    vencimiento_nuevo      DATE NOT NULL,
    CONSTRAINT pk_renovaciones PRIMARY KEY (id),
    CONSTRAINT uq_renovaciones_prestamo_id_numero UNIQUE (prestamo_id, numero),
    CONSTRAINT fk_renovaciones_prestamo FOREIGN KEY (prestamo_id) REFERENCES prestamos(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Registro de la devolución (máximo una por préstamo)
CREATE TABLE devoluciones (
    id                     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    prestamo_id            INT UNSIGNED NOT NULL UNIQUE,
    bibliotecario_id       INT UNSIGNED NOT NULL,
    fecha_devolucion       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    condicion              ENUM('Bueno','Dañado') NOT NULL DEFAULT 'Bueno',
    observaciones          VARCHAR(255),
    CONSTRAINT pk_devoluciones PRIMARY KEY (id),
    CONSTRAINT fk_devoluciones_prestamo FOREIGN KEY (prestamo_id) REFERENCES prestamos(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_devoluciones_bibliotecario FOREIGN KEY (bibliotecario_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Recibos de préstamo enviados o impresos
CREATE TABLE comprobantes_prestamo (
    id                     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    prestamo_id            INT UNSIGNED NOT NULL,
    medio                  ENUM('Email','WhatsApp','Impresión') NOT NULL,
    destino                VARCHAR(150),
    fecha_emision          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_comprobantes_prestamo PRIMARY KEY (id),
    CONSTRAINT fk_comprobantes_prestamo_prestamo FOREIGN KEY (prestamo_id) REFERENCES prestamos(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Usuarios esperando un libro sin ejemplares disponibles
CREATE TABLE lista_espera (
    id                     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    libro_id               INT UNSIGNED NOT NULL,
    usuario_id             INT UNSIGNED NOT NULL,
    fecha_solicitud        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado                 ENUM('En espera','Notificado','Atendido','Cancelado') NOT NULL DEFAULT 'En espera',
    CONSTRAINT pk_lista_espera PRIMARY KEY (id),
    CONSTRAINT fk_lista_espera_libro FOREIGN KEY (libro_id) REFERENCES libros(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_lista_espera_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Avisos de vencimiento, adeudo y lista de espera
CREATE TABLE avisos (
    id                     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    usuario_id             INT UNSIGNED NOT NULL,
    prestamo_id            INT UNSIGNED,
    tipo                   ENUM('Vencimiento','Adeudo','Lista de espera') NOT NULL,
    medio                  ENUM('Email','WhatsApp','Sistema') NOT NULL,
    mensaje                VARCHAR(500) NOT NULL,
    fecha_envio            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_avisos PRIMARY KEY (id),
    CONSTRAINT fk_avisos_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_avisos_prestamo FOREIGN KEY (prestamo_id) REFERENCES prestamos(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Multas generadas por un préstamo
CREATE TABLE multas (
    id                     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    prestamo_id            INT UNSIGNED NOT NULL,
    motivo                 ENUM('Retraso','Daño','Pérdida') NOT NULL,
    monto                  DECIMAL(10,2) NOT NULL,
    fecha_generacion       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado                 ENUM('Pendiente','Pagada','Cancelada') NOT NULL DEFAULT 'Pendiente',
    CONSTRAINT pk_multas PRIMARY KEY (id),
    CONSTRAINT ck_multas_1 CHECK (monto > 0),
    CONSTRAINT fk_multas_prestamo FOREIGN KEY (prestamo_id) REFERENCES prestamos(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Pagos (totales o parciales) de cada multa
CREATE TABLE pagos_multa (
    id                     INT UNSIGNED NOT NULL AUTO_INCREMENT,
    multa_id               INT UNSIGNED NOT NULL,
    bibliotecario_id       INT UNSIGNED NOT NULL,
    monto                  DECIMAL(10,2) NOT NULL,
    metodo                 ENUM('Efectivo','Tarjeta','Transferencia') NOT NULL,
    referencia             VARCHAR(50),
    fecha_pago             DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_pagos_multa PRIMARY KEY (id),
    CONSTRAINT ck_pagos_multa_1 CHECK (monto > 0),
    CONSTRAINT fk_pagos_multa_multa FOREIGN KEY (multa_id) REFERENCES multas(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_pagos_multa_bibliotecario FOREIGN KEY (bibliotecario_id) REFERENCES usuarios(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- Índices para búsquedas del catálogo
CREATE INDEX idx_libros_titulo ON libros (titulo);
CREATE INDEX idx_autores_nombre ON autores (apellidos, nombre);
CREATE INDEX idx_usuarios_nombre ON usuarios (apellido_paterno, nombre);
CREATE INDEX idx_ejemplares_estado ON ejemplares (estado);
CREATE INDEX idx_prestamos_estado ON prestamos (estado, fecha_vencimiento);
CREATE INDEX idx_multas_estado ON multas (estado);

