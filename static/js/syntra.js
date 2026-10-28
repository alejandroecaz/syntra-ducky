(function () {
  "use strict";

  var $ = function (sel, ctx) { return (ctx || document).querySelector(sel); };
  var $$ = function (sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); };

  var ICONOS = {
    success: '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/>',
    error: '<circle cx="12" cy="12" r="10"/><path d="M12 8v4"/><path d="M12 16h.01"/>',
    warning: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    info: '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>'
  };

  function svg(trazo, tam) {
    return '<svg class="icon" width="' + (tam || 20) + '" height="' + (tam || 20) + '" viewBox="0 0 24 24" fill="none" ' +
      'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + trazo + "</svg>";
  }

  function escapar(texto) {
    var div = document.createElement("div");
    div.textContent = texto;
    return div.innerHTML;
  }

  /* Toasts */
  var TITULOS = { success: "Listo", error: "No se pudo completar", warning: "Atención", info: "Aviso" };

  function cerrarToast(toast) {
    if (!toast || toast.classList.contains("is-leaving")) return;
    toast.classList.add("is-leaving");
    setTimeout(function () { toast.remove(); }, 250);
  }

  function programarCierre(toast) {
    var tiempo = toast.classList.contains("toast--error") ? 9000 : 6000;
    setTimeout(function () { cerrarToast(toast); }, tiempo);
  }

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

  $$(".toast").forEach(programarCierre);
  document.addEventListener("click", function (e) {
    var boton = e.target.closest(".toast__close");
    if (boton) cerrarToast(boton.closest(".toast"));
  });

  /* Modales */
  var ultimoFoco = null;

  function abrirModal(modal) {
    if (!modal) return;
    ultimoFoco = document.activeElement;
    modal.classList.add("is-open");
    document.body.classList.add("modal-open");
    var foco = modal.querySelector("[data-autofocus]") || modal.querySelector("button, input, select, textarea");
    if (foco) setTimeout(function () { foco.focus(); }, 30);
  }

  function cerrarModal(modal, cancelado) {
    if (!modal || !modal.classList.contains("is-open")) return;
    modal.classList.remove("is-open");
    if (!$(".modal.is-open")) document.body.classList.remove("modal-open");
    if (ultimoFoco) ultimoFoco.focus();
    if (cancelado && modal.dataset.cancelMessage) toast("info", modal.dataset.cancelMessage, "Operación cancelada");
  }

  document.addEventListener("click", function (e) {
    var abrir = e.target.closest("[data-modal-open]");
    if (abrir) { e.preventDefault(); abrirModal(document.getElementById(abrir.dataset.modalOpen)); return; }
    var cerrar = e.target.closest("[data-modal-close]");
    if (cerrar) { e.preventDefault(); cerrarModal(cerrar.closest(".modal"), true); }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      var abierto = $$(".modal.is-open").pop();
      if (abierto) cerrarModal(abierto, true);
      $$(".menu.is-open").forEach(function (m) { m.classList.remove("is-open"); });
    }
  });

  /* Confirmacion para botones con data-confirm */
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
    var campos = d.confirmFields ? JSON.parse(d.confirmFields) : {};
    Object.keys(campos).forEach(function (nombre) {
      var input = document.createElement("input");
      input.type = "hidden"; input.name = nombre; input.value = campos[nombre];
      $(".confirm-fields", form).appendChild(input);
    });
    modal.dataset.cancelMessage = d.confirmCancel || "No se realizaron cambios.";
    abrirModal(modal);
  });

  /* Boton en modo carga al enviar formularios */
  document.addEventListener("submit", function (e) {
    var boton = e.submitter || $("[type=submit]", e.target);
    if (boton && !e.defaultPrevented) {
      setTimeout(function () { boton.classList.add("is-loading"); }, 0);
    }
    var form = e.target;
    if (form.hasAttribute("data-track-changes")) form.dataset.enviando = "1";
  });

  /* Avisar si hay cambios sin guardar */
  $$("form[data-track-changes]").forEach(function (form) {
    var inicial = new URLSearchParams(new FormData(form)).toString();
    form.estaModificado = function () { return new URLSearchParams(new FormData(form)).toString() !== inicial; };
  });

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

  /* Mostrar / ocultar contraseña */
  document.addEventListener("click", function (e) {
    var boton = e.target.closest("[data-toggle-password]");
    if (!boton) return;
    var input = document.getElementById(boton.dataset.togglePassword);
    var visible = input.type === "text";
    input.type = visible ? "password" : "text";
    boton.setAttribute("aria-label", visible ? "Mostrar contraseña" : "Ocultar contraseña");
    boton.setAttribute("aria-pressed", String(!visible));
  });

  /* Filas clicables */
  document.addEventListener("click", function (e) {
    var fila = e.target.closest("tr[data-href]");
    if (!fila || e.target.closest("a, button, form, input, select")) return;
    window.location.href = fila.dataset.href;
  });

  /* Menu movil y menu de usuario */
  var sidebar = $(".sidebar");
  var overlay = $(".overlay");
  function alternarSidebar(abrir) {
    if (!sidebar) return;
    sidebar.classList.toggle("is-open", abrir);
    overlay.classList.toggle("is-open", abrir);
  }
  document.addEventListener("click", function (e) {
    if (e.target.closest("[data-sidebar-toggle]")) alternarSidebar(!sidebar.classList.contains("is-open"));
    else if (e.target.closest(".overlay")) alternarSidebar(false);

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

  /* Generar PDF */
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

  /* Abrir la ventana de impresion */
  if ($("[data-auto-print]")) setTimeout(function () { window.print(); }, 600);
  document.addEventListener("click", function (e) {
    if (e.target.closest("[data-print]")) { e.preventDefault(); window.print(); }
  });

  /* Llenar el modal para editar un ejemplar */
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

  /* Renglones de la orden de compra */
  var contenedor = $("[data-order-rows]");
  if (contenedor) {
    var plantilla = document.getElementById("plantilla-renglon");

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

  /* Libros marcados en el listado para imprimir o generar el PDF */
  var casillasLibro = $$("[data-seleccion-libro]");
  if (casillasLibro.length) {
    var todos = $("[data-seleccion-todos]");
    var resumen = $("[data-seleccion-resumen]");

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

  window.Syntra = { toast: toast, abrirModal: abrirModal, cerrarModal: cerrarModal };
})();
