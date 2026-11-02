"""
============================================================
Archivo:      utils/pdf.py
Proyecto:     Sistema Ducky de Gestion Bibliotecaria
Empresa desarrolladora: Syntra Technologies
Cliente:      Universidad Ducky

Descripcion:
    Generacion del listado de libros en PDF con fpdf2 (HU-01-16).

Autores:
    Melissa Silva Vazquez (624352)
    Tomas Zapata Perez (629048)
    Alejandro Evaristo Cazares Escobedo (626337)

Fecha:
    21/09/2026
============================================================
"""

from datetime import datetime

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from fpdf.fonts import FontFace

import config
from services.catalogo_servicio import obtener_estado_libro

# Colores del documento (RGB), los mismos de la marca.
AZUL = (20, 50, 107)
DORADO = (227, 160, 8)
GRIS = (100, 116, 139)
TINTA = (15, 23, 42)


def _convertir_texto(valor):
    """
    Descripcion:
        Convierte el texto a latin-1, que es lo unico que acepta la fuente del
        PDF; los caracteres que no caben se reemplazan.

    Parametros:
        valor (object): valor a escribir en el PDF.

    Salida:
        str: texto compatible con latin-1.
    """
    return (
        str(valor if valor is not None else "")
        .encode("latin-1", "replace")
        .decode("latin-1")
    )


class ListadoPDF(FPDF):
    """PDF con el encabezado y el pie de pagina del sistema en cada hoja."""

    def header(self):
        """
        Descripcion:
            Dibuja el encabezado de cada hoja: franja azul y dorada, nombre del
            sistema y de la biblioteca. Es un metodo de FPDF, por eso conserva
            su nombre en ingles.

        Parametros:
            Ninguno.

        Salida:
            Ninguna.
        """
        # Franjas de color arriba.
        self.set_fill_color(*AZUL)
        self.rect(0, 0, self.w, 4, "F")
        self.set_fill_color(*DORADO)
        self.rect(0, 4, 60, 1.2, "F")

        # Nombre del sistema.
        self.set_y(10)
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*AZUL)
        self.cell(
            0,
            8,
            _convertir_texto(config.NOMBRE_SISTEMA),
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

        # Nombre de la biblioteca.
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*GRIS)
        self.cell(
            0,
            5,
            _convertir_texto(
                config.NOMBRE_CLIENTE
                + " · Sistema Ducky de Gestión Bibliotecaria"
            ),
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )
        self.ln(4)

    def footer(self):
        """
        Descripcion:
            Dibuja el pie de cada hoja: fecha de generacion a la izquierda y
            numero de pagina a la derecha. Es un metodo de FPDF, por eso
            conserva su nombre en ingles.

        Parametros:
            Ninguno.

        Salida:
            Ninguna.
        """
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GRIS)
        self.cell(
            0,
            6,
            _convertir_texto(f"Generado el {datetime.now():%d/%m/%Y %H:%M}"),
            align="L",
        )
        self.cell(0, 6, f"Página {self.page_no()} de {{nb}}", align="R")


def generar_listado(libros, filtros_texto, generado_por):
    """
    Descripcion:
        HU-01-16: Genera el PDF horizontal del listado con clave, titulo,
        autores, tema, editorial y estado de cada libro.

    Parametros:
        libros (list[sqlite3.Row]): libros del documento.
        filtros_texto (str): descripcion de los filtros aplicados.
        generado_por (str): nombre de quien lo genera.

    Salida:
        bytes: contenido del archivo PDF.

    Excepciones:
        fpdf.errors.FPDFException si falla la generacion del documento.
    """
    # Hoja horizontal A4 con salto de pagina automatico.
    pdf = ListadoPDF(orientation="L", unit="mm", format="A4")
    pdf.set_title("Listado de libros")
    pdf.set_author(_convertir_texto(generado_por))
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()

    # Titulo y resumen de filtros (HU-01-16 · Generacion del PDF con filtros).
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*TINTA)
    pdf.cell(
        0,
        7,
        "Listado de libros del catálogo",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*GRIS)
    pdf.cell(
        0,
        5,
        _convertir_texto(
            f"Filtros: {filtros_texto}  ·  Registros: {len(libros)}  ·  "
            f"Generado por: {generado_por}"
        ),
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.ln(3)

    # Tabla de libros con encabezado azul y renglones alternados.
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*TINTA)
    pdf.set_draw_color(226, 232, 240)
    with pdf.table(
        col_widths=(22, 78, 50, 38, 45, 34),
        line_height=6.5,
        headings_style=FontFace(
            emphasis="BOLD", color=(255, 255, 255), fill_color=AZUL
        ),
        cell_fill_color=(245, 247, 251),
        cell_fill_mode="ROWS",
        borders_layout="HORIZONTAL_LINES",
    ) as tabla:
        # Encabezado de columnas.
        encabezado = tabla.row()
        for titulo in (
            "Clave",
            "Título",
            "Autores",
            "Tema",
            "Editorial",
            "Estado",
        ):
            encabezado.cell(titulo)
        # Un renglon por libro.
        for libro in libros:
            fila = tabla.row()
            fila.cell(_convertir_texto(libro["clave"]))
            fila.cell(_convertir_texto(libro["titulo"]))
            fila.cell(_convertir_texto(libro["autores"]))
            fila.cell(_convertir_texto(libro["tema"]))
            fila.cell(_convertir_texto(libro["editorial"]))
            fila.cell(_convertir_texto(obtener_estado_libro(libro)))

    return bytes(pdf.output())
