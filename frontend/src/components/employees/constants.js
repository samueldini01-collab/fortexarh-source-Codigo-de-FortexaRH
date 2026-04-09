export const departments = ["Administración", "Ventas", "Marketing", "TI", "Recursos Humanos", "Finanzas", "Operaciones", "Legal", "Producción", "Logística"];
export const documentTypes = ["Cédula", "Pasaporte", "Residencia"];
export const genders = ["Masculino", "Femenino"];
export const maritalStatuses = ["Soltero/a", "Casado/a", "Divorciado/a", "Viudo/a", "Unión Libre"];
export const contractTypes = ["Indefinido", "Temporal", "Por Obra", "Pasantía", "Medio Tiempo"];
export const paymentMethods = ["Transferencia Bancaria", "Cheque", "Efectivo"];
export const paymentFrequencies = ["Quincenal", "Mensual", "Semanal"];
export const deductionTypes = ["Préstamo Empresa", "Préstamo Cooperativa", "Seguro Adicional", "Pensión Alimenticia", "Embargo", "Otro"];
export const relationshipTypes = ["Esposo/a", "Padre", "Madre", "Hijo/a", "Hermano/a", "Amigo/a", "Otro"];
export const bloodTypes = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"];
export const countries = [
  "República Dominicana", "Estados Unidos", "España", "México", "Colombia", "Venezuela", "Argentina", "Chile", 
  "Perú", "Ecuador", "Cuba", "Puerto Rico", "Haití", "Brasil", "Panamá", "Costa Rica", "Guatemala", 
  "Honduras", "El Salvador", "Nicaragua", "Paraguay", "Uruguay", "Bolivia", "Canadá", "Francia", 
  "Alemania", "Italia", "Reino Unido", "Portugal", "China", "Japón", "Corea del Sur", "India", "Otro"
];

export const initialFormData = {
  first_name: "",
  last_name: "",
  email: "",
  phone: "",
  whatsapp: "",
  nationality: "República Dominicana",
  document_type: "Cédula",
  document_number: "",
  gender: "",
  birth_date: "",
  marital_status: "Soltero/a",
  blood_type: "",
  weight: "",
  height: "",
  status: "active",
  address: "",
  city: "Santo Domingo",
  photo_url: "",
  position: "",
  department: "",
  hire_date: "",
  contract_type: "Indefinido",
  contract_end_date: "",
  salary: "",
  supervisor: "",
  work_schedule: "Lunes a Viernes 8:00 AM - 5:00 PM",
  exclude_from_payroll: false,
  last_raise_date: "",
  afp_discount: true,
  sfs_discount: true,
  isr_discount: true,
  sfs_manual_override: false,
  sfs_manual_amount: "",
  afp_manual_override: false,
  afp_manual_amount: "",
  isr_manual_override: false,
  isr_manual_amount: "",
  additional_deductions: [],
  payment_method: "Transferencia Bancaria",
  payment_frequency: "Quincenal",
  bank_name: "",
  account_type: "Ahorros",
  account_number: "",
  emergency_contacts: []
};

export const initialDeductionForm = {
  type: "Préstamo Empresa",
  description: "",
  amount: "",
  is_percentage: false
};

export const initialEmergencyContactForm = {
  name: "",
  relationship: "",
  phone: "",
  whatsapp: "",
  address: ""
};
