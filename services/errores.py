"""Error común de la capa de servicios."""


class ErrorValidacion(Exception):
    """Una regla de negocio no se cumplió.

    Lleva el mensaje general, los errores por campo, lo que el usuario capturó (para no
    borrarlo del formulario) y el código HTTP con el que el controlador debe responder.
    """

    def __init__(self, mensaje, errores=None, valores=None, codigo=400):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.errores = errores or {}
        self.valores = valores or {}
        self.codigo = codigo
