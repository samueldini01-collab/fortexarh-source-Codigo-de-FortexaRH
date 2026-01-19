"""
TSS (Tesorería de la Seguridad Social) File Generator
Generates Excel files in official TSS format for Dominican Republic
- Archivo de Autodeterminación (v5.3)
- Archivo de Novedades (v5.1)
"""
import xlwt
from io import BytesIO
from datetime import datetime
from typing import List, Dict, Any

# TSS Constants
TSS_AUTODETER_VERSION = "5.3"
TSS_NOVEDADES_VERSION = "5.1"

# Tipo de Archivo codes
TIPO_ARCHIVO = {
    "AM": "Archivo Mensual",
    "AR": "Archivo Rectificativo"
}

# Tipo de Documento codes
TIPO_DOCUMENTO = {
    "C": "Cédula",
    "P": "Pasaporte", 
    "N": "NSS"
}

# Tipo de Ingreso codes
TIPO_INGRESO = {
    "Normal": "Normal",
    "Ocasional": "Trabajador ocasional (no fijo)",
    "Parcial": "Asalariado por hora o labora tiempo parcial",
    "Incompleto": "No laboró mes completo por razones varias",
    "Prorrateado": "Salario prorrateado semanal/bisemanal",
    "Pensionado": "Pensionado antes de la Ley 87-01",
    "Exento": "Exento por Ley de pago al SDSS",
    "Sectorizado": "Trabajador con salario sectorizado"
}

# Tipo de Novedad codes
TIPO_NOVEDAD = {
    "IN": "Ingreso",
    "SA": "Salida",
    "VC": "Vacaciones",
    "LV": "Licencia de Vacaciones",
    "LM": "Licencia de Maternidad",
    "LD": "Licencia por Duelo",
    "AD": "Ajuste de Datos"
}

# Tasas de Riesgo Laboral
TASAS_RIESGO_LABORAL = {
    "I": 0.011,   # Bajo riesgo
    "II": 0.0115, # Riesgo medio bajo
    "III": 0.012, # Riesgo medio
    "IV": 0.013   # Riesgo alto
}


def create_tss_autodeterminacion_excel(
    rnc_cedula: str,
    periodo: str,  # MMAAAA
    employees: List[Dict[str, Any]],
    tipo_archivo: str = "AM"
) -> BytesIO:
    """
    Genera archivo Excel de Autodeterminación TSS v5.3
    
    Columnas requeridas:
    - Clave Nómina, Tipo Doc, Número Documento
    - Nombres, 1er Apellido, 2do Apellido, Sexo, Fecha Nacimiento
    - Salario Cotizable SDSS, Aporte Voluntario
    - Salario ISR, Tipo Ingreso
    - Otras Remuneraciones, RNC/Cédula Agente Ret, Remuneración Otros Agentes
    - Saldo a favor del período, Regalía Pascual
    - Preaviso/Cesantía/Viático/Indemnizaciones, Retención Pensión Alimenticia
    - Salario INFOTEP
    """
    workbook = xlwt.Workbook(encoding='utf-8')
    
    # Sheet 1: Plantilla de Autodeterminación
    ws = workbook.add_sheet('Plantilla de Autodeterminación')
    
    # Styles
    header_style = xlwt.easyxf('font: bold on; align: horiz center; borders: left thin, right thin, top thin, bottom thin')
    subheader_style = xlwt.easyxf('font: bold on; align: horiz center; pattern: pattern solid, fore_colour light_green')
    data_style = xlwt.easyxf('borders: left thin, right thin, top thin, bottom thin')
    number_style = xlwt.easyxf('borders: left thin, right thin, top thin, bottom thin', num_format_str='#,##0.00')
    
    # Title row
    ws.write_merge(4, 4, 0, 5, f'Plantilla de Archivo AutoDeterminación', header_style)
    
    # Metadata
    ws.write(5, 0, 'Tipo de Archivo:', data_style)
    ws.write(5, 4, tipo_archivo, data_style)
    ws.write(5, 5, f'Ver. {TSS_AUTODETER_VERSION}', data_style)
    
    ws.write(6, 0, 'RNC o Cédula:', data_style)
    ws.write(6, 4, rnc_cedula, data_style)
    
    ws.write(7, 0, 'Período:', data_style)
    ws.write(7, 4, periodo, data_style)
    ws.write(7, 5, '<-- MMAAAA', data_style)
    
    ws.write(9, 2, '# de Empleados:', data_style)
    ws.write(9, 4, len(employees), data_style)
    
    # Section headers (row 10)
    ws.write_merge(10, 10, 1, 8, 'TRABAJADORES', subheader_style)
    ws.write_merge(10, 10, 9, 12, 'SDSS', subheader_style)
    ws.write_merge(10, 10, 13, 19, 'DGII', subheader_style)
    ws.write(10, 20, 'INFOTEP', subheader_style)
    
    # Column headers (row 11-12)
    headers_row1 = [
        '', 'Clave', 'Tipo', 'Número', 'Nombres', '1er. Apellido', '2do. Apellido', 'Sexo', 'Fecha',
        'Salario', 'Aporte', 'Salario', 'Tipo', 'Otras', 'RNC/Céd.', 'Remuneración',
        'Saldo a favor', 'Regalía Pascual', 'Preaviso, Cesantía, Viático e Indemnizaciones',
        'Retención Pensión', 'Salario'
    ]
    headers_row2 = [
        '', 'Nómina', 'Doc.', 'Documento', '', '', '', '', 'Nacimiento',
        'Cotizable', 'Voluntario', 'ISR', 'Ingreso', 'Remuneraciones', 'Agente Ret', 'Otros Agentes',
        'del período', '(Saldo 13)', 'por Accidentes Laborales', 'Alimenticia', 'INFOTEP'
    ]
    
    for col, (h1, h2) in enumerate(zip(headers_row1, headers_row2)):
        ws.write(11, col, h1, header_style)
        ws.write(12, col, h2, header_style)
    
    # Data rows starting at row 13
    for row_idx, emp in enumerate(employees, start=13):
        ws.write(row_idx, 1, emp.get('clave_nomina', ''), data_style)
        ws.write(row_idx, 2, emp.get('tipo_doc', 'C'), data_style)
        ws.write(row_idx, 3, emp.get('numero_doc', ''), data_style)
        ws.write(row_idx, 4, emp.get('nombres', ''), data_style)
        ws.write(row_idx, 5, emp.get('primer_apellido', ''), data_style)
        ws.write(row_idx, 6, emp.get('segundo_apellido', ''), data_style)
        ws.write(row_idx, 7, emp.get('sexo', 'M'), data_style)
        ws.write(row_idx, 8, emp.get('fecha_nacimiento', ''), data_style)
        ws.write(row_idx, 9, emp.get('salario_cotizable_sdss', 0), number_style)
        ws.write(row_idx, 10, emp.get('aporte_voluntario', 0), number_style)
        ws.write(row_idx, 11, emp.get('salario_isr', 0), number_style)
        ws.write(row_idx, 12, emp.get('tipo_ingreso', 'Normal'), data_style)
        ws.write(row_idx, 13, emp.get('otras_remuneraciones', 0), number_style)
        ws.write(row_idx, 14, emp.get('rnc_agente_ret', ''), data_style)
        ws.write(row_idx, 15, emp.get('remuneracion_otros_agentes', 0), number_style)
        ws.write(row_idx, 16, emp.get('saldo_favor', 0), number_style)
        ws.write(row_idx, 17, emp.get('regalia_pascual', 0), number_style)
        ws.write(row_idx, 18, emp.get('preaviso_cesantia', 0), number_style)
        ws.write(row_idx, 19, emp.get('retencion_pension', 0), number_style)
        ws.write(row_idx, 20, emp.get('salario_infotep', 0), number_style)
    
    # Set column widths
    col_widths = [3, 12, 6, 15, 20, 15, 15, 6, 12, 12, 10, 12, 10, 12, 12, 12, 12, 12, 20, 12, 12]
    for col, width in enumerate(col_widths):
        ws.col(col).width = width * 256
    
    # Sheet 2: Reporte de Contribuciones (summary)
    ws2 = workbook.add_sheet('Reporte de Contribuciones')
    ws2.write_merge(5, 5, 1, 10, 'Reporte de Contribuciones al SDSS y DGII', header_style)
    
    # Summary headers
    summary_headers = ['', 'No. Doc', 'Apellidos y Nombres', 'Salario Cotizable', 
                       'Aporte Voluntario', 'Retención SFS', 'Contribución AFP', 
                       'Riesgo Laboral', 'Total Aportes', 'Salario ISR', 
                       'Otras Rem.', 'Rem. Otro Agente', 'Total Pagado', 
                       'Ingresos Exentos', 'Saldo A Favor', 'Salario INFOTEP']
    
    for col, h in enumerate(summary_headers):
        ws2.write(8, col, h, header_style)
    
    # Summary data
    for row_idx, emp in enumerate(employees, start=9):
        ws2.write(row_idx, 1, emp.get('numero_doc', ''), data_style)
        ws2.write(row_idx, 2, f"{emp.get('nombres', '')} {emp.get('primer_apellido', '')}", data_style)
        ws2.write(row_idx, 3, emp.get('salario_cotizable_sdss', 0), number_style)
        ws2.write(row_idx, 4, emp.get('aporte_voluntario', 0), number_style)
        ws2.write(row_idx, 5, emp.get('retencion_sfs', 0), number_style)
        ws2.write(row_idx, 6, emp.get('contribucion_afp', 0), number_style)
        ws2.write(row_idx, 7, emp.get('riesgo_laboral', 0), number_style)
        ws2.write(row_idx, 8, emp.get('total_aportes', 0), number_style)
        ws2.write(row_idx, 9, emp.get('salario_isr', 0), number_style)
        ws2.write(row_idx, 10, emp.get('otras_remuneraciones', 0), number_style)
        ws2.write(row_idx, 11, emp.get('remuneracion_otros_agentes', 0), number_style)
        ws2.write(row_idx, 12, emp.get('total_pagado', 0), number_style)
        ws2.write(row_idx, 13, emp.get('ingresos_exentos', 0), number_style)
        ws2.write(row_idx, 14, emp.get('saldo_favor', 0), number_style)
        ws2.write(row_idx, 15, emp.get('salario_infotep', 0), number_style)
    
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return output


def create_tss_novedades_excel(
    rnc_cedula: str,
    periodo: str,  # MMAAAA
    novedades: List[Dict[str, Any]]
) -> BytesIO:
    """
    Genera archivo Excel de Novedades TSS v5.1
    
    Tipos de Novedad:
    - IN: Ingreso (nuevo empleado)
    - SA: Salida (terminación)
    - VC: Vacaciones
    - LV: Licencia de Vacaciones
    - LM: Licencia de Maternidad
    - LD: Licencia por Duelo
    - AD: Ajuste de Datos
    """
    workbook = xlwt.Workbook(encoding='utf-8')
    
    # Sheet 1: Plantilla de archivo novedades
    ws = workbook.add_sheet('Plantilla de archivo novedades')
    
    # Styles
    header_style = xlwt.easyxf('font: bold on; align: horiz center; borders: left thin, right thin, top thin, bottom thin')
    subheader_style = xlwt.easyxf('font: bold on; align: horiz center; pattern: pattern solid, fore_colour light_blue')
    data_style = xlwt.easyxf('borders: left thin, right thin, top thin, bottom thin')
    number_style = xlwt.easyxf('borders: left thin, right thin, top thin, bottom thin', num_format_str='#,##0.00')
    date_style = xlwt.easyxf('borders: left thin, right thin, top thin, bottom thin', num_format_str='DD/MM/YYYY')
    
    # Title
    ws.write_merge(5, 5, 1, 8, 'Plantilla de Archivo Novedades', header_style)
    
    # Metadata
    ws.write(6, 0, 'RNC o Cédula:', data_style)
    ws.write(6, 4, rnc_cedula, data_style)
    ws.write(6, 5, f'Ver. {TSS_NOVEDADES_VERSION}', data_style)
    
    ws.write(7, 0, 'Período:', data_style)
    ws.write(7, 4, periodo, data_style)
    ws.write(7, 5, '<-- MMAAAA', data_style)
    
    ws.write(9, 2, '# de Empleados:', data_style)
    ws.write(9, 4, len(novedades), data_style)
    
    # Section headers (row 10)
    ws.write_merge(10, 10, 1, 11, 'TRABAJADORES', subheader_style)
    ws.write_merge(10, 10, 12, 14, 'SDSS', subheader_style)
    ws.write_merge(10, 10, 15, 22, 'DGII', subheader_style)
    ws.write(10, 23, 'INFOTEP', subheader_style)
    
    # Column headers (row 11-12)
    headers_row1 = [
        '', 'Clave', 'Tipo', 'Fecha', 'Fecha', 'Tipo', 'Número', 'Nombres', 
        '1er. Apellido', '2do. Apellido', 'Sexo', 'Fecha', 
        'Salario', 'Aporte', 'Tipo',
        'Salario', 'Otras', 'RNC/Céd.', 'Remuneración', 'Saldo a favor',
        'Regalía Pascual', 'Preaviso, Cesantía, Viático e Indemnizaciones',
        'Retención Pensión', 'Salario'
    ]
    headers_row2 = [
        '', 'Nómina', 'Novedad', 'Inicio', 'Fin', 'Doc.', 'Documento', '',
        '', '', '', 'Nacimiento',
        'Cotizable SDSS', 'Voluntario SDSS', 'Ingreso',
        'ISR', 'Remuneraciones', 'Agente Ret', 'Otros Agentes', 'del período',
        '(Saldo 13)', 'Por Accidentes Laborales', 'Alimenticia', 'INFOTEP'
    ]
    
    for col, (h1, h2) in enumerate(zip(headers_row1, headers_row2)):
        ws.write(11, col, h1, header_style)
        ws.write(12, col, h2, header_style)
    
    # Data rows starting at row 13
    for row_idx, nov in enumerate(novedades, start=13):
        ws.write(row_idx, 1, nov.get('clave_nomina', ''), data_style)
        ws.write(row_idx, 2, nov.get('tipo_novedad', 'IN'), data_style)
        ws.write(row_idx, 3, nov.get('fecha_inicio', ''), data_style)
        ws.write(row_idx, 4, nov.get('fecha_fin', ''), data_style)
        ws.write(row_idx, 5, nov.get('tipo_doc', 'C'), data_style)
        ws.write(row_idx, 6, nov.get('numero_doc', ''), data_style)
        ws.write(row_idx, 7, nov.get('nombres', ''), data_style)
        ws.write(row_idx, 8, nov.get('primer_apellido', ''), data_style)
        ws.write(row_idx, 9, nov.get('segundo_apellido', ''), data_style)
        ws.write(row_idx, 10, nov.get('sexo', 'M'), data_style)
        ws.write(row_idx, 11, nov.get('fecha_nacimiento', ''), data_style)
        ws.write(row_idx, 12, nov.get('salario_cotizable_sdss', 0), number_style)
        ws.write(row_idx, 13, nov.get('aporte_voluntario', 0), number_style)
        ws.write(row_idx, 14, nov.get('tipo_ingreso', 'Normal'), data_style)
        ws.write(row_idx, 15, nov.get('salario_isr', 0), number_style)
        ws.write(row_idx, 16, nov.get('otras_remuneraciones', 0), number_style)
        ws.write(row_idx, 17, nov.get('rnc_agente_ret', ''), data_style)
        ws.write(row_idx, 18, nov.get('remuneracion_otros_agentes', 0), number_style)
        ws.write(row_idx, 19, nov.get('saldo_favor', 0), number_style)
        ws.write(row_idx, 20, nov.get('regalia_pascual', 0), number_style)
        ws.write(row_idx, 21, nov.get('preaviso_cesantia', 0), number_style)
        ws.write(row_idx, 22, nov.get('retencion_pension', 0), number_style)
        ws.write(row_idx, 23, nov.get('salario_infotep', 0), number_style)
    
    # Set column widths
    col_widths = [3, 12, 8, 12, 12, 6, 15, 20, 15, 15, 6, 12, 12, 10, 10, 12, 12, 12, 12, 12, 12, 20, 12, 12]
    for col, width in enumerate(col_widths):
        ws.col(col).width = width * 256
    
    # Sheet 2: Reporte summary
    ws2 = workbook.add_sheet('Reporte de Contribuciones')
    ws2.write_merge(5, 5, 1, 10, 'Reporte de Contribuciones de las Novedades', header_style)
    
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return output


def create_ir3_report(
    rnc_company: str,
    company_name: str,
    periodo: str,  # MMAAAA
    employees: List[Dict[str, Any]]
) -> BytesIO:
    """
    Genera reporte IR-3 (Retenciones de Asalariados)
    Formato DGII para reportar ISR retenido a empleados
    """
    workbook = xlwt.Workbook(encoding='utf-8')
    ws = workbook.add_sheet('IR-3')
    
    # Styles
    title_style = xlwt.easyxf('font: bold on, height 280; align: horiz center')
    header_style = xlwt.easyxf('font: bold on; align: horiz center; borders: left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_colour light_yellow')
    data_style = xlwt.easyxf('borders: left thin, right thin, top thin, bottom thin')
    number_style = xlwt.easyxf('borders: left thin, right thin, top thin, bottom thin', num_format_str='#,##0.00')
    
    # Title
    ws.write_merge(0, 0, 0, 8, 'DECLARACIÓN JURADA DE RETENCIONES DE ASALARIADOS', title_style)
    ws.write_merge(1, 1, 0, 8, 'IR-3', title_style)
    
    # Company info
    ws.write(3, 0, 'RNC:', data_style)
    ws.write(3, 1, rnc_company, data_style)
    ws.write(3, 3, 'Razón Social:', data_style)
    ws.write(3, 4, company_name, data_style)
    
    ws.write(4, 0, 'Período:', data_style)
    ws.write(4, 1, periodo, data_style)
    
    # Column headers
    headers = ['No.', 'Cédula/RNC', 'Nombres y Apellidos', 'Salario Bruto', 
               'Salario Cotizable TSS', 'Exenciones', 'Renta Neta Gravable', 
               'ISR Calculado', 'ISR Retenido']
    
    for col, h in enumerate(headers):
        ws.write(6, col, h, header_style)
    
    # Data
    total_salario = 0
    total_isr = 0
    
    for row_idx, emp in enumerate(employees, start=7):
        ws.write(row_idx, 0, row_idx - 6, data_style)
        ws.write(row_idx, 1, emp.get('cedula', ''), data_style)
        ws.write(row_idx, 2, emp.get('nombre_completo', ''), data_style)
        ws.write(row_idx, 3, emp.get('salario_bruto', 0), number_style)
        ws.write(row_idx, 4, emp.get('salario_cotizable', 0), number_style)
        ws.write(row_idx, 5, emp.get('exenciones', 0), number_style)
        ws.write(row_idx, 6, emp.get('renta_neta_gravable', 0), number_style)
        ws.write(row_idx, 7, emp.get('isr_calculado', 0), number_style)
        ws.write(row_idx, 8, emp.get('isr_retenido', 0), number_style)
        
        total_salario += emp.get('salario_bruto', 0)
        total_isr += emp.get('isr_retenido', 0)
    
    # Totals row
    total_row = 7 + len(employees)
    ws.write(total_row, 2, 'TOTALES:', header_style)
    ws.write(total_row, 3, total_salario, number_style)
    ws.write(total_row, 8, total_isr, number_style)
    
    # Column widths
    col_widths = [5, 15, 30, 15, 15, 12, 15, 12, 12]
    for col, width in enumerate(col_widths):
        ws.col(col).width = width * 256
    
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return output


def create_ir17_report(
    rnc_company: str,
    company_name: str,
    periodo: str,  # MMAAAA
    summary: Dict[str, Any]
) -> BytesIO:
    """
    Genera reporte IR-17 (Declaración Jurada Mensual del Impuesto sobre la Renta)
    Resumen de retenciones e impuestos
    """
    workbook = xlwt.Workbook(encoding='utf-8')
    ws = workbook.add_sheet('IR-17')
    
    # Styles
    title_style = xlwt.easyxf('font: bold on, height 280; align: horiz center')
    header_style = xlwt.easyxf('font: bold on; align: horiz left; borders: left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_colour light_green')
    data_style = xlwt.easyxf('borders: left thin, right thin, top thin, bottom thin')
    number_style = xlwt.easyxf('borders: left thin, right thin, top thin, bottom thin; align: horiz right', num_format_str='#,##0.00')
    
    # Title
    ws.write_merge(0, 0, 0, 4, 'DECLARACIÓN JURADA MENSUAL DEL ISR', title_style)
    ws.write_merge(1, 1, 0, 4, 'FORMULARIO IR-17', title_style)
    
    # Company info
    ws.write(3, 0, 'RNC:', data_style)
    ws.write(3, 1, rnc_company, data_style)
    ws.write(4, 0, 'Razón Social:', data_style)
    ws.write(4, 1, company_name, data_style)
    ws.write(5, 0, 'Período:', data_style)
    ws.write(5, 1, periodo, data_style)
    
    # Section: Retenciones a Asalariados
    ws.write(7, 0, 'A. RETENCIONES A ASALARIADOS', header_style)
    
    rows = [
        ('Cantidad de empleados', summary.get('cantidad_empleados', 0)),
        ('Total sueldos y salarios pagados', summary.get('total_sueldos', 0)),
        ('Aportes TSS (SFS + AFP)', summary.get('total_tss_empleado', 0)),
        ('Otras deducciones permitidas', summary.get('otras_deducciones', 0)),
        ('Total renta neta gravable', summary.get('renta_neta_gravable', 0)),
        ('ISR Retenido del período', summary.get('isr_retenido', 0)),
    ]
    
    for row_idx, (label, value) in enumerate(rows, start=8):
        ws.write(row_idx, 0, label, data_style)
        ws.write(row_idx, 1, value, number_style)
    
    # Section: Aportes Patronales
    ws.write(15, 0, 'B. APORTES PATRONALES TSS', header_style)
    
    patron_rows = [
        ('SFS Empleador (7.09%)', summary.get('sfs_empleador', 0)),
        ('AFP Empleador (7.10%)', summary.get('afp_empleador', 0)),
        ('SRL (1.00%)', summary.get('srl', 0)),
        ('INFOTEP (1.00%)', summary.get('infotep', 0)),
        ('Total Aportes Patronales', summary.get('total_aportes_patronales', 0)),
    ]
    
    for row_idx, (label, value) in enumerate(patron_rows, start=16):
        ws.write(row_idx, 0, label, data_style)
        ws.write(row_idx, 1, value, number_style)
    
    # Total a pagar
    ws.write(22, 0, 'TOTAL A PAGAR DGII', header_style)
    ws.write(22, 1, summary.get('isr_retenido', 0), number_style)
    
    ws.write(23, 0, 'TOTAL A PAGAR TSS', header_style)
    ws.write(23, 1, summary.get('total_tss', 0), number_style)
    
    # Column widths
    ws.col(0).width = 40 * 256
    ws.col(1).width = 20 * 256
    
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return output


def create_ir4_report(
    rnc_company: str,
    company_name: str,
    periodo: str,  # MMAAAA
    employees: List[Dict[str, Any]]
) -> BytesIO:
    """
    Genera reporte IR-4 (Detalle Mensual de Retenciones de Asalariados)
    Este detalle alimenta la declaración IR-3 ante la DGII
    
    Columnas:
    - Línea, Cédula/RNC, Tipo Doc, Nombres y Apellidos
    - Sueldo Bruto Mensual, Otros Ingresos, Total Ingresos
    - Aporte AFP Empleado, Aporte SFS Empleado, Total Aportes TSS
    - Renta Neta Imponible, ISR Determinado, ISR Retenido
    """
    workbook = xlwt.Workbook(encoding='utf-8')
    ws = workbook.add_sheet('IR-4 Detalle')
    
    # Styles
    title_style = xlwt.easyxf('font: bold on, height 280; align: horiz center')
    subtitle_style = xlwt.easyxf('font: bold on, height 220; align: horiz center; pattern: pattern solid, fore_colour light_blue')
    header_style = xlwt.easyxf('font: bold on; align: horiz center, vert center; borders: left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_colour light_yellow')
    data_style = xlwt.easyxf('borders: left thin, right thin, top thin, bottom thin')
    number_style = xlwt.easyxf('borders: left thin, right thin, top thin, bottom thin; align: horiz right', num_format_str='#,##0.00')
    total_style = xlwt.easyxf('font: bold on; borders: left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_colour light_green', num_format_str='#,##0.00')
    
    # Title Section
    ws.write_merge(0, 0, 0, 12, 'DIRECCIÓN GENERAL DE IMPUESTOS INTERNOS', title_style)
    ws.write_merge(1, 1, 0, 12, 'DETALLE MENSUAL DE RETENCIONES DE ASALARIADOS', subtitle_style)
    ws.write_merge(2, 2, 0, 12, 'FORMULARIO IR-4', subtitle_style)
    
    # Company info
    ws.write(4, 0, 'RNC/Cédula Agente Retención:', data_style)
    ws.write_merge(4, 4, 2, 4, rnc_company, data_style)
    
    ws.write(5, 0, 'Razón Social:', data_style)
    ws.write_merge(5, 5, 2, 6, company_name, data_style)
    
    ws.write(6, 0, 'Período Fiscal:', data_style)
    # Format periodo from MMAAAA to MM/AAAA
    mes = periodo[:2] if len(periodo) >= 2 else periodo
    anio = periodo[2:] if len(periodo) > 2 else ""
    ws.write(6, 2, f"{mes}/{anio}", data_style)
    
    ws.write(7, 0, 'Cantidad de Empleados:', data_style)
    ws.write(7, 2, len(employees), data_style)
    
    # Column headers (row 9)
    headers = [
        'Línea',
        'Cédula/RNC',
        'Tipo Doc',
        'Nombres y Apellidos',
        'Sueldo Bruto\nMensual',
        'Otros\nIngresos',
        'Total\nIngresos',
        'Aporte AFP\nEmpleado',
        'Aporte SFS\nEmpleado',
        'Total\nAportes TSS',
        'Renta Neta\nImponible',
        'ISR\nDeterminado',
        'ISR\nRetenido'
    ]
    
    for col, h in enumerate(headers):
        ws.write(9, col, h, header_style)
    
    # Set row height for headers
    ws.row(9).height_mismatch = True
    ws.row(9).height = 800
    
    # Data rows
    totals = {
        'sueldo_bruto': 0,
        'otros_ingresos': 0,
        'total_ingresos': 0,
        'afp_empleado': 0,
        'sfs_empleado': 0,
        'total_tss': 0,
        'renta_neta': 0,
        'isr_determinado': 0,
        'isr_retenido': 0
    }
    
    for row_idx, emp in enumerate(employees, start=10):
        linea = row_idx - 9
        
        sueldo_bruto = emp.get('salario_bruto', 0)
        otros_ingresos = emp.get('otros_ingresos', 0)
        total_ingresos = sueldo_bruto + otros_ingresos
        afp_emp = emp.get('afp_empleado', 0)
        sfs_emp = emp.get('sfs_empleado', 0)
        total_tss = afp_emp + sfs_emp
        renta_neta = total_ingresos - total_tss
        isr_det = emp.get('isr_calculado', 0)
        isr_ret = emp.get('isr_retenido', 0)
        
        ws.write(row_idx, 0, linea, data_style)
        ws.write(row_idx, 1, emp.get('cedula', ''), data_style)
        ws.write(row_idx, 2, emp.get('tipo_doc', 'C'), data_style)
        ws.write(row_idx, 3, emp.get('nombre_completo', ''), data_style)
        ws.write(row_idx, 4, sueldo_bruto, number_style)
        ws.write(row_idx, 5, otros_ingresos, number_style)
        ws.write(row_idx, 6, total_ingresos, number_style)
        ws.write(row_idx, 7, afp_emp, number_style)
        ws.write(row_idx, 8, sfs_emp, number_style)
        ws.write(row_idx, 9, total_tss, number_style)
        ws.write(row_idx, 10, renta_neta, number_style)
        ws.write(row_idx, 11, isr_det, number_style)
        ws.write(row_idx, 12, isr_ret, number_style)
        
        # Accumulate totals
        totals['sueldo_bruto'] += sueldo_bruto
        totals['otros_ingresos'] += otros_ingresos
        totals['total_ingresos'] += total_ingresos
        totals['afp_empleado'] += afp_emp
        totals['sfs_empleado'] += sfs_emp
        totals['total_tss'] += total_tss
        totals['renta_neta'] += renta_neta
        totals['isr_determinado'] += isr_det
        totals['isr_retenido'] += isr_ret
    
    # Totals row
    total_row = 10 + len(employees)
    ws.write(total_row, 3, 'TOTALES:', total_style)
    ws.write(total_row, 4, totals['sueldo_bruto'], total_style)
    ws.write(total_row, 5, totals['otros_ingresos'], total_style)
    ws.write(total_row, 6, totals['total_ingresos'], total_style)
    ws.write(total_row, 7, totals['afp_empleado'], total_style)
    ws.write(total_row, 8, totals['sfs_empleado'], total_style)
    ws.write(total_row, 9, totals['total_tss'], total_style)
    ws.write(total_row, 10, totals['renta_neta'], total_style)
    ws.write(total_row, 11, totals['isr_determinado'], total_style)
    ws.write(total_row, 12, totals['isr_retenido'], total_style)
    
    # Column widths
    col_widths = [6, 14, 8, 30, 14, 12, 14, 12, 12, 14, 14, 12, 12]
    for col, width in enumerate(col_widths):
        ws.col(col).width = width * 256
    
    # Sheet 2: Resumen para IR-3
    ws2 = workbook.add_sheet('Resumen IR-3')
    
    ws2.write_merge(0, 0, 0, 3, 'RESUMEN PARA DECLARACIÓN IR-3', title_style)
    ws2.write_merge(1, 1, 0, 3, f'Período: {mes}/{anio}', subtitle_style)
    
    summary_data = [
        ('Total Sueldos y Salarios', totals['sueldo_bruto']),
        ('Otros Ingresos Gravables', totals['otros_ingresos']),
        ('Total Ingresos Brutos', totals['total_ingresos']),
        ('(-) Aportes AFP Empleado', totals['afp_empleado']),
        ('(-) Aportes SFS Empleado', totals['sfs_empleado']),
        ('(=) Total Deducciones TSS', totals['total_tss']),
        ('(=) Renta Neta Imponible', totals['renta_neta']),
        ('ISR Determinado', totals['isr_determinado']),
        ('ISR Retenido a Pagar', totals['isr_retenido']),
    ]
    
    for row_idx, (label, value) in enumerate(summary_data, start=3):
        ws2.write(row_idx, 0, label, data_style)
        ws2.write(row_idx, 1, value, number_style)
    
    ws2.col(0).width = 30 * 256
    ws2.col(1).width = 18 * 256
    
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return output


def create_ir13_report(
    rnc_company: str,
    company_name: str,
    year: int,
    employees_annual: List[Dict[str, Any]],
    monthly_summary: List[Dict[str, Any]]
) -> BytesIO:
    """
    Genera reporte IR-13 (Declaración Jurada Anual de Retenciones de Asalariados)
    Consolida todos los IR-4 mensuales del año fiscal
    
    Args:
        rnc_company: RNC de la empresa
        company_name: Nombre de la empresa
        year: Año fiscal
        employees_annual: Lista de empleados con totales anuales
        monthly_summary: Resumen mensual de retenciones
    """
    workbook = xlwt.Workbook(encoding='utf-8')
    
    # Styles
    title_style = xlwt.easyxf('font: bold on, height 320; align: horiz center')
    subtitle_style = xlwt.easyxf('font: bold on, height 240; align: horiz center; pattern: pattern solid, fore_colour light_blue')
    header_style = xlwt.easyxf('font: bold on; align: horiz center, vert center; borders: left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_colour light_yellow')
    subheader_style = xlwt.easyxf('font: bold on; align: horiz center; borders: left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_colour light_green')
    data_style = xlwt.easyxf('borders: left thin, right thin, top thin, bottom thin')
    number_style = xlwt.easyxf('borders: left thin, right thin, top thin, bottom thin; align: horiz right', num_format_str='#,##0.00')
    total_style = xlwt.easyxf('font: bold on; borders: left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_colour light_orange', num_format_str='#,##0.00')
    month_style = xlwt.easyxf('font: bold on; borders: left thin, right thin, top thin, bottom thin; pattern: pattern solid, fore_colour pale_blue')
    
    # ========== Sheet 1: Detalle Anual por Empleado ==========
    ws1 = workbook.add_sheet('IR-13 Detalle Anual')
    
    # Title Section
    ws1.write_merge(0, 0, 0, 14, 'DIRECCIÓN GENERAL DE IMPUESTOS INTERNOS', title_style)
    ws1.write_merge(1, 1, 0, 14, 'DECLARACIÓN JURADA ANUAL DE RETENCIONES DE ASALARIADOS', subtitle_style)
    ws1.write_merge(2, 2, 0, 14, f'FORMULARIO IR-13 - AÑO FISCAL {year}', subtitle_style)
    
    # Company info
    ws1.write(4, 0, 'RNC/Cédula Agente Retención:', data_style)
    ws1.write_merge(4, 4, 2, 4, rnc_company, data_style)
    
    ws1.write(5, 0, 'Razón Social:', data_style)
    ws1.write_merge(5, 5, 2, 6, company_name, data_style)
    
    ws1.write(6, 0, 'Año Fiscal:', data_style)
    ws1.write(6, 2, year, data_style)
    
    ws1.write(7, 0, 'Cantidad de Empleados:', data_style)
    ws1.write(7, 2, len(employees_annual), data_style)
    
    # Column headers for employee detail
    headers = [
        'No.', 'Cédula/RNC', 'Tipo', 'Nombres y Apellidos',
        'Sueldo Anual\nBruto', 'Otros\nIngresos', 'Regalía\nPascual',
        'Total\nIngresos', 'Aporte AFP\nAnual', 'Aporte SFS\nAnual',
        'Total\nAportes TSS', 'Renta Neta\nAnual', 'ISR\nAnual',
        'Meses\nLaborados', 'Promedio\nMensual'
    ]
    
    for col, h in enumerate(headers):
        ws1.write(9, col, h, header_style)
    
    ws1.row(9).height_mismatch = True
    ws1.row(9).height = 900
    
    # Employee data
    totals = {
        'sueldo_anual': 0, 'otros_ingresos': 0, 'regalia': 0,
        'total_ingresos': 0, 'afp_anual': 0, 'sfs_anual': 0,
        'total_tss': 0, 'renta_neta': 0, 'isr_anual': 0
    }
    
    for row_idx, emp in enumerate(employees_annual, start=10):
        linea = row_idx - 9
        
        sueldo = emp.get('sueldo_anual', 0)
        otros = emp.get('otros_ingresos', 0)
        regalia = emp.get('regalia_pascual', 0)
        total_ing = sueldo + otros + regalia
        afp = emp.get('afp_anual', 0)
        sfs = emp.get('sfs_anual', 0)
        tss = afp + sfs
        renta = total_ing - tss
        isr = emp.get('isr_anual', 0)
        meses = emp.get('meses_laborados', 12)
        promedio = total_ing / meses if meses > 0 else 0
        
        ws1.write(row_idx, 0, linea, data_style)
        ws1.write(row_idx, 1, emp.get('cedula', ''), data_style)
        ws1.write(row_idx, 2, emp.get('tipo_doc', 'C'), data_style)
        ws1.write(row_idx, 3, emp.get('nombre_completo', ''), data_style)
        ws1.write(row_idx, 4, sueldo, number_style)
        ws1.write(row_idx, 5, otros, number_style)
        ws1.write(row_idx, 6, regalia, number_style)
        ws1.write(row_idx, 7, total_ing, number_style)
        ws1.write(row_idx, 8, afp, number_style)
        ws1.write(row_idx, 9, sfs, number_style)
        ws1.write(row_idx, 10, tss, number_style)
        ws1.write(row_idx, 11, renta, number_style)
        ws1.write(row_idx, 12, isr, number_style)
        ws1.write(row_idx, 13, meses, data_style)
        ws1.write(row_idx, 14, promedio, number_style)
        
        totals['sueldo_anual'] += sueldo
        totals['otros_ingresos'] += otros
        totals['regalia'] += regalia
        totals['total_ingresos'] += total_ing
        totals['afp_anual'] += afp
        totals['sfs_anual'] += sfs
        totals['total_tss'] += tss
        totals['renta_neta'] += renta
        totals['isr_anual'] += isr
    
    # Totals row
    total_row = 10 + len(employees_annual)
    ws1.write(total_row, 3, 'TOTALES ANUALES:', total_style)
    ws1.write(total_row, 4, totals['sueldo_anual'], total_style)
    ws1.write(total_row, 5, totals['otros_ingresos'], total_style)
    ws1.write(total_row, 6, totals['regalia'], total_style)
    ws1.write(total_row, 7, totals['total_ingresos'], total_style)
    ws1.write(total_row, 8, totals['afp_anual'], total_style)
    ws1.write(total_row, 9, totals['sfs_anual'], total_style)
    ws1.write(total_row, 10, totals['total_tss'], total_style)
    ws1.write(total_row, 11, totals['renta_neta'], total_style)
    ws1.write(total_row, 12, totals['isr_anual'], total_style)
    
    # Column widths
    col_widths = [5, 14, 5, 30, 14, 12, 12, 14, 12, 12, 14, 14, 12, 8, 12]
    for col, width in enumerate(col_widths):
        ws1.col(col).width = width * 256
    
    # ========== Sheet 2: Resumen Mensual ==========
    ws2 = workbook.add_sheet('Resumen Mensual')
    
    ws2.write_merge(0, 0, 0, 8, f'RESUMEN MENSUAL DE RETENCIONES - AÑO {year}', title_style)
    
    month_names = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                   'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    
    month_headers = ['Mes', 'Empleados', 'Sueldos Brutos', 'Otros Ingresos',
                     'Total Ingresos', 'Aportes TSS', 'Renta Neta', 'ISR Retenido', 'Estado']
    
    for col, h in enumerate(month_headers):
        ws2.write(2, col, h, header_style)
    
    annual_totals = {
        'empleados': 0, 'sueldos': 0, 'otros': 0,
        'total': 0, 'tss': 0, 'renta': 0, 'isr': 0
    }
    
    for row_idx, month_data in enumerate(monthly_summary, start=3):
        month_num = month_data.get('month', row_idx - 2)
        month_name = month_names[month_num - 1] if 1 <= month_num <= 12 else f'Mes {month_num}'
        
        empleados = month_data.get('employee_count', 0)
        sueldos = month_data.get('total_sueldos', 0)
        otros = month_data.get('otros_ingresos', 0)
        total = sueldos + otros
        tss = month_data.get('total_tss', 0)
        renta = total - tss
        isr = month_data.get('isr_retenido', 0)
        estado = month_data.get('status', 'pendiente')
        
        ws2.write(row_idx, 0, month_name, month_style)
        ws2.write(row_idx, 1, empleados, data_style)
        ws2.write(row_idx, 2, sueldos, number_style)
        ws2.write(row_idx, 3, otros, number_style)
        ws2.write(row_idx, 4, total, number_style)
        ws2.write(row_idx, 5, tss, number_style)
        ws2.write(row_idx, 6, renta, number_style)
        ws2.write(row_idx, 7, isr, number_style)
        ws2.write(row_idx, 8, 'Presentado' if estado in ['paid', 'closed'] else 'Pendiente', data_style)
        
        annual_totals['sueldos'] += sueldos
        annual_totals['otros'] += otros
        annual_totals['total'] += total
        annual_totals['tss'] += tss
        annual_totals['renta'] += renta
        annual_totals['isr'] += isr
    
    # Annual totals row
    total_row = 3 + len(monthly_summary)
    ws2.write(total_row, 0, 'TOTAL ANUAL', total_style)
    ws2.write(total_row, 2, annual_totals['sueldos'], total_style)
    ws2.write(total_row, 3, annual_totals['otros'], total_style)
    ws2.write(total_row, 4, annual_totals['total'], total_style)
    ws2.write(total_row, 5, annual_totals['tss'], total_style)
    ws2.write(total_row, 6, annual_totals['renta'], total_style)
    ws2.write(total_row, 7, annual_totals['isr'], total_style)
    
    ws2.col(0).width = 12 * 256
    ws2.col(1).width = 10 * 256
    for col in range(2, 8):
        ws2.col(col).width = 15 * 256
    ws2.col(8).width = 12 * 256
    
    # ========== Sheet 3: Declaración Resumen ==========
    ws3 = workbook.add_sheet('Declaración')
    
    ws3.write_merge(0, 0, 0, 3, 'DECLARACIÓN JURADA ANUAL IR-13', title_style)
    ws3.write_merge(1, 1, 0, 3, f'Año Fiscal: {year}', subtitle_style)
    
    ws3.write(3, 0, 'A. DATOS DEL AGENTE DE RETENCIÓN', subheader_style)
    ws3.write(4, 0, 'RNC/Cédula:', data_style)
    ws3.write(4, 1, rnc_company, data_style)
    ws3.write(5, 0, 'Razón Social:', data_style)
    ws3.write(5, 1, company_name, data_style)
    
    ws3.write(7, 0, 'B. RESUMEN DE RETENCIONES DEL AÑO', subheader_style)
    
    declaration_data = [
        ('1. Total de empleados durante el año', len(employees_annual)),
        ('2. Total sueldos y salarios pagados', totals['sueldo_anual']),
        ('3. Otros ingresos gravables', totals['otros_ingresos']),
        ('4. Regalía Pascual pagada', totals['regalia']),
        ('5. Total ingresos brutos (2+3+4)', totals['total_ingresos']),
        ('6. (-) Aportes AFP empleados', totals['afp_anual']),
        ('7. (-) Aportes SFS empleados', totals['sfs_anual']),
        ('8. (=) Total aportes TSS empleados (6+7)', totals['total_tss']),
        ('9. (=) Renta Neta Imponible (5-8)', totals['renta_neta']),
        ('10. ISR Retenido Anual', totals['isr_anual']),
    ]
    
    for row_idx, (label, value) in enumerate(declaration_data, start=8):
        ws3.write(row_idx, 0, label, data_style)
        if isinstance(value, (int, float)):
            ws3.write(row_idx, 1, value, number_style)
        else:
            ws3.write(row_idx, 1, value, data_style)
    
    # Certification section
    ws3.write(20, 0, 'C. CERTIFICACIÓN', subheader_style)
    ws3.write(21, 0, 'Certifico que la información contenida en esta declaración es correcta y completa.', data_style)
    ws3.write(23, 0, 'Firma del Representante Legal: _________________________', data_style)
    ws3.write(24, 0, 'Fecha: _________________________', data_style)
    
    ws3.col(0).width = 45 * 256
    ws3.col(1).width = 20 * 256
    
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return output
