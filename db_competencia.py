"""
Funciones de base de datos para el módulo de Competencia
Usa Supabase para persistencia en la nube
Con caché para mejor rendimiento
"""
import streamlit as st
from supabase_client import get_admin_client
from datetime import datetime

# Factor de normalización para comparar precios entre tipos de vehículo
FACTOR_VEHICULO_NORM = {
    'STD': 1.0,
    'EXEC': 1.15,
    'VIP': 1.30,
    'MICRO': 0.65,
    'MINI': 0.80,
    'GRAN': 1.10,
}

# ============================================
# FUNCIONES DE CACHÉ
# ============================================

def limpiar_cache_competencia():
    """Limpia todo el caché de competencia."""
    st.cache_data.clear()

def limpiar_cache_competidores():
    """Limpia caché de competidores."""
    _obtener_competidores_cached.clear()
    _obtener_estadisticas_flota_cached.clear()
    _obtener_comparativa_flotas_cached.clear()

def limpiar_cache_vehiculos():
    """Limpia caché de vehículos."""
    _obtener_vehiculos_cached.clear()
    _obtener_estadisticas_flota_cached.clear()
    _obtener_comparativa_flotas_cached.clear()

def limpiar_cache_cotizaciones():
    """Limpia caché de cotizaciones."""
    _obtener_cotizaciones_cached.clear()
    _obtener_estadisticas_mercado_cached.clear()
    _obtener_ranking_cached.clear()


# ============================================
# COMPETIDORES (con caché)
# ============================================

@st.cache_data(ttl=300, show_spinner=False)
def _obtener_competidores_cached(solo_activos: bool = True) -> list:
    """Versión cacheada de obtener competidores."""
    client = get_admin_client()
    query = client.table('competidores').select('*')
    if solo_activos:
        query = query.eq('activo', True)
    result = query.order('nombre').execute()
    return result.data or []

def obtener_competidores(solo_activos: bool = True) -> list:
    """Obtiene la lista de competidores (cacheado)."""
    return _obtener_competidores_cached(solo_activos)

def guardar_competidor(nombre: str, segmento: str = 'estandar', zona_operacion: str = '',
                       flota_estimada: int = None, fortalezas: str = '',
                       debilidades: str = '', notas: str = '') -> int:
    """Guarda o actualiza un competidor."""
    client = get_admin_client()
    existe = client.table('competidores').select('id').eq('nombre', nombre).execute()

    if existe.data:
        client.table('competidores').update({
            'segmento': segmento,
            'zona_operacion': zona_operacion,
            'flota_estimada': flota_estimada,
            'fortalezas': fortalezas,
            'debilidades': debilidades,
            'notas': notas,
            'fecha_actualizacion': datetime.now().isoformat()
        }).eq('nombre', nombre).execute()
        limpiar_cache_competidores()
        return existe.data[0]['id']
    else:
        result = client.table('competidores').insert({
            'nombre': nombre,
            'segmento': segmento,
            'zona_operacion': zona_operacion,
            'flota_estimada': flota_estimada,
            'fortalezas': fortalezas,
            'debilidades': debilidades,
            'notas': notas
        }).execute()
        limpiar_cache_competidores()
        return result.data[0]['id'] if result.data else None

def obtener_competidor_por_id(competidor_id: int) -> dict:
    """Obtiene un competidor por su ID."""
    competidores = obtener_competidores()
    return next((c for c in competidores if c['id'] == competidor_id), None)

def eliminar_competidor(competidor_id: int) -> bool:
    """Elimina un competidor y sus datos relacionados."""
    client = get_admin_client()
    client.table('cotizaciones_competencia').delete().eq('competidor_id', competidor_id).execute()
    client.table('vehiculos_competencia').delete().eq('competidor_id', competidor_id).execute()
    result = client.table('competidores').delete().eq('id', competidor_id).execute()
    limpiar_cache_competidores()
    limpiar_cache_vehiculos()
    limpiar_cache_cotizaciones()
    return len(result.data) > 0 if result.data else False


# ============================================
# COTIZACIONES (con caché)
# ============================================

@st.cache_data(ttl=300, show_spinner=False)
def _obtener_cotizaciones_cached(competidor_id: int = None, tipo_servicio: str = None) -> list:
    """Versión cacheada de obtener cotizaciones."""
    client = get_admin_client()
    query = client.table('cotizaciones_competencia').select('*, competidores(nombre)')

    if competidor_id:
        query = query.eq('competidor_id', competidor_id)
    if tipo_servicio:
        query = query.eq('tipo_servicio', tipo_servicio)

    result = query.order('fecha_captura', desc=True).execute()

    datos = []
    for row in result.data or []:
        row['competidor_nombre'] = row.get('competidores', {}).get('nombre', '') if row.get('competidores') else ''
        datos.append(row)
    return datos

def obtener_cotizaciones_competencia(competidor_id: int = None, tipo_servicio: str = None) -> list:
    """Obtiene cotizaciones de la competencia (cacheado)."""
    return _obtener_cotizaciones_cached(competidor_id, tipo_servicio)

def guardar_cotizacion_competencia(competidor_id: int, tipo_servicio: str, precio: float,
                                   tipo_vehiculo: str = 'STD', km_estimados: int = None,
                                   duracion_horas: float = None, origen: str = '', destino: str = '',
                                   fecha_captura: str = None, fuente: str = '', notas: str = '') -> int:
    """Guarda una cotización de la competencia."""
    client = get_admin_client()

    if not fecha_captura:
        fecha_captura = datetime.now().strftime('%Y-%m-%d')

    result = client.table('cotizaciones_competencia').insert({
        'competidor_id': competidor_id,
        'tipo_servicio': tipo_servicio,
        'precio': precio,
        'tipo_vehiculo': tipo_vehiculo,
        'km_estimados': km_estimados,
        'duracion_horas': duracion_horas,
        'origen': origen,
        'destino': destino,
        'fecha_captura': fecha_captura,
        'fuente': fuente,
        'notas': notas
    }).execute()

    limpiar_cache_cotizaciones()
    return result.data[0]['id'] if result.data else None

def eliminar_cotizacion_competencia(cotizacion_id: int) -> bool:
    """Elimina una cotización."""
    client = get_admin_client()
    result = client.table('cotizaciones_competencia').delete().eq('id', cotizacion_id).execute()
    limpiar_cache_cotizaciones()
    return len(result.data) > 0 if result.data else False


# ============================================
# VEHÍCULOS (con caché)
# ============================================

@st.cache_data(ttl=300, show_spinner=False)
def _obtener_vehiculos_cached(competidor_id: int = None, solo_activos: bool = True) -> list:
    """Versión cacheada de obtener vehículos."""
    client = get_admin_client()
    query = client.table('vehiculos_competencia').select('*, competidores(nombre)')

    if competidor_id:
        query = query.eq('competidor_id', competidor_id)
    if solo_activos:
        query = query.eq('activo', True)

    result = query.order('plazas', desc=True).execute()

    datos = []
    for row in result.data or []:
        row['competidor_nombre'] = row.get('competidores', {}).get('nombre', '') if row.get('competidores') else ''
        datos.append(row)
    return datos

def obtener_vehiculos_competencia(competidor_id: int = None, solo_activos: bool = True) -> list:
    """Obtiene vehículos de la competencia (cacheado)."""
    return _obtener_vehiculos_cached(competidor_id, solo_activos)

def guardar_vehiculo_competencia(competidor_id: int, matricula: str = None, tipo_vehiculo: str = 'AUTOBUS',
                                 marca: str = '', modelo: str = '', plazas: int = None,
                                 ano_matriculacion: int = None, distintivo_ambiental: str = '',
                                 pmr: bool = False, wc: bool = False, wifi: bool = False,
                                 escolar: bool = False, observaciones: str = '') -> int:
    """Guarda un vehículo de competidor."""
    client = get_admin_client()

    edad = None
    if ano_matriculacion:
        edad = round(datetime.now().year - ano_matriculacion + (datetime.now().month / 12), 1)

    result = client.table('vehiculos_competencia').insert({
        'competidor_id': competidor_id,
        'matricula': matricula,
        'tipo_vehiculo': tipo_vehiculo,
        'marca': marca,
        'modelo': modelo,
        'plazas': plazas,
        'ano_matriculacion': ano_matriculacion,
        'edad': edad,
        'distintivo_ambiental': distintivo_ambiental,
        'pmr': pmr,
        'wc': wc,
        'wifi': wifi,
        'escolar': escolar,
        'observaciones': observaciones
    }).execute()

    limpiar_cache_vehiculos()
    return result.data[0]['id'] if result.data else None

def actualizar_vehiculo_competencia(vehiculo_id: int, **kwargs) -> bool:
    """Actualiza un vehículo de la competencia."""
    client = get_admin_client()

    if not kwargs:
        return False

    if 'ano_matriculacion' in kwargs and kwargs['ano_matriculacion']:
        kwargs['edad'] = round(datetime.now().year - kwargs['ano_matriculacion'] + (datetime.now().month / 12), 1)

    kwargs['fecha_actualizacion'] = datetime.now().isoformat()

    result = client.table('vehiculos_competencia').update(kwargs).eq('id', vehiculo_id).execute()
    limpiar_cache_vehiculos()
    return len(result.data) > 0 if result.data else False

def eliminar_vehiculo_competencia(vehiculo_id: int) -> bool:
    """Elimina un vehículo (soft delete)."""
    client = get_admin_client()
    result = client.table('vehiculos_competencia').update({
        'activo': False,
        'fecha_actualizacion': datetime.now().isoformat()
    }).eq('id', vehiculo_id).execute()
    limpiar_cache_vehiculos()
    return len(result.data) > 0 if result.data else False

def importar_vehiculos_masivo(competidor_id: int, vehiculos: list) -> int:
    """Importa múltiples vehículos para un competidor."""
    count = 0
    for v in vehiculos:
        try:
            guardar_vehiculo_competencia(
                competidor_id=competidor_id,
                matricula=v.get('matricula'),
                tipo_vehiculo=v.get('tipo_vehiculo', 'AUTOBUS'),
                marca=v.get('marca', ''),
                modelo=v.get('modelo', ''),
                plazas=v.get('plazas'),
                ano_matriculacion=v.get('ano_matriculacion'),
                distintivo_ambiental=v.get('distintivo_ambiental', ''),
                pmr=v.get('pmr', False),
                wc=v.get('wc', False),
                wifi=v.get('wifi', False),
                escolar=v.get('escolar', False),
                observaciones=v.get('observaciones', '')
            )
            count += 1
        except Exception as e:
            print(f"Error importando vehículo: {e}")
    return count


# ============================================
# ESTADÍSTICAS (con caché)
# ============================================

@st.cache_data(ttl=300, show_spinner=False)
def _obtener_estadisticas_flota_cached() -> list:
    """Versión cacheada de estadísticas de flota."""
    client = get_admin_client()

    competidores = client.table('competidores').select('id, nombre').eq('activo', True).execute().data or []
    vehiculos_todos = client.table('vehiculos_competencia').select('*').eq('activo', True).execute().data or []

    # Agrupar vehículos por competidor
    vehiculos_por_comp = {}
    for v in vehiculos_todos:
        cid = v['competidor_id']
        if cid not in vehiculos_por_comp:
            vehiculos_por_comp[cid] = []
        vehiculos_por_comp[cid].append(v)

    stats = []
    for comp in competidores:
        vehiculos = vehiculos_por_comp.get(comp['id'], [])
        total = len(vehiculos)

        if total == 0:
            stats.append({
                'competidor_id': comp['id'],
                'competidor': comp['nombre'],
                'total_vehiculos': 0,
                'buses_grandes': 0,
                'buses_medianos': 0,
                'microbuses': 0,
                'edad_media': None,
                'capacidad_total': 0,
                'con_pmr': 0,
                'con_wc': 0,
                'con_wifi': 0,
                'escolares': 0
            })
            continue

        buses_grandes = sum(1 for v in vehiculos if (v.get('plazas') or 0) >= 50)
        buses_medianos = sum(1 for v in vehiculos if 30 <= (v.get('plazas') or 0) < 50)
        microbuses = sum(1 for v in vehiculos if (v.get('plazas') or 0) < 30)

        edades = [v.get('edad') for v in vehiculos if v.get('edad')]
        edad_media = round(sum(edades) / len(edades), 1) if edades else None

        stats.append({
            'competidor_id': comp['id'],
            'competidor': comp['nombre'],
            'total_vehiculos': total,
            'buses_grandes': buses_grandes,
            'buses_medianos': buses_medianos,
            'microbuses': microbuses,
            'edad_media': edad_media,
            'capacidad_total': sum(v.get('plazas') or 0 for v in vehiculos),
            'con_pmr': sum(1 for v in vehiculos if v.get('pmr')),
            'con_wc': sum(1 for v in vehiculos if v.get('wc')),
            'con_wifi': sum(1 for v in vehiculos if v.get('wifi')),
            'escolares': sum(1 for v in vehiculos if v.get('escolar'))
        })

    stats.sort(key=lambda x: x['total_vehiculos'], reverse=True)
    return stats

def obtener_estadisticas_flota_competencia(competidor_id: int = None) -> list:
    """Obtiene estadísticas de la flota de competidores (cacheado)."""
    stats = _obtener_estadisticas_flota_cached()
    if competidor_id:
        return [s for s in stats if s['competidor_id'] == competidor_id]
    return stats

@st.cache_data(ttl=300, show_spinner=False)
def _obtener_comparativa_flotas_cached() -> dict:
    """Versión cacheada de comparativa de flotas."""
    stats = _obtener_estadisticas_flota_cached()

    if not stats:
        return {'competidores': [], 'resumen': None}

    total_vehiculos = sum(s['total_vehiculos'] or 0 for s in stats)
    total_capacidad = sum(s['capacidad_total'] or 0 for s in stats)

    edad_media_mercado = 0
    if total_vehiculos > 0:
        suma_ponderada = sum((s['edad_media'] or 0) * (s['total_vehiculos'] or 0) for s in stats)
        edad_media_mercado = round(suma_ponderada / total_vehiculos, 1)

    return {
        'competidores': stats,
        'resumen': {
            'total_competidores': len([s for s in stats if s['total_vehiculos'] > 0]),
            'total_vehiculos_mercado': total_vehiculos,
            'capacidad_total_mercado': total_capacidad,
            'edad_media_mercado': edad_media_mercado,
            'lider_flota': max(stats, key=lambda x: x['total_vehiculos'] or 0)['competidor'] if stats else None
        }
    }

def obtener_comparativa_flotas() -> dict:
    """Obtiene una comparativa de flotas entre competidores (cacheado)."""
    return _obtener_comparativa_flotas_cached()

@st.cache_data(ttl=300, show_spinner=False)
def _obtener_estadisticas_mercado_cached(tipo_servicio: str = None) -> list:
    """Versión cacheada de estadísticas de mercado."""
    client = get_admin_client()

    query = client.table('cotizaciones_competencia').select('tipo_servicio, tipo_vehiculo, precio')
    if tipo_servicio:
        query = query.eq('tipo_servicio', tipo_servicio)

    result = query.execute().data or []

    if not result:
        return []

    from collections import defaultdict
    grupos = defaultdict(list)
    for row in result:
        key = (row['tipo_servicio'], row['tipo_vehiculo'])
        grupos[key].append(float(row['precio']))

    stats = []
    for (tipo_serv, tipo_veh), precios in grupos.items():
        stats.append({
            'tipo_servicio': tipo_serv,
            'tipo_vehiculo': tipo_veh,
            'precio_medio': round(sum(precios) / len(precios), 2),
            'precio_min': min(precios),
            'precio_max': max(precios),
            'num_cotizaciones': len(precios)
        })

    return stats

def obtener_estadisticas_mercado(tipo_servicio: str = None) -> list:
    """Obtiene estadísticas agregadas del mercado (cacheado)."""
    return _obtener_estadisticas_mercado_cached(tipo_servicio)

@st.cache_data(ttl=300, show_spinner=False)
def _obtener_ranking_cached() -> list:
    """Versión cacheada de ranking de competidores."""
    client = get_admin_client()

    result = client.table('cotizaciones_competencia').select('competidor_id, precio, competidores(nombre, segmento)').execute()

    if not result.data:
        return []

    from collections import defaultdict
    grupos = defaultdict(lambda: {'precios': [], 'nombre': '', 'segmento': ''})

    for row in result.data:
        comp_id = row['competidor_id']
        grupos[comp_id]['precios'].append(float(row['precio']))
        if row.get('competidores'):
            grupos[comp_id]['nombre'] = row['competidores'].get('nombre', '')
            grupos[comp_id]['segmento'] = row['competidores'].get('segmento', '')

    ranking = []
    for comp_id, data in grupos.items():
        if data['precios']:
            ranking.append({
                'competidor_id': comp_id,
                'nombre': data['nombre'],
                'segmento': data['segmento'],
                'precio_medio': round(sum(data['precios']) / len(data['precios']), 2),
                'num_cotizaciones': len(data['precios'])
            })

    ranking.sort(key=lambda x: x['precio_medio'])
    return ranking

def obtener_ranking_competidores() -> list:
    """Obtiene ranking de competidores por precio medio (cacheado)."""
    return _obtener_ranking_cached()

def obtener_posicion_por_servicio(tipo_servicio: str, tipo_vehiculo: str = None) -> dict:
    """Obtiene la posición de precios para un tipo de servicio."""
    cotizaciones = obtener_cotizaciones_competencia(tipo_servicio=tipo_servicio)

    if tipo_vehiculo:
        cotizaciones = [c for c in cotizaciones if c.get('tipo_vehiculo') == tipo_vehiculo]

    if not cotizaciones:
        return {'posiciones': [], 'precio_medio': 0, 'precio_min': 0, 'precio_max': 0}

    from collections import defaultdict
    grupos = defaultdict(lambda: {'precios': [], 'nombre': ''})

    for row in cotizaciones:
        comp_id = row['competidor_id']
        grupos[comp_id]['precios'].append(float(row['precio']))
        grupos[comp_id]['nombre'] = row.get('competidor_nombre', '')

    posiciones = []
    for comp_id, data in grupos.items():
        if data['precios']:
            posiciones.append({
                'competidor_id': comp_id,
                'nombre': data['nombre'],
                'precio_medio': round(sum(data['precios']) / len(data['precios']), 2)
            })

    posiciones.sort(key=lambda x: x['precio_medio'])

    todos_precios = [float(c['precio']) for c in cotizaciones]

    return {
        'posiciones': posiciones,
        'precio_medio': round(sum(todos_precios) / len(todos_precios), 2),
        'precio_min': min(todos_precios),
        'precio_max': max(todos_precios)
    }

def detectar_alertas_competencia(umbral_diferencia: float = 15) -> list:
    """Detecta alertas cuando los precios de David difieren significativamente del mercado."""
    return []

def comparar_con_tarifa_david(tipo_servicio: str, tipo_vehiculo: str, km: int, horas: float) -> dict:
    """Compara precios del mercado con tarifa de David."""
    return {
        'precio_david': None,
        'resumen': None,
        'comparacion': []
    }
