import streamlit as st
import streamlit.components.v1 as components
from streamlit_js_eval import streamlit_js_eval
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime, timedelta
import locale
import io
import json
from fpdf import FPDF
import folium
from streamlit_folium import st_folium
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Autenticación
from auth import login_page, check_auth, get_user_permissions, logout, mostrar_usuario_no_autorizado
from admin_panel import panel_admin, registrar_accion

# Configurar locale español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'es_ES')
    except:
        pass  # Si no está disponible, usar el default

# Meses en español para gráficos
MESES_ES = {
    '01': 'Ene', '02': 'Feb', '03': 'Mar', '04': 'Abr',
    '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Ago',
    '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dic'
}

def formato_mes_es(fecha_str):
    """Convierte '2024-01' a 'Ene 2024'"""
    if pd.isna(fecha_str):
        return fecha_str
    try:
        partes = str(fecha_str).split('-')
        if len(partes) >= 2:
            año = partes[0]
            mes = partes[1]
            return f"{MESES_ES.get(mes, mes)} {año}"
    except:
        pass
    return fecha_str

def normalizar_texto(texto):
    """Normaliza texto a Primera mayúscula y resto minúsculas."""
    if pd.isna(texto) or not isinstance(texto, str):
        return texto
    return texto.strip().capitalize()

from data_loader import (
    cargar_todos, cargar_presupuestos_actuales, obtener_kpis,
    obtener_presupuestos_pendientes, obtener_clientes_inactivos,
    obtener_segmentacion, obtener_analisis_conversion, obtener_tendencia_mensual,
    obtener_grupos_clientes, obtener_tipos_servicio, obtener_comerciales,
    obtener_formas_contacto, obtener_fuentes, ESTADOS_PRESUPUESTO,
    cargar_clientes, cargar_datos_con_clientes, calcular_tipo_cliente,
    obtener_estadisticas_cliente, DEFAULT_PARAMS, calcular_metricas_clientes,
    obtener_anticipacion_por_tipo, obtener_distribucion_anticipacion,
    obtener_tendencia_anticipacion_mensual, calcular_tiempo_anticipacion
)

# Segmentos de cliente disponibles
SEGMENTOS_CLIENTE = ['Todos', 'HABITUAL', 'OCASIONAL_ACTIVO', 'REACTIVADO', 'PROSPECTO', 'INACTIVO']
from database import (
    agregar_nota, obtener_notas_cliente, obtener_notas_presupuesto,
    obtener_todas_notas, buscar_notas, guardar_tipo_servicio,
    obtener_tipos_servicio_db, eliminar_tipo_servicio,
    # Incentivos
    guardar_config_incentivo, obtener_config_incentivo, obtener_todas_config_incentivos,
    guardar_tramo_comision, obtener_tramos_comision, limpiar_tramos_comision,
    guardar_bonus, obtener_bonus_objetivos, limpiar_bonus,
    guardar_puntos_accion, obtener_puntos_acciones, limpiar_puntos_acciones,
    guardar_premio, obtener_premios, limpiar_premios,
    guardar_incentivo_historico, obtener_historico_incentivos,
    # Premios especiales por presupuesto
    guardar_premio_presupuesto, obtener_premios_presupuesto, marcar_premio_conseguido,
    eliminar_premio_presupuesto, obtener_premio_por_presupuesto,
    # Tarifas
    guardar_temporada, obtener_temporadas, eliminar_temporada, obtener_temporada_por_fecha,
    guardar_tipo_bus, obtener_tipos_bus, eliminar_tipo_bus,
    guardar_tipo_cliente, obtener_tipos_cliente, eliminar_tipo_cliente,
    guardar_tarifa_servicio, obtener_tarifas_servicio, obtener_tarifa_servicio, eliminar_tarifa_servicio,
    guardar_tarifa_cliente, obtener_tarifas_cliente, obtener_tarifa_cliente_especifica, eliminar_tarifa_cliente,
    calcular_tarifa,
    # Clientes desactivados
    obtener_clientes_desactivados, desactivar_cliente, reactivar_cliente
)

# Competencia y Análisis de Mercado (Supabase - persistente)
from db_competencia import (
    guardar_competidor, obtener_competidores, obtener_competidor_por_id, eliminar_competidor,
    guardar_cotizacion_competencia, obtener_cotizaciones_competencia, eliminar_cotizacion_competencia,
    obtener_estadisticas_mercado, obtener_posicion_por_servicio, obtener_ranking_competidores,
    detectar_alertas_competencia, comparar_con_tarifa_david, FACTOR_VEHICULO_NORM,
    guardar_vehiculo_competencia, obtener_vehiculos_competencia, eliminar_vehiculo_competencia,
    actualizar_vehiculo_competencia, obtener_estadisticas_flota_competencia, obtener_comparativa_flotas, importar_vehiculos_masivo
)

# Configuración de la página
st.set_page_config(
    page_title="CRM Autocares David",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# VERIFICACIÓN DE AUTENTICACIÓN
# ============================================
DEV_MODE = st.secrets.get("DEV_MODE", False)

if DEV_MODE:
    # Modo desarrollo - usuario local sin Azure
    user = {
        'id': 'dev-user',
        'email': 'dev@local.com',
        'nombre': 'Usuario Dev',
        'rol': 'admin',
        'activo': True
    }
    permisos = {
        'Acciones': {'ver': True, 'editar': True},
        'Dashboard': {'ver': True, 'editar': True},
        'Tiempo Anticipacion': {'ver': True, 'editar': True},
        'Seguimiento Presupuestos': {'ver': True, 'editar': True},
        'Pipeline': {'ver': True, 'editar': True},
        'Clientes': {'ver': True, 'editar': True},
        'Campanas Segmentadas': {'ver': True, 'editar': True},
        'Analisis Conversion': {'ver': True, 'editar': True},
        'Incentivos': {'ver': True, 'editar': True},
        'Calculadora': {'ver': True, 'editar': True},
        'Tarifas': {'ver': True, 'editar': True},
        'Configuracion': {'ver': True, 'editar': True}
    }
else:
    user = check_auth()

    if user is None:
        # No autenticado - mostrar login
        login_page()
        st.stop()

    if isinstance(user, dict) and user.get('error') == 'inactive':
        # Usuario no autorizado
        mostrar_usuario_no_autorizado()
        st.stop()

    permisos = get_user_permissions(user['id'])

# Guardar usuario en session_state
st.session_state.user = user

# ============================================
# DAVID BRAND COLORS
# ============================================
# Primary: Negro #000000 (50%) - Headers, títulos, texto principal
# Secondary: Blanco #FFFFFF (45%) - Fondos, cards
# Accent: Rojo #F15025 (5%) - Solo para elementos interactivos destacados
DAVID_BLACK = "#000000"
DAVID_WHITE = "#FFFFFF"
DAVID_RED = "#F15025"
DAVID_GRAY_LIGHT = "#F5F5F5"
DAVID_GRAY_MEDIUM = "#E0E0E0"
DAVID_GRAY_DARK = "#424242"

# Estilo CSS personalizado - DAVID Brand Identity
st.markdown("""
<style>
    /* ============================================
       DAVID BRAND - Sistema de Diseño
       Negro (#000000), Blanco (#FFFFFF), Rojo Acento (#F15025)
       ============================================ */

    /* Import Google Font similar to Aeonik (brand font) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Base Typography */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }

    /* Streamlit main container */
    .main .block-container {
        padding-top: 2rem;
        max-width: 1400px;
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        color: #000000 !important;
        letter-spacing: -0.02em;
    }

    /* Metric Cards - DAVID Brand */
    .metric-card {
        background-color: #FFFFFF;
        padding: 24px;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #E0E0E0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    .stMetric {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        border: 1px solid #E0E0E0;
    }

    .stMetric label {
        color: #424242 !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        font-size: 12px !important;
        letter-spacing: 0.05em;
    }

    .stMetric [data-testid="stMetricValue"] {
        color: #000000 !important;
        font-weight: 700 !important;
    }

    /* Sidebar - DAVID Brand */
    [data-testid="stSidebar"] {
        background-color: #000000 !important;
    }

    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdown"],
    [data-testid="stSidebar"] [data-testid="stMarkdown"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdown"] span {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stRadio label,
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stMultiSelect label {
        color: #FFFFFF !important;
    }

    /* Radio buttons in sidebar */
    [data-testid="stSidebar"] .stRadio > div {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] .stRadio > div > label {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] .stRadio > div > label > div {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] p {
        color: #FFFFFF !important;
    }

    /* Navigation items */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] * {
        color: #FFFFFF !important;
    }

    /* Selectbox text in sidebar */
    [data-testid="stSidebar"] [data-baseweb="select"] {
        color: #000000 !important;
    }

    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #000000 !important;
    }

    /* Buttons - Primary uses DAVID Red accent */
    .stButton > button[kind="primary"],
    .stButton > button:first-child {
        background-color: #F15025 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease;
    }

    .stButton > button[kind="primary"]:hover,
    .stButton > button:first-child:hover {
        background-color: #D94420 !important;
        box-shadow: 0 4px 12px rgba(241, 80, 37, 0.3) !important;
    }

    /* Secondary buttons */
    .stButton > button[kind="secondary"] {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 2px solid #000000 !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }

    .stButton > button[kind="secondary"]:hover {
        background-color: #000000 !important;
        color: #FFFFFF !important;
    }

    /* Sidebar buttons - Override for visibility */
    [data-testid="stSidebar"] .stButton > button,
    [data-testid="stSidebar"] .stButton > button p,
    [data-testid="stSidebar"] .stButton > button span,
    [data-testid="stSidebar"] .stButton > button div {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 6px !important;
    }

    [data-testid="stSidebar"] .stButton > button:hover,
    [data-testid="stSidebar"] .stButton > button:hover p,
    [data-testid="stSidebar"] .stButton > button:hover span,
    [data-testid="stSidebar"] .stButton > button:hover div {
        background-color: #F15025 !important;
        color: #FFFFFF !important;
    }

    /* Tabs - DAVID Brand */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: transparent;
        border-bottom: 2px solid #E0E0E0;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        color: #424242;
        font-weight: 500;
        padding: 12px 20px;
        margin-bottom: -2px;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #000000;
        border-bottom-color: #E0E0E0;
    }

    .stTabs [aria-selected="true"] {
        background-color: transparent !important;
        color: #F15025 !important;
        border-bottom: 2px solid #F15025 !important;
        font-weight: 600 !important;
    }

    /* Expanders - DAVID Brand */
    .streamlit-expanderHeader {
        background-color: #FFFFFF !important;
        border: 1px solid #E0E0E0 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        color: #000000 !important;
    }

    .streamlit-expanderHeader:hover {
        border-color: #F15025 !important;
    }

    /* DataFrames - DAVID Brand */
    .stDataFrame {
        border: 1px solid #E0E0E0;
        border-radius: 8px;
    }

    /* Inputs - DAVID Brand */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        border-color: #E0E0E0 !important;
        border-radius: 6px !important;
    }

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #F15025 !important;
        box-shadow: 0 0 0 2px rgba(241, 80, 37, 0.1) !important;
    }

    /* Success/Warning/Error messages - Using brand-compatible colors */
    .stSuccess {
        background-color: #F5F5F5 !important;
        border-left: 4px solid #000000 !important;
        color: #000000 !important;
    }

    .stWarning {
        background-color: #FFF5F2 !important;
        border-left: 4px solid #F15025 !important;
    }

    /* Custom DAVID Brand Cards */
    .david-card {
        background: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    .david-card-dark {
        background: #000000;
        border-radius: 8px;
        padding: 24px;
        color: #FFFFFF;
    }

    .david-card-accent {
        background: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-left: 4px solid #F15025;
        border-radius: 8px;
        padding: 24px;
    }

    /* DAVID Header Style */
    .david-header {
        background: #000000;
        padding: 24px 32px;
        border-radius: 8px;
        color: #FFFFFF;
        margin-bottom: 24px;
    }

    .david-header h2 {
        color: #FFFFFF !important;
        margin: 0;
        font-weight: 600;
    }

    .david-header p {
        color: rgba(255,255,255,0.7);
        margin: 8px 0 0 0;
    }

    /* Accent text */
    .david-accent {
        color: #F15025 !important;
    }

    /* Price display */
    .david-price {
        font-size: 48px;
        font-weight: 700;
        color: #000000;
        letter-spacing: -0.02em;
    }

    .david-price-accent {
        font-size: 48px;
        font-weight: 700;
        color: #F15025;
        letter-spacing: -0.02em;
    }

    /* Progress bars */
    .stProgress > div > div > div {
        background-color: #F15025 !important;
    }

    /* Dividers */
    hr {
        border-color: #E0E0E0 !important;
    }

    /* Badges */
    .david-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .david-badge-black {
        background: #000000;
        color: #FFFFFF;
    }

    .david-badge-red {
        background: #F15025;
        color: #FFFFFF;
    }

    .david-badge-outline {
        background: transparent;
        border: 1px solid #000000;
        color: #000000;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# FUNCIONES DE RUTAS Y MAPAS
# ============================================
def geocodificar_direccion(direccion, google_api_key=None):
    """Convierte una dirección en coordenadas usando Google Places API (si disponible) o Nominatim"""
    try:
        # Intentar obtener API key si no se pasa
        if google_api_key is None:
            google_api_key = get_google_api_key()

        # Intentar con Google Places API primero
        if google_api_key:
            # Usar Google Places Text Search API
            url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            params = {
                'query': direccion,
                'key': google_api_key,
                'region': 'es',
                'language': 'es'
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'OK' and data.get('results'):
                    result = data['results'][0]
                    lat = result['geometry']['location']['lat']
                    lon = result['geometry']['location']['lng']
                    display_name = result.get('formatted_address', result.get('name', direccion))
                    return (lat, lon, display_name)

        # Fallback a Nominatim si no hay Google API o falla
        if 'españa' not in direccion.lower() and 'spain' not in direccion.lower():
            direccion_buscar = f"{direccion}, España"
        else:
            direccion_buscar = direccion

        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': direccion_buscar,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1
        }
        headers = {
            'User-Agent': 'CRM_Autocares_David/1.0'
        }

        response = requests.get(url, params=params, headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                result = data[0]
                lat = float(result['lat'])
                lon = float(result['lon'])
                display_name = result.get('display_name', direccion)
                return (lat, lon, display_name)
        return None
    except Exception as e:
        return None


@st.cache_data(ttl=300)
def buscar_direcciones_sugerencias(texto, limite=8):
    """
    Busca direcciones y devuelve múltiples sugerencias (estilo Google Maps).
    Retorna lista de dict con lat, lon, display_name, tipo
    """
    if not texto or len(texto) < 3:
        return []

    try:
        # Añadir España si no está especificado
        if 'españa' not in texto.lower() and 'spain' not in texto.lower() and 'france' not in texto.lower():
            texto_buscar = f"{texto}, España"
        else:
            texto_buscar = texto

        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': texto_buscar,
            'format': 'json',
            'limit': limite,
            'addressdetails': 1
        }
        headers = {
            'User-Agent': 'CRM_Autocares_David/1.0'
        }

        response = requests.get(url, params=params, headers=headers, timeout=10, verify=False)
        if response.status_code == 200:
            data = response.json()
            sugerencias = []
            for result in data:
                # Extraer información relevante
                lat = float(result['lat'])
                lon = float(result['lon'])
                display_name = result.get('display_name', texto)
                tipo = result.get('type', '')
                clase = result.get('class', '')

                # Crear nombre corto
                address = result.get('address', {})
                nombre_corto = address.get('name') or address.get('road') or address.get('city') or display_name.split(',')[0]
                ciudad = address.get('city') or address.get('town') or address.get('village') or address.get('municipality', '')
                provincia = address.get('province') or address.get('state', '')

                # Formato amigable
                if ciudad and ciudad != nombre_corto:
                    nombre_display = f"{nombre_corto}, {ciudad}"
                else:
                    nombre_display = nombre_corto
                if provincia and provincia not in nombre_display:
                    nombre_display += f" ({provincia})"

                sugerencias.append({
                    'lat': lat,
                    'lon': lon,
                    'display_name': display_name,
                    'nombre_corto': nombre_display,
                    'tipo': tipo,
                    'clase': clase
                })
            return sugerencias
        return []
    except Exception as e:
        return []


# ============================================
# FUNCIONES GOOGLE PLACES API
# ============================================

def get_google_api_key():
    """Obtiene la API key de Google Maps desde la configuración."""
    from database import obtener_config_calc
    return obtener_config_calc('google_maps_api_key', '')


def google_places_autocomplete(texto, api_key=None):
    """
    Busca lugares usando Google Places Autocomplete API.
    Retorna lista de predicciones con place_id, descripcion, etc.
    """
    from database import registrar_uso_api

    if not texto or len(texto) < 2:
        return []

    if not api_key:
        api_key = get_google_api_key()

    if not api_key:
        return []

    try:
        url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
        params = {
            'input': texto,
            'key': api_key,
            'language': 'es',
            'components': 'country:es|country:fr|country:pt|country:ad',  # España, Francia, Portugal, Andorra
            'types': 'geocode|establishment'
        }

        response = requests.get(url, params=params, timeout=5)

        if response.status_code == 200:
            data = response.json()
            # Registrar uso de API
            registrar_uso_api('google_places', 1)

            if data.get('status') == 'OK':
                predicciones = []
                for pred in data.get('predictions', []):
                    predicciones.append({
                        'place_id': pred.get('place_id'),
                        'descripcion': pred.get('description'),
                        'texto_principal': pred.get('structured_formatting', {}).get('main_text', ''),
                        'texto_secundario': pred.get('structured_formatting', {}).get('secondary_text', ''),
                        'tipos': pred.get('types', [])
                    })
                return predicciones
            elif data.get('status') == 'ZERO_RESULTS':
                return []
        return []
    except Exception as e:
        return []


def google_place_details(place_id, api_key=None):
    """
    Obtiene detalles de un lugar usando su place_id.
    Retorna coordenadas, dirección formateada, etc.
    """
    from database import registrar_uso_api

    if not api_key:
        api_key = get_google_api_key()

    if not api_key or not place_id:
        return None

    try:
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            'place_id': place_id,
            'key': api_key,
            'language': 'es',
            'fields': 'geometry,formatted_address,name,address_components'
        }

        response = requests.get(url, params=params, timeout=5)

        if response.status_code == 200:
            data = response.json()
            # Registrar uso de API (Place Details es más caro pero lo contamos igual)
            registrar_uso_api('google_places', 1)

            if data.get('status') == 'OK':
                result = data.get('result', {})
                location = result.get('geometry', {}).get('location', {})
                return {
                    'lat': location.get('lat'),
                    'lon': location.get('lng'),
                    'direccion': result.get('formatted_address', ''),
                    'nombre': result.get('name', ''),
                    'place_id': place_id
                }
        return None
    except Exception as e:
        return None


def crear_autocomplete_component(key, placeholder, google_api_key):
    """
    Crea un componente HTML con Google Maps Autocomplete.
    Usa JavaScript para autocompletado fluido.
    """
    html_code = f'''
    <style>
        .pac-container {{
            z-index: 10000 !important;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        .autocomplete-wrapper {{
            position: relative;
            width: 100%;
        }}
        .autocomplete-input {{
            width: 100%;
            padding: 12px 15px;
            font-size: 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s;
            box-sizing: border-box;
        }}
        .autocomplete-input:focus {{
            border-color: #4CAF50;
            box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.1);
        }}
        .autocomplete-input::placeholder {{
            color: #999;
        }}
        .selected-place {{
            margin-top: 8px;
            padding: 10px 12px;
            background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
            border-radius: 6px;
            border-left: 4px solid #4CAF50;
            font-size: 14px;
            display: none;
        }}
        .selected-place.visible {{
            display: block;
        }}
        .selected-place .name {{
            font-weight: 600;
            color: #2e7d32;
        }}
        .selected-place .address {{
            color: #555;
            font-size: 12px;
            margin-top: 2px;
        }}
    </style>

    <div class="autocomplete-wrapper">
        <input
            type="text"
            id="autocomplete_{key}"
            class="autocomplete-input"
            placeholder="{placeholder}"
        />
        <div id="selected_{key}" class="selected-place">
            <div class="name" id="name_{key}"></div>
            <div class="address" id="address_{key}"></div>
        </div>
    </div>

    <script src="https://maps.googleapis.com/maps/api/js?key={google_api_key}&libraries=places&callback=initAutocomplete_{key}" async defer></script>

    <script>
        function initAutocomplete_{key}() {{
            const input = document.getElementById('autocomplete_{key}');
            const selectedDiv = document.getElementById('selected_{key}');
            const nameDiv = document.getElementById('name_{key}');
            const addressDiv = document.getElementById('address_{key}');

            const options = {{
                componentRestrictions: {{ country: ['es', 'fr', 'pt', 'ad'] }},
                fields: ['place_id', 'geometry', 'name', 'formatted_address'],
                types: ['geocode', 'establishment']
            }};

            const autocomplete = new google.maps.places.Autocomplete(input, options);

            autocomplete.addListener('place_changed', function() {{
                const place = autocomplete.getPlace();

                if (place.geometry) {{
                    // Mostrar lugar seleccionado
                    nameDiv.textContent = place.name || '';
                    addressDiv.textContent = place.formatted_address || '';
                    selectedDiv.classList.add('visible');

                    // Enviar datos a Streamlit
                    const data = {{
                        place_id: place.place_id,
                        name: place.name,
                        address: place.formatted_address,
                        lat: place.geometry.location.lat(),
                        lng: place.geometry.location.lng()
                    }};

                    // Guardar en sessionStorage para que Streamlit pueda leerlo
                    sessionStorage.setItem('selected_place_{key}', JSON.stringify(data));

                    // Trigger custom event
                    window.parent.postMessage({{
                        type: 'streamlit:setComponentValue',
                        key: '{key}',
                        value: data
                    }}, '*');
                }}
            }});
        }}
    </script>
    '''
    return html_code


@st.cache_data(ttl=3600)
def calcular_ruta_osrm(puntos):
    """
    Calcula la ruta por carretera usando OSRM (gratuito).
    puntos: lista de tuplas (lat, lon)
    Retorna: distancia en km, duracion en minutos, geometria de la ruta
    """
    if len(puntos) < 2:
        return None

    # Formatear coordenadas para OSRM (lon,lat)
    coords = ";".join([f"{p[1]},{p[0]}" for p in puntos])
    url = f"http://router.project-osrm.org/route/v1/driving/{coords}?overview=full&geometries=geojson"

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['code'] == 'Ok':
                route = data['routes'][0]
                distancia_km = route['distance'] / 1000
                duracion_min = route['duration'] / 60
                geometria = route['geometry']['coordinates']
                # Convertir a formato folium (lat, lon)
                ruta_coords = [(coord[1], coord[0]) for coord in geometria]
                return {
                    'distancia_km': round(distancia_km, 1),
                    'duracion_min': round(duracion_min, 0),
                    'ruta_coords': ruta_coords
                }
    except Exception as e:
        st.error(f"Error al calcular ruta: {e}")
    return None

def crear_mapa_ruta(puntos, nombres, ruta_coords=None):
    """Crea un mapa con los puntos y la ruta"""
    if not puntos:
        # Mapa centrado en País Vasco por defecto
        m = folium.Map(location=[43.0, -2.5], zoom_start=8)
        return m

    # Centrar mapa en el primer punto
    centro = puntos[0]
    m = folium.Map(location=centro, zoom_start=10)

    # Colores para los marcadores
    colores = ['green', 'blue', 'orange', 'purple', 'red']

    # Añadir marcadores
    for i, (punto, nombre) in enumerate(zip(puntos, nombres)):
        color = colores[0] if i == 0 else (colores[-1] if i == len(puntos)-1 else colores[1])
        icono = 'play' if i == 0 else ('stop' if i == len(puntos)-1 else 'pause')

        folium.Marker(
            location=punto,
            popup=nombre,
            tooltip=nombre,
            icon=folium.Icon(color=color, icon=icono, prefix='fa')
        ).add_to(m)

    # Añadir línea de ruta si existe
    if ruta_coords and len(ruta_coords) > 1:
        folium.PolyLine(
            ruta_coords,
            weight=4,
            color='blue',
            opacity=0.8
        ).add_to(m)

    # Ajustar zoom para mostrar todos los puntos
    if len(puntos) > 1:
        m.fit_bounds(puntos)

    return m

# Sidebar - Navegación con Logo DAVID
st.sidebar.image("logo-david-blanco.svg", width=180)
st.sidebar.markdown("")

# Info del usuario y logout
with st.sidebar:
    nombre_usuario = user.get('nombre') or user.get('email', '').split('@')[0]
    st.markdown(f"👤 **{nombre_usuario}**")
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        logout()
    st.divider()

# Lista de todas las páginas (ordenadas por naturaleza)
# 🎯 ACCIÓN → 📊 OPERATIVO → 👥 COMERCIAL → 📈 ANÁLISIS → ⚙️ CONFIGURACIÓN
TODAS_LAS_PAGINAS = [
    # Acción (lo primero)
    "Acciones",
    # Operativo (día a día)
    "Calculadora", "Pipeline", "Seguimiento Presupuestos",
    # Comercial
    "Clientes", "Campanas Segmentadas", "Incentivos",
    # Análisis
    "Dashboard", "Analisis Conversion", "Tiempo Anticipacion", "Analisis Mercado", "Flotas Competencia",
    # Configuración
    "Tarifas", "Configuracion"
]

# Filtrar páginas según permisos del usuario
paginas_disponibles = []
for pag in TODAS_LAS_PAGINAS:
    # Si tiene permiso para ver o no hay restricción explícita
    if permisos.get(pag, {}).get('ver', True):
        paginas_disponibles.append(pag)

# Si es admin, añadir panel de administración
if user.get('rol') == 'admin':
    paginas_disponibles.append("Admin")

pagina = st.sidebar.radio(
    "Navegación",
    paginas_disponibles,
    label_visibility="collapsed"
)

# Cargar datos con spinner
@st.cache_data(ttl=300, show_spinner="Cargando datos...")
def cargar_datos():
    return cargar_todos()

@st.cache_data(ttl=300, show_spinner="Cargando presupuestos...")
def cargar_actuales():
    return cargar_presupuestos_actuales()

@st.cache_data(ttl=300, show_spinner="Cargando clientes...")
def cargar_datos_clientes():
    return cargar_datos_con_clientes()

try:
    df = cargar_datos()
    df_actuales = cargar_actuales()
    df_con_clientes, df_clientes, df_metricas_clientes = cargar_datos_clientes()

    # Filtrar clientes desactivados de todos los DataFrames
    clientes_desactivados = obtener_clientes_desactivados()
    if clientes_desactivados:
        lista_desactivados = list(clientes_desactivados.keys())
        if 'Cliente' in df.columns:
            df = df[~df['Cliente'].isin(lista_desactivados)]
        if 'Cliente' in df_actuales.columns:
            df_actuales = df_actuales[~df_actuales['Cliente'].isin(lista_desactivados)]
        if 'Cliente' in df_con_clientes.columns:
            df_con_clientes = df_con_clientes[~df_con_clientes['Cliente'].isin(lista_desactivados)]
        if 'Cliente' in df_clientes.columns:
            df_clientes = df_clientes[~df_clientes['Cliente'].isin(lista_desactivados)]
        if 'Cliente' in df_metricas_clientes.columns:
            df_metricas_clientes = df_metricas_clientes[~df_metricas_clientes['Cliente'].isin(lista_desactivados)]
except Exception as e:
    st.error(f"Error cargando datos: {e}")
    st.stop()

# Función para obtener descripción de tipo de servicio
def get_tipo_descripcion(codigo):
    """Devuelve la descripción del tipo o el código si no está definido."""
    tipos = obtener_tipos_servicio_db()
    if codigo in tipos and tipos[codigo]['descripcion']:
        return tipos[codigo]['descripcion']
    return codigo

# ============================================
# PÁGINA: CENTRO DE ACCIONES
# ============================================
if pagina == "Acciones":
    st.title("🎯 Centro de Acciones")
    st.caption("Todo lo que necesita tu atención hoy")

    # Parámetros configurables
    DIAS_URGENTE = 7  # Presupuestos sin respuesta > 7 días = urgente
    DIAS_SEGUIMIENTO = 3  # Presupuestos sin respuesta > 3 días = seguimiento
    MESES_INACTIVO = 6  # Cliente sin actividad > 6 meses = a recuperar

    hoy = datetime.now()

    # --- FILTROS RÁPIDOS DE TIEMPO ---
    col_rapidos_acc = st.columns(6)

    # Calcular trimestre
    trim_actual = (hoy.month - 1) // 3 + 1
    inicio_trim = datetime(hoy.year, (trim_actual - 1) * 3 + 1, 1)

    periodos_acc = {
        "Este mes": (hoy.replace(day=1).date(), hoy.date()),
        "Mes ant.": ((hoy.replace(day=1) - timedelta(days=1)).replace(day=1).date(), (hoy.replace(day=1) - timedelta(days=1)).date()),
        "Este trim.": (inicio_trim.date(), hoy.date()),
        "Este año": (datetime(hoy.year, 1, 1).date(), hoy.date()),
        "Año ant.": (datetime(hoy.year-1, 1, 1).date(), datetime(hoy.year-1, 12, 31).date()),
        "Todo": None
    }

    if 'periodo_acc' not in st.session_state:
        st.session_state.periodo_acc = "Este año"

    for i, nombre in enumerate(periodos_acc.keys()):
        with col_rapidos_acc[i]:
            if st.button(nombre, key=f"btn_acc_{nombre}",
                        type="primary" if st.session_state.periodo_acc == nombre else "secondary",
                        use_container_width=True):
                st.session_state.periodo_acc = nombre
                st.rerun()

    # --- FILTROS POR FECHA ---
    col_fecha_tipo, col_fecha_desde, col_fecha_hasta = st.columns([1, 1, 1])

    with col_fecha_tipo:
        campo_fecha_acc = st.selectbox("Filtrar por", ["Fecha de alta", "Fecha de salida"], key="campo_fecha_acc")

    col_fecha_acc = 'Fecha alta' if campo_fecha_acc == "Fecha de alta" else 'Fecha Salida'

    # Calcular rango de fechas disponibles
    df['Fecha alta'] = pd.to_datetime(df['Fecha alta'], errors='coerce')
    df['Fecha Salida'] = pd.to_datetime(df['Fecha Salida'], errors='coerce')
    fechas_validas_acc = df[col_fecha_acc].dropna()

    if len(fechas_validas_acc) > 0:
        fecha_min_acc = fechas_validas_acc.min().date()
        fecha_max_acc = fechas_validas_acc.max().date()
    else:
        fecha_min_acc = hoy.date() - timedelta(days=365)
        fecha_max_acc = hoy.date()

    # Usar periodo rápido seleccionado o defaults
    if st.session_state.periodo_acc == "Todo":
        fecha_default_desde_acc = fecha_min_acc
        fecha_default_hasta_acc = fecha_max_acc
    elif st.session_state.periodo_acc in periodos_acc and periodos_acc[st.session_state.periodo_acc]:
        fecha_default_desde_acc = max(periodos_acc[st.session_state.periodo_acc][0], fecha_min_acc)
        fecha_default_hasta_acc = min(periodos_acc[st.session_state.periodo_acc][1], fecha_max_acc)
    else:
        fecha_default_desde_acc = max(datetime(hoy.year, 1, 1).date(), fecha_min_acc)
        fecha_default_hasta_acc = min(hoy.date(), fecha_max_acc)

    with col_fecha_desde:
        fecha_desde_acc = st.date_input("Desde", value=fecha_default_desde_acc, min_value=fecha_min_acc, max_value=fecha_max_acc, key="fecha_desde_acc")

    with col_fecha_hasta:
        fecha_hasta_acc = st.date_input("Hasta", value=fecha_default_hasta_acc, min_value=fecha_min_acc, max_value=fecha_max_acc, key="fecha_hasta_acc")

    # Aplicar filtro de fechas al DataFrame (incluir día completo hasta las 23:59:59)
    df_filtrado = df[
        (df[col_fecha_acc] >= pd.Timestamp(fecha_desde_acc)) &
        (df[col_fecha_acc] < pd.Timestamp(fecha_hasta_acc) + pd.Timedelta(days=1))
    ].copy()

    # Calcular periodo año anterior
    try:
        fecha_desde_ant_acc = fecha_desde_acc.replace(year=fecha_desde_acc.year - 1)
        fecha_hasta_ant_acc = fecha_hasta_acc.replace(year=fecha_hasta_acc.year - 1)
    except ValueError:
        fecha_desde_ant_acc = fecha_desde_acc.replace(year=fecha_desde_acc.year - 1, day=28)
        fecha_hasta_ant_acc = fecha_hasta_acc.replace(year=fecha_hasta_acc.year - 1, day=28)

    df_filtrado_ant = df[
        (df[col_fecha_acc] >= pd.Timestamp(fecha_desde_ant_acc)) &
        (df[col_fecha_acc] < pd.Timestamp(fecha_hasta_ant_acc) + pd.Timedelta(days=1))
    ].copy()

    st.caption(f"📊 Comparando con: {fecha_desde_ant_acc.strftime('%d/%m/%Y')} - {fecha_hasta_ant_acc.strftime('%d/%m/%Y')}")
    st.markdown("---")

    # Presupuestos enviados pendientes de respuesta (agrupados por Cod. Presupuesto)
    df_enviados = df_filtrado[df_filtrado['Estado presupuesto'] == 'E'].copy()
    df_enviados['Fecha alta'] = pd.to_datetime(df_enviados['Fecha alta'], errors='coerce')

    # Agrupar por Cod. Presupuesto para tratar cada presupuesto como unidad
    df_enviados_agrup = df_enviados.groupby('Cod. Presupuesto').agg({
        'Cliente': 'first',
        'Total importe': 'sum',
        'Fecha alta': 'first',
        'Atendido por': 'first'
    }).reset_index()
    df_enviados_agrup['Dias_Sin_Respuesta'] = (hoy - df_enviados_agrup['Fecha alta']).dt.days

    # Clasificar por urgencia
    urgentes = df_enviados_agrup[df_enviados_agrup['Dias_Sin_Respuesta'] >= DIAS_URGENTE].sort_values('Dias_Sin_Respuesta', ascending=False)
    seguimiento = df_enviados_agrup[(df_enviados_agrup['Dias_Sin_Respuesta'] >= DIAS_SEGUIMIENTO) & (df_enviados_agrup['Dias_Sin_Respuesta'] < DIAS_URGENTE)].sort_values('Dias_Sin_Respuesta', ascending=False)

    # Clientes inactivos que antes compraban (dentro del rango filtrado)
    df_aceptados = df_filtrado[df_filtrado['Estado presupuesto'].isin(['A', 'AP'])].copy()
    df_aceptados['Fecha alta'] = pd.to_datetime(df_aceptados['Fecha alta'], errors='coerce')

    if not df_aceptados.empty:
        ultima_compra = df_aceptados.groupby('Cliente').agg({
            'Fecha alta': 'max',
            'Total importe': 'sum',
            'Cod. Presupuesto': 'nunique'  # Contar presupuestos únicos, no líneas
        }).reset_index()
        ultima_compra.columns = ['Cliente', 'Ultima_Compra', 'Total_Historico', 'Num_Servicios']
        ultima_compra['Dias_Inactivo'] = (hoy - ultima_compra['Ultima_Compra']).dt.days
        inactivos = ultima_compra[ultima_compra['Dias_Inactivo'] >= MESES_INACTIVO * 30].sort_values('Total_Historico', ascending=False)
    else:
        inactivos = pd.DataFrame()

    # Clientes con varios presupuestos recientes (oportunidades calientes dentro del rango)
    df_reciente = df_filtrado[df_filtrado['Fecha alta'] >= (hoy - timedelta(days=30))].copy()
    if not df_reciente.empty:
        actividad_reciente = df_reciente.groupby('Cliente').agg({
            'Cod. Presupuesto': 'nunique',  # Contar presupuestos únicos, no líneas
            'Total importe': 'sum'
        }).reset_index()
        actividad_reciente.columns = ['Cliente', 'Presupuestos_Mes', 'Importe_Total']
        oportunidades = actividad_reciente[actividad_reciente['Presupuestos_Mes'] >= 2].sort_values('Importe_Total', ascending=False)
    else:
        oportunidades = pd.DataFrame()

    # --- MÉTRICAS AÑO ANTERIOR ---
    # Calcular métricas del año anterior para comparar
    if not df_filtrado_ant.empty:
        df_env_ant = df_filtrado_ant[df_filtrado_ant['Estado presupuesto'] == 'E']
        df_env_ant_agrup = df_env_ant.groupby('Cod. Presupuesto').first().reset_index() if not df_env_ant.empty else pd.DataFrame()
        urgentes_ant = len(df_env_ant_agrup) if not df_env_ant_agrup.empty else 0

        df_acept_ant = df_filtrado_ant[df_filtrado_ant['Estado presupuesto'].isin(['A', 'AP'])]
        aceptados_ant = df_acept_ant['Cod. Presupuesto'].nunique() if not df_acept_ant.empty else 0
        facturado_ant = df_acept_ant['Total importe'].sum() if not df_acept_ant.empty else 0
    else:
        urgentes_ant = aceptados_ant = facturado_ant = 0

    # Métricas actuales
    aceptados_actual = df_filtrado[df_filtrado['Estado presupuesto'].isin(['A', 'AP'])]['Cod. Presupuesto'].nunique()
    facturado_actual = df_filtrado[df_filtrado['Estado presupuesto'].isin(['A', 'AP'])]['Total importe'].sum()

    # Calcular deltas
    delta_aceptados = ((aceptados_actual - aceptados_ant) / aceptados_ant * 100) if aceptados_ant > 0 else None
    delta_facturado = ((facturado_actual - facturado_ant) / facturado_ant * 100) if facturado_ant > 0 else None

    # --- MÉTRICAS RESUMEN ---
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("🔴 Urgentes", len(urgentes), help=f"Sin respuesta >{DIAS_URGENTE} días")
    col2.metric("🟡 Seguimiento", len(seguimiento), help=f"Sin respuesta {DIAS_SEGUIMIENTO}-{DIAS_URGENTE} días")
    col3.metric("🔵 Recuperar", len(inactivos), help=f"Clientes inactivos >{MESES_INACTIVO} meses")
    col4.metric("🟢 Oportunidades", len(oportunidades), help="Clientes con +2 presupuestos este mes")
    col5.metric("✅ Aceptados", f"{aceptados_actual:,}",
                delta=f"{delta_aceptados:+.1f}% vs año ant." if delta_aceptados else None)
    col6.metric("💰 Facturado", f"{facturado_actual:,.0f}€",
                delta=f"{delta_facturado:+.1f}% vs año ant." if delta_facturado else None)

    st.markdown("---")

    # --- URGENTES ---
    with st.expander(f"🔴 URGENTE - Presupuestos sin respuesta (+{DIAS_URGENTE} días)", expanded=True):
        if not urgentes.empty:
            for idx, (_, row) in enumerate(urgentes.head(10).iterrows()):
                st.markdown(f"""
                <div style="background: #fdeaea; padding: 12px; border-radius: 8px; margin: 4px 0; border-left: 4px solid #dc3545;">
                    <strong>{row['Cod. Presupuesto']}</strong> · {row['Cliente']}<br>
                    <span style="color: #666;">💰 {row['Total importe']:,.0f}€ · ⏰ {int(row['Dias_Sin_Respuesta'])} días sin respuesta</span>
                </div>
                """, unsafe_allow_html=True)
            if len(urgentes) > 10:
                st.caption(f"+{len(urgentes) - 10} más...")
        else:
            st.success("✅ No hay presupuestos urgentes")

    # --- SEGUIMIENTO ---
    with st.expander(f"🟡 SEGUIMIENTO - Presupuestos pendientes ({DIAS_SEGUIMIENTO}-{DIAS_URGENTE} días)", expanded=True):
        if not seguimiento.empty:
            for _, row in seguimiento.head(10).iterrows():
                st.markdown(f"""
                <div style="background: #fff3e6; padding: 12px; border-radius: 8px; margin: 4px 0; border-left: 4px solid #fd7e14;">
                    <strong>{row['Cod. Presupuesto']}</strong> · {row['Cliente']}<br>
                    <span style="color: #666;">💰 {row['Total importe']:,.0f}€ · ⏰ {int(row['Dias_Sin_Respuesta'])} días</span>
                </div>
                """, unsafe_allow_html=True)
            if len(seguimiento) > 10:
                st.caption(f"+{len(seguimiento) - 10} más...")
        else:
            st.success("✅ No hay presupuestos pendientes de seguimiento")

    # --- CLIENTES A RECUPERAR ---
    with st.expander(f"🔵 RECUPERAR - Clientes inactivos (+{MESES_INACTIVO} meses)", expanded=False):
        if not inactivos.empty:
            for _, row in inactivos.head(10).iterrows():
                meses_inactivo = int(row['Dias_Inactivo'] / 30)
                st.markdown(f"""
                <div style="background: #e7f1ff; padding: 12px; border-radius: 8px; margin: 4px 0; border-left: 4px solid #0d6efd;">
                    <strong>{row['Cliente']}</strong><br>
                    <span style="color: #666;">📊 {int(row['Num_Servicios'])} servicios · 💰 {row['Total_Historico']:,.0f}€ histórico · ⏰ {meses_inactivo} meses inactivo</span>
                </div>
                """, unsafe_allow_html=True)
            if len(inactivos) > 10:
                st.caption(f"+{len(inactivos) - 10} más...")
        else:
            st.info("No hay clientes inactivos a recuperar")

    # --- OPORTUNIDADES ---
    with st.expander("🟢 OPORTUNIDADES - Clientes activos este mes", expanded=False):
        if not oportunidades.empty:
            for _, row in oportunidades.head(10).iterrows():
                st.markdown(f"""
                <div style="background: #e8f5e9; padding: 12px; border-radius: 8px; margin: 4px 0; border-left: 4px solid #198754;">
                    <strong>{row['Cliente']}</strong><br>
                    <span style="color: #666;">📝 {int(row['Presupuestos_Mes'])} presupuestos este mes · 💰 {row['Importe_Total']:,.0f}€</span>
                </div>
                """, unsafe_allow_html=True)
            if len(oportunidades) > 10:
                st.caption(f"+{len(oportunidades) - 10} más...")
        else:
            st.info("No hay oportunidades destacadas este mes")

    st.markdown("---")

    # --- RESUMEN DEL DÍA ---
    st.subheader("📋 Resumen de Acciones")

    total_acciones = len(urgentes) + len(seguimiento)
    importe_en_juego = urgentes['Total importe'].sum() + seguimiento['Total importe'].sum()

    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.metric("Presupuestos pendientes de acción", total_acciones)
    with col_res2:
        st.metric("Importe en juego", f"{importe_en_juego:,.0f} €")


# ============================================
# PÁGINA 1: DASHBOARD
# ============================================
elif pagina == "Dashboard":
    col_titulo, col_recargar = st.columns([4, 1])
    with col_titulo:
        st.title("Dashboard Principal")
    with col_recargar:
        if st.button("🔄 Recargar Datos", help="Recarga los datos del Excel"):
            st.cache_data.clear()
            st.success("Datos recargados!")
            st.rerun()

    # ========== FILTROS RAPIDOS ==========
    st.subheader("Periodo")

    # Filtros rápidos de tiempo
    hoy = datetime.now()

    col_rapidos = st.columns(8)

    # Calcular trimestres
    trimestre_actual = (hoy.month - 1) // 3 + 1
    inicio_trim_actual = datetime(hoy.year, (trimestre_actual - 1) * 3 + 1, 1)

    if trimestre_actual == 1:
        inicio_trim_anterior = datetime(hoy.year - 1, 10, 1)
        fin_trim_anterior = datetime(hoy.year - 1, 12, 31)
    else:
        inicio_trim_anterior = datetime(hoy.year, (trimestre_actual - 2) * 3 + 1, 1)
        fin_trim_anterior = inicio_trim_actual - timedelta(days=1)

    # Definir períodos
    periodos = {
        "Este mes": (hoy.replace(day=1), hoy),
        "Mes anterior": ((hoy.replace(day=1) - timedelta(days=1)).replace(day=1), hoy.replace(day=1) - timedelta(days=1)),
        "Este trim.": (inicio_trim_actual, hoy),
        "Trim. anterior": (inicio_trim_anterior, fin_trim_anterior),
        "Este año": (hoy.replace(month=1, day=1), hoy),
        "Año anterior": (datetime(hoy.year-1, 1, 1), datetime(hoy.year-1, 12, 31)),
        "Ult. 6 meses": (hoy - timedelta(days=180), hoy),
        "Todo": (df['Fecha alta'].min(), hoy)
    }

    # Inicializar estado si no existe
    if 'periodo_seleccionado' not in st.session_state:
        st.session_state.periodo_seleccionado = "Este año"

    # Botones de período rápido
    for i, (nombre, fechas) in enumerate(periodos.items()):
        with col_rapidos[i]:
            if st.button(nombre, key=f"btn_{nombre}",
                        type="primary" if st.session_state.periodo_seleccionado == nombre else "secondary"):
                st.session_state.periodo_seleccionado = nombre
                st.session_state.fecha_inicio = fechas[0]
                st.session_state.fecha_fin = fechas[1]
                st.rerun()

    # Obtener fechas del período seleccionado
    periodo_actual = periodos.get(st.session_state.periodo_seleccionado, periodos["Este año"])
    fecha_inicio_default = periodo_actual[0]
    fecha_fin_default = periodo_actual[1]

    st.markdown("---")
    st.subheader("Filtros")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        # Selector de tipo de fecha
        tipo_fecha = st.radio(
            "Filtrar por",
            ["Fecha alta", "Fecha Salida"],
            horizontal=True,
            help="Fecha alta = fecha del presupuesto, Fecha Salida = fecha del servicio"
        )

        # Filtro de fechas personalizado
        col_fecha = tipo_fecha
        fecha_min = pd.to_datetime(df[col_fecha].min()).date()
        fecha_max_data = pd.to_datetime(df[col_fecha].max()).date()
        fecha_max = max(fecha_max_data, datetime.now().date())  # Incluir hoy si es mayor
        # Convertir defaults a date si son datetime
        fecha_ini_date = fecha_inicio_default.date() if hasattr(fecha_inicio_default, 'date') else fecha_inicio_default
        fecha_fin_date = fecha_fin_default.date() if hasattr(fecha_fin_default, 'date') else fecha_fin_default
        # Asegurar que los valores default estan dentro del rango
        fecha_inicio_adj = max(fecha_ini_date, fecha_min) if fecha_min else fecha_ini_date
        fecha_fin_adj = min(fecha_fin_date, fecha_max) if fecha_max else fecha_fin_date
        rango_fecha = st.date_input(
            "Rango de fechas",
            value=(fecha_inicio_adj, fecha_fin_adj),
            min_value=fecha_min,
            max_value=fecha_max,
            format="DD/MM/YYYY"
        )

    with col2:
        # Obtener tipos con sus descripciones
        tipos_guardados = obtener_tipos_servicio_db()
        codigos_unicos = sorted(df['Tipo Servicio'].dropna().unique().tolist())

        # Crear mapeo código -> descripción
        opciones_tipo = {'Todos': 'Todos'}
        for codigo in codigos_unicos:
            desc = tipos_guardados.get(codigo, {}).get('descripcion', '')
            opciones_tipo[codigo] = normalizar_texto(desc) if desc else codigo

        # Mostrar descripciones en el selectbox
        descripciones_unicas = ['Todos'] + sorted(set([v for k, v in opciones_tipo.items() if k != 'Todos']))
        tipo_desc_sel = st.selectbox("Tipo de Servicio", descripciones_unicas)

        # Encontrar todos los códigos que corresponden a esa descripción
        if tipo_desc_sel == 'Todos':
            tipo_sel = 'Todos'
        else:
            tipo_sel = tipo_desc_sel  # Usamos la descripción para filtrar

    with col3:
        grupos = obtener_grupos_clientes(df)
        grupo_sel = st.selectbox("Grupo de Clientes", grupos)

    with col4:
        comerciales = obtener_comerciales(df)
        comercial_sel = st.selectbox("Comercial", comerciales)

    with col5:
        segmento_sel = st.selectbox("Segmento Cliente", SEGMENTOS_CLIENTE)

    # Leyenda de segmentos
    with st.expander("Ver definicion de segmentos"):
        st.markdown(f"""
        | Segmento | Definicion |
        |----------|------------|
        | **HABITUAL** | Ultimo servicio en ultimos {DEFAULT_PARAMS['active_months']} meses Y ({DEFAULT_PARAMS['habitual_min_services_12m']}+ servicios/12m O {DEFAULT_PARAMS['habitual_min_services_24m']}+ servicios/24m O {DEFAULT_PARAMS['habitual_min_revenue_24m']:,}+ EUR/24m) |
        | **OCASIONAL_ACTIVO** | Ultimo servicio en ultimos {DEFAULT_PARAMS['active_months']} meses, pero no cumple criterios de habitual |
        | **REACTIVADO** | Volvio en ultimos {DEFAULT_PARAMS['active_months']} meses tras estar inactivo |
        | **PROSPECTO** | Cliente presupuestado sin servicios aceptados |
        | **INACTIVO** | Sin actividad en mas de {DEFAULT_PARAMS['inactive_months']} meses |
        """)

    # Aplicar filtros - usar df_con_clientes que tiene Tipo_Cliente
    df_filtrado = df_con_clientes.copy()

    if len(rango_fecha) == 2:
        df_filtrado = df_filtrado[
            (df_filtrado[col_fecha] >= pd.Timestamp(rango_fecha[0])) &
            (df_filtrado[col_fecha] < pd.Timestamp(rango_fecha[1]) + pd.Timedelta(days=1))
        ]

    if tipo_sel != 'Todos':
        # Filtrar por descripción: encontrar todos los códigos que tienen esa descripción
        codigos_filtrar = [cod for cod, desc in opciones_tipo.items() if desc == tipo_sel]
        df_filtrado = df_filtrado[df_filtrado['Tipo Servicio'].isin(codigos_filtrar)]

    if grupo_sel != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Grupo de clientes'] == grupo_sel]

    if comercial_sel != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Atendido por'] == comercial_sel]

    if segmento_sel != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Segmento_Cliente'] == segmento_sel]

    # ========== CALCULAR PERIODO AÑO ANTERIOR ==========
    if len(rango_fecha) == 2:
        fecha_ini = rango_fecha[0]
        fecha_fin = rango_fecha[1]
        # Mismo periodo del año anterior
        try:
            fecha_ini_anterior = fecha_ini.replace(year=fecha_ini.year - 1)
            fecha_fin_anterior = fecha_fin.replace(year=fecha_fin.year - 1)
        except ValueError:  # Para 29 de febrero
            fecha_ini_anterior = fecha_ini.replace(year=fecha_ini.year - 1, day=28)
            fecha_fin_anterior = fecha_fin.replace(year=fecha_fin.year - 1, day=28)

        # Filtrar datos del año anterior
        df_anterior = df_con_clientes[
            (df_con_clientes[col_fecha] >= pd.Timestamp(fecha_ini_anterior)) &
            (df_con_clientes[col_fecha] < pd.Timestamp(fecha_fin_anterior) + pd.Timedelta(days=1))
        ].copy()

        # Aplicar mismos filtros
        if tipo_sel != 'Todos':
            codigos_filtrar = [cod for cod, desc in opciones_tipo.items() if desc == tipo_sel]
            df_anterior = df_anterior[df_anterior['Tipo Servicio'].isin(codigos_filtrar)]
        if grupo_sel != 'Todos':
            df_anterior = df_anterior[df_anterior['Grupo de clientes'] == grupo_sel]
        if comercial_sel != 'Todos':
            df_anterior = df_anterior[df_anterior['Atendido por'] == comercial_sel]
        if segmento_sel != 'Todos':
            df_anterior = df_anterior[df_anterior['Segmento_Cliente'] == segmento_sel]
    else:
        df_anterior = pd.DataFrame()

    st.markdown("---")

    # Mostrar periodo de comparación
    if len(rango_fecha) == 2 and not df_anterior.empty:
        st.caption(f"📊 Comparando con el mismo periodo del año anterior: {fecha_ini_anterior.strftime('%d/%m/%Y')} - {fecha_fin_anterior.strftime('%d/%m/%Y')}")

    # ========== KPIs PRINCIPALES ==========
    kpis = obtener_kpis(df_filtrado)
    kpis_anterior = obtener_kpis(df_anterior) if not df_anterior.empty else None

    # Función para calcular delta
    def calcular_delta(actual, anterior):
        if anterior and anterior > 0:
            return ((actual - anterior) / anterior) * 100
        return None

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        delta_presup = calcular_delta(kpis['total_presupuestos'], kpis_anterior['total_presupuestos'] if kpis_anterior else 0)
        st.metric("Total Presupuestos", f"{kpis['total_presupuestos']:,}",
                  delta=f"{delta_presup:+.1f}% vs año ant." if delta_presup is not None else None)

    with col2:
        delta_acept = calcular_delta(kpis['aceptados'], kpis_anterior['aceptados'] if kpis_anterior else 0)
        st.metric("Aceptados (A+AP)", f"{kpis['aceptados']:,}",
                  delta=f"{delta_acept:+.1f}% vs año ant." if delta_acept is not None else None)

    with col3:
        delta_rech = calcular_delta(kpis['rechazados'], kpis_anterior['rechazados'] if kpis_anterior else 0)
        st.metric("Rechazados", f"{kpis['rechazados']:,}",
                  delta=f"{delta_rech:+.1f}% vs año ant." if delta_rech is not None else None,
                  delta_color="inverse")

    with col4:
        delta_pend = calcular_delta(kpis['pendientes'], kpis_anterior['pendientes'] if kpis_anterior else 0)
        st.metric("Pendientes", f"{kpis['pendientes']:,}",
                  delta=f"{delta_pend:+.1f}% vs año ant." if delta_pend is not None else None,
                  delta_color="off")

    with col5:
        delta_tasa = kpis['tasa_conversion'] - (kpis_anterior['tasa_conversion'] if kpis_anterior else 0)
        st.metric("TASA CONVERSION", f"{kpis['tasa_conversion']:.1f}%",
                  delta=f"{delta_tasa:+.1f}pp vs año ant." if kpis_anterior else None)

    col1, col2 = st.columns(2)

    with col1:
        delta_fact = calcular_delta(kpis['importe_aceptado'], kpis_anterior['importe_aceptado'] if kpis_anterior else 0)
        st.metric("Importe Facturado (A+AP)", f"{kpis['importe_aceptado']:,.0f} EUR",
                  delta=f"{delta_fact:+.1f}% vs año ant." if delta_fact is not None else None)

    with col2:
        delta_total = calcular_delta(kpis['importe_total'], kpis_anterior['importe_total'] if kpis_anterior else 0)
        st.metric("Importe Total Presupuestado", f"{kpis['importe_total']:,.0f} EUR",
                  delta=f"{delta_total:+.1f}% vs año ant." if delta_total is not None else None)

    # KPIs de segmentos de clientes
    st.markdown("**Segmentos de clientes en el periodo:**")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        n_habitual = df_filtrado[df_filtrado['Segmento_Cliente'] == 'HABITUAL']['Código'].nunique()
        st.metric("Habitual", f"{n_habitual:,}", help="Activo con alta frecuencia/facturacion")

    with col2:
        n_ocasional = df_filtrado[df_filtrado['Segmento_Cliente'] == 'OCASIONAL_ACTIVO']['Código'].nunique()
        st.metric("Ocasional", f"{n_ocasional:,}", help="Activo con baja frecuencia")

    with col3:
        n_reactivado = df_filtrado[df_filtrado['Segmento_Cliente'] == 'REACTIVADO']['Código'].nunique()
        st.metric("Reactivado", f"{n_reactivado:,}", help="Volvio tras inactividad")

    with col4:
        n_prospecto = df_filtrado[df_filtrado['Segmento_Cliente'] == 'PROSPECTO']['Código'].nunique()
        st.metric("Prospecto", f"{n_prospecto:,}", help="Presupuestado sin servicios aceptados")

    with col5:
        n_inactivo = df_filtrado[df_filtrado['Segmento_Cliente'] == 'INACTIVO']['Código'].nunique()
        st.metric("Inactivo", f"{n_inactivo:,}", help="Sin actividad >24 meses")

    st.markdown("---")

    # ========== ANALISIS POR TIPO DE SERVICIO ==========
    st.subheader("Conversion por Tipo de Servicio")

    # Obtener descripciones guardadas
    tipos_guardados = obtener_tipos_servicio_db()

    # Añadir columna de descripción al dataframe filtrado
    # Normalizar a "Primera mayúscula" para agrupar "Disposiciones" y "DISPOSICIONES" como uno solo
    df_con_desc = df_filtrado.copy()
    df_con_desc['Tipo Descripcion'] = df_con_desc['Tipo Servicio'].apply(
        lambda x: normalizar_texto(tipos_guardados.get(x, {}).get('descripcion', '') or x) if pd.notna(x) else 'Sin definir'
    )

    # Agrupar por DESCRIPCION (no por código) - contando presupuestos únicos
    # Presupuestos únicos por tipo
    presup_por_tipo = df_con_desc.groupby('Tipo Descripcion')['Cod. Presupuesto'].nunique().reset_index()
    presup_por_tipo.columns = ['Tipo Servicio', 'Total']

    # Presupuestos aceptados únicos por tipo
    df_aceptados_tipo = df_con_desc[df_con_desc['Estado presupuesto'].isin(['A', 'AP'])]
    acept_por_tipo = df_aceptados_tipo.groupby('Tipo Descripcion')['Cod. Presupuesto'].nunique().reset_index()
    acept_por_tipo.columns = ['Tipo Servicio', 'Aceptados']

    # Importe total y aceptado
    importe_total_tipo = df_con_desc.groupby('Tipo Descripcion')['Total importe'].sum().reset_index()
    importe_total_tipo.columns = ['Tipo Servicio', 'Importe Total']

    importe_aceptado_tipo = df_aceptados_tipo.groupby('Tipo Descripcion')['Total importe'].sum().reset_index()
    importe_aceptado_tipo.columns = ['Tipo Servicio', 'Importe Aceptado']

    # Combinar
    tipos_stats = presup_por_tipo.merge(acept_por_tipo, on='Tipo Servicio', how='left')
    tipos_stats = tipos_stats.merge(importe_total_tipo, on='Tipo Servicio', how='left')
    tipos_stats = tipos_stats.merge(importe_aceptado_tipo, on='Tipo Servicio', how='left')
    tipos_stats = tipos_stats.fillna(0)

    tipos_stats['Total'] = pd.to_numeric(tipos_stats['Total'], errors='coerce').fillna(0).astype(int)
    tipos_stats['Aceptados'] = pd.to_numeric(tipos_stats['Aceptados'], errors='coerce').fillna(0).astype(int)
    tipos_stats['Tasa Conversion'] = (tipos_stats['Aceptados'] / tipos_stats['Total'].replace(0, 1) * 100).round(1)
    tipos_stats = tipos_stats.sort_values('Total', ascending=False).head(15)

    # Para mostrar qué códigos incluye cada descripción
    codigos_por_desc = df_con_desc.groupby('Tipo Descripcion')['Tipo Servicio'].apply(lambda x: ', '.join(sorted(x.dropna().unique()))).to_dict()
    tipos_stats['Codigos'] = tipos_stats['Tipo Servicio'].map(codigos_por_desc)

    col1, col2 = st.columns(2)

    with col1:
        # Grafico de barras: Total vs Aceptados por tipo
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Total Presupuestos',
            x=tipos_stats['Tipo Servicio'],
            y=tipos_stats['Total'],
            marker_color='lightblue'
        ))
        fig.add_trace(go.Bar(
            name='Aceptados',
            x=tipos_stats['Tipo Servicio'],
            y=tipos_stats['Aceptados'],
            marker_color='green'
        ))
        fig.update_layout(
            barmode='group',
            height=400,
            title="Presupuestos por Tipo de Servicio",
            xaxis_title="Tipo de Servicio",
            yaxis_title="Cantidad"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Grafico de tasa de conversion
        fig = px.bar(
            tipos_stats,
            x='Tipo Servicio',
            y='Tasa Conversion',
            color='Tasa Conversion',
            color_continuous_scale='RdYlGn',
            title="Tasa de Conversion por Tipo de Servicio (%)"
        )
        fig.update_layout(height=400)
        fig.add_hline(y=kpis['tasa_conversion'], line_dash="dash",
                      annotation_text=f"Media: {kpis['tasa_conversion']:.1f}%")
        st.plotly_chart(fig, use_container_width=True)

    # Tabla detallada - muestra descripción y qué códigos agrupa
    st.dataframe(
        tipos_stats[['Tipo Servicio', 'Codigos', 'Total', 'Aceptados', 'Tasa Conversion', 'Importe Total', 'Importe Aceptado']].style.format({
            'Tasa Conversion': '{:.1f}%',
            'Importe Total': '{:,.0f} EUR',
            'Importe Aceptado': '{:,.0f} EUR'
        }),
        use_container_width=True,
        height=300
    )

    st.markdown("---")

    # ========== GRAFICOS ADICIONALES ==========
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Distribucion por Estado")
        estados = df_filtrado['Estado presupuesto'].value_counts()
        # DAVID Brand color palette for pie charts
        david_palette = ['#000000', '#F15025', '#424242', '#757575', '#E0E0E0', '#F5F5F5']
        fig = px.pie(
            values=estados.values,
            names=[ESTADOS_PRESUPUESTO.get(e, e) for e in estados.index],
            hole=0.4,
            color_discrete_sequence=david_palette
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Top 10 Grupos de Clientes")
        grupos_chart = df_filtrado['Grupo de clientes'].value_counts().head(10).reset_index()
        grupos_chart.columns = ['Grupo', 'Cantidad']
        fig = px.bar(
            grupos_chart,
            x='Cantidad',
            y='Grupo',
            orientation='h',
            color='Cantidad',
            color_continuous_scale=[[0, '#E0E0E0'], [1, '#000000']]  # DAVID Brand grayscale
        )
        fig.update_layout(height=350, showlegend=False, yaxis={'categoryorder': 'total ascending'})
        fig.update_xaxes(title="Numero de presupuestos")
        fig.update_yaxes(title="")
        st.plotly_chart(fig, use_container_width=True)

    # Tendencia mensual con comparativa año anterior
    st.subheader("Tendencia Mensual (vs Año Anterior)")

    # Datos año actual
    df_tendencia = df_filtrado[df_filtrado['Fecha alta'].notna()].copy()
    df_tendencia['Mes'] = df_tendencia['Fecha alta'].dt.to_period('M').astype(str)
    df_tendencia['MesNum'] = df_tendencia['Fecha alta'].dt.month

    presup_mes = df_tendencia.groupby(['Mes', 'MesNum'])['Cod. Presupuesto'].nunique().reset_index()
    presup_mes.columns = ['Mes', 'MesNum', 'Total']

    df_tendencia_acept = df_tendencia[df_tendencia['Estado presupuesto'].isin(['A', 'AP'])]
    acept_mes = df_tendencia_acept.groupby('Mes')['Cod. Presupuesto'].nunique().reset_index()
    acept_mes.columns = ['Mes', 'Aceptados']

    tendencia_mes = presup_mes.merge(acept_mes, on='Mes', how='left')
    tendencia_mes['Aceptados'] = tendencia_mes['Aceptados'].fillna(0).astype(int)
    tendencia_mes['Tasa'] = (tendencia_mes['Aceptados'] / tendencia_mes['Total'].replace(0, 1) * 100).round(1)
    tendencia_mes['Mes_ES'] = tendencia_mes['Mes'].apply(formato_mes_es)

    # Datos año anterior
    if not df_anterior.empty:
        df_tend_ant = df_anterior[df_anterior['Fecha alta'].notna()].copy()
        df_tend_ant['Mes'] = df_tend_ant['Fecha alta'].dt.to_period('M').astype(str)
        df_tend_ant['MesNum'] = df_tend_ant['Fecha alta'].dt.month

        presup_ant = df_tend_ant.groupby('MesNum')['Cod. Presupuesto'].nunique().reset_index()
        presup_ant.columns = ['MesNum', 'Total_Anterior']

        df_tend_ant_acept = df_tend_ant[df_tend_ant['Estado presupuesto'].isin(['A', 'AP'])]
        acept_ant = df_tend_ant_acept.groupby('MesNum')['Cod. Presupuesto'].nunique().reset_index()
        acept_ant.columns = ['MesNum', 'Aceptados_Anterior']

        tendencia_ant = presup_ant.merge(acept_ant, on='MesNum', how='left')
        tendencia_ant['Aceptados_Anterior'] = tendencia_ant['Aceptados_Anterior'].fillna(0).astype(int)

        # Merge con datos actuales por número de mes
        tendencia_mes = tendencia_mes.merge(tendencia_ant, on='MesNum', how='left')
        tendencia_mes['Total_Anterior'] = tendencia_mes['Total_Anterior'].fillna(0).astype(int)
        tendencia_mes['Aceptados_Anterior'] = tendencia_mes['Aceptados_Anterior'].fillna(0).astype(int)
    else:
        tendencia_mes['Total_Anterior'] = 0
        tendencia_mes['Aceptados_Anterior'] = 0

    fig = go.Figure()

    # Barras año anterior (más claras, atrás)
    fig.add_trace(go.Bar(x=tendencia_mes['Mes_ES'], y=tendencia_mes['Total_Anterior'],
                         name='Total Año Ant.', marker_color='rgba(173, 216, 230, 0.5)', opacity=0.6))
    fig.add_trace(go.Bar(x=tendencia_mes['Mes_ES'], y=tendencia_mes['Aceptados_Anterior'],
                         name='Aceptados Año Ant.', marker_color='rgba(144, 238, 144, 0.5)', opacity=0.6))

    # Barras año actual (colores sólidos)
    fig.add_trace(go.Bar(x=tendencia_mes['Mes_ES'], y=tendencia_mes['Total'], name='Total Actual', marker_color='steelblue'))
    fig.add_trace(go.Bar(x=tendencia_mes['Mes_ES'], y=tendencia_mes['Aceptados'], name='Aceptados Actual', marker_color='green'))

    # Línea de tasa
    fig.add_trace(go.Scatter(x=tendencia_mes['Mes_ES'], y=tendencia_mes['Tasa'], name='Tasa % Actual', yaxis='y2', line=dict(color='red', width=3)))

    fig.update_layout(
        barmode='group',
        height=450,
        yaxis=dict(title="Cantidad"),
        yaxis2=dict(title="Tasa Conversion %", overlaying='y', side='right', range=[0, 100]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

    # ========== TABLA DE VERIFICACIÓN DE DATOS ==========
    st.markdown("---")
    st.subheader("Tabla de Verificacion de Datos")

    with st.expander("Ver datos filtrados para verificacion", expanded=False):
        # Mostrar los datos filtrados según los filtros aplicados en el dashboard
        if len(rango_fecha) == 2:
            st.markdown(f"**Periodo:** {rango_fecha[0]} a {rango_fecha[1]}")
        else:
            st.markdown(f"**Periodo:** {rango_fecha[0]}")

        if len(df_filtrado) > 0:
            # Seleccionar columnas relevantes para mostrar
            columnas_mostrar = ['Cod. Presupuesto', 'Fecha alta', 'Cliente', 'Tipo Servicio',
                                'Estado', 'Total importe', 'Atendido por', 'Grupo de clientes']
            columnas_disponibles = [c for c in columnas_mostrar if c in df_filtrado.columns]

            df_mostrar = df_filtrado[columnas_disponibles].copy()

            # Formatear fechas para mejor visualización
            for col in ['Fecha alta']:
                if col in df_mostrar.columns:
                    df_mostrar[col] = pd.to_datetime(df_mostrar[col]).dt.strftime('%Y-%m-%d')

            # Filtros adicionales para la tabla
            col1, col2, col3 = st.columns(3)

            with col1:
                filtro_estado = st.multiselect(
                    "Filtrar por Estado",
                    options=df_mostrar['Estado'].dropna().unique().tolist(),
                    default=[],
                    key="tabla_filtro_estado"
                )
            with col2:
                if 'Atendido por' in df_mostrar.columns:
                    filtro_comercial = st.multiselect(
                        "Filtrar por Comercial",
                        options=df_mostrar['Atendido por'].dropna().unique().tolist(),
                        default=[],
                        key="tabla_filtro_comercial"
                    )
                else:
                    filtro_comercial = []
            with col3:
                buscar_texto = st.text_input("Buscar en Cliente/Codigo", "", key="tabla_buscar")

            # Aplicar filtros
            df_tabla = df_mostrar.copy()

            if filtro_estado:
                df_tabla = df_tabla[df_tabla['Estado'].isin(filtro_estado)]

            if filtro_comercial and 'Atendido por' in df_tabla.columns:
                df_tabla = df_tabla[df_tabla['Atendido por'].isin(filtro_comercial)]

            if buscar_texto:
                mask = (
                    df_tabla['Cliente'].str.contains(buscar_texto, case=False, na=False) |
                    df_tabla['Cod Presupuesto'].str.contains(buscar_texto, case=False, na=False)
                )
                df_tabla = df_tabla[mask]

            # Mostrar estadísticas de la tabla filtrada
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Registros mostrados", len(df_tabla))
            with col2:
                importe_total = df_tabla['Importe'].sum() if 'Importe' in df_tabla.columns else 0
                st.metric("Importe Total", f"{importe_total:,.0f}€")
            with col3:
                if 'Importe Factura' in df_tabla.columns:
                    fact_total = df_tabla['Importe Factura'].sum()
                    st.metric("Facturado Total", f"{fact_total:,.0f}€")
            with col4:
                aceptados = len(df_tabla[df_tabla['Estado'] == 'A']) if 'Estado' in df_tabla.columns else 0
                st.metric("Aceptados", aceptados)

            # Mostrar tabla con opción de ordenar
            st.dataframe(
                df_tabla.sort_values('Fecha alta', ascending=False).head(500),
                use_container_width=True,
                height=400
            )

            # Botón de exportar
            csv = df_tabla.to_csv(index=False).encode('utf-8')
            fecha_csv = f"{rango_fecha[0]}_{rango_fecha[1]}" if len(rango_fecha) == 2 else str(rango_fecha[0])
            st.download_button(
                label="Descargar datos en CSV",
                data=csv,
                file_name=f"verificacion_datos_{fecha_csv}.csv",
                mime="text/csv"
            )
        else:
            st.warning("No hay datos para el periodo seleccionado")


# ============================================
# PÁGINA 2: TIEMPO DE ANTICIPACIÓN
# ============================================
elif pagina == "Tiempo Anticipacion":
    st.title("Tiempo de Anticipacion")
    st.markdown("Analisis del tiempo entre la solicitud del presupuesto y la fecha del servicio")
    st.markdown("---")

    # Obtener tipos de servicio guardados
    tipos_guardados = obtener_tipos_servicio_db()

    # Obtener estadísticas de anticipación
    stats_anticipacion = obtener_anticipacion_por_tipo(df, tipos_guardados)

    if stats_anticipacion.empty:
        st.warning("No hay datos suficientes para calcular tiempos de anticipacion")
    else:
        # KPIs principales
        df_anticipacion = calcular_tiempo_anticipacion(df, solo_aceptados=True)
        media_global_dias = df_anticipacion['Dias_Anticipacion'].mean()
        media_global_meses = df_anticipacion['Meses_Anticipacion'].mean()
        mediana_global = df_anticipacion['Dias_Anticipacion'].median()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Anticipacion Media", f"{media_global_meses:.1f} meses",
                      help=f"{media_global_dias:.0f} dias")

        with col2:
            st.metric("Anticipacion Mediana", f"{mediana_global / 30.44:.1f} meses",
                      help=f"{mediana_global:.0f} dias")

        with col3:
            st.metric("Total Servicios Analizados", f"{len(df_anticipacion):,}")

        with col4:
            # Tipo con mayor anticipación
            tipo_max = stats_anticipacion.nlargest(1, 'Meses_Media')
            if not tipo_max.empty:
                st.metric("Mayor Anticipacion",
                         f"{tipo_max['Tipo Servicio'].values[0]}",
                         f"{tipo_max['Meses_Media'].values[0]} meses")

        st.markdown("---")

        # ========== GRÁFICO PRINCIPAL: ANTICIPACIÓN POR TIPO ==========
        st.subheader("Anticipacion por Tipo de Servicio")

        col1, col2 = st.columns(2)

        with col1:
            # Ordenar por meses de anticipación media
            stats_ordenadas = stats_anticipacion.nlargest(15, 'Meses_Media')

            fig = px.bar(
                stats_ordenadas,
                y='Tipo Servicio',
                x='Meses_Media',
                orientation='h',
                color='Meses_Media',
                color_continuous_scale='RdYlGn_r',
                title="Meses de anticipacion promedio por tipo",
                text='Meses_Media'
            )
            fig.update_traces(texttemplate='%{text:.1f}m', textposition='outside')
            fig.update_layout(
                height=500,
                yaxis={'categoryorder': 'total ascending'},
                xaxis_title="Meses de anticipacion",
                yaxis_title=""
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Box plot de distribución
            # Primero añadir descripción a df_anticipacion
            df_anticipacion_desc = df_anticipacion.copy()
            df_anticipacion_desc['Tipo_Desc'] = df_anticipacion_desc['Tipo Servicio'].apply(
                lambda x: normalizar_texto(tipos_guardados.get(x, {}).get('descripcion', '') or x) if pd.notna(x) else 'Sin definir'
            )

            # Obtener top 10 descripciones por volumen
            top_tipos = stats_anticipacion.nlargest(10, 'Num_Servicios')['Tipo Servicio'].tolist()

            # Filtrar por esas descripciones
            df_top_desc = df_anticipacion_desc[df_anticipacion_desc['Tipo_Desc'].isin(top_tipos)]

            if not df_top_desc.empty:
                fig = px.box(
                    df_top_desc,
                    x='Tipo_Desc',
                    y='Meses_Anticipacion',
                    color='Tipo_Desc',
                    title="Distribucion de anticipacion (top 10 por volumen)"
                )
                fig.update_layout(
                    height=500,
                    showlegend=False,
                    xaxis_title="Tipo de Servicio",
                    yaxis_title="Meses de anticipacion"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos suficientes para mostrar la distribucion")

        st.markdown("---")

        # ========== TABLA DETALLADA ==========
        st.subheader("Detalle por Tipo de Servicio")

        # Formatear tabla para mostrar
        tabla_display = stats_anticipacion.copy()
        tabla_display = tabla_display.rename(columns={
            'Tipo Servicio': 'Tipo de Servicio',
            'Meses_Media': 'Media (meses)',
            'Meses_Mediana': 'Mediana (meses)',
            'Dias_Media': 'Media (dias)',
            'Dias_Mediana': 'Mediana (dias)',
            'Dias_Min': 'Min (dias)',
            'Dias_Max': 'Max (dias)',
            'Num_Servicios': 'Servicios',
            'Importe_Total': 'Importe Total'
        })

        st.dataframe(
            tabla_display[['Tipo de Servicio', 'Servicios', 'Media (meses)', 'Mediana (meses)',
                          'Media (dias)', 'Min (dias)', 'Max (dias)', 'Importe Total']].style.format({
                'Media (meses)': '{:.1f}',
                'Mediana (meses)': '{:.1f}',
                'Importe Total': '{:,.0f} EUR'
            }),
            use_container_width=True,
            height=400
        )

        st.markdown("---")

        # ========== ANÁLISIS DETALLADO POR TIPO ==========
        st.subheader("Analisis Detallado por Tipo")

        # Selector de tipo
        opciones_tipo = ['Todos'] + stats_anticipacion['Tipo Servicio'].tolist()
        tipo_detalle = st.selectbox("Seleccionar tipo de servicio", opciones_tipo)

        if tipo_detalle != 'Todos':
            # Filtrar por tipo
            # Encontrar código(s) que corresponden a esta descripción
            codigos_tipo = [cod for cod, datos in tipos_guardados.items()
                           if normalizar_texto(datos.get('descripcion', '')) == tipo_detalle]
            if not codigos_tipo:
                codigos_tipo = [tipo_detalle]  # Si no hay descripción, usar el código

            df_tipo = df_anticipacion[df_anticipacion['Tipo Servicio'].isin(codigos_tipo)]

            if not df_tipo.empty:
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Media", f"{df_tipo['Meses_Anticipacion'].mean():.1f} meses")
                with col2:
                    st.metric("Mediana", f"{df_tipo['Meses_Anticipacion'].median():.1f} meses")
                with col3:
                    st.metric("Minimo", f"{df_tipo['Dias_Anticipacion'].min()} dias")
                with col4:
                    st.metric("Maximo", f"{df_tipo['Dias_Anticipacion'].max()} dias")

                # Histograma de distribución
                fig = px.histogram(
                    df_tipo,
                    x='Meses_Anticipacion',
                    nbins=20,
                    title=f"Distribucion de anticipacion para {tipo_detalle}",
                    color_discrete_sequence=['#000000']  # DAVID Brand
                )
                fig.update_layout(
                    xaxis_title="Meses de anticipacion",
                    yaxis_title="Numero de servicios"
                )
                st.plotly_chart(fig, use_container_width=True)

                # Tabla de servicios
                st.write("**Ultimos servicios:**")
                cols_mostrar = ['Cod. Presupuesto', 'Cliente', 'Fecha alta', 'Fecha Salida',
                               'Dias_Anticipacion', 'Meses_Anticipacion', 'Total importe']
                df_mostrar = df_tipo[cols_mostrar].sort_values('Fecha alta', ascending=False).head(20)
                df_mostrar['Fecha alta'] = df_mostrar['Fecha alta'].dt.strftime('%d/%m/%Y')
                df_mostrar['Fecha Salida'] = df_mostrar['Fecha Salida'].dt.strftime('%d/%m/%Y')
                st.dataframe(df_mostrar, width="stretch")

        else:
            # Mostrar histograma general - DAVID Brand
            fig = px.histogram(
                df_anticipacion,
                x='Meses_Anticipacion',
                nbins=30,
                title="Distribucion general de anticipacion",
                color_discrete_sequence=['#000000']  # DAVID Brand
            )
            fig.add_vline(x=media_global_meses, line_dash="dash", line_color="#F15025",
                         annotation_text=f"Media: {media_global_meses:.1f}m")
            fig.update_layout(
                xaxis_title="Meses de anticipacion",
                yaxis_title="Numero de servicios"
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # ========== TENDENCIA TEMPORAL ==========
        st.subheader("Evolucion Temporal de la Anticipacion")

        tendencia = obtener_tendencia_anticipacion_mensual(df, tipos_guardados)

        if not tendencia.empty:
            tendencia = tendencia.tail(36)  # Últimos 3 años
            tendencia['Mes_ES'] = tendencia['Mes'].apply(formato_mes_es)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=tendencia['Mes_ES'],
                y=tendencia['Meses_Media'],
                mode='lines+markers',
                name='Anticipacion media (meses)',
                line=dict(color='blue', width=2)
            ))
            fig.add_trace(go.Bar(
                x=tendencia['Mes_ES'],
                y=tendencia['Num_Servicios'],
                name='Num. servicios',
                yaxis='y2',
                marker_color='lightgray',
                opacity=0.5
            ))

            fig.update_layout(
                title="Evolucion de la anticipacion media por mes de solicitud",
                yaxis=dict(title="Meses de anticipacion", side='left'),
                yaxis2=dict(title="Numero de servicios", overlaying='y', side='right'),
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

        # Exportar datos
        csv = stats_anticipacion.to_csv(index=False).encode('utf-8')
        st.download_button(
            "Exportar analisis de anticipacion",
            csv,
            "anticipacion_por_tipo.csv",
            "text/csv"
        )


# ============================================
# PÁGINA: ANÁLISIS DE MERCADO Y COMPETENCIA
# ============================================
elif pagina == "Analisis Mercado":
    st.title("📊 Análisis de Mercado")
    st.caption("Seguimiento de competencia y posicionamiento de precios")

    # Placeholder de carga inicial
    loading_placeholder = st.empty()

    # Cargar datos principales con indicador de progreso
    with loading_placeholder.container():
        progress_bar = st.progress(0, text="Iniciando carga de datos...")
        progress_bar.progress(20, text="Cargando competidores...")
        comparativa_data = obtener_comparativa_flotas()
        progress_bar.progress(60, text="Cargando estadísticas...")
        competidores_data = obtener_competidores()
        progress_bar.progress(100, text="¡Listo!")

    # Limpiar placeholder
    loading_placeholder.empty()

    tab0, tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🏢 Competidores", "💰 Cotizaciones", "📈 Análisis", "⚠️ Alertas"])

    # TAB 0: DASHBOARD EJECUTIVO
    with tab0:
        st.subheader("Dashboard Ejecutivo")

        # Usar datos precargados
        comparativa = comparativa_data
        competidores = competidores_data
        stats_flota = comparativa.get('competidores', [])
        resumen = comparativa.get('resumen', {})

        # KPIs PRINCIPALES
        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

        total_competidores = resumen.get('total_competidores', 0) if resumen else 0
        total_vehiculos = resumen.get('total_vehiculos_mercado', 0) if resumen else 0
        total_capacidad = resumen.get('capacidad_total_mercado', 0) if resumen else 0
        edad_media = resumen.get('edad_media_mercado', 0) if resumen else 0

        with col_kpi1:
            st.metric(label="🏢 Competidores Activos", value=total_competidores)
        with col_kpi2:
            st.metric(label="🚌 Vehículos Mercado", value=f"{total_vehiculos:,}")
        with col_kpi3:
            st.metric(label="👥 Capacidad Total", value=f"{total_capacidad:,} plazas")
        with col_kpi4:
            st.metric(label="📅 Edad Media Flotas", value=f"{edad_media:.1f} años")

        st.divider()

        # GRÁFICOS PRINCIPALES
        if stats_flota:
            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                st.markdown("**Cuota de Mercado (por capacidad)**")
                # Filtrar solo competidores con vehículos
                stats_con_vehiculos = [s for s in stats_flota if s['capacidad_total'] and s['capacidad_total'] > 0]
                if stats_con_vehiculos:
                    df_cuota = pd.DataFrame(stats_con_vehiculos)
                    fig_pie = px.pie(
                        df_cuota,
                        values='capacidad_total',
                        names='competidor',
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    fig_pie.update_layout(
                        showlegend=False,
                        height=350,
                        margin=dict(t=20, b=20, l=20, r=20)
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("No hay datos de flotas registrados")

            with col_chart2:
                st.markdown("**Top 10 Competidores por Tamaño de Flota**")
                stats_con_vehiculos = [s for s in stats_flota if s['total_vehiculos'] and s['total_vehiculos'] > 0]
                if stats_con_vehiculos:
                    top_10 = sorted(stats_con_vehiculos, key=lambda x: x['total_vehiculos'], reverse=True)[:10]
                    df_top = pd.DataFrame(top_10)
                    fig_bar = px.bar(
                        df_top.sort_values('total_vehiculos'),
                        x='total_vehiculos',
                        y='competidor',
                        orientation='h',
                        color='total_vehiculos',
                        color_continuous_scale='Blues',
                        text='total_vehiculos'
                    )
                    fig_bar.update_traces(textposition='outside')
                    fig_bar.update_layout(
                        showlegend=False,
                        coloraxis_showscale=False,
                        height=350,
                        margin=dict(t=20, b=20, l=20, r=20),
                        xaxis_title="Vehículos",
                        yaxis_title=""
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.info("No hay datos de flotas registrados")

        # RESUMEN RÁPIDO
        st.divider()
        col_resumen1, col_resumen2, col_resumen3 = st.columns(3)

        if stats_flota:
            stats_con_datos = [s for s in stats_flota if s['total_vehiculos'] and s['total_vehiculos'] > 0]
            if stats_con_datos:
                # Líder del mercado (solo activos)
                lider = max(stats_con_datos, key=lambda x: x['total_vehiculos'])
                with col_resumen1:
                    st.info(f"**🏆 Líder del mercado:** {lider['competidor']} ({lider['total_vehiculos']} vehículos)")

                # Flota más joven (solo activos)
                stats_con_edad = [s for s in stats_con_datos if s['edad_media'] and s['edad_media'] > 0]
                if stats_con_edad:
                    mas_joven = min(stats_con_edad, key=lambda x: x['edad_media'])
                    with col_resumen2:
                        st.success(f"**🌟 Flota más joven:** {mas_joven['competidor']} ({mas_joven['edad_media']:.1f} años)")

                # Mayor capacidad (solo activos)
                max_capacidad = max(stats_con_datos, key=lambda x: x['capacidad_total'] or 0)
                with col_resumen3:
                    st.warning(f"**🚌 Mayor capacidad:** {max_capacidad['competidor']} ({max_capacidad['capacidad_total']:,} plazas)")
        else:
            st.info("Añade vehículos de competidores en la pestaña 'Flotas' para ver el dashboard")

    # TAB 1: GESTIÓN DE COMPETIDORES
    with tab1:
        st.subheader("Gestión de Competidores")

        competidores = competidores_data
        stats_flota = obtener_estadisticas_flota_competencia()

        # Selector de competidor
        nombres_comp = ["-- Seleccionar competidor --"] + [c['nombre'] for c in competidores]
        comp_seleccionado = st.selectbox("🏢 Seleccionar competidor para ver detalles", nombres_comp, key="selector_comp")

        if comp_seleccionado != "-- Seleccionar competidor --":
            # Obtener datos del competidor seleccionado
            comp_data = next((c for c in competidores if c['nombre'] == comp_seleccionado), None)
            flota_data = next((f for f in stats_flota if f['competidor'] == comp_seleccionado), None)

            if comp_data:
                st.divider()

                col_info, col_flota = st.columns(2)

                with col_info:
                    st.markdown(f"### 🏢 {comp_seleccionado}")
                    st.markdown(f"**Segmento:** {comp_data.get('segmento', '-')}")
                    st.markdown(f"**Zona de operación:** {comp_data.get('zona_operacion', '-') or '-'}")

                    if comp_data.get('fortalezas'):
                        st.markdown(f"**💪 Fortalezas:**")
                        st.info(comp_data['fortalezas'])
                    if comp_data.get('debilidades'):
                        st.markdown(f"**⚠️ Debilidades:**")
                        st.warning(comp_data['debilidades'])
                    if comp_data.get('notas'):
                        st.markdown(f"**📝 Notas:**")
                        st.caption(comp_data['notas'])

                with col_flota:
                    st.markdown("### 🚌 Flota")
                    if flota_data and flota_data.get('total_vehiculos', 0) > 0:
                        col_m1, col_m2 = st.columns(2)
                        col_m1.metric("Total Vehículos", flota_data['total_vehiculos'])
                        col_m2.metric("Capacidad Total", f"{flota_data['capacidad_total'] or 0:,} plazas")

                        col_m3, col_m4 = st.columns(2)
                        col_m3.metric("Edad Media", f"{flota_data['edad_media'] or 0:.1f} años")
                        col_m4.metric("Con PMR", flota_data['con_pmr'] or 0)

                        st.markdown("**Composición:**")
                        st.write(f"- 🚌 Grandes (50+): {flota_data['buses_grandes'] or 0}")
                        st.write(f"- 🚐 Medianos (30-49): {flota_data['buses_medianos'] or 0}")
                        st.write(f"- 🚙 Micros (<30): {flota_data['microbuses'] or 0}")

                        # Ver y editar vehículos de este competidor
                        if st.checkbox("Ver/Editar vehículos", key="ver_veh_comp"):
                            vehiculos_comp = obtener_vehiculos_competencia(competidor_id=comp_data['id'])
                            if vehiculos_comp:
                                # Selector de vehículo para editar
                                opciones_veh = ["-- Ver todos --"] + [
                                    f"{v['matricula'] or 'Sin mat.'} - {v['marca']} {v['modelo']} ({v['plazas']} plazas)"
                                    for v in vehiculos_comp
                                ]
                                veh_seleccionado = st.selectbox("Seleccionar vehículo", opciones_veh, key="sel_veh_edit")

                                if veh_seleccionado == "-- Ver todos --":
                                    df_v = pd.DataFrame(vehiculos_comp)
                                    st.dataframe(
                                        df_v[['matricula', 'marca', 'modelo', 'plazas', 'edad', 'distintivo_ambiental']],
                                        use_container_width=True, hide_index=True, height=200
                                    )
                                else:
                                    # Encontrar vehículo seleccionado
                                    idx = opciones_veh.index(veh_seleccionado) - 1
                                    veh_edit = vehiculos_comp[idx]

                                    st.markdown(f"**Editando:** {veh_edit['matricula'] or 'Sin matrícula'}")

                                    with st.form(f"form_edit_veh_{veh_edit['id']}"):
                                        col_e1, col_e2 = st.columns(2)
                                        with col_e1:
                                            edit_matricula = st.text_input("Matrícula", value=veh_edit['matricula'] or '')
                                            edit_marca = st.text_input("Marca", value=veh_edit['marca'] or '')
                                            edit_modelo = st.text_input("Modelo", value=veh_edit['modelo'] or '')
                                            edit_plazas = st.number_input("Plazas", min_value=1, max_value=100, value=veh_edit['plazas'] or 55)
                                        with col_e2:
                                            edit_ano = st.number_input("Año matriculación", min_value=1990, max_value=2026, value=veh_edit['ano_matriculacion'] or 2020)
                                            edit_distintivo = st.selectbox("Distintivo", ["", "0", "ECO", "C", "B", "Sin distintivo"],
                                                                          index=["", "0", "ECO", "C", "B", "Sin distintivo"].index(veh_edit['distintivo_ambiental'] or ''))
                                            edit_tipo = st.selectbox("Tipo", ["AUTOBUS", "MINIBUS", "MICROBUS", "TURISMO"],
                                                                    index=["AUTOBUS", "MINIBUS", "MICROBUS", "TURISMO"].index(veh_edit['tipo_vehiculo'] or 'AUTOBUS'))

                                        col_c1, col_c2 = st.columns(2)
                                        with col_c1:
                                            edit_pmr = st.checkbox("PMR", value=bool(veh_edit['pmr']))
                                            edit_wc = st.checkbox("WC", value=bool(veh_edit['wc']))
                                        with col_c2:
                                            edit_wifi = st.checkbox("WiFi", value=bool(veh_edit['wifi']))
                                            edit_escolar = st.checkbox("Escolar", value=bool(veh_edit['escolar']))

                                        edit_obs = st.text_area("Observaciones", value=veh_edit['observaciones'] or '', height=60)

                                        col_btn1, col_btn2 = st.columns(2)
                                        with col_btn1:
                                            if st.form_submit_button("💾 Guardar cambios", type="primary"):
                                                # Calcular edad
                                                edad_calc = datetime.now().year - edit_ano + (datetime.now().month / 12)
                                                actualizar_vehiculo_competencia(
                                                    veh_edit['id'],
                                                    matricula=edit_matricula,
                                                    marca=edit_marca,
                                                    modelo=edit_modelo,
                                                    plazas=edit_plazas,
                                                    ano_matriculacion=edit_ano,
                                                    edad=round(edad_calc, 1),
                                                    distintivo_ambiental=edit_distintivo,
                                                    tipo_vehiculo=edit_tipo,
                                                    pmr=edit_pmr,
                                                    wc=edit_wc,
                                                    wifi=edit_wifi,
                                                    escolar=edit_escolar,
                                                    observaciones=edit_obs
                                                )
                                                st.success("Vehículo actualizado")
                                                st.rerun()
                                        with col_btn2:
                                            if st.form_submit_button("🗑️ Eliminar", type="secondary"):
                                                eliminar_vehiculo_competencia(veh_edit['id'])
                                                st.success("Vehículo eliminado")
                                                st.rerun()
                    else:
                        st.info("No hay vehículos registrados para este competidor")

                # Acciones - Eliminar con doble confirmación
                st.divider()

                # Inicializar estado de confirmación
                if 'confirmar_eliminar_comp' not in st.session_state:
                    st.session_state.confirmar_eliminar_comp = None

                col_act1, col_act2 = st.columns(2)
                with col_act1:
                    if st.session_state.confirmar_eliminar_comp == comp_data['id']:
                        # Segunda confirmación
                        st.warning(f"⚠️ ¿Seguro que quieres eliminar **{comp_seleccionado}** y todos sus datos (vehículos, cotizaciones)?")
                        col_conf1, col_conf2 = st.columns(2)
                        with col_conf1:
                            if st.button("✅ Sí, eliminar todo", type="primary", key="btn_confirmar_elim"):
                                eliminar_competidor(comp_data['id'])
                                st.session_state.confirmar_eliminar_comp = None
                                st.success(f"Competidor '{comp_seleccionado}' eliminado con todos sus datos")
                                st.rerun()
                        with col_conf2:
                            if st.button("❌ Cancelar", key="btn_cancelar_elim"):
                                st.session_state.confirmar_eliminar_comp = None
                                st.rerun()
                    else:
                        # Primera confirmación
                        if st.button("🗑️ Eliminar competidor", type="secondary", key="btn_elim_comp"):
                            st.session_state.confirmar_eliminar_comp = comp_data['id']
                            st.rerun()

        st.divider()

        # Formulario para añadir nuevo competidor (colapsado)
        with st.expander("➕ Añadir nuevo competidor"):
            with st.form("form_competidor"):
                nombre_comp = st.text_input("Nombre de la empresa*")
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    segmento_comp = st.selectbox("Segmento", ["estandar", "premium", "low-cost", "especializado"])
                    zona_comp = st.text_input("Zona de operación", placeholder="Ej: País Vasco, Navarra")
                with col_f2:
                    fortalezas_comp = st.text_area("Fortalezas", height=80)
                    debilidades_comp = st.text_area("Debilidades", height=80)
                notas_comp = st.text_area("Notas adicionales", height=60)

                if st.form_submit_button("Guardar Competidor", use_container_width=True):
                    if nombre_comp:
                        guardar_competidor(
                            nombre=nombre_comp,
                            segmento=segmento_comp,
                            zona_operacion=zona_comp,
                            fortalezas=fortalezas_comp,
                            debilidades=debilidades_comp,
                            notas=notas_comp
                        )
                        st.success(f"Competidor '{nombre_comp}' guardado")
                        st.rerun()
                    else:
                        st.error("El nombre es obligatorio")

        # Tabla resumen de todos los competidores
        st.markdown("### 📋 Todos los Competidores")
        if competidores:
            # Combinar datos de competidores con flotas
            df_all = pd.DataFrame(competidores)
            df_flotas = pd.DataFrame(stats_flota) if stats_flota else pd.DataFrame()

            if not df_flotas.empty:
                df_all = df_all.merge(
                    df_flotas[['competidor', 'total_vehiculos', 'capacidad_total', 'edad_media']],
                    left_on='nombre', right_on='competidor', how='left'
                )
                df_show = df_all[['nombre', 'segmento', 'zona_operacion', 'total_vehiculos', 'capacidad_total', 'edad_media']].copy()
                df_show.columns = ['Nombre', 'Segmento', 'Zona', 'Vehículos', 'Capacidad', 'Edad Media']
                df_show = df_show.fillna(0)
                df_show = df_show.sort_values('Vehículos', ascending=False)
            else:
                df_show = df_all[['nombre', 'segmento', 'zona_operacion']].copy()
                df_show.columns = ['Nombre', 'Segmento', 'Zona']

            st.dataframe(df_show, use_container_width=True, hide_index=True)
        else:
            st.info("No hay competidores registrados.")

    # TAB 2: COTIZACIONES DE COMPETENCIA
    with tab2:
        st.subheader("Inteligencia de Precios")

        competidores = competidores_data

        if not competidores:
            st.warning("Primero debes registrar al menos un competidor")
        else:
            # Obtener todas las cotizaciones para KPIs
            todas_cotizaciones = obtener_cotizaciones_competencia()

            # KPIs de cotizaciones
            col_k1, col_k2, col_k3, col_k4 = st.columns(4)
            total_cot = len(todas_cotizaciones)
            competidores_con_cot = len(set(c['competidor_nombre'] for c in todas_cotizaciones)) if todas_cotizaciones else 0
            precio_medio = sum(c['precio'] for c in todas_cotizaciones) / total_cot if total_cot > 0 else 0
            servicios_cubiertos = len(set(c['tipo_servicio'] for c in todas_cotizaciones)) if todas_cotizaciones else 0

            col_k1.metric("📊 Total Cotizaciones", total_cot)
            col_k2.metric("🏢 Competidores", competidores_con_cot)
            col_k3.metric("💰 Precio Medio", f"{precio_medio:,.0f}€")
            col_k4.metric("📋 Tipos Servicio", servicios_cubiertos)

            st.divider()

            # Formulario en expander + Lista principal
            col_form, col_list = st.columns([1, 2])

            with col_form:
                with st.expander("➕ Nueva Cotización", expanded=True):
                    with st.form("form_cotizacion", clear_on_submit=True):
                        comp_sel = st.selectbox("🏢 Competidor*", [c['nombre'] for c in competidores])

                        col_s1, col_s2 = st.columns(2)
                        with col_s1:
                            tipo_serv = st.selectbox("📋 Servicio*", [
                                "TRANSFER", "EXCURSION", "ESCOLAR", "DEPORTIVO",
                                "CONGRESO", "CIRCUITO", "DISCRECIONAL", "OTRO"
                            ])
                        with col_s2:
                            tipo_veh = st.selectbox("🚌 Vehículo", list(FACTOR_VEHICULO_NORM.keys()))

                        col_p1, col_p2 = st.columns(2)
                        with col_p1:
                            precio_cot = st.number_input("💰 Precio (€)*", min_value=0.0, step=50.0, format="%.0f")
                        with col_p2:
                            fecha_cot = st.date_input("📅 Fecha", value=datetime.now())

                        col_r1, col_r2 = st.columns(2)
                        with col_r1:
                            origen_cot = st.text_input("📍 Origen")
                            km_cot = st.number_input("🛣️ Km", min_value=0, step=10)
                        with col_r2:
                            destino_cot = st.text_input("🎯 Destino")
                            horas_cot = st.number_input("⏱️ Horas", min_value=0.0, step=0.5)

                        fuente_cot = st.selectbox("📡 Fuente", ["Cliente", "Web competidor", "Llamada", "Conocido", "Licitación", "Otra"])
                        notas_cot = st.text_area("📝 Notas", height=60, placeholder="Detalles adicionales...")

                        if st.form_submit_button("💾 Guardar Cotización", use_container_width=True, type="primary"):
                            if comp_sel and precio_cot > 0:
                                comp_id = next((c['id'] for c in competidores if c['nombre'] == comp_sel), None)
                                if comp_id:
                                    guardar_cotizacion_competencia(
                                        competidor_id=comp_id,
                                        tipo_servicio=tipo_serv,
                                        precio=precio_cot,
                                        tipo_vehiculo=tipo_veh,
                                        km_estimados=km_cot if km_cot > 0 else None,
                                        duracion_horas=horas_cot if horas_cot > 0 else None,
                                        origen=origen_cot,
                                        destino=destino_cot,
                                        fecha_captura=fecha_cot.strftime('%Y-%m-%d'),
                                        fuente=fuente_cot,
                                        notas=notas_cot
                                    )
                                    st.success("✅ Cotización registrada")
                                    st.rerun()
                            else:
                                st.error("Competidor y precio son obligatorios")

            with col_list:
                st.markdown("### 📋 Cotizaciones Registradas")

                # Filtros en línea
                col_f1, col_f2, col_f3 = st.columns(3)
                with col_f1:
                    filtro_comp = st.selectbox("Competidor", ["Todos"] + [c['nombre'] for c in competidores], key="filtro_comp_cot")
                with col_f2:
                    filtro_tipo = st.selectbox("Tipo", ["Todos", "TRANSFER", "EXCURSION", "ESCOLAR", "DEPORTIVO", "CONGRESO", "CIRCUITO", "DISCRECIONAL"], key="filtro_tipo_cot")
                with col_f3:
                    orden = st.selectbox("Ordenar por", ["Fecha ↓", "Precio ↓", "Precio ↑", "Competidor"], key="orden_cot")

                # Obtener cotizaciones filtradas
                comp_id_filtro = None
                if filtro_comp != "Todos":
                    comp_id_filtro = next((c['id'] for c in competidores if c['nombre'] == filtro_comp), None)

                cotizaciones = obtener_cotizaciones_competencia(
                    competidor_id=comp_id_filtro,
                    tipo_servicio=filtro_tipo if filtro_tipo != "Todos" else None
                )

                if cotizaciones:
                    df_cot = pd.DataFrame(cotizaciones)

                    # Ordenar según selección
                    if orden == "Precio ↓":
                        df_cot = df_cot.sort_values('precio', ascending=False)
                    elif orden == "Precio ↑":
                        df_cot = df_cot.sort_values('precio', ascending=True)
                    elif orden == "Competidor":
                        df_cot = df_cot.sort_values('competidor_nombre')

                    # Mostrar resumen rápido
                    st.caption(f"Mostrando {len(df_cot)} cotizaciones | Precio medio: {df_cot['precio'].mean():,.0f}€ | Rango: {df_cot['precio'].min():,.0f}€ - {df_cot['precio'].max():,.0f}€")

                    # Tabla mejorada
                    df_cot_show = df_cot[['competidor_nombre', 'tipo_servicio', 'tipo_vehiculo', 'precio', 'origen', 'destino', 'fecha_captura']].copy()
                    df_cot_show['Ruta'] = df_cot_show.apply(lambda r: f"{r['origen'] or '?'} → {r['destino'] or '?'}" if r['origen'] or r['destino'] else '-', axis=1)
                    df_cot_show = df_cot_show[['competidor_nombre', 'tipo_servicio', 'tipo_vehiculo', 'precio', 'Ruta', 'fecha_captura']]
                    df_cot_show.columns = ['Competidor', 'Servicio', 'Vehículo', 'Precio', 'Ruta', 'Fecha']

                    st.dataframe(
                        df_cot_show,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            'Precio': st.column_config.NumberColumn(format="%.0f €"),
                            'Fecha': st.column_config.DateColumn(format="DD/MM/YYYY")
                        }
                    )

                    # Gráfico rápido de precios por competidor
                    if len(df_cot) >= 3:
                        with st.expander("📊 Ver gráfico de precios"):
                            fig_precios = px.box(
                                df_cot,
                                x='competidor_nombre',
                                y='precio',
                                color='tipo_servicio',
                                labels={'competidor_nombre': 'Competidor', 'precio': 'Precio (€)', 'tipo_servicio': 'Servicio'}
                            )
                            fig_precios.update_layout(height=300, showlegend=True)
                            st.plotly_chart(fig_precios, use_container_width=True)
                else:
                    st.info("No hay cotizaciones registradas. Añade la primera usando el formulario.")

    # TAB 3: ANÁLISIS COMPARATIVO
    with tab3:
        st.subheader("Análisis Comparativo de Precios")

        estadisticas = obtener_estadisticas_mercado()

        if estadisticas:
            # Resumen por tipo de servicio
            df_stats = pd.DataFrame(estadisticas)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Precios medios por tipo de servicio**")
                fig = px.bar(
                    df_stats,
                    x='tipo_servicio',
                    y='precio_medio',
                    color='tipo_vehiculo',
                    barmode='group',
                    labels={'tipo_servicio': 'Servicio', 'precio_medio': 'Precio Medio (€)', 'tipo_vehiculo': 'Vehículo'}
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown("**Rango de precios del mercado**")
                fig2 = go.Figure()
                for _, row in df_stats.iterrows():
                    fig2.add_trace(go.Bar(
                        name=f"{row['tipo_servicio']} ({row['tipo_vehiculo']})",
                        x=[f"{row['tipo_servicio']}\n{row['tipo_vehiculo']}"],
                        y=[row['precio_medio']],
                        error_y=dict(
                            type='data',
                            symmetric=False,
                            array=[row['precio_max'] - row['precio_medio']],
                            arrayminus=[row['precio_medio'] - row['precio_min']]
                        )
                    ))
                fig2.update_layout(showlegend=False, yaxis_title="Precio (€)")
                st.plotly_chart(fig2, use_container_width=True)

            # Ranking de competidores
            st.markdown("---")
            st.markdown("**Ranking de Competidores por Precio Medio**")

            ranking = obtener_ranking_competidores()
            if ranking:
                df_rank = pd.DataFrame(ranking)
                df_rank['precio_medio'] = df_rank['precio_medio'].round(0)

                fig3 = px.bar(
                    df_rank,
                    y='nombre',
                    x='precio_medio',
                    orientation='h',
                    color='segmento',
                    labels={'nombre': 'Competidor', 'precio_medio': 'Precio Medio (€)', 'segmento': 'Segmento'}
                )
                fig3.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig3, use_container_width=True)

            # ANÁLISIS AVANZADO DE PRECIOS
            st.markdown("---")
            st.markdown("### 📊 Análisis Avanzado de Precios")

            # Obtener todas las cotizaciones para análisis detallado
            cotizaciones_todas = obtener_cotizaciones_competencia()

            if cotizaciones_todas:
                df_cots = pd.DataFrame(cotizaciones_todas)

                col_box, col_heat = st.columns(2)

                with col_box:
                    st.markdown("**Distribución de Precios por Servicio (Box Plot)**")
                    fig_box = px.box(
                        df_cots,
                        x='tipo_servicio',
                        y='precio',
                        color='tipo_servicio',
                        labels={'tipo_servicio': 'Tipo de Servicio', 'precio': 'Precio (€)'},
                        points='all'
                    )
                    fig_box.update_layout(showlegend=False, height=400)
                    st.plotly_chart(fig_box, use_container_width=True)

                with col_heat:
                    st.markdown("**Matriz Competidor × Servicio (Precio Medio)**")
                    # Crear matriz pivote
                    pivot_data = df_cots.pivot_table(
                        values='precio',
                        index='competidor_nombre',
                        columns='tipo_servicio',
                        aggfunc='mean'
                    ).round(0)

                    if not pivot_data.empty:
                        fig_heat = px.imshow(
                            pivot_data,
                            labels=dict(x="Tipo de Servicio", y="Competidor", color="Precio (€)"),
                            color_continuous_scale='RdYlGn_r',
                            aspect='auto',
                            text_auto='.0f'
                        )
                        fig_heat.update_layout(height=400)
                        st.plotly_chart(fig_heat, use_container_width=True)
                    else:
                        st.info("No hay suficientes datos para el heatmap")

                # Tabla resumen con ranking
                st.markdown("**Ranking Detallado por Tipo de Servicio**")
                df_ranking_detalle = df_cots.groupby(['tipo_servicio', 'competidor_nombre']).agg({
                    'precio': ['mean', 'min', 'max', 'count']
                }).round(0)
                df_ranking_detalle.columns = ['Precio Medio', 'Mín', 'Máx', 'Cotizaciones']
                df_ranking_detalle = df_ranking_detalle.reset_index()
                df_ranking_detalle.columns = ['Servicio', 'Competidor', 'Precio Medio', 'Mín', 'Máx', 'Cotizaciones']
                df_ranking_detalle = df_ranking_detalle.sort_values(['Servicio', 'Precio Medio'])

                # Añadir ranking por servicio
                df_ranking_detalle['Ranking'] = df_ranking_detalle.groupby('Servicio').cumcount() + 1

                st.dataframe(df_ranking_detalle[['Servicio', 'Ranking', 'Competidor', 'Precio Medio', 'Mín', 'Máx', 'Cotizaciones']],
                           use_container_width=True, hide_index=True)

            # Comparador con tarifa David
            st.markdown("---")
            st.subheader("🔍 Comparador con Tarifas David")

            col_c1, col_c2, col_c3, col_c4 = st.columns(4)
            with col_c1:
                tipo_comp = st.selectbox("Tipo de servicio", ["TRANSFER", "EXCURSION", "ESCOLAR", "DEPORTIVO", "CONGRESO", "CIRCUITO", "DISCRECIONAL"])
            with col_c2:
                veh_comp = st.selectbox("Tipo de vehículo", list(FACTOR_VEHICULO_NORM.keys()), key="veh_comparador")
            with col_c3:
                km_comp = st.number_input("Kilómetros", min_value=0, value=100, step=10)
            with col_c4:
                horas_comp = st.number_input("Horas", min_value=0.0, value=8.0, step=0.5)

            if st.button("Comparar", type="primary"):
                resultado = comparar_con_tarifa_david(tipo_comp, veh_comp, km_comp, horas_comp)

                col_r1, col_r2, col_r3 = st.columns(3)
                with col_r1:
                    st.metric("Precio David", f"{resultado['precio_david']:,.0f}€" if resultado['precio_david'] else "N/A")
                with col_r2:
                    if resultado['resumen']:
                        st.metric("Media Competencia", f"{resultado['resumen']['precio_medio_competencia']:,.0f}€")
                    else:
                        st.metric("Media Competencia", "Sin datos")
                with col_r3:
                    if resultado['resumen']:
                        posicion = resultado['resumen']['posicion_david']
                        color = "normal" if posicion == "COMPETITIVO" else "inverse"
                        st.metric("Posición", posicion)
                    else:
                        st.metric("Posición", "Sin datos")

                if resultado['comparacion']:
                    st.markdown("**Detalle por competidor:**")
                    df_detalle = pd.DataFrame(resultado['comparacion'])
                    df_detalle['diferencia_pct'] = df_detalle['diferencia_pct'].apply(lambda x: f"{x:+.1f}%")
                    df_detalle['precio'] = df_detalle['precio'].apply(lambda x: f"{x:,.0f}€")
                    st.dataframe(df_detalle, use_container_width=True, hide_index=True)
        else:
            st.info("No hay datos de mercado. Registra cotizaciones de la competencia para ver el análisis.")

    # TAB 4: ALERTAS
    with tab4:
        st.subheader("Panel de Alertas")

        umbral = st.slider("Umbral de diferencia (%)", min_value=5, max_value=50, value=15)

        alertas = detectar_alertas_competencia(umbral_diferencia=umbral)

        # DASHBOARD DE CONTADORES
        col_count1, col_count2, col_count3, col_count4 = st.columns(4)

        alertas_caras = [a for a in alertas if a['alerta'] == 'MÁS CARO'] if alertas else []
        alertas_baratas = [a for a in alertas if a['alerta'] == 'MÁS BARATO'] if alertas else []

        with col_count1:
            st.metric("⚠️ Alertas Totales", len(alertas) if alertas else 0)
        with col_count2:
            st.metric("🔴 Más Caro", len(alertas_caras), help="Servicios donde David está por encima del mercado")
        with col_count3:
            st.metric("🟢 Más Barato", len(alertas_baratas), help="Servicios donde David está por debajo del mercado")
        with col_count4:
            # Calcular ahorro/pérdida potencial
            if alertas_caras:
                perdida_pct = sum(a['diferencia_pct'] for a in alertas_caras) / len(alertas_caras)
                st.metric("📉 Diferencia Media", f"{perdida_pct:+.1f}%", help="Diferencia media en servicios donde estamos más caros")
            else:
                st.metric("📉 Diferencia Media", "0%")

        st.divider()

        if alertas:
            col_alertas, col_detalle = st.columns([1, 1])

            with col_alertas:
                st.markdown("### ⚠️ Alertas Activas")

                # Primero las alertas de "más caro" (críticas)
                if alertas_caras:
                    st.markdown("**🔴 Servicios donde estamos más caros:**")
                    for alerta in alertas_caras:
                        st.error(f"**{alerta['tipo_servicio']}** ({alerta['tipo_vehiculo']}): +{abs(alerta['diferencia_pct'])}% vs mercado")

                # Luego las de "más barato" (oportunidades)
                if alertas_baratas:
                    st.markdown("**🟢 Servicios donde estamos más baratos:**")
                    for alerta in alertas_baratas:
                        st.success(f"**{alerta['tipo_servicio']}** ({alerta['tipo_vehiculo']}): -{abs(alerta['diferencia_pct'])}% vs mercado")

            with col_detalle:
                st.markdown("### 📊 Análisis de Impacto")

                df_alertas = pd.DataFrame(alertas)

                # Gráfico de barras de diferencias
                fig_diff = px.bar(
                    df_alertas,
                    x='tipo_servicio',
                    y='diferencia_pct',
                    color='alerta',
                    color_discrete_map={'MÁS CARO': '#e74c3c', 'MÁS BARATO': '#27ae60'},
                    labels={'tipo_servicio': 'Servicio', 'diferencia_pct': 'Diferencia (%)'},
                    text='diferencia_pct'
                )
                fig_diff.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                fig_diff.update_layout(height=300, showlegend=True)
                st.plotly_chart(fig_diff, use_container_width=True)

            # Tabla detallada
            st.divider()
            st.markdown("### 📋 Detalle de Alertas")

            df_alertas_show = df_alertas.copy()
            df_alertas_show['Ajuste Sugerido'] = df_alertas_show.apply(
                lambda r: f"Bajar a {r['precio_mercado']:,.0f}€" if r['alerta'] == 'MÁS CARO' else "Mantener/Subir",
                axis=1
            )
            df_alertas_show['precio_david'] = df_alertas_show['precio_david'].apply(lambda x: f"{x:,.0f}€")
            df_alertas_show['precio_mercado'] = df_alertas_show['precio_mercado'].apply(lambda x: f"{x:,.0f}€")
            df_alertas_show['diferencia_pct'] = df_alertas_show['diferencia_pct'].apply(lambda x: f"{x:+.1f}%")

            st.dataframe(
                df_alertas_show[['tipo_servicio', 'tipo_vehiculo', 'precio_david', 'precio_mercado', 'diferencia_pct', 'alerta', 'Ajuste Sugerido']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    'tipo_servicio': 'Servicio',
                    'tipo_vehiculo': 'Vehículo',
                    'precio_david': 'Precio David',
                    'precio_mercado': 'Precio Mercado',
                    'diferencia_pct': 'Diferencia',
                    'alerta': 'Estado'
                }
            )

            # Resumen ejecutivo
            st.divider()
            st.markdown("### 💡 Recomendaciones")
            if alertas_caras:
                servicios_caros = ", ".join([f"{a['tipo_servicio']}" for a in alertas_caras])
                st.warning(f"**Revisar precios en:** {servicios_caros}. Estos servicios están significativamente por encima del mercado.")
            if alertas_baratas:
                st.info("Los servicios donde estamos más baratos representan una ventaja competitiva. Considerar si hay margen para subir precios sin perder competitividad.")
        else:
            st.success("✅ **Situación óptima:** No hay alertas de precios. Los precios de David están dentro del rango del mercado.")


# ============================================
# PÁGINA: FLOTAS COMPETENCIA
# ============================================
elif pagina == "Flotas Competencia":
    st.title("🚌 Flotas de Competencia")

    from db_competencia import (
        obtener_competidores, obtener_vehiculos_competencia,
        guardar_vehiculo_competencia, eliminar_vehiculo_competencia,
        obtener_comparativa_flotas
    )

    competidores = obtener_competidores()

    if not competidores:
        st.warning("Primero debes añadir competidores en 'Análisis Mercado → Competidores'")
    else:
        # Tabs principales
        tab_resumen, tab_editar, tab_lista = st.tabs(["📊 Resumen", "✏️ Editar Flotas", "📋 Lista Vehículos"])

        with tab_resumen:
            st.subheader("Comparativa de Flotas")

            comparativa = obtener_comparativa_flotas()

            if comparativa['resumen']:
                res = comparativa['resumen']
                col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                col_m1.metric("Total Competidores", res['total_competidores'])
                col_m2.metric("Vehículos Mercado", res['total_vehiculos_mercado'])
                col_m3.metric("Capacidad Total", f"{res['capacidad_total_mercado']:,} plazas")
                col_m4.metric("Líder Flota", res['lider_flota'] or "-")

            if comparativa['competidores']:
                df_flotas = pd.DataFrame(comparativa['competidores'])
                df_flotas_show = df_flotas[['competidor', 'total_vehiculos', 'buses_grandes', 'buses_medianos',
                                             'microbuses', 'edad_media', 'capacidad_total', 'con_pmr']].copy()
                df_flotas_show.columns = ['Competidor', 'Total', 'Grandes (50+)', 'Medianos', 'Micro',
                                          'Edad Media', 'Capacidad', 'PMR']
                st.dataframe(df_flotas_show, use_container_width=True, hide_index=True)

                # Gráficos
                col_graf1, col_graf2 = st.columns(2)

                with col_graf1:
                    fig_flotas = px.bar(
                        df_flotas,
                        x='competidor',
                        y='total_vehiculos',
                        color='edad_media',
                        title='Tamaño de Flota por Competidor',
                        labels={'total_vehiculos': 'Vehículos', 'competidor': 'Competidor', 'edad_media': 'Edad Media'},
                        color_continuous_scale='RdYlGn_r'
                    )
                    st.plotly_chart(fig_flotas, use_container_width=True)

                df_anal_filtrado = df_flotas[df_flotas['total_vehiculos'] > 0].copy()
                if len(df_anal_filtrado) > 0:
                    with col_graf2:
                        fig_scatter = px.scatter(
                            df_anal_filtrado,
                            x='edad_media',
                            y='capacidad_total',
                            size='total_vehiculos',
                            color='competidor',
                            hover_data=['buses_grandes', 'buses_medianos', 'microbuses'],
                            title='Edad vs Capacidad',
                            labels={'edad_media': 'Edad Media (años)', 'capacidad_total': 'Capacidad (plazas)'},
                            size_max=50
                        )
                        fig_scatter.update_layout(height=400, showlegend=False)
                        st.plotly_chart(fig_scatter, use_container_width=True)

                    # Composición de flotas
                    st.markdown("**Composición de Flotas**")
                    df_stacked = df_anal_filtrado[['competidor', 'buses_grandes', 'buses_medianos', 'microbuses']].copy()
                    df_stacked = df_stacked.melt(id_vars='competidor', var_name='Tipo', value_name='Cantidad')
                    df_stacked['Tipo'] = df_stacked['Tipo'].replace({
                        'buses_grandes': 'Grandes (50+)',
                        'buses_medianos': 'Medianos (30-49)',
                        'microbuses': 'Micros (<30)'
                    })
                    fig_stacked = px.bar(
                        df_stacked,
                        x='competidor',
                        y='Cantidad',
                        color='Tipo',
                        barmode='stack',
                        color_discrete_map={'Grandes (50+)': '#1f77b4', 'Medianos (30-49)': '#ff7f0e', 'Micros (<30)': '#2ca02c'}
                    )
                    fig_stacked.update_layout(height=400, xaxis_tickangle=-45)
                    st.plotly_chart(fig_stacked, use_container_width=True)

                    # Indicadores de calidad
                    st.markdown("**Indicadores de Calidad de Flota**")
                    df_calidad = df_anal_filtrado.copy()
                    df_calidad['% PMR'] = (df_calidad['con_pmr'] / df_calidad['total_vehiculos'] * 100).round(1)
                    df_calidad['% Escolar'] = (df_calidad['escolares'] / df_calidad['total_vehiculos'] * 100).round(1)
                    df_calidad['% WiFi'] = (df_calidad['con_wifi'] / df_calidad['total_vehiculos'] * 100).round(1)
                    df_calidad['Modernidad'] = df_calidad['edad_media'].apply(lambda x: max(0, min(100, 100 - (x * 5))) if x else 0).round(0)

                    df_calidad_show = df_calidad[['competidor', 'total_vehiculos', 'edad_media', '% PMR', '% Escolar', '% WiFi', 'Modernidad']].copy()
                    df_calidad_show.columns = ['Competidor', 'Vehículos', 'Edad Media', '% PMR', '% Escolar', '% WiFi', 'Índice Modernidad']
                    st.dataframe(df_calidad_show, use_container_width=True, hide_index=True)

        with tab_editar:
            st.subheader("Editar Flotas")

            col_sel, col_add = st.columns([2, 1])

            with col_sel:
                comp_editar = st.selectbox("Seleccionar competidor", [c['nombre'] for c in competidores], key="flota_comp_editar")
                comp_id_editar = next((c['id'] for c in competidores if c['nombre'] == comp_editar), None)

            with col_add:
                st.markdown("**Añadir Vehículo**")
                with st.popover("➕ Nuevo Vehículo"):
                    with st.form("form_add_veh_flota"):
                        new_mat = st.text_input("Matrícula")
                        new_plazas = st.number_input("Plazas", min_value=1, max_value=100, value=55)
                        new_ano = st.number_input("Año", min_value=1990, max_value=2026, value=2020)
                        new_marca = st.text_input("Marca")
                        new_modelo = st.text_input("Modelo")
                        if st.form_submit_button("Añadir", type="primary"):
                            guardar_vehiculo_competencia(
                                competidor_id=comp_id_editar,
                                matricula=new_mat,
                                tipo_vehiculo='AUTOBUS',
                                marca=new_marca,
                                modelo=new_modelo,
                                plazas=new_plazas,
                                ano_matriculacion=new_ano
                            )
                            st.success("Vehículo añadido")
                            st.rerun()

            if comp_id_editar:
                vehiculos_comp = obtener_vehiculos_competencia(competidor_id=comp_id_editar, solo_activos=False)

                activos = [v for v in vehiculos_comp if v.get('activo', True)]
                inactivos = [v for v in vehiculos_comp if not v.get('activo', True)]
                st.info(f"**{comp_editar}**: {len(activos)} activos, {len(inactivos)} inactivos")

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("🔄 Marcar todos inactivos", key="btn_inactivar"):
                        from supabase_client import get_admin_client
                        client = get_admin_client()
                        client.table('vehiculos_competencia').update({'activo': False}).eq('competidor_id', comp_id_editar).execute()
                        st.rerun()

                # Subtabs para edición
                sub_lista, sub_form, sub_bulk = st.tabs(["📋 Tabla Editable", "✏️ Formulario", "📝 Masiva"])

                with sub_lista:
                    if vehiculos_comp:
                        df_edit = pd.DataFrame(vehiculos_comp)
                        df_edit = df_edit[['id', 'matricula', 'marca', 'modelo', 'plazas', 'ano_matriculacion', 'edad', 'distintivo_ambiental', 'activo']].copy()
                        df_edit.columns = ['ID', 'Matrícula', 'Marca', 'Modelo', 'Plazas', 'Año', 'Edad', 'Distintivo', 'Activo']

                        edited_df = st.data_editor(
                            df_edit,
                            hide_index=True,
                            use_container_width=True,
                            column_config={
                                'ID': st.column_config.NumberColumn(disabled=True, width="small"),
                                'Plazas': st.column_config.NumberColumn(min_value=1, max_value=100, width="small"),
                                'Año': st.column_config.NumberColumn(min_value=1990, max_value=2026, width="small"),
                                'Edad': st.column_config.NumberColumn(disabled=True, width="small"),
                                'Distintivo': st.column_config.SelectboxColumn(options=["", "0", "ECO", "C", "B"], width="small"),
                                'Activo': st.column_config.CheckboxColumn(width="small")
                            },
                            key=f"editor_flota_{comp_id_editar}"
                        )

                        if st.button("💾 Guardar Cambios", type="primary", key="btn_guardar_flota"):
                            from supabase_client import get_admin_client
                            client = get_admin_client()
                            for _, row in edited_df.iterrows():
                                ano = row['Año'] or 2020
                                edad = round(datetime.now().year - ano + (datetime.now().month / 12), 1)
                                client.table('vehiculos_competencia').update({
                                    'matricula': row['Matrícula'],
                                    'marca': row['Marca'],
                                    'modelo': row['Modelo'],
                                    'plazas': int(row['Plazas']) if row['Plazas'] else None,
                                    'ano_matriculacion': int(ano),
                                    'edad': edad,
                                    'distintivo_ambiental': row['Distintivo'],
                                    'activo': bool(row['Activo'])
                                }).eq('id', row['ID']).execute()
                            st.success("✅ Cambios guardados")
                            st.rerun()
                    else:
                        st.info("No hay vehículos")

                with sub_form:
                    if vehiculos_comp:
                        opciones_veh = [f"{v['matricula'] or 'Sin mat.'} - {v.get('marca', '')} {v.get('modelo', '')}" for v in vehiculos_comp]
                        veh_sel_idx = st.selectbox("Vehículo", range(len(opciones_veh)), format_func=lambda x: opciones_veh[x], key="sel_veh_form")
                        veh_edit = vehiculos_comp[veh_sel_idx]

                        with st.form(f"form_edit_veh_{veh_edit['id']}"):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                edit_mat = st.text_input("Matrícula", value=veh_edit.get('matricula') or '')
                                edit_marca = st.text_input("Marca", value=veh_edit.get('marca') or '')
                                edit_modelo = st.text_input("Modelo", value=veh_edit.get('modelo') or '')
                            with col2:
                                edit_plazas = st.number_input("Plazas", min_value=1, max_value=100, value=veh_edit.get('plazas') or 55)
                                edit_ano = st.number_input("Año", min_value=1990, max_value=2026, value=veh_edit.get('ano_matriculacion') or 2020)
                                distintivo_opciones = ["", "0", "ECO", "C", "B", "Sin distintivo"]
                                distintivo_actual = veh_edit.get('distintivo_ambiental') or ''
                                distintivo_idx = distintivo_opciones.index(distintivo_actual) if distintivo_actual in distintivo_opciones else 0
                                edit_distintivo = st.selectbox("Distintivo", distintivo_opciones, index=distintivo_idx)
                            with col3:
                                edit_activo = st.checkbox("Activo", value=veh_edit.get('activo', True))
                                edit_pmr = st.checkbox("PMR", value=bool(veh_edit.get('pmr')))
                                edit_wc = st.checkbox("WC", value=bool(veh_edit.get('wc')))
                                edit_wifi = st.checkbox("WiFi", value=bool(veh_edit.get('wifi')))

                            col_b1, col_b2 = st.columns(2)
                            with col_b1:
                                if st.form_submit_button("💾 Guardar", type="primary", use_container_width=True):
                                    from supabase_client import get_admin_client
                                    client = get_admin_client()
                                    edad = round(datetime.now().year - edit_ano + (datetime.now().month / 12), 1)
                                    client.table('vehiculos_competencia').update({
                                        'matricula': edit_mat, 'marca': edit_marca, 'modelo': edit_modelo,
                                        'plazas': edit_plazas, 'ano_matriculacion': edit_ano, 'edad': edad,
                                        'distintivo_ambiental': edit_distintivo, 'activo': edit_activo,
                                        'pmr': edit_pmr, 'wc': edit_wc, 'wifi': edit_wifi
                                    }).eq('id', veh_edit['id']).execute()
                                    st.success("✅ Guardado")
                                    st.rerun()
                            with col_b2:
                                if st.form_submit_button("🗑️ Eliminar", type="secondary", use_container_width=True):
                                    eliminar_vehiculo_competencia(veh_edit['id'])
                                    st.rerun()

                with sub_bulk:
                    st.markdown("**Pegar lista de matrículas activas**")
                    st.caption("Los que estén en la lista → activos. Los que NO → inactivos.")

                    matriculas_texto = st.text_area("Matrículas", height=200, placeholder="2903KGP\n3095HCG\n...", key="bulk_mat_flota")

                    if st.button("✅ Actualizar Flota", type="primary", key="btn_bulk_flota"):
                        if matriculas_texto.strip():
                            from supabase_client import get_admin_client
                            client = get_admin_client()

                            lineas = matriculas_texto.strip().split('\n')
                            matriculas_activas = [l.strip().split()[0].upper() for l in lineas if l.strip()]

                            client.table('vehiculos_competencia').update({'activo': False}).eq('competidor_id', comp_id_editar).execute()

                            existentes = client.table('vehiculos_competencia').select('id, matricula').eq('competidor_id', comp_id_editar).execute().data or []
                            mat_existentes = {v['matricula'].upper(): v['id'] for v in existentes if v['matricula']}

                            actualizados, creados = 0, 0
                            for mat in matriculas_activas:
                                if mat in mat_existentes:
                                    client.table('vehiculos_competencia').update({'activo': True}).eq('id', mat_existentes[mat]).execute()
                                    actualizados += 1
                                else:
                                    client.table('vehiculos_competencia').insert({
                                        'competidor_id': comp_id_editar, 'matricula': mat,
                                        'tipo_vehiculo': 'AUTOBUS', 'activo': True
                                    }).execute()
                                    creados += 1

                            st.success(f"✅ {actualizados} actualizados, {creados} nuevos")
                            st.rerun()

        with tab_lista:
            st.subheader("Listado de Vehículos")

            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            with col_f1:
                filtro_comp = st.selectbox("Competidor", ["Todos"] + [c['nombre'] for c in competidores], key="filtro_comp_lista")
            with col_f2:
                filtro_tipo = st.selectbox("Tipo", ["Todos", "AUTOBUS", "MINIBUS", "MICROBUS"], key="filtro_tipo_lista")
            with col_f3:
                filtro_dist = st.selectbox("Distintivo", ["Todos", "0", "ECO", "C", "B"], key="filtro_dist_lista")
            with col_f4:
                filtro_ant = st.selectbox("Antigüedad", ["Todos", "< 5 años", "5-10 años", "> 10 años"], key="filtro_ant_lista")

            comp_id_filtro = next((c['id'] for c in competidores if c['nombre'] == filtro_comp), None) if filtro_comp != "Todos" else None
            vehiculos = obtener_vehiculos_competencia(competidor_id=comp_id_filtro)

            if vehiculos:
                df_veh = pd.DataFrame(vehiculos)

                if filtro_tipo != "Todos":
                    df_veh = df_veh[df_veh['tipo_vehiculo'] == filtro_tipo]
                if filtro_dist != "Todos":
                    df_veh = df_veh[df_veh['distintivo_ambiental'] == filtro_dist]
                if filtro_ant == "< 5 años":
                    df_veh = df_veh[df_veh['edad'] < 5]
                elif filtro_ant == "5-10 años":
                    df_veh = df_veh[(df_veh['edad'] >= 5) & (df_veh['edad'] <= 10)]
                elif filtro_ant == "> 10 años":
                    df_veh = df_veh[df_veh['edad'] > 10]

                st.caption(f"Mostrando {len(df_veh)} vehículos")

                if len(df_veh) > 0:
                    col_hist, col_table = st.columns([1, 2])
                    with col_hist:
                        fig_hist = px.histogram(df_veh, x='edad', nbins=10, labels={'edad': 'Edad (años)'}, color_discrete_sequence=['#3366cc'])
                        fig_hist.update_layout(height=300, margin=dict(t=20, b=20))
                        st.plotly_chart(fig_hist, use_container_width=True)

                    with col_table:
                        df_show = df_veh[['competidor_nombre', 'matricula', 'marca', 'modelo', 'plazas', 'ano_matriculacion', 'edad', 'distintivo_ambiental']].copy()
                        df_show.columns = ['Competidor', 'Matrícula', 'Marca', 'Modelo', 'Plazas', 'Año', 'Edad', 'Distintivo']
                        df_show['Matrícula'] = df_show['Matrícula'].fillna('-')
                        st.dataframe(df_show, use_container_width=True, hide_index=True, height=300)
            else:
                st.info("No hay vehículos registrados")


# ============================================
# PÁGINA: PIPELINE VISUAL (KANBAN)
# ============================================
elif pagina == "Pipeline":
    st.title("📊 Pipeline de Presupuestos")
    st.caption("Vista Kanban del estado de los presupuestos")

    # Cargar datos
    df_todos = cargar_datos()

    if df_todos is not None and not df_todos.empty:
        # Convertir fechas
        df_todos['Fecha alta'] = pd.to_datetime(df_todos['Fecha alta'], errors='coerce')
        df_todos['Fecha Salida'] = pd.to_datetime(df_todos['Fecha Salida'], errors='coerce')
        hoy = datetime.now().date()

        # Selector de tipo de fecha
        col_tipo_fecha, col_periodo = st.columns([1, 3])
        with col_tipo_fecha:
            tipo_fecha_pipeline = st.radio(
                "Filtrar por",
                ["Fecha alta", "Fecha Salida"],
                horizontal=True,
                key="tipo_fecha_pipeline"
            )

        col_fecha_pipeline = tipo_fecha_pipeline
        fecha_min = df_todos[col_fecha_pipeline].min().date() if df_todos[col_fecha_pipeline].notna().any() else hoy
        fecha_max = df_todos[col_fecha_pipeline].max().date() if df_todos[col_fecha_pipeline].notna().any() else hoy

        # Filtros rápidos de fecha
        st.markdown("**📅 Período:**")
        filtros_rapidos = st.columns(7)

        filtro_seleccionado = None
        with filtros_rapidos[0]:
            if st.button("Hoy", use_container_width=True, type="secondary"):
                filtro_seleccionado = "hoy"
        with filtros_rapidos[1]:
            if st.button("7 días", use_container_width=True, type="secondary"):
                filtro_seleccionado = "7d"
        with filtros_rapidos[2]:
            if st.button("15 días", use_container_width=True, type="secondary"):
                filtro_seleccionado = "15d"
        with filtros_rapidos[3]:
            if st.button("30 días", use_container_width=True, type="secondary"):
                filtro_seleccionado = "30d"
        with filtros_rapidos[4]:
            if st.button("90 días", use_container_width=True, type="secondary"):
                filtro_seleccionado = "90d"
        with filtros_rapidos[5]:
            if st.button("Este año", use_container_width=True, type="secondary"):
                filtro_seleccionado = "año"
        with filtros_rapidos[6]:
            if st.button("Todo", use_container_width=True, type="secondary"):
                filtro_seleccionado = "todo"

        # Guardar filtro en session_state
        if filtro_seleccionado:
            st.session_state.pipeline_filtro = filtro_seleccionado

        # Calcular rango según filtro (asegurando que esté dentro del rango de datos)
        filtro_actual = st.session_state.get('pipeline_filtro', '90d')

        if filtro_actual == "hoy":
            fecha_inicio = min(hoy, fecha_max)
            fecha_fin = min(hoy, fecha_max)
        elif filtro_actual == "7d":
            fecha_inicio = max(fecha_max - timedelta(days=7), fecha_min)
            fecha_fin = fecha_max
        elif filtro_actual == "15d":
            fecha_inicio = max(fecha_max - timedelta(days=15), fecha_min)
            fecha_fin = fecha_max
        elif filtro_actual == "30d":
            fecha_inicio = max(fecha_max - timedelta(days=30), fecha_min)
            fecha_fin = fecha_max
        elif filtro_actual == "90d":
            fecha_inicio = max(fecha_max - timedelta(days=90), fecha_min)
            fecha_fin = fecha_max
        elif filtro_actual == "año":
            fecha_inicio = max(fecha_max.replace(month=1, day=1), fecha_min)
            fecha_fin = fecha_max
        else:  # todo
            fecha_inicio = fecha_min
            fecha_fin = fecha_max

        # Filtros adicionales
        col_filtro1, col_filtro2, col_filtro3, col_filtro4, col_filtro5, col_filtro6 = st.columns([2, 1.5, 1.5, 1, 1.5, 1])

        with col_filtro1:
            rango_fechas = st.date_input(
                "Rango personalizado",
                value=(fecha_inicio, fecha_fin),
                min_value=fecha_min,
                max_value=fecha_max
            )

        with col_filtro2:
            # Filtro por grupo de clientes
            grupos = ['Todos'] + sorted(df_todos['Grupo de clientes'].dropna().unique().tolist())
            grupo_default = st.session_state.get('pipeline_grupo', 'Todos')
            grupo_idx = grupos.index(grupo_default) if grupo_default in grupos else 0
            grupo_sel = st.selectbox("Grupo cliente", grupos, index=grupo_idx, key="sel_grupo_pipeline")

        with col_filtro3:
            # Filtro por tipo de servicio (mostrar descripciones)
            tipos_guardados_pip = obtener_tipos_servicio_db()
            codigos_unicos_pip = sorted(df_todos['Tipo Servicio'].dropna().unique().tolist())
            opciones_tipo_pip = {'Todos': 'Todos'}
            for codigo in codigos_unicos_pip:
                desc = tipos_guardados_pip.get(codigo, {}).get('descripcion', '')
                opciones_tipo_pip[codigo] = normalizar_texto(desc) if desc else codigo
            descripciones_pip = ['Todos'] + sorted(set([v for k, v in opciones_tipo_pip.items() if k != 'Todos']))
            tipo_sel_desc = st.selectbox("Tipo servicio", descripciones_pip, key="sel_tipo_pipeline")

        with col_filtro4:
            # Filtro por importe mínimo
            importe_default = st.session_state.get('pipeline_importe', 0)
            importe_min = st.number_input("Importe mín €", min_value=0, value=importe_default, step=100, key="input_importe_pipeline")

        with col_filtro5:
            # Búsqueda por cliente
            cliente_default = st.session_state.get('pipeline_cliente', '')
            buscar_cliente = st.text_input("🔍 Cliente", value=cliente_default, key="input_cliente_pipeline")

        with col_filtro6:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ Limpiar", key="limpiar_filtros_pipeline", use_container_width=True):
                st.session_state.pipeline_filtro = 'todo'
                st.session_state.pipeline_grupo = 'Todos'
                st.session_state.pipeline_tipo = 'Todos'
                st.session_state.pipeline_importe = 0
                st.session_state.pipeline_cliente = ''
                st.rerun()

        # Agrupar por presupuesto (un presupuesto = una unidad, aunque tenga varias líneas)
        df_presupuestos = df_todos.groupby('Cod. Presupuesto').agg({
            'Cliente': 'first',
            'Fecha alta': 'first',
            'Fecha Salida': 'first',
            'Estado presupuesto': 'first',
            'Total importe': 'sum',  # Sumar todas las líneas del presupuesto
            'Tipo Servicio': 'first',
            'Grupo de clientes': 'first'
        }).reset_index()

        # Aplicar filtros
        df_pipeline = df_presupuestos.copy()

        if len(rango_fechas) == 2:
            df_pipeline = df_pipeline[
                (df_pipeline[col_fecha_pipeline].dt.date >= rango_fechas[0]) &
                (df_pipeline[col_fecha_pipeline].dt.date <= rango_fechas[1])
            ]

        if grupo_sel != 'Todos':
            df_pipeline = df_pipeline[df_pipeline['Grupo de clientes'] == grupo_sel]

        if tipo_sel_desc != 'Todos':
            # Filtrar por descripción: encontrar códigos que tienen esa descripción
            codigos_filtrar_pip = [cod for cod, desc in opciones_tipo_pip.items() if desc == tipo_sel_desc]
            df_pipeline = df_pipeline[df_pipeline['Tipo Servicio'].isin(codigos_filtrar_pip)]

        if importe_min > 0:
            df_pipeline = df_pipeline[df_pipeline['Total importe'] >= importe_min]

        if buscar_cliente:
            df_pipeline = df_pipeline[
                df_pipeline['Cliente'].str.lower().str.contains(buscar_cliente.lower(), na=False)
            ]

        st.markdown("---")

        # Definir columnas del Kanban con colores
        KANBAN_COLS = {
            'EL': {'nombre': '📝 En Elaboración', 'color': '#6c757d', 'bg': '#f8f9fa', 'estados': ['EL']},
            'V': {'nombre': '💰 Valorado', 'color': '#0d6efd', 'bg': '#e7f1ff', 'estados': ['V']},
            'E': {'nombre': '📤 Enviado', 'color': '#fd7e14', 'bg': '#fff3e6', 'estados': ['E']},
            'A': {'nombre': '✅ Aceptado', 'color': '#198754', 'bg': '#e8f5e9', 'estados': ['A', 'AP']},
            'R': {'nombre': '❌ Rechazado', 'color': '#dc3545', 'bg': '#fdeaea', 'estados': ['R']},
        }

        # Calcular datos del año anterior para el mismo período (con mismos filtros)
        if len(rango_fechas) == 2:
            fecha_inicio_anterior = rango_fechas[0].replace(year=rango_fechas[0].year - 1)
            fecha_fin_anterior = rango_fechas[1].replace(year=rango_fechas[1].year - 1)

            df_anterior = df_presupuestos[
                (df_presupuestos['Fecha alta'].dt.date >= fecha_inicio_anterior) &
                (df_presupuestos['Fecha alta'].dt.date <= fecha_fin_anterior)
            ]

            # Aplicar mismos filtros de grupo y tipo
            if grupo_sel != 'Todos':
                df_anterior = df_anterior[df_anterior['Grupo de clientes'] == grupo_sel]
            if tipo_sel != 'Todos':
                df_anterior = df_anterior[df_anterior['Tipo Servicio'] == tipo_sel]
        else:
            df_anterior = pd.DataFrame()

        # Métricas actuales
        total_pipeline = df_pipeline[df_pipeline['Estado presupuesto'].isin(['EL', 'V', 'E'])]['Total importe'].sum()
        total_ganado = df_pipeline[df_pipeline['Estado presupuesto'].isin(['A', 'AP'])]['Total importe'].sum()
        total_perdido = df_pipeline[df_pipeline['Estado presupuesto'] == 'R']['Total importe'].sum()
        num_presupuestos = len(df_pipeline)
        num_ganados = len(df_pipeline[df_pipeline['Estado presupuesto'].isin(['A', 'AP'])])
        tasa_conversion = (num_ganados / num_presupuestos * 100) if num_presupuestos > 0 else 0

        # Métricas año anterior
        if not df_anterior.empty:
            total_ganado_ant = df_anterior[df_anterior['Estado presupuesto'].isin(['A', 'AP'])]['Total importe'].sum()
            total_perdido_ant = df_anterior[df_anterior['Estado presupuesto'] == 'R']['Total importe'].sum()
            num_presupuestos_ant = len(df_anterior)
            num_ganados_ant = len(df_anterior[df_anterior['Estado presupuesto'].isin(['A', 'AP'])])
            tasa_conversion_ant = (num_ganados_ant / num_presupuestos_ant * 100) if num_presupuestos_ant > 0 else 0

            # Calcular deltas
            delta_ganado = ((total_ganado - total_ganado_ant) / total_ganado_ant * 100) if total_ganado_ant > 0 else 0
            delta_perdido = ((total_perdido - total_perdido_ant) / total_perdido_ant * 100) if total_perdido_ant > 0 else 0
            delta_presupuestos = ((num_presupuestos - num_presupuestos_ant) / num_presupuestos_ant * 100) if num_presupuestos_ant > 0 else 0
            delta_conversion = tasa_conversion - tasa_conversion_ant
        else:
            delta_ganado = delta_perdido = delta_presupuestos = delta_conversion = None

        # Mostrar métricas con comparativa
        col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)

        col_m1.metric(
            "📋 Presupuestos",
            f"{num_presupuestos:,}",
            f"{delta_presupuestos:+.1f}% vs año ant." if delta_presupuestos is not None else None
        )
        col_m2.metric(
            "💼 En Pipeline",
            f"{total_pipeline:,.0f} €"
        )
        col_m3.metric(
            "✅ Ganado",
            f"{total_ganado:,.0f} €",
            f"{delta_ganado:+.1f}%" if delta_ganado is not None else None
        )
        col_m4.metric(
            "❌ Perdido",
            f"{total_perdido:,.0f} €",
            f"{delta_perdido:+.1f}%" if delta_perdido is not None else None,
            delta_color="inverse"
        )
        col_m5.metric(
            "📈 Conversión",
            f"{tasa_conversion:.1f}%",
            f"{delta_conversion:+.1f}pp" if delta_conversion is not None else None
        )

        st.markdown("---")

        # Crear columnas del Kanban
        cols = st.columns(len(KANBAN_COLS))

        for idx, (estado, config) in enumerate(KANBAN_COLS.items()):
            with cols[idx]:
                df_estado = df_pipeline[df_pipeline['Estado presupuesto'].isin(config['estados'])]
                count = len(df_estado)
                total = df_estado['Total importe'].sum()

                # Cabecera
                st.markdown(f'<div style="background-color:{config["color"]};color:white;padding:10px;border-radius:8px 8px 0 0;text-align:center;"><strong>{config["nombre"]}</strong><br><span style="font-size:0.9em;">{count} | {total:,.0f} €</span></div>', unsafe_allow_html=True)

                # Contenedor con scroll
                container = st.container(height=350)
                with container:
                    if df_estado.empty:
                        st.caption("Sin presupuestos")
                    else:
                        for _, row in df_estado.head(8).iterrows():
                            fecha_str = row['Fecha alta'].strftime('%d/%m') if pd.notna(row['Fecha alta']) else ''
                            cliente_corto = str(row['Cliente'])[:18] + '..' if len(str(row['Cliente'])) > 18 else str(row['Cliente'])
                            st.markdown(f'<div style="background:white;padding:8px;margin:4px 0;border-radius:6px;border-left:4px solid {config["color"]};box-shadow:0 1px 3px rgba(0,0,0,0.1);"><div style="font-size:0.7em;color:#666;">{row["Cod. Presupuesto"]} · {fecha_str}</div><div style="font-weight:600;color:#333;font-size:0.85em;">{cliente_corto}</div><div style="font-size:0.85em;color:{config["color"]};font-weight:600;">{row["Total importe"]:,.0f} €</div></div>', unsafe_allow_html=True)
                        if count > 8:
                            st.caption(f"+{count - 8} más...")

        st.markdown("---")

        # Gráfico de embudo
        st.subheader("🔻 Embudo de Ventas")

        embudo_data = []
        for estado, config in KANBAN_COLS.items():
            df_estado = df_pipeline[df_pipeline['Estado presupuesto'].isin(config['estados'])]
            embudo_data.append({
                'Estado': config['nombre'].split(' ', 1)[1] if ' ' in config['nombre'] else config['nombre'],
                'Cantidad': len(df_estado),
                'Importe': df_estado['Total importe'].sum()
            })

        df_embudo = pd.DataFrame(embudo_data)

        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            fig_cant = px.funnel(df_embudo, x='Cantidad', y='Estado',
                                title='Por Cantidad de Presupuestos')
            fig_cant.update_layout(height=350)
            fig_cant.update_traces(marker_color=['#6c757d', '#0d6efd', '#fd7e14', '#198754', '#dc3545'])
            st.plotly_chart(fig_cant, use_container_width=True)

        with col_chart2:
            fig_imp = px.funnel(df_embudo, x='Importe', y='Estado',
                               title='Por Importe (€)')
            fig_imp.update_layout(height=350)
            fig_imp.update_traces(marker_color=['#6c757d', '#0d6efd', '#fd7e14', '#198754', '#dc3545'])
            st.plotly_chart(fig_imp, use_container_width=True)

    else:
        st.warning("No hay datos disponibles para mostrar el pipeline.")


# ============================================
# PÁGINA 3: SEGUIMIENTO DE PRESUPUESTOS
# ============================================
elif pagina == "Seguimiento Presupuestos":
    st.title("📋 Seguimiento de Presupuestos")
    st.markdown("---")

    hoy_seg = datetime.now()

    # --- FILTROS RÁPIDOS DE TIEMPO ---
    col_rapidos_seg = st.columns(6)

    trim_actual_seg = (hoy_seg.month - 1) // 3 + 1
    inicio_trim_seg = datetime(hoy_seg.year, (trim_actual_seg - 1) * 3 + 1, 1)

    periodos_seg = {
        "Este mes": (hoy_seg.replace(day=1).date(), hoy_seg.date()),
        "Mes ant.": ((hoy_seg.replace(day=1) - timedelta(days=1)).replace(day=1).date(), (hoy_seg.replace(day=1) - timedelta(days=1)).date()),
        "Este trim.": (inicio_trim_seg.date(), hoy_seg.date()),
        "Este año": (datetime(hoy_seg.year, 1, 1).date(), hoy_seg.date()),
        "Año ant.": (datetime(hoy_seg.year-1, 1, 1).date(), datetime(hoy_seg.year-1, 12, 31).date()),
        "Todo": None
    }

    if 'periodo_seg' not in st.session_state:
        st.session_state.periodo_seg = "Este año"

    for i, nombre in enumerate(periodos_seg.keys()):
        with col_rapidos_seg[i]:
            if st.button(nombre, key=f"btn_seg_{nombre}",
                        type="primary" if st.session_state.periodo_seg == nombre else "secondary",
                        use_container_width=True):
                st.session_state.periodo_seg = nombre
                st.rerun()

    # Filtros adicionales
    col1, col2, col3 = st.columns(3)

    with col1:
        comerciales = obtener_comerciales(df)
        comercial_sel = st.selectbox("Comercial", comerciales)

    with col2:
        estado_sel = st.selectbox("Estado", ['Todos', 'E - Enviado', 'V - Valorado'])

    with col3:
        dias_antiguedad = st.slider("Días desde fecha alta", 0, 365, 30)

    # Filtrar presupuestos
    pendientes = obtener_presupuestos_pendientes(df)

    # Aplicar filtro de periodo rápido
    if st.session_state.periodo_seg != "Todo" and periodos_seg[st.session_state.periodo_seg]:
        fecha_ini_seg, fecha_fin_seg = periodos_seg[st.session_state.periodo_seg]
        pendientes = pendientes[
            (pendientes['Fecha alta'].dt.date >= fecha_ini_seg) &
            (pendientes['Fecha alta'].dt.date <= fecha_fin_seg)
        ]

    if comercial_sel != 'Todos':
        pendientes = pendientes[pendientes['Atendido por'] == comercial_sel]

    if estado_sel != 'Todos':
        estado_code = estado_sel.split(' - ')[0]
        pendientes = pendientes[pendientes['Estado presupuesto'] == estado_code]

    fecha_limite = datetime.now() - timedelta(days=dias_antiguedad)
    pendientes = pendientes[pendientes['Fecha alta'] <= fecha_limite]

    # Métricas (contando presupuestos únicos, no líneas)
    num_presupuestos_unicos = pendientes['Cod. Presupuesto'].nunique()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Presupuestos Pendientes", num_presupuestos_unicos)
    with col2:
        st.metric("Importe Total", f"€{pendientes['Total importe'].sum():,.2f}")
    with col3:
        st.metric("Clientes Únicos", pendientes['Cliente'].nunique())

    st.markdown("---")

    # Tabla de presupuestos pendientes (agrupados por Cod. Presupuesto)
    st.subheader("Lista de Presupuestos Pendientes")

    if not pendientes.empty:
        # Agrupar por Cod. Presupuesto (cada presupuesto es una unidad)
        pendientes_agrupados = pendientes.groupby('Cod. Presupuesto').agg({
            'Cliente': 'first',
            'Descripción': lambda x: ' | '.join(x.dropna().unique()[:3]),  # Primeras 3 descripciones únicas
            'Total importe': 'sum',
            'Fecha alta': 'first',
            'Atendido por': 'first',
            'Estado presupuesto': 'first'
        }).reset_index()

        # Calcular días desde alta
        pendientes_agrupados['Dias Pendiente'] = (datetime.now() - pendientes_agrupados['Fecha alta']).dt.days

        cols_mostrar = ['Cod. Presupuesto', 'Cliente', 'Descripción', 'Total importe',
                        'Fecha alta', 'Dias Pendiente', 'Atendido por', 'Estado presupuesto']

        st.dataframe(
            pendientes_agrupados[cols_mostrar].sort_values('Dias Pendiente', ascending=False),
            use_container_width=True,
            height=400
        )

        # Exportar
        csv = pendientes_agrupados[cols_mostrar].to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Exportar a CSV",
            csv,
            "presupuestos_pendientes.csv",
            "text/csv"
        )

        st.markdown("---")

        # Sección de notas
        st.subheader("📝 Agregar Nota de Seguimiento")

        col1, col2 = st.columns(2)

        with col1:
            presupuesto_nota = st.selectbox(
                "Seleccionar Presupuesto",
                pendientes['Cod. Presupuesto'].unique()
            )

            cliente_nota = pendientes[pendientes['Cod. Presupuesto'] == presupuesto_nota]['Cliente'].iloc[0]
            st.info(f"Cliente: {cliente_nota}")

        with col2:
            tipo_nota = st.selectbox("Tipo de Nota", ['Seguimiento', 'Llamada', 'Email', 'Reunión', 'Otro'])
            usuario_nota = st.text_input("Tu nombre", value="")

        contenido_nota = st.text_area("Contenido de la nota")

        if st.button("💾 Guardar Nota"):
            if contenido_nota and usuario_nota:
                agregar_nota(
                    str(presupuesto_nota),
                    cliente_nota,
                    contenido_nota,
                    tipo_nota.lower(),
                    usuario_nota
                )
                st.success("Nota guardada correctamente")
                st.rerun()
            else:
                st.error("Por favor completa el contenido y tu nombre")

        # Mostrar notas del presupuesto seleccionado
        st.subheader(f"📋 Historial de Notas - Presupuesto {presupuesto_nota}")
        notas = obtener_notas_presupuesto(str(presupuesto_nota))

        if notas:
            for nota in notas:
                with st.expander(f"📌 {nota['tipo'].upper()} - {nota['fecha'][:16]} - {nota['usuario']}"):
                    st.write(nota['contenido'])
        else:
            st.info("No hay notas para este presupuesto")

    else:
        st.info("No hay presupuestos pendientes con los filtros seleccionados")


# ============================================
# PÁGINA 4: CLIENTES INACTIVOS
# ============================================
elif pagina == "Clientes":
    st.title("👥 Gestión de Clientes")
    st.markdown("---")

    # Resumen de segmentos
    st.subheader("Resumen por Segmento")

    segmentos_count = df_clientes['Segmento_Cliente'].value_counts()
    segmentos_orden = ['HABITUAL', 'OCASIONAL_ACTIVO', 'REACTIVADO', 'PROSPECTO', 'INACTIVO']

    col1, col2, col3, col4, col5 = st.columns(5)
    cols = [col1, col2, col3, col4, col5]
    iconos = {'HABITUAL': '⭐', 'OCASIONAL_ACTIVO': '🔄', 'REACTIVADO': '🔙', 'PROSPECTO': '🎯', 'INACTIVO': '😴'}

    for i, seg in enumerate(segmentos_orden):
        with cols[i]:
            count = segmentos_count.get(seg, 0)
            st.metric(f"{iconos.get(seg, '')} {seg.replace('_', ' ').title()}", count)

    st.markdown("---")

    # Filtros
    st.subheader("Filtrar Clientes")
    col1, col2, col3 = st.columns(3)

    with col1:
        segmento_filtro = st.selectbox(
            "Segmento",
            ["Todos"] + segmentos_orden
        )

    with col2:
        grupos_disponibles = ['Todos'] + sorted(df_clientes['Grupo_Cliente'].dropna().unique().tolist())
        grupo_filtro = st.selectbox("Grupo", grupos_disponibles)

    with col3:
        buscar_cliente = st.text_input("Buscar por nombre", "")

    # Aplicar filtros
    df_filtrado = df_clientes.copy()

    if segmento_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado['Segmento_Cliente'] == segmento_filtro]

    if grupo_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado['Grupo_Cliente'] == grupo_filtro]

    if buscar_cliente:
        df_filtrado = df_filtrado[df_filtrado['Nombre_Cliente'].str.contains(buscar_cliente, case=False, na=False)]

    # Métricas del filtro
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Clientes", len(df_filtrado))

    with col2:
        con_email = len(df_filtrado[df_filtrado['Mail'].notna() & (df_filtrado['Mail'] != '')])
        st.metric("Con Email", con_email)

    with col3:
        total_revenue = df_filtrado['total_revenue'].sum() if 'total_revenue' in df_filtrado.columns else 0
        st.metric("Facturación Total", f"€{total_revenue:,.0f}")

    with col4:
        total_services = df_filtrado['total_services'].sum() if 'total_services' in df_filtrado.columns else 0
        st.metric("Total Servicios", f"{int(total_services):,}")

    st.markdown("---")

    # Tabla de clientes
    st.subheader(f"Lista de Clientes ({len(df_filtrado)})")

    if not df_filtrado.empty:
        # Seleccionar columnas a mostrar
        columnas_mostrar = ['Cod_Cliente', 'Nombre_Cliente', 'Segmento_Cliente', 'Mail', 'Población',
                           'Grupo_Cliente', 'total_services', 'total_revenue', 'days_since_last_service']
        columnas_disponibles = [c for c in columnas_mostrar if c in df_filtrado.columns]

        df_mostrar = df_filtrado[columnas_disponibles].copy()
        df_mostrar.columns = ['Código', 'Nombre', 'Segmento', 'Email', 'Población',
                              'Grupo', 'Servicios', 'Facturación', 'Días Inactivo'][:len(columnas_disponibles)]

        st.dataframe(
            df_mostrar.sort_values('Facturación' if 'Facturación' in df_mostrar.columns else 'Nombre', ascending=False),
            use_container_width=True,
            height=400
        )

        # Exportar
        clientes_email = df_filtrado[df_filtrado['Mail'].notna() & (df_filtrado['Mail'] != '')]
        if not clientes_email.empty:
            csv = clientes_email[columnas_disponibles].to_csv(index=False).encode('utf-8')
            st.download_button(
                f"📥 Exportar {len(clientes_email)} clientes con email",
                csv,
                f"clientes_{segmento_filtro.lower()}.csv",
                "text/csv"
            )

        st.markdown("---")

        # Detalle de cliente
        st.subheader("🔍 Detalle de Cliente")
        clientes_lista = df_filtrado['Nombre_Cliente'].dropna().tolist()

        if clientes_lista:
            cliente_sel = st.selectbox("Seleccionar cliente", clientes_lista)

            if cliente_sel:
                # Info del cliente
                cliente_info = df_filtrado[df_filtrado['Nombre_Cliente'] == cliente_sel].iloc[0]
                codigo_cliente = cliente_info['Cod_Cliente']

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**Código:** {codigo_cliente}")
                    st.markdown(f"**Segmento:** {cliente_info.get('Segmento_Cliente', 'N/A')}")
                    st.markdown(f"**Grupo:** {cliente_info.get('Grupo_Cliente', 'N/A')}")

                with col2:
                    st.markdown(f"**Email:** {cliente_info.get('Mail', 'N/A')}")
                    st.markdown(f"**Población:** {cliente_info.get('Población', 'N/A')}")
                    servicios = cliente_info.get('total_services', 0)
                    st.markdown(f"**Servicios totales:** {int(servicios) if pd.notna(servicios) else 0}")

                # Historial de presupuestos (agrupados por Cod. Presupuesto)
                st.markdown("**Historial de presupuestos:**")
                historial_raw = df[df['Código'] == codigo_cliente].copy()

                if not historial_raw.empty:
                    historial = historial_raw.groupby('Cod. Presupuesto').agg({
                        'Fecha alta': 'first',
                        'Descripción': lambda x: ' | '.join(x.dropna().unique()[:3]),
                        'Total importe': 'sum',
                        'Estado presupuesto': 'first'
                    }).reset_index().sort_values('Fecha alta', ascending=False)
                    st.dataframe(historial, use_container_width=True, height=200)
                else:
                    st.info("No hay presupuestos para este cliente")

                # Notas del cliente
                st.markdown(f"**📝 Notas de {cliente_sel}:**")
                notas_cliente = obtener_notas_cliente(cliente_sel)

                if notas_cliente:
                    for nota in notas_cliente:
                        with st.expander(f"📌 {nota['tipo'].upper()} - {nota['fecha'][:16]}"):
                            st.write(nota['contenido'])
                else:
                    st.info("No hay notas para este cliente")
    else:
        st.info("No hay clientes con los criterios seleccionados")


# ============================================
# PÁGINA 5: CAMPAÑAS SEGMENTADAS
# ============================================
elif pagina == "Campanas Segmentadas":
    st.title("🎯 Campañas Segmentadas")
    st.markdown("---")

    st.subheader("Configurar Segmento")

    # Filtros de segmentación
    col1, col2 = st.columns(2)

    with col1:
        grupo_seg = st.selectbox("Grupo de Clientes", obtener_grupos_clientes(df))
        importe_min = st.number_input("Importe Mínimo Histórico (€)", min_value=0, value=0, step=100)

    with col2:
        tipo_servicio_seg = st.selectbox("Tipo de Servicio", obtener_tipos_servicio(df))
        importe_max = st.number_input("Importe Máximo Histórico (€)", min_value=0, value=0, step=100)

    importe_max = importe_max if importe_max > 0 else None

    # Obtener segmento
    segmento = obtener_segmentacion(
        df,
        grupo=grupo_seg if grupo_seg != 'Todos' else None,
        tipo_servicio=tipo_servicio_seg if tipo_servicio_seg != 'Todos' else None,
        importe_min=importe_min if importe_min > 0 else None,
        importe_max=importe_max
    )

    st.markdown("---")

    # Métricas del segmento
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Clientes en Segmento", len(segmento))

    with col2:
        st.metric("Con Email Válido", len(segmento[segmento['Email'].notna()]))

    with col3:
        st.metric("Importe Total Histórico", f"€{segmento['Importe Total'].sum():,.2f}")

    st.markdown("---")

    # Vista previa del segmento
    st.subheader("Vista Previa del Segmento")

    if not segmento.empty:
        st.dataframe(
            segmento.sort_values('Importe Total', ascending=False),
            use_container_width=True,
            height=400
        )

        # Distribución por grupo
        st.subheader("Distribución del Segmento por Grupo")
        dist_grupo = segmento['Grupo'].value_counts()
        fig = px.bar(x=dist_grupo.index, y=dist_grupo.values)
        fig.update_layout(xaxis_title="Grupo", yaxis_title="Número de clientes")
        st.plotly_chart(fig, use_container_width=True)

        # Exportar
        st.markdown("---")
        st.subheader("📥 Exportar Segmento")

        col1, col2 = st.columns(2)

        with col1:
            csv_completo = segmento.to_csv(index=False).encode('utf-8')
            st.download_button(
                f"📥 Exportar todos ({len(segmento)} clientes)",
                csv_completo,
                "segmento_completo.csv",
                "text/csv"
            )

        with col2:
            solo_emails = segmento[segmento['Email'].notna()][['Cliente', 'Email']].drop_duplicates()
            csv_emails = solo_emails.to_csv(index=False).encode('utf-8')
            st.download_button(
                f"📧 Solo emails ({len(solo_emails)} emails)",
                csv_emails,
                "segmento_emails.csv",
                "text/csv"
            )

    else:
        st.warning("No hay clientes que coincidan con los criterios seleccionados")


# ============================================
# PÁGINA 6: ANÁLISIS DE CONVERSIÓN
# ============================================
elif pagina == "Analisis Conversion":
    st.title("Analisis de Conversion")
    st.markdown("---")

    # ========== FILTROS ==========
    st.subheader("Filtros")

    hoy = datetime.now()

    # --- FILTROS RÁPIDOS DE TIEMPO ---
    col_rapidos_conv = st.columns(6)

    trim_actual_conv = (hoy.month - 1) // 3 + 1
    inicio_trim_conv = datetime(hoy.year, (trim_actual_conv - 1) * 3 + 1, 1)

    periodos_conv = {
        "Este mes": (hoy.replace(day=1).date(), hoy.date()),
        "Mes ant.": ((hoy.replace(day=1) - timedelta(days=1)).replace(day=1).date(), (hoy.replace(day=1) - timedelta(days=1)).date()),
        "Este trim.": (inicio_trim_conv.date(), hoy.date()),
        "Este año": (datetime(hoy.year, 1, 1).date(), hoy.date()),
        "Año ant.": (datetime(hoy.year-1, 1, 1).date(), datetime(hoy.year-1, 12, 31).date()),
        "Todo": None
    }

    if 'periodo_conv' not in st.session_state:
        st.session_state.periodo_conv = "Este año"

    for i, nombre in enumerate(periodos_conv.keys()):
        with col_rapidos_conv[i]:
            if st.button(nombre, key=f"btn_conv_{nombre}",
                        type="primary" if st.session_state.periodo_conv == nombre else "secondary",
                        use_container_width=True):
                st.session_state.periodo_conv = nombre
                st.rerun()

    # Primera fila: Filtro de fechas
    col_fecha_tipo, col_fecha_desde, col_fecha_hasta = st.columns([1, 1, 1])

    with col_fecha_tipo:
        campo_fecha = st.selectbox("Filtrar por", ["Fecha de alta", "Fecha de salida"], key="campo_fecha_conv")

    # Determinar columna de fecha según selección
    col_fecha = 'Fecha alta' if campo_fecha == "Fecha de alta" else 'Fecha Salida'

    # Calcular rango de fechas disponibles
    fechas_validas = df[col_fecha].dropna()
    if len(fechas_validas) > 0:
        fecha_min = fechas_validas.min().date()
        fecha_max = fechas_validas.max().date()
    else:
        fecha_min = hoy.date() - timedelta(days=365)
        fecha_max = hoy.date()

    # Usar periodo rápido seleccionado o defaults
    if st.session_state.periodo_conv == "Todo":
        fecha_default_desde = fecha_min
        fecha_default_hasta = fecha_max
    elif st.session_state.periodo_conv in periodos_conv and periodos_conv[st.session_state.periodo_conv]:
        fecha_default_desde = max(periodos_conv[st.session_state.periodo_conv][0], fecha_min)
        fecha_default_hasta = min(periodos_conv[st.session_state.periodo_conv][1], fecha_max)
    else:
        fecha_default_desde = max(datetime(hoy.year, 1, 1).date(), fecha_min)
        fecha_default_hasta = min(hoy.date(), fecha_max)

    with col_fecha_desde:
        fecha_desde = st.date_input("Desde", value=fecha_default_desde, min_value=fecha_min, max_value=fecha_max, key="fecha_desde_conv")

    with col_fecha_hasta:
        fecha_hasta = st.date_input("Hasta", value=fecha_default_hasta, min_value=fecha_min, max_value=fecha_max, key="fecha_hasta_conv")

    # Segunda fila: Otros filtros
    col1, col2, col3 = st.columns(3)

    with col1:
        # Obtener tipos con descripciones (siempre mostrar descripción, nunca código)
        tipos_guardados = obtener_tipos_servicio_db()
        codigos_unicos = sorted(df['Tipo Servicio'].dropna().unique().tolist())
        opciones_tipo = {'Todos': 'Todos'}
        for codigo in codigos_unicos:
            desc = tipos_guardados.get(codigo, {}).get('descripcion', '')
            # Si no hay descripción, crear una legible a partir del código
            if desc:
                opciones_tipo[codigo] = normalizar_texto(desc)
            else:
                # Convertir código a descripción legible (ej: "ESC" -> "Escolar", "NAC" -> "Nacional")
                descripciones_default = {
                    'ESC': 'Escolar', 'NAC': 'Nacional', 'INT': 'Internacional',
                    'URB': 'Urbano', 'TRF': 'Transfer', 'EXC': 'Excursion',
                    'EVE': 'Evento', 'BOD': 'Boda', 'AER': 'Aeropuerto',
                    'CRU': 'Crucero', 'SKI': 'Nieve/Ski', 'PLY': 'Playa',
                    'EMP': 'Empresa', 'DEP': 'Deportivo', 'CUL': 'Cultural'
                }
                opciones_tipo[codigo] = descripciones_default.get(codigo.upper(), codigo.replace('_', ' ').title())
        descripciones_unicas = ['Todos'] + sorted(set([v for k, v in opciones_tipo.items() if k != 'Todos']))
        tipo_sel_conv = st.selectbox("Tipo de Servicio", descripciones_unicas, key="tipo_conv")

    with col2:
        grupos = obtener_grupos_clientes(df)
        grupo_sel_conv = st.selectbox("Grupo de Clientes", grupos, key="grupo_conv")

    with col3:
        fuentes = obtener_fuentes(df)
        fuente_sel = st.selectbox("Fuente", fuentes, key="fuente_conv")

    # Aplicar filtros
    df_conv = df.copy()

    # Filtro por rango de fechas
    if col_fecha in df_conv.columns:
        df_conv = df_conv[df_conv[col_fecha].notna()]
        df_conv = df_conv[(df_conv[col_fecha].dt.date >= fecha_desde) & (df_conv[col_fecha].dt.date <= fecha_hasta)]

    if tipo_sel_conv != 'Todos':
        codigos_filtrar = [cod for cod, desc in opciones_tipo.items() if desc == tipo_sel_conv]
        df_conv = df_conv[df_conv['Tipo Servicio'].isin(codigos_filtrar)]

    if grupo_sel_conv != 'Todos':
        df_conv = df_conv[df_conv['Grupo de clientes'] == grupo_sel_conv]

    if fuente_sel != 'Todos':
        df_conv = df_conv[df_conv['Conocido por?'] == fuente_sel]

    # ========== CALCULAR PERIODO AÑO ANTERIOR ==========
    try:
        fecha_desde_ant = fecha_desde.replace(year=fecha_desde.year - 1)
        fecha_hasta_ant = fecha_hasta.replace(year=fecha_hasta.year - 1)
    except ValueError:  # 29 febrero
        fecha_desde_ant = fecha_desde.replace(year=fecha_desde.year - 1, day=28)
        fecha_hasta_ant = fecha_hasta.replace(year=fecha_hasta.year - 1, day=28)

    df_conv_anterior = df.copy()
    if col_fecha in df_conv_anterior.columns:
        df_conv_anterior = df_conv_anterior[df_conv_anterior[col_fecha].notna()]
        df_conv_anterior = df_conv_anterior[(df_conv_anterior[col_fecha].dt.date >= fecha_desde_ant) & (df_conv_anterior[col_fecha].dt.date <= fecha_hasta_ant)]

    # Aplicar mismos filtros al año anterior
    if tipo_sel_conv != 'Todos':
        codigos_filtrar = [cod for cod, desc in opciones_tipo.items() if desc == tipo_sel_conv]
        df_conv_anterior = df_conv_anterior[df_conv_anterior['Tipo Servicio'].isin(codigos_filtrar)]
    if grupo_sel_conv != 'Todos':
        df_conv_anterior = df_conv_anterior[df_conv_anterior['Grupo de clientes'] == grupo_sel_conv]
    if fuente_sel != 'Todos':
        df_conv_anterior = df_conv_anterior[df_conv_anterior['Conocido por?'] == fuente_sel]

    # Mostrar rango seleccionado con comparativa
    st.caption(f"📅 Mostrando datos por **{campo_fecha}** del {fecha_desde.strftime('%d/%m/%Y')} al {fecha_hasta.strftime('%d/%m/%Y')} ({len(df_conv)} registros)")
    if not df_conv_anterior.empty:
        st.caption(f"📊 Comparando con: {fecha_desde_ant.strftime('%d/%m/%Y')} - {fecha_hasta_ant.strftime('%d/%m/%Y')} ({len(df_conv_anterior)} registros año ant.)")

    st.markdown("---")

    # ========== RANKING DE COMERCIALES ==========
    st.subheader("Ranking de Comerciales")

    # Calcular métricas por comercial (contando presupuestos únicos, no líneas)
    # Un presupuesto = un Cod. Presupuesto único
    # Un presupuesto aceptado = al menos una línea con estado A o AP

    # Presupuestos únicos por comercial
    presupuestos_por_comercial = df_conv.groupby('Atendido por')['Cod. Presupuesto'].nunique().reset_index()
    presupuestos_por_comercial.columns = ['Comercial', 'Presupuestos']

    # Presupuestos aceptados (únicos donde al menos una línea es A o AP)
    df_aceptados = df_conv[df_conv['Estado presupuesto'].isin(['A', 'AP'])]
    aceptados_por_comercial = df_aceptados.groupby('Atendido por')['Cod. Presupuesto'].nunique().reset_index()
    aceptados_por_comercial.columns = ['Comercial', 'Aceptados']

    # Importe total (suma de todas las líneas)
    importe_total = df_conv.groupby('Atendido por')['Total importe'].sum().reset_index()
    importe_total.columns = ['Comercial', 'Importe Total']

    # Importe aceptado (suma de líneas aceptadas)
    importe_aceptado = df_aceptados.groupby('Atendido por')['Total importe'].sum().reset_index()
    importe_aceptado.columns = ['Comercial', 'Importe Aceptado']

    # Combinar todas las métricas
    comerciales_stats = presupuestos_por_comercial.merge(aceptados_por_comercial, on='Comercial', how='left')
    comerciales_stats = comerciales_stats.merge(importe_total, on='Comercial', how='left')
    comerciales_stats = comerciales_stats.merge(importe_aceptado, on='Comercial', how='left')

    # Rellenar NaN con 0
    comerciales_stats = comerciales_stats.fillna(0)

    # Asegurar tipos numéricos
    comerciales_stats['Presupuestos'] = pd.to_numeric(comerciales_stats['Presupuestos'], errors='coerce').fillna(0).astype(int)
    comerciales_stats['Aceptados'] = pd.to_numeric(comerciales_stats['Aceptados'], errors='coerce').fillna(0).astype(int)
    comerciales_stats['Importe Total'] = pd.to_numeric(comerciales_stats['Importe Total'], errors='coerce').fillna(0)
    comerciales_stats['Importe Aceptado'] = pd.to_numeric(comerciales_stats['Importe Aceptado'], errors='coerce').fillna(0)

    comerciales_stats['Tasa Conversion'] = (comerciales_stats['Aceptados'] / comerciales_stats['Presupuestos'].replace(0, 1) * 100).round(1)
    comerciales_stats['Ticket Medio'] = (comerciales_stats['Importe Aceptado'] / comerciales_stats['Aceptados'].replace(0, 1)).round(0)
    comerciales_stats.loc[comerciales_stats['Aceptados'] == 0, 'Ticket Medio'] = 0

    # Ordenar por importe aceptado (métrica principal)
    comerciales_stats = comerciales_stats.sort_values('Importe Aceptado', ascending=False)

    # Añadir posición en ranking
    comerciales_stats['Posicion'] = range(1, len(comerciales_stats) + 1)

    # Medallas para el podio
    def get_medalla(pos):
        if pos == 1: return "🥇"
        if pos == 2: return "🥈"
        if pos == 3: return "🥉"
        return f"#{pos}"

    comerciales_stats['Ranking'] = comerciales_stats['Posicion'].apply(get_medalla)

    # KPIs del periodo actual
    total_presupuestos = comerciales_stats['Presupuestos'].sum()
    total_aceptados = comerciales_stats['Aceptados'].sum()
    total_facturado = comerciales_stats['Importe Aceptado'].sum()
    tasa_global = (total_aceptados / total_presupuestos * 100) if total_presupuestos > 0 else 0

    # KPIs del año anterior
    if not df_conv_anterior.empty:
        presup_ant = df_conv_anterior['Cod. Presupuesto'].nunique()
        acept_ant = df_conv_anterior[df_conv_anterior['Estado presupuesto'].isin(['A', 'AP'])]['Cod. Presupuesto'].nunique()
        fact_ant = df_conv_anterior[df_conv_anterior['Estado presupuesto'].isin(['A', 'AP'])]['Total importe'].sum()
        tasa_ant = (acept_ant / presup_ant * 100) if presup_ant > 0 else 0

        delta_presup = ((total_presupuestos - presup_ant) / presup_ant * 100) if presup_ant > 0 else None
        delta_acept = ((total_aceptados - acept_ant) / acept_ant * 100) if acept_ant > 0 else None
        delta_fact = ((total_facturado - fact_ant) / fact_ant * 100) if fact_ant > 0 else None
        delta_tasa = tasa_global - tasa_ant
    else:
        delta_presup = delta_acept = delta_fact = delta_tasa = None

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Presupuestos", f"{total_presupuestos:,}",
                  delta=f"{delta_presup:+.1f}% vs año ant." if delta_presup is not None else None)
    with col2:
        st.metric("Total Aceptados", f"{total_aceptados:,}",
                  delta=f"{delta_acept:+.1f}% vs año ant." if delta_acept is not None else None)
    with col3:
        st.metric("Facturado", f"{total_facturado:,.0f} EUR",
                  delta=f"{delta_fact:+.1f}% vs año ant." if delta_fact is not None else None)
    with col4:
        st.metric("Tasa Global", f"{tasa_global:.1f}%",
                  delta=f"{delta_tasa:+.1f}pp vs año ant." if delta_tasa is not None else None)

    st.markdown("---")

    # ========== PODIO VISUAL ==========
    if len(comerciales_stats) >= 3:
        st.markdown("### Podio")
        col1, col2, col3 = st.columns([1, 1.2, 1])

        # Segundo lugar - DAVID Brand
        with col1:
            segundo = comerciales_stats.iloc[1]
            st.markdown(f"""
            <div style="text-align: center; padding: 24px; background: #F5F5F5; border-radius: 8px; margin-top: 30px; border: 1px solid #E0E0E0;">
                <h1 style="margin: 0;">🥈</h1>
                <h3 style="margin: 8px 0; color: #000000; font-weight: 600;">{segundo['Comercial']}</h3>
                <p style="margin: 8px 0; font-size: 24px; font-weight: 700; color: #000000;">{segundo['Importe Aceptado']:,.0f} €</p>
                <p style="margin: 0; color: #424242;">Tasa: {segundo['Tasa Conversion']:.1f}%</p>
                <p style="margin: 0; color: #424242;">{segundo['Aceptados']:,} aceptados</p>
            </div>
            """, unsafe_allow_html=True)

        # Primer lugar - DAVID Brand
        with col2:
            primero = comerciales_stats.iloc[0]
            st.markdown(f"""
            <div style="text-align: center; padding: 28px; background: #000000; border-radius: 8px;">
                <h1 style="margin: 0; font-size: 48px;">🥇</h1>
                <h2 style="margin: 8px 0; color: #FFFFFF; font-weight: 600;">{primero['Comercial']}</h2>
                <p style="margin: 8px 0; font-size: 28px; font-weight: 700; color: #FFFFFF;">{primero['Importe Aceptado']:,.0f} €</p>
                <p style="margin: 0; font-size: 14px; color: rgba(255,255,255,0.7);">Tasa: {primero['Tasa Conversion']:.1f}%</p>
                <p style="margin: 0; color: #F15025;">{primero['Aceptados']:,} aceptados</p>
            </div>
            """, unsafe_allow_html=True)

        # Tercer lugar - DAVID Brand
        with col3:
            tercero = comerciales_stats.iloc[2]
            st.markdown(f"""
            <div style="text-align: center; padding: 24px; background: #FFFFFF; border-radius: 8px; margin-top: 50px; border: 1px solid #E0E0E0;">
                <h1 style="margin: 0;">🥉</h1>
                <h3 style="margin: 8px 0; color: #000000; font-weight: 600;">{tercero['Comercial']}</h3>
                <p style="margin: 8px 0; font-size: 24px; font-weight: 700; color: #000000;">{tercero['Importe Aceptado']:,.0f} €</p>
                <p style="margin: 0; color: #424242;">Tasa: {tercero['Tasa Conversion']:.1f}%</p>
                <p style="margin: 0; color: #424242;">{tercero['Aceptados']:,} aceptados</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

    # ========== GRÁFICOS COMPARATIVOS ==========
    st.subheader("Comparativa de Comerciales")

    col1, col2 = st.columns(2)

    with col1:
        # Gráfico de importe facturado
        fig = px.bar(
            comerciales_stats,
            x='Comercial',
            y='Importe Aceptado',
            color='Importe Aceptado',
            color_continuous_scale='Greens',
            title="Importe Facturado (EUR)",
            text='Importe Aceptado'
        )
        fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Gráfico de tasa de conversión
        fig = px.bar(
            comerciales_stats,
            x='Comercial',
            y='Tasa Conversion',
            color='Tasa Conversion',
            color_continuous_scale='RdYlGn',
            title="Tasa de Conversion (%)",
            text='Tasa Conversion'
        )
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.add_hline(y=tasa_global, line_dash="dash", line_color="red",
                      annotation_text=f"Media: {tasa_global:.1f}%")
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        # Volumen de presupuestos
        fig = px.bar(
            comerciales_stats,
            x='Comercial',
            y=['Presupuestos', 'Aceptados'],
            barmode='group',
            title="Presupuestos vs Aceptados",
            color_discrete_map={'Presupuestos': '#E0E0E0', 'Aceptados': '#000000'}  # DAVID Brand
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Ticket medio
        fig = px.bar(
            comerciales_stats,
            x='Comercial',
            y='Ticket Medio',
            color='Ticket Medio',
            color_continuous_scale='Blues',
            title="Ticket Medio (EUR)",
            text='Ticket Medio'
        )
        fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ========== TABLA RANKING COMPLETA ==========
    st.subheader("Ranking Completo")

    tabla_ranking = comerciales_stats[['Ranking', 'Comercial', 'Presupuestos', 'Aceptados',
                                        'Tasa Conversion', 'Importe Aceptado', 'Ticket Medio']].copy()

    # Formatear columnas para mostrar
    tabla_ranking['Tasa Conversion'] = tabla_ranking['Tasa Conversion'].apply(lambda x: f"{x:.1f}%")
    tabla_ranking['Importe Aceptado'] = tabla_ranking['Importe Aceptado'].apply(lambda x: f"{x:,.0f} EUR")
    tabla_ranking['Ticket Medio'] = tabla_ranking['Ticket Medio'].apply(lambda x: f"{x:,.0f} EUR")

    st.dataframe(
        tabla_ranking,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    # ========== EVOLUCIÓN MENSUAL ==========
    st.subheader("Evolucion Mensual")

    df_mensual = df_conv[df_conv['Fecha alta'].notna()].copy()
    df_mensual['Mes'] = df_mensual['Fecha alta'].dt.to_period('M').astype(str)

    # Presupuestos únicos por mes y comercial
    presup_mensual = df_mensual.groupby(['Mes', 'Atendido por'])['Cod. Presupuesto'].nunique().reset_index()
    presup_mensual.columns = ['Mes', 'Comercial', 'Presupuestos']

    # Presupuestos aceptados únicos por mes y comercial
    df_mensual_aceptados = df_mensual[df_mensual['Estado presupuesto'].isin(['A', 'AP'])]
    acept_mensual = df_mensual_aceptados.groupby(['Mes', 'Atendido por'])['Cod. Presupuesto'].nunique().reset_index()
    acept_mensual.columns = ['Mes', 'Comercial', 'Aceptados']

    # Combinar
    evolucion = presup_mensual.merge(acept_mensual, on=['Mes', 'Comercial'], how='left')
    evolucion['Aceptados'] = evolucion['Aceptados'].fillna(0).astype(int)
    evolucion['Mes_ES'] = evolucion['Mes'].apply(formato_mes_es)

    # Calcular importe por mes y comercial (suma de líneas aceptadas)
    importe_mensual = df_mensual_aceptados.groupby(['Mes', 'Atendido por'])['Total importe'].sum().reset_index()
    importe_mensual.columns = ['Mes', 'Comercial', 'Importe']

    evolucion = evolucion.merge(importe_mensual, on=['Mes', 'Comercial'], how='left')
    evolucion['Importe'] = evolucion['Importe'].fillna(0)

    fig = px.line(
        evolucion,
        x='Mes_ES',
        y='Importe',
        color='Comercial',
        markers=True,
        title="Evolucion del Importe Facturado por Comercial"
    )
    fig.update_layout(height=400, xaxis_title="Mes", yaxis_title="Importe (EUR)")
    st.plotly_chart(fig, use_container_width=True)

    # Exportar ranking
    csv = comerciales_stats.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Exportar ranking",
        csv,
        "ranking_comerciales.csv",
        "text/csv"
    )

    st.markdown("---")

    # ========== TABLA DE DATOS FILTRADOS ==========
    st.subheader("Datos del Filtro Aplicado")

    # Agrupar por Cod. Presupuesto (cada presupuesto es una unidad)
    df_agrupado = df_conv.groupby('Cod. Presupuesto').agg({
        'Fecha alta': 'first',
        'Cliente': 'first',
        'Tipo Servicio': lambda x: ' | '.join(x.dropna().unique()[:3]),
        'Estado presupuesto': 'first',
        'Total importe': 'sum',
        'Atendido por': 'first',
        'Grupo de clientes': 'first'
    }).reset_index()

    df_tabla = df_agrupado.copy()

    # Formatear fecha
    if 'Fecha alta' in df_tabla.columns:
        df_tabla['Fecha alta'] = pd.to_datetime(df_tabla['Fecha alta']).dt.strftime('%d/%m/%Y')

    # Formatear importe
    if 'Total importe' in df_tabla.columns:
        df_tabla['Total importe'] = df_tabla['Total importe'].apply(lambda x: f"{x:,.2f} €" if pd.notna(x) else "-")

    # Mapear estados
    estados_map = {'A': 'Aceptado', 'AP': 'Aceptado Parcial', 'P': 'Pendiente', 'R': 'Rechazado', 'C': 'Cancelado', 'E': 'Enviado', 'V': 'Valorado'}
    if 'Estado presupuesto' in df_tabla.columns:
        df_tabla['Estado presupuesto'] = df_tabla['Estado presupuesto'].map(estados_map).fillna(df_tabla['Estado presupuesto'])

    # Mapear tipos de servicio a descripción
    if 'Tipo Servicio' in df_tabla.columns:
        def get_tipos_desc(tipos_str):
            if pd.isna(tipos_str):
                return tipos_str
            partes = tipos_str.split(' | ')
            descripciones = []
            for codigo in partes:
                desc = tipos_guardados.get(codigo.strip(), {}).get('descripcion', '')
                descripciones.append(normalizar_texto(desc) if desc else codigo.strip())
            return ' | '.join(descripciones)
        df_tabla['Tipo Servicio'] = df_tabla['Tipo Servicio'].apply(get_tipos_desc)

    # Mostrar resumen
    total_presupuestos_unicos = len(df_agrupado)
    filtros_activos = []
    if tipo_sel_conv != 'Todos':
        filtros_activos.append(f"Tipo: {tipo_sel_conv}")
    if grupo_sel_conv != 'Todos':
        filtros_activos.append(f"Grupo: {grupo_sel_conv}")
    if fuente_sel != 'Todos':
        filtros_activos.append(f"Fuente: {fuente_sel}")

    filtros_texto = " | ".join(filtros_activos) if filtros_activos else "Sin filtros adicionales"

    st.markdown(f"""
    <div style="background:#f8f9fa;padding:12px 16px;border-radius:8px;margin-bottom:16px;border-left:4px solid #F15025;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <span style="font-size:14px;color:#666;">Periodo: <strong>{fecha_desde.strftime('%d/%m/%Y')} - {fecha_hasta.strftime('%d/%m/%Y')}</strong></span>
                <span style="margin-left:16px;font-size:13px;color:#888;">{filtros_texto}</span>
            </div>
            <div style="text-align:right;">
                <div style="font-size:18px;font-weight:600;color:#333;">{total_presupuestos_unicos} presupuestos</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Tabla con datos agrupados por presupuesto
    st.dataframe(
        df_tabla.sort_values('Fecha alta', ascending=False) if 'Fecha alta' in df_tabla.columns else df_tabla,
        use_container_width=True,
        hide_index=True,
        height=400
    )

    # Exportar datos filtrados (agrupados por presupuesto)
    csv_datos = df_agrupado.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Exportar datos filtrados",
        csv_datos,
        "datos_conversion.csv",
        "text/csv",
        key="export_datos_conv"
    )


# ============================================
# PÁGINA 7: INCENTIVOS
# ============================================
elif pagina == "Incentivos":
    st.title("Sistema de Incentivos")
    st.markdown("Configura y calcula los incentivos para el equipo comercial")

    # Panel de ayuda
    with st.expander("Como funciona el Sistema de Incentivos", expanded=False):
        st.markdown("""
        ## 💰 Sistema de Incentivos - Guia Completa

        El sistema tiene **DOBLE COMISION** (mensual + cuatrimestral) para maximizar tu motivacion!

        ---

        ### 📅 COMISION MENSUAL (Cobras cada mes!)

        **0.5% de TODA tu facturacion del mes** - Sin minimos, sin condiciones!

        | Facturacion Mensual | Comision Inmediata |
        |---------------------|-------------------|
        | 20.000 EUR | 100 EUR |
        | 50.000 EUR | 250 EUR |
        | 80.000 EUR | 400 EUR |
        | 100.000 EUR | 500 EUR |

        **Ejemplo:** Si facturas 60.000€ en marzo → Comision mensual = **300€**

        ---

        ### 📊 COMISION CUATRIMESTRAL (Bonus por superar tus objetivos!)

        Las comisiones cuatrimestrales se aplican sobre la facturacion que **SUPERA tu minimo**.
        Tu minimo = lo que facturaste en el mismo cuatrimestre del año anterior.

        | Cuatrimestre | Meses |
        |--------------|-------|
        | 1er Cuatrimestre | Enero - Abril |
        | 2do Cuatrimestre | Mayo - Agosto |
        | 3er Cuatrimestre | Septiembre - Diciembre |

        **Tramos sobre facturacion que supera el minimo:**
        | Exceso sobre minimo | Comision Extra |
        |---------------------|----------------|
        | 0 - 30.000 EUR | 0.3% |
        | 30.001 - 60.000 EUR | 0.5% |
        | 60.001 - 100.000 EUR | 0.7% |
        | +100.000 EUR | 1.0% |

        **Ejemplo:**
        - Tu minimo (1er C 2024): 180.000€
        - Tu facturacion (1er C 2025): 250.000€
        - Exceso: 70.000€ → Comision cuatrimestral = 70.000 × 0.7% = **490€**

        ---

        ### 🎁 BONUS MENSUALES (Automaticos!)

        Se calculan automaticamente cada mes:

        | Bonus | Condicion | Importe |
        |-------|-----------|---------|
        | 🚀 Crecimiento +20% | Superar mes anterior en +20% | 100 EUR |
        | 📈 Crecimiento +10% | Superar mes anterior en +10% | 50 EUR |
        | 🎯 +15 ventas | Cerrar 15+ presupuestos en el mes | 75 EUR |
        | ✓ +10 ventas | Cerrar 10+ presupuestos en el mes | 40 EUR |

        ---

        ### 🏆 LOGROS (Badges que desbloqueas!)

        | Logro | Condicion |
        |-------|-----------|
        | 🔥 En Racha! | 15+ dias con ventas en el mes |
        | 💎 Club 50K | Facturar 50.000€+ en el mes |
        | 👑 Club 100K | Facturar 100.000€+ en el mes |
        | 🎯 Precision 50% | Tasa de conversion >= 50% |
        | ⚡ Supervendedor | 20+ ventas en el mes |

        ---

        ### 📊 BARRAS DE PROGRESO

        El sistema muestra visualmente:
        - **Ranking mensual** con medallas 🥇🥈🥉
        - **Progreso hacia el minimo cuatrimestral**
        - **Comparativa vs mes anterior** (verde = mejoras, rojo = bajas)
        - **Evolucion vs mismo mes año anterior**
        - **Proximo objetivo** a alcanzar

        ---

        ### 💰 EJEMPLO COMPLETO

        **Comercial:** Ana Serrano | **Mes:** Marzo 2025

        | Concepto | Valor |
        |----------|-------|
        | Facturacion Marzo | 65.000 EUR |
        | Facturacion Febrero | 55.000 EUR |
        | Ventas cerradas | 18 |

        **Incentivos del mes:**
        - **Comision mensual:** 65.000 × 0.5% = **325€**
        - **Bonus crecimiento:** +18% vs feb = **50€**
        - **Bonus +15 ventas:** = **75€**
        - **TOTAL MES = 450€**

        **Ademas:**
        - Logros: 💎 Club 50K, ⚡ Supervendedor
        - Puntos: 18 × 2 = 36 pts

        ---

        ### 🎮 COMO FUNCIONA

        1. Selecciona el **mes y año** en la calculadora
        2. El sistema muestra automaticamente el **cuatrimestre** correspondiente
        3. Ves tu **ranking** respecto a tus compañeros
        4. Las **barras de progreso** te muestran:
           - Cuanto te falta para superar el minimo cuatrimestral
           - Cuanto llevas vs tu objetivo mensual
        5. Los **logros** aparecen automaticamente cuando los desbloqueas

        ---

        *¡Vende mas, gana mas! El sistema te recompensa por TODA tu facturacion mensual,
        y te da bonus extra cuando superas tus propios records.*
        """)

    st.markdown("---")

    # Tabs principales
    tab_calc, tab_premios_esp, tab_comisiones, tab_bonus, tab_puntos, tab_historico = st.tabs([
        "Calculadora", "Premios Especiales", "Comisiones", "Bonus Objetivos", "Sistema Puntos", "Historico"
    ])

    # ========== TAB PREMIOS ESPECIALES ==========
    with tab_premios_esp:
        st.subheader("Premios Especiales por Presupuesto")
        st.markdown("Asigna premios especiales a presupuestos estrategicos. El comercial que lo consiga recibira el premio adicional.")

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("### Crear Nuevo Premio")

            # Selector de presupuesto pendiente
            presupuestos_pendientes = df[df['Estado'].isin(['AP', 'E'])].copy()
            if len(presupuestos_pendientes) > 0:
                presupuestos_pendientes['label'] = presupuestos_pendientes.apply(
                    lambda x: f"{x['Cod Presupuesto']} - {x['Cliente'][:30]}... ({x['Importe']:,.0f}€)", axis=1
                )
                opciones_pres = presupuestos_pendientes['label'].tolist()

                pres_seleccionado = st.selectbox(
                    "Seleccionar Presupuesto",
                    options=[""] + opciones_pres,
                    help="Elige un presupuesto pendiente para asignarle un premio especial"
                )

                if pres_seleccionado:
                    cod_pres = pres_seleccionado.split(" - ")[0]
                    premio_desc = st.text_input("Descripcion del premio", placeholder="Ej: Cliente estrategico, Cierre importante...")
                    premio_importe = st.number_input("Importe del premio (EUR)", min_value=0.0, value=100.0, step=25.0)

                    comerciales = df['Atendido por'].dropna().unique().tolist()
                    comercial_asig = st.selectbox("Comercial asignado (opcional)", ["Todos"] + comerciales)

                    if st.button("Guardar Premio Especial", type="primary"):
                        if premio_desc and premio_importe > 0:
                            guardar_premio_presupuesto(
                                cod_pres,
                                premio_desc,
                                premio_importe,
                                comercial_asig if comercial_asig != "Todos" else None
                            )
                            st.success(f"Premio de {premio_importe:.0f}€ asignado al presupuesto {cod_pres}")
                            st.rerun()
                        else:
                            st.error("Completa la descripcion y el importe")
            else:
                st.info("No hay presupuestos pendientes (AP/E) para asignar premios")

        with col2:
            st.markdown("### Premios Activos")

            premios_activos = obtener_premios_presupuesto(solo_activos=True)

            if premios_activos:
                for premio in premios_activos:
                    # Verificar estado del presupuesto
                    pres_info = df[df['Cod Presupuesto'] == premio['cod_presupuesto']]
                    estado_actual = pres_info['Estado'].values[0] if len(pres_info) > 0 else "?"

                    if premio['conseguido']:
                        bg_color = "#E8F5E9"
                        border_color = "#4CAF50"
                        estado_texto = "CONSEGUIDO"
                    elif estado_actual == "A":
                        # Presupuesto aceptado pero premio no marcado como conseguido
                        bg_color = "#FFF8E1"
                        border_color = "#FFC107"
                        estado_texto = "ACEPTADO - Pendiente confirmar"
                    else:
                        bg_color = "#E3F2FD"
                        border_color = "#2196F3"
                        estado_texto = f"Pendiente ({estado_actual})"

                    st.markdown(f"""
                    <div style="background: {bg_color}; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 4px solid {border_color};">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <b style="color: #1565C0; font-size: 16px;">{premio['cod_presupuesto']}</b>
                                <span style="margin-left: 10px; padding: 3px 8px; background: {border_color}; color: white; border-radius: 5px; font-size: 12px;">{estado_texto}</span>
                            </div>
                            <b style="color: #2E7D32; font-size: 20px;">{premio['importe_premio']:.0f}€</b>
                        </div>
                        <p style="color: #424242; margin: 5px 0;">{premio['descripcion']}</p>
                        <small style="color: #757575;">
                            {f"Asignado a: {premio['comercial_asignado']}" if premio['comercial_asignado'] else "Cualquier comercial"}
                            | Creado: {premio['fecha_creacion'][:10] if premio['fecha_creacion'] else 'N/A'}
                        </small>
                    </div>
                    """, unsafe_allow_html=True)

                    col_a, col_b = st.columns(2)
                    with col_a:
                        if not premio['conseguido'] and estado_actual == "A":
                            if st.button(f"Marcar Conseguido", key=f"conseguido_{premio['cod_presupuesto']}"):
                                marcar_premio_conseguido(premio['cod_presupuesto'])
                                st.success("Premio marcado como conseguido!")
                                st.rerun()
                    with col_b:
                        if st.button(f"Eliminar", key=f"eliminar_{premio['cod_presupuesto']}"):
                            eliminar_premio_presupuesto(premio['cod_presupuesto'])
                            st.rerun()
            else:
                st.info("No hay premios especiales activos. Crea uno desde el panel izquierdo.")

        st.markdown("---")

        # Resumen de premios
        st.markdown("### Resumen de Premios")

        todos_premios = obtener_premios_presupuesto(solo_activos=False)
        if todos_premios:
            col1, col2, col3, col4 = st.columns(4)

            premios_pendientes = [p for p in todos_premios if not p['conseguido'] and p['activo']]
            premios_conseguidos = [p for p in todos_premios if p['conseguido']]

            with col1:
                st.metric("Premios Pendientes", len(premios_pendientes))
            with col2:
                st.metric("Premios Conseguidos", len(premios_conseguidos))
            with col3:
                total_pendiente = sum(p['importe_premio'] for p in premios_pendientes)
                st.metric("Importe Pendiente", f"{total_pendiente:,.0f}€")
            with col4:
                total_conseguido = sum(p['importe_premio'] for p in premios_conseguidos)
                st.metric("Importe Pagado", f"{total_conseguido:,.0f}€")

    # ========== TAB COMISIONES ==========
    with tab_comisiones:
        st.subheader("Tramos de Comision por Facturacion")
        st.markdown("Define los porcentajes de comision segun el importe **comisionable** (facturacion que supera el minimo del año anterior)")

        # Mostrar tramos actuales
        tramos = obtener_tramos_comision()

        if tramos:
            st.markdown("**Tramos configurados:**")
            for i, tramo in enumerate(tramos):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"Desde **{tramo['desde']:,.0f} EUR** hasta **{tramo['hasta']:,.0f} EUR**")
                with col2:
                    st.write(f"Comision: **{tramo['porcentaje']}%**")
        else:
            st.info("No hay tramos configurados")

        st.markdown("---")
        st.markdown("**Configurar nuevos tramos:**")

        with st.form("form_tramos"):
            st.markdown("Define los tramos (se eliminaran los anteriores)")

            col1, col2, col3 = st.columns(3)
            with col1:
                t1_hasta = st.number_input("Tramo 1 - Hasta (EUR)", value=50000, step=5000)
                t1_pct = st.number_input("Tramo 1 - Comision %", value=1.0, step=0.1, format="%.1f")

            with col2:
                t2_hasta = st.number_input("Tramo 2 - Hasta (EUR)", value=100000, step=5000)
                t2_pct = st.number_input("Tramo 2 - Comision %", value=1.5, step=0.1, format="%.1f")

            with col3:
                t3_hasta = st.number_input("Tramo 3 - Hasta (EUR)", value=9999999, step=5000)
                t3_pct = st.number_input("Tramo 3 - Comision %", value=2.0, step=0.1, format="%.1f")

            if st.form_submit_button("Guardar Tramos", type="primary"):
                limpiar_tramos_comision()
                guardar_tramo_comision(0, t1_hasta, t1_pct)
                guardar_tramo_comision(t1_hasta + 1, t2_hasta, t2_pct)
                guardar_tramo_comision(t2_hasta + 1, t3_hasta, t3_pct)
                st.success("Tramos guardados correctamente")
                st.rerun()

    # ========== TAB BONUS ==========
    with tab_bonus:
        st.subheader("Bonus por Objetivos")
        st.markdown("Define bonus que se otorgan al cumplir determinados objetivos")

        # Mostrar bonus actuales
        bonus_list = obtener_bonus_objetivos()

        if bonus_list:
            st.markdown("**Bonus configurados:**")
            for bonus in bonus_list:
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"**{bonus['nombre']}**")
                    st.caption(f"{bonus['condicion']} {bonus['valor_objetivo']}")
                with col2:
                    st.write(f"**{bonus['importe_bonus']:,.0f} EUR**")
        else:
            st.info("No hay bonus configurados")

        st.markdown("---")
        st.markdown("**Añadir bonus:**")

        with st.form("form_bonus"):
            col1, col2 = st.columns(2)

            with col1:
                bonus_nombre = st.text_input("Nombre del bonus", placeholder="Ej: Super Vendedor")
                bonus_tipo = st.selectbox("Tipo de metrica", [
                    "facturacion", "tasa_conversion", "num_aceptados",
                    "cliente_nuevo", "cliente_recuperado", "top_mes"
                ])
                bonus_condicion = st.selectbox("Condicion", [
                    "mayor_que", "mayor_igual", "igual", "es_top"
                ])

            with col2:
                bonus_valor = st.number_input("Valor objetivo", value=0.0, step=100.0)
                bonus_importe = st.number_input("Importe del bonus (EUR)", value=200.0, step=50.0)

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Añadir Bonus", type="primary"):
                    if bonus_nombre:
                        guardar_bonus(bonus_nombre, bonus_tipo, bonus_condicion, bonus_valor, bonus_importe)
                        st.success(f"Bonus '{bonus_nombre}' añadido")
                        st.rerun()
            with col2:
                if st.form_submit_button("Limpiar Todos"):
                    limpiar_bonus()
                    st.rerun()

        # Bonus predefinidos rapidos
        st.markdown("---")
        st.markdown("**Bonus rapidos predefinidos:**")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("+ Superar media conversion"):
                guardar_bonus("Superar Media Conversion", "tasa_conversion", "mayor_que", 0, 150)
                st.rerun()
        with col2:
            if st.button("+ Top 1 Facturacion"):
                guardar_bonus("Top 1 Facturacion Mes", "top_mes", "es_top", 1, 300)
                st.rerun()
        with col3:
            if st.button("+ Cliente Recuperado"):
                guardar_bonus("Recuperar Cliente Inactivo", "cliente_recuperado", "igual", 1, 50)
                st.rerun()

    # ========== TAB PUNTOS ==========
    with tab_puntos:
        st.subheader("Sistema de Puntos")
        st.markdown("Define puntos por acciones que luego se canjean por premios")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Puntos por Accion:**")

            acciones = obtener_puntos_acciones()
            if acciones:
                for accion in acciones:
                    st.write(f"- {accion['accion']} ({accion['tipo_servicio']}): **{accion['puntos']} pts**")
            else:
                st.info("No hay acciones configuradas")

            st.markdown("---")

            with st.form("form_puntos"):
                accion_nombre = st.selectbox("Accion", [
                    "presupuesto_aceptado", "cliente_nuevo", "cliente_recuperado",
                    "venta_cruzada", "objetivo_mensual"
                ])

                # Obtener tipos de servicio
                tipos_guardados = obtener_tipos_servicio_db()
                tipos_opciones = ["Todos"] + list(set([
                    normalizar_texto(v.get('descripcion', k)) for k, v in tipos_guardados.items() if v.get('descripcion')
                ]))
                tipo_serv = st.selectbox("Tipo de servicio", tipos_opciones)

                puntos_valor = st.number_input("Puntos", value=1, min_value=1, step=1)
                puntos_desc = st.text_input("Descripcion", placeholder="Descripcion opcional")

                col_a, col_b = st.columns(2)
                with col_a:
                    if st.form_submit_button("Añadir Accion"):
                        guardar_puntos_accion(accion_nombre, tipo_serv, puntos_valor, puntos_desc)
                        st.rerun()
                with col_b:
                    if st.form_submit_button("Limpiar"):
                        limpiar_puntos_acciones()
                        st.rerun()

            # Acciones rapidas
            st.markdown("**Configuracion rapida:**")
            if st.button("Cargar puntos por defecto"):
                limpiar_puntos_acciones()
                guardar_puntos_accion("presupuesto_aceptado", "Todos", 1, "Por cada presupuesto aceptado")
                guardar_puntos_accion("presupuesto_aceptado", "Bodas", 5, "Bodas valen mas")
                guardar_puntos_accion("presupuesto_aceptado", "Circuitos", 4, "Circuitos valen mas")
                guardar_puntos_accion("cliente_nuevo", "Todos", 3, "Cliente nuevo que acepta")
                guardar_puntos_accion("cliente_recuperado", "Todos", 10, "Recuperar cliente inactivo")
                st.success("Puntos por defecto cargados")
                st.rerun()

        with col2:
            st.markdown("**Premios Canjeables:**")

            premios = obtener_premios()
            if premios:
                for premio in premios:
                    st.write(f"- **{premio['nombre']}**: {premio['puntos_requeridos']} pts")
                    if premio['descripcion']:
                        st.caption(premio['descripcion'])
            else:
                st.info("No hay premios configurados")

            st.markdown("---")

            with st.form("form_premios"):
                premio_nombre = st.text_input("Nombre del premio")
                premio_puntos = st.number_input("Puntos necesarios", value=50, min_value=1, step=10)
                premio_desc = st.text_input("Descripcion del premio")

                col_a, col_b = st.columns(2)
                with col_a:
                    if st.form_submit_button("Añadir Premio"):
                        if premio_nombre:
                            guardar_premio(premio_nombre, premio_puntos, premio_desc)
                            st.rerun()
                with col_b:
                    if st.form_submit_button("Limpiar"):
                        limpiar_premios()
                        st.rerun()

            # Premios rapidos
            st.markdown("**Premios rapidos:**")
            if st.button("Cargar premios ejemplo"):
                limpiar_premios()
                guardar_premio("Dia libre", 100, "Un dia libre a elegir")
                guardar_premio("Cena para 2", 75, "Cena en restaurante")
                guardar_premio("Tarjeta regalo 50 EUR", 50, "Amazon, El Corte Ingles...")
                guardar_premio("Parking gratis 1 mes", 30, "Plaza de parking")
                st.success("Premios ejemplo cargados")
                st.rerun()

    # ========== TAB CALCULADORA ==========
    with tab_calc:
        # Header motivacional - DAVID Brand
        st.markdown("""
        <div style="background: #000000; padding: 24px 32px; border-radius: 8px; margin-bottom: 24px; text-align: center;">
            <h1 style="color: #FFFFFF; margin: 0; font-weight: 600;">💰 Centro de Incentivos</h1>
            <p style="color: rgba(255,255,255,0.7); margin: 8px 0 0 0; font-size: 14px;">Comisiones Mensuales + Cuatrimestrales | Bonus | Puntos | Logros</p>
        </div>
        """, unsafe_allow_html=True)

        # Selector de periodo
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

        with col1:
            años_disponibles = sorted(df['Fecha alta'].dt.year.dropna().unique().astype(int).tolist(), reverse=True)
            año_calc = st.selectbox("Año", años_disponibles, key="año_calc")

        with col2:
            meses_nombres = {
                1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
                5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
                9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
            }
            mes_calc = st.selectbox("Mes", list(meses_nombres.keys()),
                                   format_func=lambda x: meses_nombres[x], key="mes_calc")

        with col3:
            # Determinar cuatrimestre automaticamente
            if mes_calc <= 4:
                cuatri_actual = "1er Cuatrimestre"
                mes_inicio_cuatri, mes_fin_cuatri = 1, 4
            elif mes_calc <= 8:
                cuatri_actual = "2do Cuatrimestre"
                mes_inicio_cuatri, mes_fin_cuatri = 5, 8
            else:
                cuatri_actual = "3er Cuatrimestre"
                mes_inicio_cuatri, mes_fin_cuatri = 9, 12
            st.info(f"📅 {cuatri_actual}")

        with col4:
            comerciales_lista = ['📊 Vista General'] + sorted(df['Atendido por'].dropna().unique().tolist())
            comercial_filtro = st.selectbox("Comercial", comerciales_lista, key="comercial_filtro")

        # Obtener configuracion
        tramos = obtener_tramos_comision()
        bonus_list = obtener_bonus_objetivos()
        acciones = obtener_puntos_acciones()

        # ========== CALCULOS ==========
        # Datos del mes seleccionado
        df_mes = df[(df['Fecha alta'].dt.year == año_calc) &
                    (df['Fecha alta'].dt.month == mes_calc)].copy()

        # Datos del cuatrimestre
        df_cuatri = df[(df['Fecha alta'].dt.year == año_calc) &
                       (df['Fecha alta'].dt.month >= mes_inicio_cuatri) &
                       (df['Fecha alta'].dt.month <= mes_fin_cuatri)].copy()

        # Datos del año anterior (mismo cuatrimestre) para minimo
        año_anterior = año_calc - 1
        df_cuatri_anterior = df[(df['Fecha alta'].dt.year == año_anterior) &
                                (df['Fecha alta'].dt.month >= mes_inicio_cuatri) &
                                (df['Fecha alta'].dt.month <= mes_fin_cuatri)].copy()

        # Datos del mes anterior para comparativa
        if mes_calc == 1:
            mes_anterior, año_mes_anterior = 12, año_calc - 1
        else:
            mes_anterior, año_mes_anterior = mes_calc - 1, año_calc

        df_mes_anterior = df[(df['Fecha alta'].dt.year == año_mes_anterior) &
                             (df['Fecha alta'].dt.month == mes_anterior)].copy()

        # Facturacion minima cuatrimestral (año anterior)
        fact_cuatri_anterior = df_cuatri_anterior[df_cuatri_anterior['Estado presupuesto'].isin(['A', 'AP'])].groupby('Atendido por')['Total importe'].sum().to_dict()

        # Calcular datos por comercial
        comerciales_data = []

        for comercial in df['Atendido por'].dropna().unique():
            # Datos mensuales (contando presupuestos únicos)
            df_com_mes = df_mes[df_mes['Atendido por'] == comercial]
            df_aceptados_mes = df_com_mes[df_com_mes['Estado presupuesto'].isin(['A', 'AP'])]
            fact_mes = df_aceptados_mes['Total importe'].sum()
            num_pres_mes = df_com_mes['Cod. Presupuesto'].nunique()
            num_acept_mes = df_aceptados_mes['Cod. Presupuesto'].nunique()
            tasa_conv_mes = (num_acept_mes / num_pres_mes * 100) if num_pres_mes > 0 else 0

            # Datos mes anterior (para comparativa)
            df_com_mes_ant = df_mes_anterior[df_mes_anterior['Atendido por'] == comercial]
            df_acept_mes_ant = df_com_mes_ant[df_com_mes_ant['Estado presupuesto'].isin(['A', 'AP'])]
            fact_mes_anterior = df_acept_mes_ant['Total importe'].sum()

            # Datos cuatrimestrales (contando presupuestos únicos)
            df_com_cuatri = df_cuatri[df_cuatri['Atendido por'] == comercial]
            df_aceptados_cuatri = df_com_cuatri[df_com_cuatri['Estado presupuesto'].isin(['A', 'AP'])]
            fact_cuatri = df_aceptados_cuatri['Total importe'].sum()
            num_pres_cuatri = df_com_cuatri['Cod. Presupuesto'].nunique()
            num_acept_cuatri = df_aceptados_cuatri['Cod. Presupuesto'].nunique()

            # Minimo cuatrimestral
            minimo_cuatri = fact_cuatri_anterior.get(comercial, 0)
            fact_comisionable_cuatri = max(0, fact_cuatri - minimo_cuatri)
            progreso_minimo = min(100, (fact_cuatri / minimo_cuatri * 100)) if minimo_cuatri > 0 else 100
            ha_superado_minimo = fact_cuatri >= minimo_cuatri

            # ========== COMISION MENSUAL ==========
            # Comision mensual: 0.5% de toda la facturacion del mes (incentivo inmediato)
            comision_mensual = fact_mes * 0.005  # 0.5% fijo mensual

            # ========== COMISION CUATRIMESTRAL ==========
            # Solo sobre lo que supera el minimo, con tramos
            comision_cuatri = 0
            if ha_superado_minimo and fact_comisionable_cuatri > 0:
                for tramo in tramos:
                    if tramo['desde'] <= fact_comisionable_cuatri <= tramo['hasta']:
                        comision_cuatri = fact_comisionable_cuatri * (tramo['porcentaje'] / 100)
                        break
                    elif fact_comisionable_cuatri > tramo['hasta']:
                        comision_cuatri = fact_comisionable_cuatri * (tramo['porcentaje'] / 100)

            # ========== BONUS MENSUALES ==========
            bonus_mes = 0
            bonus_detalle_mes = []

            # Bonus por superar mes anterior
            if fact_mes > fact_mes_anterior and fact_mes_anterior > 0:
                incremento = ((fact_mes - fact_mes_anterior) / fact_mes_anterior) * 100
                if incremento >= 20:
                    bonus_mes += 100
                    bonus_detalle_mes.append(f"🚀 Crecimiento +{incremento:.0f}%")
                elif incremento >= 10:
                    bonus_mes += 50
                    bonus_detalle_mes.append(f"📈 Crecimiento +{incremento:.0f}%")

            # Bonus por numero de ventas en el mes
            if num_acept_mes >= 15:
                bonus_mes += 75
                bonus_detalle_mes.append("🎯 +15 ventas")
            elif num_acept_mes >= 10:
                bonus_mes += 40
                bonus_detalle_mes.append("✓ +10 ventas")

            # ========== BONUS CUATRIMESTRALES ==========
            bonus_cuatri = 0
            bonus_detalle_cuatri = []

            for bonus in bonus_list:
                cumple = False
                if bonus['tipo'] == 'facturacion':
                    if bonus['condicion'] == 'mayor_que' and fact_cuatri > bonus['valor_objetivo']:
                        cumple = True
                    elif bonus['condicion'] == 'mayor_igual' and fact_cuatri >= bonus['valor_objetivo']:
                        cumple = True
                elif bonus['tipo'] == 'num_aceptados':
                    if bonus['condicion'] == 'mayor_igual' and num_acept_cuatri >= bonus['valor_objetivo']:
                        cumple = True

                if cumple:
                    bonus_cuatri += bonus['importe_bonus']
                    bonus_detalle_cuatri.append(bonus['nombre'])

            # ========== PUNTOS ==========
            puntos_mes = num_acept_mes * 2  # 2 puntos por venta

            # ========== CALCULAR LOGROS ==========
            logros = []
            # Racha (simplificado - ventas consecutivas en dias diferentes)
            dias_con_ventas = df_aceptados_mes['Fecha alta'].dt.date.nunique() if not df_aceptados_mes.empty else 0
            if dias_con_ventas >= 15:
                logros.append("🔥 En Racha!")
            if fact_mes >= 50000:
                logros.append("💎 Club 50K")
            if fact_mes >= 100000:
                logros.append("👑 Club 100K")
            if tasa_conv_mes >= 50:
                logros.append("🎯 Precision 50%")
            if num_acept_mes >= 20:
                logros.append("⚡ Supervendedor")

            # Crecimiento vs año anterior mismo mes
            df_mismo_mes_anterior = df[(df['Fecha alta'].dt.year == año_anterior) &
                                       (df['Fecha alta'].dt.month == mes_calc) &
                                       (df['Atendido por'] == comercial)]
            fact_mismo_mes_anterior = df_mismo_mes_anterior[df_mismo_mes_anterior['Estado presupuesto'].isin(['A', 'AP'])]['Total importe'].sum()
            crecimiento_anual = ((fact_mes - fact_mismo_mes_anterior) / fact_mismo_mes_anterior * 100) if fact_mismo_mes_anterior > 0 else 0

            comerciales_data.append({
                'Comercial': comercial,
                # Mensual
                'Fact_Mes': fact_mes,
                'Fact_Mes_Anterior': fact_mes_anterior,
                'Pres_Mes': num_pres_mes,
                'Acept_Mes': num_acept_mes,
                'Tasa_Conv_Mes': tasa_conv_mes,
                'Comision_Mensual': comision_mensual,
                'Bonus_Mes': bonus_mes,
                'Bonus_Detalle_Mes': bonus_detalle_mes,
                # Cuatrimestral
                'Fact_Cuatri': fact_cuatri,
                'Minimo_Cuatri': minimo_cuatri,
                'Fact_Comisionable': fact_comisionable_cuatri,
                'Progreso_Minimo': progreso_minimo,
                'Ha_Superado': ha_superado_minimo,
                'Comision_Cuatri': comision_cuatri,
                'Bonus_Cuatri': bonus_cuatri,
                'Bonus_Detalle_Cuatri': bonus_detalle_cuatri,
                # Totales
                'Total_Mes': comision_mensual + bonus_mes,
                'Total_Cuatri_Acum': comision_cuatri + bonus_cuatri,
                'Puntos_Mes': puntos_mes,
                'Logros': logros,
                'Crecimiento_Anual': crecimiento_anual,
                'Fact_Mismo_Mes_Anterior': fact_mismo_mes_anterior
            })

        df_incentivos = pd.DataFrame(comerciales_data)
        if not df_incentivos.empty:
            df_incentivos = df_incentivos.sort_values('Total_Mes', ascending=False).reset_index(drop=True)

        periodo_str = f"{meses_nombres[mes_calc]} {año_calc}"

        # ========== MOSTRAR RESULTADOS ==========
        if not df_incentivos.empty and len(df_incentivos) > 0:

            # ========== VISTA INDIVIDUAL DE COMERCIAL ==========
            if comercial_filtro != '📊 Vista General':
                comercial_data = df_incentivos[df_incentivos['Comercial'] == comercial_filtro]

                if not comercial_data.empty:
                    c = comercial_data.iloc[0]
                    posicion = df_incentivos.index[df_incentivos['Comercial'] == comercial_filtro].tolist()[0] + 1

                    # ===== HEADER CON POSICION - DAVID Brand =====
                    medalla = "🥇" if posicion == 1 else ("🥈" if posicion == 2 else ("🥉" if posicion == 3 else f"#{posicion}"))
                    st.markdown(f"""
                    <div style="background: #000000; padding: 28px 32px; border-radius: 8px; margin-bottom: 24px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <h1 style="color: #FFFFFF; margin: 0; font-weight: 600;">{comercial_filtro}</h1>
                                <p style="color: rgba(255,255,255,0.7); margin: 8px 0 0 0;">{periodo_str} | {cuatri_actual}</p>
                            </div>
                            <div style="text-align: right;">
                                <span style="font-size: 48px;">{medalla}</span>
                                <p style="color: #F15025; margin: 0; font-weight: 600;">Ranking Mensual</p>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # ===== LOGROS DESBLOQUEADOS - DAVID Brand =====
                    if c['Logros']:
                        st.markdown(f"""
                        <div style="background: #FFFFFF; padding: 16px 20px; border-radius: 8px; margin-bottom: 16px; border: 1px solid #E0E0E0; border-left: 4px solid #F15025;">
                            <span style="color: #000000; font-size: 16px; font-weight: 600;">🏆 LOGROS: </span>
                            <span style="font-size: 18px;">{' '.join(c['Logros'])}</span>
                        </div>
                        """, unsafe_allow_html=True)

                    # ===== SECCION MENSUAL =====
                    st.markdown("### 📅 INCENTIVOS DEL MES")

                    col1, col2, col3, col4 = st.columns(4)

                    # Facturacion mensual con comparativa - DAVID Brand
                    with col1:
                        delta_mes = c['Fact_Mes'] - c['Fact_Mes_Anterior']
                        delta_pct = (delta_mes / c['Fact_Mes_Anterior'] * 100) if c['Fact_Mes_Anterior'] > 0 else 0
                        color_delta = "#000000" if delta_mes >= 0 else "#F15025"
                        flecha = "▲" if delta_mes >= 0 else "▼"

                        st.markdown(f"""
                        <div style="background: #FFFFFF; padding: 20px; border-radius: 8px; text-align: center; border: 1px solid #E0E0E0;">
                            <p style="color: #424242; margin: 0; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Facturación Mes</p>
                            <p style="color: #000000; margin: 8px 0; font-size: 28px; font-weight: 700;">{c['Fact_Mes']:,.0f}€</p>
                            <p style="color: {color_delta}; margin: 0; font-size: 13px; font-weight: 500;">{flecha} {delta_pct:+.1f}% vs mes ant.</p>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        st.markdown(f"""
                        <div style="background: #FFFFFF; padding: 20px; border-radius: 8px; text-align: center; border: 1px solid #E0E0E0;">
                            <p style="color: #424242; margin: 0; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Comisión Mensual</p>
                            <p style="color: #000000; margin: 8px 0; font-size: 28px; font-weight: 700;">{c['Comision_Mensual']:,.0f}€</p>
                            <p style="color: #424242; margin: 0; font-size: 12px;">0.5% de facturación</p>
                        </div>
                        """, unsafe_allow_html=True)

                    with col3:
                        bonus_txt = ' + '.join(c['Bonus_Detalle_Mes']) if c['Bonus_Detalle_Mes'] else "Sin bonus"
                        st.markdown(f"""
                        <div style="background: #FFFFFF; padding: 20px; border-radius: 8px; text-align: center; border: 1px solid #E0E0E0;">
                            <p style="color: #424242; margin: 0; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Bonus Mes</p>
                            <p style="color: #F15025; margin: 8px 0; font-size: 28px; font-weight: 700;">{c['Bonus_Mes']:,.0f}€</p>
                            <p style="color: #424242; margin: 0; font-size: 11px; max-height: 16px; overflow: hidden;">{bonus_txt[:25]}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    with col4:
                        st.markdown(f"""
                        <div style="background: #000000; padding: 20px; border-radius: 8px; text-align: center;">
                            <p style="color: rgba(255,255,255,0.7); margin: 0; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Total Mes</p>
                            <p style="color: #FFFFFF; margin: 8px 0; font-size: 28px; font-weight: 700;">{c['Total_Mes']:,.0f}€</p>
                            <p style="color: #F15025; margin: 0; font-size: 12px;">{c['Puntos_Mes']} pts</p>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("---")

                    # ===== SECCION CUATRIMESTRAL =====
                    st.markdown(f"### 📊 INCENTIVOS CUATRIMESTRALES ({cuatri_actual})")

                    # Barra de progreso hacia el minimo
                    progreso = c['Progreso_Minimo']
                    if c['Ha_Superado']:
                        bg_prog = "#E8F5E9"
                        border_prog = "#4CAF50"
                        bar_prog = "#4CAF50"
                    elif progreso >= 75:
                        bg_prog = "#FFF3E0"
                        border_prog = "#FF9800"
                        bar_prog = "#FF9800"
                    else:
                        bg_prog = "#FFEBEE"
                        border_prog = "#F44336"
                        bar_prog = "#F44336"

                    st.markdown(f"""
                    <div style="background: {bg_prog}; padding: 20px; border-radius: 12px; margin-bottom: 15px; border: 2px solid {border_prog};">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                            <span style="color: #212121; font-weight: bold;">Progreso hacia Minimo Cuatrimestral</span>
                            <span style="color: {border_prog}; font-weight: bold;">{'✅ SUPERADO - Generando comisiones!' if c['Ha_Superado'] else f'Faltan {c["Minimo_Cuatri"] - c["Fact_Cuatri"]:,.0f}€'}</span>
                        </div>
                        <div style="background: #E0E0E0; border-radius: 15px; height: 35px; overflow: hidden;">
                            <div style="background: {bar_prog}; width: {min(100, progreso)}%; height: 100%; border-radius: 15px; display: flex; align-items: center; justify-content: center;">
                                <span style="color: white; font-weight: bold; font-size: 14px;">{progreso:.0f}%</span>
                            </div>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-top: 10px; color: #424242;">
                            <span>Facturado: <b style="color: #1565C0;">{c['Fact_Cuatri']:,.0f}€</b></span>
                            <span>Minimo (año ant.): <b>{c['Minimo_Cuatri']:,.0f}€</b></span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown(f"""
                        <div style="background: #F3E5F5; padding: 20px; border-radius: 12px; text-align: center; border: 2px solid #9C27B0;">
                            <p style="color: #7B1FA2; margin: 0; font-size: 12px; font-weight: bold;">COMISION CUATRIMESTRAL</p>
                            <p style="color: #4A148C; margin: 5px 0; font-size: 32px; font-weight: bold;">{c['Comision_Cuatri']:,.0f}€</p>
                            <p style="color: #8E24AA; margin: 0; font-size: 12px;">Sobre {c['Fact_Comisionable']:,.0f}€ comisionables</p>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        bonus_cuatri_txt = ', '.join(c['Bonus_Detalle_Cuatri']) if c['Bonus_Detalle_Cuatri'] else "Pendientes"
                        st.markdown(f"""
                        <div style="background: #E8EAF6; padding: 20px; border-radius: 12px; text-align: center; border: 2px solid #3F51B5;">
                            <p style="color: #303F9F; margin: 0; font-size: 12px; font-weight: bold;">BONUS CUATRIMESTRAL</p>
                            <p style="color: #1A237E; margin: 5px 0; font-size: 32px; font-weight: bold;">{c['Bonus_Cuatri']:,.0f}€</p>
                            <p style="color: #3949AB; margin: 0; font-size: 11px;">{bonus_cuatri_txt[:30]}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("---")

                    # ===== COMPARATIVA PERSONAL =====
                    st.markdown("### 📈 TU EVOLUCION")

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        crec = c['Crecimiento_Anual']
                        if crec >= 0:
                            bg_crec = "#E8F5E9"
                            border_crec = "#4CAF50"
                            color_crec = "#2E7D32"
                        else:
                            bg_crec = "#FFEBEE"
                            border_crec = "#F44336"
                            color_crec = "#C62828"
                        st.markdown(f"""
                        <div style="background: {bg_crec}; padding: 20px; border-radius: 12px; text-align: center; border: 2px solid {border_crec};">
                            <p style="color: #424242; margin: 0; font-weight: bold;">vs Mismo Mes Año Anterior</p>
                            <p style="color: {color_crec}; margin: 10px 0; font-size: 36px; font-weight: bold;">{crec:+.1f}%</p>
                            <p style="color: #616161; margin: 0; font-size: 12px;">{c['Fact_Mismo_Mes_Anterior']:,.0f}€ → {c['Fact_Mes']:,.0f}€</p>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        # Proximos objetivos
                        siguiente_objetivo = 50000 if c['Fact_Mes'] < 50000 else (100000 if c['Fact_Mes'] < 100000 else 150000)
                        falta_obj = max(0, siguiente_objetivo - c['Fact_Mes'])
                        prog_obj = min(100, c['Fact_Mes'] / siguiente_objetivo * 100)

                        st.markdown(f"""
                        <div style="background: #FFF8E1; padding: 20px; border-radius: 12px; text-align: center; border: 2px solid #FFC107;">
                            <p style="color: #F57F17; margin: 0; font-weight: bold;">🎯 Proximo Objetivo</p>
                            <p style="color: #E65100; margin: 10px 0; font-size: 24px; font-weight: bold;">{siguiente_objetivo:,.0f}€</p>
                            <div style="background: #E0E0E0; border-radius: 10px; height: 15px; overflow: hidden; margin: 10px 0;">
                                <div style="background: #FFC107; width: {prog_obj}%; height: 100%; border-radius: 10px;"></div>
                            </div>
                            <p style="color: #F57F17; margin: 0; font-size: 12px;">Faltan {falta_obj:,.0f}€</p>
                        </div>
                        """, unsafe_allow_html=True)

                    with col3:
                        tasa_color = "#2E7D32" if c['Tasa_Conv_Mes'] >= 40 else "#E65100"
                        tasa_bg = "#E8F5E9" if c['Tasa_Conv_Mes'] >= 40 else "#FFF3E0"
                        tasa_border = "#4CAF50" if c['Tasa_Conv_Mes'] >= 40 else "#FF9800"
                        st.markdown(f"""
                        <div style="background: {tasa_bg}; padding: 20px; border-radius: 12px; text-align: center; border: 2px solid {tasa_border};">
                            <p style="color: #424242; margin: 0; font-weight: bold;">Tasa de Conversion</p>
                            <p style="color: {tasa_color}; margin: 10px 0; font-size: 36px; font-weight: bold;">{c['Tasa_Conv_Mes']:.1f}%</p>
                            <p style="color: #616161; margin: 0; font-size: 12px;">{c['Acept_Mes']} de {c['Pres_Mes']} presupuestos</p>
                        </div>
                        """, unsafe_allow_html=True)

                    # ===== TOTAL ACUMULADO DESTACADO - DAVID Brand =====
                    st.markdown(f"""
                    <div style="background: #000000; padding: 28px; border-radius: 8px; text-align: center; margin-top: 24px;">
                        <p style="color: rgba(255,255,255,0.7); margin: 0; font-size: 13px; text-transform: uppercase; letter-spacing: 0.1em;">💰 Total Incentivos del Mes</p>
                        <p style="color: #FFFFFF; margin: 12px 0; font-size: 52px; font-weight: 700; letter-spacing: -0.02em;">{c['Total_Mes']:,.0f} €</p>
                        <p style="color: rgba(255,255,255,0.5); margin: 0; font-size: 13px;">Comisión Mensual ({c['Comision_Mensual']:,.0f}€) + Bonus ({c['Bonus_Mes']:,.0f}€)</p>
                    </div>
                    """, unsafe_allow_html=True)

                else:
                    st.warning(f"No hay datos para {comercial_filtro} en este periodo")

            # ========== VISTA GENERAL (TODOS) ==========
            else:
                # KPIs Totales
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    total_fact = df_incentivos['Fact_Mes'].sum()
                    st.metric("💰 Facturacion Total Mes", f"{total_fact:,.0f}€")

                with col2:
                    total_comision_mes = df_incentivos['Comision_Mensual'].sum()
                    st.metric("📅 Comisiones Mensuales", f"{total_comision_mes:,.0f}€")

                with col3:
                    total_bonus_mes = df_incentivos['Bonus_Mes'].sum()
                    st.metric("🎁 Bonus Mensuales", f"{total_bonus_mes:,.0f}€")

                with col4:
                    total_incentivos = df_incentivos['Total_Mes'].sum()
                    st.metric("🏆 TOTAL INCENTIVOS", f"{total_incentivos:,.0f}€")

                st.markdown("---")

                # ===== RANKING CON BARRAS DE PROGRESO =====
                st.markdown(f"### 🏆 RANKING {periodo_str.upper()}")

                for idx, row in df_incentivos.iterrows():
                    pos = idx + 1
                    medalla = "🥇" if pos == 1 else ("🥈" if pos == 2 else ("🥉" if pos == 3 else f"#{pos}"))

                    # Colores claros y legibles
                    if pos == 1:
                        bg_color = "#FFF8E1"  # Amarillo claro
                        border_color = "#FFC107"
                        bar_color = "#FFC107"
                    elif pos == 2:
                        bg_color = "#F5F5F5"  # Gris claro
                        border_color = "#9E9E9E"
                        bar_color = "#9E9E9E"
                    elif pos == 3:
                        bg_color = "#FBE9E7"  # Naranja claro
                        border_color = "#FF7043"
                        bar_color = "#FF7043"
                    else:
                        bg_color = "#FFFFFF"
                        border_color = "#E0E0E0"
                        bar_color = "#2196F3"

                    # Calcular barra de progreso relativa al primero
                    max_fact = df_incentivos['Fact_Mes'].max()
                    progreso_rel = (row['Fact_Mes'] / max_fact * 100) if max_fact > 0 else 0

                    # Delta vs mes anterior
                    delta = row['Fact_Mes'] - row['Fact_Mes_Anterior']
                    delta_color = "#2E7D32" if delta >= 0 else "#C62828"
                    delta_arrow = "▲" if delta >= 0 else "▼"

                    # Logros
                    logros_str = ' '.join(row['Logros']) if row['Logros'] else ""

                    st.markdown(f"""
                    <div style="background: {bg_color}; padding: 18px 22px; border-radius: 12px; margin-bottom: 12px; border-left: 6px solid {border_color}; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="display: flex; align-items: center; gap: 15px;">
                                <span style="font-size: 36px;">{medalla}</span>
                                <div>
                                    <p style="color: #212121; margin: 0; font-size: 20px; font-weight: bold;">{row['Comercial']}</p>
                                    <p style="color: #616161; margin: 4px 0 0 0; font-size: 14px;">{row['Acept_Mes']} ventas | {row['Tasa_Conv_Mes']:.0f}% conversion</p>
                                </div>
                            </div>
                            <div style="text-align: right;">
                                <p style="color: #212121; margin: 0; font-size: 28px; font-weight: bold;">{row['Fact_Mes']:,.0f}€</p>
                                <p style="color: {delta_color}; margin: 4px 0 0 0; font-size: 14px; font-weight: 500;">{delta_arrow} {abs(delta):,.0f}€ vs mes ant.</p>
                            </div>
                        </div>
                        <div style="background: #E0E0E0; border-radius: 8px; height: 14px; margin: 14px 0 10px 0; overflow: hidden;">
                            <div style="background: {bar_color}; width: {progreso_rel}%; height: 100%; border-radius: 8px;"></div>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="color: #424242; font-size: 14px;">💵 <b style="color: #1565C0;">{row['Total_Mes']:,.0f}€</b> incentivo (Com: {row['Comision_Mensual']:,.0f}€ + Bonus: {row['Bonus_Mes']:,.0f}€)</span>
                            <span style="font-size: 18px;">{logros_str}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("---")

                # ===== PROGRESO CUATRIMESTRAL =====
                st.markdown(f"### 📊 PROGRESO CUATRIMESTRAL ({cuatri_actual})")
                st.caption("Las comisiones cuatrimestrales se generan sobre la facturacion que supera el minimo del año anterior")

                for idx, row in df_incentivos.sort_values('Fact_Cuatri', ascending=False).iterrows():
                    progreso = row['Progreso_Minimo']

                    # Colores claros segun progreso
                    if row['Ha_Superado']:
                        bg_color = "#E8F5E9"  # Verde claro
                        border_color = "#4CAF50"
                        bar_color = "#4CAF50"
                        estado = "✅ Generando comisiones"
                    elif progreso >= 75:
                        bg_color = "#FFF3E0"  # Naranja claro
                        border_color = "#FF9800"
                        bar_color = "#FF9800"
                        estado = f"⏳ Faltan {row['Minimo_Cuatri'] - row['Fact_Cuatri']:,.0f}€"
                    else:
                        bg_color = "#FFEBEE"  # Rojo claro
                        border_color = "#F44336"
                        bar_color = "#F44336"
                        estado = f"📍 Faltan {row['Minimo_Cuatri'] - row['Fact_Cuatri']:,.0f}€"

                    st.markdown(f"""
                    <div style="background: {bg_color}; padding: 16px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid {border_color}; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                            <span style="color: #212121; font-weight: bold; font-size: 16px;">{row['Comercial']}</span>
                            <span style="color: {border_color}; font-weight: bold;">{estado}</span>
                        </div>
                        <div style="background: #E0E0E0; border-radius: 10px; height: 24px; overflow: hidden;">
                            <div style="background: {bar_color}; width: {min(100, progreso)}%; height: 100%; border-radius: 10px; display: flex; align-items: center; justify-content: center;">
                                <span style="color: white; font-size: 12px; font-weight: bold;">{progreso:.0f}%</span>
                            </div>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-top: 10px; font-size: 13px;">
                            <span style="color: #424242;">Facturado: <b style="color: #1565C0;">{row['Fact_Cuatri']:,.0f}€</b></span>
                            <span style="color: #424242;">Minimo: <b>{row['Minimo_Cuatri']:,.0f}€</b></span>
                            <span style="color: #424242;">Comisionable: <b style="color: #2E7D32;">{row['Fact_Comisionable']:,.0f}€</b></span>
                            <span style="color: #424242;">Comision: <b style="color: #F57C00;">{row['Comision_Cuatri']:,.0f}€</b></span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("---")

                # ===== GRAFICO COMPARATIVO =====
                col1, col2 = st.columns(2)

                with col1:
                    fig = px.bar(
                        df_incentivos,
                        x='Comercial',
                        y=['Comision_Mensual', 'Bonus_Mes'],
                        title="💰 Desglose Incentivos Mensuales",
                        barmode='stack',
                        color_discrete_map={'Comision_Mensual': '#000000', 'Bonus_Mes': '#F15025'}  # DAVID Brand
                    )
                    fig.update_layout(
                        height=350,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color='#424242'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    # Comparativa mes actual vs anterior
                    df_comp = df_incentivos[['Comercial', 'Fact_Mes', 'Fact_Mes_Anterior']].melt(
                        id_vars=['Comercial'],
                        var_name='Periodo',
                        value_name='Facturacion'
                    )
                    df_comp['Periodo'] = df_comp['Periodo'].map({'Fact_Mes': 'Mes Actual', 'Fact_Mes_Anterior': 'Mes Anterior'})

                    fig = px.bar(
                        df_comp,
                        x='Comercial',
                        y='Facturacion',
                        color='Periodo',
                        barmode='group',
                        title="📈 Evolucion vs Mes Anterior",
                        color_discrete_map={'Mes Actual': '#000000', 'Mes Anterior': '#E0E0E0'}  # DAVID Brand
                    )
                    fig.update_layout(
                        height=350,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font_color='#424242'
                    )
                    st.plotly_chart(fig, use_container_width=True)

                # Exportar
                st.markdown("---")
                export_data = df_incentivos[['Comercial', 'Fact_Mes', 'Comision_Mensual', 'Bonus_Mes', 'Total_Mes',
                                            'Fact_Cuatri', 'Comision_Cuatri', 'Puntos_Mes']].copy()
                csv = export_data.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Exportar Incentivos a CSV",
                    csv,
                    f"incentivos_{periodo_str.replace(' ', '_')}.csv",
                    "text/csv"
                )

        else:
            st.warning("No hay datos para el periodo seleccionado. Selecciona otro mes/año.")

    # ========== TAB HISTORICO ==========
    with tab_historico:
        st.subheader("Historico de Incentivos")

        historico = obtener_historico_incentivos()

        if historico:
            df_hist = pd.DataFrame(historico)

            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                comerciales_hist = ['Todos'] + df_hist['comercial'].unique().tolist()
                com_filter = st.selectbox("Filtrar por comercial", comerciales_hist)
            with col2:
                periodos_hist = ['Todos'] + df_hist['periodo'].unique().tolist()
                per_filter = st.selectbox("Filtrar por periodo", periodos_hist)

            # Aplicar filtros
            if com_filter != 'Todos':
                df_hist = df_hist[df_hist['comercial'] == com_filter]
            if per_filter != 'Todos':
                df_hist = df_hist[df_hist['periodo'] == per_filter]

            # Mostrar tabla
            st.dataframe(df_hist, width="stretch")

            # Grafico evolucion
            if com_filter != 'Todos':
                fig = px.line(
                    df_hist.sort_values('fecha_calculo'),
                    x='periodo',
                    y='total',
                    title=f"Evolucion de Incentivos - {com_filter}",
                    markers=True
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay registros en el historico. Usa 'Guardar en Historico' en la calculadora.")


# ============================================
# PAGINA 8: CALCULADORA DE TARIFAS
# ============================================
elif pagina == "Calculadora":
    st.title("🧮 Calculadora de Tarifas")
    st.caption("Calcula precios de servicios de transporte")

    # Usar las descripciones de tipos de servicio de la base de datos
    tipos_servicio_guardados = obtener_tipos_servicio_db()

    def get_servicio_desc(codigo):
        """Obtiene descripcion de tipo de servicio o devuelve el codigo si no existe"""
        codigo_upper = codigo.upper().strip() if codigo else ''
        tipo_info = tipos_servicio_guardados.get(codigo_upper, {})
        return tipo_info.get('descripcion', codigo_upper) if tipo_info else codigo_upper

    def get_servicio_con_desc(codigo):
        """Devuelve 'Descripcion' para mostrar en selectbox"""
        codigo_upper = codigo.upper().strip() if codigo else ''
        tipo_info = tipos_servicio_guardados.get(codigo_upper, {})
        desc = tipo_info.get('descripcion', '') if tipo_info else ''
        return normalizar_texto(desc) if desc else codigo_upper

    # Importar funciones necesarias
    from database import (guardar_lugar_frecuente, obtener_lugares_frecuentes,
                         buscar_lugares_frecuentes, obtener_config_calc, guardar_config_calc)

    # Inicializar session state
    if 'calc_paradas' not in st.session_state:
        st.session_state.calc_paradas = []
    if 'calc_origen_coords' not in st.session_state:
        st.session_state.calc_origen_coords = None
    if 'calc_destino_coords' not in st.session_state:
        st.session_state.calc_destino_coords = None
    if 'calc_resultado' not in st.session_state:
        st.session_state.calc_resultado = None

    # Obtener datos necesarios
    tipos_bus = obtener_tipos_bus()
    tipos_bus_dict = {f"{b['nombre']} ({b['capacidad']} plz)": b for b in tipos_bus}
    # Tipos de servicio (normalizados desde los datos)
    tipos_servicio_lista = obtener_tipos_servicio(df)  # Ya incluye 'Todos' al inicio
    # Grupos de cliente desde los datos reales
    grupos_cliente_lista = sorted(df['Grupo de clientes'].dropna().unique().tolist())
    clientes_lista = ["-- Sin cliente especifico --"] + sorted(df['Cliente'].dropna().unique().tolist())
    lugares_guardados = obtener_lugares_frecuentes(limite=20)
    base_direccion = obtener_config_calc('base_direccion', 'Paseo de Anoeta 22, San Sebastian')

    if not tipos_bus_dict or not grupos_cliente_lista:
        st.warning("Configura primero los tipos de bus y segmentos de cliente en 'Configuracion'")
    else:
        # ========== LAYOUT EN 2 COLUMNAS ==========
        col_izq, col_der = st.columns([3, 2])

        with col_izq:
            # -------- SECCION: DATOS DEL SERVICIO - DAVID Brand --------
            st.markdown("""
            <div style="background:#FFFFFF;padding:16px 20px;border-radius:8px;border:1px solid #E0E0E0;border-left:4px solid #000000;margin-bottom:20px;">
                <h4 style="margin:0;color:#000000;font-weight:600;">📋 Datos del Servicio</h4>
            </div>
            """, unsafe_allow_html=True)

            from datetime import datetime, timedelta

            # Selector de modo y checkboxes en una fila
            col_modo, col_ida, col_vuelta = st.columns([2, 1, 1])
            with col_modo:
                modo_calculo = st.radio("Modo", ["Itinerario", "Disposición"], horizontal=True, key="c_modo_calc", label_visibility="collapsed")
            with col_ida:
                incluir_pos_ida = st.checkbox("Ida desde base", value=True, key="c_pos_ida")
            with col_vuelta:
                incluir_pos_vuelta = st.checkbox("Vuelta a base", value=True, key="c_pos_vuelta")

            # Campos según modo seleccionado
            if modo_calculo == "Itinerario":
                c1, c2 = st.columns(2)
                with c1:
                    fecha_salida = st.date_input("Fecha Salida", key="c_fecha_sal", format="DD/MM/YYYY")
                    hora_salida = st.time_input("Hora Salida", value=pd.Timestamp("09:00").time(), key="c_hora_sal")
                with c2:
                    fecha_llegada = st.date_input("Fecha Llegada", key="c_fecha_lleg", format="DD/MM/YYYY")
                    hora_llegada = st.time_input("Hora Llegada", value=pd.Timestamp("21:00").time(), key="c_hora_lleg")

                    # Mostrar hora estimada si hay cálculo
                    hora_estimada = st.session_state.get('calc_tiempo_desglose', {}).get('hora_estimada_llegada')
                    if hora_estimada:
                        hora_llegada_str = hora_llegada.strftime('%H:%M')
                        try:
                            h_est = datetime.strptime(hora_estimada, '%H:%M')
                            h_lleg = datetime.strptime(hora_llegada_str, '%H:%M')
                            diff_min = abs((h_est - h_lleg).total_seconds() / 60)
                            horas_srv = st.session_state.get('calc_resultado', {}).get('horas', 12)
                            umbral = horas_srv * 60 * 0.05
                            color = "#D32F2F" if diff_min > umbral else "#4CAF50"
                        except:
                            color = "#666"
                        st.markdown(f"<span style='font-size:12px;color:{color};'>Estimada: <b>{hora_estimada}</b></span>", unsafe_allow_html=True)

                # Calcular horas totales desde fechas/horas
                dt_salida = datetime.combine(fecha_salida, hora_salida)
                dt_llegada = datetime.combine(fecha_llegada, hora_llegada)
                if dt_llegada <= dt_salida:
                    dt_llegada = dt_llegada + timedelta(days=1)
                horas_totales_input = (dt_llegada - dt_salida).total_seconds() / 3600

                horas_int = int(horas_totales_input)
                mins_int = int((horas_totales_input - horas_int) * 60)
                duracion_texto = f"{horas_int}h {mins_int}m" if mins_int > 0 else f"{horas_int}h"
                st.markdown(f"**Duración del servicio:** {duracion_texto}")

            else:  # Modo Disposición
                c1, c2, c3 = st.columns([2, 2, 1])
                with c1:
                    fecha_salida = st.date_input("Fecha Salida", key="c_fecha_sal_disp", format="DD/MM/YYYY")
                with c2:
                    hora_salida = st.time_input("Hora Salida", value=pd.Timestamp("09:00").time(), key="c_hora_sal_disp")
                with c3:
                    horas_disposicion = st.number_input("Horas", min_value=1, max_value=72, value=8, key="c_horas_disp")

                # Calcular llegada a partir de salida + horas
                horas_totales_input = float(horas_disposicion)
                dt_salida = datetime.combine(fecha_salida, hora_salida)
                dt_llegada = dt_salida + timedelta(hours=horas_totales_input)
                fecha_llegada = dt_llegada.date()
                hora_llegada = dt_llegada.time()

                # Mostrar campos calculados de llegada
                c4, c5 = st.columns(2)
                with c4:
                    st.markdown(f"""
                    <div style="margin-bottom:4px;"><span style="font-size:14px;color:#31333F;">Fecha Llegada</span></div>
                    <div style="background:#EAEAEA;padding:9px 12px;border-radius:6px;color:#31333F;font-size:14px;">
                        {fecha_llegada.strftime('%d/%m/%Y')}
                    </div>
                    """, unsafe_allow_html=True)
                with c5:
                    hora_estimada = st.session_state.get('calc_tiempo_desglose', {}).get('hora_estimada_llegada')
                    hora_mostrar = hora_estimada if hora_estimada else hora_llegada.strftime('%H:%M')
                    color_hora = "#31333F"
                    if hora_estimada:
                        try:
                            h_est = datetime.strptime(hora_estimada, '%H:%M')
                            h_calc = datetime.strptime(hora_llegada.strftime('%H:%M'), '%H:%M')
                            diff_min = abs((h_est - h_calc).total_seconds() / 60)
                            umbral = horas_totales_input * 60 * 0.05
                            color_hora = "#D32F2F" if diff_min > umbral else "#31333F"
                        except:
                            pass
                    st.markdown(f"""
                    <div style="margin-bottom:4px;"><span style="font-size:14px;color:#31333F;">Hora Llegada</span></div>
                    <div style="background:#EAEAEA;padding:9px 12px;border-radius:6px;color:{color_hora};font-size:14px;">
                        {hora_mostrar}
                    </div>
                    """, unsafe_allow_html=True)

            c3, c4, c5 = st.columns(3)
            with c3:
                tipo_bus_sel = st.selectbox("Tipo de Bus", list(tipos_bus_dict.keys()), key="c_tipo_bus")
                bus_info = tipos_bus_dict[tipo_bus_sel]
            with c4:
                tipo_servicio_sel = st.selectbox("Tipo de Servicio", tipos_servicio_lista, key="c_tipo_srv")
                tipo_servicio_codigo = tipo_servicio_sel if tipo_servicio_sel != "Todos" else None
            with c5:
                num_vehiculos = st.number_input("Vehiculos", min_value=1, max_value=10, value=1, key="c_vehiculos")

            c6, c7 = st.columns(2)
            with c6:
                grupo_cliente_sel = st.selectbox("Grupo de cliente", grupos_cliente_lista, key="c_grupo_cli")
            with c7:
                cliente_sel = st.selectbox("Cliente especifico", clientes_lista, key="c_cliente")
                cliente = None if cliente_sel == "-- Sin cliente especifico --" else cliente_sel

            st.markdown("---")

            # ========== ITINERARIO - DISEÑO LIMPIO ==========
            st.markdown("#### Itinerario")

            # ORIGEN Y DESTINO - Siempre editable
            col_orig, col_dest = st.columns(2)

            with col_orig:
                origen_guardado = st.session_state.get('calc_origen_nombre', '')
                origen_txt = st.text_input("Origen (recogida)", value=origen_guardado, placeholder="Ej: Aeropuerto Bilbao", key="input_origen")

                # Geocodificar cuando hay texto y es diferente al guardado
                if origen_txt and origen_txt != origen_guardado:
                    geo = geocodificar_direccion(origen_txt)
                    if geo:
                        st.session_state.calc_origen_coords = (geo[0], geo[1])
                        st.session_state.calc_origen_dir = geo[2]
                        st.session_state.calc_origen_nombre = origen_txt
                        st.rerun()
                elif not origen_txt and origen_guardado:
                    for k in ['calc_origen_coords', 'calc_origen_dir', 'calc_origen_nombre']:
                        st.session_state.pop(k, None)
                    st.rerun()

            with col_dest:
                destino_guardado = st.session_state.get('calc_destino_nombre', '')
                destino_txt = st.text_input("Destino (llegada)", value=destino_guardado, placeholder="Ej: Hotel Gran Bilbao", key="input_destino")

                # Geocodificar cuando hay texto y es diferente al guardado
                if destino_txt and destino_txt != destino_guardado:
                    geo = geocodificar_direccion(destino_txt)
                    if geo:
                        st.session_state.calc_destino_coords = (geo[0], geo[1])
                        st.session_state.calc_destino_dir = geo[2]
                        st.session_state.calc_destino_nombre = destino_txt
                        st.rerun()
                elif not destino_txt and destino_guardado:
                    for k in ['calc_destino_coords', 'calc_destino_dir', 'calc_destino_nombre']:
                        st.session_state.pop(k, None)
                    st.rerun()

            # Paradas intermedias - editables directamente
            num_paradas = len(st.session_state.calc_paradas)
            if num_paradas > 0:
                st.caption("Paradas intermedias:")
                for i, parada in enumerate(st.session_state.calc_paradas):
                    c1, c2 = st.columns([6, 1])
                    with c1:
                        nuevo_txt = st.text_input(f"Parada {i+1}", value=parada['texto'], key=f"parada_{i}", label_visibility="collapsed")
                        if nuevo_txt != parada['texto']:
                            if nuevo_txt:
                                geo = geocodificar_direccion(nuevo_txt)
                                if geo:
                                    st.session_state.calc_paradas[i] = {'texto': nuevo_txt, 'dir': geo[2], 'coords': (geo[0], geo[1])}
                                    st.rerun()
                            else:
                                st.session_state.calc_paradas.pop(i)
                                st.rerun()
                    with c2:
                        if st.button("✕", key=f"del_p_{i}"):
                            st.session_state.calc_paradas.pop(i)
                            st.rerun()

            # Añadir nueva parada - con botón explícito para evitar duplicados
            with st.expander("+ Añadir parada"):
                col_p1, col_p2 = st.columns([4, 1])
                with col_p1:
                    parada_txt = st.text_input("Nueva parada", placeholder="Ej: Vitoria", key="input_parada_new", label_visibility="collapsed")
                with col_p2:
                    btn_add = st.button("Añadir", key="btn_add_parada", type="primary")

                if btn_add and parada_txt:
                    geo = geocodificar_direccion(parada_txt)
                    if geo:
                        st.session_state.calc_paradas.append({'texto': parada_txt, 'dir': geo[2], 'coords': (geo[0], geo[1])})
                        st.rerun()
                    else:
                        st.error("No se encontró la dirección")

            st.markdown("---")

            # ========== OPCIONES - COMPACTAS ==========
            st.markdown("#### Opciones")
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                tiempo_limpieza = st.selectbox("Limpieza", [0, 15, 30, 45, 60],
                                               format_func=lambda x: f"{x}min" if x > 0 else "No", key="c_limpieza")
            with c2:
                peajes_manual = st.number_input("Peajes €", min_value=0.0, value=0.0, step=5.0, key="c_peajes")
            with c3:
                dietas_manual = st.number_input("Dietas €", min_value=0.0, value=0.0, step=10.0, key="c_dietas")
            with c4:
                hoteles_manual = st.number_input("Hoteles €", min_value=0.0, value=0.0, step=25.0, key="c_hoteles")
            with c5:
                otros_manual = st.number_input("Otros €", min_value=0.0, value=0.0, step=10.0, key="c_otros")

            # Configuración avanzada
            with st.expander("Configuración avanzada"):
                col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
                with col_cfg1:
                    nueva_base = st.text_input("Dirección base/cochera", value=base_direccion, key="nueva_base")
                with col_cfg2:
                    indice_actual = float(obtener_config_calc('indice_vehiculo_pesado') or '1.20')
                    nuevo_indice = st.number_input("Índice veh. pesado", min_value=1.0, max_value=2.0,
                                                    value=indice_actual, step=0.05, key="cfg_indice",
                                                    help="Multiplica el tiempo de ruta (1.20 = +20%)")
                with col_cfg3:
                    tiempo_presentacion_actual = int(obtener_config_calc('tiempo_presentacion') or '15')
                    nuevo_tiempo_pres = st.number_input("Presentación (min)", min_value=0, max_value=60,
                                                         value=tiempo_presentacion_actual, step=5, key="cfg_presentacion",
                                                         help="Tiempo de presentación antes de la hora de servicio")
                if st.button("Guardar configuración", key="btn_save_cfg"):
                    guardar_config_calc('base_direccion', nueva_base)
                    guardar_config_calc('indice_vehiculo_pesado', str(nuevo_indice))
                    guardar_config_calc('tiempo_presentacion', str(nuevo_tiempo_pres))
                    st.success("Configuración guardada")
                    st.rerun()

            st.markdown("")

            # ========== BOTONES ==========
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                btn_calcular = st.button("🧮 CALCULAR PRESUPUESTO", type="primary", use_container_width=True, key="btn_calc_main")
            with col_btn2:
                if st.button("🗑️ Limpiar todo", use_container_width=True, key="btn_limpiar"):
                    for key in ['calc_origen_coords', 'calc_origen_dir', 'calc_origen_nombre',
                               'calc_destino_coords', 'calc_destino_dir', 'calc_destino_nombre',
                               'calc_paradas', 'calc_km_total', 'calc_resultado', 'calc_ruta_info',
                               'calc_puntos', 'calc_ruta_coords', 'calc_km_desglose']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.session_state.calc_paradas = []
                    st.rerun()

        # ========== LOGICA DE CALCULO AUTOMATICO (antes de mostrar resultados) ==========
        tiene_origen = st.session_state.get('calc_origen_coords') is not None
        tiene_destino = st.session_state.get('calc_destino_coords') is not None
        debe_calcular = tiene_origen and tiene_destino

        if debe_calcular:
            # Detectar si algo cambió para recalcular
            origen_coords = st.session_state.get('calc_origen_coords', '')
            destino_coords = st.session_state.get('calc_destino_coords', '')
            paradas_str = str([(p.get('coords', '')) for p in st.session_state.get('calc_paradas', [])])
            estado_actual = f"{modo_calculo}_{fecha_salida}_{hora_salida}_{horas_totales_input}_{bus_info['codigo']}_{tipo_servicio_codigo}_{num_vehiculos}_{grupo_cliente_sel}_{incluir_pos_ida}_{incluir_pos_vuelta}_{tiempo_limpieza}_{peajes_manual}_{dietas_manual}_{hoteles_manual}_{otros_manual}_{origen_coords}_{destino_coords}_{paradas_str}"
            estado_anterior = st.session_state.get('_estado_calc', '')

            if estado_actual != estado_anterior:
                st.session_state._estado_calc = estado_actual

                # Calcular ruta
                base_geo = None
                km_pos_ida = 0
                km_servicio = 0
                km_pos_vuelta = 0
                tiempo_pos_ida_min = 0
                tiempo_servicio_min = 0
                tiempo_pos_vuelta_min = 0
                puntos_completos = []
                ruta_coords_total = []

                indice_pesado = float(obtener_config_calc('indice_vehiculo_pesado') or '1.20')
                tiempo_presentacion_min = int(obtener_config_calc('tiempo_presentacion') or '15')

                if incluir_pos_ida or incluir_pos_vuelta:
                    base_geo = geocodificar_direccion(base_direccion)

                # TRAMO 1: Posicionamiento IDA
                if incluir_pos_ida and base_geo:
                    tramo_ida = calcular_ruta_osrm([(base_geo[0], base_geo[1]), st.session_state.calc_origen_coords])
                    if tramo_ida:
                        km_pos_ida = round(tramo_ida['distancia_km'])
                        tiempo_pos_ida_min = tramo_ida.get('duracion_min', 0)
                        ruta_coords_total.extend(tramo_ida.get('ruta_coords', []))
                    puntos_completos.append((base_geo[0], base_geo[1]))

                # TRAMO 2: Servicio
                puntos_servicio = [st.session_state.calc_origen_coords]
                for parada in st.session_state.calc_paradas:
                    puntos_servicio.append(parada['coords'])
                puntos_servicio.append(st.session_state.calc_destino_coords)

                if len(puntos_servicio) >= 2:
                    tramo_servicio = calcular_ruta_osrm(puntos_servicio)
                    if tramo_servicio:
                        km_servicio = round(tramo_servicio['distancia_km'])
                        tiempo_servicio_min = tramo_servicio.get('duracion_min', 0)
                        ruta_coords_total.extend(tramo_servicio.get('ruta_coords', []))

                puntos_completos.extend(puntos_servicio)

                # TRAMO 3: Posicionamiento VUELTA
                if incluir_pos_vuelta and base_geo:
                    tramo_vuelta = calcular_ruta_osrm([st.session_state.calc_destino_coords, (base_geo[0], base_geo[1])])
                    if tramo_vuelta:
                        km_pos_vuelta = round(tramo_vuelta['distancia_km'])
                        tiempo_pos_vuelta_min = tramo_vuelta.get('duracion_min', 0)
                        ruta_coords_total.extend(tramo_vuelta.get('ruta_coords', []))
                    puntos_completos.append((base_geo[0], base_geo[1]))

                km = km_pos_ida + km_servicio + km_pos_vuelta

                if km > 0:
                    st.session_state.calc_km_total = km
                    st.session_state.calc_km_desglose = {'pos_ida': km_pos_ida, 'servicio': km_servicio, 'pos_vuelta': km_pos_vuelta}
                    st.session_state.calc_ruta_coords = ruta_coords_total
                    st.session_state.calc_puntos = puntos_completos

                    from datetime import datetime as dt, timedelta
                    try:
                        h_ini = dt.combine(fecha_salida, hora_salida)
                        h_fin = dt.combine(fecha_llegada, hora_llegada)
                        if h_fin < h_ini:
                            h_fin = dt.combine(fecha_llegada + timedelta(days=1), hora_llegada)
                        tiempo_servicio_manual_min = (h_fin - h_ini).total_seconds() / 60

                        tiempo_pos_ida_ajustado = tiempo_pos_ida_min * indice_pesado
                        tiempo_pos_vuelta_ajustado = tiempo_pos_vuelta_min * indice_pesado
                        tiempo_total_min = tiempo_pos_ida_ajustado + tiempo_presentacion_min + tiempo_servicio_manual_min + tiempo_pos_vuelta_ajustado + tiempo_limpieza
                        horas = tiempo_total_min / 60

                        # Tiempo total estimado: base→origen→paradas→destino→base
                        tiempo_servicio_ajustado = tiempo_servicio_min * indice_pesado
                        tiempo_total_estimado_min = tiempo_pos_ida_ajustado + tiempo_presentacion_min + tiempo_servicio_ajustado + tiempo_pos_vuelta_ajustado
                        hora_estimada_llegada = h_ini + timedelta(minutes=tiempo_total_estimado_min)
                    except:
                        horas = 8
                        tiempo_pos_ida_ajustado = tiempo_pos_vuelta_ajustado = 0
                        tiempo_servicio_manual_min = tiempo_total_min = 0
                        hora_estimada_llegada = None

                    st.session_state.calc_tiempo_desglose = {
                        'pos_ida_min': round(tiempo_pos_ida_ajustado) if tiempo_pos_ida_ajustado else 0,
                        'presentacion_min': tiempo_presentacion_min,
                        'servicio_manual_min': round(tiempo_servicio_manual_min) if tiempo_servicio_manual_min else 0,
                        'pos_vuelta_min': round(tiempo_pos_vuelta_ajustado) if tiempo_pos_vuelta_ajustado else 0,
                        'limpieza_min': tiempo_limpieza,
                        'total_min': round(tiempo_total_min) if tiempo_total_min else 0,
                        'hora_estimada_llegada': hora_estimada_llegada.strftime('%H:%M') if hora_estimada_llegada else None,
                        'indice_pesado': indice_pesado
                    }

                    resultado = calcular_tarifa(
                        tipo_servicio=tipo_servicio_codigo,
                        tipo_bus=bus_info['codigo'],
                        horas=horas,
                        km=km,
                        cliente=cliente,
                        fecha=fecha_salida
                    )

                    if resultado:
                        precio_base = resultado.get('total', 0)
                        extras_totales = peajes_manual + dietas_manual + hoteles_manual + otros_manual
                        precio_con_extras = precio_base + extras_totales
                        precio_final = precio_con_extras * num_vehiculos

                        st.session_state.calc_resultado = {
                            'precio_final': precio_final,
                            'precio_unitario': precio_con_extras,
                            'desglose': resultado,
                            'horas': horas,
                            'km': km,
                            'km_desglose': st.session_state.calc_km_desglose,
                            'tiempo_desglose': st.session_state.calc_tiempo_desglose,
                            'vehiculos': num_vehiculos,
                            'peajes': peajes_manual,
                            'dietas': dietas_manual,
                            'hoteles': hoteles_manual,
                            'otros': otros_manual,
                            'tipo_bus_codigo': bus_info['codigo'],
                            'tipo_bus_nombre': tipo_bus_sel,
                            'tipo_servicio': tipo_servicio_codigo
                        }

        # ========== COLUMNA DERECHA: RESULTADO - DAVID Brand ==========
        with col_der:
            st.markdown("""
            <div style="background:#FFFFFF;padding:16px 20px;border-radius:8px;border:1px solid #E0E0E0;border-left:4px solid #F15025;margin-bottom:20px;">
                <h4 style="margin:0;color:#000000;font-weight:600;">💰 Presupuesto</h4>
            </div>
            """, unsafe_allow_html=True)

            if st.session_state.get('calc_resultado'):
                res = st.session_state.calc_resultado
                # Calcular km total desde desglose para asegurar consistencia
                km_desg_card = res.get('km_desglose', {})
                km_total_card = km_desg_card.get('pos_ida', 0) + km_desg_card.get('servicio', 0) + km_desg_card.get('pos_vuelta', 0)

                # Obtener costes del tipo de bus seleccionado
                tipo_bus_codigo = res.get('tipo_bus_codigo', '')
                tipo_bus_nombre = res.get('tipo_bus_nombre', 'Bus')
                COSTE_POR_KM = 0.85  # Default
                COSTE_POR_HORA = 30.0  # Default

                # Buscar costes configurados del bus
                tipos_bus_data = obtener_tipos_bus()
                for bus in tipos_bus_data:
                    if bus['codigo'] == tipo_bus_codigo:
                        COSTE_POR_KM = bus.get('coste_km', 0.85)
                        COSTE_POR_HORA = bus.get('coste_hora', 30.0)
                        break

                coste_total = (COSTE_POR_KM * km_total_card) + (COSTE_POR_HORA * res['horas'])
                coste_total *= res['vehiculos']  # Multiplicar por número de vehículos
                rentabilidad = res['precio_final'] - coste_total
                margen_pct = (rentabilidad / res['precio_final'] * 100) if res['precio_final'] > 0 else 0

                # Color según rentabilidad
                if rentabilidad > 0:
                    color_rent = "#4CAF50"  # Verde
                    icono_rent = "📈"
                else:
                    color_rent = "#F44336"  # Rojo
                    icono_rent = "📉"

                # Card principal del precio - Compacta, blanca con borde de color
                st.markdown(f"""
                <div style="background: #FFFFFF; padding: 16px; border-radius: 8px; text-align: center; margin-bottom: 16px; border: 2px solid #F15025;">
                    <p style="margin: 0 0 8px 0; font-size: 36px; font-weight: 700; color: #000000;">{res['precio_final']:,.2f} €</p>
                    <div style="display: flex; justify-content: center; gap: 16px; font-size: 13px; color: #666;">
                        <span>🚌 {res['vehiculos']} veh</span>
                        <span>🛣️ {km_total_card} km</span>
                        <span>⏱️ {res['horas']:.1f}h</span>
                    </div>
                    <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #eee; font-size: 12px; color: {color_rent};">
                        {icono_rent} Rentab: <strong>{rentabilidad:,.0f}€</strong> ({margen_pct:.0f}%)
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Botón de desglose completo
                with st.expander("📊 Ver desglose completo del cálculo", expanded=False):
                    desglose = res.get('desglose', {})
                    tiempo_desg_exp = res.get('tiempo_desglose', {})
                    km_desg_exp = res.get('km_desglose', {})

                    # Origen de la tarifa
                    origen_tarifa = desglose.get('origen', 'base')
                    origen_texto = {
                        'cliente_personalizado': '✨ Tarifa personalizada del cliente',
                        'tarifa_servicio': '📋 Tarifa por tipo de servicio',
                        'tipo_bus': '🚌 Tarifa base del vehículo'
                    }.get(origen_tarifa, 'Tarifa base')

                    # Multiplicadores
                    mult_temporada = desglose.get('multiplicador_temporada', 1.0)
                    mult_cliente = desglose.get('multiplicador_cliente', 1.0)

                    # Índices y costes
                    indice_pesado = tiempo_desg_exp.get('indice_pesado', 1.2)

                    st.markdown(f"""
                    <div style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);color:white;padding:12px 16px;border-radius:8px 8px 0 0;margin:-1rem -1rem 0 -1rem;">
                        <strong style="font-size:15px;">DESGLOSE COMPLETO DEL PRESUPUESTO</strong>
                    </div>
                    """, unsafe_allow_html=True)

                    # Sección 1: Origen de Tarifa
                    st.markdown(f"""
                    <div style="background:#f8f9fa;padding:12px;border-radius:0 0 8px 8px;border:1px solid #e0e0e0;border-top:none;margin-bottom:12px;">
                        <div style="font-size:12px;color:#666;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;">Tarifa Aplicada</div>
                        <div style="font-size:14px;font-weight:600;color:#333;">{origen_texto}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Sección 2: Tarifas unitarias
                    precio_km = desglose.get('precio_km', 0)
                    precio_hora = desglose.get('precio_hora', 0)
                    precio_base = desglose.get('precio_base', 0)

                    st.markdown("""<div style="font-weight:600;color:#333;margin:12px 0 8px 0;font-size:13px;">TARIFAS UNITARIAS</div>""", unsafe_allow_html=True)
                    col_t1, col_t2, col_t3 = st.columns(3)
                    with col_t1:
                        st.markdown(f"""
                        <div style="background:#e3f2fd;padding:10px;border-radius:6px;text-align:center;">
                            <div style="font-size:11px;color:#1565c0;">Precio/Hora</div>
                            <div style="font-size:18px;font-weight:700;color:#0d47a1;">{precio_hora:.2f}€</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_t2:
                        st.markdown(f"""
                        <div style="background:#e8f5e9;padding:10px;border-radius:6px;text-align:center;">
                            <div style="font-size:11px;color:#2e7d32;">Precio/Km</div>
                            <div style="font-size:18px;font-weight:700;color:#1b5e20;">{precio_km:.2f}€</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_t3:
                        st.markdown(f"""
                        <div style="background:#fff3e0;padding:10px;border-radius:6px;text-align:center;">
                            <div style="font-size:11px;color:#e65100;">Precio Base</div>
                            <div style="font-size:18px;font-weight:700;color:#bf360c;">{precio_base:.2f}€</div>
                        </div>
                        """, unsafe_allow_html=True)

                    # Sección 3: Cálculo del servicio
                    st.markdown("""<div style="font-weight:600;color:#333;margin:16px 0 8px 0;font-size:13px;">CÁLCULO DEL SERVICIO</div>""", unsafe_allow_html=True)

                    importe_horas = precio_hora * res['horas']
                    importe_km = precio_km * km_total_card
                    subtotal = desglose.get('subtotal', importe_horas + importe_km + precio_base)

                    st.markdown(f"""
                    <div style="background:#fafafa;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden;">
                        <table style="width:100%;border-collapse:collapse;font-size:13px;">
                            <tr style="background:#f5f5f5;">
                                <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;">Horas de servicio</td>
                                <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;text-align:right;">{res['horas']:.1f}h × {precio_hora:.2f}€</td>
                                <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;text-align:right;font-weight:600;">{importe_horas:.2f}€</td>
                            </tr>
                            <tr>
                                <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;">Kilómetros totales</td>
                                <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;text-align:right;">{km_total_card}km × {precio_km:.2f}€</td>
                                <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;text-align:right;font-weight:600;">{importe_km:.2f}€</td>
                            </tr>
                            <tr style="background:#f5f5f5;">
                                <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;">Precio base</td>
                                <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;text-align:right;">-</td>
                                <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;text-align:right;font-weight:600;">{precio_base:.2f}€</td>
                            </tr>
                            <tr style="background:#e3f2fd;">
                                <td colspan="2" style="padding:10px 12px;font-weight:600;">SUBTOTAL</td>
                                <td style="padding:10px 12px;text-align:right;font-weight:700;font-size:15px;">{subtotal:.2f}€</td>
                            </tr>
                        </table>
                    </div>
                    """, unsafe_allow_html=True)

                    # Sección 4: Multiplicadores
                    st.markdown("""<div style="font-weight:600;color:#333;margin:16px 0 8px 0;font-size:13px;">MULTIPLICADORES APLICADOS</div>""", unsafe_allow_html=True)
                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        color_temp = "#4caf50" if mult_temporada > 1 else ("#ff9800" if mult_temporada < 1 else "#9e9e9e")
                        st.markdown(f"""
                        <div style="background:#fff;border:2px solid {color_temp};padding:10px;border-radius:6px;text-align:center;">
                            <div style="font-size:11px;color:#666;">Temporada</div>
                            <div style="font-size:22px;font-weight:700;color:{color_temp};">×{mult_temporada:.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_m2:
                        color_cli = "#4caf50" if mult_cliente > 1 else ("#ff9800" if mult_cliente < 1 else "#9e9e9e")
                        st.markdown(f"""
                        <div style="background:#fff;border:2px solid {color_cli};padding:10px;border-radius:6px;text-align:center;">
                            <div style="font-size:11px;color:#666;">Tipo Cliente</div>
                            <div style="font-size:22px;font-weight:700;color:{color_cli};">×{mult_cliente:.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    total_con_mult = subtotal * mult_temporada * mult_cliente
                    st.markdown(f"""
                    <div style="background:#e8eaf6;padding:10px;border-radius:6px;margin-top:8px;display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-size:13px;">Subtotal × Temporada × Cliente</span>
                        <span style="font-size:16px;font-weight:700;color:#3f51b5;">{subtotal:.2f}€ × {mult_temporada:.2f} × {mult_cliente:.2f} = {total_con_mult:.2f}€</span>
                    </div>
                    """, unsafe_allow_html=True)

                    # Sección 5: Extras
                    extras_total = res.get('peajes', 0) + res.get('dietas', 0) + res.get('hoteles', 0) + res.get('otros', 0)
                    if extras_total > 0:
                        st.markdown("""<div style="font-weight:600;color:#333;margin:16px 0 8px 0;font-size:13px;">EXTRAS Y GASTOS ADICIONALES</div>""", unsafe_allow_html=True)
                        extras_html = "<div style='display:flex;gap:8px;flex-wrap:wrap;'>"
                        if res.get('peajes', 0) > 0:
                            extras_html += f"<div style='background:#ffecb3;padding:8px 12px;border-radius:6px;'><span style='font-size:11px;color:#ff8f00;'>Peajes</span><br><strong>{res['peajes']:.2f}€</strong></div>"
                        if res.get('dietas', 0) > 0:
                            extras_html += f"<div style='background:#c8e6c9;padding:8px 12px;border-radius:6px;'><span style='font-size:11px;color:#388e3c;'>Dietas</span><br><strong>{res['dietas']:.2f}€</strong></div>"
                        if res.get('hoteles', 0) > 0:
                            extras_html += f"<div style='background:#bbdefb;padding:8px 12px;border-radius:6px;'><span style='font-size:11px;color:#1976d2;'>Hoteles</span><br><strong>{res['hoteles']:.2f}€</strong></div>"
                        if res.get('otros', 0) > 0:
                            extras_html += f"<div style='background:#e1bee7;padding:8px 12px;border-radius:6px;'><span style='font-size:11px;color:#7b1fa2;'>Otros</span><br><strong>{res['otros']:.2f}€</strong></div>"
                        extras_html += "</div>"
                        st.markdown(extras_html, unsafe_allow_html=True)

                    # Sección 6: Total por vehículo y final
                    precio_unitario = res.get('precio_unitario', total_con_mult + extras_total)
                    st.markdown("""<div style="font-weight:600;color:#333;margin:16px 0 8px 0;font-size:13px;">PRECIO FINAL</div>""", unsafe_allow_html=True)
                    st.markdown(f"""
                    <div style="background:#fafafa;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden;">
                        <table style="width:100%;border-collapse:collapse;font-size:13px;">
                            <tr style="background:#f5f5f5;">
                                <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;">Precio por vehículo</td>
                                <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;text-align:right;font-weight:600;">{precio_unitario:.2f}€</td>
                            </tr>
                            <tr>
                                <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;">Número de vehículos</td>
                                <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;text-align:right;font-weight:600;">×{res['vehiculos']}</td>
                            </tr>
                            <tr style="background:linear-gradient(135deg, #F15025 0%, #ff7043 100%);color:white;">
                                <td style="padding:12px;font-weight:600;font-size:15px;">PRECIO TOTAL</td>
                                <td style="padding:12px;text-align:right;font-weight:700;font-size:20px;">{res['precio_final']:.2f}€</td>
                            </tr>
                        </table>
                    </div>
                    """, unsafe_allow_html=True)

                    # Sección 7: Rentabilidad
                    st.markdown("""<div style="font-weight:600;color:#333;margin:16px 0 8px 0;font-size:13px;">ANÁLISIS DE RENTABILIDAD</div>""", unsafe_allow_html=True)
                    coste_km_total = COSTE_POR_KM * km_total_card * res['vehiculos']
                    coste_hora_total = COSTE_POR_HORA * res['horas'] * res['vehiculos']

                    st.markdown(f"""
                    <div style="background:#fafafa;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden;margin-bottom:8px;">
                        <table style="width:100%;border-collapse:collapse;font-size:13px;">
                            <tr style="background:#ffebee;">
                                <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;">Coste kilómetros</td>
                                <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;text-align:right;">{km_total_card}km × {COSTE_POR_KM:.2f}€ × {res['vehiculos']} veh</td>
                                <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;text-align:right;font-weight:600;color:#c62828;">{coste_km_total:.2f}€</td>
                            </tr>
                            <tr style="background:#fff;">
                                <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;">Coste horas</td>
                                <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;text-align:right;">{res['horas']:.1f}h × {COSTE_POR_HORA:.2f}€ × {res['vehiculos']} veh</td>
                                <td style="padding:8px 12px;border-bottom:1px solid #e0e0e0;text-align:right;font-weight:600;color:#c62828;">{coste_hora_total:.2f}€</td>
                            </tr>
                            <tr style="background:#ffcdd2;">
                                <td colspan="2" style="padding:10px 12px;font-weight:600;">COSTE TOTAL</td>
                                <td style="padding:10px 12px;text-align:right;font-weight:700;font-size:15px;color:#b71c1c;">{coste_total:.2f}€</td>
                            </tr>
                        </table>
                    </div>
                    """, unsafe_allow_html=True)

                    # Resultado rentabilidad
                    bg_rent = "#e8f5e9" if rentabilidad > 0 else "#ffebee"
                    color_rent_final = "#2e7d32" if rentabilidad > 0 else "#c62828"
                    st.markdown(f"""
                    <div style="background:{bg_rent};padding:14px;border-radius:8px;display:flex;justify-content:space-between;align-items:center;border:2px solid {color_rent_final};">
                        <div>
                            <div style="font-size:12px;color:#666;">Rentabilidad (Precio - Coste)</div>
                            <div style="font-size:11px;color:#999;">{res['precio_final']:.2f}€ - {coste_total:.2f}€</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:28px;font-weight:700;color:{color_rent_final};">{rentabilidad:+,.2f}€</div>
                            <div style="font-size:14px;color:{color_rent_final};">Margen: {margen_pct:.1f}%</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Índices técnicos
                    st.markdown("""<div style="font-weight:600;color:#333;margin:16px 0 8px 0;font-size:13px;">ÍNDICES TÉCNICOS</div>""", unsafe_allow_html=True)
                    st.markdown(f"""
                    <div style="background:#f5f5f5;padding:10px;border-radius:6px;font-size:12px;color:#666;">
                        <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                            <span>Índice vehículo pesado (OSRM):</span><strong>×{indice_pesado:.2f}</strong>
                        </div>
                        <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                            <span>Coste operativo por km:</span><strong>{COSTE_POR_KM:.2f}€/km</strong>
                        </div>
                        <div style="display:flex;justify-content:space-between;">
                            <span>Coste operativo por hora:</span><strong>{COSTE_POR_HORA:.2f}€/h</strong>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                # Mapa de la ruta (debajo del total)
                if st.session_state.get('calc_puntos') and st.session_state.get('calc_ruta_coords'):
                    # Obtener valores de checkboxes desde session_state
                    pos_ida = st.session_state.get('c_pos_ida', True)
                    pos_vuelta = st.session_state.get('c_pos_vuelta', True)
                    nombres = []
                    if pos_ida:
                        nombres.append("Base")
                    nombres.append(st.session_state.get('calc_origen_nombre', 'Origen'))
                    for i, p in enumerate(st.session_state.calc_paradas):
                        nombres.append(f"Parada {i+1}")
                    nombres.append(st.session_state.get('calc_destino_nombre', 'Destino'))
                    if pos_vuelta:
                        nombres.append("Base")

                    mapa = crear_mapa_ruta(
                        st.session_state.calc_puntos,
                        nombres,
                        st.session_state.calc_ruta_coords
                    )
                    st_folium(mapa, width=None, height=250, key="mapa_ruta")

                # Desglose compacto - calcular totales reales
                precio_base = res['desglose'].get('precio_base', 0)
                tarifa_km = res['desglose'].get('precio_km', 0)  # €/km
                tarifa_hora = res['desglose'].get('precio_hora', 0)  # €/hora
                km_total = res.get('km', 0)
                horas_total = res.get('horas', 0)

                # Calcular importes totales
                importe_km = tarifa_km * km_total
                importe_horas = tarifa_hora * horas_total

                # Mostrar resumen de horas y km - DAVID Brand
                st.markdown(f"""
                <div style="background:#F5F5F5;padding:14px;border-radius:8px;margin-bottom:16px;border:1px solid #E0E0E0;">
                    <div style="display:flex;justify-content:space-around;text-align:center;">
                        <div>
                            <div style="font-size:24px;font-weight:700;color:#000000;">{km_total:.0f} km</div>
                            <div style="font-size:11px;color:#424242;text-transform:uppercase;letter-spacing:0.05em;">Total kilómetros</div>
                        </div>
                        <div style="border-left:1px solid #E0E0E0;"></div>
                        <div>
                            <div style="font-size:24px;font-weight:700;color:#000000;">{horas_total:.1f} h</div>
                            <div style="font-size:11px;color:#424242;text-transform:uppercase;letter-spacing:0.05em;">Total horas</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("**Desglose económico**")
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("Horas", f"{importe_horas:.0f} €", help=f"{horas_total:.1f}h × {tarifa_hora:.2f}€/h")
                with c2:
                    st.metric("Kilometros", f"{importe_km:.0f} €", help=f"{km_total:.0f}km × {tarifa_km:.2f}€/km")

                # Mostrar extras solo si hay valores
                extras_cols = []
                extras_vals = []
                if res.get('peajes', 0) > 0:
                    extras_cols.append("Peajes")
                    extras_vals.append(res['peajes'])
                if res.get('dietas', 0) > 0:
                    extras_cols.append("Dietas")
                    extras_vals.append(res['dietas'])
                if res.get('hoteles', 0) > 0:
                    extras_cols.append("Hoteles")
                    extras_vals.append(res['hoteles'])
                if res.get('otros', 0) > 0:
                    extras_cols.append("Otros")
                    extras_vals.append(res['otros'])

                if extras_cols:
                    cols = st.columns(len(extras_cols))
                    for i, col in enumerate(cols):
                        with col:
                            st.metric(extras_cols[i], f"{extras_vals[i]:.0f} €")

                # Desglose km
                km_desg = res.get('km_desglose', {})
                if km_desg:
                    # Calcular total real desde desglose
                    km_total_real = km_desg.get('pos_ida', 0) + km_desg.get('servicio', 0) + km_desg.get('pos_vuelta', 0)
                    st.markdown("**Kilometros por tramo**")
                    st.markdown(f"""
                    <div style="font-size:13px;background:#f5f5f5;padding:10px;border-radius:8px;">
                        <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
                            <span>🚌→📍 Pos. ida:</span><strong>{km_desg.get('pos_ida', 0)} km</strong>
                        </div>
                        <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
                            <span>📍→🏁 Servicio:</span><strong>{km_desg.get('servicio', 0)} km</strong>
                        </div>
                        <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
                            <span>🏁→🚌 Pos. vuelta:</span><strong>{km_desg.get('pos_vuelta', 0)} km</strong>
                        </div>
                        <div style="display:flex;justify-content:space-between;border-top:1px solid #ddd;padding-top:5px;margin-top:5px;">
                            <span><strong>TOTAL:</strong></span><strong style="color:#1976D2;">{km_total_real} km</strong>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                # Desglose tiempos
                tiempo_desg = res.get('tiempo_desglose', {})
                if tiempo_desg:
                    def min_to_hm(minutos):
                        """Convierte minutos a formato Xh Ym"""
                        h = int(minutos // 60)
                        m = int(minutos % 60)
                        if h > 0 and m > 0:
                            return f"{h}h {m}m"
                        elif h > 0:
                            return f"{h}h"
                        else:
                            return f"{m}m"

                    hora_estimada = tiempo_desg.get('hora_estimada_llegada')
                    indice = tiempo_desg.get('indice_pesado', 1.2)

                    st.markdown(f"**Tiempos por tramo** <span style='font-size:11px;color:#666;'>(índice veh. pesado: x{indice:.2f})</span>", unsafe_allow_html=True)
                    st.markdown(f"""
                    <div style="font-size:13px;background:#FFF3E0;padding:10px;border-radius:8px;border-left:3px solid #FF9800;">
                        <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
                            <span>🚌→📍 Pos. ida:</span><strong>{min_to_hm(tiempo_desg.get('pos_ida_min', 0))}</strong>
                        </div>
                        <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
                            <span>⏱️ Presentación:</span><strong>{tiempo_desg.get('presentacion_min', 0)}m</strong>
                        </div>
                        <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
                            <span>📍→🏁 Servicio:</span><strong>{min_to_hm(tiempo_desg.get('servicio_manual_min', 0))}</strong>
                        </div>
                        <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
                            <span>🏁→🚌 Pos. vuelta:</span><strong>{min_to_hm(tiempo_desg.get('pos_vuelta_min', 0))}</strong>
                        </div>
                        <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
                            <span>🧹 Limpieza:</span><strong>{tiempo_desg.get('limpieza_min', 0)}m</strong>
                        </div>
                        <div style="display:flex;justify-content:space-between;border-top:1px solid #FFB74D;padding-top:5px;margin-top:5px;">
                            <span><strong>TOTAL:</strong></span><strong style="color:#E65100;">{min_to_hm(tiempo_desg.get('total_min', 0))}</strong>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Hora estimada de llegada
                    if hora_estimada:
                        st.markdown(f"""
                        <div style="background:#E8F5E9;padding:10px;border-radius:8px;margin-top:10px;text-align:center;">
                            <span style="font-size:12px;color:#666;">Hora estimada llegada destino</span><br>
                            <span style="font-size:24px;font-weight:bold;color:#2E7D32;">🕐 {hora_estimada}</span>
                        </div>
                        """, unsafe_allow_html=True)

                # Info tarifa
                origen_tarifa = res['desglose'].get('origen', 'bus')
                if origen_tarifa == 'cliente':
                    st.success(f"✨ Tarifa personalizada: {cliente}")
                elif origen_tarifa == 'servicio':
                    st.info("Tarifa por tipo de servicio")
                else:
                    st.info(f"Tarifa base: {tipo_bus_sel}")
            else:
                # Estado vacio
                st.markdown("""
                <div style="text-align:center;padding:40px 20px;color:#999;">
                    <div style="font-size:48px;margin-bottom:15px;">🧮</div>
                    <p style="margin:0;font-size:14px;">Completa el formulario y pulsa<br><strong>CALCULAR PRESUPUESTO</strong></p>
                </div>
                """, unsafe_allow_html=True)

                # Resumen de lo seleccionado
                if st.session_state.get('calc_origen_dir') or st.session_state.get('calc_destino_dir'):
                    st.markdown("---")
                    st.markdown("**Resumen actual:**")
                    if st.session_state.get('calc_origen_dir'):
                        st.markdown(f"📍 **Origen:** {st.session_state.get('calc_origen_nombre', 'Seleccionado')}")
                    if st.session_state.calc_paradas:
                        st.markdown(f"⬤ **Paradas:** {len(st.session_state.calc_paradas)}")
                    if st.session_state.get('calc_destino_dir'):
                        st.markdown(f"🏁 **Destino:** {st.session_state.get('calc_destino_nombre', 'Seleccionado')}")

# ============================================
# PAGINA 9: TARIFAS - CONFIGURACION
# ============================================
elif pagina == "Tarifas":
    st.title("Gestión de Tarifas")
    st.caption("Configura tarifas y gestiona clientes VIP")

    tipos_servicio_guardados = obtener_tipos_servicio_db()

    # 3 TABS: Configuración, VIP, Informes
    tab_config, tab_vip, tab_informes = st.tabs([
        "Configuracion", "Clientes VIP", "Informes"
    ])

    # ========== TAB CONFIGURACION - CON EXPANDERS ==========
    with tab_config:
        # Sub-tabs para mejor organización
        cfg_tab1, cfg_tab2, cfg_tab3, cfg_tab4 = st.tabs([
            "Temporadas", "Buses", "Segmentos", "Tarifas Servicio"
        ])

        # -------- TAB: TEMPORADAS --------
        with cfg_tab1:
            st.markdown("#### Temporadas y Multiplicadores")
            st.caption("Define multiplicadores de precio según la época del año. Usa el calendario para seleccionar las fechas.")

            temporadas_cfg = obtener_temporadas()

            # Mostrar temporadas existentes con estilo visual
            if temporadas_cfg:
                for t in temporadas_cfg:
                    mult = float(t['multiplicador'])
                    if mult < 1:
                        color_bg = "#E8F5E9"
                        color_border = "#4CAF50"
                        badge = "🔽 Baja"
                    elif mult > 1:
                        color_bg = "#FFF3E0"
                        color_border = "#FF9800"
                        badge = "🔼 Alta"
                    else:
                        color_bg = "#F5F5F5"
                        color_border = "#9E9E9E"
                        badge = "➖ Normal"

                    st.markdown(f"""
                    <div style="background: {color_bg}; border-left: 4px solid {color_border}; padding: 12px 16px; border-radius: 8px; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong style="font-size: 16px;">{t['nombre']}</strong>
                                <span style="margin-left: 10px; background: {color_border}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px;">{badge}</span>
                            </div>
                            <div style="font-size: 24px; font-weight: bold; color: {color_border};">x{mult:.2f}</div>
                        </div>
                        <div style="color: #666; margin-top: 5px;">📅 {t['fecha_inicio']} → {t['fecha_fin']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button(f"🗑️ Eliminar {t['nombre']}", key=f"del_temp_{t['codigo']}"):
                        eliminar_temporada(t['codigo'])
                        st.rerun()
            else:
                st.info("No hay temporadas definidas. Añade una nueva o carga las de ejemplo.")

            st.markdown("---")
            st.markdown("##### Añadir Nueva Temporada")

            col_nt1, col_nt2 = st.columns(2)
            with col_nt1:
                new_temp_cod = st.text_input("Código", placeholder="ALTA", key="new_temp_cod", help="Código único (ej: ALTA, BAJA, NAVIDAD)")
                new_temp_nom = st.text_input("Nombre", placeholder="Temporada Alta", key="new_temp_nom")
                new_temp_mult = st.slider("Multiplicador", min_value=0.50, max_value=2.00, value=1.00, step=0.05, key="new_temp_mult",
                                          help="< 1.0 = descuento, 1.0 = normal, > 1.0 = recargo")
                mult_preview = new_temp_mult
                if mult_preview < 1:
                    st.success(f"🔽 Descuento del {(1-mult_preview)*100:.0f}%")
                elif mult_preview > 1:
                    st.warning(f"🔼 Recargo del {(mult_preview-1)*100:.0f}%")
                else:
                    st.info("➖ Precio normal (sin ajuste)")

            with col_nt2:
                st.markdown("**Rango de fechas:**")
                # Usar date_input con calendario
                año_actual = datetime.now().year
                fecha_ini_default = datetime(año_actual, 6, 15)
                fecha_fin_default = datetime(año_actual, 9, 15)

                new_temp_fecha_ini = st.date_input("Fecha de inicio", value=fecha_ini_default, key="new_temp_ini_cal", format="DD/MM/YYYY")
                new_temp_fecha_fin = st.date_input("Fecha de fin", value=fecha_fin_default, key="new_temp_fin_cal", format="DD/MM/YYYY")

                # Convertir a formato MM-DD
                fecha_ini_str = new_temp_fecha_ini.strftime("%m-%d")
                fecha_fin_str = new_temp_fecha_fin.strftime("%m-%d")

                st.caption(f"Se guardará como: {fecha_ini_str} → {fecha_fin_str}")

                if st.button("💾 Guardar Temporada", key="btn_save_temp", type="primary"):
                    if new_temp_cod and new_temp_nom:
                        guardar_temporada(new_temp_cod.upper(), new_temp_nom, fecha_ini_str, fecha_fin_str, new_temp_mult)
                        st.success(f"✅ Temporada '{new_temp_nom}' guardada")
                        st.rerun()
                    else:
                        st.error("Completa código y nombre")

            if not temporadas_cfg:
                st.markdown("---")
                if st.button("📥 Cargar Temporadas de Ejemplo", key="btn_temp_ejemplo", type="secondary"):
                    guardar_temporada("BAJA", "Temporada Baja", "01-07", "03-14", 0.85)
                    guardar_temporada("MEDIA", "Temporada Media", "03-15", "06-14", 1.0)
                    guardar_temporada("ALTA", "Temporada Alta", "06-15", "09-15", 1.25)
                    guardar_temporada("NAVIDAD", "Navidad", "12-15", "01-06", 1.15)
                    st.success("✅ Temporadas de ejemplo cargadas")
                    st.rerun()

        # -------- TAB: TIPOS DE BUS --------
        with cfg_tab2:
            st.markdown("#### Tipos de Bus")
            st.caption("Configura precios de venta y costes operativos (del Observatorio de Viajeros)")

            tipos_bus_cfg = obtener_tipos_bus()

            # Mostrar tabla de buses existentes
            if tipos_bus_cfg:
                import pandas as pd
                df_buses = pd.DataFrame([
                    {
                        'Nombre': b['nombre'],
                        'Plazas': b['capacidad'],
                        'Precio €/h': f"{b['precio_base_hora']:.2f}",
                        'Precio €/km': f"{b['precio_base_km']:.2f}",
                        'Coste €/km': f"{b.get('coste_km', 0.85):.2f}",
                        'Coste €/h': f"{b.get('coste_hora', 30.0):.2f}",
                        'Código': b['codigo']
                    }
                    for b in sorted(tipos_bus_cfg, key=lambda x: x['capacidad'])
                ])
                st.dataframe(df_buses, use_container_width=True, hide_index=True)

                # Selector para eliminar
                bus_a_eliminar = st.selectbox(
                    "Eliminar bus:",
                    [""] + [f"{b['nombre']} ({b['codigo']})" for b in tipos_bus_cfg],
                    key="sel_del_bus"
                )
                if bus_a_eliminar and st.button("🗑️ Confirmar eliminación", key="btn_del_bus"):
                    codigo = bus_a_eliminar.split("(")[-1].replace(")", "")
                    eliminar_tipo_bus(codigo)
                    st.rerun()
            else:
                st.info("No hay tipos de bus definidos")

            st.markdown("---")
            st.markdown("##### Añadir nuevo bus")

            col_bus_1, col_bus_2 = st.columns(2)
            with col_bus_1:
                st.markdown("**Datos básicos:**")
                new_bus_cod = st.text_input("Código", placeholder="AUTOCAR_55", key="new_bus_cod_cfg2")
                new_bus_nom = st.text_input("Nombre", placeholder="Autocar 55 plazas", key="new_bus_nom_cfg2")
                new_bus_cap = st.number_input("Plazas", min_value=1, value=55, key="new_bus_cap_cfg2")

            with col_bus_2:
                st.markdown("**Precios de venta:**")
                new_bus_hora = st.number_input("Precio €/Hora", min_value=0.0, value=60.0, step=5.0, key="new_bus_hora_cfg2")
                new_bus_km = st.number_input("Precio €/Km", min_value=0.0, value=1.30, step=0.05, key="new_bus_km_cfg2")

            st.markdown("**Costes operativos** (Observatorio de Viajeros):")
            col_coste1, col_coste2 = st.columns(2)
            with col_coste1:
                new_bus_coste_km = st.number_input("Coste €/Km", min_value=0.0, value=0.85, step=0.05, key="new_bus_coste_km",
                                                    help="Combustible, mantenimiento, neumáticos")
            with col_coste2:
                new_bus_coste_hora = st.number_input("Coste €/Hora", min_value=0.0, value=30.0, step=1.0, key="new_bus_coste_hora",
                                                      help="Conductor, seguros, amortización")

            # Mostrar margen estimado
            if new_bus_km > 0 and new_bus_hora > 0:
                margen_km = ((new_bus_km - new_bus_coste_km) / new_bus_km) * 100
                margen_hora = ((new_bus_hora - new_bus_coste_hora) / new_bus_hora) * 100
                st.info(f"📊 Margen estimado: **{margen_km:.0f}%** por km | **{margen_hora:.0f}%** por hora")

            if st.button("💾 Guardar Bus", key="btn_save_bus_cfg2", type="primary"):
                if new_bus_cod and new_bus_nom:
                    guardar_tipo_bus(new_bus_cod.upper(), new_bus_nom, new_bus_cap, new_bus_hora, new_bus_km,
                                    new_bus_coste_km, new_bus_coste_hora)
                    st.success(f"✅ Bus '{new_bus_nom}' guardado")
                    st.rerun()
                else:
                    st.error("Completa código y nombre")

        # -------- TAB: SEGMENTOS DE CLIENTE --------
        with cfg_tab3:
            st.markdown("#### Segmentos de Cliente")

            tipos_cli_cfg = obtener_tipos_cliente()

            if tipos_cli_cfg:
                import pandas as pd
                df_cli = pd.DataFrame([
                    {
                        'Nombre': c['nombre'],
                        'Multiplicador': f"x{float(c['multiplicador']):.2f}",
                        'Efecto': f"{(float(c['multiplicador'])-1)*100:+.0f}%" if float(c['multiplicador']) != 1 else "base",
                        'Código': c['codigo']
                    }
                    for c in tipos_cli_cfg
                ])
                st.dataframe(df_cli, use_container_width=True, hide_index=True)

                # Selector para eliminar
                cli_a_eliminar = st.selectbox(
                    "Eliminar segmento:",
                    [""] + [f"{c['nombre']} ({c['codigo']})" for c in tipos_cli_cfg],
                    key="sel_del_cli"
                )
                if cli_a_eliminar and st.button("🗑️ Confirmar eliminación", key="btn_del_cli"):
                    codigo = cli_a_eliminar.split("(")[-1].replace(")", "")
                    eliminar_tipo_cliente(codigo)
                    st.rerun()
            else:
                st.info("No hay segmentos definidos")

            st.markdown("---")
            st.markdown("##### Añadir nuevo segmento")
            col_nc1, col_nc2, col_nc3 = st.columns([2, 2, 1])
            with col_nc1:
                new_cli_cod = st.text_input("Código", placeholder="EMPRESA", key="new_cli_cod2")
            with col_nc2:
                new_cli_nom = st.text_input("Nombre", placeholder="Empresa", key="new_cli_nom2")
            with col_nc3:
                new_cli_mult = st.number_input("Multiplicador", min_value=0.5, max_value=2.0, value=1.0, step=0.05, key="new_cli_mult2")

            if st.button("💾 Guardar Segmento", key="btn_save_cli2", type="primary"):
                if new_cli_cod and new_cli_nom:
                    guardar_tipo_cliente(new_cli_cod.upper(), new_cli_nom, new_cli_mult)
                    st.success(f"✅ Segmento '{new_cli_nom}' guardado")
                    st.rerun()
                else:
                    st.error("Completa código y nombre")

        # -------- TAB: TARIFAS POR SERVICIO --------
        with cfg_tab4:
            st.markdown("#### Tarifas por Tipo de Servicio")

            tarifas_srv_cfg = obtener_tarifas_servicio()

            if tarifas_srv_cfg:
                import pandas as pd
                df_tar = pd.DataFrame([
                    {
                        'Servicio': t['tipo_servicio'],
                        'Bus': t['tipo_bus'],
                        'Base €': f"{t['precio_base']:.0f}",
                        '€/Hora': f"{t['precio_hora']:.2f}",
                        '€/Km': f"{t['precio_km']:.2f}",
                        'ID': t['id']
                    }
                    for t in tarifas_srv_cfg
                ])
                st.dataframe(df_tar, use_container_width=True, hide_index=True)

                # Selector para eliminar
                tar_a_eliminar = st.selectbox(
                    "Eliminar tarifa:",
                    [""] + [f"{t['tipo_servicio']} + {t['tipo_bus']} (ID:{t['id']})" for t in tarifas_srv_cfg],
                    key="sel_del_tar"
                )
                if tar_a_eliminar and st.button("🗑️ Confirmar eliminación", key="btn_del_tar"):
                    id_tar = int(tar_a_eliminar.split("ID:")[-1].replace(")", ""))
                    eliminar_tarifa_servicio(id_tar)
                    st.rerun()
            else:
                st.info("No hay tarifas por servicio definidas")

            st.markdown("---")
            st.markdown("##### Añadir nueva tarifa")

            tipos_srv = obtener_tipos_servicio_db()
            tipos_bus_list = [b['codigo'] for b in obtener_tipos_bus()]

            col_nts1, col_nts2, col_nts3, col_nts4, col_nts5 = st.columns([2, 2, 1, 1, 1])
            with col_nts1:
                new_ts_srv = st.selectbox("Servicio", list(tipos_srv.keys()) if tipos_srv else [""], key="new_ts_srv2")
            with col_nts2:
                new_ts_bus = st.selectbox("Bus", tipos_bus_list if tipos_bus_list else [""], key="new_ts_bus2")
            with col_nts3:
                new_ts_base = st.number_input("Base €", min_value=0.0, value=0.0, key="new_ts_base2")
            with col_nts4:
                new_ts_hora = st.number_input("€/Hora", min_value=0.0, value=50.0, key="new_ts_hora2")
            with col_nts5:
                new_ts_km = st.number_input("€/Km", min_value=0.0, value=1.20, key="new_ts_km2")

            if st.button("💾 Guardar Tarifa", key="btn_save_ts2", type="primary"):
                if new_ts_srv and new_ts_bus:
                    guardar_tarifa_servicio(new_ts_srv, new_ts_bus, new_ts_base, new_ts_hora, new_ts_km)
                    st.success(f"✅ Tarifa guardada")
                    st.rerun()
                else:
                    st.error("Selecciona servicio y bus")

    # ========== TAB CLIENTES VIP ==========
    with tab_vip:
        st.markdown("### Tarifas Personalizadas por Cliente")
        st.caption("Define precios especiales para clientes individuales")

        col_vip1, col_vip2 = st.columns([1, 1])

        with col_vip1:
            st.markdown("#### Nueva Tarifa")
            clientes_vip = sorted(df['Cliente'].dropna().unique().tolist())
            tipos_bus_vip = obtener_tipos_bus()
            tipos_bus_dict_vip = {"* (Todos)": "*"}
            tipos_bus_dict_vip.update({b['nombre']: b['codigo'] for b in tipos_bus_vip})

            vip_cliente = st.selectbox("Cliente", clientes_vip, key="vip_cliente")
            vip_bus = st.selectbox("Tipo de Bus", list(tipos_bus_dict_vip.keys()), key="vip_bus")

            col_v1, col_v2 = st.columns(2)
            with col_v1:
                vip_hora = st.number_input("€/Hora", min_value=0.0, value=0.0, key="vip_hora")
            with col_v2:
                vip_km = st.number_input("€/Km", min_value=0.0, value=0.0, key="vip_km")

            vip_notas = st.text_area("Notas", key="vip_notas", placeholder="Motivo del precio especial...")

            if st.button("Guardar Tarifa VIP", type="primary", key="btn_vip_save"):
                bus_code = tipos_bus_dict_vip[vip_bus]
                guardar_tarifa_cliente(
                    vip_cliente,
                    bus_code if bus_code != "*" else None,
                    None,
                    vip_hora if vip_hora > 0 else None,
                    vip_km if vip_km > 0 else None,
                    vip_notas
                )
                st.success("Tarifa guardada")
                st.rerun()

        with col_vip2:
            st.markdown("#### Tarifas Activas")
            buscar_vip = st.text_input("Buscar cliente...", key="buscar_vip")

            tarifas_vip = obtener_tarifas_cliente()
            if tarifas_vip:
                if buscar_vip:
                    tarifas_vip = [t for t in tarifas_vip if buscar_vip.lower() in t['cliente'].lower()]

                for t in tarifas_vip[:15]:
                    st.markdown(f"""
                    <div style="background: #FCE4EC; padding: 10px; border-radius: 6px; margin-bottom: 6px; border-left: 3px solid #E91E63;">
                        <b>{t['cliente'][:35]}...</b><br>
                        <small>{t['precio_hora']:.2f}€/h | {t['precio_km']:.2f}€/km</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No hay tarifas personalizadas")

    # ========== TAB INFORMES ==========
    with tab_informes:
        st.markdown("### Generar Informe PDF")
        st.caption("Exporta las tarifas configuradas a PDF")

        col_inf1, col_inf2 = st.columns([1, 1])

        with col_inf1:
            st.markdown("#### Opciones")
            inc_temp = st.checkbox("Incluir Temporadas", value=True, key="pdf_inc_temp")
            inc_buses = st.checkbox("Incluir Tipos de Bus", value=True, key="pdf_inc_buses")
            inc_cli = st.checkbox("Incluir Tipos de Cliente", value=True, key="pdf_inc_cli")
            inc_srv = st.checkbox("Incluir Tarifas Servicio", value=True, key="pdf_inc_srv")
            inc_vip = st.checkbox("Incluir Tarifas VIP", value=True, key="pdf_inc_vip")

            st.markdown("---")
            pdf_empresa = st.text_input("Empresa", value="Autocares David", key="pdf_empresa_new")
            pdf_fecha = st.date_input("Fecha vigencia", value=datetime.now(), key="pdf_fecha_new")

        with col_inf2:
            st.markdown("#### Vista Previa")
            temp_pdf = obtener_temporadas() if inc_temp else []
            buses_pdf = obtener_tipos_bus() if inc_buses else []
            cli_pdf = obtener_tipos_cliente() if inc_cli else []
            srv_pdf = obtener_tarifas_servicio() if inc_srv else []
            vip_pdf = obtener_tarifas_cliente() if inc_vip else []

            st.markdown(f"""
            <div style="background: #F5F5F5; padding: 15px; border-radius: 8px;">
                <b>{pdf_empresa}</b><br>
                Vigencia: {pdf_fecha}<br><br>
                Temporadas: {len(temp_pdf)}<br>
                Tipos Bus: {len(buses_pdf)}<br>
                Segmentos: {len(cli_pdf)}<br>
                Tarifas Servicio: {len(srv_pdf)}<br>
                Tarifas VIP: {len(vip_pdf)}
            </div>
            """, unsafe_allow_html=True)

        if st.button("Generar PDF", type="primary", key="btn_gen_pdf_new", use_container_width=True):
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)

            # Portada
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 24)
            pdf.cell(0, 60, "", ln=True)
            pdf.cell(0, 15, pdf_empresa, ln=True, align="C")
            pdf.set_font("Helvetica", "", 18)
            pdf.cell(0, 15, "TARIFAS DE SERVICIOS", ln=True, align="C")
            pdf.set_font("Helvetica", "", 14)
            pdf.cell(0, 10, f"Vigencia: {pdf_fecha.strftime('%d/%m/%Y')}", ln=True, align="C")

            # Tipos de Bus
            if inc_buses and buses_pdf:
                pdf.add_page()
                pdf.set_font("Helvetica", "B", 16)
                pdf.cell(0, 12, "TIPOS DE VEHICULO", ln=True)
                pdf.set_font("Helvetica", "", 10)
                for b in sorted(buses_pdf, key=lambda x: x['capacidad']):
                    pdf.cell(0, 7, f"{b['nombre']} ({b['capacidad']} plz): {b['precio_base_hora']:.2f} EUR/h, {b['precio_base_km']:.2f} EUR/km", ln=True)

            # Temporadas
            if inc_temp and temp_pdf:
                pdf.add_page()
                pdf.set_font("Helvetica", "B", 16)
                pdf.cell(0, 12, "TEMPORADAS", ln=True)
                pdf.set_font("Helvetica", "", 10)
                for t in temp_pdf:
                    pdf.cell(0, 7, f"{t['nombre']}: {t['fecha_inicio']} a {t['fecha_fin']} (x{t['multiplicador']:.2f})", ln=True)

            pdf_output = pdf.output()
            st.success("PDF generado!")
            st.download_button(
                "Descargar PDF",
                data=pdf_output,
                file_name=f"tarifas_{pdf_empresa.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )


# ============================================
# PÁGINA 9: CONFIGURACIÓN
# ============================================
elif pagina == "Configuracion":
    st.title("Configuracion")
    st.markdown("---")

    st.subheader("Definir Tipos de Servicio")
    st.write("Asigna una descripcion a cada codigo de tipo de servicio para que aparezca en los graficos.")

    # Obtener tipos existentes de la base de datos
    tipos_guardados = obtener_tipos_servicio_db()

    # Obtener todos los códigos únicos de los datos
    codigos_en_datos = sorted(df['Tipo Servicio'].dropna().unique().tolist())

    # Contar presupuestos por código
    conteo_codigos = df['Tipo Servicio'].value_counts().to_dict()

    # Tabs para organizar
    tab1, tab2 = st.tabs(["Editar Tipos", "Ver Todos"])

    with tab1:
        # Mostrar todos los códigos ordenados por frecuencia
        todos_codigos = sorted(conteo_codigos.items(), key=lambda x: x[1], reverse=True)
        todos_codigos = [(c, q) for c, q in todos_codigos if pd.notna(c)]

        st.write(f"**Todos los codigos ({len(todos_codigos)}):**")

        # Filtro de búsqueda
        buscar = st.text_input("Buscar codigo...", placeholder="Escribe para filtrar")

        if buscar:
            todos_codigos = [(c, q) for c, q in todos_codigos if buscar.upper() in str(c).upper()]

        # Formulario para editar
        with st.form("form_tipos"):
            cambios = {}

            for codigo, cantidad in todos_codigos:
                col1, col2, col3 = st.columns([1, 3, 1])

                with col1:
                    st.text(f"{codigo}")

                with col2:
                    valor_actual = tipos_guardados.get(codigo, {}).get('descripcion', '')
                    nueva_desc = st.text_input(
                        f"Descripcion para {codigo}",
                        value=valor_actual,
                        key=f"desc_{codigo}",
                        label_visibility="collapsed",
                        placeholder=f"Descripcion para {codigo}..."
                    )
                    cambios[codigo] = nueva_desc

                with col3:
                    st.caption(f"{cantidad:,} presup.")

            submitted = st.form_submit_button("Guardar Cambios", type="primary")

            if submitted:
                guardados = 0
                for codigo, descripcion in cambios.items():
                    if descripcion:  # Solo guardar si hay descripción
                        # Normalizar: Primera mayúscula, resto minúsculas
                        descripcion_normalizada = descripcion.strip().capitalize()
                        guardar_tipo_servicio(codigo, descripcion_normalizada)
                        guardados += 1
                st.success(f"Se guardaron {guardados} tipos de servicio")
                st.rerun()

    with tab2:
        st.write("**Todos los codigos definidos:**")

        if tipos_guardados:
            datos_tabla = []
            for codigo, datos in tipos_guardados.items():
                cantidad = conteo_codigos.get(codigo, 0)
                datos_tabla.append({
                    'Codigo': codigo,
                    'Descripcion': datos['descripcion'],
                    'Categoria': datos['categoria'],
                    'Presupuestos': cantidad
                })

            df_tipos = pd.DataFrame(datos_tabla)
            df_tipos = df_tipos.sort_values('Presupuestos', ascending=False)
            st.dataframe(df_tipos, width="stretch", height=400)

            # Exportar
            csv = df_tipos.to_csv(index=False).encode('utf-8')
            st.download_button("Exportar tipos definidos", csv, "tipos_servicio.csv", "text/csv")
        else:
            st.info("No hay tipos de servicio definidos todavia")

        st.markdown("---")

        # Códigos sin definir
        st.write("**Codigos SIN definir:**")
        sin_definir = [c for c in codigos_en_datos if c not in tipos_guardados and pd.notna(c)]
        if sin_definir:
            sin_definir_con_cantidad = [(c, conteo_codigos.get(c, 0)) for c in sin_definir]
            sin_definir_con_cantidad.sort(key=lambda x: x[1], reverse=True)

            for codigo, cantidad in sin_definir_con_cantidad[:20]:
                st.text(f"{codigo}: {cantidad:,} presupuestos")
        else:
            st.success("Todos los codigos tienen descripcion")

    # ============================================
    # SECCIÓN: CLIENTES DESACTIVADOS
    # ============================================
    st.markdown("---")
    st.subheader("Clientes Desactivados")
    st.caption("Los clientes desactivados no aparecen en ninguna parte de la aplicacion (estadisticas, calculos, listas, etc.)")

    # Cargar datos originales sin filtrar para poder ver todos los clientes
    df_todos_clientes = cargar_datos()
    todos_los_clientes = sorted(df_todos_clientes['Cliente'].dropna().unique().tolist())
    clientes_desactivados_actual = obtener_clientes_desactivados()

    col_desact1, col_desact2 = st.columns(2)

    with col_desact1:
        st.write("**Desactivar clientes:**")
        # Filtrar los que ya están desactivados
        clientes_activos = [c for c in todos_los_clientes if c not in clientes_desactivados_actual]
        clientes_a_desactivar = st.multiselect(
            "Selecciona clientes",
            options=clientes_activos,
            key="sel_desactivar_clientes",
            placeholder="Busca y selecciona clientes..."
        )
        motivo_desactivacion = st.text_input("Motivo (opcional)", key="motivo_desact")

        if st.button("Desactivar seleccionados", type="primary", disabled=len(clientes_a_desactivar) == 0):
            errores = 0
            for cliente in clientes_a_desactivar:
                if not desactivar_cliente(cliente, motivo_desactivacion):
                    errores += 1
            if errores == 0:
                st.success(f"{len(clientes_a_desactivar)} cliente(s) desactivado(s)")
            else:
                st.warning(f"Desactivados {len(clientes_a_desactivar) - errores}, errores: {errores}")
            st.rerun()

    with col_desact2:
        st.write(f"**Clientes desactivados ({len(clientes_desactivados_actual)}):**")
        if clientes_desactivados_actual:
            # Opción para reactivar todos
            if st.button("Reactivar todos", type="secondary"):
                for cliente in list(clientes_desactivados_actual.keys()):
                    reactivar_cliente(cliente)
                st.success("Todos los clientes reactivados")
                st.rerun()

            st.markdown("---")
            for cliente, datos in sorted(clientes_desactivados_actual.items()):
                c1, c2, c3 = st.columns([3, 2, 1])
                with c1:
                    st.write(f"**{cliente}**")
                with c2:
                    fecha_str = datos.get('fecha', '')[:10] if datos.get('fecha') else ''
                    st.caption(f"{datos.get('motivo', '-')} | {fecha_str}")
                with c3:
                    if st.button("X", key=f"react_{cliente}", help="Reactivar"):
                        reactivar_cliente(cliente)
                        st.rerun()
        else:
            st.info("No hay clientes desactivados")

# ============================================
# PÁGINA: ADMIN (Solo para administradores)
# ============================================
elif pagina == "Admin":
    panel_admin()

# Carga de archivos Excel - Modal
import os
directorio_actual = os.path.dirname(os.path.abspath(__file__))
IMPORT_DATES_FILE = os.path.join(directorio_actual, "import_dates.json")

def cargar_fechas_importacion():
    """Carga las fechas de última importación de cada archivo."""
    if os.path.exists(IMPORT_DATES_FILE):
        with open(IMPORT_DATES_FILE, 'r') as f:
            return json.load(f)
    return {}

def guardar_fecha_importacion(archivo, fecha):
    """Guarda la fecha de importación de un archivo."""
    fechas = cargar_fechas_importacion()
    fechas[archivo] = fecha
    with open(IMPORT_DATES_FILE, 'w') as f:
        json.dump(fechas, f)

def actualizar_excel(ruta_existente, df_nuevo, clave):
    """Actualiza un Excel existente con nuevos datos (merge por clave)."""
    if os.path.exists(ruta_existente):
        try:
            df_existente = pd.read_excel(ruta_existente)
            if len(df_existente) > 0 and clave in df_existente.columns and clave in df_nuevo.columns:
                # Eliminar registros existentes que están en el nuevo
                claves_nuevas = df_nuevo[clave].dropna().unique()
                df_existente = df_existente[~df_existente[clave].isin(claves_nuevas)]
                # Combinar
                df_combinado = pd.concat([df_existente, df_nuevo], ignore_index=True)
                return df_combinado
        except Exception:
            pass
    return df_nuevo

@st.dialog("Actualizar Datos")
def modal_actualizar_datos():
    # Mostrar fechas de última importación
    fechas = cargar_fechas_importacion()

    st.markdown("**Última importación:**")
    col1, col2 = st.columns(2)
    col1.caption(f"todos: {fechas.get('todos.xlsx', 'Nunca')}")
    col1.caption(f"Clientes: {fechas.get('Clientes.xlsx', 'Nunca')}")
    col2.caption(f"Localizar: {fechas.get('Localizar presupuestos', 'Nunca')}")
    col2.caption(f"Servicios: {fechas.get('Servicios Discrecionales', 'Nunca')}")

    # Botón limpiar caché
    if st.button("🔄 Limpiar caché y recargar", use_container_width=True, type="secondary"):
        st.cache_data.clear()
        st.success("Caché limpiada")
        st.rerun()

    st.markdown("---")

    archivo_tipo = st.radio(
        "Selecciona archivo:",
        ["todos.xlsx", "Clientes.xlsx", "Localizar presupuestos", "Servicios Discrecionales"],
        horizontal=True
    )

    # Instrucciones según el archivo seleccionado
    if archivo_tipo == "todos.xlsx":
        st.info("**Comercial → Presupuestos → Exportar detallado**\n\nRenombrar como 'todos'. Eliminar filtros para exportar todos los datos.")
    elif archivo_tipo == "Clientes.xlsx":
        st.info("**Clientes → Exportar**\n\nMantener el nombre del fichero.")
    elif archivo_tipo == "Localizar presupuestos":
        st.info("**Comercial → Localizar → Exportar**\n\nNo cambiar el nombre.")
    elif archivo_tipo == "Servicios Discrecionales":
        st.info("**Tráfico → Servicios Discrecionales → Exportar**\n\nSe usa para completar códigos de cliente faltantes.")

    archivo = st.file_uploader("", type=['xlsx'], key="upload_modal", label_visibility="collapsed")

    if archivo:
        # Determinar nombre de archivo y clave para merge
        if archivo_tipo == "Localizar presupuestos":
            nombre_archivo = "Localizar presupuestos a partir de servicios.xlsx"
            clave = "Presupuesto"
        elif archivo_tipo == "todos.xlsx":
            nombre_archivo = "todos.xlsx"
            clave = "Cod. Presupuesto"
        elif archivo_tipo == "Servicios Discrecionales":
            nombre_archivo = "Servicios Discrecionales.xlsx"
            clave = "Código"
        else:
            nombre_archivo = "Clientes.xlsx"
            clave = "Código"

        ruta = os.path.join(directorio_actual, nombre_archivo)

        # Leer nuevo archivo
        df_nuevo = pd.read_excel(archivo)
        registros_nuevos = len(df_nuevo)

        # Actualizar (merge) con datos existentes
        df_actualizado = actualizar_excel(ruta, df_nuevo, clave)
        registros_totales = len(df_actualizado)

        # Guardar
        df_actualizado.to_excel(ruta, index=False)

        # Guardar fecha de importación
        fecha_actual = datetime.now().strftime('%d/%m/%Y %H:%M')
        guardar_fecha_importacion(archivo_tipo, fecha_actual)

        st.success(f"Actualizado: {archivo_tipo}")
        st.caption(f"Registros importados: {registros_nuevos} | Total: {registros_totales}")
        st.cache_data.clear()

        if st.button("Cerrar", use_container_width=True):
            st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("📂 Actualizar Datos", use_container_width=True, type="primary"):
    modal_actualizar_datos()

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("CRM v1.0")
st.sidebar.caption(f"Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
