"""
Aplicación Completa de Análisis de Costes - Autocares David
Sistema integral para gestión y análisis de costes de flota
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import os
from pathlib import Path

# Importar módulos locales
import database as db
import data_loader as loader

# ============================================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================================

st.set_page_config(
    page_title="Análisis de Costes - DAVID",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Colores del brandbook DAVID
COLORS = {
    'negro': '#000000',
    'blanco': '#FFFFFF',
    'rojo': '#F15025',
    'gris_oscuro': '#333333',
    'gris_claro': '#F5F5F5',
    'gris_medio': '#666666',
    'verde': '#2E7D32',
    'naranja': '#F57C00',
    'azul': '#1976D2'
}

CHART_COLORS = ['#000000', '#F15025', '#333333', '#666666', '#999999', '#1976D2', '#2E7D32']

# CSS personalizado
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .main { background-color: #FFFFFF; }
    .stApp { font-family: 'Inter', Arial, sans-serif; }

    h1, h2, h3 { color: #000000 !important; font-weight: 600 !important; }

    [data-testid="stSidebar"] { background-color: #000000; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }

    [data-testid="stMetricValue"] {
        color: #000000 !important;
        font-size: 1.8rem !important;
        font-weight: 600 !important;
    }

    .stButton > button {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 4px !important;
    }
    .stButton > button:hover { background-color: #F15025 !important; }

    .stTabs [data-baseweb="tab"] {
        background-color: #F5F5F5;
        border-radius: 4px;
        color: #000000;
    }
    .stTabs [aria-selected="true"] {
        background-color: #000000 !important;
        color: #FFFFFF !important;
    }

    .logo-text {
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: 0.3em;
        color: #FFFFFF;
        text-align: center;
        padding: 1rem 0 2rem 0;
    }

    .category-header {
        background-color: #F5F5F5;
        padding: 0.5rem 1rem;
        border-left: 4px solid #F15025;
        margin: 1rem 0;
        font-weight: 600;
    }

    .info-box {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 4px;
        border-left: 4px solid #1976D2;
        margin: 1rem 0;
    }

    .warning-box {
        background-color: #FFF3E0;
        padding: 1rem;
        border-radius: 4px;
        border-left: 4px solid #F57C00;
        margin: 1rem 0;
    }

    .success-box {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 4px;
        border-left: 4px solid #2E7D32;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# ESTADO DE LA SESIÓN
# ============================================================================

def init_session_state():
    """Inicializa el estado de la sesión."""
    if 'ejercicio_actual' not in st.session_state:
        ejercicios = db.obtener_ejercicios()
        if ejercicios:
            st.session_state.ejercicio_actual = ejercicios[0]['año']
        else:
            st.session_state.ejercicio_actual = datetime.now().year

    if 'ejercicio_id' not in st.session_state:
        ej = db.obtener_ejercicio_por_año(st.session_state.ejercicio_actual)
        st.session_state.ejercicio_id = ej['id'] if ej else None


init_session_state()


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def format_currency(value, decimals=0):
    """Formatea un valor como moneda."""
    if pd.isna(value) or value is None:
        return "-"
    return f"{value:,.{decimals}f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def format_number(value, decimals=0):
    """Formatea un número con separadores de miles."""
    if pd.isna(value) or value is None:
        return "-"
    return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def safe_get(data, key, default=0):
    """Obtiene un valor de un diccionario o lista de forma segura."""
    if isinstance(data, list) and len(data) > 0:
        data = data[0]
    if isinstance(data, dict):
        return data.get(key, default) or default
    return default


# ============================================================================
# COMPONENTES DE VISUALIZACIÓN
# ============================================================================

def create_kpi_cards(data):
    """Crea las tarjetas de KPIs principales."""
    df = data.get('resumen_flota', pd.DataFrame())
    if df.empty:
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_vehiculos = len(df[df['coste_total'].notna()])
        st.metric("Vehículos Activos", total_vehiculos)

    with col2:
        coste_total = df['coste_total'].sum()
        st.metric("Coste Total Anual", format_currency(coste_total))

    with col3:
        coste_mensual = df['coste_mensual'].sum()
        st.metric("Coste Mensual", format_currency(coste_mensual))

    with col4:
        km_total = df['km_anual'].sum()
        st.metric("Km Totales/Año", format_number(km_total))

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if km_total > 0:
            coste_km = coste_total / km_total
            st.metric("Coste/Km Promedio", format_currency(coste_km, 3))
        else:
            st.metric("Coste/Km Promedio", "-")

    with col2:
        coste_hora = df['coste_hora'].mean()
        st.metric("Coste/Hora Promedio", format_currency(coste_hora, 2))

    with col3:
        plazas = df['plazas'].sum()
        st.metric("Plazas Totales", format_number(plazas))

    with col4:
        horas = df['horas_servicio'].sum()
        st.metric("Horas Servicio/Año", format_number(horas))


def create_cost_breakdown_chart(data):
    """Crea gráfico de distribución de costes."""
    df = data.get('resumen_flota', pd.DataFrame())
    if df.empty:
        return None

    costes_tiempo = df['costes_tiempo'].sum()
    costes_km = df['costes_km'].sum()

    # P&G para más detalle
    pyg_resumen = data.get('pyg_resumen', {})

    categories = {
        'Costes por Tiempo': costes_tiempo,
        'Costes por Km': costes_km
    }

    fig = px.pie(
        values=list(categories.values()),
        names=list(categories.keys()),
        color_discrete_sequence=[COLORS['negro'], COLORS['rojo']],
        hole=0.4
    )

    fig.update_layout(
        font_family="Inter, Arial, sans-serif",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=30, b=30, l=20, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
    )

    return fig


def create_vehicle_comparison(data, metric='coste_total'):
    """Crea gráfico de comparación entre vehículos."""
    df = data.get('resumen_flota', pd.DataFrame())
    if df.empty:
        return None

    df_valid = df[df[metric].notna()].sort_values(metric, ascending=True)

    fig = px.bar(
        df_valid,
        x=metric,
        y='matricula',
        orientation='h',
        color_discrete_sequence=[COLORS['negro']]
    )

    fig.update_layout(
        font_family="Inter, Arial, sans-serif",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_title="Coste (€)",
        yaxis_title="",
        showlegend=False,
        margin=dict(t=30, b=50, l=100, r=20)
    )
    fig.update_xaxes(gridcolor='#E0E0E0')

    return fig


def create_pyg_chart(data):
    """Crea gráfico del P&G."""
    pyg_data = data.get('pyg', [])
    if not pyg_data:
        return None

    # Agrupar por categoría
    df = pd.DataFrame(pyg_data)

    if df.empty:
        return None

    # Filtrar solo gastos principales (cuentas de 3 dígitos)
    df['importe'] = df['importe_ajustado'].abs()
    df = df[df['importe'] > 1000].sort_values('importe', ascending=False).head(15)

    fig = px.bar(
        df,
        x='importe',
        y='descripcion',
        orientation='h',
        color='categoria',
        color_discrete_map={'Gastos': COLORS['rojo'], 'Ingresos': COLORS['verde'], 'Otros': COLORS['gris_medio']}
    )

    fig.update_layout(
        font_family="Inter, Arial, sans-serif",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_title="Importe (€)",
        yaxis_title="",
        margin=dict(t=30, b=50, l=250, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig


# ============================================================================
# PÁGINAS DE LA APLICACIÓN
# ============================================================================

def page_dashboard():
    """Página principal del dashboard."""
    st.title("📊 Dashboard de Costes")

    ejercicio_id = st.session_state.ejercicio_id
    if not ejercicio_id:
        st.warning("No hay datos cargados. Por favor, importa un archivo Excel desde la sección de Configuración.")
        return

    # Cargar datos
    data = loader.obtener_datos_completos(ejercicio_id)

    if data['resumen_flota'].empty:
        st.warning("No hay datos de costes para este ejercicio. Importa datos desde Configuración.")
        return

    # KPIs
    st.markdown("### Indicadores Clave")
    create_kpi_cards(data)

    st.markdown("---")

    # Gráficos
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Distribución de Costes")
        fig = create_cost_breakdown_chart(data)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### Coste Total por Vehículo")
        fig = create_vehicle_comparison(data)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    # P&G si está disponible
    if data.get('pyg'):
        st.markdown("---")
        st.markdown("### Resumen P&G")

        pyg_resumen = data.get('pyg_resumen', {})
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Gastos", format_currency(pyg_resumen.get('total_gastos', 0)))
        with col2:
            st.metric("Total Ingresos", format_currency(pyg_resumen.get('total_ingresos', 0)))
        with col3:
            st.metric("Costes Directos", format_currency(pyg_resumen.get('costes_directos', 0)))
        with col4:
            st.metric("Costes Indirectos", format_currency(pyg_resumen.get('costes_indirectos', 0)))

        fig = create_pyg_chart(data)
        if fig:
            st.plotly_chart(fig, use_container_width=True)


def page_vehiculos():
    """Página de gestión de vehículos."""
    st.title("🚌 Gestión de Vehículos")

    ejercicio_id = st.session_state.ejercicio_id

    tabs = st.tabs(["📋 Lista de Vehículos", "🔍 Detalle Vehículo", "➕ Añadir Vehículo", "✏️ Editar Vehículo", "📥 Importar"])

    with tabs[0]:
        st.markdown("### Flota Actual")

        vehiculos = db.obtener_vehiculos()

        if not vehiculos:
            st.info("No hay vehículos registrados. Añade vehículos o importa desde Excel.")
        else:
            # Crear DataFrame para mostrar
            data = []
            for v in vehiculos:
                datos_año = db.obtener_datos_vehiculo_año(v['id'], ejercicio_id) if ejercicio_id else {}
                data.append({
                    'Matrícula': v['matricula'],
                    'Marca': v.get('marca', '') or '',
                    'Modelo': v.get('modelo', '') or '',
                    'Plazas': v['plazas'],
                    'Tipo': ['', 'Gran Turismo', 'Estándar', 'Midi', 'Mini'][v['tipo']] if v['tipo'] else '',
                    'F. Matriculación': v.get('fecha_matriculacion', '') or '',
                    'F. Baja': v.get('fecha_baja', '') or '',
                    'Estado': v.get('estado', 'A') or 'A',
                    'Km': format_number(v.get('kilometros', 0) or 0),
                    'Conductor': v.get('conductor', '') or '',
                    'Empresa': v.get('empresa', '') or '',
                    'Activo': '✓' if v['activo'] else '✗'
                })

            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Estadísticas rápidas
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Vehículos", len(vehiculos))
            with col2:
                activos = len([v for v in vehiculos if v['activo']])
                st.metric("Activos", activos)
            with col3:
                plazas_total = sum(v['plazas'] or 0 for v in vehiculos)
                st.metric("Plazas Totales", format_number(plazas_total))
            with col4:
                km_total = sum(v.get('kilometros', 0) or 0 for v in vehiculos)
                st.metric("Km Totales", format_number(km_total))

    with tabs[1]:
        st.markdown("### Detalle del Vehículo")

        vehiculos = db.obtener_vehiculos(activos_solo=False)
        if not vehiculos:
            st.info("No hay vehículos registrados.")
        else:
            vehiculo_sel = st.selectbox(
                "Seleccionar vehículo para ver detalle",
                options=vehiculos,
                format_func=lambda x: f"{x['matricula']} - {x.get('marca', '')} {x.get('modelo', '')}",
                key="vehiculo_detalle"
            )

            if vehiculo_sel:
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown("#### Identificación")
                    st.write(f"**Código:** {vehiculo_sel.get('codigo_vehiculo', '-')}")
                    st.write(f"**Matrícula:** {vehiculo_sel['matricula']}")
                    st.write(f"**Tipo Código:** {vehiculo_sel.get('tipo_codigo', '-')}")
                    st.write(f"**Bastidor:** {vehiculo_sel.get('bastidor', '-')}")
                    st.write(f"**Núm. Obra:** {vehiculo_sel.get('num_obra', '-')}")

                    st.markdown("#### Características")
                    st.write(f"**Marca:** {vehiculo_sel.get('marca', '-')}")
                    st.write(f"**Modelo:** {vehiculo_sel.get('modelo', '-')}")
                    st.write(f"**Plazas:** {vehiculo_sel['plazas']}")
                    st.write(f"**Tipo Vehículo:** {vehiculo_sel.get('vehiculo_tipo', '-')}")
                    st.write(f"**Longitud:** {vehiculo_sel.get('longitud', '-')} mm")
                    st.write(f"**Altura:** {vehiculo_sel.get('altura', '-')} mm")

                with col2:
                    st.markdown("#### Fechas")
                    st.write(f"**F. Matriculación:** {vehiculo_sel.get('fecha_matriculacion', '-')}")
                    st.write(f"**1ª Matriculación:** {vehiculo_sel.get('primera_matriculacion', '-')}")
                    st.write(f"**F. Baja:** {vehiculo_sel.get('fecha_baja', '-') or 'Activo'}")

                    st.markdown("#### Inspecciones")
                    st.write(f"**F. Final ITV:** {vehiculo_sel.get('fecha_final_itv', '-')}")
                    st.write(f"**F. Final Tacógrafo:** {vehiculo_sel.get('fecha_final_tacografo', '-')}")
                    st.write(f"**Caducidad Extintores:** {vehiculo_sel.get('caducidad_extintores', '-')}")
                    st.write(f"**Caducidad Escolar:** {vehiculo_sel.get('caducidad_escolar', '-')}")

                with col3:
                    st.markdown("#### Asignación")
                    st.write(f"**Conductor:** {vehiculo_sel.get('conductor', '-')}")
                    st.write(f"**Código Conductor:** {vehiculo_sel.get('codigo_conductor', '-')}")
                    st.write(f"**Empresa:** {vehiculo_sel.get('empresa', '-')}")
                    st.write(f"**Código Empresa:** {vehiculo_sel.get('codigo_empresa', '-')}")

                    st.markdown("#### Estado")
                    st.write(f"**Estado:** {vehiculo_sel.get('estado', 'A')}")
                    st.write(f"**Kilómetros:** {format_number(vehiculo_sel.get('kilometros', 0) or 0)}")
                    st.write(f"**Bloqueado:** {'Sí' if vehiculo_sel.get('vehiculo_bloqueado') else 'No'}")
                    st.write(f"**Inhabilitado Tráfico:** {'Sí' if vehiculo_sel.get('inhabilitado_trafico') else 'No'}")

                # Datos del año actual
                if ejercicio_id:
                    datos_año = db.obtener_datos_vehiculo_año(vehiculo_sel['id'], ejercicio_id)
                    if datos_año:
                        st.markdown("---")
                        st.markdown(f"#### Datos del Ejercicio {st.session_state.ejercicio_actual}")
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Km Anuales", format_number(datos_año.get('km_anual', 0)))
                        with col2:
                            st.metric("Horas Servicio", format_number(datos_año.get('horas_servicio', 0), 1))
                        with col3:
                            st.metric("% Año", f"{(datos_año.get('porcentaje_año', 1) or 1) * 100:.0f}%")
                        with col4:
                            st.metric("Fecha Inicio", datos_año.get('fecha_inicio', '-'))

    with tabs[2]:
        st.markdown("### Añadir Nuevo Vehículo")

        with st.form("nuevo_vehiculo"):
            st.markdown("#### Datos Básicos")
            col1, col2, col3 = st.columns(3)

            with col1:
                matricula = st.text_input("Matrícula *", placeholder="1234ABC")
                marca = st.text_input("Marca", placeholder="MAN")
                modelo = st.text_input("Modelo", placeholder="IRIZAR PB")

            with col2:
                plazas = st.number_input("Plazas *", min_value=1, max_value=100, value=55)
                tipo = st.selectbox(
                    "Tipo de Vehículo",
                    options=[1, 2, 3, 4],
                    format_func=lambda x: ['', 'Gran Turismo (>55)', 'Estándar (35-55)', 'Midi (20-35)', 'Mini (<20)'][x]
                )
                vehiculo_tipo = st.text_input("Vehículo Tipo", placeholder="AUTOCAR")

            with col3:
                fecha_mat = st.date_input("Fecha de Matriculación")
                kilometros = st.number_input("Kilómetros", min_value=0, value=0)
                estado = st.selectbox("Estado", options=['A', 'B'], format_func=lambda x: 'Activo' if x == 'A' else 'Baja')

            st.markdown("#### Datos Adicionales")
            col1, col2, col3 = st.columns(3)

            with col1:
                bastidor = st.text_input("Bastidor")
                num_obra = st.text_input("Núm. Obra")
                longitud = st.number_input("Longitud (mm)", min_value=0.0, value=0.0)

            with col2:
                altura = st.number_input("Altura (mm)", min_value=0.0, value=0.0)
                conductor = st.text_input("Conductor")
                empresa = st.text_input("Empresa", value="Autopullman San Sebastián S.L.")

            with col3:
                fecha_itv = st.date_input("Fecha Final ITV", value=None)
                fecha_tacografo = st.date_input("Fecha Final Tacógrafo", value=None)
                fecha_extintores = st.date_input("Caducidad Extintores", value=None)

            submitted = st.form_submit_button("Añadir Vehículo")

            if submitted:
                if matricula:
                    try:
                        kwargs = {
                            'marca': marca,
                            'modelo': modelo,
                            'vehiculo_tipo': vehiculo_tipo,
                            'fecha_matriculacion': fecha_mat.strftime("%Y-%m-%d") if fecha_mat else None,
                            'kilometros': kilometros,
                            'estado': estado,
                            'bastidor': bastidor,
                            'num_obra': num_obra,
                            'longitud': longitud if longitud > 0 else None,
                            'altura': altura if altura > 0 else None,
                            'conductor': conductor,
                            'empresa': empresa,
                            'fecha_final_itv': fecha_itv.strftime("%Y-%m-%d") if fecha_itv else None,
                            'fecha_final_tacografo': fecha_tacografo.strftime("%Y-%m-%d") if fecha_tacografo else None,
                            'caducidad_extintores': fecha_extintores.strftime("%Y-%m-%d") if fecha_extintores else None
                        }

                        vehiculo_id = db.crear_vehiculo(
                            matricula.upper().replace("-", "").replace(" ", ""),
                            plazas,
                            tipo,
                            **kwargs
                        )

                        # Crear registro para el ejercicio actual si existe
                        if ejercicio_id and vehiculo_id:
                            db.guardar_vehiculo_año(vehiculo_id, ejercicio_id, km_anual=kilometros)

                        st.success(f"Vehículo {matricula} añadido correctamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al añadir vehículo: {str(e)}")
                else:
                    st.error("La matrícula es obligatoria.")

    with tabs[3]:
        st.markdown("### Editar Vehículo")

        vehiculos = db.obtener_vehiculos(activos_solo=False)
        if not vehiculos:
            st.info("No hay vehículos para editar.")
        else:
            vehiculo_seleccionado = st.selectbox(
                "Seleccionar vehículo",
                options=vehiculos,
                format_func=lambda x: f"{x['matricula']} - {x.get('marca', '')} {x.get('modelo', '')}",
                key="vehiculo_editar"
            )

            if vehiculo_seleccionado:
                with st.form("editar_vehiculo"):
                    st.markdown("#### Datos Básicos")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        marca = st.text_input("Marca", value=vehiculo_seleccionado.get('marca', '') or '')
                        modelo = st.text_input("Modelo", value=vehiculo_seleccionado.get('modelo', '') or '')
                        plazas = st.number_input(
                            "Plazas",
                            min_value=1,
                            max_value=100,
                            value=vehiculo_seleccionado['plazas'] or 55
                        )

                    with col2:
                        tipo = st.selectbox(
                            "Tipo",
                            options=[1, 2, 3, 4],
                            index=(vehiculo_seleccionado['tipo'] or 1) - 1,
                            format_func=lambda x: ['', 'Gran Turismo', 'Estándar', 'Midi', 'Mini'][x]
                        )
                        vehiculo_tipo = st.text_input("Vehículo Tipo", value=vehiculo_seleccionado.get('vehiculo_tipo', '') or '')
                        kilometros = st.number_input("Kilómetros", min_value=0, value=vehiculo_seleccionado.get('kilometros', 0) or 0)

                    with col3:
                        estado = st.selectbox(
                            "Estado",
                            options=['A', 'B'],
                            index=0 if vehiculo_seleccionado.get('estado', 'A') == 'A' else 1,
                            format_func=lambda x: 'Activo' if x == 'A' else 'Baja'
                        )
                        activo = st.checkbox("Activo en Sistema", value=bool(vehiculo_seleccionado['activo']))
                        conductor = st.text_input("Conductor", value=vehiculo_seleccionado.get('conductor', '') or '')

                    st.markdown("#### Fechas")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        fecha_baja_str = vehiculo_seleccionado.get('fecha_baja')
                        fecha_baja = st.date_input(
                            "Fecha Baja",
                            value=datetime.strptime(fecha_baja_str, "%Y-%m-%d") if fecha_baja_str else None
                        )

                    with col2:
                        fecha_itv_str = vehiculo_seleccionado.get('fecha_final_itv')
                        fecha_itv = st.date_input(
                            "Fecha Final ITV",
                            value=datetime.strptime(fecha_itv_str, "%Y-%m-%d") if fecha_itv_str else None
                        )

                    with col3:
                        fecha_tac_str = vehiculo_seleccionado.get('fecha_final_tacografo')
                        fecha_tacografo = st.date_input(
                            "Fecha Final Tacógrafo",
                            value=datetime.strptime(fecha_tac_str, "%Y-%m-%d") if fecha_tac_str else None
                        )

                    col1, col2 = st.columns(2)
                    with col1:
                        submitted = st.form_submit_button("Guardar Cambios")
                    with col2:
                        eliminar = st.form_submit_button("Desactivar Vehículo", type="secondary")

                    if submitted:
                        db.actualizar_vehiculo(
                            vehiculo_seleccionado['id'],
                            marca=marca,
                            modelo=modelo,
                            plazas=plazas,
                            tipo=tipo,
                            vehiculo_tipo=vehiculo_tipo,
                            kilometros=kilometros,
                            estado=estado,
                            activo=1 if activo else 0,
                            conductor=conductor,
                            fecha_baja=fecha_baja.strftime("%Y-%m-%d") if fecha_baja else None,
                            fecha_final_itv=fecha_itv.strftime("%Y-%m-%d") if fecha_itv else None,
                            fecha_final_tacografo=fecha_tacografo.strftime("%Y-%m-%d") if fecha_tacografo else None
                        )
                        st.success("Vehículo actualizado correctamente.")
                        st.rerun()

                    if eliminar:
                        db.eliminar_vehiculo(vehiculo_seleccionado['id'])
                        st.success("Vehículo desactivado.")
                        st.rerun()

    with tabs[4]:
        st.markdown("### Importar Vehículos desde Excel")

        st.markdown("""
        <div class="info-box">
        <strong>Importación de Vehículos</strong><br>
        Esta función importa vehículos desde un archivo Excel (Vehiculos.xlsx) con todos sus campos
        y los asigna automáticamente a los años correspondientes según su fecha de matriculación y baja.
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Seleccionar archivo Excel de vehículos",
            type=['xlsx', 'xls'],
            key="vehiculos_upload"
        )

        use_default = st.checkbox("Usar archivo por defecto (Datos/Vehiculos.xlsx)")

        años_import = st.multiselect(
            "Años para asignar vehículos",
            options=[2023, 2024, 2025, 2026],
            default=[2024, 2025]
        )

        if st.button("Importar Vehículos"):
            if uploaded_file:
                from pathlib import Path
                temp_path = Path("/tmp/vehiculos_import.xlsx")
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                file_path = str(temp_path)
            elif use_default:
                file_path = str(Path(__file__).parent / "Datos" / "Vehiculos.xlsx")
            else:
                st.error("Selecciona un archivo o marca la opción de archivo por defecto.")
                return

            if os.path.exists(file_path):
                with st.spinner("Importando vehículos..."):
                    try:
                        resultados = loader.importar_vehiculos_completo(file_path, años_import)

                        st.markdown('<div class="success-box">', unsafe_allow_html=True)
                        st.markdown("### Importación Completada")

                        st.metric("Vehículos Procesados", resultados.get('vehiculos_creados', 0))

                        st.markdown("#### Asignaciones por Año")
                        for año, count in resultados.get('asignaciones_año', {}).items():
                            st.write(f"- **{año}:** {count} vehículos asignados")

                        st.markdown('</div>', unsafe_allow_html=True)

                        if resultados.get('errores'):
                            st.warning("Algunos errores durante la importación:")
                            for error in resultados['errores'][:10]:
                                st.write(f"- {error}")

                        st.rerun()

                    except Exception as e:
                        st.error(f"Error durante la importación: {str(e)}")
            else:
                st.error(f"No se encuentra el archivo: {file_path}")


def page_costes_tiempo():
    """Página de edición de costes por tiempo."""
    st.title("⏱️ Costes por Tiempo")

    ejercicio_id = st.session_state.ejercicio_id
    if not ejercicio_id:
        st.warning("Selecciona un ejercicio primero.")
        return

    st.markdown("""
    <div class="info-box">
    Los costes por tiempo son aquellos que se generan independientemente del uso del vehículo:
    adquisición, financiación, seguros, fiscales, etc.
    </div>
    """, unsafe_allow_html=True)

    vehiculos = db.obtener_vehiculos()
    if not vehiculos:
        st.warning("No hay vehículos registrados.")
        return

    vehiculo = st.selectbox(
        "Seleccionar vehículo",
        options=vehiculos,
        format_func=lambda x: f"{x['matricula']} - {x['plazas']} plazas"
    )

    if vehiculo:
        tabs = st.tabs(["📈 Adquisición", "💰 Financiación", "🛡️ Seguros", "📋 Fiscales"])

        # Tab Adquisición
        with tabs[0]:
            st.markdown('<div class="category-header">1.1 Costes de Adquisición</div>', unsafe_allow_html=True)

            adq = db.obtener_costes('costes_adquisicion', ejercicio_id, vehiculo['id'])
            adq = adq[0] if adq else {}

            with st.form("form_adquisicion"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    valor_compra = st.number_input(
                        "Valor de Compra (€)",
                        min_value=0.0,
                        value=float(adq.get('valor_compra', 0))
                    )
                    fecha_compra = st.date_input(
                        "Fecha de Compra",
                        value=datetime.strptime(adq['fecha_compra'], "%Y-%m-%d") if adq.get('fecha_compra') else None
                    )

                with col2:
                    valor_residual = st.number_input(
                        "Valor Residual (€)",
                        min_value=0.0,
                        value=float(adq.get('valor_residual', 0))
                    )
                    vida_util = st.number_input(
                        "Vida Útil (años)",
                        min_value=1.0,
                        max_value=30.0,
                        value=float(adq.get('vida_util', 10))
                    )

                with col3:
                    años_uso = st.number_input(
                        "Años de Uso",
                        min_value=0.0,
                        value=float(adq.get('años_uso', 0))
                    )

                    # Cálculo automático
                    if vida_util > 0:
                        coste_calc = (valor_compra - valor_residual) / vida_util
                    else:
                        coste_calc = 0

                    st.metric("Coste Anual Calculado", format_currency(coste_calc, 2))

                submitted = st.form_submit_button("Guardar")
                if submitted:
                    db.guardar_coste(
                        'costes_adquisicion',
                        vehiculo['id'],
                        ejercicio_id,
                        valor_compra=valor_compra,
                        valor_residual=valor_residual,
                        vida_util=vida_util,
                        años_uso=años_uso,
                        coste_anual=coste_calc,
                        fecha_compra=fecha_compra.strftime("%Y-%m-%d") if fecha_compra else None
                    )
                    db.calcular_resumen_vehiculo(vehiculo['id'], ejercicio_id)
                    st.success("Datos guardados correctamente.")

        # Tab Financiación
        with tabs[1]:
            st.markdown('<div class="category-header">1.2 Costes de Financiación</div>', unsafe_allow_html=True)

            fin = db.obtener_costes('costes_financiacion', ejercicio_id, vehiculo['id'])
            fin = fin[0] if fin else {}

            with st.form("form_financiacion"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    financiado = st.checkbox("Vehículo Financiado", value=bool(fin.get('financiado', 0)))
                    importe = st.number_input(
                        "Importe Financiado (€)",
                        min_value=0.0,
                        value=float(fin.get('importe_financiado', 0))
                    )

                with col2:
                    plazo = st.number_input(
                        "Plazo (meses)",
                        min_value=0,
                        max_value=120,
                        value=int(fin.get('plazo_meses', 60))
                    )
                    tae = st.number_input(
                        "TAE (%)",
                        min_value=0.0,
                        max_value=20.0,
                        value=float(fin.get('tae', 0)) * 100,
                        step=0.1
                    ) / 100

                with col3:
                    intereses = st.number_input(
                        "Intereses Anuales (€)",
                        min_value=0.0,
                        value=float(fin.get('intereses', 0))
                    )

                    # Cálculo
                    if financiado and importe > 0 and tae > 0:
                        coste_calc = importe * tae
                    else:
                        coste_calc = intereses

                    st.metric("Coste Anual", format_currency(coste_calc, 2))

                submitted = st.form_submit_button("Guardar")
                if submitted:
                    db.guardar_coste(
                        'costes_financiacion',
                        vehiculo['id'],
                        ejercicio_id,
                        financiado=1 if financiado else 0,
                        importe_financiado=importe,
                        plazo_meses=plazo,
                        tae=tae,
                        intereses=intereses,
                        coste_anual=coste_calc
                    )
                    db.calcular_resumen_vehiculo(vehiculo['id'], ejercicio_id)
                    st.success("Datos guardados correctamente.")

        # Tab Seguros
        with tabs[2]:
            st.markdown('<div class="category-header">1.4 Costes de Seguros</div>', unsafe_allow_html=True)

            seg = db.obtener_costes('costes_seguros', ejercicio_id, vehiculo['id'])
            seg = seg[0] if seg else {}

            with st.form("form_seguros"):
                col1, col2 = st.columns(2)

                with col1:
                    aseguradora = st.text_input(
                        "Aseguradora",
                        value=seg.get('aseguradora', 'PLUS ULTRA')
                    )
                    num_poliza = st.text_input(
                        "Nº Póliza",
                        value=seg.get('num_poliza', '')
                    )

                with col2:
                    prima_1 = st.number_input(
                        "Prima 1º Semestre (€)",
                        min_value=0.0,
                        value=float(seg.get('prima_1_semestre', 0))
                    )
                    prima_2 = st.number_input(
                        "Prima 2º Semestre (€)",
                        min_value=0.0,
                        value=float(seg.get('prima_2_semestre', 0))
                    )

                coste_anual = prima_1 + prima_2
                st.metric("Coste Anual Total", format_currency(coste_anual, 2))

                submitted = st.form_submit_button("Guardar")
                if submitted:
                    db.guardar_coste(
                        'costes_seguros',
                        vehiculo['id'],
                        ejercicio_id,
                        aseguradora=aseguradora,
                        num_poliza=num_poliza,
                        prima_1_semestre=prima_1,
                        prima_2_semestre=prima_2,
                        coste_anual=coste_anual
                    )
                    db.calcular_resumen_vehiculo(vehiculo['id'], ejercicio_id)
                    st.success("Datos guardados correctamente.")

        # Tab Fiscales
        with tabs[3]:
            st.markdown('<div class="category-header">1.5 Costes Fiscales</div>', unsafe_allow_html=True)

            fis = db.obtener_costes('costes_fiscales', ejercicio_id, vehiculo['id'])
            fis = fis[0] if fis else {}

            with st.form("form_fiscales"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    sovi = st.number_input("SOVI (€)", min_value=0.0, value=float(fis.get('sovi', 0)))
                    itv_1 = st.number_input("ITV 1 (€)", min_value=0.0, value=float(fis.get('itv_1', 0)))
                    itv_escolar_1 = st.number_input("ITV Escolar 1 (€)", min_value=0.0, value=float(fis.get('itv_escolar_1', 0)))
                    itv_2 = st.number_input("ITV 2 (€)", min_value=0.0, value=float(fis.get('itv_2', 0)))

                with col2:
                    itv_escolar_2 = st.number_input("ITV Escolar 2 (€)", min_value=0.0, value=float(fis.get('itv_escolar_2', 0)))
                    tacografo = st.number_input("Revisión Tacógrafo (€)", min_value=0.0, value=float(fis.get('revision_tacografo', 0)))
                    ivtm = st.number_input("IVTM (€)", min_value=0.0, value=float(fis.get('ivtm', 0)))
                    iae = st.number_input("IAE (€)", min_value=0.0, value=float(fis.get('iae', 0)))

                with col3:
                    dris = st.number_input("DRIS (€)", min_value=0.0, value=float(fis.get('dris', 0)))
                    visado = st.number_input("Visado (€)", min_value=0.0, value=float(fis.get('visado', 0)))
                    licencia = st.number_input("Licencia Comunitaria (€)", min_value=0.0, value=float(fis.get('licencia_com', 0)))

                coste_anual = sovi + itv_1 + itv_escolar_1 + itv_2 + itv_escolar_2 + tacografo + ivtm + iae + dris + visado + licencia
                st.metric("Coste Anual Total", format_currency(coste_anual, 2))

                submitted = st.form_submit_button("Guardar")
                if submitted:
                    db.guardar_coste(
                        'costes_fiscales',
                        vehiculo['id'],
                        ejercicio_id,
                        sovi=sovi, itv_1=itv_1, itv_escolar_1=itv_escolar_1,
                        itv_2=itv_2, itv_escolar_2=itv_escolar_2,
                        revision_tacografo=tacografo, ivtm=ivtm, iae=iae,
                        dris=dris, visado=visado, licencia_com=licencia,
                        coste_anual=coste_anual
                    )
                    db.calcular_resumen_vehiculo(vehiculo['id'], ejercicio_id)
                    st.success("Datos guardados correctamente.")


def page_costes_km():
    """Página de edición de costes por kilómetro."""
    st.title("🛣️ Costes por Kilómetro")

    ejercicio_id = st.session_state.ejercicio_id
    if not ejercicio_id:
        st.warning("Selecciona un ejercicio primero.")
        return

    st.markdown("""
    <div class="info-box">
    Los costes por kilómetro son aquellos que varían según el uso del vehículo:
    combustible, neumáticos, mantenimiento, urea, etc.
    </div>
    """, unsafe_allow_html=True)

    vehiculos = db.obtener_vehiculos()
    if not vehiculos:
        st.warning("No hay vehículos registrados.")
        return

    vehiculo = st.selectbox(
        "Seleccionar vehículo",
        options=vehiculos,
        format_func=lambda x: f"{x['matricula']} - {x['plazas']} plazas",
        key="vehiculo_costes_km"
    )

    if vehiculo:
        # Obtener km anuales
        datos_año = db.obtener_datos_vehiculo_año(vehiculo['id'], ejercicio_id)
        km_anual = datos_año.get('km_anual', 0) if datos_año else 0

        st.info(f"Km Anuales: {format_number(km_anual)}")

        tabs = st.tabs(["⛽ Combustible", "🔧 Mantenimiento", "🛞 Neumáticos", "💧 Urea/AdBlue"])

        # Tab Combustible
        with tabs[0]:
            st.markdown('<div class="category-header">2.1 Costes de Combustible</div>', unsafe_allow_html=True)

            comb = db.obtener_costes('costes_combustible', ejercicio_id, vehiculo['id'])
            comb = comb[0] if comb else {}

            with st.form("form_combustible"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    consumo_ciudad = st.number_input(
                        "Consumo Ciudad (L/100km)",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(comb.get('consumo_ciudad', 0))
                    )
                    consumo_carretera = st.number_input(
                        "Consumo Carretera (L/100km)",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(comb.get('consumo_carretera', 0))
                    )

                with col2:
                    consumo_mixto = st.number_input(
                        "Consumo Mixto (L/100km)",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(comb.get('consumo_mixto', (consumo_ciudad + consumo_carretera) / 2 if consumo_ciudad or consumo_carretera else 0))
                    )
                    precio_litro = st.number_input(
                        "Precio Litro (€)",
                        min_value=0.0,
                        max_value=5.0,
                        value=float(comb.get('precio_litro', 0.974)),
                        step=0.01
                    )

                with col3:
                    # Cálculos
                    coste_km = (consumo_mixto / 100) * precio_litro
                    coste_anual = coste_km * km_anual

                    st.metric("Coste por Km", format_currency(coste_km, 4))
                    st.metric("Coste Anual", format_currency(coste_anual, 2))

                submitted = st.form_submit_button("Guardar")
                if submitted:
                    db.guardar_coste(
                        'costes_combustible',
                        vehiculo['id'],
                        ejercicio_id,
                        consumo_ciudad=consumo_ciudad,
                        consumo_carretera=consumo_carretera,
                        consumo_mixto=consumo_mixto,
                        precio_litro=precio_litro,
                        coste_km=coste_km,
                        coste_anual=coste_anual
                    )
                    db.calcular_resumen_vehiculo(vehiculo['id'], ejercicio_id)
                    st.success("Datos guardados correctamente.")

        # Tab Mantenimiento
        with tabs[1]:
            st.markdown('<div class="category-header">1.3 Costes de Mantenimiento</div>', unsafe_allow_html=True)

            mant = db.obtener_costes('costes_mantenimiento', ejercicio_id, vehiculo['id'])
            mant = mant[0] if mant else {}

            with st.form("form_mantenimiento"):
                col1, col2 = st.columns(2)

                with col1:
                    ratio = st.number_input(
                        "Ratio por Tipo (€/km)",
                        min_value=0.0,
                        max_value=1.0,
                        value=float(mant.get('ratio_tipo', 0.2)),
                        step=0.01,
                        format="%.4f"
                    )

                with col2:
                    coste_anual = ratio * km_anual
                    st.metric("Coste Anual Calculado", format_currency(coste_anual, 2))

                coste_manual = st.number_input(
                    "Coste Anual Manual (€) - dejar en 0 para usar cálculo automático",
                    min_value=0.0,
                    value=float(mant.get('coste_anual', 0))
                )

                submitted = st.form_submit_button("Guardar")
                if submitted:
                    db.guardar_coste(
                        'costes_mantenimiento',
                        vehiculo['id'],
                        ejercicio_id,
                        ratio_tipo=ratio,
                        coste_anual=coste_manual if coste_manual > 0 else coste_anual
                    )
                    db.calcular_resumen_vehiculo(vehiculo['id'], ejercicio_id)
                    st.success("Datos guardados correctamente.")

        # Tab Neumáticos
        with tabs[2]:
            st.markdown('<div class="category-header">2.2 Costes de Neumáticos</div>', unsafe_allow_html=True)

            neum = db.obtener_costes('costes_neumaticos', ejercicio_id, vehiculo['id'])
            neum = neum[0] if neum else {}

            with st.form("form_neumaticos"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    coste_unitario = st.number_input(
                        "Coste Unitario (€)",
                        min_value=0.0,
                        value=float(neum.get('coste_unitario', 0))
                    )

                with col2:
                    vida_util_km = st.number_input(
                        "Vida Útil (km)",
                        min_value=0,
                        value=int(neum.get('vida_util_km', 50000))
                    )

                with col3:
                    # Cálculo (6 neumáticos típico)
                    if vida_util_km > 0:
                        coste_km = (coste_unitario * 6) / vida_util_km
                    else:
                        coste_km = 0
                    coste_anual = coste_km * km_anual

                    st.metric("Coste por Km", format_currency(coste_km, 4))
                    st.metric("Coste Anual", format_currency(coste_anual, 2))

                submitted = st.form_submit_button("Guardar")
                if submitted:
                    db.guardar_coste(
                        'costes_neumaticos',
                        vehiculo['id'],
                        ejercicio_id,
                        coste_unitario=coste_unitario,
                        vida_util_km=vida_util_km,
                        coste_km=coste_km,
                        coste_anual=coste_anual
                    )
                    db.calcular_resumen_vehiculo(vehiculo['id'], ejercicio_id)
                    st.success("Datos guardados correctamente.")

        # Tab Urea
        with tabs[3]:
            st.markdown('<div class="category-header">2.3 Costes de Urea/AdBlue</div>', unsafe_allow_html=True)

            urea = db.obtener_costes('costes_urea', ejercicio_id, vehiculo['id'])
            urea = urea[0] if urea else {}

            with st.form("form_urea"):
                col1, col2 = st.columns(2)

                with col1:
                    consumo_km = st.number_input(
                        "Consumo por Km (L/km)",
                        min_value=0.0,
                        max_value=0.1,
                        value=float(urea.get('consumo_por_km', 0.02)),
                        step=0.001,
                        format="%.4f"
                    )
                    precio_litro = st.number_input(
                        "Precio Litro (€)",
                        min_value=0.0,
                        max_value=5.0,
                        value=float(urea.get('precio_litro', 0.5)),
                        step=0.01
                    )

                with col2:
                    coste_anual = consumo_km * precio_litro * km_anual
                    st.metric("Coste Anual", format_currency(coste_anual, 2))

                    # O coste fijo
                    coste_fijo = st.number_input(
                        "Coste Anual Fijo (€) - típico 514€",
                        min_value=0.0,
                        value=float(urea.get('coste_anual', 514))
                    )

                submitted = st.form_submit_button("Guardar")
                if submitted:
                    db.guardar_coste(
                        'costes_urea',
                        vehiculo['id'],
                        ejercicio_id,
                        consumo_por_km=consumo_km,
                        precio_litro=precio_litro,
                        coste_anual=coste_fijo if coste_fijo > 0 else coste_anual
                    )
                    db.calcular_resumen_vehiculo(vehiculo['id'], ejercicio_id)
                    st.success("Datos guardados correctamente.")


def page_personal():
    """Página de gestión de costes de personal."""
    st.title("👥 Costes de Personal")

    ejercicio_id = st.session_state.ejercicio_id
    if not ejercicio_id:
        st.warning("Selecciona un ejercicio primero.")
        return

    st.markdown("""
    <div class="info-box">
    Los costes de personal incluyen salarios, seguridad social y otros costes asociados
    a los conductores. Estos costes se imputan a cada vehículo según sus horas de servicio.
    </div>
    """, unsafe_allow_html=True)

    personal = db.obtener_personal(ejercicio_id)

    with st.form("form_personal"):
        st.markdown("### Datos Generales de Conductores")

        col1, col2, col3 = st.columns(3)

        with col1:
            coste_total = st.number_input(
                "Coste Total Conductores (€)",
                min_value=0.0,
                value=float(personal.get('coste_total_conductores', 0))
            )
            total_horas = st.number_input(
                "Total Horas Contratadas",
                min_value=0.0,
                value=float(personal.get('total_horas', 0))
            )

        with col2:
            absentismo = st.number_input(
                "Horas Absentismo",
                min_value=0.0,
                value=float(personal.get('absentismo', 0))
            )
            horas_servicio = st.number_input(
                "Horas en Servicio",
                min_value=0.0,
                value=float(personal.get('horas_servicio', 0))
            )

        with col3:
            coste_empresa = st.number_input(
                "Coste Empresa (Salario + SS)",
                min_value=0.0,
                value=float(personal.get('coste_empresa_salario_ss', 0))
            )
            indirectos = st.number_input(
                "Indirectos (€)",
                min_value=0.0,
                value=float(personal.get('indirectos', 0))
            )

        # Cálculos
        st.markdown("---")
        st.markdown("### Cálculos")

        col1, col2, col3 = st.columns(3)

        with col1:
            horas_productivas = horas_servicio * 0.95  # 95% productividad típica
            st.metric("Horas Productivas", format_number(horas_productivas, 2))

        with col2:
            if horas_servicio > 0:
                salario_hora = coste_total / horas_servicio
            else:
                salario_hora = 0
            st.metric("Coste/Hora Servicio", format_currency(salario_hora, 2))

        with col3:
            coste_total_calc = coste_empresa + indirectos
            st.metric("Coste Total Calculado", format_currency(coste_total_calc, 2))

        submitted = st.form_submit_button("Guardar")
        if submitted:
            db.guardar_personal(
                ejercicio_id,
                coste_total_conductores=coste_total,
                total_horas=total_horas,
                absentismo=absentismo,
                horas_servicio=horas_servicio,
                horas_productivas=horas_productivas,
                salario_hora_servicio=salario_hora,
                coste_empresa_salario_ss=coste_empresa,
                indirectos=indirectos
            )

            # Recalcular todos los vehículos
            vehiculos = db.obtener_vehiculos()
            for v in vehiculos:
                db.calcular_resumen_vehiculo(v['id'], ejercicio_id)

            st.success("Datos de personal guardados y costes recalculados.")


def page_pyg():
    """Página de gestión del P&G."""
    st.title("📊 Pérdidas y Ganancias")

    ejercicio_id = st.session_state.ejercicio_id
    if not ejercicio_id:
        st.warning("Selecciona un ejercicio primero.")
        return

    st.markdown("""
    <div class="info-box">
    El P&G (Cuenta de Pérdidas y Ganancias) proporciona una visión global de los
    ingresos y gastos de la empresa, permitiendo identificar qué porcentaje corresponde
    a costes directos e indirectos.
    </div>
    """, unsafe_allow_html=True)

    # Mostrar resumen
    pyg_resumen = db.obtener_pyg_resumen(ejercicio_id)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Gastos", format_currency(pyg_resumen.get('total_gastos', 0)))
    with col2:
        st.metric("Total Ingresos", format_currency(pyg_resumen.get('total_ingresos', 0)))
    with col3:
        st.metric("Costes Directos", format_currency(pyg_resumen.get('costes_directos', 0)))
    with col4:
        st.metric("Costes Indirectos", format_currency(pyg_resumen.get('costes_indirectos', 0)))

    st.markdown("---")

    tabs = st.tabs(["📋 Ver P&G", "✏️ Editar Partidas", "📥 Importar"])

    with tabs[0]:
        pyg_data = db.obtener_pyg(ejercicio_id)

        if pyg_data:
            df = pd.DataFrame(pyg_data)
            df = df[['cuenta', 'descripcion', 'importe_ajustado', 'categoria', 'es_coste_directo', 'es_coste_indirecto']]
            df['importe_ajustado'] = df['importe_ajustado'].apply(lambda x: format_currency(x))
            df['es_coste_directo'] = df['es_coste_directo'].apply(lambda x: '✓' if x else '')
            df['es_coste_indirecto'] = df['es_coste_indirecto'].apply(lambda x: '✓' if x else '')
            df.columns = ['Cuenta', 'Descripción', 'Importe', 'Categoría', 'Directo', 'Indirecto']

            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No hay datos de P&G. Importa desde Excel o añade partidas manualmente.")

    with tabs[1]:
        st.markdown("### Añadir/Editar Partida")

        with st.form("form_pyg"):
            col1, col2 = st.columns(2)

            with col1:
                cuenta = st.text_input("Código Cuenta", placeholder="600")
                descripcion = st.text_input("Descripción", placeholder="COMPRAS DE MERCADERÍAS")
                importe = st.number_input("Importe (€)", value=0.0)

            with col2:
                categoria = st.selectbox("Categoría", options=['Gastos', 'Ingresos', 'Otros'])
                es_directo = st.checkbox("Es Coste Directo")
                es_indirecto = st.checkbox("Es Coste Indirecto")

            submitted = st.form_submit_button("Añadir Partida")
            if submitted and cuenta:
                registro = {
                    'cuenta': cuenta,
                    'descripcion': descripcion,
                    'importe_no_ajustado': importe,
                    'importe_ajustado': importe,
                    'ponderado_directo': 1 if es_directo else 0,
                    'ponderado_indirecto': 1 if es_indirecto else 0,
                    'es_coste_directo': 1 if es_directo else 0,
                    'es_coste_indirecto': 1 if es_indirecto else 0,
                    'categoria': categoria
                }

                # Obtener datos existentes y añadir
                pyg_actual = db.obtener_pyg(ejercicio_id)
                pyg_actual.append(registro)
                db.guardar_pyg(ejercicio_id, pyg_actual)

                st.success("Partida añadida correctamente.")
                st.rerun()

    with tabs[2]:
        st.markdown("### Importar desde Excel")
        st.info("Para importar el P&G completo, utiliza la función de importación en Configuración.")


def page_configuracion():
    """Página de configuración e importación."""
    st.title("⚙️ Configuración")

    tabs = st.tabs(["📅 Ejercicios", "📥 Importar Excel", "🔧 Opciones"])

    with tabs[0]:
        st.markdown("### Gestión de Ejercicios Fiscales")

        ejercicios = db.obtener_ejercicios()

        # Lista de ejercicios
        if ejercicios:
            st.markdown("#### Ejercicios Existentes")
            for ej in ejercicios:
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"**{ej['año']}** - {ej['descripcion']}")
                with col2:
                    st.write(f"Creado: {ej['fecha_creacion'][:10] if ej['fecha_creacion'] else 'N/A'}")
                with col3:
                    if st.button("Seleccionar", key=f"sel_{ej['año']}"):
                        st.session_state.ejercicio_actual = ej['año']
                        st.session_state.ejercicio_id = ej['id']
                        st.success(f"Ejercicio {ej['año']} seleccionado.")
                        st.rerun()
        else:
            st.info("No hay ejercicios creados.")

        st.markdown("---")

        # Crear nuevo ejercicio
        st.markdown("#### Crear Nuevo Ejercicio")
        with st.form("nuevo_ejercicio"):
            col1, col2 = st.columns(2)
            with col1:
                año = st.number_input(
                    "Año",
                    min_value=2000,
                    max_value=2100,
                    value=datetime.now().year
                )
            with col2:
                descripcion = st.text_input("Descripción", value=f"Ejercicio {datetime.now().year}")

            submitted = st.form_submit_button("Crear Ejercicio")
            if submitted:
                try:
                    ej_id = db.crear_ejercicio(año, descripcion)
                    st.session_state.ejercicio_actual = año
                    st.session_state.ejercicio_id = ej_id
                    st.success(f"Ejercicio {año} creado correctamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    with tabs[1]:
        st.markdown("### Importar Datos desde Excel")

        st.markdown("""
        <div class="warning-box">
        <strong>Importante:</strong> La importación sobrescribirá los datos existentes para el año seleccionado.
        Asegúrate de tener una copia de seguridad si es necesario.
        </div>
        """, unsafe_allow_html=True)

        # Seleccionar año para importar
        año_import = st.number_input(
            "Año de los datos a importar",
            min_value=2000,
            max_value=2100,
            value=st.session_state.ejercicio_actual or datetime.now().year
        )

        # Archivo
        uploaded_file = st.file_uploader(
            "Seleccionar archivo Excel",
            type=['xlsx', 'xls']
        )

        # O usar archivo por defecto
        use_default = st.checkbox("Usar archivo por defecto (costes2024app.xlsx)")

        if st.button("Importar Datos"):
            if uploaded_file:
                # Guardar temporalmente
                temp_path = Path("/tmp/costes_import.xlsx")
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                file_path = str(temp_path)
            elif use_default:
                file_path = "/Users/cesarmartin/Downloads/costes2024app.xlsx"
            else:
                st.error("Selecciona un archivo o marca la opción de archivo por defecto.")
                return

            if os.path.exists(file_path):
                with st.spinner("Importando datos..."):
                    try:
                        resultados = loader.importar_excel(file_path, año_import)

                        st.markdown('<div class="success-box">', unsafe_allow_html=True)
                        st.markdown("### Importación Completada")

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Vehículos", resultados.get('vehiculos', 0))
                            st.metric("Adquisición", resultados.get('adquisicion', 0))
                            st.metric("Financiación", resultados.get('financiacion', 0))

                        with col2:
                            st.metric("Mantenimiento", resultados.get('mantenimiento', 0))
                            st.metric("Seguros", resultados.get('seguros', 0))
                            st.metric("Fiscales", resultados.get('fiscales', 0))

                        with col3:
                            st.metric("Combustible", resultados.get('combustible', 0))
                            st.metric("Personal", resultados.get('personal', 0))
                            st.metric("P&G", resultados.get('pyg', 0))

                        st.markdown('</div>', unsafe_allow_html=True)

                        if resultados.get('errores'):
                            st.warning("Algunos errores durante la importación:")
                            for error in resultados['errores']:
                                st.write(f"- {error}")

                        # Actualizar ejercicio actual
                        ej = db.obtener_ejercicio_por_año(año_import)
                        if ej:
                            st.session_state.ejercicio_actual = año_import
                            st.session_state.ejercicio_id = ej['id']

                    except Exception as e:
                        st.error(f"Error durante la importación: {str(e)}")
            else:
                st.error("No se encuentra el archivo especificado.")

    with tabs[2]:
        st.markdown("### Opciones de la Aplicación")

        st.markdown("#### Base de Datos")
        db_path = Path(__file__).parent / "costes_david.db"
        st.write(f"Ubicación: `{db_path}`")

        if st.button("Reiniciar Base de Datos"):
            if st.checkbox("Confirmar reinicio (se perderán todos los datos)"):
                try:
                    os.remove(db_path)
                    db.init_database()
                    st.session_state.clear()
                    st.success("Base de datos reiniciada.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")


def page_simulacion():
    """Página de simulación y proyecciones."""
    st.title("🔮 Simulación y Proyecciones")

    ejercicio_id = st.session_state.ejercicio_id
    if not ejercicio_id:
        st.warning("Selecciona un ejercicio primero.")
        return

    data = loader.obtener_datos_completos(ejercicio_id)

    tabs = st.tabs(["🎯 Simulación What-If", "📈 Proyecciones"])

    with tabs[0]:
        st.markdown("### Simulador de Escenarios")

        df = data.get('resumen_flota', pd.DataFrame())
        if df.empty:
            st.warning("No hay datos para simular.")
            return

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Parámetros")

            fuel_change = st.slider("Variación Combustible (%)", -30, 50, 0, 5)
            km_change = st.slider("Variación Kilómetros (%)", -50, 50, 0, 5)
            personal_change = st.slider("Variación Personal (%)", -20, 30, 0, 5)

        with col2:
            st.markdown("#### Resultados")

            # Calcular impacto
            original = df['coste_total'].sum()
            combustible_base = df['costes_km'].sum() * 0.6  # Aprox 60% es combustible
            personal_base = df['costes_tiempo'].sum() * 0.6  # Aprox 60% es personal

            fuel_impact = combustible_base * (fuel_change / 100)
            km_impact = df['costes_km'].sum() * (km_change / 100)
            personal_impact = personal_base * (personal_change / 100)

            total_impact = fuel_impact + km_impact + personal_impact
            nuevo_total = original + total_impact

            st.metric("Coste Original", format_currency(original))
            st.metric(
                "Coste Simulado",
                format_currency(nuevo_total),
                delta=f"{total_impact:+,.0f} € ({(total_impact/original*100):+.1f}%)"
            )

            # Gráfico de impacto
            fig = go.Figure(go.Waterfall(
                name="Impacto",
                orientation="v",
                x=["Original", "Combustible", "Km", "Personal", "Nuevo Total"],
                y=[original, fuel_impact, km_impact, personal_impact, 0],
                measure=["absolute", "relative", "relative", "relative", "total"],
                connector={"line": {"color": COLORS['gris_medio']}},
                decreasing={"marker": {"color": COLORS['verde']}},
                increasing={"marker": {"color": COLORS['rojo']}},
                totals={"marker": {"color": COLORS['negro']}}
            ))

            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=300
            )

            st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        st.markdown("### Proyecciones Futuras")

        df = data.get('resumen_flota', pd.DataFrame())
        if df.empty:
            st.warning("No hay datos para proyectar.")
            return

        col1, col2 = st.columns([1, 2])

        with col1:
            años_proyeccion = st.selectbox("Horizonte", [1, 2, 3, 5], index=2)
            inflacion = st.number_input("Inflación anual (%)", 0.0, 15.0, 3.0, 0.5)
            combustible_trend = st.number_input("Tendencia combustible (%)", -10.0, 20.0, 2.0, 0.5)
            km_growth = st.number_input("Crecimiento km (%)", -10.0, 20.0, 1.0, 0.5)

        with col2:
            # Generar proyección
            año_base = st.session_state.ejercicio_actual
            coste_base = df['coste_total'].sum()
            combustible_base = df['costes_km'].sum() * 0.6
            otros_base = coste_base - combustible_base

            años = list(range(año_base, año_base + años_proyeccion + 1))
            proyeccion = [coste_base]

            for i in range(años_proyeccion):
                combustible_nuevo = proyeccion[-1] * 0.4 * (1 + combustible_trend/100) * (1 + km_growth/100)
                otros_nuevo = proyeccion[-1] * 0.6 * (1 + inflacion/100)
                proyeccion.append(combustible_nuevo + otros_nuevo)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=años,
                y=proyeccion,
                mode='lines+markers',
                name='Coste Total',
                line=dict(color=COLORS['negro'], width=3),
                marker=dict(size=10)
            ))

            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis_title="Año",
                yaxis_title="Coste (€)",
                hovermode='x unified'
            )
            fig.update_xaxes(dtick=1)

            st.plotly_chart(fig, use_container_width=True)

            # Tabla resumen
            df_proy = pd.DataFrame({
                'Año': años,
                'Coste Proyectado': [format_currency(c) for c in proyeccion],
                'Variación': ['Base'] + [f"+{(proyeccion[i]/proyeccion[i-1]-1)*100:.1f}%" for i in range(1, len(proyeccion))]
            })
            st.dataframe(df_proy, use_container_width=True, hide_index=True)


# ============================================================================
# APLICACIÓN PRINCIPAL
# ============================================================================

def main():
    # Sidebar
    with st.sidebar:
        st.markdown('<div class="logo-text">DAVID</div>', unsafe_allow_html=True)
        st.markdown("---")

        # Selector de ejercicio
        ejercicios = db.obtener_ejercicios()
        if ejercicios:
            años = [e['año'] for e in ejercicios]
            año_seleccionado = st.selectbox(
                "📅 Ejercicio",
                options=años,
                index=años.index(st.session_state.ejercicio_actual) if st.session_state.ejercicio_actual in años else 0
            )

            if año_seleccionado != st.session_state.ejercicio_actual:
                st.session_state.ejercicio_actual = año_seleccionado
                ej = db.obtener_ejercicio_por_año(año_seleccionado)
                st.session_state.ejercicio_id = ej['id'] if ej else None
                st.rerun()
        else:
            st.info("Crea un ejercicio en Configuración")

        st.markdown("---")

        # Navegación
        st.markdown("### 📊 Navegación")
        paginas = {
            "🏠 Dashboard": page_dashboard,
            "🚌 Vehículos": page_vehiculos,
            "⏱️ Costes Tiempo": page_costes_tiempo,
            "🛣️ Costes Km": page_costes_km,
            "👥 Personal": page_personal,
            "📊 P&G": page_pyg,
            "🔮 Simulación": page_simulacion,
            "⚙️ Configuración": page_configuracion
        }

        pagina = st.radio(
            "Seleccionar página",
            options=list(paginas.keys()),
            label_visibility="collapsed"
        )

    # Contenido principal
    paginas[pagina]()


if __name__ == "__main__":
    main()
