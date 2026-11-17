/*
   ============================================================
   Archivo:      static/js/syntra.js
   Proyecto:     Sistema Ducky de Gestion Bibliotecaria
   Empresa desarrolladora: Syntra Technologies
   Cliente:      Universidad Ducky

   Descripcion:
       Comportamiento de la interfaz: avisos, modales, confirmaciones,
       cambios sin guardar, PDF, impresion, orden de compra y seleccion de
       libros del listado.

   Autores:
       Melissa Silva Vazquez (624352)
       Tomas Zapata Perez (629048)
       Alejandro Evaristo Cazares Escobedo (626337)

   Fecha:
       21/09/2026
   ============================================================

*/
(function () {
    "use strict";

    // ============================================================
    // UTILIDADES
    // Funciones para buscar elementos, dibujar iconos y escapar texto.
    // ============================================================

    // Busca el primer elemento que cumple el selector.
    function buscarElemento(selector, contexto) {
        return (contexto || document).querySelector(selector);
    }

    // Busca todos los elementos que cumplen el selector y los regresa en un arreglo.
    function buscarElementos(selector, contexto) {
        var lista = (contexto || document).querySelectorAll(selector);
        return Array.prototype.slice.call(lista);
    }

    // Trazos SVG de los iconos de los avisos (los mismos de utils/iconos.py).
    var ICONOS = {
        exito: '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/>',
        error: '<circle cx="12" cy="12" r="10"/><path d="M12 8v4"/><path d="M12 16h.01"/>',
        advertencia: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 '
            + '2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
        informacion: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/>'
            + '<path d="M12 8h.01"/>'
    };
    var TRAZO_CERRAR = '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>';

    // Arma el SVG de un icono con su tamano.
    function dibujarIcono(trazo, tamano) {
        var medida = tamano || 20;
        return '<svg class="icono" width="' + medida + '" height="' + medida + '" '
            + 'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            + 'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            + trazo + "</svg>";
    }

    // Escapa el texto para insertarlo como HTML sin riesgo.
    function escaparTexto(texto) {
        var contenedor = document.createElement("div");
        contenedor.textContent = texto;
        return contenedor.innerHTML;
    }

    // ============================================================
    // AVISOS FLOTANTES
    // Muestran los mensajes del servidor y los de esta pagina, y los
    // cierran solos despues de unos segundos.
    // ============================================================

    // Titulo de cada tono de aviso.
    var TITULOS = {
        exito: "Listo",
        error: "No se pudo completar",
        advertencia: "Atención",
        informacion: "Aviso"
    };

    // Cierra el aviso con animacion.
    function cerrarAviso(aviso) {
        if (!aviso || aviso.classList.contains("saliendo")) {
            return;
        }
        aviso.classList.add("saliendo");
        setTimeout(function () {
            aviso.remove();
        }, 250);
    }

    // Los errores se quedan mas tiempo en pantalla.
    function programarCierre(aviso) {
        var tiempo = aviso.classList.contains("aviso-error") ? 9000 : 6000;
        setTimeout(function () {
            cerrarAviso(aviso);
        }, tiempo);
    }

    // Muestra un aviso nuevo (lo usan los modales y el PDF).
    function mostrarAviso(tono, mensaje, titulo) {
        var pila = buscarElemento(".pila-avisos");
        if (!pila) {
            return;
        }
        var aviso = document.createElement("div");
        aviso.className = "aviso aviso-" + tono;
        aviso.setAttribute("role", tono === "error" ? "alert" : "status");
        aviso.innerHTML = dibujarIcono(ICONOS[tono] || ICONOS.informacion)
            + '<div class="aviso-cuerpo"><strong class="aviso-titulo">'
            + escaparTexto(titulo || TITULOS[tono]) + "</strong>"
            + escaparTexto(mensaje) + "</div>"
            + '<button type="button" class="aviso-cerrar" aria-label="Cerrar aviso">'
            + dibujarIcono(TRAZO_CERRAR, 16) + "</button>";
        pila.appendChild(aviso);
        programarCierre(aviso);
    }

    // Avisos que ya vienen del servidor (mensajes flash) y boton para cerrarlos.
    buscarElementos(".aviso").forEach(programarCierre);
    document.addEventListener("click", function (evento) {
        var boton = evento.target.closest(".aviso-cerrar");
        if (boton) {
            cerrarAviso(boton.closest(".aviso"));
        }
    });

    // ============================================================
    // MODALES
    // Abren y cierran las ventanas modales y regresan el foco al
    // elemento que las abrio.
    // ============================================================

    // Elemento que tenia el foco antes de abrir el modal.
    var ultimoFoco = null;

    // Abre el modal y pone el foco en su primer control.
    function abrirModal(modal) {
        if (!modal) {
            return;
        }
        ultimoFoco = document.activeElement;
        modal.classList.add("abierto");
        document.body.classList.add("modal-abierto");
        var foco = modal.querySelector("[data-enfocar]")
            || modal.querySelector("button, input, select, textarea");
        if (foco) {
            setTimeout(function () {
                foco.focus();
            }, 30);
        }
    }

    // Cierra el modal; si fue cancelado avisa que no hubo cambios.
    function cerrarModal(modal, cancelado) {
        if (!modal || !modal.classList.contains("abierto")) {
            return;
        }
        modal.classList.remove("abierto");
        if (!buscarElemento(".modal.abierto")) {
            document.body.classList.remove("modal-abierto");
        }
        if (ultimoFoco) {
            ultimoFoco.focus();
        }
        if (cancelado && modal.dataset.mensajeCancelado) {
            mostrarAviso("informacion", modal.dataset.mensajeCancelado, "Operación cancelada");
        }
    }

    // Botones que abren (data-abrir-modal) o cierran (data-cerrar-modal) un modal.
    document.addEventListener("click", function (evento) {
        var abrir = evento.target.closest("[data-abrir-modal]");
        if (abrir) {
            evento.preventDefault();
            abrirModal(document.getElementById(abrir.dataset.abrirModal));
            return;
        }
        var cerrar = evento.target.closest("[data-cerrar-modal]");
        if (cerrar) {
            evento.preventDefault();
            cerrarModal(cerrar.closest(".modal"), true);
        }
    });

    // La tecla Escape cierra el modal abierto y los menus.
    document.addEventListener("keydown", function (evento) {
        if (evento.key !== "Escape") {
            return;
        }
        var abierto = buscarElementos(".modal.abierto").pop();
        if (abierto) {
            cerrarModal(abierto, true);
        }
        buscarElementos(".menu.abierto").forEach(function (menu) {
            menu.classList.remove("abierto");
        });
    });

    // ============================================================
    // CONFIRMACION (HU-01-03 Y HU-01-10)
    // Los botones con data-confirmar (deshabilitar cuenta, dar de baja
    // un libro...) llenan el modal de confirmacion; Cancelar no cambia
    // nada.
    // ============================================================
    document.addEventListener("click", function (evento) {
        var disparador = evento.target.closest("[data-confirmar]");
        if (!disparador) {
            return;
        }
        evento.preventDefault();
        var modal = document.getElementById("modal-confirmar");
        var datos = disparador.dataset;
        var tono = datos.confirmarTono || "peligro";

        // Titulo, texto e icono del modal.
        buscarElemento("[data-confirmar-titulo]", modal).textContent =
            datos.confirmarTitulo || "¿Confirmas la operación?";
        buscarElemento("[data-confirmar-texto]", modal).textContent = datos.confirmarTexto || "";
        var icono = buscarElemento("[data-confirmar-icono]", modal);
        icono.className = "modal-icono modal-icono-" + tono;
        icono.innerHTML = dibujarIcono(
            tono === "peligro" ? ICONOS.advertencia : ICONOS.informacion,
            22
        );

        // Boton para aceptar con el estilo del tono.
        var aceptar = buscarElemento("[data-confirmar-aceptar]", modal);
        aceptar.textContent = datos.confirmarEtiqueta || "Confirmar";
        aceptar.className = "boton " + (tono === "peligro" ? "boton-peligro" : "boton-primario");

        // Formulario con la accion y los campos ocultos que se mandan (por ejemplo la accion).
        var formulario = buscarElemento("form", modal);
        var campos = buscarElemento(".campos-confirmacion", formulario);
        formulario.action = datos.confirmarAccion;
        campos.innerHTML = "";
        var valores = datos.confirmarCampos ? JSON.parse(datos.confirmarCampos) : {};
        Object.keys(valores).forEach(function (nombre) {
            var oculto = document.createElement("input");
            oculto.type = "hidden";
            oculto.name = nombre;
            oculto.value = valores[nombre];
            campos.appendChild(oculto);
        });
        modal.dataset.mensajeCancelado = datos.confirmarCancelado || "No se realizaron cambios.";
        abrirModal(modal);
    });

    // ============================================================
    // BOTON EN MODO CARGA
    // Al enviar un formulario el boton muestra que esta procesando.
    // ============================================================
    document.addEventListener("submit", function (evento) {
        var boton = evento.submitter || buscarElemento("[type=submit]", evento.target);
        if (boton && !evento.defaultPrevented) {
            setTimeout(function () {
                boton.classList.add("cargando");
            }, 0);
        }
        var formulario = evento.target;
        if (formulario.hasAttribute("data-vigilar-cambios")) {
            formulario.dataset.enviando = "1";
        }
    });

    // ============================================================
    // CAMBIOS SIN GUARDAR (HU-01-11 · CANCELAR EDICION)
    // Se guarda el estado inicial del formulario y, si se cancela con
    // cambios, se pide confirmar antes de descartarlos.
    // ============================================================
    buscarElementos("form[data-vigilar-cambios]").forEach(function (formulario) {
        var inicial = new URLSearchParams(new FormData(formulario)).toString();
        formulario.estaModificado = function () {
            return new URLSearchParams(new FormData(formulario)).toString() !== inicial;
        };
    });

    document.addEventListener("click", function (evento) {
        var enlace = evento.target.closest("[data-cancelar-edicion]");
        if (!enlace) {
            return;
        }
        var formulario = buscarElemento("form[data-vigilar-cambios]");
        if (formulario && formulario.estaModificado && formulario.estaModificado()) {
            evento.preventDefault();
            var modal = document.getElementById("modal-descartar");
            buscarElemento("[data-aceptar-descartar]", modal).href =
                enlace.dataset.enlaceDescartar || enlace.href;
            abrirModal(modal);
        }
    });

    // ============================================================
    // MOSTRAR U OCULTAR CONTRASENA
    // El boton del ojo cambia el campo entre texto y contrasena.
    // ============================================================
    document.addEventListener("click", function (evento) {
        var boton = evento.target.closest("[data-alternar-contrasena]");
        if (!boton) {
            return;
        }
        var campo = document.getElementById(boton.dataset.alternarContrasena);
        var visible = campo.type === "text";
        campo.type = visible ? "password" : "text";
        boton.setAttribute("aria-label", visible ? "Mostrar contraseña" : "Ocultar contraseña");
        boton.setAttribute("aria-pressed", String(!visible));
    });

    // ============================================================
    // FILAS CLICABLES
    // Las filas con data-enlace abren el detalle, salvo que se de clic
    // en un boton o enlace de la fila.
    // ============================================================
    document.addEventListener("click", function (evento) {
        var fila = evento.target.closest("tr[data-enlace]");
        if (!fila || evento.target.closest("a, button, form, input, select")) {
            return;
        }
        window.location.href = fila.dataset.enlace;
    });

    // ============================================================
    // MENU LATERAL EN CELULAR Y MENU DEL USUARIO
    // Abren y cierran el menu lateral en pantallas chicas y el menu
    // desplegable del usuario.
    // ============================================================
    var menuLateral = buscarElemento(".menu-lateral");
    var velo = buscarElemento(".velo");

    // Abre o cierra el menu lateral en pantallas chicas.
    function alternarMenuLateral(abrir) {
        if (!menuLateral) {
            return;
        }
        menuLateral.classList.toggle("abierto", abrir);
        velo.classList.toggle("abierto", abrir);
    }

    document.addEventListener("click", function (evento) {
        if (evento.target.closest("[data-alternar-menu-lateral]")) {
            alternarMenuLateral(!menuLateral.classList.contains("abierto"));
        } else if (evento.target.closest(".velo")) {
            alternarMenuLateral(false);
        }

        // El menu del usuario se cierra al dar clic fuera de el.
        var ficha = evento.target.closest("[data-alternar-menu]");
        buscarElementos(".menu.abierto").forEach(function (menu) {
            if (!ficha || menu !== document.getElementById(ficha.dataset.alternarMenu)) {
                menu.classList.remove("abierto");
            }
        });
        if (ficha) {
            var menu = document.getElementById(ficha.dataset.alternarMenu);
            menu.classList.toggle("abierto");
            ficha.setAttribute("aria-expanded", String(menu.classList.contains("abierto")));
        }
    });

    // ============================================================
    // GENERAR PDF (HU-01-16)
    // Se pide el PDF con fetch para mostrar el resultado sin salir del
    // listado.
    // ============================================================

    // Descarga el PDF y muestra el aviso de exito con sus enlaces.
    function mostrarPdfGenerado(destino, archivo, total) {
        var enlaceArchivo = URL.createObjectURL(archivo);
        var descarga = document.createElement("a");
        descarga.href = enlaceArchivo;
        descarga.download = "listado_libros.pdf";
        document.body.appendChild(descarga);
        descarga.click();
        descarga.remove();
        destino.innerHTML = '<div class="alerta alerta-exito" role="status">'
            + dibujarIcono(ICONOS.exito)
            + '<div class="alerta-cuerpo">'
            + '<strong class="alerta-titulo">PDF generado correctamente</strong>'
            + "El documento incluye " + total + " libros con clave, título, autor, tema, "
            + "editorial y estado. "
            + '<a href="' + enlaceArchivo + '" target="_blank" rel="noopener">Abrir PDF</a> · '
            + '<a href="' + enlaceArchivo + '" download="listado_libros.pdf">'
            + "Descargar de nuevo</a></div></div>";
        mostrarAviso("exito", "Se descargó el listado con " + total + " libros.", "PDF generado");
    }

    // Muestra el error o la advertencia del PDF en la pagina y en un aviso.
    function mostrarErrorPdf(destino, problema) {
        var tono = problema && problema.tono ? problema.tono : "error";
        var mensaje = problema && problema.mensaje
            ? problema.mensaje
            : "El documento no pudo generarse. Intenta nuevamente.";
        var titulo = tono === "error" ? "No se generó el PDF" : "Sin registros para el PDF";
        destino.innerHTML = '<div class="alerta alerta-' + tono + '" role="alert">'
            + dibujarIcono(ICONOS[tono])
            + '<div class="alerta-cuerpo"><strong class="alerta-titulo">' + titulo + "</strong>"
            + escaparTexto(mensaje) + "</div></div>";
        mostrarAviso(tono, mensaje);
    }

    document.addEventListener("click", function (evento) {
        var boton = evento.target.closest("[data-url-pdf]");
        if (!boton) {
            return;
        }
        evento.preventDefault();
        var destino = buscarElemento(boton.dataset.resultadoPdf);
        boton.classList.add("cargando");
        destino.innerHTML = "";

        // Si el boton tiene un formulario asociado, manda sus datos (filtros y libros marcados).
        var direccion = boton.dataset.urlPdf;
        var formularioPdf = boton.dataset.formularioPdf
            && document.getElementById(boton.dataset.formularioPdf);
        if (formularioPdf) {
            direccion += (direccion.indexOf("?") === -1 ? "?" : "&")
                + new URLSearchParams(new FormData(formularioPdf)).toString();
        }

        // HU-01-16 · Generacion satisfactoria / Catalogo sin registros / Error en la generacion.
        fetch(direccion, {
            headers: { "X-Requested-With": "fetch" },
            credentials: "same-origin"
        })
            .then(function (respuesta) {
                var tipo = respuesta.headers.get("Content-Type") || "";
                if (respuesta.ok && tipo.indexOf("application/pdf") === 0) {
                    var total = respuesta.headers.get("X-Total-Registros");
                    return respuesta.blob().then(function (archivo) {
                        mostrarPdfGenerado(destino, archivo, total);
                    });
                }
                if (respuesta.status === 401 || respuesta.status === 403 || respuesta.redirected) {
                    throw {
                        tono: "error",
                        mensaje: "Acceso no autorizado para generar documentos."
                    };
                }
                return respuesta.json().then(function (datos) {
                    throw {
                        tono: respuesta.status >= 500 ? "error" : "advertencia",
                        mensaje: datos.mensaje
                    };
                });
            })
            .catch(function (problema) {
                mostrarErrorPdf(destino, problema);
            })
            .finally(function () {
                boton.classList.remove("cargando");
            });
    });

    // ============================================================
    // IMPRESION (HU-01-17 Y HU-01-18)
    // Abre el dialogo de impresion al confirmar o con los botones
    // data-imprimir.
    // ============================================================
    if (buscarElemento("[data-imprimir-al-cargar]")) {
        setTimeout(function () {
            window.print();
        }, 600);
    }
    document.addEventListener("click", function (evento) {
        if (evento.target.closest("[data-imprimir]")) {
            evento.preventDefault();
            window.print();
        }
    });

    // ============================================================
    // BOLETA POR WHATSAPP (HU-02-04)
    // El formulario abre WhatsApp en otra pestana; esta pagina se recarga
    // para mostrar la boleta en el historial.
    // ============================================================
    document.addEventListener("submit", function (evento) {
        if (evento.target.matches("[data-recargar-al-enviar]")) {
            setTimeout(function () {
                window.location.reload();
            }, 1500);
        }
    });

    // ============================================================
    // ACTUALIZAR EJEMPLAR (HU-01-15 · DISPONIBILIDAD ACTUALIZADA)
    // Llena el modal con los datos del ejemplar elegido.
    // ============================================================
    document.addEventListener("click", function (evento) {
        var boton = evento.target.closest("[data-ejemplar]");
        if (!boton) {
            return;
        }
        var datos = JSON.parse(boton.dataset.ejemplar);
        var modal = document.getElementById("modal-ejemplar");
        var formulario = buscarElemento("form", modal);
        formulario.action = datos.accion;
        buscarElemento("[data-ejemplar-codigo]", modal).textContent = datos.codigo;
        ["estancia", "estante", "posicion", "estado"].forEach(function (campo) {
            formulario.elements[campo].value = datos[campo] || "";
        });
        abrirModal(modal);
    });

    // ============================================================
    // RENGLONES DE LA ORDEN DE COMPRA (HU-01-18)
    // Agrega y quita renglones y recalcula el resumen de la orden.
    // ============================================================
    var contenedorRenglones = buscarElemento("[data-renglones-orden]");
    if (contenedorRenglones) {
        var plantilla = document.getElementById("plantilla-renglon");

        // Recalcula renglones, titulos distintos y total de ejemplares.
        var actualizarResumenOrden = function () {
            var renglones = buscarElementos(".renglon-orden", contenedorRenglones);
            var titulos = {};
            var ejemplares = 0;
            renglones.forEach(function (renglon) {
                var libro = buscarElemento("select", renglon).value;
                var cantidad = parseInt(buscarElemento("input", renglon).value, 10);
                if (libro && cantidad > 0) {
                    titulos[libro] = true;
                    ejemplares += cantidad;
                }
                buscarElemento("[data-quitar-renglon]", renglon).disabled = renglones.length === 1;
            });
            buscarElemento("[data-total-titulos]").textContent = Object.keys(titulos).length;
            buscarElemento("[data-total-ejemplares]").textContent = ejemplares;
            buscarElemento("[data-total-renglones]").textContent = renglones.length;
        };

        // Agrega un renglon (copia de la plantilla) o lo quita.
        document.addEventListener("click", function (evento) {
            if (evento.target.closest("[data-agregar-renglon]")) {
                contenedorRenglones.appendChild(plantilla.content.cloneNode(true));
                var nuevo = buscarElementos(".renglon-orden", contenedorRenglones).pop();
                buscarElemento("select", nuevo).focus();
                actualizarResumenOrden();
            }
            var quitar = evento.target.closest("[data-quitar-renglon]");
            if (quitar) {
                quitar.closest(".renglon-orden").remove();
                actualizarResumenOrden();
            }
        });
        contenedorRenglones.addEventListener("input", actualizarResumenOrden);
        contenedorRenglones.addEventListener("change", actualizarResumenOrden);
        actualizarResumenOrden();
    }

    // ============================================================
    // SELECCION DE LIBROS DEL LISTADO (HU-01-16 Y HU-01-17)
    // Solo los libros marcados entran al PDF y a la impresion.
    // ============================================================
    var casillasLibro = buscarElementos("[data-seleccion-libro]");
    if (casillasLibro.length) {
        var casillaTodos = buscarElemento("[data-seleccion-todos]");
        var resumenSeleccion = buscarElemento("[data-seleccion-resumen]");

        // Actualiza la casilla de todos, el resumen y habilita o deshabilita Imprimir y PDF.
        var actualizarSeleccion = function () {
            var marcadas = casillasLibro.filter(function (casilla) {
                return casilla.checked;
            }).length;
            casillaTodos.checked = marcadas === casillasLibro.length;
            casillaTodos.indeterminate = marcadas > 0 && marcadas < casillasLibro.length;
            resumenSeleccion.textContent = marcadas
                ? marcadas + " de " + casillasLibro.length + " seleccionados"
                : "Marca al menos un libro para imprimir o generar el PDF";
            resumenSeleccion.classList.toggle("con-advertencia", !marcadas);
            buscarElementos("[data-requiere-seleccion]").forEach(function (boton) {
                boton.disabled = !marcadas;
            });
        };

        casillaTodos.addEventListener("change", function () {
            casillasLibro.forEach(function (casilla) {
                casilla.checked = casillaTodos.checked;
            });
            actualizarSeleccion();
        });
        casillasLibro.forEach(function (casilla) {
            casilla.addEventListener("change", actualizarSeleccion);
        });
        actualizarSeleccion();
    }

    // ============================================================
    // DATOS DEL LIBRO POR ISBN (HU-01-09)
    // Pide a la app los datos de Open Library y llena el formulario de
    // alta. El Enter del campo ISBN (o del lector de codigo de barras)
    // busca en lugar de guardar.
    // ============================================================
    var botonIsbn = buscarElemento("[data-buscar-isbn]");
    if (botonIsbn) {
        var campoIsbn = document.getElementById("isbn");

        // Llena los campos que trajo Open Library sin borrar los demas.
        var llenarFicha = function (datos) {
            ["isbn", "titulo", "autores", "editorial", "anio"].forEach(function (nombre) {
                var campo = document.getElementById(nombre);
                if (campo && datos[nombre]) {
                    campo.value = datos[nombre];
                    campo.classList.remove("invalido");
                }
            });
        };

        var buscarIsbn = function () {
            var isbn = campoIsbn.value.trim();
            if (!isbn) {
                mostrarAviso("advertencia", "Escribe el ISBN para buscar los datos del libro.");
                campoIsbn.focus();
                return;
            }
            botonIsbn.classList.add("cargando");
            botonIsbn.disabled = true;
            fetch(botonIsbn.dataset.buscarIsbn + "?isbn=" + encodeURIComponent(isbn), {
                headers: { "X-Requested-With": "fetch" },
                credentials: "same-origin"
            })
                .then(function (respuesta) {
                    if (respuesta.status === 401 || respuesta.status === 403
                        || respuesta.redirected) {
                        throw { tono: "error", mensaje: "Tu perfil no puede dar de alta libros." };
                    }
                    return respuesta.json().then(function (datos) {
                        if (!respuesta.ok) {
                            throw {
                                tono: respuesta.status >= 500 ? "error" : "advertencia",
                                mensaje: datos.mensaje
                            };
                        }
                        llenarFicha(datos.datos);
                        mostrarAviso(datos.tono, datos.mensaje);
                        var tema = document.getElementById("tema");
                        if (tema && !tema.value) {
                            tema.focus();
                        }
                    });
                })
                .catch(function (problema) {
                    mostrarAviso(problema.tono || "error", problema.mensaje
                        || "No se pudo consultar el ISBN. Captura los datos a mano.");
                })
                .finally(function () {
                    botonIsbn.classList.remove("cargando");
                    botonIsbn.disabled = false;
                });
        };

        botonIsbn.addEventListener("click", buscarIsbn);
        campoIsbn.addEventListener("keydown", function (evento) {
            if (evento.key === "Enter") {
                evento.preventDefault();
                buscarIsbn();
            }
        });
    }

    // ============================================================
    // RESULTADO DE LA DEVOLUCION (HU-02-07)
    // Solo se ven los campos del resultado elegido (monto por dano o costo
    // de reposicion). Sin JavaScript se ven todos.
    // ============================================================
    var opcionesResultado = buscarElementos("[data-mostrar-segun]");
    if (opcionesResultado.length) {
        // Muestra los bloques del resultado marcado y oculta los demas.
        var actualizarResultado = function () {
            var marcada = opcionesResultado.filter(function (opcion) {
                return opcion.checked;
            })[0];
            buscarElementos("[data-mostrar-con]").forEach(function (bloque) {
                bloque.hidden = !marcada || bloque.dataset.mostrarCon !== marcada.value;
            });
        };
        opcionesResultado.forEach(function (opcion) {
            opcion.addEventListener("change", actualizarResultado);
        });
        actualizarResultado();
    }

    // ============================================================
    // CHATBOT (HU-02-09)
    // Ventana de chat: carga la conversacion abierta, manda las preguntas
    // (sugeridas o escritas) y muestra las respuestas. El texto se pinta con
    // textContent para no interpretar HTML.
    // ============================================================
    var chatbot = buscarElemento("[data-chatbot]");
    if (chatbot) {
        var panelChat = buscarElemento(".chatbot-panel", chatbot);
        var botonChat = buscarElemento("[data-chatbot-abrir]", chatbot);
        var listaChat = buscarElemento("[data-chatbot-mensajes]", chatbot);
        var sugerenciasChat = buscarElemento("[data-chatbot-sugerencias]", chatbot);
        var textoChat = buscarElemento("[data-chatbot-texto]", chatbot);
        var modoChat = buscarElemento("[data-chatbot-modo]", chatbot);
        var chatCargado = false;
        var chatEnviando = false;

        // Agrega una burbuja a la conversacion y baja hasta ella.
        var agregarMensajeChat = function (emisor, texto, clase) {
            var burbuja = document.createElement("div");
            burbuja.className = "chatbot-mensaje chatbot-mensaje-"
                + (emisor === "Usuario" ? "usuario" : "bot") + (clase ? " " + clase : "");
            burbuja.textContent = texto;
            listaChat.appendChild(burbuja);
            listaChat.scrollTop = listaChat.scrollHeight;
            return burbuja;
        };

        var saludarChat = function () {
            listaChat.innerHTML = "";
            agregarMensajeChat("Chatbot", "¡Hola! Soy Ducky, el asistente de la biblioteca. "
                + "Elige una de las preguntas de abajo o escribe la tuya.");
        };

        var mostrarModoChat = function (modo) {
            modoChat.textContent = modo === "ia"
                ? "Asistente con IA"
                : "Respuestas básicas (sin IA)";
        };

        // Manda la pregunta y muestra la respuesta.
        var enviarPreguntaChat = function (texto) {
            texto = (texto || "").trim();
            if (!texto || chatEnviando) {
                return;
            }
            chatEnviando = true;
            agregarMensajeChat("Usuario", texto);
            textoChat.value = "";
            var pensando = agregarMensajeChat("Chatbot", "Ducky está pensando…",
                "chatbot-pensando");
            fetch(chatbot.dataset.urlMensajes, {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-Requested-With": "fetch" },
                credentials: "same-origin",
                body: JSON.stringify({ mensaje: texto })
            })
                .then(function (respuesta) {
                    if (respuesta.redirected || respuesta.status === 401
                        || respuesta.status === 403) {
                        throw { mensaje: "Tu sesión terminó. Vuelve a iniciar sesión." };
                    }
                    return respuesta.json().then(function (datos) {
                        if (!respuesta.ok) {
                            throw { mensaje: datos.mensaje };
                        }
                        pensando.remove();
                        agregarMensajeChat("Chatbot", datos.respuesta);
                        mostrarModoChat(datos.modo);
                        if (datos.aviso) {
                            mostrarAviso("advertencia", datos.aviso);
                        }
                    });
                })
                .catch(function (problema) {
                    pensando.remove();
                    agregarMensajeChat("Chatbot", (problema && problema.mensaje)
                        || "No pude responder. Revisa tu conexión e intenta de nuevo.",
                        "chatbot-mensaje-error");
                })
                .finally(function () {
                    chatEnviando = false;
                    textoChat.focus();
                });
        };

        // Preguntas por defecto como botones.
        var pintarSugerenciasChat = function (preguntas) {
            sugerenciasChat.innerHTML = "";
            preguntas.forEach(function (pregunta) {
                var chip = document.createElement("button");
                chip.type = "button";
                chip.className = "chatbot-sugerencia";
                chip.textContent = pregunta;
                chip.addEventListener("click", function () {
                    enviarPreguntaChat(pregunta);
                });
                sugerenciasChat.appendChild(chip);
            });
        };

        // Carga la conversacion abierta (si la hay) la primera vez que se abre.
        var cargarChat = function () {
            chatCargado = true;
            saludarChat();
            fetch(chatbot.dataset.urlMensajes, {
                headers: { "X-Requested-With": "fetch" },
                credentials: "same-origin"
            })
                .then(function (respuesta) {
                    return respuesta.json();
                })
                .then(function (datos) {
                    datos.mensajes.forEach(function (mensaje) {
                        agregarMensajeChat(mensaje.emisor, mensaje.mensaje);
                    });
                    mostrarModoChat(datos.modo);
                    pintarSugerenciasChat(datos.sugerencias);
                })
                .catch(function () {
                    chatCargado = false;
                });
        };

        // Abre o cierra la ventana y recuerda si quedo abierta al cambiar de pagina.
        var abrirChat = function (abrir) {
            panelChat.hidden = !abrir;
            chatbot.classList.toggle("abierto", abrir);
            botonChat.setAttribute("aria-expanded", String(abrir));
            try {
                sessionStorage.setItem("chatbotAbierto", abrir ? "1" : "0");
            } catch (error) {
                // Sin almacenamiento solo no se recuerda.
            }
            if (abrir) {
                if (!chatCargado) {
                    cargarChat();
                }
                textoChat.focus();
            } else {
                botonChat.focus();
            }
        };

        botonChat.addEventListener("click", function () {
            abrirChat(true);
        });
        buscarElemento("[data-chatbot-cerrar]", chatbot).addEventListener("click", function () {
            abrirChat(false);
        });
        buscarElemento("[data-chatbot-nueva]", chatbot).addEventListener("click", function () {
            fetch(chatbot.dataset.urlNueva, {
                method: "POST",
                headers: { "X-Requested-With": "fetch" },
                credentials: "same-origin"
            }).finally(saludarChat);
        });
        buscarElemento("[data-chatbot-formulario]", chatbot).addEventListener("submit",
            function (evento) {
                evento.preventDefault();
                enviarPreguntaChat(textoChat.value);
            });
        // Enter manda la pregunta; Shift+Enter hace un salto de linea.
        textoChat.addEventListener("keydown", function (evento) {
            if (evento.key === "Enter" && !evento.shiftKey) {
                evento.preventDefault();
                enviarPreguntaChat(textoChat.value);
            }
        });
        panelChat.addEventListener("keydown", function (evento) {
            if (evento.key === "Escape") {
                abrirChat(false);
            }
        });
        try {
            if (sessionStorage.getItem("chatbotAbierto") === "1") {
                abrirChat(true);
            }
        } catch (error) {
            // Sin almacenamiento el chat empieza cerrado.
        }
    }

    // Funciones disponibles para otras paginas.
    window.Syntra = {
        mostrarAviso: mostrarAviso,
        abrirModal: abrirModal,
        cerrarModal: cerrarModal
    };
})();
