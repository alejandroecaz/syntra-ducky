# Lecciones aprendidas y propuesta de mejora (borrador)

> Borrador para que el equipo lo ajuste con su experiencia antes de la presentación.

## Lecciones aprendidas (técnicas)

1. **Diseñar la base de datos antes de programar ahorra retrabajo.** El primer prototipo guardaba autor, tema, editorial y ubicación como texto. Al alinear con el diagrama hubo que tocar modelos, servicios, plantillas y datos de prueba. Con el diseño cerrado desde el inicio el cambio habría sido mucho menor.
2. **Separar reglas de negocio de los controladores paga rápido.** Con la capa de servicios, el portal móvil se construyó sin duplicar la búsqueda ni el login: un controlador y unas vistas nuevas bastaron.
3. **Los criterios de aceptación son la mejor lista de pruebas.** Cada criterio ("clave exacta", "texto vacío", "cuenta deshabilitada", "ubicación no registrada") se volvió una prueba con pytest. Correrlas antes de cada commit evitó romper lo que ya funcionaba.
4. **Controlar el acceso por permisos, no por nombre de perfil.** Restringir el portal a alumnos fue asignar un permiso; abrirlo a colaboradores sería solo marcarlo en la pantalla de perfiles.
5. **Revisar el diseño con ojo crítico.** Copiar el diagrama tal cual habría permitido ubicaciones a medias y autores con el mismo orden; las restricciones `CHECK` y `UNIQUE` lo evitan desde la base de datos.
6. **Un design system reutilizable acelera.** Los tokens y macros de la web permitieron que el portal móvil se viera de la misma familia sin rediseñar.
7. **Probar en un celular real desde temprano.** El WiFi de la universidad puede aislar dispositivos; tener el hotspot y la vista de celular del navegador como plan B evita sorpresas en la demo.

## Propuesta de mejora para los siguientes sprints

| Mejora | Beneficio | Sprint sugerido |
|---|---|---|
| Préstamos, devoluciones y renovaciones desde el portal móvil (reservar un ejemplar disponible) | El alumno ya ve la disponibilidad; el siguiente paso natural es apartar el libro | 2 |
| Historial de préstamos y avisos para el alumno en el portal | Cumple lo que la propuesta promete para el portal de consulta | 2–3 |
| Pantallas de catálogos (autores, editoriales, temas, estancias, proveedores) con edición y fusión de duplicados | Mantener limpia la BD normalizada | 2 |
| Migraciones de esquema (en lugar de recrear `syntra.db`) | No perder datos al actualizar entre sprints | 2 |
| Pruebas de interfaz automatizadas con Playwright en cada Pull Request (CI en GitHub Actions) | Detectar errores visuales y de flujo antes de integrar | 2 |
| Paginación y orden en el catálogo | Rendimiento cuando el acervo crezca | 3 |
| Revisión de accesibilidad (contraste, lector de pantalla) en web y móvil | Uso por cualquier alumno | 3 |
| Definir con el cliente si el portal se abre a colaboradores | Basta con asignar el permiso `movil.acceder` | 2 |
