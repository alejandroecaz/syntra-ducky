"""
============================================================
Archivo:      services/errores.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Error comun de la capa de servicios.

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""


class ErrorValidacion(Exception):
    """Una regla de negocio no se cumplio.

    Lleva el mensaje general, los errores por campo, lo que el usuario
    capturo (para no borrarlo del formulario) y el codigo HTTP con el que el
    controlador debe responder.
    """

    def __init__(self, mensaje, errores=None, valores=None, codigo=400):
        """
        Descripcion:
            Guarda el mensaje general, los errores por campo, lo que capturo el
            usuario y el codigo HTTP con el que debe responder el controlador.

        Parametros:
            mensaje (str): mensaje general para el aviso.
            errores (dict o None): mensaje de error de cada campo.
            valores (dict o None): lo que capturo el usuario, para no borrarlo
                del formulario.
            codigo (int): codigo HTTP de la respuesta (400 por omision).

        Salida:
            Ninguna.
        """
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.errores = errores or {}
        self.valores = valores or {}
        self.codigo = codigo
