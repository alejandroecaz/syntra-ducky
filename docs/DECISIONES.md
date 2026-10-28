# Decisiones del Sprint 1

## 1. Base de datos: cambios respecto al draw.io

El esquema de `init_db.py` ahora sigue el diagrama `base_de_datos/BD_Sistema_Ducky.drawio` (hoja *Sprint 1*) y el script `ducky_bd_sprint1.sql`, traducido de MySQL a SQLite. Antes los libros guardaban autor, tema y editorial como texto, los ejemplares la estancia como texto, los permisos eran texto libre, el usuario tenía un solo campo de nombre y el proveedor era texto. Todo eso ya está normalizado.

### Traducción de MySQL a SQLite (mismo significado)
| Diseño (MySQL) | SQLite | Motivo |
|---|---|---|
| `INT UNSIGNED AUTO_INCREMENT` | `INTEGER PRIMARY KEY AUTOINCREMENT` | Tipo nativo de SQLite |
| `ENUM(...)` en estados | `CHECK (estado IN (...))` | SQLite no tiene ENUM; los valores salen de `config.py` |
| `BOOLEAN` | `INTEGER` 0/1 | SQLite no tiene BOOLEAN |
| Colación `utf8mb4_spanish_ci` | `COLLATE NOCASE` en claves, cuentas y nombres únicos | Para que `alumno` y `Alumno` sigan contando como la misma cuenta, igual que en MySQL |
| Llaves foráneas | `PRAGMA foreign_keys = ON` en cada conexión | En SQLite vienen apagadas por omisión |

### Correcciones al diseño (errores reales que no se copiaron)
| Tabla | En el diseño | Corrección | Por qué |
|---|---|---|---|
| `libro_autores` | `orden` sin restricción | `UNIQUE (libro_id, orden)` y `CHECK (orden > 0)` | Sin esto dos autores podían ser "primer autor" del mismo libro y el orden de la portada quedaba ambiguo. |
| `ejemplares` | `estante_id` y `posicion` opcionales por separado | `CHECK ((estante_id IS NULL) = (posicion IS NULL))` | Permitía una posición sin estante o un estante sin posición: una ubicación a medias. HU-01-14 pide "Ubicación no registrada" y **no presentar una ubicación inventada**: o está completa o está pendiente. |
| `proveedores` | `nombre` sin `UNIQUE` | `nombre UNIQUE` | Dos proveedores con el mismo nombre no se pueden distinguir al capturar la orden de compra. |

### Ajustes menores
- **`tipo_acceso`** (Circulante, Reservado, Consulta externa) está en el diseño completo pero no en el script del Sprint 1. Se incluyó en `libros` porque es parte de la ficha bibliográfica y no cuesta nada; por omisión es *Circulante*.
- **`ejemplares.fecha_actualizacion`** se deja opcional como en el diseño; en pantalla se muestra la fecha de alta si nunca se ha actualizado.
- Se agregó el índice `idx_ejemplares_libro` porque la ficha del libro siempre consulta sus ejemplares.
- Solo se crearon las tablas del Sprint 1. Préstamos, multas, avisos, etc. (diseño completo) quedan para los siguientes sprints.

### Datos de demostración
Se conservan las mismas cuentas y los libros `LIB-001` a `LIB-014` con los mismos códigos de ejemplar. Se agregaron:
- Autores reales a los libros que ya tenían varios (`LIB-009`, `LIB-010`; `LIB-013` pasó de "Sears y Zemansky" a dos autores) y dos libros nuevos con varios autores (`LIB-015` *Patrones de diseño*, `LIB-016` *El lenguaje de programación C*).
- Ejemplares en distintas salas (`LIB-001`), uno sin ubicación (`LIB-002`, EJ-0005), un libro sin ejemplares (`LIB-008`) y ejemplares en cada estado.
- El ISBN se dejó vacío en los datos de prueba para no inventar números.

## 2. Cambios respecto al prototipo anterior

- **Capa de servicios** (`services/`): las reglas de negocio salieron de los controladores. Los controladores solo reciben la petición, llaman al servicio y regresan la vista; los modelos solo acceden a datos. Los servicios avisan de un error con `ErrorValidacion` (mensaje, errores por campo, lo capturado y el código HTTP).
- **Se conservó la captura por texto** de autores, tema, editorial y proveedor (con sugerencias). El servicio busca el registro sin importar acentos ni mayúsculas y lo crea si no existe. Es más rápido para el bibliotecario que obligarlo a dar de alta catálogos aparte, y la BD queda normalizada igual. Los autores se separan con punto y coma, en el orden de la portada.
- **Búsqueda por clave**: coincidencia exacta del valor completo (sin importar mayúsculas); `LIB-00` no encuentra `LIB-001`.
- **Usuarios**: el formulario separa nombre, apellido paterno y materno, y agrega correo y teléfono opcionales (únicos y validados).
- **HU-01-15**: la ficha de un libro sin ejemplares ya no muestra "0 de 0"; dice "Sin ejemplares".
- **HU-01-16 y HU-01-17**: en el listado se marcan con casillas los libros que entran al PDF o a la impresión (todos marcados por omisión). La selección se combina con los filtros; si no hay ninguno marcado se pide marcar al menos uno y no se genera nada.
- Las pantallas de acceso (web y móvil) ya no muestran la lista de cuentas de demostración; las cuentas siguen en el README.
- Se mantienen la baja lógica de libros y usuarios, los mensajes de los criterios de aceptación y el diseño visual.

## 3. Portal móvil: por qué es un portal responsive dentro del mismo Flask

La propuesta de negocio define el sistema como "una aplicación web administrativa y un **portal responsive de autoservicio**". También menciona Android Studio para una aplicación móvil; para el Sprint 1 se eligió el portal responsive porque:

1. **Lo pide la propuesta** como el canal de autoservicio de los usuarios.
2. **Reutiliza el MVC completo.** El portal es un controlador más (`movil_controller.py`) con sus vistas; usa los mismos servicios y modelos que la web. No hay lógica duplicada ni una API aparte que mantener, y las mismas pruebas cubren las reglas de las dos caras.
3. **Funciona en Android y en iPhone** desde el navegador, sin tiendas de apps. Con `manifest.json`, íconos y meta tags se puede "Agregar a pantalla de inicio" y se abre como app. Una app de Android Studio solo cubriría Android.
4. **Cabe en el sprint** y deja el camino abierto: si después se hace una app nativa, puede consumir los mismos servicios a través de una API.

Otras decisiones del portal:
- **Solo alumnos, por permiso.** Se creó `movil.acceder` ("Acceder al portal móvil", grupo General) y se asignó solo al perfil Alumno. El código revisa el permiso, no el nombre del perfil; si después se quiere abrir a colaboradores basta con asignarles el permiso desde *Perfiles y permisos*.
- **Del Figma se tomó solo la estructura** de las pantallas M00 a M04 (acceso, búsqueda, resultados, ficha y hoja de ubicación). M01 y M02 son la misma ruta `/movil`. El estilo sale del prototipo web: `movil.css` reusa los tokens y componentes de `syntra.css`. Se agregó el botón *Buscar* y la editorial en las tarjetas, que pide la entrega.
- **Sin service worker**: el portal necesita datos en vivo (disponibilidad) y no se pidió modo sin conexión.
