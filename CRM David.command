#!/bin/bash
# Acceso directo para CRM - Funciona en cualquier Mac sincronizado por iCloud

# Ruta al proyecto (usa $HOME para ser portable entre equipos)
PROJECT_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/DEVELOPER/crm"

cd "$PROJECT_DIR"

# Ejecutar Streamlit
streamlit run app.py
