/* ============================================================
   Archivo: static/js/syntra.js
   Proyecto: Sistema Ducky de Gestión Bibliotecaria
   Syntra Technologies - Equipo 1 - Sprint 1
   Materia: Ingeniería de Software
   Autores:
     - Melissa Silva Vázquez                #624352
     - Tomás Zapata Pérez                   #629048
     - Alejandro Evaristo Cazares Escobedo  #626337
   Descripción: Comportamiento de la interfaz: avisos, modales, confirmaciones, cambios sin guardar, PDF,
                impresión, orden de compra y selección de libros del listado.
   ============================================================ */
(function () {
  "use strict";

  /* === UTILIDADES === */
  // Atajos para buscar un elemento ($) o una lista de elementos ($$)
  var $ = function (sel, ctx) { return (ctx || document).querySelector(sel); };
  var $$ = function (sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); };

  // Trazos SVG de los íconos de los avisos (los mismos de utils/iconos.py)
  var ICONOS = {
    success: '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/>',
    error: '<circle cx="12" cy="12" r="10"/><path d="M12 8v4"/><path d="M12 16h.01"/>',
    warning: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>'
  };

  // Arma el SVG de un ícono con su tamaño
  function svg(trazo, tam) {
    return '<svg class="icon" width="' + (tam || 20) + '" height="' + (tam || 20) + '" viewBox="0 0 24 24" fill="none" ' +
      'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + trazo + "</svg>";
  }

  // Escapa el texto para insertarlo como HTML sin riesgo
  function escapar(texto) {
    var div = document.createElement("div");
    div.textContent = texto;
    return div.innerHTML;
  }

  /* === AVISOS FLOTANTES (TOASTS) === */
  // Título de cada tipo de aviso
  var TITULOS = { success: "Listo", error: "No se pudo completar", warning: "Atención", info: "Aviso" };

  // Cierra el aviso con animación
  function cerrarToast(toast) {
    if (!toast || toast.classList.contains("is-leaving")) return;
    toast.classList.add("is-leaving");
    setTimeout(function () { toast.remove(); }, 250);
  }

  // Los errores se quedan más tiempo en pantalla
  function programarCierre(toast) {
    var tiempo = toast.classList.contains("toast--error") ? 9000 : 6000;
    setTimeout(function () { cerrarToast(toast); }, tiempo);
  }

  // Muestra un aviso nuevo (lo usan los modales y el PDF)
  function toast(tono, mensaje, titulo) {
    var pila = $(".toast-stack");
    if (!pila) return;
    var el = document.createElement("div");
    el.className = "toast toast--" + tono;
    el.setAttribute("role", tono === "error" ? "alert" : "status");
    el.innerHTML = svg(ICONOS[tono] || ICONOS.info) +
      '<div class="toast__body"><strong class="toast__title">' + escapar(titulo || TITULOS[tono]) + "</strong>" +
      escapar(mensaje) + "</div>" +
      '<button type="button" class="toast__close" aria-label="Cerrar aviso">' +
      svg('<path d="M18 6 6 18"/><path d="m6 6 12 12"/>', 16) + "</button>";
    pila.appendChild(el);
    programarCierre(el);
  }

  // Avisos que ya vienen del servidor (mensajes flash) y botón para cerrarlos
  $$(".toast").forEach(programarCierre);
  document.addEventListener("click", function (e) {
    var boton = e.target.closest(".toast__close");
    if (boton) cerrarToast(boton.closest(".toast"));
  });

  /* === MODALES === */
  // Elemento que tenía el foco antes de abrir el modal, para regresarlo al cerrar
  var ultimoFoco = null;

  // Abre el modal y pone el foco en su primer control
  function abrirModal(modal) {
    if (!modal) return;
    ultimoFoco = document.activeElement;
    modal.classList.add("is-open");
    document.body.classList.add("modal-open");
    var foco = modal.querySelector("[data-autofocus]") || modal.querySelector("button, input, select, textarea");
    if (foco) setTimeout(function () { foco.focus(); }, 30);
  }

  // Cierra el modal; si fue cancelado avisa que no hubo cambios
  function cerrarModal(modal, cancelado) {
    if (!modal || !modal.classList.contains("is-open")) return;
    modal.classList.remove("is-open");
    if (!$(".modal.is-open")) document.body.classList.remove("modal-open");
    if (ultimoFoco) ultimoFoco.focus();
    if (cancelado && modal.dataset.cancelMessage) toast("info", modal.dataset.cancelMessage, "Operación cancelada");
  }

  // Botones que abren (data-modal-open) o cierran (data-modal-close) un modal
  document.addEventListener("click", function (e) {
    var abrir = e.target.closest("[data-modal-open]");
    if (abrir) { e.preventDefault(); abrirModal(document.getElementById(abrir.dataset.modalOpen)); return; }
    var cerrar = e.target.closest("[data-modal-close]");
    if (cerrar) { e.preventDefault(); cerrarModal(cerrar.closest(".modal"), true); }
  });

  // Escape cierra el modal abierto y los menús
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      var abierto = $$(".modal.is-open").pop();
      if (abierto) cerrarModal(abierto, true);
      $$(".menu.is-open").forEach(function (m) { m.classList.remove("is-open"); });
    }
  });

  /* === CONFIRMACIÓN (HU-01-03 Y HU-01-10) === */
  // Botones con data-confirm: deshabilitar cuenta, dar de baja un libro... Cancelar no cambia nada
  document.addEventListener("click", function (e) {
    var disparador = e.target.closest("[data-confirm]");
    if (!disparador) return;
    e.preventDefault();
    var modal = document.getElementById("modal-confirm");
    var d = disparador.dataset;
    var tono = d.confirmTone || "danger";
    $("[data-confirm-title]", modal).textContent = d.confirmTitle || "¿Confirmas la operación?";
    $("[data-confirm-text]", modal).textContent = d.confirmText || "";
    var icono = $("[data-confirm-icon]", modal);
    icono.className = "modal__icon modal__icon--" + tono;
    icono.innerHTML = svg(tono === "danger" ? ICONOS.warning : ICONOS.info, 22);
    var aceptar = $("[data-confirm-accept]", modal);
    aceptar.textContent = d.confirmLabel || "Confirmar";
    aceptar.className = "btn " + (tono === "danger" ? "btn--danger" : "btn--primary");
    var form = $("form", modal);
    form.action = d.confirmAction;
    $(".confirm-fields", form).innerHTML = "";
    // Campos ocultos que se mandan con la confirmación (por ejemplo la acción)
    var campos = d.confirmFields ? JSON.parse(d.confirmFields) : {};
    Object.keys(campos).forEach(function (nombre) {
      var input = document.createElement("input");
      input.type = "hidden"; input.name = nombre; input.value = campos[nombre];
      $(".confirm-fields", form).appendChild(input);
    });
    modal.dataset.cancelMessage = d.confirmCancel || "No se realizaron cambios.";
    abrirModal(modal);
  });

  /* === BOTÓN EN MODO CARGA === */
  // Al enviar un formulario el botón muestra que está procesando
  document.addEventListener("submit", function (e) {
    var boton = e.submitter || $("[type=submit]", e.target);
    if (boton && !e.defaultPrevented) {
      setTimeout(function () { boton.classList.add("is-loading"); }, 0);
    }
    var form = e.target;
    if (form.hasAttribute("data-track-changes")) form.dataset.enviando = "1";
  });

  /* === CAMBIOS SIN GUARDAR (HU-01-11 · CANCELAR EDICIÓN) === */
  // Se guarda el estado inicial del formulario para saber si se modificó
  $$("form[data-track-changes]").forEach(function (form) {
    var inicial = new URLSearchParams(new FormData(form)).toString();
    form.estaModificado = function () { return new URLSearchParams(new FormData(form)).toString() !== inicial; };
  });

  // Si se cancela con cambios, se pide confirmar antes de descartarlos
  document.addEventListener("click", function (e) {
    var enlace = e.target.closest("[data-cancel-edit]");
    if (!enlace) return;
    var form = $("form[data-track-changes]");
    if (form && form.estaModificado && form.estaModificado()) {
      e.preventDefault();
      var modal = document.getElementById("modal-descartar");
      $("[data-discard-accept]", modal).href = enlace.dataset.discardHref || enlace.href;
      abrirModal(modal);
    }
  });

  /* === MOSTRAR / OCULTAR CONTRASEÑA === */
  document.addEventListener("click", function (e) {
    var boton = e.target.closest("[data-toggle-password]");
    if (!boton) return;
    var input = document.getElementById(boton.dataset.togglePassword);
    var visible = input.type === "text";
    input.type = visible ? "password" : "text";
    boton.setAttribute("aria-label", visible ? "Mostrar contraseña" : "Ocultar contraseña");
    boton.setAttribute("aria-pressed", String(!visible));
  });

  /* === FILAS CLICABLES === */
  // Las filas con data-href abren el detalle (salvo que se dé clic en un botón o enlace)
  document.addEventListener("click", function (e) {
    var fila = e.target.closest("tr[data-href]");
    if (!fila || e.target.closest("a, button, form, input, select")) return;
    window.location.href = fila.dataset.href;
  });

  /* === MENÚ LATERAL EN CELULAR Y MENÚ DEL USUARIO === */
  var sidebar = $(".sidebar");
  var overlay = $(".overlay");
  // Abre o cierra el menú lateral en pantallas chicas
  function alternarSidebar(abrir) {
    if (!sidebar) return;
    sidebar.classList.toggle("is-open", abrir);
    overlay.classList.toggle("is-open", abrir);
  }
  document.addEventListener("click", function (e) {
    if (e.target.closest("[data-sidebar-toggle]")) alternarSidebar(!sidebar.classList.contains("is-open"));
    else if (e.target.closest(".overlay")) alternarSidebar(false);

    // Menú del usuario: se cierra al dar clic fuera
    var chip = e.target.closest("[data-menu-toggle]");
    $$(".menu.is-open").forEach(function (m) {
      if (!chip || m !== document.getElementById(chip.dataset.menuToggle)) m.classList.remove("is-open");
    });
    if (chip) {
      var menu = document.getElementById(chip.dataset.menuToggle);
      menu.classList.toggle("is-open");
      chip.setAttribute("aria-expanded", String(menu.classList.contains("is-open")));
    }
  });

  /* === GENERAR PDF (HU-01-16) === */
  // Se pide el PDF con fetch para mostrar el resultado sin salir del listado
  document.addEventListener("click", function (e) {
    var boton = e.target.closest("[data-pdf-url]");
    if (!boton) return;
    e.preventDefault();
    var destino = $(boton.dataset.pdfResult);
    boton.classList.add("is-loading");
    destino.innerHTML = "";

    // Si el botón tiene un formulario asociado, manda sus datos (filtros y libros marcados)
    var url = boton.dataset.pdfUrl;
    var formPdf = boton.dataset.pdfForm && document.getElementById(boton.dataset.pdfForm);
    if (formPdf) url += (url.indexOf("?") === -1 ? "?" : "&") + new URLSearchParams(new FormData(formPdf)).toString();

    // HU-01-16 · Generación satisfactoria / Catálogo sin registros / Error durante la generación
    fetch(url, { headers: { "X-Requested-With": "fetch" }, credentials: "same-origin" })
      .then(function (resp) {
        var tipo = resp.headers.get("Content-Type") || "";
        if (resp.ok && tipo.indexOf("application/pdf") === 0) {
          var total = resp.headers.get("X-Total-Registros");
          return resp.blob().then(function (blob) {
            var url = URL.createObjectURL(blob);
            var a = document.createElement("a");
            a.href = url; a.download = "listado_libros.pdf";
            document.body.appendChild(a); a.click(); a.remove();
            destino.innerHTML = '<div class="alert alert--success" role="status">' + svg(ICONOS.success) +
              '<div class="alert__body"><strong class="alert__title">PDF generado correctamente</strong>' +
              "El documento incluye " + total + " libros con clave, título, autor, tema, editorial y estado. " +
              '<a href="' + url + '" target="_blank" rel="noopener">Abrir PDF</a> · ' +
              '<a href="' + url + '" download="listado_libros.pdf">Descargar de nuevo</a></div></div>';
            toast("success", "Se descargó el listado con " + total + " libros.", "PDF generado");
          });
        }
        if (resp.status === 401 || resp.status === 403 || resp.redirected) {
          throw { tono: "error", mensaje: "Acceso no autorizado para generar documentos." };
        }
        return resp.json().then(function (datos) {
          throw { tono: resp.status >= 500 ? "error" : "warning", mensaje: datos.mensaje };
        });
      })
      .catch(function (err) {
        var tono = err && err.tono ? err.tono : "error";
        var mensaje = err && err.mensaje ? err.mensaje : "El documento no pudo generarse. Intenta nuevamente.";
        destino.innerHTML = '<div class="alert alert--' + tono + '" role="alert">' + svg(ICONOS[tono]) +
          '<div class="alert__body"><strong class="alert__title">' +
          (tono === "error" ? "No se generó el PDF" : "Sin registros para el PDF") + "</strong>" + escapar(mensaje) + "</div></div>";
        toast(tono, mensaje);
      })
      .finally(function () { boton.classList.remove("is-loading"); });
  });

  /* === IMPRESIÓN (HU-01-17 Y HU-01-18) === */
  // Abre el diálogo de impresión al confirmar o con los botones data-print
  if ($("[data-auto-print]")) setTimeout(function () { window.print(); }, 600);
  document.addEventListener("click", function (e) {
    if (e.target.closest("[data-print]")) { e.preventDefault(); window.print(); }
  });

  /* === ACTUALIZAR EJEMPLAR (HU-01-15 · DISPONIBILIDAD ACTUALIZADA) === */
  // Llena el modal con los datos del ejemplar elegido
  document.addEventListener("click", function (e) {
    var boton = e.target.closest("[data-ejemplar]");
    if (!boton) return;
    var datos = JSON.parse(boton.dataset.ejemplar);
    var modal = document.getElementById("modal-ejemplar");
    var form = $("form", modal);
    form.action = datos.accion;
    $("[data-ejemplar-codigo]", modal).textContent = datos.codigo;
    ["estancia", "estante", "posicion", "estado"].forEach(function (campo) {
      form.elements[campo].value = datos[campo] || "";
    });
    abrirModal(modal);
  });

  /* === RENGLONES DE LA ORDEN DE COMPRA (HU-01-18) === */
  var contenedor = $("[data-order-rows]");
  if (contenedor) {
    var plantilla = document.getElementById("plantilla-renglon");

    // Recalcula renglones, títulos distintos y total de ejemplares
    var actualizarResumen = function () {
      var filas = $$(".order-row", contenedor);
      var titulos = {};
      var ejemplares = 0;
      filas.forEach(function (fila) {
        var libro = $("select", fila).value;
        var cantidad = parseInt($("input", fila).value, 10);
        if (libro && cantidad > 0) {
          titulos[libro] = true;
          ejemplares += cantidad;
        }
        $("[data-remove-row]", fila).disabled = filas.length === 1;
      });
      $("[data-sum-titulos]").textContent = Object.keys(titulos).length;
      $("[data-sum-ejemplares]").textContent = ejemplares;
      $("[data-sum-renglones]").textContent = filas.length;
    };

    // Agregar un renglón (copia de la plantilla) o quitarlo
    document.addEventListener("click", function (e) {
      if (e.target.closest("[data-add-row]")) {
        contenedor.appendChild(plantilla.content.cloneNode(true));
        var nueva = $$(".order-row", contenedor).pop();
        $("select", nueva).focus();
        actualizarResumen();
      }
      var quitar = e.target.closest("[data-remove-row]");
      if (quitar) {
        quitar.closest(".order-row").remove();
        actualizarResumen();
      }
    });
    contenedor.addEventListener("input", actualizarResumen);
    contenedor.addEventListener("change", actualizarResumen);
    actualizarResumen();
  }

  /* === SELECCIÓN DE LIBROS DEL LISTADO (HU-01-16 Y HU-01-17) === */
  // Solo los libros marcados entran al PDF y a la impresión
  var casillasLibro = $$("[data-seleccion-libro]");
  if (casillasLibro.length) {
    var todos = $("[data-seleccion-todos]");
    var resumen = $("[data-seleccion-resumen]");

    // Actualiza la casilla "todos", el resumen y habilita o deshabilita Imprimir y PDF
    var actualizarSeleccion = function () {
      var marcadas = casillasLibro.filter(function (c) { return c.checked; }).length;
      todos.checked = marcadas === casillasLibro.length;
      todos.indeterminate = marcadas > 0 && marcadas < casillasLibro.length;
      resumen.textContent = marcadas
        ? marcadas + " de " + casillasLibro.length + " seleccionados"
        : "Marca al menos un libro para imprimir o generar el PDF";
      resumen.classList.toggle("is-warning", !marcadas);
      $$("[data-requiere-seleccion]").forEach(function (b) { b.disabled = !marcadas; });
    };

    todos.addEventListener("change", function () {
      casillasLibro.forEach(function (c) { c.checked = todos.checked; });
      actualizarSeleccion();
    });
    casillasLibro.forEach(function (c) { c.addEventListener("change", actualizarSeleccion); });
    actualizarSeleccion();
  }

  // Funciones disponibles para otras páginas
  window.Syntra = { toast: toast, abrirModal: abrirModal, cerrarModal: cerrarModal };
})();
