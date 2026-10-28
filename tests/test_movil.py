"""Portal móvil para alumnos (/movil)."""
from models.db import consultar
from tests.conftest import entrar, id_libro

SOLO_ALUMNOS = "Acceso no autorizado: el portal móvil es solo para alumnos"


def entrar_movil(cliente, cuenta="alumno", contrasena="Alumno123"):
    return entrar(cliente, cuenta, contrasena, ruta="/movil/login")


def test_alumno_entra(cliente):
    respuesta = entrar_movil(cliente)
    assert respuesta.status_code == 302
    assert respuesta.headers["Location"].endswith("/movil")
    assert "Hola, Mariana" in cliente.get("/movil").get_data(as_text=True)


def test_profesor_rechazado(cliente):
    respuesta = entrar_movil(cliente, "profesor", "Profe123")
    assert respuesta.status_code == 403
    assert SOLO_ALUMNOS in respuesta.get_data(as_text=True)
    with cliente.session_transaction() as sesion:
        assert "usuario_id" not in sesion


def test_profesor_con_sesion_web_no_entra_al_portal(cliente):
    entrar(cliente, "profesor", "Profe123")
    respuesta = cliente.get("/movil")
    assert respuesta.status_code == 403
    assert SOLO_ALUMNOS in respuesta.get_data(as_text=True)


def test_mismos_mensajes_que_la_web(cliente):
    assert "La cuenta no está habilitada" in entrar_movil(cliente, "deshabilitado", "Demo123").get_data(as_text=True)
    assert "no tiene autorización para acceder" in entrar_movil(cliente, "visitante", "Demo123").get_data(as_text=True)
    assert "Cuenta o contraseña incorrecta" in entrar_movil(cliente, "alumno", "mala").get_data(as_text=True)


def test_sin_sesion_manda_al_login_movil(cliente):
    respuesta = cliente.get("/movil")
    assert respuesta.status_code == 302
    assert "/movil/login" in respuesta.headers["Location"]


def test_busqueda_vacia(cliente):
    entrar_movil(cliente)
    html = cliente.get("/movil?buscar=1&campo=autor&q=%20%20").get_data(as_text=True)
    assert "Captura un criterio de búsqueda" in html
    # Conserva el campo que se había elegido
    assert 'value="autor" checked' in html


def test_busqueda_sin_resultados(cliente):
    entrar_movil(cliente)
    html = cliente.get("/movil?buscar=1&campo=titulo&q=zzzz").get_data(as_text=True)
    assert "No se encontraron libros" in html
    assert "m-libro__titulo" not in html


def test_login_movil_sin_aviso_de_solo_alumnos(cliente):
    assert "Solo para alumnos." not in cliente.get("/movil/login").get_data(as_text=True)


def test_despues_de_buscar_se_puede_limpiar(cliente):
    entrar_movil(cliente)
    html = cliente.get("/movil?buscar=1&campo=titulo&q=asdasd").get_data(as_text=True)
    assert '<a href="/movil" class="btn btn--secondary btn--lg">' in html
    assert "Nueva búsqueda" in html
    # En la pantalla inicial no hay nada que limpiar
    assert "<span>Limpiar</span>" not in cliente.get("/movil").get_data(as_text=True)


def test_busqueda_con_resultados_en_tarjetas(cliente):
    entrar_movil(cliente)
    html = cliente.get("/movil?buscar=1&campo=autor&q=kernighan").get_data(as_text=True)
    assert "El lenguaje de programación C" in html
    assert "Brian W. Kernighan, Dennis M. Ritchie" in html
    assert "1 de 1 disponibles" in html


def test_detalle_sin_ubicacion(app, cliente):
    entrar_movil(cliente)
    html = cliente.get(f"/movil/libros/{id_libro(app, 'LIB-002')}").get_data(as_text=True)
    assert "EJ-0005" in html
    assert "Ubicación no registrada" in html
    assert "Sala General · Estante A-2 · Posición 7" in html


def test_detalle_libro_sin_ejemplares(app, cliente):
    entrar_movil(cliente)
    html = cliente.get(f"/movil/libros/{id_libro(app, 'LIB-008')}").get_data(as_text=True)
    assert "Este libro no tiene ejemplares registrados" in html


def test_estados_no_disponibles_no_se_muestran_como_disponible(app, cliente):
    entrar_movil(cliente)
    html = cliente.get(f"/movil/libros/{id_libro(app, 'LIB-006')}").get_data(as_text=True)
    assert "Perdido" in html and "Fuera de servicio" in html
    assert "badge--success" not in html


def test_libro_inexistente(cliente):
    entrar_movil(cliente)
    respuesta = cliente.get("/movil/libros/9999")
    assert respuesta.status_code == 404
    assert "No encontramos ese libro" in respuesta.get_data(as_text=True)


def test_permiso_movil_solo_en_perfil_alumno(contexto):
    filas = consultar(
        "SELECT p.nombre FROM perfil_permisos pp JOIN perfiles p ON p.id = pp.perfil_id "
        "JOIN permisos pe ON pe.id = pp.permiso_id WHERE pe.codigo = 'movil.acceder'"
    )
    assert [fila["nombre"] for fila in filas] == ["Alumno"]


def test_permiso_movil_visible_en_perfiles(cliente):
    entrar(cliente, "admin", "Admin123")
    assert "Acceder al portal móvil" in cliente.get("/perfiles").get_data(as_text=True)


def test_manifest_para_pantalla_de_inicio(cliente):
    manifest = cliente.get("/static/manifest.json").get_json()
    assert manifest["start_url"] == "/movil"
    assert manifest["display"] == "standalone"
