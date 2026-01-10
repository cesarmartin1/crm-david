"""
Base de datos persistente usando Supabase
Migrado de SQLite local para persistencia en la nube
"""
import streamlit as st
from datetime import datetime
from supabase_client import get_admin_client

# ============================================
# FUNCIONES DE CACHÉ
# ============================================

def limpiar_cache_tipos():
    """Limpia caché de tipos de servicio."""
    obtener_tipos_servicio_db.clear()

def limpiar_cache_config():
    """Limpia caché de configuración."""
    obtener_tramos_comision.clear()
    obtener_bonus_objetivos.clear()
    obtener_puntos_acciones.clear()
    obtener_premios.clear()

def limpiar_cache_tarifas():
    """Limpia caché de tarifas."""
    obtener_temporadas.clear()
    obtener_tipos_bus.clear()
    obtener_tipos_cliente.clear()
    obtener_tarifas_servicio.clear()


# ============================================
# NOTAS
# ============================================

def agregar_nota(cod_presupuesto: str, cliente: str, contenido: str, tipo: str, usuario: str = "Sistema"):
    """Agrega una nota a un cliente o presupuesto."""
    client = get_admin_client()
    client.table('notas').insert({
        'cod_presupuesto': cod_presupuesto,
        'cliente': cliente,
        'contenido': contenido,
        'tipo': tipo,
        'usuario': usuario
    }).execute()

def obtener_notas_cliente(cliente: str):
    """Obtiene todas las notas de un cliente."""
    client = get_admin_client()
    result = client.table('notas').select('*').eq('cliente', cliente).order('fecha', desc=True).execute()
    return result.data or []

def obtener_notas_presupuesto(cod_presupuesto: str):
    """Obtiene todas las notas de un presupuesto."""
    client = get_admin_client()
    result = client.table('notas').select('*').eq('cod_presupuesto', cod_presupuesto).order('fecha', desc=True).execute()
    return result.data or []

def obtener_todas_notas(limite: int = 100):
    """Obtiene las últimas notas."""
    client = get_admin_client()
    result = client.table('notas').select('*').order('fecha', desc=True).limit(limite).execute()
    return result.data or []

def buscar_notas(termino: str):
    """Busca notas que contengan el término."""
    client = get_admin_client()
    result = client.table('notas').select('*').ilike('contenido', f'%{termino}%').order('fecha', desc=True).execute()
    return result.data or []

def eliminar_nota(nota_id: int):
    """Elimina una nota por ID."""
    client = get_admin_client()
    client.table('notas').delete().eq('id', nota_id).execute()


# ============================================
# TIPOS DE SERVICIO
# ============================================

def guardar_tipo_servicio(codigo: str, descripcion: str, categoria: str = ""):
    """Guarda o actualiza un tipo de servicio."""
    client = get_admin_client()
    client.table('tipos_servicio').upsert({
        'codigo': codigo,
        'descripcion': descripcion,
        'categoria': categoria
    }).execute()
    limpiar_cache_tipos()

@st.cache_data(ttl=600)
def obtener_tipos_servicio_db():
    """Obtiene todos los tipos de servicio (cacheado)."""
    client = get_admin_client()
    result = client.table('tipos_servicio').select('*').order('codigo').execute()
    return {t['codigo']: {'descripcion': t['descripcion'], 'categoria': t['categoria']} for t in (result.data or [])}

def obtener_descripcion_tipo(codigo: str):
    """Obtiene la descripción de un tipo de servicio."""
    tipos = obtener_tipos_servicio_db()
    return tipos.get(codigo, {}).get('descripcion')

def eliminar_tipo_servicio(codigo: str):
    """Elimina un tipo de servicio."""
    client = get_admin_client()
    client.table('tipos_servicio').delete().eq('codigo', codigo).execute()
    limpiar_cache_tipos()

def guardar_tipos_servicio_masivo(tipos: dict):
    """Guarda múltiples tipos de servicio."""
    client = get_admin_client()
    for codigo, datos in tipos.items():
        client.table('tipos_servicio').upsert({
            'codigo': codigo,
            'descripcion': datos.get('descripcion', ''),
            'categoria': datos.get('categoria', '')
        }).execute()
    limpiar_cache_tipos()


# ============================================
# CONFIGURACIÓN INCENTIVOS
# ============================================

def guardar_config_incentivo(clave: str, valor: str, descripcion: str = ""):
    """Guarda una configuración de incentivo."""
    client = get_admin_client()
    client.table('config_general').upsert({
        'clave': clave,
        'valor': valor,
        'descripcion': descripcion,
        'fecha_actualizacion': datetime.now().isoformat()
    }).execute()

def obtener_config_incentivo(clave: str, default: str = None):
    """Obtiene una configuración de incentivo."""
    client = get_admin_client()
    result = client.table('config_general').select('valor').eq('clave', clave).execute()
    if result.data:
        return result.data[0]['valor']
    return default

def obtener_todas_config_incentivos():
    """Obtiene todas las configuraciones."""
    client = get_admin_client()
    result = client.table('config_general').select('*').execute()
    return {r['clave']: r['valor'] for r in (result.data or [])}


# ============================================
# COMISIONES - TRAMOS
# ============================================

def guardar_tramo_comision(desde: float, hasta: float, porcentaje: float):
    """Guarda un tramo de comisión."""
    client = get_admin_client()
    client.table('comisiones_tramos').insert({
        'desde': desde,
        'hasta': hasta,
        'porcentaje': porcentaje
    }).execute()
    limpiar_cache_config()

@st.cache_data(ttl=600)
def obtener_tramos_comision():
    """Obtiene todos los tramos de comisión (cacheado)."""
    client = get_admin_client()
    result = client.table('comisiones_tramos').select('*').eq('activo', True).order('desde').execute()
    return result.data or []

def eliminar_tramo_comision(tramo_id: int):
    """Elimina un tramo de comisión."""
    client = get_admin_client()
    client.table('comisiones_tramos').delete().eq('id', tramo_id).execute()
    limpiar_cache_config()

def limpiar_tramos_comision():
    """Elimina todos los tramos de comisión."""
    client = get_admin_client()
    client.table('comisiones_tramos').delete().neq('id', 0).execute()
    limpiar_cache_config()


# ============================================
# BONUS POR OBJETIVOS
# ============================================

def guardar_bonus(nombre: str, tipo: str, condicion: str, valor_objetivo: float, importe_bonus: float):
    """Guarda un bonus por objetivo."""
    client = get_admin_client()
    client.table('bonus_objetivos').insert({
        'nombre': nombre,
        'tipo': tipo,
        'condicion': condicion,
        'valor_objetivo': valor_objetivo,
        'importe_bonus': importe_bonus
    }).execute()
    limpiar_cache_config()

@st.cache_data(ttl=600)
def obtener_bonus_objetivos():
    """Obtiene todos los bonus activos (cacheado)."""
    client = get_admin_client()
    result = client.table('bonus_objetivos').select('*').eq('activo', True).execute()
    return result.data or []

def eliminar_bonus(bonus_id: int):
    """Elimina un bonus."""
    client = get_admin_client()
    client.table('bonus_objetivos').delete().eq('id', bonus_id).execute()
    limpiar_cache_config()

def limpiar_bonus():
    """Elimina todos los bonus."""
    client = get_admin_client()
    client.table('bonus_objetivos').delete().neq('id', 0).execute()
    limpiar_cache_config()


# ============================================
# PUNTOS POR ACCIONES
# ============================================

def guardar_puntos_accion(nombre: str, accion: str, puntos: int):
    """Guarda una acción con puntos."""
    client = get_admin_client()
    client.table('puntos_acciones').insert({
        'nombre': nombre,
        'accion': accion,
        'puntos': puntos
    }).execute()
    limpiar_cache_config()

@st.cache_data(ttl=600)
def obtener_puntos_acciones():
    """Obtiene todas las acciones con puntos (cacheado)."""
    client = get_admin_client()
    result = client.table('puntos_acciones').select('*').eq('activo', True).execute()
    return result.data or []

def eliminar_puntos_accion(accion_id: int):
    """Elimina una acción de puntos."""
    client = get_admin_client()
    client.table('puntos_acciones').delete().eq('id', accion_id).execute()
    limpiar_cache_config()

def limpiar_puntos_acciones():
    """Elimina todas las acciones de puntos."""
    client = get_admin_client()
    client.table('puntos_acciones').delete().neq('id', 0).execute()
    limpiar_cache_config()


# ============================================
# PREMIOS CANJEABLES
# ============================================

def guardar_premio(nombre: str, puntos_requeridos: int, descripcion: str = ""):
    """Guarda un premio canjeable."""
    client = get_admin_client()
    client.table('puntos_premios').insert({
        'nombre': nombre,
        'puntos_requeridos': puntos_requeridos,
        'descripcion': descripcion
    }).execute()
    limpiar_cache_config()

@st.cache_data(ttl=600)
def obtener_premios():
    """Obtiene todos los premios activos (cacheado)."""
    client = get_admin_client()
    result = client.table('puntos_premios').select('*').eq('activo', True).order('puntos_requeridos').execute()
    return result.data or []

def eliminar_premio(premio_id: int):
    """Elimina un premio."""
    client = get_admin_client()
    client.table('puntos_premios').delete().eq('id', premio_id).execute()
    limpiar_cache_config()

def limpiar_premios():
    """Elimina todos los premios."""
    client = get_admin_client()
    client.table('puntos_premios').delete().neq('id', 0).execute()
    limpiar_cache_config()


# ============================================
# PREMIOS ESPECIALES POR PRESUPUESTO
# ============================================

def guardar_premio_presupuesto(cod_presupuesto: str, cliente: str, comercial: str,
                                importe_presupuesto: float, premio_euros: float, motivo: str = ""):
    """Guarda un premio especial por presupuesto."""
    client = get_admin_client()
    client.table('premios_presupuesto').insert({
        'cod_presupuesto': cod_presupuesto,
        'cliente': cliente,
        'comercial': comercial,
        'importe_presupuesto': importe_presupuesto,
        'premio_euros': premio_euros,
        'motivo': motivo
    }).execute()

def obtener_premios_presupuesto(solo_activos: bool = True, solo_pendientes: bool = False):
    """Obtiene los premios especiales por presupuesto."""
    client = get_admin_client()
    query = client.table('premios_presupuesto').select('*')
    if solo_activos:
        query = query.eq('activo', True)
    if solo_pendientes:
        query = query.eq('conseguido', False)
    result = query.order('fecha_creacion', desc=True).execute()
    return result.data or []

def marcar_premio_conseguido(premio_id: int):
    """Marca un premio como conseguido."""
    client = get_admin_client()
    client.table('premios_presupuesto').update({
        'conseguido': True,
        'fecha_conseguido': datetime.now().isoformat()
    }).eq('id', premio_id).execute()

def eliminar_premio_presupuesto(premio_id: int):
    """Elimina un premio de presupuesto."""
    client = get_admin_client()
    client.table('premios_presupuesto').update({'activo': False}).eq('id', premio_id).execute()

def obtener_premio_por_presupuesto(cod_presupuesto: str):
    """Obtiene el premio asociado a un presupuesto."""
    client = get_admin_client()
    result = client.table('premios_presupuesto').select('*').eq('cod_presupuesto', cod_presupuesto).eq('activo', True).execute()
    return result.data[0] if result.data else None


# ============================================
# HISTORIAL DE INCENTIVOS
# ============================================

def guardar_incentivo_historico(comercial: str, periodo: str, importe_facturado: float,
                                 comision_base: float, bonus_total: float, puntos_totales: int, detalles: dict):
    """Guarda el histórico de incentivos de un comercial."""
    client = get_admin_client()
    import json
    client.table('incentivos_historico').insert({
        'comercial': comercial,
        'periodo': periodo,
        'importe_facturado': importe_facturado,
        'comision_base': comision_base,
        'bonus_total': bonus_total,
        'puntos_totales': puntos_totales,
        'detalles': json.dumps(detalles)
    }).execute()

def obtener_historico_incentivos(comercial: str = None, periodo: str = None):
    """Obtiene el histórico de incentivos."""
    client = get_admin_client()
    query = client.table('incentivos_historico').select('*')
    if comercial:
        query = query.eq('comercial', comercial)
    if periodo:
        query = query.eq('periodo', periodo)
    result = query.order('fecha_calculo', desc=True).execute()
    return result.data or []


# ============================================
# TEMPORADAS
# ============================================

def guardar_temporada(codigo: str, nombre: str, fecha_inicio: str, fecha_fin: str, multiplicador: float = 1.0):
    """Guarda o actualiza una temporada."""
    client = get_admin_client()
    client.table('temporadas').upsert({
        'codigo': codigo,
        'nombre': nombre,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'multiplicador': multiplicador
    }).execute()
    limpiar_cache_tarifas()

@st.cache_data(ttl=600)
def obtener_temporadas():
    """Obtiene todas las temporadas activas (cacheado)."""
    client = get_admin_client()
    result = client.table('temporadas').select('*').eq('activo', True).order('fecha_inicio').execute()
    return result.data or []

def eliminar_temporada(codigo: str):
    """Elimina una temporada."""
    client = get_admin_client()
    client.table('temporadas').delete().eq('codigo', codigo).execute()
    limpiar_cache_tarifas()

def obtener_temporada_por_fecha(fecha: str):
    """Obtiene la temporada activa para una fecha (formato MM-DD)."""
    temporadas = obtener_temporadas()
    for t in temporadas:
        inicio = t['fecha_inicio']
        fin = t['fecha_fin']
        if inicio <= fin:
            if inicio <= fecha <= fin:
                return t
        else:  # Temporada que cruza año (ej: 12-01 a 01-15)
            if fecha >= inicio or fecha <= fin:
                return t
    return None


# ============================================
# TIPOS DE BUS
# ============================================

def guardar_tipo_bus(codigo: str, nombre: str, capacidad: int, precio_base_hora: float, precio_base_km: float,
                     coste_km: float = 0.85, coste_hora: float = 30.0):
    """Guarda o actualiza un tipo de bus."""
    client = get_admin_client()
    client.table('tipos_bus').upsert({
        'codigo': codigo,
        'nombre': nombre,
        'capacidad': capacidad,
        'precio_base_hora': precio_base_hora,
        'precio_base_km': precio_base_km,
        'coste_km': coste_km,
        'coste_hora': coste_hora
    }).execute()
    limpiar_cache_tarifas()

@st.cache_data(ttl=600)
def obtener_tipos_bus():
    """Obtiene todos los tipos de bus activos (cacheado)."""
    client = get_admin_client()
    result = client.table('tipos_bus').select('*').eq('activo', True).order('capacidad').execute()
    return result.data or []

def eliminar_tipo_bus(codigo: str):
    """Elimina un tipo de bus."""
    client = get_admin_client()
    client.table('tipos_bus').delete().eq('codigo', codigo).execute()
    limpiar_cache_tarifas()


# ============================================
# TIPOS DE CLIENTE
# ============================================

def guardar_tipo_cliente(codigo: str, nombre: str, multiplicador: float = 1.0):
    """Guarda o actualiza un tipo de cliente."""
    client = get_admin_client()
    client.table('tipos_cliente').upsert({
        'codigo': codigo,
        'nombre': nombre,
        'multiplicador': multiplicador
    }).execute()
    limpiar_cache_tarifas()

@st.cache_data(ttl=600)
def obtener_tipos_cliente():
    """Obtiene todos los tipos de cliente activos (cacheado)."""
    client = get_admin_client()
    result = client.table('tipos_cliente').select('*').eq('activo', True).order('nombre').execute()
    return result.data or []

def eliminar_tipo_cliente(codigo: str):
    """Elimina un tipo de cliente."""
    client = get_admin_client()
    client.table('tipos_cliente').delete().eq('codigo', codigo).execute()
    limpiar_cache_tarifas()


# ============================================
# TARIFAS POR SERVICIO
# ============================================

def guardar_tarifa_servicio(tipo_servicio: str, tipo_bus: str, precio_hora: float = None,
                            precio_km: float = None, precio_minimo: float = None, notas: str = ""):
    """Guarda o actualiza una tarifa de servicio."""
    client = get_admin_client()
    # Buscar si existe
    existe = client.table('tarifas_servicio').select('id').eq('tipo_servicio', tipo_servicio).eq('tipo_bus', tipo_bus).execute()

    datos = {
        'tipo_servicio': tipo_servicio,
        'tipo_bus': tipo_bus,
        'precio_hora': precio_hora,
        'precio_km': precio_km,
        'precio_minimo': precio_minimo,
        'notas': notas
    }

    if existe.data:
        client.table('tarifas_servicio').update(datos).eq('id', existe.data[0]['id']).execute()
    else:
        client.table('tarifas_servicio').insert(datos).execute()
    limpiar_cache_tarifas()

@st.cache_data(ttl=600)
def obtener_tarifas_servicio():
    """Obtiene todas las tarifas por servicio (cacheado)."""
    client = get_admin_client()
    result = client.table('tarifas_servicio').select('*').eq('activo', True).order('tipo_servicio').execute()
    return result.data or []

def obtener_tarifa_servicio(tipo_servicio: str, tipo_bus: str):
    """Obtiene la tarifa para un tipo de servicio y bus específico."""
    tarifas = obtener_tarifas_servicio()
    return next((t for t in tarifas if t['tipo_servicio'] == tipo_servicio and t['tipo_bus'] == tipo_bus), None)

def eliminar_tarifa_servicio(tipo_servicio: str, tipo_bus: str):
    """Elimina una tarifa de servicio."""
    client = get_admin_client()
    client.table('tarifas_servicio').delete().eq('tipo_servicio', tipo_servicio).eq('tipo_bus', tipo_bus).execute()
    limpiar_cache_tarifas()


# ============================================
# TARIFAS PERSONALIZADAS POR CLIENTE
# ============================================

def guardar_tarifa_cliente(cliente: str, tipo_bus: str = None, tipo_servicio: str = None,
                           precio_hora: float = None, precio_km: float = None, notas: str = ""):
    """Guarda o actualiza una tarifa personalizada para un cliente."""
    client = get_admin_client()
    tipo_bus = tipo_bus or '*'
    tipo_servicio = tipo_servicio or '*'

    # Buscar si existe
    existe = client.table('tarifas_cliente').select('id').eq('cliente', cliente).eq('tipo_bus', tipo_bus).eq('tipo_servicio', tipo_servicio).execute()

    datos = {
        'cliente': cliente,
        'tipo_bus': tipo_bus,
        'tipo_servicio': tipo_servicio,
        'precio_hora': precio_hora,
        'precio_km': precio_km,
        'notas': notas,
        'fecha_actualizacion': datetime.now().isoformat()
    }

    if existe.data:
        client.table('tarifas_cliente').update(datos).eq('id', existe.data[0]['id']).execute()
    else:
        client.table('tarifas_cliente').insert(datos).execute()

def obtener_tarifas_cliente(cliente: str = None):
    """Obtiene las tarifas personalizadas de un cliente o todas."""
    client = get_admin_client()
    query = client.table('tarifas_cliente').select('*').eq('activo', True)
    if cliente:
        query = query.eq('cliente', cliente)
    result = query.order('cliente').execute()
    return result.data or []

def obtener_tarifa_cliente_especifica(cliente: str, tipo_bus: str, tipo_servicio: str):
    """Obtiene la tarifa específica de un cliente."""
    client = get_admin_client()
    # Buscar tarifa exacta
    result = client.table('tarifas_cliente').select('*').eq('cliente', cliente).eq('tipo_bus', tipo_bus).eq('tipo_servicio', tipo_servicio).eq('activo', True).execute()
    if result.data:
        return result.data[0]

    # Buscar con comodín en tipo_servicio
    result = client.table('tarifas_cliente').select('*').eq('cliente', cliente).eq('tipo_bus', tipo_bus).eq('tipo_servicio', '*').eq('activo', True).execute()
    if result.data:
        return result.data[0]

    # Buscar con comodín en tipo_bus
    result = client.table('tarifas_cliente').select('*').eq('cliente', cliente).eq('tipo_bus', '*').eq('tipo_servicio', tipo_servicio).eq('activo', True).execute()
    if result.data:
        return result.data[0]

    # Buscar con ambos comodines
    result = client.table('tarifas_cliente').select('*').eq('cliente', cliente).eq('tipo_bus', '*').eq('tipo_servicio', '*').eq('activo', True).execute()
    if result.data:
        return result.data[0]

    return None

def eliminar_tarifa_cliente(cliente: str, tipo_bus: str, tipo_servicio: str):
    """Elimina una tarifa de cliente."""
    client = get_admin_client()
    client.table('tarifas_cliente').delete().eq('cliente', cliente).eq('tipo_bus', tipo_bus).eq('tipo_servicio', tipo_servicio).execute()


# ============================================
# CÁLCULO DE TARIFAS
# ============================================

def calcular_tarifa(tipo_servicio: str, tipo_bus: str, horas: float, km: float,
                    cliente: str = None, fecha: str = None):
    """Calcula la tarifa para un servicio."""
    origen_tarifa = 'base'

    # Buscar tarifa de cliente primero
    tarifa = None
    if cliente:
        tarifa = obtener_tarifa_cliente_especifica(cliente, tipo_bus, tipo_servicio)
        if tarifa:
            origen_tarifa = 'cliente_personalizado'

    # Si no hay tarifa de cliente, usar tarifa estándar por servicio
    if not tarifa and tipo_servicio:
        tarifa = obtener_tarifa_servicio(tipo_servicio, tipo_bus)
        if tarifa:
            origen_tarifa = 'tarifa_servicio'

    # Si no hay tarifa específica, usar tarifa base del tipo de bus
    if not tarifa:
        tipos_bus = obtener_tipos_bus()
        bus_info = next((b for b in tipos_bus if b['codigo'] == tipo_bus), None)
        if bus_info:
            tarifa = {
                'precio_hora': bus_info.get('precio_base_hora', 30),
                'precio_km': bus_info.get('precio_base_km', 0.85),
                'precio_minimo': 0
            }
            origen_tarifa = 'tipo_bus'

    if not tarifa:
        return None

    precio_hora = tarifa.get('precio_hora') or 0
    precio_km = tarifa.get('precio_km') or 0
    precio_minimo = tarifa.get('precio_minimo') or 0

    total = (precio_hora * horas) + (precio_km * km)

    # Aplicar mínimo
    if precio_minimo > 0:
        total = max(total, precio_minimo)

    # Aplicar temporada
    if fecha:
        temporada = obtener_temporada_por_fecha(fecha)
        if temporada and temporada.get('multiplicador'):
            total *= temporada['multiplicador']

    return {
        'total': round(total, 2),
        'precio_hora': precio_hora,
        'precio_km': precio_km,
        'precio_minimo': precio_minimo,
        'origen': origen_tarifa,
        'es_tarifa_cliente': origen_tarifa == 'cliente_personalizado'
    }


# ============================================
# FUNCIONES DE COMPATIBILIDAD (sin uso)
# ============================================

def init_db():
    """Función de compatibilidad - no hace nada con Supabase."""
    pass

def init_incentivos_db():
    """Función de compatibilidad - no hace nada con Supabase."""
    pass

def contar_notas_por_cliente():
    """Cuenta notas por cliente."""
    client = get_admin_client()
    result = client.table('notas').select('cliente').execute()
    conteo = {}
    for nota in (result.data or []):
        cliente = nota['cliente']
        conteo[cliente] = conteo.get(cliente, 0) + 1
    return conteo


# ============================================
# LUGARES FRECUENTES (Calculadora)
# ============================================

def guardar_lugar_frecuente(nombre: str, direccion: str, lat: float, lng: float, tipo: str = "general"):
    """Guarda un lugar frecuente para la calculadora."""
    client = get_admin_client()
    # Verificar si ya existe
    existe = client.table('lugares_frecuentes').select('id').eq('nombre', nombre).execute()
    if existe.data:
        # Actualizar
        client.table('lugares_frecuentes').update({
            'direccion': direccion,
            'lat': lat,
            'lng': lng,
            'tipo': tipo
        }).eq('nombre', nombre).execute()
    else:
        # Insertar
        client.table('lugares_frecuentes').insert({
            'nombre': nombre,
            'direccion': direccion,
            'lat': lat,
            'lng': lng,
            'tipo': tipo
        }).execute()

def obtener_lugares_frecuentes(limite: int = None):
    """Obtiene los lugares frecuentes."""
    client = get_admin_client()
    try:
        query = client.table('lugares_frecuentes').select('*').order('nombre')
        if limite:
            query = query.limit(limite)
        result = query.execute()
        return result.data or []
    except:
        return []

def buscar_lugares_frecuentes(termino: str):
    """Busca lugares frecuentes por nombre."""
    client = get_admin_client()
    try:
        result = client.table('lugares_frecuentes').select('*').ilike('nombre', f'%{termino}%').execute()
        return result.data or []
    except:
        return []


# ============================================
# CONFIGURACIÓN CALCULADORA
# ============================================

def obtener_config_calc(clave: str = None, default: str = None):
    """Obtiene la configuración de la calculadora. Si se pasa clave, retorna ese valor."""
    client = get_admin_client()
    try:
        if clave:
            result = client.table('config_calculadora').select('valor').eq('clave', clave).execute()
            if result.data:
                return result.data[0]['valor']
            return default
        else:
            result = client.table('config_calculadora').select('*').execute()
            if result.data:
                config = {}
                for item in result.data:
                    config[item['clave']] = item['valor']
                return config
            return {}
    except:
        return default if clave else {}

def guardar_config_calc(clave: str, valor: str):
    """Guarda un valor de configuración de la calculadora."""
    client = get_admin_client()
    try:
        # Verificar si existe
        existe = client.table('config_calculadora').select('id').eq('clave', clave).execute()
        if existe.data:
            client.table('config_calculadora').update({'valor': valor}).eq('clave', clave).execute()
        else:
            client.table('config_calculadora').insert({'clave': clave, 'valor': valor}).execute()
    except:
        pass


# ============================================
# CLIENTES DESACTIVADOS
# ============================================

import json

def limpiar_cache_clientes_desactivados():
    """Limpia caché de clientes desactivados."""
    if 'clientes_desactivados_cache' in st.session_state:
        del st.session_state['clientes_desactivados_cache']

def obtener_clientes_desactivados(force_reload: bool = False):
    """Obtiene la lista de clientes desactivados (usa config_general)."""
    if not force_reload and 'clientes_desactivados_cache' in st.session_state:
        return st.session_state['clientes_desactivados_cache'].copy()

    client = get_admin_client()
    try:
        result = client.table('config_general').select('valor').eq('clave', 'clientes_desactivados').execute()
        if result.data and result.data[0]['valor']:
            datos = json.loads(result.data[0]['valor'])
            st.session_state['clientes_desactivados_cache'] = datos
            return datos.copy()
    except Exception as e:
        print(f"Error obteniendo clientes desactivados: {e}")
    return {}

def _guardar_clientes_desactivados(datos: dict):
    """Guarda la lista de clientes desactivados usando upsert."""
    client = get_admin_client()
    valor_json = json.dumps(datos)
    try:
        # Usar upsert con on_conflict
        client.table('config_general').upsert({
            'clave': 'clientes_desactivados',
            'valor': valor_json
        }, on_conflict='clave').execute()
        # Actualizar cache
        st.session_state['clientes_desactivados_cache'] = datos.copy()
        return True
    except Exception as e:
        print(f"Error guardando clientes desactivados: {e}")
        return False

def desactivar_cliente(cliente: str, motivo: str = ""):
    """Desactiva un cliente para que no aparezca en la app."""
    try:
        # Forzar recarga desde DB para evitar datos obsoletos
        desactivados = obtener_clientes_desactivados(force_reload=True)
        desactivados[cliente] = {
            'motivo': motivo,
            'fecha': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
        return _guardar_clientes_desactivados(desactivados)
    except Exception as e:
        print(f"Error desactivando cliente: {e}")
        return False

def reactivar_cliente(cliente: str):
    """Reactiva un cliente previamente desactivado."""
    try:
        desactivados = obtener_clientes_desactivados(force_reload=True)
        if cliente in desactivados:
            del desactivados[cliente]
            return _guardar_clientes_desactivados(desactivados)
        return True
    except Exception as e:
        print(f"Error reactivando cliente: {e}")
        return False

def esta_cliente_desactivado(cliente: str) -> bool:
    """Verifica si un cliente está desactivado."""
    desactivados = obtener_clientes_desactivados()
    return cliente in desactivados
