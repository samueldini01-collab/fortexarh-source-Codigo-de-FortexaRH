"""
Report Catalog - FortexaRH
Report category and definition data for the reporting system.
"""

REPORT_CATEGORIES = {
    "nomina": {
        "name": "Nómina",
        "icon": "dollar-sign",
        "color": "emerald"
    },
    "empleados": {
        "name": "Empleados",
        "icon": "users",
        "color": "blue"
    },
    "asistencia": {
        "name": "Asistencia",
        "icon": "clock",
        "color": "amber"
    },
    "vacaciones": {
        "name": "Vacaciones y Permisos",
        "icon": "calendar",
        "color": "purple"
    },
    "evaluaciones": {
        "name": "Evaluaciones",
        "icon": "target",
        "color": "indigo"
    },
    "financiero": {
        "name": "Financiero/Contable",
        "icon": "wallet",
        "color": "rose"
    },
    "reclutamiento": {
        "name": "Reclutamiento",
        "icon": "briefcase",
        "color": "cyan"
    },
    "capacitacion": {
        "name": "Capacitación",
        "icon": "graduation-cap",
        "color": "orange"
    },
    "analytics": {
        "name": "Análisis y KPIs",
        "icon": "bar-chart",
        "color": "violet"
    },
    "cumplimiento": {
        "name": "Cumplimiento Legal",
        "icon": "shield-check",
        "color": "teal"
    }
}

REPORT_DEFINITIONS = {
    # ========== NÓMINA (8 reports) ==========
    "nomina_resumen": {
        "id": "nomina_resumen",
        "name": "Resumen de Nómina por Período",
        "description": "Vista general de la nómina con totales por concepto",
        "category": "nomina",
        "filters": ["period", "department", "status"],
        "columns": ["employee", "department", "base_salary", "bonuses", "deductions", "net_pay"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "nomina_detalle_empleado": {
        "id": "nomina_detalle_empleado",
        "name": "Detalle de Nómina por Empleado",
        "description": "Desglose completo de cada empleado con todos los conceptos",
        "category": "nomina",
        "filters": ["period", "employee", "department"],
        "columns": ["concept", "type", "amount", "percentage"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "nomina_comparativo": {
        "id": "nomina_comparativo",
        "name": "Comparativo de Nómina",
        "description": "Comparación mes a mes de costos de nómina",
        "category": "nomina",
        "filters": ["date_range", "department"],
        "columns": ["month", "total_employees", "gross_pay", "deductions", "net_pay", "variation"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "nomina_deducciones": {
        "id": "nomina_deducciones",
        "name": "Deducciones por Tipo",
        "description": "Resumen de deducciones (SFS, AFP, ISR, préstamos)",
        "category": "nomina",
        "filters": ["period", "deduction_type", "department"],
        "columns": ["employee", "sfs", "afp", "isr", "loans", "other", "total"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "nomina_horas_extras": {
        "id": "nomina_horas_extras",
        "name": "Horas Extras y Bonificaciones",
        "description": "Detalle de horas extras y bonos pagados",
        "category": "nomina",
        "filters": ["period", "employee", "department"],
        "columns": ["employee", "regular_hours", "overtime_35", "overtime_100", "bonuses", "total_extra"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "nomina_historico": {
        "id": "nomina_historico",
        "name": "Histórico de Pagos por Empleado",
        "description": "Historial completo de pagos de un empleado",
        "category": "nomina",
        "filters": ["employee", "date_range"],
        "columns": ["period", "gross_pay", "deductions", "net_pay", "payment_date"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "nomina_costos_departamento": {
        "id": "nomina_costos_departamento",
        "name": "Costos Laborales por Departamento",
        "description": "Análisis de costos por área organizacional",
        "category": "nomina",
        "filters": ["period", "department"],
        "columns": ["department", "employees", "salaries", "benefits", "taxes", "total_cost", "percentage"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "nomina_proyeccion": {
        "id": "nomina_proyeccion",
        "name": "Proyección de Nómina",
        "description": "Estimación de costos futuros basado en tendencias",
        "category": "nomina",
        "filters": ["months_ahead", "include_increases"],
        "columns": ["month", "projected_gross", "projected_deductions", "projected_net", "confidence"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    
    # ========== EMPLEADOS (6 reports) ==========
    "empleados_listado": {
        "id": "empleados_listado",
        "name": "Listado General de Empleados",
        "description": "Lista completa con datos básicos de todos los empleados",
        "category": "empleados",
        "filters": ["status", "department", "position"],
        "columns": ["cedula", "name", "department", "position", "hire_date", "salary", "status"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "empleados_departamento": {
        "id": "empleados_departamento",
        "name": "Empleados por Departamento",
        "description": "Distribución de personal por área",
        "category": "empleados",
        "filters": ["department", "status"],
        "columns": ["department", "total", "active", "inactive", "avg_salary", "total_cost"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "empleados_antiguedad": {
        "id": "empleados_antiguedad",
        "name": "Antigüedad de Empleados",
        "description": "Análisis de tiempo de servicio del personal",
        "category": "empleados",
        "filters": ["department", "years_range"],
        "columns": ["name", "department", "hire_date", "years", "months", "vacation_days"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "empleados_rotacion": {
        "id": "empleados_rotacion",
        "name": "Rotación de Personal",
        "description": "Índice de rotación y análisis de bajas",
        "category": "empleados",
        "filters": ["date_range", "department"],
        "columns": ["month", "hires", "terminations", "rotation_rate", "avg_tenure"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "empleados_cumpleanos": {
        "id": "empleados_cumpleanos",
        "name": "Cumpleaños del Mes",
        "description": "Lista de empleados que cumplen años en el período",
        "category": "empleados",
        "filters": ["month"],
        "columns": ["name", "department", "birth_date", "age", "years_service"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "empleados_contratos": {
        "id": "empleados_contratos",
        "name": "Contratos por Vencer",
        "description": "Contratos que expiran próximamente",
        "category": "empleados",
        "filters": ["days_ahead", "contract_type"],
        "columns": ["name", "department", "contract_type", "start_date", "end_date", "days_remaining"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    
    # ========== ASISTENCIA (5 reports) ==========
    "asistencia_diaria": {
        "id": "asistencia_diaria",
        "name": "Resumen de Asistencia Diaria",
        "description": "Estado de asistencia del día actual o fecha específica",
        "category": "asistencia",
        "filters": ["date", "department"],
        "columns": ["name", "department", "shift", "check_in", "check_out", "hours", "status"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "asistencia_tardanzas": {
        "id": "asistencia_tardanzas",
        "name": "Tardanzas y Ausencias",
        "description": "Registro de llegadas tarde y faltas",
        "category": "asistencia",
        "filters": ["date_range", "employee", "department"],
        "columns": ["name", "date", "expected", "actual", "delay_minutes", "type", "justified"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "asistencia_horas_empleado": {
        "id": "asistencia_horas_empleado",
        "name": "Horas Trabajadas por Empleado",
        "description": "Acumulado de horas por empleado en el período",
        "category": "asistencia",
        "filters": ["date_range", "employee", "department"],
        "columns": ["name", "regular_hours", "overtime", "absences", "total_hours", "efficiency"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "asistencia_horas_extras": {
        "id": "asistencia_horas_extras",
        "name": "Horas Extras Acumuladas",
        "description": "Detalle de horas extras por empleado",
        "category": "asistencia",
        "filters": ["date_range", "department"],
        "columns": ["name", "department", "ot_35", "ot_100", "total_ot", "estimated_cost"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "asistencia_tendencia": {
        "id": "asistencia_tendencia",
        "name": "Tendencia de Asistencia Mensual",
        "description": "Evolución de indicadores de asistencia",
        "category": "asistencia",
        "filters": ["date_range", "department"],
        "columns": ["month", "attendance_rate", "punctuality_rate", "absence_rate", "overtime_avg"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    
    # ========== VACACIONES Y PERMISOS (4 reports) ==========
    "vacaciones_balance": {
        "id": "vacaciones_balance",
        "name": "Balance de Vacaciones",
        "description": "Días acumulados, usados y disponibles por empleado",
        "category": "vacaciones",
        "filters": ["department", "status"],
        "columns": ["name", "department", "hire_date", "accrued", "used", "pending", "available"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "vacaciones_pendientes": {
        "id": "vacaciones_pendientes",
        "name": "Solicitudes Pendientes",
        "description": "Solicitudes de vacaciones/permisos por aprobar",
        "category": "vacaciones",
        "filters": ["type", "department"],
        "columns": ["name", "type", "start_date", "end_date", "days", "status", "requested_at"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "vacaciones_historico": {
        "id": "vacaciones_historico",
        "name": "Histórico de Permisos",
        "description": "Registro histórico de todos los permisos otorgados",
        "category": "vacaciones",
        "filters": ["date_range", "employee", "type"],
        "columns": ["name", "type", "start_date", "end_date", "days", "approved_by", "status"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "vacaciones_calendario": {
        "id": "vacaciones_calendario",
        "name": "Calendario de Ausencias",
        "description": "Vista de ausencias programadas por período",
        "category": "vacaciones",
        "filters": ["date_range", "department"],
        "columns": ["date", "employee", "department", "type", "status"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    
    # ========== EVALUACIONES (4 reports) ==========
    "evaluaciones_ciclo": {
        "id": "evaluaciones_ciclo",
        "name": "Resultados por Ciclo",
        "description": "Resumen de evaluaciones de un ciclo específico",
        "category": "evaluaciones",
        "filters": ["cycle", "department"],
        "columns": ["name", "department", "evaluator", "score", "rating", "status", "date"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "evaluaciones_comparativo": {
        "id": "evaluaciones_comparativo",
        "name": "Comparativo de Desempeño",
        "description": "Comparación de resultados entre períodos",
        "category": "evaluaciones",
        "filters": ["employee", "date_range"],
        "columns": ["period", "score", "rating", "strengths", "areas_improvement", "variation"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "evaluaciones_objetivos": {
        "id": "evaluaciones_objetivos",
        "name": "Objetivos y KPIs",
        "description": "Estado de cumplimiento de objetivos",
        "category": "evaluaciones",
        "filters": ["cycle", "employee", "department"],
        "columns": ["employee", "objective", "target", "current", "progress", "due_date", "status"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "evaluaciones_planes": {
        "id": "evaluaciones_planes",
        "name": "Planes de Mejora",
        "description": "Seguimiento de planes de desarrollo",
        "category": "evaluaciones",
        "filters": ["status", "department"],
        "columns": ["employee", "plan", "actions", "progress", "supervisor", "due_date"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    
    # ========== FINANCIERO/CONTABLE (5 reports) ==========
    "financiero_prestamos": {
        "id": "financiero_prestamos",
        "name": "Préstamos Activos",
        "description": "Estado de préstamos a empleados",
        "category": "financiero",
        "filters": ["status", "employee", "department"],
        "columns": ["employee", "amount", "installments", "paid", "remaining", "monthly", "status"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "financiero_gastos": {
        "id": "financiero_gastos",
        "name": "Gastos y Viáticos",
        "description": "Reporte de gastos y reembolsos",
        "category": "financiero",
        "filters": ["date_range", "type", "department", "status"],
        "columns": ["employee", "date", "type", "description", "amount", "status", "approved_by"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "financiero_provisiones": {
        "id": "financiero_provisiones",
        "name": "Provisiones Laborales",
        "description": "Cálculo de provisiones (vacaciones, cesantía, preaviso)",
        "category": "financiero",
        "filters": ["department", "as_of_date"],
        "columns": ["employee", "salary", "vacation_prov", "severance_prov", "notice_prov", "total"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "financiero_asientos": {
        "id": "financiero_asientos",
        "name": "Asientos Contables",
        "description": "Asientos generados por nómina",
        "category": "financiero",
        "filters": ["date_range", "type"],
        "columns": ["date", "account", "description", "debit", "credit", "reference"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "financiero_dgii": {
        "id": "financiero_dgii",
        "name": "Reportes DGII (TSS, IR-17)",
        "description": "Reportes para la Dirección General de Impuestos",
        "category": "financiero",
        "filters": ["period", "report_type"],
        "columns": ["cedula", "name", "salary", "sfs_employee", "sfs_employer", "afp_employee", "afp_employer", "isr"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    
    # ========== RECLUTAMIENTO (6 reports) ==========
    "reclutamiento_pipeline": {
        "id": "reclutamiento_pipeline",
        "name": "Pipeline de Candidatos",
        "description": "Estado actual de candidatos en proceso de selección",
        "category": "reclutamiento",
        "filters": ["position", "status", "date_range"],
        "columns": ["candidate", "position", "stage", "source", "days_in_process", "recruiter", "status"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "reclutamiento_tiempo_contratacion": {
        "id": "reclutamiento_tiempo_contratacion",
        "name": "Tiempo Promedio de Contratación",
        "description": "Análisis de duración del proceso de contratación",
        "category": "reclutamiento",
        "filters": ["date_range", "department", "position"],
        "columns": ["position", "department", "avg_days", "min_days", "max_days", "total_hired", "conversion_rate"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "reclutamiento_fuentes": {
        "id": "reclutamiento_fuentes",
        "name": "Fuentes de Reclutamiento",
        "description": "Efectividad de canales de reclutamiento",
        "category": "reclutamiento",
        "filters": ["date_range"],
        "columns": ["source", "candidates", "interviews", "hired", "conversion_rate", "avg_cost", "quality_score"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "reclutamiento_costos": {
        "id": "reclutamiento_costos",
        "name": "Costos de Reclutamiento",
        "description": "Análisis de inversión en contratación",
        "category": "reclutamiento",
        "filters": ["date_range", "department"],
        "columns": ["department", "positions_filled", "advertising_cost", "agency_fees", "other_costs", "total_cost", "cost_per_hire"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "reclutamiento_vacantes": {
        "id": "reclutamiento_vacantes",
        "name": "Vacantes Activas",
        "description": "Posiciones abiertas pendientes de cubrir",
        "category": "reclutamiento",
        "filters": ["department", "priority", "status"],
        "columns": ["position", "department", "priority", "salary_range", "posted_date", "days_open", "candidates", "status"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "reclutamiento_entrevistas": {
        "id": "reclutamiento_entrevistas",
        "name": "Calendario de Entrevistas",
        "description": "Programación y resultados de entrevistas",
        "category": "reclutamiento",
        "filters": ["date_range", "interviewer", "status"],
        "columns": ["date", "candidate", "position", "interviewer", "type", "result", "notes"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    
    # ========== CAPACITACIÓN (6 reports) ==========
    "capacitacion_horas": {
        "id": "capacitacion_horas",
        "name": "Horas de Capacitación",
        "description": "Horas de formación por empleado y departamento",
        "category": "capacitacion",
        "filters": ["date_range", "department", "employee"],
        "columns": ["employee", "department", "internal_hours", "external_hours", "online_hours", "total_hours", "target", "compliance"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "capacitacion_inversion": {
        "id": "capacitacion_inversion",
        "name": "Inversión en Formación",
        "description": "Costos de capacitación por área y tipo",
        "category": "capacitacion",
        "filters": ["date_range", "department", "training_type"],
        "columns": ["department", "employees_trained", "internal_cost", "external_cost", "total_cost", "cost_per_employee", "roi"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "capacitacion_certificaciones": {
        "id": "capacitacion_certificaciones",
        "name": "Certificaciones por Vencer",
        "description": "Control de certificaciones y renovaciones",
        "category": "capacitacion",
        "filters": ["days_ahead", "certification_type", "department"],
        "columns": ["employee", "certification", "issued_date", "expiry_date", "days_remaining", "renewal_cost", "status"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "capacitacion_plan": {
        "id": "capacitacion_plan",
        "name": "Plan de Capacitación Anual",
        "description": "Programación y avance del plan de formación",
        "category": "capacitacion",
        "filters": ["year", "department", "status"],
        "columns": ["training", "department", "target_employees", "completed", "scheduled_date", "budget", "actual_cost", "status"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "capacitacion_efectividad": {
        "id": "capacitacion_efectividad",
        "name": "Efectividad de Programas",
        "description": "Evaluación de impacto de capacitaciones",
        "category": "capacitacion",
        "filters": ["date_range", "training_type"],
        "columns": ["training", "participants", "pre_score", "post_score", "improvement", "satisfaction", "applied_percentage"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "capacitacion_necesidades": {
        "id": "capacitacion_necesidades",
        "name": "Detección de Necesidades",
        "description": "Análisis de brechas de competencias",
        "category": "capacitacion",
        "filters": ["department", "competency_area"],
        "columns": ["employee", "department", "competency", "current_level", "required_level", "gap", "priority", "recommended_training"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    
    # ========== ANALYTICS Y KPIs (8 reports) ==========
    "analytics_indicadores_rrhh": {
        "id": "analytics_indicadores_rrhh",
        "name": "Dashboard de Indicadores RRHH",
        "description": "KPIs principales de gestión de talento",
        "category": "analytics",
        "filters": ["date_range"],
        "columns": ["indicator", "current_value", "previous_value", "target", "variation", "trend", "status"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "analytics_costo_empleado": {
        "id": "analytics_costo_empleado",
        "name": "Costo Total por Empleado",
        "description": "Análisis integral de costos laborales",
        "category": "analytics",
        "filters": ["department", "position_level"],
        "columns": ["employee", "department", "salary", "benefits", "taxes", "training", "equipment", "total_cost"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "analytics_productividad": {
        "id": "analytics_productividad",
        "name": "Índices de Productividad",
        "description": "Métricas de rendimiento por área",
        "category": "analytics",
        "filters": ["date_range", "department"],
        "columns": ["department", "employees", "output_metric", "hours_worked", "productivity_index", "efficiency", "trend"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "analytics_satisfaccion": {
        "id": "analytics_satisfaccion",
        "name": "Índice de Satisfacción Laboral",
        "description": "Resultados de encuestas de clima",
        "category": "analytics",
        "filters": ["survey_period", "department"],
        "columns": ["department", "participation", "overall_score", "leadership", "environment", "growth", "compensation", "nps"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "analytics_benchmarking": {
        "id": "analytics_benchmarking",
        "name": "Benchmarking Salarial",
        "description": "Comparación con mercado laboral",
        "category": "analytics",
        "filters": ["department", "position"],
        "columns": ["position", "current_salary", "market_min", "market_median", "market_max", "percentile", "competitiveness", "recommendation"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "analytics_headcount": {
        "id": "analytics_headcount",
        "name": "Evolución de Plantilla",
        "description": "Histórico de cambios en headcount",
        "category": "analytics",
        "filters": ["date_range", "department"],
        "columns": ["month", "starting_count", "hires", "terminations", "transfers_in", "transfers_out", "ending_count", "net_change"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "analytics_absentismo": {
        "id": "analytics_absentismo",
        "name": "Análisis de Absentismo",
        "description": "Patrones y costos de ausencias",
        "category": "analytics",
        "filters": ["date_range", "department", "absence_type"],
        "columns": ["department", "total_absences", "sick_days", "personal_days", "unjustified", "absence_rate", "estimated_cost", "trend"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "analytics_diversidad": {
        "id": "analytics_diversidad",
        "name": "Métricas de Diversidad",
        "description": "Indicadores de inclusión y equidad",
        "category": "analytics",
        "filters": ["department"],
        "columns": ["metric", "male", "female", "other", "total", "female_percentage", "leadership_female", "pay_gap"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    
    # ========== CUMPLIMIENTO LEGAL (6 reports) ==========
    "cumplimiento_documentos": {
        "id": "cumplimiento_documentos",
        "name": "Estado de Documentos Legales",
        "description": "Verificación de documentación requerida",
        "category": "cumplimiento",
        "filters": ["document_type", "status", "department"],
        "columns": ["employee", "document", "required", "uploaded", "expiry_date", "days_remaining", "status"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "cumplimiento_contratos": {
        "id": "cumplimiento_contratos",
        "name": "Auditoría de Contratos",
        "description": "Estado y cumplimiento de contratos laborales",
        "category": "cumplimiento",
        "filters": ["contract_type", "status"],
        "columns": ["employee", "contract_type", "start_date", "end_date", "signed", "registered_mt", "amendments", "status"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "cumplimiento_auditoria": {
        "id": "cumplimiento_auditoria",
        "name": "Auditoría de Datos de Empleados",
        "description": "Verificación de información completa",
        "category": "cumplimiento",
        "filters": ["department", "completeness_threshold"],
        "columns": ["employee", "personal_data", "contact_info", "bank_info", "documents", "emergency_contact", "completeness", "missing_items"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "cumplimiento_vencimientos": {
        "id": "cumplimiento_vencimientos",
        "name": "Calendario de Vencimientos",
        "description": "Próximas fechas críticas y renovaciones",
        "category": "cumplimiento",
        "filters": ["days_ahead", "type"],
        "columns": ["type", "description", "related_to", "due_date", "days_remaining", "responsible", "priority", "action_required"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "cumplimiento_checklist": {
        "id": "cumplimiento_checklist",
        "name": "Checklist de Cumplimiento",
        "description": "Estado de obligaciones laborales",
        "category": "cumplimiento",
        "filters": ["category"],
        "columns": ["requirement", "category", "frequency", "last_completed", "next_due", "responsible", "status", "evidence"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    },
    "cumplimiento_seguridad_social": {
        "id": "cumplimiento_seguridad_social",
        "name": "Registro Seguridad Social",
        "description": "Estado de afiliaciones TSS",
        "category": "cumplimiento",
        "filters": ["status"],
        "columns": ["employee", "cedula", "nss", "afp", "ars", "registration_date", "status", "last_payment"],
        "supports_preview": True,
        "supports_pdf": True,
        "supports_excel": True
    }
}


