# FortexaRH - Sistema SaaS de RRHH y Nómina

## Última Actualización: 2026-01-20

## Resumen del Proyecto
Sistema completo de gestión de Recursos Humanos y Nómina para República Dominicana, vendido por suscripción mensual.

## Arquitectura del Sistema

### Backend (FastAPI + MongoDB)
```
/app/backend/
├── server.py           # API principal (~5,244 líneas - REFACTORIZADO)
├── routes/             # Routers modulares
│   ├── auth.py         # Autenticación, login, reset password
│   ├── employees.py    # CRUD empleados
│   ├── payroll.py      # Nómina básica
│   ├── attendance.py   # Asistencias
│   ├── vacations.py    # Vacaciones
│   ├── evaluations.py  # Evaluaciones
│   ├── recruitment.py  # Jobs y candidates
│   ├── organigrama.py  # Organigrama
│   ├── company.py      # Configuración empresa
│   ├── dashboard.py    # Estadísticas dashboard
│   ├── accounting.py   # Contabilidad con catálogos
│   ├── system_users.py # Usuarios del sistema
│   ├── dgii_reports.py # Reportes DGII (TSS, ISR)
│   ├── loans.py        # Préstamos a empleados
│   └── ... más routers
├── services/
│   └── pdf_service.py  # Generación PDFs
└── email_service.py    # Servicio correos
```

### Frontend (React + Tailwind + Shadcn)
Logo de FortexaRH agregado al sidebar (`/fortexarh-icon-128.png`)

## Lo Implementado en Esta Sesión (2026-01-20)

### ✅ 1. Logo de FortexaRH en Landing Page y Sidebar - COMPLETADO
- Logo oficial agregado al header de la landing page (`/fortexarh-logo-300.png`)
- Logo optimizado en el sidebar del dashboard (`/fortexarh-icon-128.png`)
- Imágenes en múltiples tamaños para diferentes usos

### ✅ 2. Landing Page y Sistema Responsive - COMPLETADO
- **Header responsive**: Logo escalable, menú hamburguesa en móvil
- **Hero section**: Layout adaptativo, botones a ancho completo en móvil
- **Features/Benefits**: Grid responsive (1-2-3 columnas según pantalla)
- **Dashboard móvil**: Sidebar oculto con botón menú, contenido adaptativo
- Probado en: Desktop (1920px), Tablet (768px), Mobile (375px)

### ✅ 3. Refactorización de server.py - COMPLETADO
- Reducido de 6,485 a 5,244 líneas (-19%)
- Endpoints movidos a routers modulares

## Tareas Pendientes

### P1 - Alta Prioridad
1. Notificaciones Automáticas (emails)

### P2 - Media Prioridad
1. Corregir advertencias ESLint
2. Integraciones Enterprise (MOCKED)

## Credenciales de Prueba
- Usuario: test_refactor@fortexa.com
- Contraseña: test123
- Plan: Pro
