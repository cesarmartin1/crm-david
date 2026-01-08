import sqlite3
import os
from datetime import datetime
from pathlib import Path

# En Streamlit Cloud usar /tmp/ (único directorio escribible)
if os.environ.get('STREAMLIT_SERVER_HEADLESS'):
    DB_PATH = Path("/tmp/crm_notas.db")
else:
    DB_PATH = Path(__file__).parent / "crm_notas.db"

def get_connection():
    """Obtiene conexión a la base de datos SQLite."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa la base de datos creando las tablas necesarias."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cod_presupuesto TEXT,
            cliente TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            usuario TEXT,
            contenido TEXT,
            tipo TEXT
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_notas_cliente ON notas(cliente)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_notas_presupuesto ON notas(cod_presupuesto)
    ''')

    # Tabla para tipos de servicio
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tipos_servicio (
            codigo TEXT PRIMARY KEY,
            descripcion TEXT,
            categoria TEXT
        )
    ''')

    # Tabla para lugares frecuentes (direcciones guardadas)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lugares_frecuentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            direccion TEXT NOT NULL,
            direccion_completa TEXT,
            latitud REAL,
            longitud REAL,
            categoria TEXT DEFAULT 'general',
            uso_count INTEGER DEFAULT 0,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_lugares_nombre ON lugares_frecuentes(nombre)
    ''')

    # Tabla para configuracion de la calculadora (posicionamiento, base, etc.)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config_calculadora (
            clave TEXT PRIMARY KEY,
            valor TEXT
        )
    ''')

    # Tabla para tracking de uso de Google Maps API
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE NOT NULL,
            api_name TEXT NOT NULL,
            requests INTEGER DEFAULT 0,
            cost REAL DEFAULT 0.0,
            UNIQUE(fecha, api_name)
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_api_usage_fecha ON api_usage(fecha)
    ''')

    conn.commit()
    conn.close()


# ============================================
# FUNCIONES PARA LUGARES FRECUENTES
# ============================================

def guardar_lugar_frecuente(nombre: str, direccion: str, direccion_completa: str = None,
                            latitud: float = None, longitud: float = None, categoria: str = 'general'):
    """Guarda un lugar frecuente en la base de datos."""
    conn = get_connection()
    cursor = conn.cursor()

    # Verificar si ya existe
    cursor.execute('SELECT id FROM lugares_frecuentes WHERE direccion = ?', (direccion,))
    existe = cursor.fetchone()

    if existe:
        # Actualizar contador de uso
        cursor.execute('''
            UPDATE lugares_frecuentes
            SET uso_count = uso_count + 1, nombre = ?
            WHERE direccion = ?
        ''', (nombre, direccion))
    else:
        cursor.execute('''
            INSERT INTO lugares_frecuentes (nombre, direccion, direccion_completa, latitud, longitud, categoria)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (nombre, direccion, direccion_completa, latitud, longitud, categoria))

    conn.commit()
    conn.close()


def obtener_lugares_frecuentes(categoria: str = None, limite: int = 50):
    """Obtiene lugares frecuentes ordenados por uso."""
    conn = get_connection()
    cursor = conn.cursor()

    if categoria:
        cursor.execute('''
            SELECT * FROM lugares_frecuentes
            WHERE categoria = ?
            ORDER BY uso_count DESC, nombre ASC
            LIMIT ?
        ''', (categoria, limite))
    else:
        cursor.execute('''
            SELECT * FROM lugares_frecuentes
            ORDER BY uso_count DESC, nombre ASC
            LIMIT ?
        ''', (limite,))

    lugares = cursor.fetchall()
    conn.close()
    return [dict(l) for l in lugares]


def buscar_lugares_frecuentes(texto: str, limite: int = 10):
    """Busca lugares frecuentes por nombre o direccion."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM lugares_frecuentes
        WHERE nombre LIKE ? OR direccion LIKE ? OR direccion_completa LIKE ?
        ORDER BY uso_count DESC
        LIMIT ?
    ''', (f'%{texto}%', f'%{texto}%', f'%{texto}%', limite))

    lugares = cursor.fetchall()
    conn.close()
    return [dict(l) for l in lugares]


def eliminar_lugar_frecuente(id_lugar: int):
    """Elimina un lugar frecuente."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM lugares_frecuentes WHERE id = ?', (id_lugar,))
    conn.commit()
    conn.close()


def incrementar_uso_lugar(id_lugar: int):
    """Incrementa el contador de uso de un lugar."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE lugares_frecuentes SET uso_count = uso_count + 1 WHERE id = ?', (id_lugar,))
    conn.commit()
    conn.close()


# ============================================
# FUNCIONES PARA CONFIGURACION CALCULADORA
# ============================================

def guardar_config_calc(clave: str, valor: str):
    """Guarda una configuracion de la calculadora."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO config_calculadora (clave, valor) VALUES (?, ?)
    ''', (clave, valor))
    conn.commit()
    conn.close()


def obtener_config_calc(clave: str, default: str = None):
    """Obtiene una configuracion de la calculadora."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT valor FROM config_calculadora WHERE clave = ?', (clave,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado['valor'] if resultado else default


# ============================================
# FUNCIONES PARA TRACKING DE API USAGE
# ============================================

def registrar_uso_api(api_name: str = 'google_places', num_requests: int = 1):
    """
    Registra el uso de una API. Acumula requests por día.
    Coste: $2.83 por 1000 requests después de los primeros 10,000 gratis.
    """
    from datetime import date
    conn = get_connection()
    cursor = conn.cursor()

    hoy = date.today().isoformat()

    # Insertar o actualizar el registro del día
    cursor.execute('''
        INSERT INTO api_usage (fecha, api_name, requests, cost)
        VALUES (?, ?, ?, 0.0)
        ON CONFLICT(fecha, api_name) DO UPDATE SET
            requests = requests + ?
    ''', (hoy, api_name, num_requests, num_requests))

    # Recalcular el coste del mes actual
    primer_dia_mes = date.today().replace(day=1).isoformat()
    cursor.execute('''
        SELECT SUM(requests) as total FROM api_usage
        WHERE api_name = ? AND fecha >= ?
    ''', (api_name, primer_dia_mes))

    total_mes = cursor.fetchone()['total'] or 0

    # Calcular coste (primeros 10,000 gratis, después $2.83 por 1000)
    if total_mes <= 10000:
        coste_total = 0.0
    else:
        requests_de_pago = total_mes - 10000
        coste_total = (requests_de_pago / 1000) * 2.83

    # Actualizar coste del día (proporcionalmente)
    cursor.execute('''
        UPDATE api_usage SET cost = ? WHERE fecha = ? AND api_name = ?
    ''', (coste_total, hoy, api_name))

    conn.commit()
    conn.close()

    return {'requests_hoy': num_requests, 'total_mes': total_mes, 'coste_mes': coste_total}


def obtener_uso_api_mes(api_name: str = 'google_places'):
    """Obtiene el uso acumulado del mes actual."""
    from datetime import date
    conn = get_connection()
    cursor = conn.cursor()

    primer_dia_mes = date.today().replace(day=1).isoformat()

    cursor.execute('''
        SELECT
            SUM(requests) as total_requests,
            MAX(cost) as coste_acumulado
        FROM api_usage
        WHERE api_name = ? AND fecha >= ?
    ''', (api_name, primer_dia_mes))

    resultado = cursor.fetchone()
    conn.close()

    total = resultado['total_requests'] or 0

    # Recalcular coste
    if total <= 10000:
        coste = 0.0
    else:
        coste = ((total - 10000) / 1000) * 2.83

    return {
        'total_requests': total,
        'gratis_restantes': max(0, 10000 - total),
        'coste_usd': round(coste, 2),
        'coste_eur': round(coste * 0.92, 2)  # Aproximado USD a EUR
    }


def obtener_historial_api(api_name: str = 'google_places', dias: int = 30):
    """Obtiene el historial de uso de los últimos N días."""
    from datetime import date, timedelta
    conn = get_connection()
    cursor = conn.cursor()

    fecha_inicio = (date.today() - timedelta(days=dias)).isoformat()

    cursor.execute('''
        SELECT fecha, requests, cost
        FROM api_usage
        WHERE api_name = ? AND fecha >= ?
        ORDER BY fecha DESC
    ''', (api_name, fecha_inicio))

    historial = cursor.fetchall()
    conn.close()

    return [dict(h) for h in historial]


def agregar_nota(cod_presupuesto: str, cliente: str, contenido: str, tipo: str, usuario: str = "Sistema"):
    """Agrega una nueva nota de seguimiento."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO notas (cod_presupuesto, cliente, contenido, tipo, usuario, fecha)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (cod_presupuesto, cliente, contenido, tipo, usuario, datetime.now()))

    conn.commit()
    conn.close()

def obtener_notas_cliente(cliente: str):
    """Obtiene todas las notas de un cliente."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM notas
        WHERE cliente = ?
        ORDER BY fecha DESC
    ''', (cliente,))

    notas = cursor.fetchall()
    conn.close()
    return [dict(n) for n in notas]

def obtener_notas_presupuesto(cod_presupuesto: str):
    """Obtiene todas las notas de un presupuesto específico."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM notas
        WHERE cod_presupuesto = ?
        ORDER BY fecha DESC
    ''', (cod_presupuesto,))

    notas = cursor.fetchall()
    conn.close()
    return [dict(n) for n in notas]

def obtener_todas_notas(limite: int = 100):
    """Obtiene las últimas notas del sistema."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM notas
        ORDER BY fecha DESC
        LIMIT ?
    ''', (limite,))

    notas = cursor.fetchall()
    conn.close()
    return [dict(n) for n in notas]

def buscar_notas(termino: str):
    """Busca notas que contengan un término específico."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM notas
        WHERE contenido LIKE ? OR cliente LIKE ?
        ORDER BY fecha DESC
    ''', (f'%{termino}%', f'%{termino}%'))

    notas = cursor.fetchall()
    conn.close()
    return [dict(n) for n in notas]

def eliminar_nota(nota_id: int):
    """Elimina una nota por su ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM notas WHERE id = ?', (nota_id,))

    conn.commit()
    conn.close()

def contar_notas_por_cliente():
    """Cuenta el número de notas por cliente."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT cliente, COUNT(*) as total
        FROM notas
        GROUP BY cliente
        ORDER BY total DESC
    ''')

    resultado = cursor.fetchall()
    conn.close()
    return [dict(r) for r in resultado]


# ============================================
# FUNCIONES PARA TIPOS DE SERVICIO
# ============================================

def guardar_tipo_servicio(codigo: str, descripcion: str, categoria: str = ""):
    """Guarda o actualiza un tipo de servicio."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO tipos_servicio (codigo, descripcion, categoria)
        VALUES (?, ?, ?)
    ''', (codigo, descripcion, categoria))

    conn.commit()
    conn.close()

def obtener_tipos_servicio_db():
    """Obtiene todos los tipos de servicio definidos."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM tipos_servicio ORDER BY codigo')

    tipos = cursor.fetchall()
    conn.close()
    return {t['codigo']: {'descripcion': t['descripcion'], 'categoria': t['categoria']} for t in tipos}

def obtener_descripcion_tipo(codigo: str):
    """Obtiene la descripción de un tipo de servicio."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT descripcion FROM tipos_servicio WHERE codigo = ?', (codigo,))

    resultado = cursor.fetchone()
    conn.close()
    return resultado['descripcion'] if resultado else None

def eliminar_tipo_servicio(codigo: str):
    """Elimina un tipo de servicio."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM tipos_servicio WHERE codigo = ?', (codigo,))

    conn.commit()
    conn.close()

def guardar_tipos_servicio_masivo(tipos: dict):
    """Guarda múltiples tipos de servicio de una vez."""
    conn = get_connection()
    cursor = conn.cursor()

    for codigo, datos in tipos.items():
        descripcion = datos.get('descripcion', '')
        categoria = datos.get('categoria', '')
        cursor.execute('''
            INSERT OR REPLACE INTO tipos_servicio (codigo, descripcion, categoria)
            VALUES (?, ?, ?)
        ''', (codigo, descripcion, categoria))

    conn.commit()
    conn.close()


# ============================================
# FUNCIONES PARA SISTEMA DE INCENTIVOS
# ============================================

def init_incentivos_db():
    """Inicializa las tablas para el sistema de incentivos."""
    conn = get_connection()
    cursor = conn.cursor()

    # Configuración general de incentivos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS incentivos_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clave TEXT UNIQUE,
            valor TEXT,
            descripcion TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tramos de comisión por facturación
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comisiones_tramos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            desde REAL,
            hasta REAL,
            porcentaje REAL,
            activo INTEGER DEFAULT 1
        )
    ''')

    # Bonus por objetivos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bonus_objetivos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            tipo TEXT,
            condicion TEXT,
            valor_objetivo REAL,
            importe_bonus REAL,
            activo INTEGER DEFAULT 1
        )
    ''')

    # Sistema de puntos por acción
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS puntos_acciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            accion TEXT,
            tipo_servicio TEXT,
            puntos INTEGER,
            descripcion TEXT,
            activo INTEGER DEFAULT 1
        )
    ''')

    # Valor del punto y premios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS puntos_premios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            puntos_requeridos INTEGER,
            descripcion TEXT,
            activo INTEGER DEFAULT 1
        )
    ''')

    # Histórico de incentivos calculados
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS incentivos_historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comercial TEXT,
            periodo TEXT,
            comision REAL,
            bonus REAL,
            puntos INTEGER,
            total REAL,
            fecha_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()


def guardar_config_incentivo(clave: str, valor: str, descripcion: str = ""):
    """Guarda o actualiza una configuración de incentivo."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO incentivos_config (clave, valor, descripcion, updated_at)
        VALUES (?, ?, ?, ?)
    ''', (clave, valor, descripcion, datetime.now()))

    conn.commit()
    conn.close()


def obtener_config_incentivo(clave: str, default: str = None):
    """Obtiene el valor de una configuración de incentivo."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT valor FROM incentivos_config WHERE clave = ?', (clave,))
    resultado = cursor.fetchone()
    conn.close()

    return resultado['valor'] if resultado else default


def obtener_todas_config_incentivos():
    """Obtiene todas las configuraciones de incentivos."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM incentivos_config')
    configs = cursor.fetchall()
    conn.close()

    return {c['clave']: c['valor'] for c in configs}


# --- COMISIONES ---
def guardar_tramo_comision(desde: float, hasta: float, porcentaje: float):
    """Guarda un tramo de comisión."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO comisiones_tramos (desde, hasta, porcentaje)
        VALUES (?, ?, ?)
    ''', (desde, hasta, porcentaje))

    conn.commit()
    conn.close()


def obtener_tramos_comision():
    """Obtiene todos los tramos de comisión activos."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM comisiones_tramos WHERE activo = 1 ORDER BY desde')
    tramos = cursor.fetchall()
    conn.close()

    return [dict(t) for t in tramos]


def eliminar_tramo_comision(tramo_id: int):
    """Elimina un tramo de comisión."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM comisiones_tramos WHERE id = ?', (tramo_id,))

    conn.commit()
    conn.close()


def limpiar_tramos_comision():
    """Elimina todos los tramos de comisión."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM comisiones_tramos')

    conn.commit()
    conn.close()


# --- BONUS ---
def guardar_bonus(nombre: str, tipo: str, condicion: str, valor_objetivo: float, importe_bonus: float):
    """Guarda un bonus por objetivo."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO bonus_objetivos (nombre, tipo, condicion, valor_objetivo, importe_bonus)
        VALUES (?, ?, ?, ?, ?)
    ''', (nombre, tipo, condicion, valor_objetivo, importe_bonus))

    conn.commit()
    conn.close()


def obtener_bonus_objetivos():
    """Obtiene todos los bonus activos."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM bonus_objetivos WHERE activo = 1')
    bonus = cursor.fetchall()
    conn.close()

    return [dict(b) for b in bonus]


def eliminar_bonus(bonus_id: int):
    """Elimina un bonus."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM bonus_objetivos WHERE id = ?', (bonus_id,))

    conn.commit()
    conn.close()


def limpiar_bonus():
    """Elimina todos los bonus."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM bonus_objetivos')

    conn.commit()
    conn.close()


# --- PUNTOS ---
def guardar_puntos_accion(accion: str, tipo_servicio: str, puntos: int, descripcion: str = ""):
    """Guarda puntos por acción."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO puntos_acciones (accion, tipo_servicio, puntos, descripcion)
        VALUES (?, ?, ?, ?)
    ''', (accion, tipo_servicio, puntos, descripcion))

    conn.commit()
    conn.close()


def obtener_puntos_acciones():
    """Obtiene todas las acciones con puntos."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM puntos_acciones WHERE activo = 1')
    acciones = cursor.fetchall()
    conn.close()

    return [dict(a) for a in acciones]


def eliminar_puntos_accion(accion_id: int):
    """Elimina una acción de puntos."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM puntos_acciones WHERE id = ?', (accion_id,))

    conn.commit()
    conn.close()


def limpiar_puntos_acciones():
    """Elimina todas las acciones de puntos."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM puntos_acciones')

    conn.commit()
    conn.close()


# --- PREMIOS ---
def guardar_premio(nombre: str, puntos_requeridos: int, descripcion: str = ""):
    """Guarda un premio canjeable por puntos."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO puntos_premios (nombre, puntos_requeridos, descripcion)
        VALUES (?, ?, ?)
    ''', (nombre, puntos_requeridos, descripcion))

    conn.commit()
    conn.close()


def obtener_premios():
    """Obtiene todos los premios activos."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM puntos_premios WHERE activo = 1 ORDER BY puntos_requeridos')
    premios = cursor.fetchall()
    conn.close()

    return [dict(p) for p in premios]


def limpiar_premios():
    """Elimina todos los premios."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM puntos_premios')

    conn.commit()
    conn.close()


# --- HISTÓRICO ---
def guardar_incentivo_historico(comercial: str, periodo: str, comision: float, bonus: float, puntos: int, total: float):
    """Guarda el cálculo de incentivos en el histórico."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO incentivos_historico (comercial, periodo, comision, bonus, puntos, total)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (comercial, periodo, comision, bonus, puntos, total))

    conn.commit()
    conn.close()


def obtener_historico_incentivos(comercial: str = None, periodo: str = None):
    """Obtiene el histórico de incentivos."""
    conn = get_connection()
    cursor = conn.cursor()

    query = 'SELECT * FROM incentivos_historico WHERE 1=1'
    params = []

    if comercial:
        query += ' AND comercial = ?'
        params.append(comercial)

    if periodo:
        query += ' AND periodo = ?'
        params.append(periodo)

    query += ' ORDER BY fecha_calculo DESC'

    cursor.execute(query, params)
    historico = cursor.fetchall()
    conn.close()

    return [dict(h) for h in historico]


# ============================================
# FUNCIONES PARA PREMIOS ESPECIALES POR PRESUPUESTO
# ============================================

def init_premios_presupuesto_db():
    """Inicializa la tabla para premios especiales por presupuesto."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS premios_presupuesto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cod_presupuesto TEXT UNIQUE,
            descripcion TEXT,
            importe_premio REAL,
            comercial_asignado TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            conseguido INTEGER DEFAULT 0,
            fecha_conseguido TIMESTAMP,
            activo INTEGER DEFAULT 1
        )
    ''')

    conn.commit()
    conn.close()


def guardar_premio_presupuesto(cod_presupuesto: str, descripcion: str, importe_premio: float, comercial_asignado: str = None):
    """Guarda un premio especial para un presupuesto."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO premios_presupuesto (cod_presupuesto, descripcion, importe_premio, comercial_asignado)
        VALUES (?, ?, ?, ?)
    ''', (cod_presupuesto, descripcion, importe_premio, comercial_asignado))

    conn.commit()
    conn.close()


def obtener_premios_presupuesto(solo_activos: bool = True, solo_pendientes: bool = False):
    """Obtiene los premios especiales de presupuestos."""
    conn = get_connection()
    cursor = conn.cursor()

    query = 'SELECT * FROM premios_presupuesto WHERE 1=1'
    if solo_activos:
        query += ' AND activo = 1'
    if solo_pendientes:
        query += ' AND conseguido = 0'
    query += ' ORDER BY fecha_creacion DESC'

    cursor.execute(query)
    premios = cursor.fetchall()
    conn.close()

    return [dict(p) for p in premios]


def marcar_premio_conseguido(cod_presupuesto: str):
    """Marca un premio como conseguido."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE premios_presupuesto
        SET conseguido = 1, fecha_conseguido = ?
        WHERE cod_presupuesto = ?
    ''', (datetime.now(), cod_presupuesto))

    conn.commit()
    conn.close()


def eliminar_premio_presupuesto(cod_presupuesto: str):
    """Elimina un premio de presupuesto."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM premios_presupuesto WHERE cod_presupuesto = ?', (cod_presupuesto,))

    conn.commit()
    conn.close()


def obtener_premio_por_presupuesto(cod_presupuesto: str):
    """Obtiene el premio de un presupuesto específico."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM premios_presupuesto WHERE cod_presupuesto = ? AND activo = 1', (cod_presupuesto,))
    premio = cursor.fetchone()
    conn.close()

    return dict(premio) if premio else None


# ============================================
# FUNCIONES PARA SISTEMA DE TARIFAS
# ============================================

def init_tarifas_db():
    """Inicializa las tablas para el sistema de tarifas."""
    conn = get_connection()
    cursor = conn.cursor()

    # Temporadas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS temporadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE,
            nombre TEXT,
            fecha_inicio TEXT,
            fecha_fin TEXT,
            multiplicador REAL DEFAULT 1.0,
            activo INTEGER DEFAULT 1
        )
    ''')

    # Tipos de bus
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tipos_bus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE,
            nombre TEXT,
            capacidad INTEGER,
            precio_base_hora REAL,
            precio_base_km REAL,
            activo INTEGER DEFAULT 1
        )
    ''')

    # Tipos de cliente (segmentos)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tipos_cliente (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE,
            nombre TEXT,
            multiplicador REAL DEFAULT 1.0,
            descuento_porcentaje REAL DEFAULT 0,
            activo INTEGER DEFAULT 1
        )
    ''')

    # Tarifas por tipo de servicio
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tarifas_servicio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_servicio TEXT,
            tipo_bus TEXT,
            precio_base REAL,
            precio_km REAL,
            precio_hora REAL,
            minimo REAL DEFAULT 0,
            activo INTEGER DEFAULT 1,
            UNIQUE(tipo_servicio, tipo_bus)
        )
    ''')

    # Tarifas personalizadas por cliente individual
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tarifas_cliente (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            tipo_bus TEXT,
            tipo_servicio TEXT,
            precio_hora REAL,
            precio_km REAL,
            descuento_porcentaje REAL DEFAULT 0,
            notas TEXT,
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            activo INTEGER DEFAULT 1,
            UNIQUE(cliente, tipo_bus, tipo_servicio)
        )
    ''')

    # Histórico de tarifas aplicadas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tarifas_historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cod_presupuesto TEXT,
            cliente TEXT,
            tipo_bus TEXT,
            tipo_servicio TEXT,
            temporada TEXT,
            precio_calculado REAL,
            precio_aplicado REAL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabla de peajes de autopistas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS peajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            autopista TEXT,
            nombre TEXT,
            tramo_origen TEXT,
            tramo_destino TEXT,
            tarifa_autobus REAL,
            tarifa_coche REAL DEFAULT 0,
            notas TEXT,
            activo INTEGER DEFAULT 1,
            UNIQUE(autopista, tramo_origen, tramo_destino)
        )
    ''')

    conn.commit()
    conn.close()


# --- TEMPORADAS ---
def guardar_temporada(codigo: str, nombre: str, fecha_inicio: str, fecha_fin: str, multiplicador: float = 1.0):
    """Guarda o actualiza una temporada."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO temporadas (codigo, nombre, fecha_inicio, fecha_fin, multiplicador)
        VALUES (?, ?, ?, ?, ?)
    ''', (codigo, nombre, fecha_inicio, fecha_fin, multiplicador))

    conn.commit()
    conn.close()


def obtener_temporadas():
    """Obtiene todas las temporadas activas."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM temporadas WHERE activo = 1 ORDER BY fecha_inicio')
    temporadas = cursor.fetchall()
    conn.close()

    return [dict(t) for t in temporadas]


def eliminar_temporada(codigo: str):
    """Elimina una temporada."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM temporadas WHERE codigo = ?', (codigo,))

    conn.commit()
    conn.close()


def obtener_temporada_por_fecha(fecha: str):
    """Obtiene la temporada activa para una fecha dada (formato MM-DD)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM temporadas
        WHERE activo = 1
        AND (
            (fecha_inicio <= ? AND fecha_fin >= ?) OR
            (fecha_inicio > fecha_fin AND (fecha_inicio <= ? OR fecha_fin >= ?))
        )
    ''', (fecha, fecha, fecha, fecha))
    temporada = cursor.fetchone()
    conn.close()

    return dict(temporada) if temporada else None


# --- TIPOS DE BUS ---
def guardar_tipo_bus(codigo: str, nombre: str, capacidad: int, precio_base_hora: float, precio_base_km: float,
                     coste_km: float = 0.85, coste_hora: float = 30.0):
    """Guarda o actualiza un tipo de bus con precios y costes."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO tipos_bus (codigo, nombre, capacidad, precio_base_hora, precio_base_km, coste_km, coste_hora)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (codigo, nombre, capacidad, precio_base_hora, precio_base_km, coste_km, coste_hora))

    conn.commit()
    conn.close()


def obtener_tipos_bus():
    """Obtiene todos los tipos de bus activos."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM tipos_bus WHERE activo = 1 ORDER BY capacidad')
    tipos = cursor.fetchall()
    conn.close()

    return [dict(t) for t in tipos]


def eliminar_tipo_bus(codigo: str):
    """Elimina un tipo de bus."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM tipos_bus WHERE codigo = ?', (codigo,))

    conn.commit()
    conn.close()


# --- TIPOS DE CLIENTE ---
def guardar_tipo_cliente(codigo: str, nombre: str, multiplicador: float = 1.0):
    """Guarda o actualiza un tipo de cliente."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO tipos_cliente (codigo, nombre, multiplicador)
        VALUES (?, ?, ?)
    ''', (codigo, nombre, multiplicador))

    conn.commit()
    conn.close()


def obtener_tipos_cliente():
    """Obtiene todos los tipos de cliente activos."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM tipos_cliente WHERE activo = 1 ORDER BY nombre')
    tipos = cursor.fetchall()
    conn.close()

    return [dict(t) for t in tipos]


def eliminar_tipo_cliente(codigo: str):
    """Elimina un tipo de cliente."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM tipos_cliente WHERE codigo = ?', (codigo,))

    conn.commit()
    conn.close()


# --- TARIFAS POR SERVICIO ---
def guardar_tarifa_servicio(tipo_servicio: str, tipo_bus: str, precio_base: float, precio_km: float, precio_hora: float, minimo: float = 0):
    """Guarda o actualiza una tarifa por tipo de servicio y bus."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO tarifas_servicio (tipo_servicio, tipo_bus, precio_base, precio_km, precio_hora, minimo)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (tipo_servicio, tipo_bus, precio_base, precio_km, precio_hora, minimo))

    conn.commit()
    conn.close()


def obtener_tarifas_servicio():
    """Obtiene todas las tarifas por servicio."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM tarifas_servicio WHERE activo = 1 ORDER BY tipo_servicio, tipo_bus')
    tarifas = cursor.fetchall()
    conn.close()

    return [dict(t) for t in tarifas]


def obtener_tarifa_servicio(tipo_servicio: str, tipo_bus: str):
    """Obtiene la tarifa para un tipo de servicio y bus específico."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM tarifas_servicio
        WHERE tipo_servicio = ? AND tipo_bus = ? AND activo = 1
    ''', (tipo_servicio, tipo_bus))
    tarifa = cursor.fetchone()
    conn.close()

    return dict(tarifa) if tarifa else None


def eliminar_tarifa_servicio(tipo_servicio: str, tipo_bus: str):
    """Elimina una tarifa de servicio."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM tarifas_servicio WHERE tipo_servicio = ? AND tipo_bus = ?', (tipo_servicio, tipo_bus))

    conn.commit()
    conn.close()


# --- TARIFAS PERSONALIZADAS POR CLIENTE ---
def guardar_tarifa_cliente(cliente: str, tipo_bus: str = None, tipo_servicio: str = None,
                           precio_hora: float = None, precio_km: float = None,
                           notas: str = ""):
    """Guarda o actualiza una tarifa personalizada para un cliente."""
    conn = get_connection()
    cursor = conn.cursor()

    # Usar comodines si no se especifica
    tipo_bus = tipo_bus or '*'
    tipo_servicio = tipo_servicio or '*'

    cursor.execute('''
        INSERT OR REPLACE INTO tarifas_cliente
        (cliente, tipo_bus, tipo_servicio, precio_hora, precio_km, notas, fecha_actualizacion)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (cliente, tipo_bus, tipo_servicio, precio_hora, precio_km, notas, datetime.now()))

    conn.commit()
    conn.close()


def obtener_tarifas_cliente(cliente: str = None):
    """Obtiene las tarifas personalizadas de un cliente o todas."""
    conn = get_connection()
    cursor = conn.cursor()

    if cliente:
        cursor.execute('SELECT * FROM tarifas_cliente WHERE cliente = ? AND activo = 1 ORDER BY tipo_bus, tipo_servicio', (cliente,))
    else:
        cursor.execute('SELECT * FROM tarifas_cliente WHERE activo = 1 ORDER BY cliente, tipo_bus, tipo_servicio')

    tarifas = cursor.fetchall()
    conn.close()

    return [dict(t) for t in tarifas]


def obtener_tarifa_cliente_especifica(cliente: str, tipo_bus: str, tipo_servicio: str):
    """Obtiene la tarifa específica de un cliente para un tipo de bus y servicio."""
    conn = get_connection()
    cursor = conn.cursor()

    # Buscar primero tarifa exacta, luego con comodines
    cursor.execute('''
        SELECT * FROM tarifas_cliente
        WHERE cliente = ? AND activo = 1
        AND (tipo_bus = ? OR tipo_bus = '*')
        AND (tipo_servicio = ? OR tipo_servicio = '*')
        ORDER BY
            CASE WHEN tipo_bus = '*' THEN 1 ELSE 0 END,
            CASE WHEN tipo_servicio = '*' THEN 1 ELSE 0 END
        LIMIT 1
    ''', (cliente, tipo_bus, tipo_servicio))

    tarifa = cursor.fetchone()
    conn.close()

    return dict(tarifa) if tarifa else None


def eliminar_tarifa_cliente(cliente: str, tipo_bus: str = None, tipo_servicio: str = None):
    """Elimina una tarifa personalizada de cliente."""
    conn = get_connection()
    cursor = conn.cursor()

    if tipo_bus and tipo_servicio:
        cursor.execute('DELETE FROM tarifas_cliente WHERE cliente = ? AND tipo_bus = ? AND tipo_servicio = ?',
                      (cliente, tipo_bus, tipo_servicio))
    else:
        cursor.execute('DELETE FROM tarifas_cliente WHERE cliente = ?', (cliente,))

    conn.commit()
    conn.close()


# --- CÁLCULO DE TARIFA ---
def calcular_tarifa(cliente: str, tipo_bus: str, tipo_servicio: str, fecha: str,
                    kms: float = 0, horas: float = 0, tipo_cliente_codigo: str = None):
    """
    Calcula la tarifa aplicable considerando:
    1. Tarifa personalizada del cliente (si existe)
    2. Tarifa por tipo de servicio + bus
    3. Multiplicador de temporada
    4. Multiplicador de tipo de cliente
    """
    resultado = {
        'precio_base': 0,
        'precio_km': 0,
        'precio_hora': 0,
        'subtotal': 0,
        'multiplicador_temporada': 1.0,
        'multiplicador_cliente': 1.0,
        'total': 0,
        'origen': 'base'
    }

    # 1. Buscar tarifa personalizada del cliente
    tarifa_cliente = obtener_tarifa_cliente_especifica(cliente, tipo_bus, tipo_servicio)

    if tarifa_cliente:
        resultado['precio_hora'] = tarifa_cliente.get('precio_hora') or 0
        resultado['precio_km'] = tarifa_cliente.get('precio_km') or 0
        resultado['origen'] = 'cliente_personalizado'
    else:
        # 2. Buscar tarifa por servicio + bus
        tarifa_servicio = obtener_tarifa_servicio(tipo_servicio, tipo_bus)
        if tarifa_servicio:
            resultado['precio_base'] = tarifa_servicio.get('precio_base') or 0
            resultado['precio_km'] = tarifa_servicio.get('precio_km') or 0
            resultado['precio_hora'] = tarifa_servicio.get('precio_hora') or 0
            resultado['origen'] = 'tarifa_servicio'
        else:
            # 3. Buscar precio base del tipo de bus
            tipos_bus = obtener_tipos_bus()
            for tb in tipos_bus:
                if tb['codigo'] == tipo_bus:
                    resultado['precio_hora'] = tb.get('precio_base_hora') or 0
                    resultado['precio_km'] = tb.get('precio_base_km') or 0
                    resultado['origen'] = 'tipo_bus'
                    break

    # Calcular subtotal
    resultado['subtotal'] = (
        resultado['precio_base'] +
        (resultado['precio_km'] * kms) +
        (resultado['precio_hora'] * horas)
    )

    # 4. Aplicar multiplicador de temporada
    if fecha:
        # Convertir fecha a string si es datetime.date
        if hasattr(fecha, 'strftime'):
            fecha_str = fecha.strftime('%Y-%m-%d')
        else:
            fecha_str = str(fecha)
        fecha_mm_dd = fecha_str[5:10] if len(fecha_str) >= 10 else fecha_str  # Extraer MM-DD
        temporada = obtener_temporada_por_fecha(fecha_mm_dd)
        if temporada:
            resultado['multiplicador_temporada'] = temporada.get('multiplicador') or 1.0

    # 5. Aplicar multiplicador de tipo de cliente
    if tipo_cliente_codigo:
        tipos_cliente = obtener_tipos_cliente()
        for tc in tipos_cliente:
            if tc['codigo'] == tipo_cliente_codigo:
                resultado['multiplicador_cliente'] = tc.get('multiplicador') or 1.0
                break

    # Calcular total (subtotal * multiplicadores)
    resultado['total'] = resultado['subtotal'] * resultado['multiplicador_temporada'] * resultado['multiplicador_cliente']

    return resultado


# --- PEAJES DE AUTOPISTAS ---
def guardar_peaje(autopista: str, nombre: str, tramo_origen: str, tramo_destino: str,
                  tarifa_autobus: float, tarifa_coche: float = 0, notas: str = ""):
    """Guarda o actualiza un peaje de autopista."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO peajes (autopista, nombre, tramo_origen, tramo_destino, tarifa_autobus, tarifa_coche, notas)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (autopista, nombre, tramo_origen, tramo_destino, tarifa_autobus, tarifa_coche, notas))

    conn.commit()
    conn.close()


def obtener_peajes(autopista: str = None):
    """Obtiene todos los peajes activos, opcionalmente filtrados por autopista."""
    conn = get_connection()
    cursor = conn.cursor()

    if autopista:
        cursor.execute('SELECT * FROM peajes WHERE autopista = ? AND activo = 1 ORDER BY tramo_origen', (autopista,))
    else:
        cursor.execute('SELECT * FROM peajes WHERE activo = 1 ORDER BY autopista, tramo_origen')

    peajes = cursor.fetchall()
    conn.close()

    return [dict(p) for p in peajes]


def obtener_autopistas():
    """Obtiene la lista de autopistas únicas."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT DISTINCT autopista, nombre FROM peajes WHERE activo = 1 ORDER BY autopista')
    autopistas = cursor.fetchall()
    conn.close()

    return [dict(a) for a in autopistas]


def eliminar_peaje(peaje_id: int):
    """Elimina un peaje por su ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM peajes WHERE id = ?', (peaje_id,))

    conn.commit()
    conn.close()


def limpiar_y_recargar_peajes():
    """Limpia todos los peajes y recarga los datos iniciales."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM peajes')
    conn.commit()
    conn.close()

    cargar_peajes_iniciales()
    return obtener_peajes()


def cargar_peajes_iniciales():
    """Carga peajes de todas las autopistas de España con tarifas para autobuses."""
    peajes_iniciales = [
        # ============================================
        # AP-8 (Autopista del Cantábrico) - Bilbao a Behobia
        # ============================================
        ("AP-8", "Autopista del Cantábrico", "Bilbao", "Ermua", 4.85, 2.15, "Tramo Bizkaia"),
        ("AP-8", "Autopista del Cantábrico", "Ermua", "Elgoibar", 2.40, 1.05, ""),
        ("AP-8", "Autopista del Cantábrico", "Elgoibar", "Zarautz", 3.95, 1.75, ""),
        ("AP-8", "Autopista del Cantábrico", "Zarautz", "Donostia", 3.25, 1.45, ""),
        ("AP-8", "Autopista del Cantábrico", "Donostia", "Irun/Behobia", 4.15, 1.85, "Frontera Francia"),
        ("AP-8", "Autopista del Cantábrico", "Bilbao", "Donostia", 14.45, 6.40, "Tramo completo"),
        ("AP-8", "Autopista del Cantábrico", "Bilbao", "Irun/Behobia", 18.60, 8.25, "Tramo completo"),

        # ============================================
        # AP-1 (Autopista del Norte) - Vitoria a Burgos
        # ============================================
        ("AP-1", "Autopista del Norte", "Vitoria", "Miranda de Ebro", 5.80, 2.55, ""),
        ("AP-1", "Autopista del Norte", "Miranda de Ebro", "Briviesca", 4.95, 2.20, ""),
        ("AP-1", "Autopista del Norte", "Briviesca", "Burgos", 4.25, 1.90, ""),
        ("AP-1", "Autopista del Norte", "Eibar", "Vitoria", 6.45, 2.85, "Tramo Maltzaga"),
        ("AP-1", "Autopista del Norte", "Vitoria", "Burgos", 15.00, 6.65, "Tramo completo"),
        ("AP-1", "Autopista del Norte", "Eibar", "Burgos", 21.45, 9.50, "Eibar-Burgos completo"),

        # ============================================
        # AP-15 (Autopista de Navarra)
        # ============================================
        ("AP-15", "Autopista de Navarra", "Pamplona", "Tafalla", 4.50, 2.00, ""),
        ("AP-15", "Autopista de Navarra", "Tafalla", "Tudela", 5.20, 2.30, ""),
        ("AP-15", "Autopista de Navarra", "Pamplona", "Tudela", 9.70, 4.30, "Tramo completo"),

        # ============================================
        # AP-68 (Autopista Vasco-Aragonesa) - Bilbao a Zaragoza
        # Tarifas Pesados 2 (autobuses 4+ ejes)
        # ============================================
        ("AP-68", "Autopista Vasco-Aragonesa", "Bilbao", "Altube", 7.82, 3.45, ""),
        ("AP-68", "Autopista Vasco-Aragonesa", "Altube", "Miranda de Ebro", 8.95, 3.95, ""),
        ("AP-68", "Autopista Vasco-Aragonesa", "Miranda de Ebro", "Haro", 10.92, 4.82, ""),
        ("AP-68", "Autopista Vasco-Aragonesa", "Haro", "Logroño", 5.56, 2.45, ""),
        ("AP-68", "Autopista Vasco-Aragonesa", "Logroño", "Calahorra", 8.12, 3.58, ""),
        ("AP-68", "Autopista Vasco-Aragonesa", "Calahorra", "Alfaro", 5.78, 2.55, ""),
        ("AP-68", "Autopista Vasco-Aragonesa", "Alfaro", "Tudela", 4.95, 2.18, ""),
        ("AP-68", "Autopista Vasco-Aragonesa", "Tudela", "Gallur", 8.45, 3.73, ""),
        ("AP-68", "Autopista Vasco-Aragonesa", "Gallur", "Alagón", 4.85, 2.14, ""),
        ("AP-68", "Autopista Vasco-Aragonesa", "Alagón", "Zaragoza", 5.70, 2.52, ""),
        ("AP-68", "Autopista Vasco-Aragonesa", "Bilbao", "Haro", 27.78, 12.27, ""),
        ("AP-68", "Autopista Vasco-Aragonesa", "Bilbao", "Logroño", 30.54, 13.49, ""),
        ("AP-68", "Autopista Vasco-Aragonesa", "Bilbao", "Zaragoza", 57.10, 25.22, "Tramo completo"),
        ("AP-68", "Autopista Vasco-Aragonesa", "Logroño", "Zaragoza", 37.85, 16.72, ""),

        # ============================================
        # A-636 (Beasain-Bergara) - Free flow
        # ============================================
        ("A-636", "Autopista Beasain-Bergara", "Beasain", "Bergara", 2.85, 1.25, "Free flow - sin cabinas"),

        # ============================================
        # AP-7 (Autopista del Mediterráneo)
        # ============================================
        # Tramo Cataluña
        ("AP-7", "Autopista del Mediterráneo", "La Jonquera", "Girona", 15.80, 6.98, "Frontera Francia"),
        ("AP-7", "Autopista del Mediterráneo", "Girona", "Barcelona", 16.45, 7.27, ""),
        ("AP-7", "Autopista del Mediterráneo", "Barcelona", "Tarragona", 14.20, 6.27, ""),
        ("AP-7", "Autopista del Mediterráneo", "Tarragona", "Castellón", 24.50, 10.82, ""),
        ("AP-7", "Autopista del Mediterráneo", "La Jonquera", "Barcelona", 32.25, 14.25, ""),
        # Tramo Valencia
        ("AP-7", "Autopista del Mediterráneo", "Castellón", "Valencia", 12.80, 5.65, ""),
        ("AP-7", "Autopista del Mediterráneo", "Valencia", "Alicante", 18.60, 8.21, ""),
        ("AP-7", "Autopista del Mediterráneo", "Alicante", "Murcia", 8.40, 3.71, ""),
        # Tramo completo
        ("AP-7", "Autopista del Mediterráneo", "Barcelona", "Valencia", 37.30, 16.47, ""),
        ("AP-7", "Autopista del Mediterráneo", "Barcelona", "Alicante", 55.90, 24.68, ""),
        ("AP-7", "Autopista del Mediterráneo", "Valencia", "Murcia", 27.00, 11.92, ""),

        # ============================================
        # AP-2 (Autopista del Nordeste) - Zaragoza a Barcelona
        # ============================================
        ("AP-2", "Autopista del Nordeste", "Zaragoza", "Lleida", 22.40, 9.89, ""),
        ("AP-2", "Autopista del Nordeste", "Lleida", "Barcelona", 26.80, 11.84, ""),
        ("AP-2", "Autopista del Nordeste", "Zaragoza", "Barcelona", 49.20, 21.73, "Tramo completo"),

        # ============================================
        # AP-6 / AP-61 / AP-51 (Autopistas de Madrid)
        # ============================================
        ("AP-6", "Autopista del Noroeste", "Villalba", "Adanero", 18.95, 8.37, ""),
        ("AP-6", "Autopista del Noroeste", "Villalba", "San Rafael", 9.85, 4.35, ""),
        ("AP-6", "Autopista del Noroeste", "San Rafael", "Villacastín", 5.20, 2.30, "Túnel de Guadarrama"),
        ("AP-51", "Autopista AP-51", "Villacastín", "Ávila", 8.75, 3.86, ""),
        ("AP-61", "Autopista AP-61", "San Rafael", "Segovia", 7.80, 3.44, ""),

        # ============================================
        # AP-9 (Autopista del Atlántico - Galicia)
        # 50% descuento vehículos pesados ya aplicado
        # ============================================
        ("AP-9", "Autopista del Atlántico", "Ferrol", "A Coruña", 5.25, 2.32, "50% dto. pesados aplicado"),
        ("AP-9", "Autopista del Atlántico", "A Coruña", "Santiago", 6.80, 3.00, "50% dto. pesados aplicado"),
        ("AP-9", "Autopista del Atlántico", "Santiago", "Pontevedra", 7.45, 3.29, "50% dto. pesados aplicado"),
        ("AP-9", "Autopista del Atlántico", "Pontevedra", "Vigo", 4.85, 2.14, "50% dto. pesados aplicado"),
        ("AP-9", "Autopista del Atlántico", "Vigo", "Tui", 3.90, 1.72, "Frontera Portugal"),
        ("AP-9", "Autopista del Atlántico", "A Coruña", "Vigo", 19.10, 8.44, "50% dto. pesados aplicado"),
        ("AP-9", "Autopista del Atlántico", "Ferrol", "Vigo", 24.35, 10.75, "Tramo completo"),

        # ============================================
        # AP-66 (Autopista de la Plata - León a Campomanes)
        # 60% descuento vehículos pesados ya aplicado
        # ============================================
        ("AP-66", "Autopista de la Plata", "León", "La Robla", 4.80, 2.12, "60% dto. pesados aplicado"),
        ("AP-66", "Autopista de la Plata", "La Robla", "Villamanín", 5.60, 2.47, "60% dto. pesados aplicado"),
        ("AP-66", "Autopista de la Plata", "Villamanín", "Campomanes", 6.40, 2.83, "60% dto. pesados aplicado"),
        ("AP-66", "Autopista de la Plata", "León", "Campomanes", 16.80, 7.42, "Tramo completo, 60% dto."),

        # ============================================
        # AP-71 (Autopista León - Astorga)
        # ============================================
        ("AP-71", "Autopista León-Astorga", "León", "Astorga", 7.25, 3.20, ""),

        # ============================================
        # C-32 / C-16 (Autopistas Generalitat Catalunya)
        # ============================================
        ("C-32", "Autopista del Maresme", "Barcelona", "Mataró", 4.85, 2.14, ""),
        ("C-32", "Autopista del Maresme", "Mataró", "Blanes", 6.40, 2.83, ""),
        ("C-32", "Autopista del Maresme", "Barcelona", "Blanes", 11.25, 4.97, ""),
        ("C-32", "Autopista del Garraf", "Barcelona", "Sitges", 5.20, 2.30, ""),
        ("C-32", "Autopista del Garraf", "Sitges", "El Vendrell", 6.80, 3.00, ""),
        ("C-16", "Autopista Montserrat", "Barcelona", "Terrassa", 4.45, 1.96, ""),
        ("C-16", "Autopista Montserrat", "Terrassa", "Manresa", 8.60, 3.80, "Túnel del Cadí incluido"),
        ("C-16", "Túnel del Cadí", "Bagà", "Bellver", 22.40, 9.89, "Solo túnel"),

        # ============================================
        # R-2, R-3, R-4, R-5 (Radiales de Madrid)
        # ============================================
        ("R-2", "Radial 2", "M-40", "Guadalajara", 8.95, 3.95, ""),
        ("R-3", "Radial 3", "M-40", "Arganda", 5.80, 2.56, ""),
        ("R-4", "Radial 4", "M-40", "Ocaña", 11.20, 4.95, ""),
        ("R-5", "Radial 5", "M-40", "Navalcarnero", 6.45, 2.85, ""),

        # ============================================
        # M-12 (Madrid - Aeropuerto)
        # ============================================
        ("M-12", "Eje Aeropuerto", "M-40", "Aeropuerto T4", 4.80, 2.12, ""),

        # ============================================
        # AP-36 / AP-41 (Autopistas de Castilla-La Mancha)
        # ============================================
        ("AP-36", "Autopista AP-36", "Ocaña", "La Roda", 16.80, 7.42, ""),
        ("AP-41", "Autopista AP-41", "Madrid", "Toledo", 12.50, 5.52, ""),

        # ============================================
        # AG-55 / AG-57 (Autopistas Galicia)
        # ============================================
        ("AG-55", "Autovía A Coruña-Carballo", "A Coruña", "Carballo", 3.80, 1.68, ""),
        ("AG-57", "Autovía Vigo-O Porriño", "Vigo", "O Porriño", 2.95, 1.30, ""),

        # ============================================
        # TÚNELES
        # ============================================
        ("TUNEL", "Túnel de Artxanda", "Bilbao centro", "Artxanda", 3.20, 1.40, "Túnel urbano Bilbao"),
        ("TUNEL", "Túnel del Cadí", "Bagà", "Bellver", 22.40, 9.89, "Pirineos"),
        ("TUNEL", "Túnel de Vallvidrera", "Barcelona", "Sant Cugat", 5.60, 2.47, ""),
        ("TUNEL", "Túnel de Sóller", "Sóller", "Palma", 6.80, 3.00, "Mallorca"),

        # ============================================
        # AP-4 (Sevilla - Cádiz)
        # ============================================
        ("AP-4", "Autopista del Sur", "Sevilla", "Jerez", 9.85, 4.35, ""),
        ("AP-4", "Autopista del Sur", "Jerez", "Cádiz", 4.20, 1.85, ""),
        ("AP-4", "Autopista del Sur", "Sevilla", "Cádiz", 14.05, 6.20, "Tramo completo"),

        # ============================================
        # A-15 (Autovía Leitzaran) - Gratuita
        # ============================================
        ("A-15", "Autovía del Leitzaran", "Andoain", "Lekunberri", 0, 0, "Gratuita"),
    ]

    for peaje in peajes_iniciales:
        guardar_peaje(*peaje)


def cargar_tipos_bus_iniciales():
    """Carga tipos de bus iniciales."""
    tipos_bus = [
        ("MINI", "Minibus 16-19 plazas", 19, 45.00, 0.95),
        ("MIDI", "Midibus 25-35 plazas", 35, 52.00, 1.10),
        ("STD", "Bus estándar 50-55 plazas", 55, 58.00, 1.25),
        ("GRAN", "Gran turismo 55-60 plazas", 60, 65.00, 1.40),
        ("DOBLE", "Bus 2 pisos 70-80 plazas", 80, 85.00, 1.65),
    ]
    for codigo, nombre, capacidad, precio_hora, precio_km in tipos_bus:
        guardar_tipo_bus(codigo, nombre, capacidad, precio_hora, precio_km)


def cargar_tipos_cliente_iniciales():
    """Carga tipos de cliente iniciales con multiplicadores."""
    tipos_cliente = [
        ("STANDARD", "Cliente estándar", 1.0),
        ("FRECUENTE", "Cliente frecuente", 0.95),
        ("VIP", "Cliente VIP", 0.90),
        ("AGENCIA", "Agencia de viajes", 0.85),
        ("EMPRESA", "Empresa con contrato", 0.88),
        ("COLEGIO", "Centro educativo", 0.92),
        ("DEPORTIVO", "Club deportivo", 0.90),
        ("PREMIUM", "Premium (margen alto)", 1.15),
    ]
    for codigo, nombre, multiplicador in tipos_cliente:
        guardar_tipo_cliente(codigo, nombre, multiplicador)


def cargar_temporadas_iniciales():
    """Carga temporadas iniciales."""
    temporadas = [
        ("BAJA", "Temporada baja", "01-15", "03-14", 0.85),
        ("MEDIA", "Temporada media", "03-15", "06-14", 1.00),
        ("ALTA", "Temporada alta", "06-15", "09-14", 1.20),
        ("PUENTES", "Puentes y festivos", "09-15", "11-14", 1.10),
        ("NAVIDAD", "Navidad y fin de año", "12-15", "01-06", 1.25),
    ]
    for codigo, nombre, inicio, fin, mult in temporadas:
        guardar_temporada(codigo, nombre, inicio, fin, mult)


def cargar_tarifas_servicio_iniciales():
    """Carga tarifas por tipo de servicio con precios base."""
    # Formato: (tipo_servicio, tipo_bus, precio_base, precio_km, precio_hora, minimo)
    tarifas = [
        # BODAS - Precio base alto, servicio premium
        ("BODA", "MINI", 180.00, 1.20, 55.00, 350.00),
        ("BODA", "MIDI", 220.00, 1.35, 62.00, 420.00),
        ("BODA", "STD", 280.00, 1.50, 72.00, 520.00),
        ("BODA", "GRAN", 350.00, 1.70, 85.00, 650.00),

        # TRANSFER AEROPUERTO - Base fija por el servicio
        ("TRANSFER", "MINI", 80.00, 1.00, 45.00, 120.00),
        ("TRANSFER", "MIDI", 100.00, 1.15, 52.00, 150.00),
        ("TRANSFER", "STD", 120.00, 1.30, 60.00, 180.00),
        ("TRANSFER", "GRAN", 150.00, 1.45, 70.00, 220.00),

        # EXCURSION - Base pequeña, principalmente km y horas
        ("EXCURSION", "MINI", 50.00, 0.95, 42.00, 200.00),
        ("EXCURSION", "MIDI", 60.00, 1.08, 50.00, 250.00),
        ("EXCURSION", "STD", 70.00, 1.22, 56.00, 300.00),
        ("EXCURSION", "GRAN", 90.00, 1.38, 65.00, 380.00),

        # ESCOLAR - Sin base, precio ajustado
        ("ESCOLAR", "MINI", 0.00, 0.85, 38.00, 150.00),
        ("ESCOLAR", "MIDI", 0.00, 0.98, 45.00, 180.00),
        ("ESCOLAR", "STD", 0.00, 1.10, 52.00, 220.00),

        # DEPORTIVO - Similar a escolar
        ("DEPORTIVO", "MINI", 30.00, 0.88, 40.00, 160.00),
        ("DEPORTIVO", "MIDI", 40.00, 1.00, 48.00, 200.00),
        ("DEPORTIVO", "STD", 50.00, 1.15, 55.00, 260.00),
        ("DEPORTIVO", "GRAN", 65.00, 1.30, 62.00, 320.00),

        # CONGRESOS/EVENTOS - Base alta, servicio completo
        ("CONGRESO", "MINI", 100.00, 1.05, 48.00, 200.00),
        ("CONGRESO", "MIDI", 130.00, 1.20, 56.00, 280.00),
        ("CONGRESO", "STD", 160.00, 1.35, 65.00, 350.00),
        ("CONGRESO", "GRAN", 200.00, 1.55, 78.00, 450.00),
        ("CONGRESO", "DOBLE", 280.00, 1.80, 95.00, 600.00),

        # CIRCUITO TURISTICO - Varios días
        ("CIRCUITO", "STD", 150.00, 1.18, 54.00, 450.00),
        ("CIRCUITO", "GRAN", 200.00, 1.35, 65.00, 550.00),
        ("CIRCUITO", "DOBLE", 300.00, 1.60, 85.00, 750.00),

        # DISCRECIONAL - Base pequeña, estándar
        ("DISCRECIONAL", "MINI", 40.00, 0.92, 42.00, 150.00),
        ("DISCRECIONAL", "MIDI", 50.00, 1.05, 50.00, 200.00),
        ("DISCRECIONAL", "STD", 60.00, 1.20, 58.00, 260.00),
        ("DISCRECIONAL", "GRAN", 80.00, 1.38, 68.00, 340.00),
    ]

    for tipo_serv, tipo_bus, base, km, hora, minimo in tarifas:
        guardar_tarifa_servicio(tipo_serv, tipo_bus, base, km, hora, minimo)


# Inicializar todas las bases de datos
init_incentivos_db()
init_premios_presupuesto_db()
init_tarifas_db()

# Inicializar la base de datos al importar el módulo
init_db()

# Cargar datos iniciales si las tablas están vacías
if not obtener_peajes():
    cargar_peajes_iniciales()

if not obtener_tipos_bus():
    cargar_tipos_bus_iniciales()

if not obtener_tipos_cliente():
    cargar_tipos_cliente_iniciales()

if not obtener_temporadas():
    cargar_temporadas_iniciales()

if not obtener_tarifas_servicio():
    cargar_tarifas_servicio_iniciales()
