"""
============================================================
Archivo:      scripts/tomar_capturas.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Toma las capturas de pantalla de docs/capturas/ con Playwright.

    Levanta la app con una copia temporal de la base de datos (no toca
    syntra.db), recorre las pantallas web en escritorio y las del portal
    movil con tamanio de iPhone, y guarda los PNG.

    Uso (la primera vez se instalan las dependencias y Chromium):
        venv/bin/pip install -r requirements-dev.txt
        venv/bin/playwright install chromium
        venv/bin/python scripts/tomar_capturas.py

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

import logging
import os
import sys
import tempfile
import threading

from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import init_db  # noqa: E402
from app import crear_aplicacion  # noqa: E402

DESTINO = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "docs",
    "capturas",
)
ESCRITORIO = {"viewport": {"width": 1440, "height": 900}}
IPHONE = {
    "viewport": {"width": 390, "height": 844},
    "device_scale_factor": 2,
    "is_mobile": True,
    "has_touch": True,
    "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
}
# Oculta los avisos flotantes para que no tapen la pantalla.
SIN_AVISOS = ".pila-avisos { display: none !important; }"


def iniciar_servidor():
    """
    Descripcion:
        Arranca la app en un hilo con una base de datos temporal; no toca
        syntra.db.

    Parametros:
        Ninguno.

    Salida:
        tuple[werkzeug.serving.BaseWSGIServer, str]: servidor y URL base.
    """
    ruta = os.path.join(tempfile.mkdtemp(), "capturas.db")
    init_db.inicializar(ruta)
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    servidor = make_server(
        "127.0.0.1", 0, crear_aplicacion({"RUTA_BASE_DATOS": ruta})
    )
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    return servidor, f"http://127.0.0.1:{servidor.server_port}"


def capturar(pagina, nombre, completa=False):
    """
    Descripcion:
        Oculta los avisos flotantes y guarda la captura de la pagina en
        docs/capturas/.

    Parametros:
        pagina (playwright.sync_api.Page): pagina del navegador.
        nombre (str): nombre del archivo PNG.
        completa (bool): True para capturar la pagina completa.

    Salida:
        Ninguna.
    """
    pagina.add_style_tag(content=SIN_AVISOS)
    pagina.wait_for_load_state("networkidle")
    pagina.screenshot(path=os.path.join(DESTINO, nombre), full_page=completa)
    print("  ", nombre)


def entrar(pagina, base, ruta, cuenta, contrasena):
    """
    Descripcion:
        Inicia sesion desde el formulario de la ruta indicada (web o movil).

    Parametros:
        pagina (playwright.sync_api.Page): pagina del navegador.
        base (str): URL base.
        ruta (str): ruta del login.
        cuenta (str): cuenta.
        contrasena (str): contrasena.

    Salida:
        Ninguna.
    """
    pagina.goto(base + ruta)
    pagina.fill("#cuenta", cuenta)
    pagina.fill("#contrasena", contrasena)
    pagina.click("button[type=submit]")
    pagina.wait_for_load_state("networkidle")


def tomar_capturas_web(navegador, base):
    """
    Descripcion:
        Toma las capturas de las pantallas web: login, inicio, busqueda, ficha,
        perfiles y listado.

    Parametros:
        navegador (playwright.sync_api.Browser): navegador abierto.
        base (str): URL base.

    Salida:
        Ninguna.
    """
    pagina = navegador.new_context(**ESCRITORIO).new_page()
    pagina.goto(base + "/login")
    capturar(pagina, "01-login-web.png")
    entrar(pagina, base, "/login", "admin", "Admin123")
    capturar(pagina, "02-inicio-web.png")
    pagina.goto(base + "/catalogo?buscar=1&campo=autor&q=garcia%20marquez")
    capturar(pagina, "03-busqueda-web.png")
    pagina.goto(base + "/catalogo?buscar=1&campo=clave&q=LIB-001")
    pagina.click("text=Ver ejemplares")
    capturar(pagina, "04-ficha-libro-web.png", completa=True)
    pagina.goto(base + "/perfiles")
    capturar(pagina, "05-perfiles-permisos-web.png")
    pagina.goto(base + "/reportes/libros")
    pagina.uncheck("[data-seleccion-todos]")
    for casilla in pagina.locator("[data-seleccion-libro]").all()[:3]:
        casilla.check()
    capturar(pagina, "14-listado-seleccion-web.png")


def tomar_capturas_movil(navegador, base):
    """
    Descripcion:
        Toma las capturas del portal movil con tamanio de iPhone.

    Parametros:
        navegador (playwright.sync_api.Browser): navegador abierto.
        base (str): URL base.

    Salida:
        Ninguna.
    """
    pagina = navegador.new_context(**IPHONE).new_page()
    pagina.goto(base + "/movil/login")
    capturar(pagina, "06-login-movil.png")
    entrar(pagina, base, "/movil/login", "profesor", "Profe123")
    capturar(pagina, "07-solo-alumnos-movil.png")
    entrar(pagina, base, "/movil/login", "alumno", "Alumno123")
    capturar(pagina, "08-busqueda-movil.png")
    pagina.check("input[name=campo][value=autor]", force=True)
    pagina.fill("#q", "kernighan")
    pagina.click("button[type=submit]")
    capturar(pagina, "09-resultados-movil.png")
    pagina.goto(base + "/movil?buscar=1&campo=titulo&q=zzz")
    capturar(pagina, "10-sin-resultados-movil.png")
    pagina.goto(base + "/movil?buscar=1&campo=titulo&q=")
    capturar(pagina, "11-busqueda-vacia-movil.png")
    pagina.goto(base + "/movil?buscar=1&campo=titulo&q=paramo")
    pagina.click(".m-libro")
    capturar(pagina, "12-ficha-movil.png", completa=True)
    pagina.locator("text=Ver ubicación").last.click()
    pagina.wait_for_timeout(400)
    capturar(pagina, "13-ubicacion-movil.png")


def ejecutar():
    """
    Descripcion:
        Arranca el servidor, toma todas las capturas y lo detiene.

    Parametros:
        Ninguno.

    Salida:
        Ninguna.

    Excepciones:
        playwright.sync_api.Error si no esta instalado Chromium.
    """
    os.makedirs(DESTINO, exist_ok=True)
    servidor, base = iniciar_servidor()
    print("Guardando capturas en", DESTINO)
    with sync_playwright() as playwright:
        navegador = playwright.chromium.launch()
        tomar_capturas_web(navegador, base)
        tomar_capturas_movil(navegador, base)
        navegador.close()
    servidor.shutdown()


if __name__ == "__main__":
    ejecutar()
