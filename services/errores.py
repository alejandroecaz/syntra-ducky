# ============================================================
# Archivo: services/errores.py
# Proyecto: Sistema Ducky de Gestión Bibliotecaria
# Syntra Technologies - Equipo 1 - Sprint 1
# Materia: Ingeniería de Software
# Autores:
#   - Melissa Silva Vázquez                #624352
#   - Tomás Zapata Pérez                   #629048
#   - Alejandro Evaristo Cazares Escobedo  #626337
# Descripción: Error común de la capa de servicios.
# ============================================================
"""Error común de la capa de servicios."""


class ErrorValidacion(Exception):
    """Una regla de negocio no se cumplió.

    Lleva el mensaje general, los errores por campo, lo que el usuario capturó (para no
    borrarlo del formulario) y el código HTTP con el que el controlador debe responder.
    """

    def __init__(self, mensaje, errores=None, valores=None, codigo=400):
        """Guarda el mensaje, los errores por campo, lo capturado y el código HTTP."""
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.errores = errores or {}
        self.valores = valores or {}
        self.codigo = codigo
