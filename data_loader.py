import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import streamlit as st

DATA_PATH = Path(__file__).parent

# Parámetros por defecto para clasificación de clientes
DEFAULT_PARAMS = {
    'active_months': 12,           # Meses para considerar cliente activo
    'inactive_months': 24,         # Meses para considerar cliente inactivo
    'habitual_min_services_12m': 2,  # Mínimo servicios en 12 meses para ser habitual
    'habitual_min_services_24m': 3,  # Mínimo servicios en 24 meses para ser habitual
    'habitual_min_revenue_24m': 5000  # Mínimo facturación en 24 meses para ser habitual
}

# Mapeo de estados de presupuesto
ESTADOS_PRESUPUESTO = {
    'A': 'Aceptado',
    'AP': 'Aceptado Parcialmente',
    'R': 'Rechazado',
    'E': 'Enviado',
    'V': 'Valorado',
    'EL': 'En elaboracion',
    'AN': 'Anulado'
}

# Estados que cuentan como aceptados
ESTADOS_ACEPTADOS = ['A', 'AP']

# Estados pendientes de respuesta del cliente
ESTADOS_PENDIENTES = ['E', 'V']

@st.cache_data(ttl=300)
def cargar_servicios_discrecionales():
    """Carga el archivo de Servicios Discrecionales para obtener relación presupuesto-cliente."""
    archivo = DATA_PATH / "Servicios Discrecionales.xlsx"
    if not archivo.exists():
        return pd.DataFrame()

    df = pd.read_excel(archivo)
    return df

def obtener_mapa_presupuesto_cliente():
    """Crea un mapa de Código presupuesto -> Código cliente desde Servicios Discrecionales."""
    df_servicios = cargar_servicios_discrecionales()
    if df_servicios.empty:
        return {}

    # Crear mapa solo con registros que tienen ambos códigos
    df_validos = df_servicios[
        df_servicios['Código presupuesto'].notna() &
        df_servicios['Código cliente'].notna()
    ].copy()

    return dict(zip(
        df_validos['Código presupuesto'].astype(int),
        df_validos['Código cliente'].astype(int)
    ))

@st.cache_data(ttl=300)  # Cache por 5 minutos
def cargar_todos():
    """Carga el archivo todos.xlsx con el histórico completo de presupuestos."""
    archivo = DATA_PATH / "todos.xlsx"
    df = pd.read_excel(archivo)

    # Limpiar y convertir fechas
    for col in ['Fecha alta', 'Fecha Salida', 'Fecha Llegada', 'Fecha alta cliente',
                'Fecha primer presupuesto del Cliente', 'Fecha de envío']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Agregar columna con nombre descriptivo del estado
    df['Estado Descripcion'] = df['Estado presupuesto'].map(ESTADOS_PRESUPUESTO).fillna('Desconocido')

    # Limpiar valores de importe
    df['Total importe'] = pd.to_numeric(df['Total importe'], errors='coerce').fillna(0)

    # Normalizar tipos de servicio a mayúsculas
    df['Tipo Servicio'] = df['Tipo Servicio'].apply(lambda x: x.upper() if pd.notna(x) and isinstance(x, str) else x)

    # Completar códigos de cliente faltantes usando Servicios Discrecionales
    mapa_pres_cliente = obtener_mapa_presupuesto_cliente()
    if mapa_pres_cliente:
        # Solo completar donde Código está vacío
        mask_sin_codigo = df['Código'].isna()
        if mask_sin_codigo.any():
            df.loc[mask_sin_codigo, 'Código'] = df.loc[mask_sin_codigo, 'Cod. Presupuesto'].map(mapa_pres_cliente)

    return df

@st.cache_data(ttl=300)
def cargar_presupuestos_actuales():
    """Carga el archivo de presupuestos actuales/pendientes."""
    archivo = DATA_PATH / "Localizar presupuestos a partir de servicios.xlsx"
    df = pd.read_excel(archivo)

    # Convertir fecha
    if 'Fecha Salida' in df.columns:
        df['Fecha Salida'] = pd.to_datetime(df['Fecha Salida'], errors='coerce')

    # Limpiar importe
    df['Importe'] = pd.to_numeric(df['Importe'], errors='coerce').fillna(0)

    return df

@st.cache_data(ttl=300)
def cargar_clientes():
    """Carga el archivo de clientes."""
    archivo = DATA_PATH / "Clientes.xlsx"
    df = pd.read_excel(archivo)

    # Renombrar columnas para consistencia
    df = df.rename(columns={
        'Código': 'Cod_Cliente',
        'Nombre': 'Nombre_Cliente',
        'Código grupo cliente': 'Cod_Grupo',
        'Grupo cliente': 'Grupo_Cliente'
    })

    return df

def clasificar_cliente(
    first_service_date,
    last_service_date,
    previous_service_date,
    services_last_12m,
    services_last_24m,
    revenue_last_24m,
    as_of_date,
    active_months=12,
    inactive_months=24,
    habitual_min_services_12m=2,
    habitual_min_services_24m=3,
    habitual_min_revenue_24m=5000
):
    """
    Clasifica un cliente según las reglas de negocio.

    Retorna: 'PROSPECTO', 'INACTIVO', 'REACTIVADO', 'HABITUAL', 'OCASIONAL_ACTIVO'
    """
    # Si no tiene servicios aceptados -> PROSPECTO
    if pd.isna(first_service_date) or pd.isna(last_service_date):
        return 'PROSPECTO'

    # Calcular días desde último servicio
    days_since_last = (as_of_date - last_service_date).days
    active_days = active_months * 30
    inactive_days = inactive_months * 30

    # Si days_since_last > inactive_months -> INACTIVO
    if days_since_last > inactive_days:
        return 'INACTIVO'

    # Verificar si es REACTIVADO
    # (último servicio dentro de active_months, pero el anterior fue hace más de active_months)
    if days_since_last <= active_days and pd.notna(previous_service_date):
        days_between_last_two = (last_service_date - previous_service_date).days
        if days_between_last_two > active_days:
            return 'REACTIVADO'

    # Si está dentro de active_months, verificar si es HABITUAL
    if days_since_last <= active_days:
        is_habitual = (
            services_last_12m >= habitual_min_services_12m or
            services_last_24m >= habitual_min_services_24m or
            (revenue_last_24m is not None and revenue_last_24m >= habitual_min_revenue_24m)
        )
        if is_habitual:
            return 'HABITUAL'
        else:
            return 'OCASIONAL_ACTIVO'

    # Fallback
    return 'INACTIVO'


@st.cache_data(ttl=300)
def calcular_metricas_clientes(df_presupuestos, as_of_date=None, params=None):
    """
    Calcula métricas y clasificación para cada cliente.

    Parámetros:
    - df_presupuestos: DataFrame con los presupuestos
    - as_of_date: Fecha de referencia (por defecto hoy)
    - params: Diccionario con parámetros de clasificación

    Retorna: DataFrame con métricas por cliente
    """
    if as_of_date is None:
        as_of_date = datetime.now()

    if params is None:
        params = DEFAULT_PARAMS

    # Fechas límite
    fecha_12m = as_of_date - timedelta(days=365)
    fecha_24m = as_of_date - timedelta(days=730)

    # Solo presupuestos aceptados para métricas de servicios
    df_aceptados = df_presupuestos[df_presupuestos['Estado presupuesto'].isin(ESTADOS_ACEPTADOS)].copy()

    # Calcular métricas por cliente
    metricas = []

    for codigo in df_presupuestos['Código'].dropna().unique():
        df_cliente = df_aceptados[df_aceptados['Código'] == codigo]
        df_cliente_todos = df_presupuestos[df_presupuestos['Código'] == codigo]

        if df_cliente.empty:
            # Cliente sin servicios aceptados
            metricas.append({
                'Código': codigo,
                'first_service_date': None,
                'last_service_date': None,
                'previous_service_date': None,
                'services_last_12m': 0,
                'services_last_24m': 0,
                'revenue_last_12m': 0,
                'revenue_last_24m': 0,
                'total_services': 0,
                'total_revenue': 0,
                'days_since_last_service': None,
                'Segmento_Cliente': 'PROSPECTO'
            })
            continue

        # Ordenar por fecha
        df_cliente_sorted = df_cliente.sort_values('Fecha alta')
        fechas = df_cliente_sorted['Fecha alta'].dropna()

        first_service_date = fechas.min() if not fechas.empty else None
        last_service_date = fechas.max() if not fechas.empty else None

        # Fecha del servicio anterior al último
        previous_service_date = None
        if len(fechas) >= 2:
            previous_service_date = fechas.iloc[-2]

        # Servicios e ingresos últimos 12 meses
        df_12m = df_cliente[df_cliente['Fecha alta'] >= fecha_12m]
        services_last_12m = len(df_12m)
        revenue_last_12m = df_12m['Total importe'].sum()

        # Servicios e ingresos últimos 24 meses
        df_24m = df_cliente[df_cliente['Fecha alta'] >= fecha_24m]
        services_last_24m = len(df_24m)
        revenue_last_24m = df_24m['Total importe'].sum()

        # Totales
        total_services = len(df_cliente)
        total_revenue = df_cliente['Total importe'].sum()

        # Días desde último servicio
        days_since_last = None
        if pd.notna(last_service_date):
            days_since_last = (as_of_date - last_service_date).days

        # Clasificar cliente
        segmento = clasificar_cliente(
            first_service_date=first_service_date,
            last_service_date=last_service_date,
            previous_service_date=previous_service_date,
            services_last_12m=services_last_12m,
            services_last_24m=services_last_24m,
            revenue_last_24m=revenue_last_24m,
            as_of_date=as_of_date,
            **params
        )

        metricas.append({
            'Código': codigo,
            'first_service_date': first_service_date,
            'last_service_date': last_service_date,
            'previous_service_date': previous_service_date,
            'services_last_12m': services_last_12m,
            'services_last_24m': services_last_24m,
            'revenue_last_12m': revenue_last_12m,
            'revenue_last_24m': revenue_last_24m,
            'total_services': total_services,
            'total_revenue': total_revenue,
            'days_since_last_service': days_since_last,
            'Segmento_Cliente': segmento
        })

    return pd.DataFrame(metricas)


@st.cache_data(ttl=300)
def calcular_tipo_cliente(df_presupuestos, as_of_date=None, params=None):
    """
    Calcula el segmento de cada cliente.
    Retorna un diccionario {codigo_cliente: segmento}
    """
    df_metricas = calcular_metricas_clientes(df_presupuestos, as_of_date, params)
    return dict(zip(df_metricas['Código'], df_metricas['Segmento_Cliente']))

@st.cache_data(ttl=300)
def cargar_datos_con_clientes(params=None):
    """
    Carga presupuestos y clientes, y los relaciona.
    Añade información del segmento de cliente.

    Segmentos: PROSPECTO, INACTIVO, REACTIVADO, HABITUAL, OCASIONAL_ACTIVO
    """
    df_presupuestos = cargar_todos()
    df_clientes = cargar_clientes()

    # Calcular métricas y segmento de cliente
    df_metricas = calcular_metricas_clientes(df_presupuestos, params=params)

    # Añadir segmento a presupuestos
    segmento_map = dict(zip(df_metricas['Código'], df_metricas['Segmento_Cliente']))
    df_presupuestos['Segmento_Cliente'] = df_presupuestos['Código'].map(segmento_map).fillna('PROSPECTO')

    # Añadir métricas del cliente
    metricas_cols = ['Código', 'services_last_12m', 'services_last_24m', 'revenue_last_12m',
                     'revenue_last_24m', 'total_services', 'total_revenue', 'days_since_last_service']
    df_presupuestos = df_presupuestos.merge(
        df_metricas[metricas_cols],
        on='Código',
        how='left'
    )

    # Añadir datos del cliente desde tabla clientes
    df_clientes_simple = df_clientes[['Cod_Cliente', 'Nombre_Cliente', 'NIF', 'Población', 'Provincia', 'Pais', 'Mail', 'Grupo_Cliente']].copy()
    df_presupuestos = df_presupuestos.merge(
        df_clientes_simple,
        left_on='Código',
        right_on='Cod_Cliente',
        how='left'
    )

    # Añadir segmento a tabla de clientes
    df_clientes = df_clientes.merge(
        df_metricas[['Código', 'Segmento_Cliente', 'services_last_12m', 'services_last_24m',
                     'revenue_last_24m', 'total_services', 'total_revenue', 'days_since_last_service']],
        left_on='Cod_Cliente',
        right_on='Código',
        how='left'
    )
    df_clientes['Segmento_Cliente'] = df_clientes['Segmento_Cliente'].fillna('PROSPECTO')

    return df_presupuestos, df_clientes, df_metricas

def obtener_estadisticas_cliente(df_presupuestos, codigo_cliente):
    """Obtiene estadísticas de un cliente específico."""
    df_cliente = df_presupuestos[df_presupuestos['Código'] == codigo_cliente]

    if df_cliente.empty:
        return None

    return {
        'total_presupuestos': len(df_cliente),
        'aceptados': len(df_cliente[df_cliente['Estado presupuesto'].isin(ESTADOS_ACEPTADOS)]),
        'rechazados': len(df_cliente[df_cliente['Estado presupuesto'] == 'R']),
        'importe_total': df_cliente['Total importe'].sum(),
        'importe_aceptado': df_cliente[df_cliente['Estado presupuesto'].isin(ESTADOS_ACEPTADOS)]['Total importe'].sum(),
        'primera_fecha': df_cliente['Fecha alta'].min(),
        'ultima_fecha': df_cliente['Fecha alta'].max(),
        'tasa_conversion': len(df_cliente[df_cliente['Estado presupuesto'].isin(ESTADOS_ACEPTADOS)]) / len(df_cliente) * 100 if len(df_cliente) > 0 else 0
    }

def obtener_kpis(df):
    """Calcula los KPIs principales.

    IMPORTANTE: Cada Cod. Presupuesto es un presupuesto único que puede tener varias líneas.
    Se cuentan presupuestos únicos, no líneas.
    """
    # Contar presupuestos únicos (no líneas)
    total_presupuestos = df['Cod. Presupuesto'].nunique()

    # Presupuestos aceptados: únicos donde al menos una línea tiene estado A o AP
    df_aceptados = df[df['Estado presupuesto'].isin(ESTADOS_ACEPTADOS)]
    aceptados = df_aceptados['Cod. Presupuesto'].nunique()

    # Presupuestos rechazados: únicos donde al menos una línea tiene estado R
    df_rechazados = df[df['Estado presupuesto'] == 'R']
    rechazados = df_rechazados['Cod. Presupuesto'].nunique()

    # Presupuestos pendientes: únicos donde al menos una línea está pendiente
    df_pendientes = df[df['Estado presupuesto'].isin(ESTADOS_PENDIENTES)]
    pendientes = df_pendientes['Cod. Presupuesto'].nunique()

    tasa_conversion = (aceptados / total_presupuestos * 100) if total_presupuestos > 0 else 0

    # Los importes sí suman todas las líneas
    importe_aceptado = df_aceptados['Total importe'].sum()
    importe_total = df['Total importe'].sum()

    return {
        'total_presupuestos': total_presupuestos,
        'aceptados': aceptados,
        'rechazados': rechazados,
        'pendientes': pendientes,
        'tasa_conversion': tasa_conversion,
        'importe_aceptado': importe_aceptado,
        'importe_total': importe_total,
        'total_lineas': len(df)  # Para referencia, el número de líneas de servicio
    }

def obtener_presupuestos_pendientes(df):
    """Obtiene los presupuestos pendientes de respuesta (Enviado, Valorado)."""
    return df[df['Estado presupuesto'].isin(ESTADOS_PENDIENTES)].copy()

def obtener_clientes_inactivos(df, meses: int = 6):
    """
    Identifica clientes que no han tenido actividad en los últimos X meses.
    """
    fecha_limite = datetime.now() - timedelta(days=meses * 30)

    # Agrupar por cliente (contando presupuestos únicos)
    clientes = df.groupby('Cliente').agg({
        'Fecha alta': 'max',
        'Total importe': 'sum',
        'Cod. Presupuesto': 'nunique',  # Presupuestos únicos, no líneas
        'E-mail': 'first',
        'Teléfono': 'first',
        'Móvil': 'first',
        'Grupo de clientes': 'first'
    }).reset_index()

    clientes.columns = ['Cliente', 'Ultima Actividad', 'Importe Total',
                        'Num Presupuestos', 'Email', 'Telefono', 'Movil', 'Grupo']

    # Filtrar inactivos
    inactivos = clientes[clientes['Ultima Actividad'] < fecha_limite].copy()
    inactivos['Dias Inactivo'] = (datetime.now() - inactivos['Ultima Actividad']).dt.days

    return inactivos.sort_values('Importe Total', ascending=False)

def obtener_segmentacion(df, grupo: str = None, tipo_servicio: str = None,
                         importe_min: float = None, importe_max: float = None):
    """
    Filtra clientes según criterios de segmentación.
    """
    filtro = df.copy()

    if grupo and grupo != 'Todos':
        filtro = filtro[filtro['Grupo de clientes'] == grupo]

    if tipo_servicio and tipo_servicio != 'Todos':
        filtro = filtro[filtro['Tipo Servicio'] == tipo_servicio]

    if importe_min is not None:
        filtro = filtro[filtro['Total importe'] >= importe_min]

    if importe_max is not None:
        filtro = filtro[filtro['Total importe'] <= importe_max]

    # Obtener clientes únicos con email (contando presupuestos únicos)
    clientes = filtro[filtro['E-mail'].notna()].groupby('Cliente').agg({
        'E-mail': 'first',
        'Teléfono': 'first',
        'Móvil': 'first',
        'Total importe': 'sum',
        'Cod. Presupuesto': 'nunique',  # Presupuestos únicos, no líneas
        'Grupo de clientes': 'first'
    }).reset_index()

    clientes.columns = ['Cliente', 'Email', 'Telefono', 'Movil',
                        'Importe Total', 'Num Presupuestos', 'Grupo']

    return clientes

def obtener_analisis_conversion(df, por: str = 'Atendido por'):
    """
    Calcula tasas de conversión agrupadas por un campo específico.
    Cuenta presupuestos únicos, no líneas.
    """
    # Presupuestos únicos por grupo
    total_presup = df.groupby(por)['Cod. Presupuesto'].nunique().reset_index()
    total_presup.columns = [por, 'Total Presupuestos']

    # Presupuestos aceptados únicos
    df_aceptados = df[df['Estado presupuesto'].isin(ESTADOS_ACEPTADOS)]
    acept_presup = df_aceptados.groupby(por)['Cod. Presupuesto'].nunique().reset_index()
    acept_presup.columns = [por, 'Aceptados']

    # Importe aceptado
    importe_acept = df_aceptados.groupby(por)['Total importe'].sum().reset_index()
    importe_acept.columns = [por, 'Importe Aceptado']

    # Combinar
    analisis = total_presup.merge(acept_presup, on=por, how='left')
    analisis = analisis.merge(importe_acept, on=por, how='left')
    analisis = analisis.fillna(0)

    analisis['Tasa Conversion'] = (analisis['Aceptados'] / analisis['Total Presupuestos'].replace(0, 1) * 100).round(2)

    return analisis.sort_values('Total Presupuestos', ascending=False)

def obtener_tendencia_mensual(df):
    """Obtiene la tendencia mensual de presupuestos."""
    df_fecha = df[df['Fecha alta'].notna()].copy()
    df_fecha['Mes'] = df_fecha['Fecha alta'].dt.to_period('M')

    tendencia = df_fecha.groupby(['Mes', 'Estado presupuesto']).size().unstack(fill_value=0)
    tendencia.index = tendencia.index.astype(str)

    return tendencia

def obtener_grupos_clientes(df):
    """Obtiene lista de grupos de clientes únicos."""
    return ['Todos'] + sorted(df['Grupo de clientes'].dropna().unique().tolist())

def obtener_tipos_servicio(df):
    """Obtiene lista de tipos de servicio únicos."""
    return ['Todos'] + sorted(df['Tipo Servicio'].dropna().unique().tolist())

def obtener_comerciales(df):
    """Obtiene lista de comerciales únicos."""
    return ['Todos'] + sorted(df['Atendido por'].dropna().unique().tolist())

def obtener_formas_contacto(df):
    """Obtiene lista de formas de contacto únicas."""
    return ['Todos'] + sorted(df['Forma de contacto'].dropna().unique().tolist())

def obtener_fuentes(df):
    """Obtiene lista de fuentes (conocido por) únicas."""
    return ['Todos'] + sorted(df['Conocido por?'].dropna().unique().tolist())


def calcular_tiempo_anticipacion(df, solo_aceptados=True):
    """
    Calcula el tiempo de anticipación entre la fecha de alta del presupuesto
    y la fecha de salida del servicio.

    Parámetros:
    - df: DataFrame con los presupuestos
    - solo_aceptados: Si True, solo considera presupuestos aceptados (A, AP)

    Retorna: DataFrame con métricas de anticipación por presupuesto
    """
    df_calc = df.copy()

    # Filtrar solo aceptados si se requiere
    if solo_aceptados:
        df_calc = df_calc[df_calc['Estado presupuesto'].isin(ESTADOS_ACEPTADOS)]

    # Necesitamos ambas fechas
    df_calc = df_calc[df_calc['Fecha alta'].notna() & df_calc['Fecha Salida'].notna()]

    # Calcular días de anticipación
    df_calc['Dias_Anticipacion'] = (df_calc['Fecha Salida'] - df_calc['Fecha alta']).dt.days

    # Solo considerar anticipaciones positivas (servicio después de solicitud)
    df_calc = df_calc[df_calc['Dias_Anticipacion'] >= 0]

    # Calcular meses de anticipación
    df_calc['Meses_Anticipacion'] = df_calc['Dias_Anticipacion'] / 30.44  # Promedio días por mes

    return df_calc


def obtener_anticipacion_por_tipo(df, tipos_servicio_db=None):
    """
    Obtiene estadísticas de tiempo de anticipación por tipo de servicio.

    Parámetros:
    - df: DataFrame con los presupuestos
    - tipos_servicio_db: Dict con las descripciones de tipos de servicio

    Retorna: DataFrame con estadísticas por tipo de servicio
    """
    df_anticipacion = calcular_tiempo_anticipacion(df, solo_aceptados=True)

    if df_anticipacion.empty:
        return pd.DataFrame()

    # Añadir descripción del tipo
    if tipos_servicio_db:
        df_anticipacion['Tipo_Descripcion'] = df_anticipacion['Tipo Servicio'].apply(
            lambda x: tipos_servicio_db.get(x, {}).get('descripcion', '') or x if pd.notna(x) else 'Sin definir'
        )
        # Normalizar a Primera mayúscula
        df_anticipacion['Tipo_Descripcion'] = df_anticipacion['Tipo_Descripcion'].apply(
            lambda x: x.strip().capitalize() if isinstance(x, str) else x
        )
    else:
        df_anticipacion['Tipo_Descripcion'] = df_anticipacion['Tipo Servicio']

    # Agrupar por tipo (descripción)
    stats = df_anticipacion.groupby('Tipo_Descripcion').agg({
        'Dias_Anticipacion': ['mean', 'median', 'min', 'max', 'std', 'count'],
        'Meses_Anticipacion': ['mean', 'median'],
        'Total importe': 'sum'
    }).reset_index()

    # Aplanar columnas
    stats.columns = [
        'Tipo Servicio',
        'Dias_Media', 'Dias_Mediana', 'Dias_Min', 'Dias_Max', 'Dias_Desv', 'Num_Servicios',
        'Meses_Media', 'Meses_Mediana',
        'Importe_Total'
    ]

    # Redondear valores
    stats['Dias_Media'] = stats['Dias_Media'].round(0).astype(int)
    stats['Dias_Mediana'] = stats['Dias_Mediana'].round(0).astype(int)
    stats['Meses_Media'] = stats['Meses_Media'].round(1)
    stats['Meses_Mediana'] = stats['Meses_Mediana'].round(1)
    stats['Dias_Desv'] = stats['Dias_Desv'].round(0)

    return stats.sort_values('Num_Servicios', ascending=False)


def obtener_distribucion_anticipacion(df, tipo_servicio=None):
    """
    Obtiene la distribución de anticipación para visualización.

    Parámetros:
    - df: DataFrame con los presupuestos
    - tipo_servicio: Código de tipo de servicio a filtrar (opcional)

    Retorna: DataFrame con los datos para histograma
    """
    df_anticipacion = calcular_tiempo_anticipacion(df, solo_aceptados=True)

    if tipo_servicio and tipo_servicio != 'Todos':
        df_anticipacion = df_anticipacion[df_anticipacion['Tipo Servicio'] == tipo_servicio]

    return df_anticipacion[['Cod. Presupuesto', 'Cliente', 'Tipo Servicio',
                           'Fecha alta', 'Fecha Salida', 'Dias_Anticipacion',
                           'Meses_Anticipacion', 'Total importe']]


def obtener_tendencia_anticipacion_mensual(df, tipos_servicio_db=None):
    """
    Obtiene la tendencia de anticipación promedio por mes de solicitud.

    Retorna: DataFrame con anticipación media por mes
    """
    df_anticipacion = calcular_tiempo_anticipacion(df, solo_aceptados=True)

    if df_anticipacion.empty:
        return pd.DataFrame()

    # Agrupar por mes de solicitud
    df_anticipacion['Mes_Solicitud'] = df_anticipacion['Fecha alta'].dt.to_period('M').astype(str)

    tendencia = df_anticipacion.groupby('Mes_Solicitud').agg({
        'Dias_Anticipacion': 'mean',
        'Meses_Anticipacion': 'mean',
        'Cod. Presupuesto': 'count'
    }).reset_index()

    tendencia.columns = ['Mes', 'Dias_Media', 'Meses_Media', 'Num_Servicios']
    tendencia['Dias_Media'] = tendencia['Dias_Media'].round(0)
    tendencia['Meses_Media'] = tendencia['Meses_Media'].round(1)

    return tendencia


# ============================================
# SISTEMA DE DESTACADOS
# ============================================
import sqlite3

DB_PATH = DATA_PATH / "crm_notas.db"

def get_db_connection():
    """Obtiene conexión a la base de datos"""
    return sqlite3.connect(str(DB_PATH))

# --- PRESUPUESTOS DESTACADOS ---
def obtener_presupuestos_destacados():
    """Obtiene todos los presupuestos destacados"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT cod_presupuesto, prioridad, nota, fecha_marcado FROM presupuestos_destacados")
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: {'prioridad': row[1], 'nota': row[2], 'fecha': row[3]} for row in rows}

def marcar_presupuesto_destacado(cod_presupuesto, prioridad=1, nota=''):
    """Marca un presupuesto como destacado"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO presupuestos_destacados (cod_presupuesto, prioridad, nota, fecha_marcado)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    """, (str(cod_presupuesto), prioridad, nota))
    conn.commit()
    conn.close()

def desmarcar_presupuesto_destacado(cod_presupuesto):
    """Quita un presupuesto de destacados"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM presupuestos_destacados WHERE cod_presupuesto = ?", (str(cod_presupuesto),))
    conn.commit()
    conn.close()

def es_presupuesto_destacado(cod_presupuesto):
    """Comprueba si un presupuesto está destacado"""
    destacados = obtener_presupuestos_destacados()
    return str(cod_presupuesto) in destacados

# --- CLIENTES DESTACADOS ---
def obtener_clientes_destacados():
    """Obtiene todos los clientes destacados"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT cod_cliente, nombre_cliente, prioridad, nota, fecha_marcado FROM clientes_destacados")
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: {'nombre': row[1], 'prioridad': row[2], 'nota': row[3], 'fecha': row[4]} for row in rows}

def marcar_cliente_destacado(cod_cliente, nombre_cliente='', prioridad=1, nota=''):
    """Marca un cliente como destacado"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO clientes_destacados (cod_cliente, nombre_cliente, prioridad, nota, fecha_marcado)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (str(cod_cliente), nombre_cliente, prioridad, nota))
    conn.commit()
    conn.close()

def desmarcar_cliente_destacado(cod_cliente):
    """Quita un cliente de destacados"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clientes_destacados WHERE cod_cliente = ?", (str(cod_cliente),))
    conn.commit()
    conn.close()

def es_cliente_destacado(cod_cliente):
    """Comprueba si un cliente está destacado"""
    destacados = obtener_clientes_destacados()
    return str(cod_cliente) in destacados
