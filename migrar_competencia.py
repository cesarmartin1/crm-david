"""
Script para migrar datos de competencia de SQLite local a Supabase
Ejecutar una sola vez después de crear las tablas en Supabase
"""
import sqlite3
from pathlib import Path
from supabase import create_client
import os

# Configuración - ajustar según necesidad
SQLITE_PATH = Path(__file__).parent / "crm_notas.db"

# Leer credenciales de Supabase desde archivo .streamlit/secrets.toml
def get_supabase_creds():
    secrets_path = Path(__file__).parent / ".streamlit" / "secrets.toml"
    creds = {}
    if secrets_path.exists():
        with open(secrets_path, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"')
                    creds[key] = value
    return creds

def migrar():
    print("=== Migración de Competencia a Supabase ===\n")

    # Conectar a SQLite local
    if not SQLITE_PATH.exists():
        print(f"ERROR: No se encuentra la base de datos local en {SQLITE_PATH}")
        return

    conn = sqlite3.connect(str(SQLITE_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Conectar a Supabase
    creds = get_supabase_creds()
    if not creds.get('SUPABASE_URL') or not creds.get('SUPABASE_SERVICE_ROLE_KEY'):
        print("ERROR: No se encontraron las credenciales de Supabase en .streamlit/secrets.toml")
        return

    supabase = create_client(creds['SUPABASE_URL'], creds['SUPABASE_SERVICE_ROLE_KEY'])

    # 1. Migrar competidores
    print("1. Migrando competidores...")
    cursor.execute("SELECT * FROM competidores WHERE activo = 1")
    competidores = [dict(row) for row in cursor.fetchall()]

    mapa_ids = {}  # SQLite ID -> Supabase ID

    for comp in competidores:
        try:
            # Verificar si ya existe
            existe = supabase.table('competidores').select('id').eq('nombre', comp['nombre']).execute()
            if existe.data:
                mapa_ids[comp['id']] = existe.data[0]['id']
                print(f"   - {comp['nombre']}: ya existe (id={existe.data[0]['id']})")
                continue

            result = supabase.table('competidores').insert({
                'nombre': comp['nombre'],
                'segmento': comp.get('segmento', 'estandar'),
                'zona_operacion': comp.get('zona_operacion', ''),
                'flota_estimada': comp.get('flota_estimada'),
                'fortalezas': comp.get('fortalezas', ''),
                'debilidades': comp.get('debilidades', ''),
                'notas': comp.get('notas', ''),
                'activo': True
            }).execute()

            if result.data:
                mapa_ids[comp['id']] = result.data[0]['id']
                print(f"   - {comp['nombre']}: migrado (id={result.data[0]['id']})")
        except Exception as e:
            print(f"   - {comp['nombre']}: ERROR - {e}")

    print(f"\n   Total competidores migrados: {len(mapa_ids)}")

    # 2. Migrar vehículos
    print("\n2. Migrando vehículos...")
    cursor.execute("SELECT * FROM vehiculos_competencia WHERE activo = 1")
    vehiculos = [dict(row) for row in cursor.fetchall()]

    count_vehiculos = 0
    for veh in vehiculos:
        try:
            nuevo_comp_id = mapa_ids.get(veh['competidor_id'])
            if not nuevo_comp_id:
                print(f"   - Saltando vehículo {veh.get('matricula')}: competidor no migrado")
                continue

            # Verificar si ya existe por matrícula
            if veh.get('matricula'):
                existe = supabase.table('vehiculos_competencia').select('id')\
                    .eq('competidor_id', nuevo_comp_id)\
                    .eq('matricula', veh['matricula']).execute()
                if existe.data:
                    continue  # Ya existe

            supabase.table('vehiculos_competencia').insert({
                'competidor_id': nuevo_comp_id,
                'matricula': veh.get('matricula'),
                'tipo_vehiculo': veh.get('tipo_vehiculo', 'AUTOBUS'),
                'marca': veh.get('marca', ''),
                'modelo': veh.get('modelo', ''),
                'plazas': veh.get('plazas'),
                'ano_matriculacion': veh.get('ano_matriculacion'),
                'edad': veh.get('edad'),
                'distintivo_ambiental': veh.get('distintivo_ambiental', ''),
                'pmr': bool(veh.get('pmr')),
                'wc': bool(veh.get('wc')),
                'wifi': bool(veh.get('wifi')),
                'escolar': bool(veh.get('escolar')),
                'observaciones': veh.get('observaciones', ''),
                'activo': True
            }).execute()
            count_vehiculos += 1
        except Exception as e:
            print(f"   - Error vehículo {veh.get('matricula')}: {e}")

    print(f"   Total vehículos migrados: {count_vehiculos}")

    # 3. Migrar cotizaciones
    print("\n3. Migrando cotizaciones...")
    cursor.execute("SELECT * FROM cotizaciones_competencia")
    cotizaciones = [dict(row) for row in cursor.fetchall()]

    count_cot = 0
    for cot in cotizaciones:
        try:
            nuevo_comp_id = mapa_ids.get(cot['competidor_id'])
            if not nuevo_comp_id:
                continue

            supabase.table('cotizaciones_competencia').insert({
                'competidor_id': nuevo_comp_id,
                'tipo_servicio': cot.get('tipo_servicio'),
                'precio': cot.get('precio'),
                'tipo_vehiculo': cot.get('tipo_vehiculo', 'STD'),
                'km_estimados': cot.get('km_estimados'),
                'duracion_horas': cot.get('duracion_horas'),
                'origen': cot.get('origen', ''),
                'destino': cot.get('destino', ''),
                'fecha_captura': cot.get('fecha_captura'),
                'fuente': cot.get('fuente', ''),
                'notas': cot.get('notas', '')
            }).execute()
            count_cot += 1
        except Exception as e:
            print(f"   - Error cotización: {e}")

    print(f"   Total cotizaciones migradas: {count_cot}")

    conn.close()
    print("\n=== Migración completada ===")


if __name__ == "__main__":
    migrar()
