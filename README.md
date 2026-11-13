# Syntra · Prototipo funcional del Sprint 1

**Sistema Ducky de Gestión Bibliotecaria**, Biblioteca Universidad Ducky
Equipo Syntra: Melissa Silva Vázquez (624352), Tomás Zapata Pérez (629048), Alejandro Evaristo Cazares Escobedo (626337)

El prototipo cubre el **Sprint 1** (Gestión de usuarios, Gestionar libros y Buscar libros), es decir, las historias **HU-01-01 a HU-01-18** con sus criterios de aceptación, y del **Sprint 2** el préstamo y la devolución de libros: registro, boleta, renovación, lista de espera, devolución y multas con envío a Tesorería (**HU-02-01 a HU-02-08**). Tiene dos caras sobre el mismo Flask y el mismo MVC:

- **App web administrativa** (`/`): todas las historias del sprint.
- **Portal móvil de autoservicio para alumnos** (`/movil`): inicio de sesión, búsqueda y consulta de libros desde el navegador del celular.

## Cómo ejecutarlo

> **Después de cada `git pull` corre `venv/bin/python init_db.py`.** El esquema de la base de datos cambió en el Sprint 2 (tablas de préstamos, devoluciones, multas, precios y tipos de cambio, y reglas de préstamo en `perfiles`). Si `syntra.db` es de la versión anterior, la app no arranca y te recuerda este paso.

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
| `biblio` | `Biblio123` | Bibliotecario | Alta, edición y baja de libros, reportes, órdenes de compra, préstamos, renovaciones, lista de espera, devoluciones y multas | No (solo alumnos) |
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

### Sprint 2: préstamos

| HU | Dónde se demuestra |
|---|---|
| HU-02-01 Validación del solicitante | Préstamos → Registrar préstamo. `jlopez` tiene un préstamo **vencido**, `pmartinez` (N20500) tiene una **multa pendiente** de $30.00, `deshabilitado` tiene la cuenta deshabilitada, `visitante` no tiene préstamos en su perfil y un alumno no puede pasar de 3 préstamos |
| HU-02-02 Validación del libro | Mismo formulario. `EJ-0006` ya está prestado, `EJ-0013` está perdido, `EJ-0022` es de acceso reservado, `EJ-0025` es de un libro dado de baja, `600101` ya tiene un ejemplar de `LIB-001` y `EJ-0008` está apartado para el turno 1 de la lista de espera |
| HU-02-03 Registro del préstamo | Captura → confirmación → se asigna folio `PR-2026-0008` (los datos de prueba traen 5 préstamos activos y 2 ya devueltos). También desde la ficha del libro con el botón **Prestar** de cada ejemplar disponible |
| HU-02-04 Boleta de préstamo | Al registrar se abre la boleta: **correo** (con PDF adjunto), **WhatsApp**, **impresión** (la impresora de Sala de lectura está fuera de línea a propósito) y **Descargar PDF**. Abajo queda el historial de boletas emitidas |
| HU-02-05 Renovación de préstamo | En la boleta, tarjeta **Renovar préstamo**: muestra la nueva fecha antes de renovar. `PR-2026-0001` se puede renovar; `PR-2026-0002` no (su libro tiene lista de espera), `PR-2026-0003` no (vencido) y `PR-2026-0004` no (ya usó 2 de 2 renovaciones). Después de renovar se reenvía la boleta con la fecha nueva |
| HU-02-06 Registro de lista de espera | Circulación → Lista de espera, o el botón **Lista de espera** en la ficha de un libro sin disponibles (`LIB-011`). Se asigna turno; si el libro tiene ejemplares disponibles se pide prestarlo directo. Cuando se libera un ejemplar, el turno 1 aparece con **Ejemplar disponible** para avisarle por correo o WhatsApp y prestárselo (ver `LIB-003` con Daniela Fuentes); a nadie más se le puede prestar ese ejemplar mientras tanto |
| HU-02-07 Registro de devolución | Circulación → Devoluciones (o el botón **Registrar devolución** en la boleta). Se captura el código del ejemplar y qué pasó con el libro: lo devuelve bien, dañado o reporta que lo perdió. El préstamo queda Devuelto o Perdido y el ejemplar Disponible, Dañado o Perdido. Si el libro tiene lista de espera se avisa que el ejemplar es para el turno 1 (prueba con `EJ-0021`) |
| HU-02-08 Generación de multas y envío a Tesorería | Al registrar la devolución se generan las multas: **retraso** (días × multa diaria del perfil; `EJ-0019` llega 3 días tarde = $15.00), **daño** (monto que captura el bibliotecario) y **pérdida** (último precio del libro; `EJ-0002` cobra $429.00 y `EJ-0019` está en dólares: $95.00 × tipo de cambio; `EJ-0027` no tiene precio y pide capturar el costo). Las multas se mandan a Tesorería por correo con el aviso en PDF. En Circulación → **Multas** se ven las pendientes, se reenvían a Tesorería y se registra el pago cuando Tesorería confirma el cobro; con eso el usuario puede volver a pedir libros y renovar |

Reglas de préstamo por perfil (tabla `perfiles`): Alumno 3 libros por 7 días, Profesor, Bibliotecario y Administrador 5 libros por 14 días, Colaborador 2 por 7 días, y Visitante sin préstamos. Todos con 2 renovaciones (1 el Colaborador) y $5.00 de multa por día de retraso. Cada renovación suma los días de préstamo del perfil a la fecha de devolución.

Permisos nuevos (se ven en *Perfiles y permisos*): `prestamos.registrar`, `prestamos.renovar`, `espera.gestionar`, `devoluciones.registrar` y `multas.gestionar`, que tienen el Bibliotecario y el Administrador. Quien tenga multas pendientes no puede pedir prestado ni renovar hasta que se registre su pago.

### Envío de boletas por correo y WhatsApp

Se configura en el archivo `.env` (cópialo de `.env.example`). **Si no se configura nada, todo sigue funcionando**:

- **Correo sin configurar (modo demostración):** la boleta no sale a internet, se guarda como archivo `.eml` en la carpeta `boletas_enviadas/` (se abre con doble clic en Mail u Outlook y trae el PDF adjunto).
- **Avisos de multa para Tesorería:** se mandan a `TESORERIA_CORREO` (por omisión `tesoreria@ducky.edu.mx`); sin cuenta de correo también se guardan como `.eml` en `boletas_enviadas/`.
- **WhatsApp sin configurar:** el botón abre WhatsApp Web (o la app en el celular) con el chat del número capturado y la boleta ya escrita; solo hay que presionar enviar.

Para que el **correo se envíe de verdad** con una cuenta de Gmail:

1. En la cuenta de Google activa la **verificación en dos pasos**.
2. Entra a <https://myaccount.google.com/apppasswords>, crea una contraseña de aplicación (por ejemplo "Syntra") y copia las 16 letras.
3. En `.env` pon:

   ```
   CORREO_USUARIO=tu_cuenta@gmail.com
   CORREO_CONTRASENA=las16letrasdelacontrasena
   ```

4. Reinicia la app. En la boleta ya no aparece "Modo demostración" y el correo llega con el PDF adjunto.

Para que **WhatsApp se envíe solo, sin abrir el chat** (opcional), se usa el *sandbox* gratuito de Twilio: crea una cuenta en twilio.com, entra a *Messaging → Try it out → Send a WhatsApp message*, manda desde tu celular el código `join ...` al número del sandbox y pon en `.env` el `TWILIO_SID` y `TWILIO_TOKEN` de tu consola. En el sandbox solo reciben mensajes los celulares que mandaron el código `join`.

Los datos de prueba no tienen teléfono y sus correos son ficticios: para la demo escribe tu propio correo o celular en la boleta (los campos se pueden editar).

Datos de prueba útiles: `LIB-001` tiene ejemplares en dos salas; `LIB-002` (*Pedro Páramo*) tiene un ejemplar con **ubicación no registrada**; `LIB-008` (*El principito*) **no tiene ejemplares**; `LIB-006` tiene ejemplares perdido y fuera de servicio; `LIB-010`, `LIB-015` y `LIB-016` tienen **varios autores**; `LIB-014` está dado de baja.

## Estructura (MVC con Flask)

```
ingsoftprot/
├── app.py          # Arranca la app e imprime la dirección para el celular
├── config.py       # Permisos, estados y mensajes
├── init_db.py      # Crea la base de datos con los datos de prueba
├── controllers/    # Controladores: uno por módulo + movil_controller.py
├── services/       # Reglas de negocio (validaciones, búsqueda, login)
├── models/         # Acceso a datos con SQL
├── views/          # Vistas (plantillas); views/movil/ es el portal móvil
├── static/         # CSS, JS, imágenes y manifest.json
└── tests/          # Pruebas con pytest
```

La web y el móvil comparten servicios y modelos; solo cambian el controlador y las vistas.

## Pruebas

```bash
venv/bin/pip install -r requirements-dev.txt   # solo la primera vez
venv/bin/pytest
venv/bin/ruff check .
```

Las pruebas usan su propia base de datos temporal; no modifican `syntra.db`.
