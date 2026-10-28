# Estándares de código

## Nombres
- **Español** en código, mensajes y documentación, con los mismos nombres que la base de datos (`libros`, `ejemplares`, `estante_id`, `apellido_paterno`).
- Archivos y funciones en `snake_case`: `catalogo_servicio.py`, `buscar_libros()`. Clases en `PascalCase`: `ErrorValidacion`. Constantes en `MAYUSCULAS`: `ESTADO_DISPONIBLE`.
- Un archivo por módulo en cada capa: `catalogo_controller.py` → `catalogo_servicio.py` → `models/libro.py`.

## Estructura de carpetas (MVC + servicios)
| Carpeta | Contiene | No contiene |
|---|---|---|
| `controllers/` | Un blueprint por módulo: lee la petición, llama al servicio, regresa la vista | SQL, reglas de negocio |
| `services/` | Validaciones, búsqueda, autenticación | SQL, `request`, `session`, plantillas |
| `models/` | Consultas SQL parametrizadas | Reglas de negocio |
| `views/` | Plantillas Jinja y macros de `components/ui.html` | Lógica de negocio |
| `config.py` | Permisos, estados, límites y mensajes compartidos | — |

## Estilo de código
- **PEP 8** revisado con **ruff** (`pyproject.toml`): líneas de hasta 120 caracteres, imports ordenados, nombres PEP 8.
- Docstring breve en español en cada módulo, servicio y modelo; comentario al inicio de cada plantilla con su papel.
- Sin valores mágicos: estados, permisos y límites salen de `config.py`.
- SQL siempre con parámetros `?`, nunca con texto del usuario concatenado.
- Compatible con Python 3.9.

## Manejo de errores
- Los servicios lanzan `ErrorValidacion(mensaje, errores, valores, codigo)`; el controlador muestra el mensaje, marca los campos y conserva lo capturado.
- Errores 403, 404 y 500 con páginas propias; **nunca** se muestra la traza.
- Contraseñas con hash PBKDF2; nunca se muestran ni se guardan en texto plano.

## Commits y ramas
- Nunca commit directo a `main` ni `push --force`; se trabaja en ramas y se integra con Pull Request.
- Commits pequeños, en español, con prefijo del área: `Esquema:`, `Servicios:`, `Web:`, `Móvil:`, `Calidad:`, `Docs:`.
- No se suben `venv/`, `.env` ni `syntra.db`.

## Pruebas
```bash
venv/bin/pip install -r requirements-dev.txt   # una vez
venv/bin/pytest                                 # todas las pruebas (usan una BD temporal)
venv/bin/ruff check .                           # estilo
```
Antes de abrir un Pull Request: `pytest` en verde y `ruff check .` sin errores.
