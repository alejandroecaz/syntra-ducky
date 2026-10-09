#!/bin/bash
cd "$(dirname "$0")"

if [ ! -d "venv" ]; then
  echo "Creando entorno virtual e instalando dependencias..."
  python3 -m venv venv
  venv/bin/pip install -q -r requirements.txt
fi

# Abre el navegador cuando el servidor ya arranco
( sleep 2 && open "http://127.0.0.1:5050" ) &
venv/bin/python app.py
