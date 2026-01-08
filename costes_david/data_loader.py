"""
Módulo de Carga de Datos - Análisis de Costes DAVID
Importación de datos desde Excel a la base de datos
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import database as db


def clean_matricula(matricula):
    """Limpia y normaliza una matrícula."""
    if pd.isna(matricula) or matricula is None:
        return None
    return str(matricula).strip().replace("-", "").replace(" ", "").upper()


def safe_float(value, default=0):
    """Convierte un valor a float de forma segura."""
    if pd.isna(value) or value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    """Convierte un valor a int de forma segura."""
    if pd.isna(value) or value is None:
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def safe_date(value):
    """Convierte un valor a fecha string de forma segura."""
    if pd.isna(value) or value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, str):
        return value[:10] if len(value) >= 10 else value
    try:
        return pd.to_datetime(value).strftime("%Y-%m-%d")
    except:
        return None


class ExcelDataLoader:
    """Clase para cargar datos desde Excel."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.xl = pd.ExcelFile(file_path)
        self.año = None
        self.ejercicio_id = None

    def importar_todo(self, año: int) -> dict:
        """Importa todos los datos del Excel para un año específico."""
        self.año = año

        # Crear ejercicio
        self.ejercicio_id = db.crear_ejercicio(año, f"Ejercicio {año}")

        resultados = {
            'vehiculos': 0,
            'adquisicion': 0,
            'financiacion': 0,
            'mantenimiento': 0,
            'seguros': 0,
            'fiscales': 0,
            'combustible': 0,
            'neumaticos': 0,
            'urea': 0,
            'personal': 0,
            'indirectos': 0,
            'pyg': 0,
            'errores': []
        }

        try:
            # Importar vehículos base
            resultados['vehiculos'] = self._importar_vehiculos()
        except Exception as e:
            resultados['errores'].append(f"Error en vehículos: {str(e)}")

        try:
            # Importar datos de autobuses (km por año)
            self._importar_autobuses()
        except Exception as e:
            resultados['errores'].append(f"Error en autobuses: {str(e)}")

        try:
            # Importar adquisición
            resultados['adquisicion'] = self._importar_adquisicion()
        except Exception as e:
            resultados['errores'].append(f"Error en adquisición: {str(e)}")

        try:
            # Importar financiación
            resultados['financiacion'] = self._importar_financiacion()
        except Exception as e:
            resultados['errores'].append(f"Error en financiación: {str(e)}")

        try:
            # Importar mantenimiento
            resultados['mantenimiento'] = self._importar_mantenimiento()
        except Exception as e:
            resultados['errores'].append(f"Error en mantenimiento: {str(e)}")

        try:
            # Importar seguros
            resultados['seguros'] = self._importar_seguros()
        except Exception as e:
            resultados['errores'].append(f"Error en seguros: {str(e)}")

        try:
            # Importar fiscales
            resultados['fiscales'] = self._importar_fiscales()
        except Exception as e:
            resultados['errores'].append(f"Error en fiscales: {str(e)}")

        try:
            # Importar combustible
            resultados['combustible'] = self._importar_combustible()
        except Exception as e:
            resultados['errores'].append(f"Error en combustible: {str(e)}")

        try:
            # Importar neumáticos
            resultados['neumaticos'] = self._importar_neumaticos()
        except Exception as e:
            resultados['errores'].append(f"Error en neumáticos: {str(e)}")

        try:
            # Importar urea
            resultados['urea'] = self._importar_urea()
        except Exception as e:
            resultados['errores'].append(f"Error en urea: {str(e)}")

        try:
            # Importar personal
            resultados['personal'] = self._importar_personal()
        except Exception as e:
            resultados['errores'].append(f"Error en personal: {str(e)}")

        try:
            # Importar indirectos
            resultados['indirectos'] = self._importar_indirectos()
        except Exception as e:
            resultados['errores'].append(f"Error en indirectos: {str(e)}")

        try:
            # Importar P&G
            resultados['pyg'] = self._importar_pyg()
        except Exception as e:
            resultados['errores'].append(f"Error en P&G: {str(e)}")

        # Calcular resúmenes
        self._calcular_resumenes()

        return resultados

    def _obtener_vehiculo_id(self, matricula: str) -> int:
        """Obtiene el ID de un vehículo por matrícula."""
        matricula = clean_matricula(matricula)
        if not matricula:
            return None

        vehiculos = db.obtener_vehiculos(activos_solo=False)
        for v in vehiculos:
            if clean_matricula(v['matricula']) == matricula:
                return v['id']
        return None

    def _importar_vehiculos(self) -> int:
        """Importa vehículos desde la hoja Vehículos."""
        df = pd.read_excel(self.file_path, sheet_name='Vehículos', header=5)
        df.columns = df.columns.str.strip()

        count = 0
        for _, row in df.iterrows():
            matricula = clean_matricula(row.get('Matrícula'))
            if not matricula:
                continue

            plazas = safe_int(row.get('Plazas', 0))
            fecha_mat = safe_date(row.get('F.Matricula'))

            # Determinar tipo basado en plazas
            if plazas <= 20:
                tipo = 4  # Mini
            elif plazas <= 35:
                tipo = 3  # Midi
            elif plazas <= 55:
                tipo = 2  # Estándar
            else:
                tipo = 1  # Gran Turismo

            db.crear_vehiculo(matricula, plazas, tipo, fecha_mat)
            count += 1

        return count

    def _importar_autobuses(self) -> int:
        """Importa datos de autobuses (km, horas) desde la hoja (0) Autobuses."""
        df = pd.read_excel(self.file_path, sheet_name='(0) Autobuses', header=5)
        df.columns = df.columns.str.strip()

        count = 0
        for _, row in df.iterrows():
            matricula = clean_matricula(row.get('Matrícula'))
            vehiculo_id = self._obtener_vehiculo_id(matricula)
            if not vehiculo_id:
                continue

            datos = {
                'km_anual': safe_int(row.get('Kilómetros reales', 0)),
                'horas_servicio': safe_float(row.get('Horas anuales \n(en servicio)', 0)),
                'fecha_inicio': safe_date(row.get('Fecha de inicio')),
                'fecha_fin': safe_date(row.get('Fecha de fin')),
                'porcentaje_año': safe_float(row.get('% en año incompleto', 1.0))
            }

            db.guardar_vehiculo_año(vehiculo_id, self.ejercicio_id, **datos)
            count += 1

        return count

    def _importar_adquisicion(self) -> int:
        """Importa datos de adquisición desde la hoja (1.1) Adquisición."""
        df = pd.read_excel(self.file_path, sheet_name='(1.1) Adquisición', header=5)
        df.columns = df.columns.str.strip()

        count = 0
        for _, row in df.iterrows():
            matricula = clean_matricula(row.get('Matrícula'))
            vehiculo_id = self._obtener_vehiculo_id(matricula)
            if not vehiculo_id:
                continue

            datos = {
                'valor_compra': safe_float(row.get('Valor de Compra', 0)),
                'valor_residual': safe_float(row.get('Valor Residual', 0)),
                'vida_util': safe_float(row.get('Vida Útil', 10)),
                'años_uso': safe_float(row.get('Años de uso', 0)),
                'coste_anual': safe_float(row.get('Total AÑO calculado', row.get('Total año', 0))),
                'fecha_compra': safe_date(row.get('F.Compra')),
                'fecha_venta': safe_date(row.get('Fecha DE VENTA')),
                'valor_venta': safe_float(row.get('Valor Venta (residual real)'))
            }

            db.guardar_coste('costes_adquisicion', vehiculo_id, self.ejercicio_id, **datos)
            count += 1

        return count

    def _importar_financiacion(self) -> int:
        """Importa datos de financiación desde la hoja (1.2) Financiación."""
        df = pd.read_excel(self.file_path, sheet_name='(1.2) Financiación', header=5)
        df.columns = df.columns.str.strip()

        count = 0
        for _, row in df.iterrows():
            matricula = clean_matricula(row.get('Matrícula'))
            vehiculo_id = self._obtener_vehiculo_id(matricula)
            if not vehiculo_id:
                continue

            financiado = 1 if safe_float(row.get('Financiación', 0)) > 0 else 0

            datos = {
                'financiado': financiado,
                'importe_financiado': safe_float(row.get('Valor de Compra', 0)) if financiado else 0,
                'plazo_meses': safe_int(row.get('Plazo', 60)),
                'tae': safe_float(row.get('TAE', 0)),
                'cuota_anual': safe_float(row.get('Cuota \nAnual', 0)),
                'intereses': safe_float(row.get('Intereses (medios)', 0)),
                'coste_anual': safe_float(row.get('Total año', 0))
            }

            db.guardar_coste('costes_financiacion', vehiculo_id, self.ejercicio_id, **datos)
            count += 1

        return count

    def _importar_mantenimiento(self) -> int:
        """Importa datos de mantenimiento desde la hoja (1.3) Mantenimiento."""
        df = pd.read_excel(self.file_path, sheet_name='(1.3) Mantenimiento', header=5)
        df.columns = df.columns.str.strip()

        count = 0
        for _, row in df.iterrows():
            matricula = clean_matricula(row.get('Matrícula'))
            vehiculo_id = self._obtener_vehiculo_id(matricula)
            if not vehiculo_id:
                continue

            datos = {
                'ratio_tipo': safe_float(row.get('Ratio por Tamaño \n(calculado)', 0)),
                'coste_anual': safe_float(row.get('Total año', 0))
            }

            db.guardar_coste('costes_mantenimiento', vehiculo_id, self.ejercicio_id, **datos)
            count += 1

        return count

    def _importar_seguros(self) -> int:
        """Importa datos de seguros desde la hoja (1.4) Seguros."""
        try:
            df = pd.read_excel(self.file_path, sheet_name='(1.4) Seguros', header=5)
            df.columns = df.columns.str.strip()
        except:
            # Intentar obtener de COSTE DIR. + IND.
            df = pd.read_excel(self.file_path, sheet_name='COSTE DIR. + IND.', header=5)
            df.columns = df.columns.str.strip()

        count = 0
        for _, row in df.iterrows():
            matricula = clean_matricula(row.get('MATRÍCULA', row.get('Matrícula')))
            vehiculo_id = self._obtener_vehiculo_id(matricula)
            if not vehiculo_id:
                continue

            # Buscar columnas de seguros
            prima_1 = safe_float(row.get('1º Semestre', 0))
            prima_2 = safe_float(row.get('2º Semestre', 0))
            coste = safe_float(row.get('Seguros', prima_1 + prima_2))

            datos = {
                'aseguradora': str(row.get('Aseguradora', 'PLUS ULTRA')) if pd.notna(row.get('Aseguradora')) else 'PLUS ULTRA',
                'num_poliza': str(row.get('Flota Nº Poliza', '')) if pd.notna(row.get('Flota Nº Poliza')) else '',
                'prima_1_semestre': prima_1,
                'prima_2_semestre': prima_2,
                'coste_anual': coste
            }

            db.guardar_coste('costes_seguros', vehiculo_id, self.ejercicio_id, **datos)
            count += 1

        return count

    def _importar_fiscales(self) -> int:
        """Importa datos fiscales desde la hoja (1.5) Fiscales o COSTE DIR. + IND."""
        try:
            df = pd.read_excel(self.file_path, sheet_name='(1.5) Fiscales', header=5)
            df.columns = df.columns.str.strip()
        except:
            df = pd.read_excel(self.file_path, sheet_name='COSTE DIR. + IND.', header=5)
            df.columns = df.columns.str.strip()

        count = 0
        for _, row in df.iterrows():
            matricula = clean_matricula(row.get('MATRÍCULA', row.get('Matrícula')))
            vehiculo_id = self._obtener_vehiculo_id(matricula)
            if not vehiculo_id:
                continue

            datos = {
                'sovi': safe_float(row.get('Sovi', 0)),
                'itv_1': safe_float(row.get('ITV 1', 0)),
                'itv_escolar_1': safe_float(row.get('ITV ESCOLAR', 0)),
                'itv_2': safe_float(row.get('ITV 2', 0)),
                'itv_escolar_2': safe_float(row.get('ITV ESCOLAR 2', 0)),
                'revision_tacografo': safe_float(row.get('REVISIÓN TACÓGRAFO', 0)),
                'ivtm': safe_float(row.get('IVTM', 0)),
                'iae': safe_float(row.get('IAE', 0)),
                'dris': safe_float(row.get('DRIS', 0)),
                'visado': safe_float(row.get('VISADO', 0)),
                'licencia_com': safe_float(row.get('LICENCIA COM', 0)),
                'coste_anual': safe_float(row.get('Fiscales', 0))
            }

            db.guardar_coste('costes_fiscales', vehiculo_id, self.ejercicio_id, **datos)
            count += 1

        return count

    def _importar_combustible(self) -> int:
        """Importa datos de combustible desde la hoja (2.1) Combustible."""
        df = pd.read_excel(self.file_path, sheet_name='(2.1) Combustible', header=5)
        df.columns = df.columns.str.strip()

        count = 0
        for _, row in df.iterrows():
            matricula = clean_matricula(row.get('Matrícula'))
            vehiculo_id = self._obtener_vehiculo_id(matricula)
            if not vehiculo_id:
                continue

            datos = {
                'consumo_ciudad': safe_float(row.get('Consumo ciudad', 0)),
                'consumo_carretera': safe_float(row.get('Consumo carretera', 0)),
                'consumo_mixto': safe_float(row.get('Consumo mixto', 0)),
                'precio_litro': 0.974,  # Precio por defecto
                'coste_km': safe_float(row.get('Precio Km', 0)),
                'coste_anual': safe_float(row.get('Total año', 0))
            }

            db.guardar_coste('costes_combustible', vehiculo_id, self.ejercicio_id, **datos)
            count += 1

        return count

    def _importar_neumaticos(self) -> int:
        """Importa datos de neumáticos desde la hoja (2.2) Neumaticos."""
        try:
            df = pd.read_excel(self.file_path, sheet_name='(2.2) Neumaticos', header=5)
            df.columns = df.columns.str.strip()
        except:
            return 0

        count = 0
        for _, row in df.iterrows():
            matricula = clean_matricula(row.get('Matrícula'))
            vehiculo_id = self._obtener_vehiculo_id(matricula)
            if not vehiculo_id:
                continue

            datos = {
                'coste_unitario': safe_float(row.get('Coste Unitario', 0)),
                'vida_util_km': safe_int(row.get('Vida Útil (km)', 0)),
                'coste_km': safe_float(row.get('Coste por km', 0)),
                'coste_anual': safe_float(row.get('Total año', 0))
            }

            db.guardar_coste('costes_neumaticos', vehiculo_id, self.ejercicio_id, **datos)
            count += 1

        return count

    def _importar_urea(self) -> int:
        """Importa datos de urea/adblue desde la hoja (2.3) Urea."""
        try:
            df = pd.read_excel(self.file_path, sheet_name='(2.3) Urea', header=5)
            df.columns = df.columns.str.strip()
        except:
            return 0

        count = 0
        for _, row in df.iterrows():
            matricula = clean_matricula(row.get('Matrícula'))
            vehiculo_id = self._obtener_vehiculo_id(matricula)
            if not vehiculo_id:
                continue

            datos = {
                'consumo_por_km': safe_float(row.get('Consumo por km', 0)),
                'precio_litro': safe_float(row.get('Precio Litro', 0)),
                'coste_anual': safe_float(row.get('Total año', 514))  # Valor por defecto del Excel
            }

            db.guardar_coste('costes_urea', vehiculo_id, self.ejercicio_id, **datos)
            count += 1

        return count

    def _importar_personal(self) -> int:
        """Importa datos de personal desde la hoja (3) Personal."""
        df = pd.read_excel(self.file_path, sheet_name='(3) Personal', header=5)
        df.columns = df.columns.str.strip()

        # Buscar la fila de Total Conductores
        for _, row in df.iterrows():
            if 'Total Conductores' in str(row.values):
                datos = {
                    'coste_total_conductores': safe_float(row.get('Coste Total de Conductores', 0)),
                    'total_horas': safe_float(row.get('Total horas', 0)),
                    'absentismo': safe_float(row.get('Absentismo', 0)),
                    'horas_servicio': safe_float(row.get('Horas en Servicio', 0)),
                    'horas_productivas': safe_float(row.get('Horas Productivas', 0)),
                    'salario_hora_servicio': safe_float(row.get('Salario Efectivo\n(por hora de servicio)', 0))
                }
                db.guardar_personal(self.ejercicio_id, **datos)
                return 1

        return 0

    def _importar_indirectos(self) -> int:
        """Importa datos de indirectos desde la hoja (4) Indirectos."""
        df = pd.read_excel(self.file_path, sheet_name='(4) Indirectos', header=5)
        df.columns = df.columns.str.strip()

        # Calcular totales con manejo de errores
        total_km = 0
        total_coste = 0

        if 'km/año' in df.columns:
            try:
                total_km = pd.to_numeric(df['km/año'], errors='coerce').sum()
            except:
                total_km = 0

        if 'Total año' in df.columns:
            try:
                total_coste = pd.to_numeric(df['Total año'], errors='coerce').sum()
            except:
                total_coste = 0

        datos = {
            'porcentaje_estructura': 0.137,  # Valor del Excel
            'total_horas_estructura': 1792,  # Valor del Excel
            'total_km_flota': safe_int(total_km),
            'coste_total': safe_float(total_coste)
        }

        db.guardar_indirectos(self.ejercicio_id, **datos)
        return 1

    def _importar_pyg(self) -> int:
        """Importa datos de P&G desde la hoja (0) P&G."""
        df = pd.read_excel(self.file_path, sheet_name='(0) P&G', header=None)

        registros = []
        categoria_actual = None

        for idx, row in df.iterrows():
            if idx < 6:  # Saltar cabeceras
                continue

            cuenta = str(row.iloc[1]) if pd.notna(row.iloc[1]) else None
            if not cuenta or cuenta == 'nan':
                continue

            # Detectar si es categoría principal (empieza con número de 3 dígitos)
            if len(cuenta) >= 3 and cuenta[:3].isdigit() and ' ' in cuenta:
                # Es una cuenta principal
                descripcion = cuenta
                cuenta_num = cuenta.split()[0]

                # Determinar categoría
                if cuenta_num.startswith('6'):
                    categoria_actual = 'Gastos'
                elif cuenta_num.startswith('7'):
                    categoria_actual = 'Ingresos'
                else:
                    categoria_actual = 'Otros'

                registro = {
                    'cuenta': cuenta_num,
                    'descripcion': descripcion,
                    'importe_no_ajustado': safe_float(row.iloc[6] if len(row) > 6 else 0),
                    'importe_ajustado': safe_float(row.iloc[7] if len(row) > 7 else 0),
                    'ponderado_directo': safe_float(row.iloc[12] if len(row) > 12 else 0),
                    'ponderado_indirecto': safe_float(row.iloc[13] if len(row) > 13 else 0),
                    'es_coste_directo': 1 if safe_float(row.iloc[12] if len(row) > 12 else 0) > 0 else 0,
                    'es_coste_indirecto': 1 if safe_float(row.iloc[13] if len(row) > 13 else 0) > 0 else 0,
                    'categoria': categoria_actual
                }
                registros.append(registro)

        if registros:
            return db.guardar_pyg(self.ejercicio_id, registros)
        return 0

    def _calcular_resumenes(self):
        """Calcula los resúmenes de todos los vehículos."""
        vehiculos = db.obtener_vehiculos()
        for vehiculo in vehiculos:
            db.calcular_resumen_vehiculo(vehiculo['id'], self.ejercicio_id)


def importar_excel(file_path: str, año: int) -> dict:
    """Función de conveniencia para importar un Excel."""
    loader = ExcelDataLoader(file_path)
    return loader.importar_todo(año)


def importar_vehiculos_completo(file_path: str, años: list = None) -> dict:
    """
    Importa vehículos con todos los campos del Excel Vehiculos.xlsx.
    Asigna vehículos a los años correspondientes basándose en fecha_matriculacion y fecha_baja.

    Args:
        file_path: Ruta al archivo Vehiculos.xlsx
        años: Lista de años para los que crear registros (ej: [2024, 2025])

    Returns:
        dict con resultados de importación
    """
    if años is None:
        años = [2024, 2025]

    df = pd.read_excel(file_path)

    resultados = {
        'vehiculos_creados': 0,
        'vehiculos_actualizados': 0,
        'asignaciones_año': {año: 0 for año in años},
        'errores': []
    }

    # Mapeo de columnas Excel a campos de base de datos
    mapeo_columnas = {
        'Código de vehículo': 'codigo_vehiculo',
        'Tipo': 'tipo_codigo',
        'Matrícula': 'matricula',
        'Marca': 'marca',
        'Modelo': 'modelo',
        'Plazas': 'plazas',
        'Código de conductor': 'codigo_conductor',
        'Conductor': 'conductor',
        'Vehículo bloqueado': 'vehiculo_bloqueado',
        'Estado': 'estado',
        'Fecha baja': 'fecha_baja',
        'Fecha final ITV': 'fecha_final_itv',
        'Fecha final tacógrafo': 'fecha_final_tacografo',
        'Bastidor': 'bastidor',
        'Núm. Obra': 'num_obra',
        'Longitud': 'longitud',
        'Altura': 'altura',
        'Vehículo tipo': 'vehiculo_tipo',
        'Fecha matriculación': 'fecha_matriculacion',
        'Primera matriculación': 'primera_matriculacion',
        'Código Empresa': 'codigo_empresa',
        'Empresa': 'empresa',
        'Inhabilitado para tráfico': 'inhabilitado_trafico',
        'Kilómetros': 'kilometros',
        'Caducidad extintores': 'caducidad_extintores',
        'Caducidad Escolar': 'caducidad_escolar'
    }

    for _, row in df.iterrows():
        try:
            matricula = clean_matricula(row.get('Matrícula'))
            if not matricula:
                continue

            # Construir datos del vehículo
            plazas = safe_int(row.get('Plazas', 0))

            # Determinar tipo numérico basado en plazas
            if plazas <= 20:
                tipo = 4  # Mini
            elif plazas <= 35:
                tipo = 3  # Midi
            elif plazas <= 55:
                tipo = 2  # Estándar
            else:
                tipo = 1  # Gran Turismo

            # Construir kwargs con todos los campos opcionales
            kwargs = {}

            for col_excel, campo_db in mapeo_columnas.items():
                if col_excel in ['Matrícula', 'Plazas', 'Tipo']:
                    continue

                valor = row.get(col_excel)

                if campo_db in ['fecha_baja', 'fecha_final_itv', 'fecha_final_tacografo',
                               'fecha_matriculacion', 'primera_matriculacion',
                               'caducidad_extintores', 'caducidad_escolar']:
                    kwargs[campo_db] = safe_date(valor)
                elif campo_db in ['codigo_vehiculo', 'codigo_conductor', 'codigo_empresa',
                                  'kilometros']:
                    kwargs[campo_db] = safe_int(valor)
                elif campo_db in ['longitud', 'altura']:
                    kwargs[campo_db] = safe_float(valor)
                elif campo_db in ['vehiculo_bloqueado', 'inhabilitado_trafico']:
                    # Convertir 'No'/'Sí' a 0/1
                    if pd.isna(valor):
                        kwargs[campo_db] = 0
                    elif isinstance(valor, str):
                        kwargs[campo_db] = 1 if valor.lower() in ['sí', 'si', 'yes', 's'] else 0
                    else:
                        kwargs[campo_db] = safe_int(valor)
                else:
                    if pd.notna(valor):
                        kwargs[campo_db] = str(valor) if not pd.isna(valor) else None

            # Crear o actualizar vehículo
            vehiculo_id = db.crear_vehiculo(matricula, plazas, tipo, **kwargs)

            if vehiculo_id:
                resultados['vehiculos_creados'] += 1

                # Asignar a años según fechas
                fecha_mat = kwargs.get('fecha_matriculacion')
                fecha_baja = kwargs.get('fecha_baja')

                for año in años:
                    # El vehículo estuvo activo en el año si:
                    # - Fue matriculado antes o durante ese año
                    # - Y no fue dado de baja antes de ese año

                    inicio_año = f"{año}-01-01"
                    fin_año = f"{año}-12-31"

                    # Verificar si el vehículo estaba activo en este año
                    activo_en_año = True

                    if fecha_mat:
                        # Si fue matriculado después del fin de año, no estaba activo
                        if fecha_mat > fin_año:
                            activo_en_año = False

                    if fecha_baja and activo_en_año:
                        # Si fue dado de baja antes del inicio del año, no estaba activo
                        if fecha_baja < inicio_año:
                            activo_en_año = False

                    if activo_en_año:
                        # Crear ejercicio si no existe
                        ejercicio_id = db.crear_ejercicio(año, f"Ejercicio {año}")

                        # Calcular porcentaje del año
                        porcentaje = 1.0
                        fecha_inicio_real = inicio_año
                        fecha_fin_real = fin_año

                        if fecha_mat and fecha_mat > inicio_año:
                            fecha_inicio_real = fecha_mat
                            # Calcular días
                            from datetime import datetime
                            d_inicio = datetime.strptime(fecha_mat, "%Y-%m-%d")
                            d_fin = datetime.strptime(fin_año, "%Y-%m-%d")
                            dias = (d_fin - d_inicio).days + 1
                            porcentaje = min(dias / 365, 1.0)

                        if fecha_baja and fecha_baja < fin_año:
                            fecha_fin_real = fecha_baja
                            from datetime import datetime
                            d_inicio = datetime.strptime(fecha_inicio_real, "%Y-%m-%d")
                            d_fin = datetime.strptime(fecha_baja, "%Y-%m-%d")
                            dias = (d_fin - d_inicio).days + 1
                            porcentaje = min(dias / 365, 1.0)

                        # Guardar datos del vehículo para el año
                        db.guardar_vehiculo_año(
                            vehiculo_id,
                            ejercicio_id,
                            km_anual=safe_int(kwargs.get('kilometros', 0)),
                            fecha_inicio=fecha_inicio_real,
                            fecha_fin=fecha_fin_real,
                            porcentaje_año=porcentaje
                        )

                        resultados['asignaciones_año'][año] += 1

        except Exception as e:
            resultados['errores'].append(f"Error en {matricula}: {str(e)}")

    return resultados


def vehiculo_activo_en_año(fecha_matriculacion: str, fecha_baja: str, año: int) -> bool:
    """
    Determina si un vehículo estaba activo en un año específico.

    Args:
        fecha_matriculacion: Fecha de matriculación (YYYY-MM-DD)
        fecha_baja: Fecha de baja (YYYY-MM-DD) o None si aún activo
        año: Año a verificar

    Returns:
        True si el vehículo estaba activo en ese año
    """
    inicio_año = f"{año}-01-01"
    fin_año = f"{año}-12-31"

    # Si no tiene fecha de matriculación, asumir que estaba activo
    if not fecha_matriculacion:
        if fecha_baja and fecha_baja < inicio_año:
            return False
        return True

    # Si fue matriculado después del fin de año, no estaba activo
    if fecha_matriculacion > fin_año:
        return False

    # Si fue dado de baja antes del inicio del año, no estaba activo
    if fecha_baja and fecha_baja < inicio_año:
        return False

    return True


def obtener_datos_completos(ejercicio_id: int) -> dict:
    """Obtiene todos los datos de un ejercicio."""
    datos = {
        'vehiculos': db.obtener_vehiculos(),
        'personal': db.obtener_personal(ejercicio_id),
        'pyg': db.obtener_pyg(ejercicio_id),
        'pyg_resumen': db.obtener_pyg_resumen(ejercicio_id),
        'resumen_flota': db.obtener_resumen_flota(ejercicio_id)
    }

    # Obtener costes por vehículo
    for vehiculo in datos['vehiculos']:
        vid = vehiculo['id']
        vehiculo['datos_año'] = db.obtener_datos_vehiculo_año(vid, ejercicio_id)
        vehiculo['adquisicion'] = db.obtener_costes('costes_adquisicion', ejercicio_id, vid)
        vehiculo['financiacion'] = db.obtener_costes('costes_financiacion', ejercicio_id, vid)
        vehiculo['mantenimiento'] = db.obtener_costes('costes_mantenimiento', ejercicio_id, vid)
        vehiculo['seguros'] = db.obtener_costes('costes_seguros', ejercicio_id, vid)
        vehiculo['fiscales'] = db.obtener_costes('costes_fiscales', ejercicio_id, vid)
        vehiculo['combustible'] = db.obtener_costes('costes_combustible', ejercicio_id, vid)
        vehiculo['neumaticos'] = db.obtener_costes('costes_neumaticos', ejercicio_id, vid)
        vehiculo['urea'] = db.obtener_costes('costes_urea', ejercicio_id, vid)

    return datos
