"""
============================================================
Archivo:      app.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Punto de entrada: crea la aplicacion Flask y registra los
    controladores (blueprints).

    Ejecutar:
        venv/bin/python app.py

    Al arrancar imprime la direccion para abrir el portal movil desde el
    celular.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
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
from services.catalogo_servicio import obtener_estado_libro
from utils.iconos import dibujar_icono
from utils.seguridad import obtener_usuario_actual, verificar_permiso

# Un blueprint por modulo de la web, mas el del portal movil.
BLUEPRINTS = (
    auth_bp,
    inicio_bp,
    usuario_bp,
    perfil_bp,
    catalogo_bp,
    reporte_bp,
    compra_bp,
    cuenta_bp,
    movil_bp,
)


def formatear_fecha(valor, formato="%d/%m/%Y"):
    """
    Descripcion:
        Filtro de Jinja para mostrar las fechas como dd/mm/aaaa. SQLite regresa
        las fechas como texto, por eso se prueban los dos formatos que usa.

    Parametros:
        valor (str, datetime o None): fecha a mostrar.
        formato (str): formato de salida de strftime.

    Salida:
        str: la fecha con formato, un guion si no hay fecha o el texto tal cual
        si no se reconoce.
    """
    # Sin fecha se muestra un guion.
    if not valor:
        return "—"

    # SQLite regresa las fechas como texto: probamos los dos formatos que usa.
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
    """
    Descripcion:
        Crea la base de datos si no existe y revisa que tenga el esquema
        vigente.

    Parametros:
        ruta (str): ruta del archivo SQLite.

    Salida:
        Ninguna.

    Excepciones:
        RuntimeError si la base de datos es del esquema anterior; hay que
        correr init_db.py.
    """
    if not os.path.exists(ruta):
        init_db.inicializar(ruta)
    elif not init_db.verificar_esquema_vigente(ruta):
        raise RuntimeError(
            "La base de datos syntra.db tiene el esquema anterior. Ejecuta "
            "primero: venv/bin/python init_db.py"
        )


def crear_aplicacion(configuracion=None):
    """
    Descripcion:
        Application factory: crea la app Flask con las carpetas del MVC,
        registra los controladores, los globales de las plantillas y las
        paginas de error. En las pruebas se pasa otra RUTA_BASE_DATOS.

    Parametros:
        configuracion (dict o None): valores que reemplazan la configuracion,
            por ejemplo RUTA_BASE_DATOS.

    Salida:
        flask.Flask: la aplicacion lista para usarse.

    Excepciones:
        RuntimeError si la base de datos es del esquema anterior.
    """
    # Creamos la aplicacion con las carpetas del MVC y su configuracion.
    app = Flask(__name__, template_folder="views", static_folder="static")
    app.secret_key = config.CLAVE_SECRETA
    app.config["RUTA_BASE_DATOS"] = config.RUTA_BASE_DATOS
    app.config.update(configuracion or {})

    # Revisamos que la base de datos exista y tenga el esquema vigente.
    preparar_base_de_datos(app.config["RUTA_BASE_DATOS"])

    # Registramos los controladores y el cierre de la conexion al terminar cada
    # peticion.
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)

    app.teardown_appcontext(cerrar_conexion)

    # Para poder usarlas en las plantillas.
    app.jinja_env.globals.update(
        dibujar_icono=dibujar_icono,
        verificar_permiso=verificar_permiso,
        obtener_usuario_actual=obtener_usuario_actual,
        obtener_estado_libro=obtener_estado_libro,
        # se llama cfg porque "config" ya lo usa Flask.
        cfg=config,
    )
    app.jinja_env.filters["formatear_fecha"] = formatear_fecha

    @app.errorhandler(403)
    def mostrar_acceso_no_autorizado(_error):
        """
        Descripcion:
            Criterio Acceso sin autorizacion de todas las HU: hay sesion pero
            falta el permiso.

        Parametros:
            _error (Exception): error 403 (no se usa).

        Salida:
            tuple[str, int]: pagina errores/403.html y 403.
        """
        return render_template("errores/403.html"), 403

    @app.errorhandler(404)
    def mostrar_no_encontrado(_error):
        """
        Descripcion:
            Muestra la pagina de registro o pagina inexistente.

        Parametros:
            _error (Exception): error 404 (no se usa).

        Salida:
            tuple[str, int]: pagina errores/404.html y 404.
        """
        return render_template("errores/404.html"), 404

    # Nunca se muestra la traza del error al usuario.
    @app.errorhandler(500)
    def mostrar_error_interno(_error):
        """
        Descripcion:
            Muestra un mensaje amable ante un error inesperado; nunca se ensena
            la traza al usuario.

        Parametros:
            _error (Exception): error 500 (no se usa).

        Salida:
            tuple[str, int]: pagina errores/500.html y 500.
        """
        return render_template("errores/500.html"), 500

    return app


def obtener_ip_local():
    """
    Descripcion:
        Obtiene la IP de la computadora en la red local, la que usa el celular
        para abrir el portal movil. No envia datos; solo pregunta que interfaz
        usaria para salir a internet.

    Parametros:
        Ninguno.

    Salida:
        str: IP local, o 127.0.0.1 si no hay red.
    """
    conexion = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # No envia nada; solo pregunta que interfaz usaria para salir a
        # internet.
        conexion.connect(("8.8.8.8", 80))
        return conexion.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        conexion.close()


if __name__ == "__main__":
    # Creamos la app; si la BD es del esquema anterior se explica que correr.
    try:
        app = crear_aplicacion()
    except RuntimeError as error:
        raise SystemExit(str(error)) from None

    # Imprimimos las direcciones para la web y para el celular.
    print()
    print(f"  Web (esta computadora):  http://127.0.0.1:{config.PUERTO}")
    print(
        "  Portal móvil (celular):  "
        f"http://{obtener_ip_local()}:{config.PUERTO}/movil"
    )
    print("  El celular debe estar en la misma red WiFi que esta computadora.")
    print()

    # Corremos el servidor.
    app.run(host=config.DIRECCION_SERVIDOR, port=config.PUERTO, debug=False)
