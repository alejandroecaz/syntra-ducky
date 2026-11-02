"""
============================================================
Archivo:      services/usuario_servicio.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Servicio de usuarios: registro, consulta, actualizacion, baja logica y
    asignacion de perfil.

    Cubre HU-01-02, HU-01-03, HU-01-04, HU-01-05 y HU-01-08.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

import re

import config
from models import perfil as perfil_modelo
from models import usuario as usuario_modelo
from services.auth_servicio import cifrar_contrasena
from services.errores import ErrorValidacion

# Campos que se capturan al registrar y al editar.
CAMPOS_DATOS = (
    "nombre",
    "apellido_paterno",
    "apellido_materno",
    "cuenta",
    "email",
    "telefono",
)

# Obligatorios del registro con su etiqueta para el mensaje (HU-01-02).
OBLIGATORIOS_REGISTRO = {
    "identificador": "el identificador institucional",
    "nombre": "el nombre",
    "apellido_paterno": "el apellido paterno",
    "cuenta": "la cuenta",
}

# Criterios de la consulta de usuarios (HU-01-05); el primero es el
# predeterminado.
CRITERIOS_BUSQUEDA = ("nombre", "identificador")


def formar_nombre_completo(datos):
    """
    Descripcion:
        Forma el nombre completo, por ejemplo 'Mariana Lopez Hernandez', a
        partir de nombre y apellidos.

    Parametros:
        datos (dict): nombre, apellido_paterno y apellido_materno.

    Salida:
        str: nombre completo.
    """
    partes = [
        datos.get("nombre"),
        datos.get("apellido_paterno"),
        datos.get("apellido_materno"),
    ]
    return " ".join(parte for parte in partes if parte)


def _leer(formulario, campos):
    """
    Descripcion:
        Lee y limpia los campos indicados del formulario.

    Parametros:
        formulario (werkzeug.datastructures.MultiDict): datos capturados.
        campos (tuple[str]): nombres de los campos.

    Salida:
        dict: valor limpio de cada campo.
    """
    return {campo: (formulario.get(campo) or "").strip() for campo in campos}


def _limpiar_opcional(valor):
    """
    Descripcion:
        Convierte un campo opcional vacio en None, que se guarda como NULL.

    Parametros:
        valor (str): valor capturado.

    Salida:
        str o None.
    """
    return valor or None


def _validar_contacto(valores, errores, excluir_id=None):
    """
    Descripcion:
        Valida correo y telefono, que son opcionales, y agrega sus errores.

    Parametros:
        valores (dict): valores capturados.
        errores (dict): errores por campo (se modifica).
        excluir_id (int o None): id del usuario que se edita.

    Salida:
        bool: True si el correo ya es de otra persona.
    """
    # Correo: formato valido y que no lo tenga otra cuenta.
    duplicado = False
    if valores["email"]:
        if not re.match(config.PATRON_EMAIL, valores["email"]):
            errores["email"] = (
                "Escribe un correo válido, por ejemplo nombre@ducky.edu.mx."
            )
        elif usuario_modelo.verificar_email_en_uso(
            valores["email"], excluir_id
        ):
            errores["email"] = (
                f"El correo {valores['email']} ya está registrado."
            )
            duplicado = True

    # Telefono: solo numeros, espacios, parentesis o guiones.
    if valores["telefono"] and not re.match(
        config.PATRON_TELEFONO, valores["telefono"]
    ):
        errores["telefono"] = (
            "Escribe un teléfono válido (solo números, espacios o guiones)."
        )
    return duplicado


def _preparar_datos(valores):
    """
    Descripcion:
        Copia los valores con los campos opcionales vacios convertidos en None.

    Parametros:
        valores (dict): valores validados.

    Salida:
        dict: datos listos para guardar.
    """
    datos = dict(valores)
    for campo in ("apellido_materno", "email", "telefono"):
        datos[campo] = _limpiar_opcional(valores[campo])
    return datos


def buscar(criterio, texto, buscando):
    """
    Descripcion:
        HU-01-05: Consulta de usuarios por identificador o por nombre. Sin
        busqueda se muestran todos.

    Parametros:
        criterio (str): 'nombre' o 'identificador'.
        texto (str): texto capturado.
        buscando (bool): True si se envio el formulario de busqueda.

    Salida:
        tuple[list[sqlite3.Row], str o None]: usuarios y mensaje de error.
    """
    # Sin busqueda se muestran todos.
    if not buscando:
        return usuario_modelo.listar(), None

    # Se busco sin texto: se pide un criterio.
    if not texto:
        return [], "Captura un identificador o un nombre para buscar."

    # HU-01-05 · Consulta por identificador / Coincidencias por nombre (o
    # Consulta sin coincidencias).
    criterio = (
        criterio if criterio in CRITERIOS_BUSQUEDA else CRITERIOS_BUSQUEDA[0]
    )
    return usuario_modelo.buscar(criterio, texto), None


def obtener(usuario_id):
    """
    Descripcion:
        Busca un usuario por su id.

    Parametros:
        usuario_id (int): id del usuario.

    Salida:
        sqlite3.Row o None.
    """
    return usuario_modelo.obtener_por_id(usuario_id)


def listar_permisos(usuario):
    """
    Descripcion:
        Lista los codigos de permiso del perfil asignado a la cuenta.

    Parametros:
        usuario (sqlite3.Row): usuario.

    Salida:
        list[str]: codigos de permiso.
    """
    return (
        perfil_modelo.listar_permisos(usuario["perfil_id"])
        if usuario["perfil_id"]
        else []
    )


def listar_perfiles():
    """
    Descripcion:
        Lista los perfiles para el formulario de registro y la asignacion.

    Parametros:
        Ninguno.

    Salida:
        list[sqlite3.Row]: perfiles.
    """
    return perfil_modelo.listar()


def registrar(formulario):
    """
    Descripcion:
        HU-01-02: Registra una cuenta. La contrasena se guarda cifrada.

    Parametros:
        formulario (werkzeug.datastructures.MultiDict): datos capturados.

    Salida:
        tuple[int, str]: id del usuario y mensaje de exito.

    Excepciones:
        ErrorValidacion si faltan obligatorios, hay datos duplicados o el
        perfil no esta disponible; no se crea ningun registro.
    """
    # Leemos los campos del formulario.
    valores = _leer(formulario, ("identificador", *CAMPOS_DATOS, "perfil_id"))
    contrasena = formulario.get("contrasena", "")
    errores = {}

    # HU-01-02 · Registro incompleto: obligatorios, perfil y contrasena
    # inicial.
    for campo, etiqueta in OBLIGATORIOS_REGISTRO.items():
        if not valores[campo]:
            errores[campo] = f"Captura {etiqueta}."
    if not valores["perfil_id"]:
        errores["perfil_id"] = "Selecciona un perfil de usuario."
    if not contrasena:
        errores["contrasena"] = "Captura la contraseña inicial."
    elif len(contrasena) < config.LONGITUD_MINIMA_CONTRASENA:
        errores["contrasena"] = (
            "La contraseña debe tener al menos "
            f"{config.LONGITUD_MINIMA_CONTRASENA} caracteres."
        )

    # HU-01-02 · Usuario duplicado: identificador, cuenta o correo ya
    # registrados.
    duplicados = []
    if valores[
        "identificador"
    ] and usuario_modelo.verificar_identificador_existente(
        valores["identificador"]
    ):
        errores["identificador"] = (
            f"El identificador {valores['identificador']} ya está registrado."
        )
        duplicados.append(f"identificador {valores['identificador']}")
    if valores["cuenta"] and usuario_modelo.verificar_cuenta_en_uso(
        valores["cuenta"]
    ):
        errores["cuenta"] = (
            f"La cuenta {valores['cuenta']} ya está registrada."
        )
        duplicados.append(f"cuenta {valores['cuenta']}")
    if _validar_contacto(valores, errores):
        duplicados.append(f"correo {valores['email']}")

    # El perfil elegido debe existir y estar disponible.
    perfil = None
    if valores["perfil_id"] and "perfil_id" not in errores:
        perfil = (
            perfil_modelo.obtener_por_id(valores["perfil_id"])
            if valores["perfil_id"].isdigit()
            else None
        )
        if perfil is None or not perfil["disponible"]:
            errores["perfil_id"] = "El perfil seleccionado no está disponible."

    # Si algo fallo no se crea ningun registro.
    if errores:
        if duplicados:
            mensaje = (
                "Ya existe un usuario con "
                + " y ".join(duplicados)
                + ". No se creó ningún registro."
            )
        else:
            mensaje = "Revisa los campos marcados. El usuario no se registró."
        raise ErrorValidacion(mensaje, errores, valores)

    # HU-01-02 · Registro exitoso: la contrasena se guarda cifrada.
    nuevo_id = usuario_modelo.crear(
        _preparar_datos(valores), cifrar_contrasena(contrasena), perfil["id"]
    )
    mensaje = (
        f"Usuario registrado: {formar_nombre_completo(valores)} "
        f"({valores['identificador']}) "
        f"con perfil {perfil['nombre']}."
    )
    return nuevo_id, mensaje


def obtener_valores_edicion(usuario):
    """
    Descripcion:
        HU-01-04: Obtiene los datos actuales del usuario para llenar el
        formulario de edicion.

    Parametros:
        usuario (sqlite3.Row): usuario a editar.

    Salida:
        dict: valor de cada campo.
    """
    return {campo: usuario[campo] or "" for campo in CAMPOS_DATOS}


def actualizar(usuario, formulario):
    """
    Descripcion:
        HU-01-04: Actualiza nombre, apellidos, cuenta y contacto.

    Parametros:
        usuario (sqlite3.Row): usuario a editar.
        formulario (werkzeug.datastructures.MultiDict): datos capturados.

    Salida:
        dict: datos guardados con nombre_completo.

    Excepciones:
        ErrorValidacion si falta un obligatorio o la cuenta o el correo ya son
        de otra persona; se conservan los datos guardados.
    """
    # Leemos los campos del formulario.
    valores = _leer(formulario, CAMPOS_DATOS)
    errores = {}

    # HU-01-04 · Nombre obligatorio omitido (tambien apellido paterno y
    # cuenta).
    if not valores["nombre"]:
        errores["nombre"] = "El nombre es obligatorio."
    if not valores["apellido_paterno"]:
        errores["apellido_paterno"] = "El apellido paterno es obligatorio."
    if not valores["cuenta"]:
        errores["cuenta"] = "La cuenta es obligatoria."
    # HU-01-04 · Cuenta asignada a otra persona.
    elif usuario_modelo.verificar_cuenta_en_uso(
        valores["cuenta"], excluir_id=usuario["id"]
    ):
        errores["cuenta"] = "La cuenta ya está en uso"
    _validar_contacto(valores, errores, excluir_id=usuario["id"])

    # Si algo fallo se conservan los datos guardados.
    if errores:
        if errores.get("cuenta") == "La cuenta ya está en uso":
            mensaje = (
                "La cuenta ya está en uso por otro usuario. Se "
                "conservan los datos guardados."
            )
        else:
            mensaje = (
                "No se guardaron los cambios. Revisa los campos marcados."
            )
        raise ErrorValidacion(mensaje, errores, valores)

    # HU-01-04 · Actualizacion exitosa.
    datos = _preparar_datos(valores)
    usuario_modelo.actualizar_datos(usuario["id"], datos)
    datos["nombre_completo"] = formar_nombre_completo(datos)
    return datos


def cambiar_estado(usuario, accion, id_en_sesion):
    """
    Descripcion:
        HU-01-03: Habilita o deshabilita la cuenta. No se permite deshabilitar
        la cuenta propia.

    Parametros:
        usuario (sqlite3.Row): usuario.
        accion (str): 'habilitar' o 'deshabilitar'.
        id_en_sesion (int): id del usuario en sesion.

    Salida:
        tuple[str, str]: categoria del aviso y mensaje.
    """
    nombre = usuario["nombre_completo"]

    # HU-01-03 · Baja logica exitosa (no se permite deshabilitar la cuenta
    # propia).
    if accion == "deshabilitar":
        if usuario["id"] == id_en_sesion:
            return (
                "error",
                "No puedes deshabilitar tu propia cuenta mientras tienes la "
                "sesión iniciada.",
            )
        usuario_modelo.cambiar_estado(
            usuario["id"], config.ESTADO_DESHABILITADA
        )
        return "exito", (
            f"La cuenta de {nombre} fue deshabilitada. Sus datos se "
            "conservan y ya no podrá "
            "iniciar sesión."
        )

    # Reactivar una cuenta deshabilitada.
    if accion == "habilitar":
        usuario_modelo.cambiar_estado(usuario["id"], config.ESTADO_HABILITADA)
        return "exito", f"La cuenta de {nombre} fue habilitada nuevamente."
    return "error", "Acción no reconocida. No se realizaron cambios."


def asignar_perfil(usuario, seleccionado):
    """
    Descripcion:
        HU-01-08: Asigna o cambia el perfil de la cuenta.

    Parametros:
        usuario (sqlite3.Row): usuario.
        seleccionado (str): id del perfil elegido.

    Salida:
        tuple[str, str]: categoria del aviso y mensaje.

    Excepciones:
        ErrorValidacion si no se eligio perfil o no esta disponible; se
        conserva el anterior.
    """
    # HU-01-08 · Perfil de usuario sin seleccionar.
    seleccionado = (seleccionado or "").strip()
    if not seleccionado:
        mensaje = (
            "Selecciona un perfil de usuario. Se conserva la "
            "asignación anterior."
        )
        raise ErrorValidacion(mensaje, {"perfil_id": mensaje})

    # HU-01-08 · Perfil de usuario inexistente o no disponible.
    perfil = (
        perfil_modelo.obtener_por_id(seleccionado)
        if seleccionado.isdigit()
        else None
    )
    if perfil is None or not perfil["disponible"]:
        mensaje = (
            "El perfil de usuario no está disponible. Se conserva el "
            "perfil asignado previamente."
        )
        raise ErrorValidacion(mensaje, {"perfil_id": mensaje})

    # Si ya tenia ese perfil no hay cambios.
    if perfil["id"] == usuario["perfil_id"]:
        return (
            "informacion",
            f"{usuario['nombre_completo']} ya tiene asignado el perfil "
            f"{perfil['nombre']}. No hubo cambios.",
        )

    # HU-01-08 · Asignar perfil / Modificar perfil de usuario.
    usuario_modelo.asignar_perfil(usuario["id"], perfil["id"])
    anterior = usuario["perfil_nombre"] or "sin perfil"
    return "exito", (
        f"Perfil actualizado de {anterior} a {perfil['nombre']}. Los nuevos "
        "permisos se aplicarán "
        "en el siguiente inicio de sesión."
    )
