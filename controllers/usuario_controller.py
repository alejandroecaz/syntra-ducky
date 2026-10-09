from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from models import perfil as perfil_modelo
from models import usuario as usuario_modelo
from utils.seguridad import permiso_requerido

usuario_bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


def _usuario_o_404(usuario_id):
    usuario = usuario_modelo.obtener_por_id(usuario_id)
    if usuario is None:
        abort(404)
    return usuario


# HU-01-05: consulta de usuarios

@usuario_bp.route("")
@permiso_requerido("usuarios.consultar")
def lista():
    criterio = request.args.get("criterio", "nombre")
    texto = request.args.get("q", "").strip()
    buscando = "buscar" in request.args
    error_busqueda = None

    if buscando and not texto:
        error_busqueda = "Captura un identificador o un nombre para buscar."
        usuarios = []
    elif buscando:
        usuarios = usuario_modelo.buscar(criterio, texto)
    else:
        usuarios = usuario_modelo.listar()

    return render_template(
        "usuarios/lista.html",
        usuarios=usuarios,
        criterio=criterio,
        texto=texto,
        buscando=buscando,
        error_busqueda=error_busqueda,
        resaltar=request.args.get("resaltar", type=int),
    )


@usuario_bp.route("/<int:usuario_id>")
@permiso_requerido("usuarios.consultar")
def detalle(usuario_id):
    usuario = _usuario_o_404(usuario_id)
    permisos = perfil_modelo.permisos_de(usuario["perfil_id"]) if usuario["perfil_id"] else []
    return render_template("usuarios/detalle.html", usuario=usuario, permisos=permisos)


# HU-01-02: registro de usuarios

@usuario_bp.route("/nuevo", methods=["GET", "POST"])
@permiso_requerido("usuarios.registrar")
def nuevo():
    perfiles = perfil_modelo.listar()
    if request.method == "GET":
        return render_template("usuarios/form.html", modo="nuevo", valores={}, errores={}, perfiles=perfiles)

    valores = {campo: request.form.get(campo, "").strip()
               for campo in ("identificador", "nombre", "cuenta", "perfil_id")}
    contrasena = request.form.get("contrasena", "")
    errores = {}

    etiquetas = {
        "identificador": "el identificador institucional",
        "nombre": "el nombre",
        "cuenta": "la cuenta",
        "perfil_id": "el perfil de usuario",
    }
    for campo, etiqueta in etiquetas.items():
        if not valores[campo]:
            errores[campo] = f"Captura {etiqueta}." if campo != "perfil_id" else "Selecciona un perfil de usuario."
    if not contrasena:
        errores["contrasena"] = "Captura la contraseña inicial."
    elif len(contrasena) < 6:
        errores["contrasena"] = "La contraseña debe tener al menos 6 caracteres."

    duplicados = []
    if valores["identificador"] and usuario_modelo.existe_identificador(valores["identificador"]):
        errores["identificador"] = f"El identificador {valores['identificador']} ya está registrado."
        duplicados.append(f"identificador {valores['identificador']}")
    if valores["cuenta"] and usuario_modelo.cuenta_en_uso(valores["cuenta"]):
        errores["cuenta"] = f"La cuenta {valores['cuenta']} ya está registrada."
        duplicados.append(f"cuenta {valores['cuenta']}")

    perfil = None
    if valores["perfil_id"] and "perfil_id" not in errores:
        perfil = perfil_modelo.obtener_por_id(valores["perfil_id"])
        if perfil is None or not perfil["disponible"]:
            errores["perfil_id"] = "El perfil seleccionado no está disponible."

    if errores:
        if duplicados:
            mensaje = "Ya existe un usuario con " + " y ".join(duplicados) + ". No se creó ningún registro."
        else:
            mensaje = "Revisa los campos marcados. El usuario no se registró."
        return render_template(
            "usuarios/form.html", modo="nuevo", valores=valores, errores=errores,
            perfiles=perfiles, error_general=mensaje,
        ), 400

    nuevo_id = usuario_modelo.crear(
        valores["identificador"], valores["nombre"], valores["cuenta"], contrasena, perfil["id"]
    )
    flash(f"Usuario registrado: {valores['nombre']} ({valores['identificador']}) con perfil {perfil['nombre']}.",
          "success")
    return redirect(url_for("usuarios.lista", resaltar=nuevo_id))


# HU-01-04: actualizar datos

@usuario_bp.route("/<int:usuario_id>/editar", methods=["GET", "POST"])
@permiso_requerido("usuarios.editar")
def editar(usuario_id):
    usuario = _usuario_o_404(usuario_id)
    if request.method == "GET":
        valores = {"nombre": usuario["nombre"], "cuenta": usuario["cuenta"]}
        return render_template("usuarios/form.html", modo="editar", usuario=usuario, valores=valores, errores={})

    valores = {"nombre": request.form.get("nombre", "").strip(),
               "cuenta": request.form.get("cuenta", "").strip()}
    errores = {}
    if not valores["nombre"]:
        errores["nombre"] = "El nombre es obligatorio."
    if not valores["cuenta"]:
        errores["cuenta"] = "La cuenta es obligatoria."
    elif usuario_modelo.cuenta_en_uso(valores["cuenta"], excluir_id=usuario_id):
        errores["cuenta"] = "La cuenta ya está en uso"

    if errores:
        mensaje = ("La cuenta ya está en uso por otro usuario. Se conservan los datos guardados."
                   if errores.get("cuenta") == "La cuenta ya está en uso"
                   else "No se guardaron los cambios. Revisa los campos marcados.")
        return render_template(
            "usuarios/form.html", modo="editar", usuario=usuario, valores=valores,
            errores=errores, error_general=mensaje,
        ), 400

    usuario_modelo.actualizar_datos(usuario_id, valores["nombre"], valores["cuenta"])
    if usuario_id == session.get("usuario_id"):
        session["nombre"], session["cuenta"] = valores["nombre"], valores["cuenta"]
    flash("Datos del usuario actualizados correctamente.", "success")
    return redirect(url_for("usuarios.detalle", usuario_id=usuario_id))


# HU-01-03: habilitar / deshabilitar cuenta

@usuario_bp.route("/<int:usuario_id>/estado", methods=["POST"])
@permiso_requerido("usuarios.baja")
def cambiar_estado(usuario_id):
    usuario = _usuario_o_404(usuario_id)
    accion = request.form.get("accion")
    destino = request.form.get("volver") or url_for("usuarios.detalle", usuario_id=usuario_id)

    if accion == "deshabilitar":
        if usuario_id == session.get("usuario_id"):
            flash("No puedes deshabilitar tu propia cuenta mientras tienes la sesión iniciada.", "error")
            return redirect(destino)
        usuario_modelo.cambiar_estado(usuario_id, "Deshabilitada")
        flash(f"La cuenta de {usuario['nombre']} fue deshabilitada. Sus datos se conservan y ya no podrá "
              "iniciar sesión.", "success")
    elif accion == "habilitar":
        usuario_modelo.cambiar_estado(usuario_id, "Habilitada")
        flash(f"La cuenta de {usuario['nombre']} fue habilitada nuevamente.", "success")
    else:
        flash("Acción no reconocida. No se realizaron cambios.", "error")
    return redirect(destino)


# HU-01-08: asignar perfil

@usuario_bp.route("/<int:usuario_id>/perfil", methods=["GET", "POST"])
@permiso_requerido("perfiles.asignar")
def asignar_perfil(usuario_id):
    usuario = _usuario_o_404(usuario_id)
    perfiles = perfil_modelo.listar()
    permisos = perfil_modelo.permisos_por_perfil()

    if request.method == "GET":
        return render_template("usuarios/asignar_perfil.html", usuario=usuario, perfiles=perfiles,
                               permisos=permisos, seleccionado="", errores={})

    seleccionado = request.form.get("perfil_id", "").strip()

    def rechazar(mensaje):
        return render_template("usuarios/asignar_perfil.html", usuario=usuario, perfiles=perfiles,
                               permisos=permisos, seleccionado=seleccionado,
                               errores={"perfil_id": mensaje}, error_general=mensaje), 400

    if not seleccionado:
        return rechazar("Selecciona un perfil de usuario. Se conserva la asignación anterior.")

    perfil = perfil_modelo.obtener_por_id(seleccionado) if seleccionado.isdigit() else None
    if perfil is None or not perfil["disponible"]:
        return rechazar("El perfil de usuario no está disponible. Se conserva el perfil asignado previamente.")

    if perfil["id"] == usuario["perfil_id"]:
        flash(f"{usuario['nombre']} ya tiene asignado el perfil {perfil['nombre']}. No hubo cambios.", "info")
        return redirect(url_for("usuarios.detalle", usuario_id=usuario_id))

    usuario_modelo.asignar_perfil(usuario_id, perfil["id"])
    anterior = usuario["perfil_nombre"] or "sin perfil"
    flash(f"Perfil actualizado de {anterior} a {perfil['nombre']}. Los nuevos permisos se aplicarán en el "
          "siguiente inicio de sesión.", "success")
    return redirect(url_for("usuarios.detalle", usuario_id=usuario_id))
