#!/bin/bash
cd "$(dirname "$0")"
echo "============================================"
echo "  DAVID - Análisis de Costes de Flota"
echo "============================================"
echo ""
echo "Iniciando aplicación..."
streamlit run app.py --server.port 8506
