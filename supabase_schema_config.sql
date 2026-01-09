-- =============================================
-- TABLAS DE CONFIGURACIÓN PARA SUPABASE
-- Migración de SQLite local a Supabase (persistente)
-- Ejecutar en Supabase SQL Editor
-- =============================================

-- Tabla de notas
CREATE TABLE IF NOT EXISTS notas (
    id BIGSERIAL PRIMARY KEY,
    cod_presupuesto TEXT,
    cliente TEXT,
    fecha TIMESTAMPTZ DEFAULT NOW(),
    usuario TEXT,
    contenido TEXT,
    tipo TEXT
);
CREATE INDEX IF NOT EXISTS idx_notas_cliente ON notas(cliente);
CREATE INDEX IF NOT EXISTS idx_notas_presupuesto ON notas(cod_presupuesto);

-- Tabla de tipos de servicio
CREATE TABLE IF NOT EXISTS tipos_servicio (
    codigo TEXT PRIMARY KEY,
    descripcion TEXT,
    categoria TEXT
);

-- Tabla de configuración general
CREATE TABLE IF NOT EXISTS config_general (
    clave TEXT PRIMARY KEY,
    valor TEXT,
    descripcion TEXT,
    fecha_actualizacion TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de tramos de comisión
CREATE TABLE IF NOT EXISTS comisiones_tramos (
    id BIGSERIAL PRIMARY KEY,
    desde DECIMAL(12,2) NOT NULL,
    hasta DECIMAL(12,2) NOT NULL,
    porcentaje DECIMAL(5,2) NOT NULL,
    activo BOOLEAN DEFAULT true
);

-- Tabla de bonus por objetivos
CREATE TABLE IF NOT EXISTS bonus_objetivos (
    id BIGSERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL,
    condicion TEXT,
    valor_objetivo DECIMAL(12,2),
    importe_bonus DECIMAL(10,2),
    activo BOOLEAN DEFAULT true
);

-- Tabla de puntos por acciones
CREATE TABLE IF NOT EXISTS puntos_acciones (
    id BIGSERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    accion TEXT NOT NULL,
    puntos INTEGER NOT NULL,
    activo BOOLEAN DEFAULT true
);

-- Tabla de premios canjeables
CREATE TABLE IF NOT EXISTS puntos_premios (
    id BIGSERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    puntos_requeridos INTEGER NOT NULL,
    descripcion TEXT,
    activo BOOLEAN DEFAULT true
);

-- Tabla de premios especiales por presupuesto
CREATE TABLE IF NOT EXISTS premios_presupuesto (
    id BIGSERIAL PRIMARY KEY,
    cod_presupuesto TEXT NOT NULL,
    cliente TEXT NOT NULL,
    comercial TEXT NOT NULL,
    importe_presupuesto DECIMAL(12,2),
    premio_euros DECIMAL(10,2) NOT NULL,
    motivo TEXT,
    fecha_creacion TIMESTAMPTZ DEFAULT NOW(),
    conseguido BOOLEAN DEFAULT false,
    fecha_conseguido TIMESTAMPTZ,
    activo BOOLEAN DEFAULT true
);

-- Tabla de temporadas
CREATE TABLE IF NOT EXISTS temporadas (
    codigo TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    fecha_inicio TEXT NOT NULL,
    fecha_fin TEXT NOT NULL,
    multiplicador DECIMAL(4,2) DEFAULT 1.0,
    activo BOOLEAN DEFAULT true
);

-- Tabla de tipos de bus
CREATE TABLE IF NOT EXISTS tipos_bus (
    codigo TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    capacidad INTEGER,
    precio_base_hora DECIMAL(10,2),
    precio_base_km DECIMAL(10,2),
    coste_km DECIMAL(10,2) DEFAULT 0.85,
    coste_hora DECIMAL(10,2) DEFAULT 30.0,
    activo BOOLEAN DEFAULT true
);

-- Tabla de tipos de cliente
CREATE TABLE IF NOT EXISTS tipos_cliente (
    codigo TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    multiplicador DECIMAL(4,2) DEFAULT 1.0,
    activo BOOLEAN DEFAULT true
);

-- Tabla de tarifas por servicio
CREATE TABLE IF NOT EXISTS tarifas_servicio (
    id BIGSERIAL PRIMARY KEY,
    tipo_servicio TEXT NOT NULL,
    tipo_bus TEXT NOT NULL,
    precio_hora DECIMAL(10,2),
    precio_km DECIMAL(10,2),
    precio_minimo DECIMAL(10,2),
    notas TEXT,
    activo BOOLEAN DEFAULT true,
    UNIQUE(tipo_servicio, tipo_bus)
);

-- Tabla de tarifas personalizadas por cliente
CREATE TABLE IF NOT EXISTS tarifas_cliente (
    id BIGSERIAL PRIMARY KEY,
    cliente TEXT NOT NULL,
    tipo_bus TEXT DEFAULT '*',
    tipo_servicio TEXT DEFAULT '*',
    precio_hora DECIMAL(10,2),
    precio_km DECIMAL(10,2),
    notas TEXT,
    fecha_actualizacion TIMESTAMPTZ DEFAULT NOW(),
    activo BOOLEAN DEFAULT true,
    UNIQUE(cliente, tipo_bus, tipo_servicio)
);

-- Tabla de historial de incentivos
CREATE TABLE IF NOT EXISTS incentivos_historico (
    id BIGSERIAL PRIMARY KEY,
    comercial TEXT NOT NULL,
    periodo TEXT NOT NULL,
    importe_facturado DECIMAL(12,2),
    comision_base DECIMAL(10,2),
    bonus_total DECIMAL(10,2),
    puntos_totales INTEGER,
    detalles JSONB,
    fecha_calculo TIMESTAMPTZ DEFAULT NOW()
);

-- Habilitar RLS
ALTER TABLE notas ENABLE ROW LEVEL SECURITY;
ALTER TABLE tipos_servicio ENABLE ROW LEVEL SECURITY;
ALTER TABLE config_general ENABLE ROW LEVEL SECURITY;
ALTER TABLE comisiones_tramos ENABLE ROW LEVEL SECURITY;
ALTER TABLE bonus_objetivos ENABLE ROW LEVEL SECURITY;
ALTER TABLE puntos_acciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE puntos_premios ENABLE ROW LEVEL SECURITY;
ALTER TABLE premios_presupuesto ENABLE ROW LEVEL SECURITY;
ALTER TABLE temporadas ENABLE ROW LEVEL SECURITY;
ALTER TABLE tipos_bus ENABLE ROW LEVEL SECURITY;
ALTER TABLE tipos_cliente ENABLE ROW LEVEL SECURITY;
ALTER TABLE tarifas_servicio ENABLE ROW LEVEL SECURITY;
ALTER TABLE tarifas_cliente ENABLE ROW LEVEL SECURITY;
ALTER TABLE incentivos_historico ENABLE ROW LEVEL SECURITY;

-- Políticas de acceso (permitir todo para service_role)
CREATE POLICY "Allow all for service role" ON notas FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON tipos_servicio FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON config_general FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON comisiones_tramos FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON bonus_objetivos FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON puntos_acciones FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON puntos_premios FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON premios_presupuesto FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON temporadas FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON tipos_bus FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON tipos_cliente FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON tarifas_servicio FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON tarifas_cliente FOR ALL USING (true);
CREATE POLICY "Allow all for service role" ON incentivos_historico FOR ALL USING (true);
