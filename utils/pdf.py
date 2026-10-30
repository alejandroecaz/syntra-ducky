# ============================================================
# Archivo: utils/pdf.py
# Proyecto: Sistema Ducky de Gestión Bibliotecaria
# Syntra Technologies - Equipo 1 - Sprint 1
# Materia: Ingeniería de Software
# Autores:
#   - Melissa Silva Vázquez                #624352
#   - Tomás Zapata Pérez                   #629048
#   - Alejandro Evaristo Cazares Escobedo  #626337
# Descripción: Generación del listado de libros en PDF con fpdf2 (HU-01-16).
# ============================================================
"""Generación del listado de libros en PDF con fpdf2 (HU-01-16)."""
from datetime import datetime

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from fpdf.fonts import FontFace

import config
from services.catalogo_servicio import estado_libro

# Colores del documento (RGB), los mismos de la marca
AZUL = (20, 50, 107)
DORADO = (227, 160, 8)
GRIS = (100, 116, 139)
TINTA = (15, 23, 42)


def _texto(valor):
    """El PDF solo acepta latin-1; lo demás se reemplaza."""
    return str(valor if valor is not None else "").encode("latin-1", "replace").decode("latin-1")


class ListadoPDF(FPDF):
    """PDF con el encabezado y el pie de página del sistema en cada hoja."""

    def header(self):
        """Franja azul y dorada, nombre del sistema y de la biblioteca."""
        # Franjas de color arriba
        self.set_fill_color(*AZUL)
        self.rect(0, 0, self.w, 4, "F")
        self.set_fill_color(*DORADO)
        self.rect(0, 4, 60, 1.2, "F")

        # Nombre del sistema
        self.set_y(10)
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*AZUL)
        self.cell(0, 8, _texto(config.NOMBRE_SISTEMA), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Nombre de la biblioteca
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*GRIS)
        self.cell(0, 5, _texto(config.NOMBRE_CLIENTE + " · Sistema Ducky de Gestión Bibliotecaria"),
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(4)

    def footer(self):
        """Fecha de generación a la izquierda y número de página a la derecha."""
        self.set_y(-12)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GRIS)
        self.cell(0, 6, _texto(f"Generado el {datetime.now():%d/%m/%Y %H:%M}"), align="L")
        self.cell(0, 6, f"Página {self.page_no()} de {{nb}}", align="R")


def generar_listado(libros, filtros_texto, generado_por):
    """Regresa los bytes del PDF con clave, título, autores, tema, editorial y estado."""
    # Hoja horizontal A4 con salto de página automático
    pdf = ListadoPDF(orientation="L", unit="mm", format="A4")
    pdf.set_title("Listado de libros")
    pdf.set_author(_texto(generado_por))
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()

    # Título y resumen de filtros (HU-01-16 · Generación del PDF con filtros)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*TINTA)
    pdf.cell(0, 7, "Listado de libros del catálogo", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*GRIS)
    pdf.cell(0, 5, _texto(f"Filtros: {filtros_texto}  ·  Registros: {len(libros)}  ·  Generado por: {generado_por}"),
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)

    # Tabla de libros con encabezado azul y renglones alternados
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*TINTA)
    pdf.set_draw_color(226, 232, 240)
    with pdf.table(
        col_widths=(22, 78, 50, 38, 45, 34),
        line_height=6.5,
        headings_style=FontFace(emphasis="BOLD", color=(255, 255, 255), fill_color=AZUL),
        cell_fill_color=(245, 247, 251),
        cell_fill_mode="ROWS",
        borders_layout="HORIZONTAL_LINES",
    ) as tabla:
        # Encabezado de columnas
        encabezado = tabla.row()
        for titulo in ("Clave", "Título", "Autores", "Tema", "Editorial", "Estado"):
            encabezado.cell(titulo)
        # Un renglón por libro
        for libro in libros:
            fila = tabla.row()
            fila.cell(_texto(libro["clave"]))
            fila.cell(_texto(libro["titulo"]))
            fila.cell(_texto(libro["autores"]))
            fila.cell(_texto(libro["tema"]))
            fila.cell(_texto(libro["editorial"]))
            fila.cell(_texto(estado_libro(libro)))

    return bytes(pdf.output())
