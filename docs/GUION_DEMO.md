# Guion de la demo (≈ 4 minutos)

**Antes de presentar (5 min antes):**
1. `venv/bin/python init_db.py` (datos limpios) y `venv/bin/python app.py`.
2. Copia la dirección "Portal móvil (celular)" que imprime la terminal y ábrela en el celular. Si no carga, conecta la laptop al hotspot del celular y vuelve a sacar la IP con `ipconfig getifaddr en0`.
3. Deja abiertas dos pestañas en la laptop: http://127.0.0.1:5050/login y http://127.0.0.1:5050/movil (plan B).
4. En el celular, deja el portal en la pantalla de acceso (ideal: ya agregado a la pantalla de inicio).

## Parte 1 · Web (≈ 1:45)

| Tiempo | Acción | Qué decir |
|---|---|---|
| 0:00 | En `/login` toca la cuenta **visitante** → Iniciar sesión | "El login valida credenciales, estado y perfil: este perfil no tiene acceso." |
| 0:15 | Toca **admin** → Iniciar sesión | "El panel y el menú muestran solo las funciones del perfil." |
| 0:30 | Menú **Catálogo** → Buscar por **Autor**: `garcia marquez` → Buscar | "Búsqueda sin acentos ni mayúsculas. La consulta une libros, autores, editorial y tema." |
| 0:50 | Cambia a **Clave**: `LIB-001` → Buscar → **Ver ejemplares** | "La clave es exacta. En la ficha: cada ejemplar con su estancia, estante, posición y estado." |
| 1:10 | Clic en **Ver ubicación** de un ejemplar | "La ubicación viene de estancias → estantes → ejemplares, como en el diseño de BD." |
| 1:25 | Menú **Perfiles y permisos** | "Aquí está el permiso *Acceder al portal móvil*: solo lo tiene Alumno. El acceso se controla por permiso, no por el nombre del perfil." |

## Parte 2 · Portal móvil en el celular (≈ 2:00)

| Tiempo | Acción | Qué decir |
|---|---|---|
| 1:45 | Entra con **profesor / Profe123** | "Mismo servicio de login que la web; además pide el permiso del portal: *Acceso no autorizado: el portal móvil es solo para alumnos*." |
| 2:00 | Entra con **alumno / Alumno123** | "Saludo con su nombre, resumen y libros disponibles ahora." |
| 2:15 | Elige el chip **Autor**, escribe `kernighan` → **Buscar** | "Tarjetas con clave, título, autores, editorial y disponibles. Es el mismo servicio de búsqueda que la web." |
| 2:35 | Chip **Clave**, escribe `LIB-001` → Buscar | "Clave exacta: un solo resultado." |
| 2:50 | Chip **Título**, escribe `zzz` → Buscar | "Sin coincidencias: *No se encontraron libros* y la lista vacía." |
| 3:05 | Borra el texto (o deja espacios) → Buscar | "Texto vacío: *Captura un criterio de búsqueda* y el formulario se conserva." |
| 3:15 | Chip **Título**, `paramo` → abre *Pedro Páramo* | "Ficha con datos bibliográficos y ejemplares. EJ-0005 dice *Ubicación no registrada*: no inventamos una ubicación." |
| 3:35 | **Ver ubicación** en EJ-0004 → Entendido | "Hoja con estancia, estante, posición y estado." |
| 3:45 | Cierra con la flecha / ícono de salir | "Mismo Flask, mismo MVC: solo cambian el controlador y las vistas. Funciona en Android y iPhone y se agrega a la pantalla de inicio." |

## Plan B si falla la red

1. En la laptop abre http://127.0.0.1:5050/movil.
2. Activa la vista de celular del navegador: Chrome `Cmd+Opción+I` y luego `Cmd+Shift+M` (elige *iPhone 12 Pro*). En Safari: menú *Desarrollo → Entrar al modo de diseño adaptable*.
3. Sigue el mismo guion de la Parte 2. Si el navegador está en tamaño normal, el portal también se ve centrado con ancho de celular.
4. Último recurso: mostrar las capturas de `docs/capturas/` (06 a 13 son las del portal móvil).
