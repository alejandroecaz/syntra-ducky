# ============================================================
# Archivo: app.py
# Proyecto: Sistema Ducky de Gestión Bibliotecaria
# Syntra Technologies - Equipo 1 - Sprint 1
# Materia: Ingeniería de Software
# Autores:
#   - Melissa Silva Vázquez                #624352
#   - Tomás Zapata Pérez                   #629048
#   - Alejandro Evaristo Cazares Escobedo  #626337
# Descripción: Punto de entrada: crea la aplicación Flask y registra los controladores (blueprints).
# ============================================================
"""Punto de entrada: crea la aplicación Flask y registra los controladores (blueprints).

Ejecutar:  venv/bin/python app.py
Al arrancar imprime la dirección para abrir el portal móvil desde el celular.
"""
import os
import socket
from datetime import datetime

from flask import Flask, render_template

import config
import init_db
from controllers.auth_controller import auth_bp
from controllers.catalogo_controller import catalogo_bp
from controllers.compra_controller import compra_bp
from controllers.cuenta_controller import cuenta_bp
from controllers.inicio_controller import inicio_bp
from controllers.movil_controller import movil_bp
from controllers.perfil_controller import perfil_bp
from controllers.reporte_controller import reporte_bp
from controllers.usuario_controller import usuario_bp
from models.db import cerrar_conexion
from services.catalogo_servicio import estado_libro
from utils.iconos import icon
from utils.seguridad import tiene_permiso, usuario_actual

# Un blueprint por módulo de la web, más el del portal móvil
BLUEPRINTS = (auth_bp, inicio_bp, usuario_bp, perfil_bp, catalogo_bp, reporte_bp, compra_bp, cuenta_bp, movil_bp)


def fecha(valor, formato="%d/%m/%Y"):
    """Filtro de Jinja para mostrar las fechas como dd/mm/aaaa."""
    # Sin fecha se muestra un guion
    if not valor:
        return "—"

    # SQLite regresa las fechas como texto: probamos los dos formatos que usa
    if isinstance(valor, str):
        for patron in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                valor = datetime.strptime(valor, patron)
                break
            except ValueError:
                continue
        else:
            return valor
    return valor.strftime(formato)


def preparar_base_de_datos(ruta):
    """Crea la BD si no existe; si es del esquema anterior pide correr init_db.py."""
    if not os.path.exists(ruta):
        init_db.inicializar(ruta)
    elif not init_db.esquema_vigente(ruta):
        raise RuntimeError(
            "La base de datos syntra.db tiene el esquema anterior. Ejecuta primero: venv/bin/python init_db.py"
        )


def crear_aplicacion(configuracion=None):
    """Application factory. En las pruebas se pasa otra DATABASE_PATH."""
    # Creamos la aplicación con las carpetas del MVC y su configuración
    app = Flask(__name__, template_folder="views", static_folder="static")
    app.secret_key = config.SECRET_KEY
    app.config["DATABASE_PATH"] = config.DATABASE_PATH
    app.config.update(configuracion or {})

    # Revisamos que la base de datos exista y tenga el esquema vigente
    preparar_base_de_datos(app.config["DATABASE_PATH"])

    # Registramos los controladores y el cierre de la conexión al terminar cada petición
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)

    app.teardown_appcontext(cerrar_conexion)

    # Para poder usarlas en las plantillas
    app.jinja_env.globals.update(
        icon=icon,
        tiene_permiso=tiene_permiso,
        usuario_actual=usuario_actual,
        estado_libro=estado_libro,
        # se llama cfg porque "config" ya lo usa Flask
        cfg=config,
    )
    app.jinja_env.filters["fecha"] = fecha

    @app.errorhandler(403)
    def acceso_no_autorizado(_error):
        """Criterio "Acceso sin autorización" de todas las HU: hay sesión pero falta el permiso."""
        return render_template("errores/403.html"), 403

    @app.errorhandler(404)
    def no_encontrado(_error):
        """Registro o página inexistente."""
        return render_template("errores/404.html"), 404

    # Nunca se muestra la traza del error al usuario
    @app.errorhandler(500)
    def error_interno(_error):
        """Error inesperado con un mensaje amable."""
        return render_template("errores/500.html"), 500

    return app


def ip_local():
    """IP de la Mac en la red local (la que usa el celular para conectarse)."""
    conexion = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # No envía nada; solo pregunta qué interfaz usaría para salir a internet
        conexion.connect(("8.8.8.8", 80))
        return conexion.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        conexion.close()


if __name__ == "__main__":
    # Creamos la app; si la BD es del esquema anterior se explica qué correr
    try:
        app = crear_aplicacion()
    except RuntimeError as error:
        raise SystemExit(str(error)) from None

    # Imprimimos las direcciones para la web y para el celular
    print()
    print(f"  Web (esta computadora):  http://127.0.0.1:{config.PUERTO}")
    print(f"  Portal móvil (celular):  http://{ip_local()}:{config.PUERTO}/movil")
    print("  El celular debe estar en la misma red WiFi que esta computadora.")
    print()

    # Corremos el servidor
    app.run(host=config.HOST, port=config.PUERTO, debug=False)
