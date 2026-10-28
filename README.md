# Syntra · Prototipo funcional del Sprint 1

**Sistema Ducky de Gestión Bibliotecaria**, Biblioteca Universidad Ducky
Equipo Syntra: Melissa Silva Vázquez (624352), Tomás Zapata Pérez (629048), Alejandro Evaristo Cazares Escobedo (626337)

El prototipo cubre el **Sprint 1** (Gestión de usuarios, Gestionar libros y Buscar libros), es decir, las historias **HU-01-01 a HU-01-18** con sus criterios de aceptación. Tiene dos caras sobre el mismo Flask y el mismo MVC:

- **App web administrativa** (`/`): todas las historias del sprint.
- **Portal móvil de autoservicio para alumnos** (`/movil`): inicio de sesión, búsqueda y consulta de libros desde el navegador del celular.

## Cómo ejecutarlo

> **Después de cada `git pull` corre `venv/bin/python init_db.py`.** El esquema de la base de datos cambió en el Sprint 1 (tablas de autores, temas, editoriales, estantes, permisos…). Si `syntra.db` es de la versión anterior, la app no arranca y te recuerda este paso.

**Opción rápida (macOS):** doble clic en `iniciar.command`. Instala dependencias si hace falta, vuelve a crear `syntra.db` con los datos de prueba si es de la versión anterior y abre http://127.0.0.1:5050

**Desde la terminal:**

```bash
cd ~/Desktop/ingsoftprot
python3 -m venv venv                       # solo la primera vez
venv/bin/pip install -r requirements.txt   # solo la primera vez
venv/bin/python init_db.py                 # crea (o reinicia) syntra.db con los datos de prueba
venv/bin/python app.py                     # http://127.0.0.1:5050
```

Al arrancar, la terminal muestra las dos direcciones:

```
  Web (esta computadora):  http://127.0.0.1:5050
  Portal móvil (celular):  http://192.168.x.x:5050/movil
```

> Se usa el puerto **5050** porque en macOS el 5000 lo ocupa AirPlay. El servidor escucha en `0.0.0.0` para que el celular pueda conectarse.

## Cuentas de demostración

| Cuenta | Contraseña | Perfil | Web | Portal móvil |
|---|---|---|---|---|
| `admin` | `Admin123` | Administrador | Usuarios, perfiles y todo el catálogo | No (solo alumnos) |
| `biblio` | `Biblio123` | Bibliotecario | Alta, edición y baja de libros, reportes, órdenes de compra | No (solo alumnos) |
| `profesor` | `Profe123` | Profesor | Consulta del catálogo, PDF e impresión | **Rechazado**: "Acceso no autorizado: el portal móvil es solo para alumnos" |
| `alumno` | `Alumno123` | Alumno | Solo consulta | **Sí** |
| `deshabilitado` | `Demo123` | Alumno | Criterio "Cuenta deshabilitada" | Mismo mensaje que la web |
| `visitante` | `Demo123` | Visitante | Criterio "Perfil sin acceso al sistema" | Mismo mensaje que la web |

En el **portal móvil solo entran alumnos**: el acceso se controla con el permiso `movil.acceder` ("Acceder al portal móvil"), que solo tiene el perfil Alumno y se ve en *Perfiles y permisos*. Las pantallas de acceso no muestran estas cuentas: se escriben a mano.

## Demo en celular real

1. **Misma red.** La laptop y el celular deben estar en la misma red WiFi.
2. **Arranca el servidor** con `venv/bin/python app.py` y copia la dirección que imprime en "Portal móvil (celular)". También puedes sacar la IP de la Mac con:

   ```bash
   ipconfig getifaddr en0
   ```

   y abrir en el celular `http://<esa IP>:5050/movil`.
3. **Si macOS pregunta** si Python puede aceptar conexiones entrantes, elige *Permitir*.
4. **Si el WiFi de la universidad bloquea la conexión** entre dispositivos (la página no carga en el celular), activa el *hotspot* del celular, conecta la laptop a ese hotspot, vuelve a sacar la IP con `ipconfig getifaddr en0` (cambia al cambiar de red) y abre la nueva dirección en el celular.
5. **Agregar a la pantalla de inicio** (se abre como app, sin barra del navegador):
   - **iPhone (Safari):** botón Compartir → *Agregar a inicio*.
   - **Android (Chrome):** menú ⋮ → *Agregar a la pantalla principal* (o *Instalar app*).

**Plan B sin red:** abre http://127.0.0.1:5050/movil en la laptop y activa la vista de celular del navegador (Chrome: `Cmd+Opción+I` y luego `Cmd+Shift+M`). En computadora el portal también funciona: se muestra centrado con ancho de celular.

## Historias de usuario y dónde se demuestran

| HU | Web | Portal móvil |
|---|---|---|
| HU-01-01 Inicio de sesión | `/login`. El menú y el panel cambian según el perfil | `/movil/login` con los mismos mensajes + "solo alumnos" |
| HU-01-02 Registro de usuarios | Usuarios → Registrar usuario | — |
| HU-01-03 Baja de usuario | Usuarios → Deshabilitar (modal con Cancelar) | — |
| HU-01-04 Actualización de datos | Usuario → Editar datos | — |
| HU-01-05 Consulta de usuarios | Usuarios (por identificador o nombre) | — |
| HU-01-06 Cambio de contraseña | Menú del usuario → Cambiar contraseña | — |
| HU-01-07 Creación de perfiles | Perfiles y permisos → Crear perfil | — |
| HU-01-08 Asignación de perfiles | Usuario → Asignar perfil | — |
| HU-01-09 Alta de libros | Catálogo → Registrar libro | — |
| HU-01-10 Baja de libro | Ficha del libro → Dar de baja | — |
| HU-01-11 Actualización de libros | Ficha del libro → Editar libro | — |
| HU-01-12 Consulta del catálogo | Catálogo → Ver ejemplares | `/movil` → Ver catálogo → ficha |
| HU-01-13 Búsqueda por filtros | Catálogo (título, autor, tema, editorial, clave) | `/movil` (chips Título, Autor, Tema, Editorial, Clave) |
| HU-01-14 Ubicación física | Ficha del libro → Ver ubicación | Ficha → Ver ubicación (hoja inferior) |
| HU-01-15 Disponibilidad | Ficha del libro → estado de cada ejemplar | Ficha → estado de cada ejemplar |
| HU-01-16 Listado en PDF | Listado de libros → marca los libros → Generar PDF | — |
| HU-01-17 Impresión del listado | Listado de libros → marca los libros → Imprimir | — |
| HU-01-18 Orden de compra | Órdenes de compra → Nueva | — |

Datos de prueba útiles: `LIB-001` tiene ejemplares en dos salas; `LIB-002` (*Pedro Páramo*) tiene un ejemplar con **ubicación no registrada**; `LIB-008` (*El principito*) **no tiene ejemplares**; `LIB-006` tiene ejemplares perdido y fuera de servicio; `LIB-010`, `LIB-015` y `LIB-016` tienen **varios autores**; `LIB-014` está dado de baja.

## Arquitectura (MVC con Flask)

```
ingsoftprot/
├── app.py                  # Application factory, registro de blueprints, IP para el celular
├── config.py               # Permisos, estados, límites y mensajes compartidos
├── init_db.py              # Esquema SQLite (según el draw.io) + datos de demostración
├── controllers/            # C: un blueprint por módulo (auth, usuarios, perfiles, catálogo,
│                           #    reportes, compras, cuenta) y movil_controller.py para /movil
├── services/               # Reglas de negocio: validaciones, búsqueda, autenticación
├── models/                 # M: acceso a datos con SQL parametrizado (una tabla o grupo por archivo)
├── views/                  # V: plantillas Jinja
│   ├── layouts/            #    app (web), publico, movil (portal)
│   ├── components/ui.html  #    macros reutilizables (botones, campos, badges, ubicación…)
│   ├── movil/              #    pantallas del portal móvil
│   └── <módulo>/           #    pantallas web
├── static/
│   ├── css/syntra.css      # Design system: tokens + componentes
│   ├── css/movil.css       # Portal móvil, sobre los tokens de syntra.css
│   ├── manifest.json       # Para "Agregar a pantalla de inicio"
│   └── js/syntra.js        # Avisos, modales, confirmaciones, PDF, orden de compra
├── tests/                  # Pruebas con pytest
├── scripts/                # tomar_capturas.py (Playwright)
└── docs/                   # Arquitectura, estándares, decisiones, guion de demo, capturas
```

La web y el móvil **comparten servicios y modelos**; solo cambian el controlador y las vistas. Detalle en [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md).

- **Seguridad:** las rutas protegidas usan `@permiso_requerido(...)` con códigos de permiso (nunca nombres de perfil). Sin sesión se pide iniciar sesión; sin permiso se muestra *Acceso no autorizado* (403). Las contraseñas se guardan con hash PBKDF2 y los errores nunca muestran trazas.
- **Base de datos:** SQLite con llaves foráneas activas, alineada con `base_de_datos/BD_Sistema_Ducky.drawio`. Los cambios respecto al diseño están en [docs/DECISIONES.md](docs/DECISIONES.md).
- **Design system:** tokens y componentes en `static/css/syntra.css` y macros en `views/components/ui.html`; el portal móvil reusa ambos.

## Calidad: pruebas y estilo

```bash
venv/bin/pip install -r requirements-dev.txt   # pytest, ruff y playwright (solo la primera vez)
venv/bin/pytest                                 # todas las pruebas
venv/bin/ruff check .                           # PEP 8 y convenciones
```

Las pruebas crean su propia base de datos temporal; no modifican `syntra.db`. Convenciones en [docs/ESTANDARES.md](docs/ESTANDARES.md).

## Material para la presentación

- [docs/GUION_DEMO.md](docs/GUION_DEMO.md): guion de 4 minutos con plan B.
- [docs/capturas/](docs/capturas/): pantallas web y móviles. Para regenerarlas: `venv/bin/playwright install chromium` (una vez) y `venv/bin/python scripts/tomar_capturas.py`.
- [docs/LECCIONES.md](docs/LECCIONES.md): borrador de lecciones aprendidas y propuesta de mejora.
