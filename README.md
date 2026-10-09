# Syntra · Prototipo funcional del Sprint 1

**Sistema Ducky de Gestión Bibliotecaria**, Biblioteca Universidad Ducky
Equipo Syntra: Melissa Silva Vázquez (624352), Tomás Zapata Pérez (629048), Alejandro Evaristo Cazares Escobedo (626337)

El prototipo cubre el **Sprint 1** (Gestión de usuarios, Gestionar libros y Buscar libros), es decir, las historias **HU-01-01 a HU-01-18** con sus criterios de aceptación.

## Cómo ejecutarlo

**Opción rápida (macOS):** doble clic en `iniciar.command`. Se abre el navegador en http://127.0.0.1:5050

**Desde la terminal:**

```bash
cd ~/Desktop/ingsoftprot
python3 -m venv venv              # solo la primera vez
venv/bin/pip install -r requirements.txt
venv/bin/python app.py            # http://127.0.0.1:5050
```

> Se usa el puerto **5050** porque en macOS el 5000 lo ocupa AirPlay.
> Para reiniciar los datos: `venv/bin/python init_db.py`.

## Cuentas de demostración

| Cuenta | Contraseña | Perfil | Sirve para |
|---|---|---|---|
| `admin` | `Admin123` | Administrador | Usuarios, perfiles y todo el catálogo |
| `biblio` | `Biblio123` | Bibliotecario | Alta, edición y baja de libros, reportes, órdenes de compra |
| `profesor` | `Profe123` | Profesor | Consulta del catálogo, PDF e impresión |
| `alumno` | `Alumno123` | Alumno | Solo consulta (para mostrar "Acceso no autorizado") |
| `deshabilitado` | `Demo123` | Alumno | Criterio "Cuenta deshabilitada" |
| `visitante` | `Demo123` | Visitante | Criterio "Perfil sin acceso al sistema" |

La pantalla de acceso muestra estas cuentas y las llena con un clic.

## Historias de usuario y dónde se demuestran

| HU | Pantalla |
|---|---|
| HU-01-01 Inicio de sesión | `/login`. El menú y el panel cambian según el perfil |
| HU-01-02 Registro de usuarios | Usuarios → Registrar usuario |
| HU-01-03 Baja de usuario | Usuarios → Deshabilitar (modal con Cancelar) |
| HU-01-04 Actualización de datos | Usuario → Editar datos |
| HU-01-05 Consulta de usuarios | Usuarios (por identificador o nombre) |
| HU-01-06 Cambio de contraseña | Menú del usuario → Cambiar contraseña |
| HU-01-07 Creación de perfiles | Perfiles y permisos → Crear perfil |
| HU-01-08 Asignación de perfiles | Usuario → Asignar perfil |
| HU-01-09 Alta de libros | Catálogo → Registrar libro |
| HU-01-10 Baja de libro | Ficha del libro → Dar de baja |
| HU-01-11 Actualización de libros | Ficha del libro → Editar libro |
| HU-01-12 Consulta del catálogo | Catálogo → Ver ejemplares |
| HU-01-13 Búsqueda por filtros | Catálogo (título, autor, tema, editorial, clave) |
| HU-01-14 Ubicación física | Ficha del libro → Ver ubicación |
| HU-01-15 Disponibilidad | Ficha del libro → estado de cada ejemplar |
| HU-01-16 Listado en PDF | Listado de libros → Generar PDF |
| HU-01-17 Impresión del listado | Listado de libros → Imprimir |
| HU-01-18 Orden de compra | Órdenes de compra → Nueva |

Cada plantilla documenta las HU que cubre en su cabecera (`ui.page_header(hus=[...])`) y en sus comentarios. Esta referencia es interna: no se muestra en la interfaz.

## Arquitectura (MVC con Flask)

```
ingsoftprot/
├── app.py                  # Punto de entrada, registro de blueprints
├── config.py               # Permisos, estados, catálogos
├── init_db.py              # Esquema SQLite + datos de demostración
├── controllers/            # Un blueprint por módulo (auth, usuarios, perfiles,
│                           #   catálogo, reportes, compras, cuenta)
├── models/                 # Acceso a datos (SQL parametrizado)
├── utils/                  # Seguridad (sesión/permisos), íconos SVG, PDF
├── views/
│   ├── base.html           # Documento base, avisos y modales comunes
│   ├── layouts/            # app (sidebar + topbar), público
│   ├── components/         # ui.html: macros reutilizables (botones, campos,
│   │                       #   badges, alertas, estados vacíos, encabezados…)
│   └── <módulo>/           # Pantallas
└── static/
    ├── css/syntra.css      # Design System: tokens + componentes
    ├── js/syntra.js        # Toasts, modales, confirmaciones, PDF, orden de compra
    └── img/                # Logotipos: ducky-libreria.png, syntra-technologies.png
```

- **Seguridad:** todas las rutas protegidas usan `@permiso_requerido(...)`. Sin sesión se pide iniciar sesión; si el perfil no tiene el permiso se muestra *Acceso no autorizado* (403). Las contraseñas se guardan cifradas (PBKDF2).
- **Base de datos:** SQLite para que el prototipo sea portátil. La propuesta contempla MariaDB en producción; el SQL es estándar.
- **Design System:** tokens y componentes en `static/css/syntra.css` y macros en `views/components/ui.html`. Todas las pantallas usan los mismos componentes.
- **Identidad visual:** el escudo de Ducky Librería aparece en la pantalla de acceso, el menú lateral y los documentos imprimibles; el logotipo de Syntra Technologies, en la pantalla de acceso.
- **Accesibilidad:** foco visible, texto alternativo en los logotipos, etiquetas en todos los campos y navegación con teclado.
