"""Servicio de usuarios: registro, consulta, actualización, baja lógica y asignación de perfil.

Cubre HU-01-02, HU-01-03, HU-01-04, HU-01-05 y HU-01-08.
"""
import re

import config
from models import perfil as perfil_modelo
from models import usuario as usuario_modelo
from services.auth_servicio import cifrar_contrasena
from services.errores import ErrorValidacion

CAMPOS_DATOS = ("nombre", "apellido_paterno", "apellido_materno", "cuenta", "email", "telefono")
OBLIGATORIOS_REGISTRO = {
    "identificador": "el identificador institucional",
    "nombre": "el nombre",
    "apellido_paterno": "el apellido paterno",
    "cuenta": "la cuenta",
}
CRITERIOS_BUSQUEDA = ("nombre", "identificador")


def nombre_completo(datos):
    """'Mariana López Hernández' a partir de nombre y apellidos."""
    partes = [datos.get("nombre"), datos.get("apellido_paterno"), datos.get("apellido_materno")]
    return " ".join(parte for parte in partes if parte)


def _leer(form, campos):
    return {campo: (form.get(campo) or "").strip() for campo in campos}


def _opcional(valor):
    # En la BD los campos opcionales vacíos se guardan como NULL
    return valor or None


def _validar_contacto(valores, errores, excluir_id=None):
    # Correo y teléfono son opcionales; regresa True si el correo ya es de otra persona
    duplicado = False
    if valores["email"]:
        if not re.match(config.PATRON_EMAIL, valores["email"]):
            errores["email"] = "Escribe un correo válido, por ejemplo nombre@ducky.edu.mx."
        elif usuario_modelo.email_en_uso(valores["email"], excluir_id):
            errores["email"] = f"El correo {valores['email']} ya está registrado."
            duplicado = True
    if valores["telefono"] and not re.match(config.PATRON_TELEFONO, valores["telefono"]):
        errores["telefono"] = "Escribe un teléfono válido (solo números, espacios o guiones)."
    return duplicado


def _datos_para_guardar(valores):
    datos = dict(valores)
    for campo in ("apellido_materno", "email", "telefono"):
        datos[campo] = _opcional(valores[campo])
    return datos


def buscar(criterio, texto, buscando):
    """Consulta de usuarios (HU-01-05). Regresa (usuarios, mensaje de error o None)."""
    if not buscando:
        return usuario_modelo.listar(), None
    if not texto:
        return [], "Captura un identificador o un nombre para buscar."
    criterio = criterio if criterio in CRITERIOS_BUSQUEDA else CRITERIOS_BUSQUEDA[0]
    return usuario_modelo.buscar(criterio, texto), None


def obtener(usuario_id):
    """Un usuario o None."""
    return usuario_modelo.obtener_por_id(usuario_id)


def permisos_de(usuario):
    """Códigos de permiso del perfil asignado a la cuenta."""
    return perfil_modelo.permisos_de(usuario["perfil_id"]) if usuario["perfil_id"] else []


def perfiles():
    """Perfiles para el formulario de registro y la asignación."""
    return perfil_modelo.listar()


def registrar(form):
    """Registra una cuenta (HU-01-02). Regresa (id, mensaje) o lanza ErrorValidacion."""
    valores = _leer(form, ("identificador", *CAMPOS_DATOS, "perfil_id"))
    contrasena = form.get("contrasena", "")
    errores = {}

    for campo, etiqueta in OBLIGATORIOS_REGISTRO.items():
        if not valores[campo]:
            errores[campo] = f"Captura {etiqueta}."
    if not valores["perfil_id"]:
        errores["perfil_id"] = "Selecciona un perfil de usuario."
    if not contrasena:
        errores["contrasena"] = "Captura la contraseña inicial."
    elif len(contrasena) < config.LONGITUD_MINIMA_CONTRASENA:
        errores["contrasena"] = f"La contraseña debe tener al menos {config.LONGITUD_MINIMA_CONTRASENA} caracteres."

    duplicados = []
    if valores["identificador"] and usuario_modelo.existe_identificador(valores["identificador"]):
        errores["identificador"] = f"El identificador {valores['identificador']} ya está registrado."
        duplicados.append(f"identificador {valores['identificador']}")
    if valores["cuenta"] and usuario_modelo.cuenta_en_uso(valores["cuenta"]):
        errores["cuenta"] = f"La cuenta {valores['cuenta']} ya está registrada."
        duplicados.append(f"cuenta {valores['cuenta']}")
    if _validar_contacto(valores, errores):
        duplicados.append(f"correo {valores['email']}")

    perfil = None
    if valores["perfil_id"] and "perfil_id" not in errores:
        perfil = perfil_modelo.obtener_por_id(valores["perfil_id"]) if valores["perfil_id"].isdigit() else None
        if perfil is None or not perfil["disponible"]:
            errores["perfil_id"] = "El perfil seleccionado no está disponible."

    if errores:
        if duplicados:
            mensaje = "Ya existe un usuario con " + " y ".join(duplicados) + ". No se creó ningún registro."
        else:
            mensaje = "Revisa los campos marcados. El usuario no se registró."
        raise ErrorValidacion(mensaje, errores, valores)

    nuevo_id = usuario_modelo.crear(_datos_para_guardar(valores), cifrar_contrasena(contrasena), perfil["id"])
    mensaje = (f"Usuario registrado: {nombre_completo(valores)} ({valores['identificador']}) "
               f"con perfil {perfil['nombre']}.")
    return nuevo_id, mensaje


def valores_edicion(usuario):
    """Datos actuales del usuario para llenar el formulario de edición."""
    return {campo: usuario[campo] or "" for campo in CAMPOS_DATOS}


def actualizar(usuario, form):
    """Actualiza nombre, apellidos, cuenta y contacto (HU-01-04). Regresa los datos guardados."""
    valores = _leer(form, CAMPOS_DATOS)
    errores = {}
    if not valores["nombre"]:
        errores["nombre"] = "El nombre es obligatorio."
    if not valores["apellido_paterno"]:
        errores["apellido_paterno"] = "El apellido paterno es obligatorio."
    if not valores["cuenta"]:
        errores["cuenta"] = "La cuenta es obligatoria."
    elif usuario_modelo.cuenta_en_uso(valores["cuenta"], excluir_id=usuario["id"]):
        errores["cuenta"] = "La cuenta ya está en uso"
    _validar_contacto(valores, errores, excluir_id=usuario["id"])

    if errores:
        if errores.get("cuenta") == "La cuenta ya está en uso":
            mensaje = "La cuenta ya está en uso por otro usuario. Se conservan los datos guardados."
        else:
            mensaje = "No se guardaron los cambios. Revisa los campos marcados."
        raise ErrorValidacion(mensaje, errores, valores)

    datos = _datos_para_guardar(valores)
    usuario_modelo.actualizar_datos(usuario["id"], datos)
    datos["nombre_completo"] = nombre_completo(datos)
    return datos


def cambiar_estado(usuario, accion, id_en_sesion):
    """Habilita o deshabilita la cuenta (HU-01-03). Regresa (categoría, mensaje) para el aviso."""
    nombre = usuario["nombre_completo"]
    if accion == "deshabilitar":
        if usuario["id"] == id_en_sesion:
            return "error", "No puedes deshabilitar tu propia cuenta mientras tienes la sesión iniciada."
        usuario_modelo.cambiar_estado(usuario["id"], config.ESTADO_DESHABILITADA)
        return "success", (f"La cuenta de {nombre} fue deshabilitada. Sus datos se conservan y ya no podrá "
                           "iniciar sesión.")
    if accion == "habilitar":
        usuario_modelo.cambiar_estado(usuario["id"], config.ESTADO_HABILITADA)
        return "success", f"La cuenta de {nombre} fue habilitada nuevamente."
    return "error", "Acción no reconocida. No se realizaron cambios."


def asignar_perfil(usuario, seleccionado):
    """Asigna o cambia el perfil (HU-01-08). Regresa (categoría, mensaje) o lanza ErrorValidacion."""
    seleccionado = (seleccionado or "").strip()
    if not seleccionado:
        mensaje = "Selecciona un perfil de usuario. Se conserva la asignación anterior."
        raise ErrorValidacion(mensaje, {"perfil_id": mensaje})

    perfil = perfil_modelo.obtener_por_id(seleccionado) if seleccionado.isdigit() else None
    if perfil is None or not perfil["disponible"]:
        mensaje = "El perfil de usuario no está disponible. Se conserva el perfil asignado previamente."
        raise ErrorValidacion(mensaje, {"perfil_id": mensaje})

    if perfil["id"] == usuario["perfil_id"]:
        return "info", f"{usuario['nombre_completo']} ya tiene asignado el perfil {perfil['nombre']}. No hubo cambios."

    usuario_modelo.asignar_perfil(usuario["id"], perfil["id"])
    anterior = usuario["perfil_nombre"] or "sin perfil"
    return "success", (f"Perfil actualizado de {anterior} a {perfil['nombre']}. Los nuevos permisos se aplicarán "
                       "en el siguiente inicio de sesión.")
