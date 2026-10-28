"""Capa de servicios: reglas de negocio entre los controladores y los modelos.

Los controladores (web y móvil) llaman a estos servicios; los servicios validan, deciden
y llaman a los modelos. Aquí no hay SQL ni nada de Flask (request, session, plantillas).
"""
