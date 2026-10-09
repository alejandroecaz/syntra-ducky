import os
from datetime import datetime

from flask import Flask, render_template

import config
import init_db
from controllers.auth_controller import auth_bp
from controllers.catalogo_controller import catalogo_bp
from controllers.compra_controller import compra_bp
from controllers.cuenta_controller import cuenta_bp
from controllers.inicio_controller import inicio_bp
from controllers.perfil_controller import perfil_bp
from controllers.reporte_controller import reporte_bp
from controllers.usuario_controller import usuario_bp
from models.db import cerrar_conexion
from utils.iconos import icon
from utils.pdf import estado_libro
from utils.seguridad import tiene_permiso, usuario_actual


def fecha(valor, formato="%d/%m/%Y"):
    # Filtro para mostrar las fechas como dd/mm/aaaa
    if not valor:
        return "—"
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


def crear_aplicacion():
    app = Flask(__name__, template_folder="views", static_folder="static")
    app.secret_key = config.SECRET_KEY

    # Si no hay base de datos se crea con datos de prueba
    if not os.path.exists(config.DATABASE_PATH):
        init_db.inicializar()

    for blueprint in (auth_bp, inicio_bp, usuario_bp, perfil_bp, catalogo_bp,
                      reporte_bp, compra_bp, cuenta_bp):
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
        return render_template("errores/403.html"), 403

    @app.errorhandler(404)
    def no_encontrado(_error):
        return render_template("errores/404.html"), 404

    return app


app = crear_aplicacion()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)
