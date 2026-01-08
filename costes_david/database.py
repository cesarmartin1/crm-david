"""
Módulo de Base de Datos - Análisis de Costes DAVID
Gestión de datos multi-año con SQLite
"""

import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

# Ruta de la base de datos
DB_PATH = Path(__file__).parent / "costes_david.db"


@contextmanager
def get_connection():
    """Context manager para conexiones a la base de datos."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_database():
    """Inicializa la base de datos con todas las tablas necesarias."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Tabla de años fiscales
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ejercicios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                año INTEGER UNIQUE NOT NULL,
                descripcion TEXT,
                activo INTEGER DEFAULT 1,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabla de vehículos (maestro) - Todos los campos del Excel
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehiculos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_vehiculo INTEGER,
                tipo_codigo TEXT,
                matricula TEXT UNIQUE NOT NULL,
                marca TEXT,
                modelo TEXT,
                plazas INTEGER,
                codigo_conductor INTEGER,
                conductor TEXT,
                vehiculo_bloqueado INTEGER DEFAULT 0,
                estado TEXT DEFAULT 'A',
                fecha_baja DATE,
                fecha_final_itv DATE,
                fecha_final_tacografo DATE,
                bastidor TEXT,
                num_obra TEXT,
                longitud REAL,
                altura REAL,
                vehiculo_tipo TEXT,
                tipo INTEGER,
                fecha_matriculacion DATE,
                primera_matriculacion DATE,
                codigo_empresa INTEGER,
                empresa TEXT,
                inhabilitado_trafico INTEGER DEFAULT 0,
                kilometros INTEGER DEFAULT 0,
                caducidad_extintores DATE,
                caducidad_escolar DATE,
                activo INTEGER DEFAULT 1,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabla de datos de vehículos por año
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehiculos_año (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehiculo_id INTEGER NOT NULL,
                ejercicio_id INTEGER NOT NULL,
                km_inicio_año INTEGER DEFAULT 0,
                km_fin_año INTEGER DEFAULT 0,
                km_anual INTEGER DEFAULT 0,
                horas_servicio REAL DEFAULT 0,
                fecha_inicio DATE,
                fecha_fin DATE,
                porcentaje_año REAL DEFAULT 1.0,
                consumo_ciudad REAL,
                consumo_carretera REAL,
                consumo_mixto REAL,
                FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id),
                FOREIGN KEY (ejercicio_id) REFERENCES ejercicios(id),
                UNIQUE(vehiculo_id, ejercicio_id)
            )
        """)

        # Tabla de adquisición
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS costes_adquisicion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehiculo_id INTEGER NOT NULL,
                ejercicio_id INTEGER NOT NULL,
                valor_compra REAL DEFAULT 0,
                valor_residual REAL DEFAULT 0,
                vida_util REAL DEFAULT 10,
                años_uso REAL DEFAULT 0,
                coste_anual REAL DEFAULT 0,
                fecha_compra DATE,
                fecha_venta DATE,
                valor_venta REAL,
                FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id),
                FOREIGN KEY (ejercicio_id) REFERENCES ejercicios(id),
                UNIQUE(vehiculo_id, ejercicio_id)
            )
        """)

        # Tabla de financiación
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS costes_financiacion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehiculo_id INTEGER NOT NULL,
                ejercicio_id INTEGER NOT NULL,
                financiado INTEGER DEFAULT 0,
                importe_financiado REAL DEFAULT 0,
                plazo_meses INTEGER DEFAULT 60,
                tae REAL DEFAULT 0,
                cuota_anual REAL DEFAULT 0,
                intereses REAL DEFAULT 0,
                coste_anual REAL DEFAULT 0,
                FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id),
                FOREIGN KEY (ejercicio_id) REFERENCES ejercicios(id),
                UNIQUE(vehiculo_id, ejercicio_id)
            )
        """)

        # Tabla de mantenimiento
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS costes_mantenimiento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehiculo_id INTEGER NOT NULL,
                ejercicio_id INTEGER NOT NULL,
                ratio_tipo REAL DEFAULT 0,
                coste_anual REAL DEFAULT 0,
                detalle TEXT,
                FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id),
                FOREIGN KEY (ejercicio_id) REFERENCES ejercicios(id),
                UNIQUE(vehiculo_id, ejercicio_id)
            )
        """)

        # Tabla de seguros
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS costes_seguros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehiculo_id INTEGER NOT NULL,
                ejercicio_id INTEGER NOT NULL,
                aseguradora TEXT,
                num_poliza TEXT,
                prima_1_semestre REAL DEFAULT 0,
                prima_2_semestre REAL DEFAULT 0,
                coste_anual REAL DEFAULT 0,
                FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id),
                FOREIGN KEY (ejercicio_id) REFERENCES ejercicios(id),
                UNIQUE(vehiculo_id, ejercicio_id)
            )
        """)

        # Tabla de fiscales
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS costes_fiscales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehiculo_id INTEGER NOT NULL,
                ejercicio_id INTEGER NOT NULL,
                sovi REAL DEFAULT 0,
                itv_1 REAL DEFAULT 0,
                itv_escolar_1 REAL DEFAULT 0,
                itv_2 REAL DEFAULT 0,
                itv_escolar_2 REAL DEFAULT 0,
                revision_tacografo REAL DEFAULT 0,
                ivtm REAL DEFAULT 0,
                iae REAL DEFAULT 0,
                dris REAL DEFAULT 0,
                visado REAL DEFAULT 0,
                licencia_com REAL DEFAULT 0,
                coste_anual REAL DEFAULT 0,
                FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id),
                FOREIGN KEY (ejercicio_id) REFERENCES ejercicios(id),
                UNIQUE(vehiculo_id, ejercicio_id)
            )
        """)

        # Tabla de combustible
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS costes_combustible (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehiculo_id INTEGER NOT NULL,
                ejercicio_id INTEGER NOT NULL,
                consumo_ciudad REAL DEFAULT 0,
                consumo_carretera REAL DEFAULT 0,
                consumo_mixto REAL DEFAULT 0,
                precio_litro REAL DEFAULT 0,
                coste_km REAL DEFAULT 0,
                coste_anual REAL DEFAULT 0,
                FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id),
                FOREIGN KEY (ejercicio_id) REFERENCES ejercicios(id),
                UNIQUE(vehiculo_id, ejercicio_id)
            )
        """)

        # Tabla de neumáticos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS costes_neumaticos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehiculo_id INTEGER NOT NULL,
                ejercicio_id INTEGER NOT NULL,
                coste_unitario REAL DEFAULT 0,
                vida_util_km INTEGER DEFAULT 0,
                coste_km REAL DEFAULT 0,
                coste_anual REAL DEFAULT 0,
                FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id),
                FOREIGN KEY (ejercicio_id) REFERENCES ejercicios(id),
                UNIQUE(vehiculo_id, ejercicio_id)
            )
        """)

        # Tabla de urea/adblue
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS costes_urea (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehiculo_id INTEGER NOT NULL,
                ejercicio_id INTEGER NOT NULL,
                consumo_por_km REAL DEFAULT 0,
                precio_litro REAL DEFAULT 0,
                coste_anual REAL DEFAULT 0,
                FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id),
                FOREIGN KEY (ejercicio_id) REFERENCES ejercicios(id),
                UNIQUE(vehiculo_id, ejercicio_id)
            )
        """)

        # Tabla de personal
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS costes_personal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ejercicio_id INTEGER NOT NULL,
                coste_total_conductores REAL DEFAULT 0,
                total_horas REAL DEFAULT 0,
                absentismo REAL DEFAULT 0,
                horas_servicio REAL DEFAULT 0,
                horas_productivas REAL DEFAULT 0,
                salario_hora_servicio REAL DEFAULT 0,
                coste_empresa_salario_ss REAL DEFAULT 0,
                indirectos REAL DEFAULT 0,
                FOREIGN KEY (ejercicio_id) REFERENCES ejercicios(id),
                UNIQUE(ejercicio_id)
            )
        """)

        # Tabla de indirectos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS costes_indirectos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ejercicio_id INTEGER NOT NULL,
                porcentaje_estructura REAL DEFAULT 0.137,
                total_horas_estructura INTEGER DEFAULT 1792,
                total_km_flota INTEGER DEFAULT 0,
                coste_total REAL DEFAULT 0,
                FOREIGN KEY (ejercicio_id) REFERENCES ejercicios(id),
                UNIQUE(ejercicio_id)
            )
        """)

        # Tabla de P&G (Pérdidas y Ganancias)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pyg (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ejercicio_id INTEGER NOT NULL,
                cuenta TEXT NOT NULL,
                descripcion TEXT,
                importe_no_ajustado REAL DEFAULT 0,
                importe_ajustado REAL DEFAULT 0,
                ponderado_directo REAL DEFAULT 0,
                ponderado_indirecto REAL DEFAULT 0,
                es_coste_directo INTEGER DEFAULT 0,
                es_coste_indirecto INTEGER DEFAULT 0,
                categoria TEXT,
                FOREIGN KEY (ejercicio_id) REFERENCES ejercicios(id)
            )
        """)

        # Tabla de resumen de costes por vehículo
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resumen_costes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehiculo_id INTEGER NOT NULL,
                ejercicio_id INTEGER NOT NULL,
                costes_tiempo REAL DEFAULT 0,
                costes_km REAL DEFAULT 0,
                coste_total REAL DEFAULT 0,
                coste_hora REAL DEFAULT 0,
                coste_km_unitario REAL DEFAULT 0,
                coste_mensual REAL DEFAULT 0,
                fecha_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id),
                FOREIGN KEY (ejercicio_id) REFERENCES ejercicios(id),
                UNIQUE(vehiculo_id, ejercicio_id)
            )
        """)

        # Índices para mejorar rendimiento
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vehiculos_año_vehiculo ON vehiculos_año(vehiculo_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vehiculos_año_ejercicio ON vehiculos_año(ejercicio_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pyg_ejercicio ON pyg(ejercicio_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resumen_ejercicio ON resumen_costes(ejercicio_id)")

        conn.commit()


# ============================================================================
# FUNCIONES CRUD PARA EJERCICIOS
# ============================================================================

def crear_ejercicio(año: int, descripcion: str = None) -> int:
    """Crea un nuevo ejercicio fiscal."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO ejercicios (año, descripcion) VALUES (?, ?)",
            (año, descripcion or f"Ejercicio {año}")
        )
        conn.commit()
        cursor.execute("SELECT id FROM ejercicios WHERE año = ?", (año,))
        return cursor.fetchone()[0]


def obtener_ejercicios() -> list:
    """Obtiene todos los ejercicios."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ejercicios ORDER BY año DESC")
        return [dict(row) for row in cursor.fetchall()]


def obtener_ejercicio_por_año(año: int) -> dict:
    """Obtiene un ejercicio por año."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM ejercicios WHERE año = ?", (año,))
        row = cursor.fetchone()
        return dict(row) if row else None


# ============================================================================
# FUNCIONES CRUD PARA VEHÍCULOS
# ============================================================================

def crear_vehiculo(matricula: str, plazas: int = 0, tipo: int = 2, **kwargs) -> int:
    """Crea un nuevo vehículo con todos sus campos."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Campos base
        campos = ['matricula', 'plazas', 'tipo']
        valores = [matricula, plazas, tipo]

        # Campos opcionales
        campos_opcionales = [
            'codigo_vehiculo', 'tipo_codigo', 'marca', 'modelo', 'codigo_conductor',
            'conductor', 'vehiculo_bloqueado', 'estado', 'fecha_baja', 'fecha_final_itv',
            'fecha_final_tacografo', 'bastidor', 'num_obra', 'longitud', 'altura',
            'vehiculo_tipo', 'fecha_matriculacion', 'primera_matriculacion',
            'codigo_empresa', 'empresa', 'inhabilitado_trafico', 'kilometros',
            'caducidad_extintores', 'caducidad_escolar'
        ]

        for campo in campos_opcionales:
            if campo in kwargs and kwargs[campo] is not None:
                campos.append(campo)
                valores.append(kwargs[campo])

        placeholders = ', '.join(['?'] * len(campos))
        campos_str = ', '.join(campos)

        cursor.execute(
            f"INSERT OR IGNORE INTO vehiculos ({campos_str}) VALUES ({placeholders})",
            valores
        )
        conn.commit()
        cursor.execute("SELECT id FROM vehiculos WHERE matricula = ?", (matricula,))
        result = cursor.fetchone()

        if result:
            return result[0]
        else:
            # Si ya existía, actualizar los campos
            vehiculo_id = None
            cursor.execute("SELECT id FROM vehiculos WHERE matricula = ?", (matricula,))
            result = cursor.fetchone()
            if result:
                vehiculo_id = result[0]
                actualizar_vehiculo(vehiculo_id, plazas=plazas, tipo=tipo, **kwargs)
            return vehiculo_id


def obtener_vehiculos(activos_solo: bool = True) -> list:
    """Obtiene todos los vehículos."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if activos_solo:
            cursor.execute("SELECT * FROM vehiculos WHERE activo = 1 ORDER BY matricula")
        else:
            cursor.execute("SELECT * FROM vehiculos ORDER BY matricula")
        return [dict(row) for row in cursor.fetchall()]


def actualizar_vehiculo(vehiculo_id: int, **kwargs) -> bool:
    """Actualiza un vehículo."""
    if not kwargs:
        return False

    with get_connection() as conn:
        cursor = conn.cursor()
        campos = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        valores = list(kwargs.values()) + [vehiculo_id]
        cursor.execute(f"UPDATE vehiculos SET {campos}, fecha_modificacion = CURRENT_TIMESTAMP WHERE id = ?", valores)
        conn.commit()
        return cursor.rowcount > 0


def eliminar_vehiculo(vehiculo_id: int) -> bool:
    """Elimina (desactiva) un vehículo."""
    return actualizar_vehiculo(vehiculo_id, activo=0)


# ============================================================================
# FUNCIONES PARA DATOS POR AÑO
# ============================================================================

def guardar_vehiculo_año(vehiculo_id: int, ejercicio_id: int, **datos) -> int:
    """Guarda o actualiza datos de vehículo para un año específico."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Verificar si existe
        cursor.execute(
            "SELECT id FROM vehiculos_año WHERE vehiculo_id = ? AND ejercicio_id = ?",
            (vehiculo_id, ejercicio_id)
        )
        existing = cursor.fetchone()

        if existing:
            # Actualizar
            campos = ", ".join([f"{k} = ?" for k in datos.keys()])
            valores = list(datos.values()) + [vehiculo_id, ejercicio_id]
            cursor.execute(
                f"UPDATE vehiculos_año SET {campos} WHERE vehiculo_id = ? AND ejercicio_id = ?",
                valores
            )
            return existing[0]
        else:
            # Insertar
            campos = ", ".join(["vehiculo_id", "ejercicio_id"] + list(datos.keys()))
            placeholders = ", ".join(["?"] * (len(datos) + 2))
            valores = [vehiculo_id, ejercicio_id] + list(datos.values())
            cursor.execute(
                f"INSERT INTO vehiculos_año ({campos}) VALUES ({placeholders})",
                valores
            )
            conn.commit()
            return cursor.lastrowid


def obtener_datos_vehiculo_año(vehiculo_id: int, ejercicio_id: int) -> dict:
    """Obtiene datos de un vehículo para un año específico."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM vehiculos_año WHERE vehiculo_id = ? AND ejercicio_id = ?",
            (vehiculo_id, ejercicio_id)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


# ============================================================================
# FUNCIONES GENÉRICAS PARA COSTES
# ============================================================================

def guardar_coste(tabla: str, vehiculo_id: int, ejercicio_id: int, **datos) -> int:
    """Guarda o actualiza un registro de coste."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Verificar si existe
        cursor.execute(
            f"SELECT id FROM {tabla} WHERE vehiculo_id = ? AND ejercicio_id = ?",
            (vehiculo_id, ejercicio_id)
        )
        existing = cursor.fetchone()

        if existing:
            # Actualizar
            campos = ", ".join([f"{k} = ?" for k in datos.keys()])
            valores = list(datos.values()) + [vehiculo_id, ejercicio_id]
            cursor.execute(
                f"UPDATE {tabla} SET {campos} WHERE vehiculo_id = ? AND ejercicio_id = ?",
                valores
            )
            return existing[0]
        else:
            # Insertar
            campos = ", ".join(["vehiculo_id", "ejercicio_id"] + list(datos.keys()))
            placeholders = ", ".join(["?"] * (len(datos) + 2))
            valores = [vehiculo_id, ejercicio_id] + list(datos.values())
            cursor.execute(
                f"INSERT INTO {tabla} ({campos}) VALUES ({placeholders})",
                valores
            )
            conn.commit()
            return cursor.lastrowid


def obtener_costes(tabla: str, ejercicio_id: int, vehiculo_id: int = None) -> list:
    """Obtiene registros de coste."""
    with get_connection() as conn:
        cursor = conn.cursor()
        if vehiculo_id:
            cursor.execute(
                f"SELECT * FROM {tabla} WHERE ejercicio_id = ? AND vehiculo_id = ?",
                (ejercicio_id, vehiculo_id)
            )
        else:
            cursor.execute(
                f"SELECT * FROM {tabla} WHERE ejercicio_id = ?",
                (ejercicio_id,)
            )
        return [dict(row) for row in cursor.fetchall()]


# ============================================================================
# FUNCIONES PARA P&G
# ============================================================================

def guardar_pyg(ejercicio_id: int, datos: list) -> int:
    """Guarda registros de P&G para un ejercicio."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Eliminar datos anteriores
        cursor.execute("DELETE FROM pyg WHERE ejercicio_id = ?", (ejercicio_id,))

        # Insertar nuevos datos
        for registro in datos:
            cursor.execute(
                """INSERT INTO pyg (ejercicio_id, cuenta, descripcion, importe_no_ajustado,
                   importe_ajustado, ponderado_directo, ponderado_indirecto, es_coste_directo,
                   es_coste_indirecto, categoria)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (ejercicio_id, registro.get('cuenta'), registro.get('descripcion'),
                 registro.get('importe_no_ajustado', 0), registro.get('importe_ajustado', 0),
                 registro.get('ponderado_directo', 0), registro.get('ponderado_indirecto', 0),
                 registro.get('es_coste_directo', 0), registro.get('es_coste_indirecto', 0),
                 registro.get('categoria'))
            )

        conn.commit()
        return len(datos)


def obtener_pyg(ejercicio_id: int) -> list:
    """Obtiene registros de P&G para un ejercicio."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pyg WHERE ejercicio_id = ? ORDER BY cuenta", (ejercicio_id,))
        return [dict(row) for row in cursor.fetchall()]


def obtener_pyg_resumen(ejercicio_id: int) -> dict:
    """Obtiene resumen de P&G por categorías."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                SUM(CASE WHEN importe_ajustado < 0 THEN ABS(importe_ajustado) ELSE 0 END) as total_gastos,
                SUM(CASE WHEN importe_ajustado > 0 THEN importe_ajustado ELSE 0 END) as total_ingresos,
                SUM(CASE WHEN es_coste_directo = 1 THEN ABS(importe_ajustado) ELSE 0 END) as costes_directos,
                SUM(CASE WHEN es_coste_indirecto = 1 THEN ABS(importe_ajustado) ELSE 0 END) as costes_indirectos
            FROM pyg WHERE ejercicio_id = ?
        """, (ejercicio_id,))
        row = cursor.fetchone()
        return dict(row) if row else {}


# ============================================================================
# FUNCIONES PARA COSTES DE PERSONAL (GLOBAL)
# ============================================================================

def guardar_personal(ejercicio_id: int, **datos) -> int:
    """Guarda o actualiza datos de personal para un ejercicio."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM costes_personal WHERE ejercicio_id = ?", (ejercicio_id,))
        existing = cursor.fetchone()

        if existing:
            campos = ", ".join([f"{k} = ?" for k in datos.keys()])
            valores = list(datos.values()) + [ejercicio_id]
            cursor.execute(f"UPDATE costes_personal SET {campos} WHERE ejercicio_id = ?", valores)
            return existing[0]
        else:
            campos = ", ".join(["ejercicio_id"] + list(datos.keys()))
            placeholders = ", ".join(["?"] * (len(datos) + 1))
            valores = [ejercicio_id] + list(datos.values())
            cursor.execute(f"INSERT INTO costes_personal ({campos}) VALUES ({placeholders})", valores)
            conn.commit()
            return cursor.lastrowid


def obtener_personal(ejercicio_id: int) -> dict:
    """Obtiene datos de personal para un ejercicio."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM costes_personal WHERE ejercicio_id = ?", (ejercicio_id,))
        row = cursor.fetchone()
        return dict(row) if row else {}


# ============================================================================
# FUNCIONES PARA INDIRECTOS (GLOBAL)
# ============================================================================

def guardar_indirectos(ejercicio_id: int, **datos) -> int:
    """Guarda o actualiza datos de indirectos para un ejercicio."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM costes_indirectos WHERE ejercicio_id = ?", (ejercicio_id,))
        existing = cursor.fetchone()

        if existing:
            campos = ", ".join([f"{k} = ?" for k in datos.keys()])
            valores = list(datos.values()) + [ejercicio_id]
            cursor.execute(f"UPDATE costes_indirectos SET {campos} WHERE ejercicio_id = ?", valores)
            return existing[0]
        else:
            campos = ", ".join(["ejercicio_id"] + list(datos.keys()))
            placeholders = ", ".join(["?"] * (len(datos) + 1))
            valores = [ejercicio_id] + list(datos.values())
            cursor.execute(f"INSERT INTO costes_indirectos ({campos}) VALUES ({placeholders})", valores)
            conn.commit()
            return cursor.lastrowid


# ============================================================================
# FUNCIONES DE CÁLCULO Y RESUMEN
# ============================================================================

def calcular_resumen_vehiculo(vehiculo_id: int, ejercicio_id: int) -> dict:
    """Calcula el resumen de costes de un vehículo para un ejercicio."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Obtener datos del vehículo para el año
        datos_año = obtener_datos_vehiculo_año(vehiculo_id, ejercicio_id)
        if not datos_año:
            return {}

        km_anual = datos_año.get('km_anual', 0) or 0
        horas_servicio = datos_año.get('horas_servicio', 0) or 0

        # Costes por tiempo
        costes_tiempo = 0

        # Adquisición
        adq = obtener_costes('costes_adquisicion', ejercicio_id, vehiculo_id)
        if adq:
            costes_tiempo += adq[0].get('coste_anual', 0) or 0

        # Financiación
        fin = obtener_costes('costes_financiacion', ejercicio_id, vehiculo_id)
        if fin:
            costes_tiempo += fin[0].get('coste_anual', 0) or 0

        # Seguros
        seg = obtener_costes('costes_seguros', ejercicio_id, vehiculo_id)
        if seg:
            costes_tiempo += seg[0].get('coste_anual', 0) or 0

        # Fiscales
        fis = obtener_costes('costes_fiscales', ejercicio_id, vehiculo_id)
        if fis:
            costes_tiempo += fis[0].get('coste_anual', 0) or 0

        # Personal (proporcional)
        personal = obtener_personal(ejercicio_id)
        if personal and horas_servicio > 0:
            coste_hora_personal = personal.get('salario_hora_servicio', 0) or 0
            costes_tiempo += coste_hora_personal * horas_servicio

        # Costes por km
        costes_km = 0

        # Mantenimiento
        mant = obtener_costes('costes_mantenimiento', ejercicio_id, vehiculo_id)
        if mant:
            costes_km += mant[0].get('coste_anual', 0) or 0

        # Combustible
        comb = obtener_costes('costes_combustible', ejercicio_id, vehiculo_id)
        if comb:
            costes_km += comb[0].get('coste_anual', 0) or 0

        # Neumáticos
        neum = obtener_costes('costes_neumaticos', ejercicio_id, vehiculo_id)
        if neum:
            costes_km += neum[0].get('coste_anual', 0) or 0

        # Urea
        urea = obtener_costes('costes_urea', ejercicio_id, vehiculo_id)
        if urea:
            costes_km += urea[0].get('coste_anual', 0) or 0

        # Totales
        coste_total = costes_tiempo + costes_km
        coste_hora = coste_total / horas_servicio if horas_servicio > 0 else 0
        coste_km_unitario = coste_total / km_anual if km_anual > 0 else 0
        coste_mensual = coste_total / 12

        resumen = {
            'costes_tiempo': costes_tiempo,
            'costes_km': costes_km,
            'coste_total': coste_total,
            'coste_hora': coste_hora,
            'coste_km_unitario': coste_km_unitario,
            'coste_mensual': coste_mensual
        }

        # Guardar resumen
        cursor.execute(
            "SELECT id FROM resumen_costes WHERE vehiculo_id = ? AND ejercicio_id = ?",
            (vehiculo_id, ejercicio_id)
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                """UPDATE resumen_costes SET costes_tiempo = ?, costes_km = ?, coste_total = ?,
                   coste_hora = ?, coste_km_unitario = ?, coste_mensual = ?, fecha_calculo = CURRENT_TIMESTAMP
                   WHERE vehiculo_id = ? AND ejercicio_id = ?""",
                (costes_tiempo, costes_km, coste_total, coste_hora, coste_km_unitario,
                 coste_mensual, vehiculo_id, ejercicio_id)
            )
        else:
            cursor.execute(
                """INSERT INTO resumen_costes (vehiculo_id, ejercicio_id, costes_tiempo, costes_km,
                   coste_total, coste_hora, coste_km_unitario, coste_mensual)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (vehiculo_id, ejercicio_id, costes_tiempo, costes_km, coste_total,
                 coste_hora, coste_km_unitario, coste_mensual)
            )

        conn.commit()
        return resumen


def obtener_resumen_flota(ejercicio_id: int) -> pd.DataFrame:
    """Obtiene el resumen de costes de toda la flota para un ejercicio."""
    with get_connection() as conn:
        query = """
            SELECT
                v.matricula,
                v.plazas,
                v.tipo,
                v.fecha_matriculacion,
                va.km_anual,
                va.horas_servicio,
                rc.costes_tiempo,
                rc.costes_km,
                rc.coste_total,
                rc.coste_hora,
                rc.coste_km_unitario,
                rc.coste_mensual
            FROM vehiculos v
            LEFT JOIN vehiculos_año va ON v.id = va.vehiculo_id AND va.ejercicio_id = ?
            LEFT JOIN resumen_costes rc ON v.id = rc.vehiculo_id AND rc.ejercicio_id = ?
            WHERE v.activo = 1
            ORDER BY v.matricula
        """
        df = pd.read_sql_query(query, conn, params=(ejercicio_id, ejercicio_id))
        return df


# Inicializar base de datos al importar el módulo
init_database()
