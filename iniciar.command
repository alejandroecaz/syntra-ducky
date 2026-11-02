#!/bin/bash
# ============================================================
# Archivo:      iniciar.command
# Proyecto:     Sistema Ducky de Gestion Bibliotecaria
# Empresa desarrolladora: Syntra Technologies
# Cliente:      Universidad Ducky
#
# Descripcion:
#     Arranque rapido en macOS: crea el entorno virtual, prepara syntra.db y
#     abre el navegador en el puerto 5050.
#
# Autores:
#     Melissa Silva Vazquez (624352)
#     Tomas Zapata Perez (629048)
#     Alejandro Evaristo Cazares Escobedo (626337)
#
# Fecha:
#     21/09/2026
# ============================================================

cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
    echo "Creando entorno virtual e instalando dependencias..."
    python3 -m venv venv
    venv/bin/pip install -q -r requirements.txt
fi

# Crea syntra.db, o la vuelve a crear con los datos de prueba si es del
# esquema anterior.
venv/bin/python init_db.py --si-hace-falta

# Abre el navegador cuando el servidor ya arranco.
( sleep 2 && open "http://127.0.0.1:5050" ) &
venv/bin/python app.py
