-- =============================================
-- TABLAS DE COMPETENCIA PARA SUPABASE
-- Ejecutar en Supabase SQL Editor
-- =============================================

-- Tabla de competidores
CREATE TABLE IF NOT EXISTS competidores (
    id BIGSERIAL PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,
    segmento TEXT DEFAULT 'estandar',
    zona_operacion TEXT,
    flota_estimada INTEGER,
    fortalezas TEXT,
    debilidades TEXT,
    notas TEXT,
    activo BOOLEAN DEFAULT true,
    fecha_registro TIMESTAMPTZ DEFAULT NOW(),
    fecha_actualizacion TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de cotizaciones de competencia
CREATE TABLE IF NOT EXISTS cotizaciones_competencia (
    id BIGSERIAL PRIMARY KEY,
    competidor_id BIGINT NOT NULL REFERENCES competidores(id) ON DELETE CASCADE,
    tipo_servicio TEXT NOT NULL,
    precio DECIMAL(10,2) NOT NULL,
    tipo_vehiculo TEXT,
    km_estimados INTEGER,
    duracion_horas DECIMAL(5,2),
    origen TEXT,
    destino TEXT,
    fecha_captura DATE DEFAULT CURRENT_DATE,
    fuente TEXT,
    notas TEXT,
    fecha_registro TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de vehículos de competencia
CREATE TABLE IF NOT EXISTS vehiculos_competencia (
    id BIGSERIAL PRIMARY KEY,
    competidor_id BIGINT NOT NULL REFERENCES competidores(id) ON DELETE CASCADE,
    matricula TEXT,
    tipo_vehiculo TEXT DEFAULT 'AUTOBUS',
    marca TEXT,
    modelo TEXT,
    plazas INTEGER,
    ano_matriculacion INTEGER,
    edad DECIMAL(4,1),
    distintivo_ambiental TEXT,
    pmr BOOLEAN DEFAULT false,
    wc BOOLEAN DEFAULT false,
    wifi BOOLEAN DEFAULT false,
    escolar BOOLEAN DEFAULT false,
    activo BOOLEAN DEFAULT true,
    observaciones TEXT,
    fecha_registro TIMESTAMPTZ DEFAULT NOW(),
    fecha_actualizacion TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para mejor rendimiento
CREATE INDEX IF NOT EXISTS idx_competidores_nombre ON competidores(nombre);
CREATE INDEX IF NOT EXISTS idx_competidores_activo ON competidores(activo);
CREATE INDEX IF NOT EXISTS idx_cotizaciones_competidor ON cotizaciones_competencia(competidor_id);
CREATE INDEX IF NOT EXISTS idx_cotizaciones_tipo ON cotizaciones_competencia(tipo_servicio);
CREATE INDEX IF NOT EXISTS idx_vehiculos_competidor ON vehiculos_competencia(competidor_id);
CREATE INDEX IF NOT EXISTS idx_vehiculos_activo ON vehiculos_competencia(activo);

-- Habilitar RLS (Row Level Security)
ALTER TABLE competidores ENABLE ROW LEVEL SECURITY;
ALTER TABLE cotizaciones_competencia ENABLE ROW LEVEL SECURITY;
ALTER TABLE vehiculos_competencia ENABLE ROW LEVEL SECURITY;

-- Políticas de acceso (permitir todo para service_role)
CREATE POLICY "Allow all for service role" ON competidores FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON cotizaciones_competencia FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON vehiculos_competencia FOR ALL USING (true);
