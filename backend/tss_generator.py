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
