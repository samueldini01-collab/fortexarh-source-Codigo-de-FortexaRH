import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Shield, ArrowLeft } from "lucide-react";

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <img src="/favicon.png" alt="FortexaRH" className="h-8 w-8" />
            <span className="font-bold text-slate-800">FortexaRH</span>
          </Link>
          <Link to="/">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Volver
            </Button>
          </Link>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-12">
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 md:p-12">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-12 h-12 rounded-xl bg-blue-100 flex items-center justify-center">
              <Shield className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-slate-900">Política de Privacidad</h1>
              <p className="text-slate-500">Última actualización: Enero 2025</p>
            </div>
          </div>

          <div className="prose prose-slate max-w-none">
            <p className="text-slate-600 mb-6">
              En FortexaRH, operado por Cloudtexa Solutions SRL, nos comprometemos a proteger su privacidad y la de sus empleados. Esta Política de Privacidad describe cómo recopilamos, usamos, almacenamos y protegemos su información personal, en cumplimiento con la Ley 172-13 sobre Protección de Datos de Carácter Personal de la República Dominicana.
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">1. Información que Recopilamos</h2>
            <p className="text-slate-600 mb-4">Recopilamos los siguientes tipos de información:</p>
            
            <h3 className="text-lg font-medium text-slate-800 mt-4 mb-2">Datos de la Empresa</h3>
            <ul className="list-disc pl-6 text-slate-600 mb-4">
              <li>Nombre comercial y razón social</li>
              <li>RNC (Registro Nacional del Contribuyente)</li>
              <li>Dirección física y de correspondencia</li>
              <li>Información de contacto empresarial</li>
              <li>Datos bancarios para procesamiento de nómina</li>
            </ul>

            <h3 className="text-lg font-medium text-slate-800 mt-4 mb-2">Datos de Empleados</h3>
            <ul className="list-disc pl-6 text-slate-600 mb-4">
              <li>Nombre completo y cédula de identidad</li>
              <li>Fecha de nacimiento y estado civil</li>
              <li>Dirección y datos de contacto</li>
              <li>Información laboral (cargo, salario, fecha de ingreso)</li>
              <li>Número de Seguro Social (NSS)</li>
              <li>Datos bancarios para depósito de nómina</li>
              <li>Información de dependientes para fines de DGII</li>
            </ul>

            <h3 className="text-lg font-medium text-slate-800 mt-4 mb-2">Datos de Uso</h3>
            <ul className="list-disc pl-6 text-slate-600 mb-4">
              <li>Registros de acceso al sistema</li>
              <li>Dirección IP y tipo de navegador</li>
              <li>Páginas visitadas y acciones realizadas</li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">2. Cómo Usamos la Información</h2>
            <p className="text-slate-600 mb-4">Utilizamos su información para:</p>
            <ul className="list-disc pl-6 text-slate-600 mb-4">
              <li>Proveer y mantener el Servicio de gestión de RRHH y nómina</li>
              <li>Calcular y procesar nóminas conforme a la legislación dominicana</li>
              <li>Generar archivos requeridos por la TSS y DGII</li>
              <li>Notificarle sobre cambios en el Servicio</li>
              <li>Brindar soporte técnico</li>
              <li>Mejorar y personalizar el Servicio</li>
              <li>Cumplir con obligaciones legales y regulatorias</li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">3. Base Legal para el Procesamiento</h2>
            <p className="text-slate-600 mb-4">
              Procesamos sus datos personales conforme a la Ley 172-13 bajo las siguientes bases legales:
            </p>
            <ul className="list-disc pl-6 text-slate-600 mb-4">
              <li><strong>Consentimiento:</strong> Cuando usted nos proporciona sus datos al registrarse</li>
              <li><strong>Ejecución contractual:</strong> Para cumplir con nuestras obligaciones del servicio</li>
              <li><strong>Obligación legal:</strong> Para cumplir con requerimientos de TSS, DGII y otras entidades</li>
              <li><strong>Interés legítimo:</strong> Para mejorar nuestros servicios y prevenir fraudes</li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">4. Compartir Información</h2>
            <p className="text-slate-600 mb-4">
              Podemos compartir su información únicamente en los siguientes casos:
            </p>
            <ul className="list-disc pl-6 text-slate-600 mb-4">
              <li><strong>Entidades gubernamentales:</strong> TSS, DGII, Ministerio de Trabajo cuando sea requerido por ley</li>
              <li><strong>Proveedores de servicios:</strong> Procesadores de pago, servicios de alojamiento en la nube (con acuerdos de confidencialidad)</li>
              <li><strong>Con su consentimiento:</strong> Cuando usted nos autorice expresamente</li>
              <li><strong>Por orden judicial:</strong> Cuando sea requerido por autoridad competente</li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">5. Seguridad de Datos</h2>
            <p className="text-slate-600 mb-4">
              Implementamos medidas de seguridad técnicas y organizativas para proteger su información:
            </p>
            <ul className="list-disc pl-6 text-slate-600 mb-4">
              <li>Encriptación SSL/TLS para transmisión de datos</li>
              <li>Encriptación de datos sensibles en reposo</li>
              <li>Acceso restringido basado en roles</li>
              <li>Auditorías de seguridad periódicas</li>
              <li>Respaldos automáticos diarios</li>
              <li>Autenticación de dos factores (disponible)</li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">6. Derechos del Usuario (ARCO)</h2>
            <p className="text-slate-600 mb-4">
              Conforme a la Ley 172-13, usted tiene los siguientes derechos:
            </p>
            <ul className="list-disc pl-6 text-slate-600 mb-4">
              <li><strong>Acceso:</strong> Solicitar una copia de sus datos personales</li>
              <li><strong>Rectificación:</strong> Corregir datos inexactos o incompletos</li>
              <li><strong>Cancelación:</strong> Solicitar la eliminación de sus datos</li>
              <li><strong>Oposición:</strong> Oponerse al procesamiento de sus datos</li>
            </ul>
            <p className="text-slate-600 mb-4">
              Para ejercer estos derechos, envíe un correo a: <strong>privacidad@fortexarh.com</strong>
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">7. Retención de Datos</h2>
            <p className="text-slate-600 mb-4">
              Conservamos sus datos durante el tiempo necesario para cumplir con los fines descritos en esta política y según lo exija la legislación dominicana:
            </p>
            <ul className="list-disc pl-6 text-slate-600 mb-4">
              <li>Registros de nómina: 10 años (según Código de Trabajo)</li>
              <li>Documentos fiscales: 10 años (según Código Tributario)</li>
              <li>Datos de cuenta: Durante la vigencia del servicio + 2 años</li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">8. Cookies y Tecnologías Similares</h2>
            <p className="text-slate-600 mb-4">
              Utilizamos cookies para:
            </p>
            <ul className="list-disc pl-6 text-slate-600 mb-4">
              <li>Mantener su sesión activa</li>
              <li>Recordar sus preferencias</li>
              <li>Analizar el uso del servicio</li>
            </ul>
            <p className="text-slate-600 mb-4">
              Puede configurar su navegador para rechazar cookies, aunque esto puede afectar la funcionalidad del Servicio.
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">9. Transferencias Internacionales</h2>
            <p className="text-slate-600 mb-4">
              Sus datos pueden ser almacenados en servidores ubicados fuera de la República Dominicana. En tales casos, nos aseguramos de que existan garantías adecuadas de protección conforme a la Ley 172-13.
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">10. Cambios en la Política</h2>
            <p className="text-slate-600 mb-4">
              Podemos actualizar esta Política de Privacidad periódicamente. Le notificaremos sobre cambios significativos mediante correo electrónico o aviso en el Servicio. Le recomendamos revisar esta política regularmente.
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">11. Contacto</h2>
            <p className="text-slate-600 mb-4">
              Para consultas sobre privacidad o ejercer sus derechos ARCO:
            </p>
            <div className="bg-slate-50 p-4 rounded-lg text-slate-600">
              <p><strong>Oficial de Protección de Datos</strong></p>
              <p>Cloudtexa Solutions SRL</p>
              <p>Av. Winston Churchill, Santo Domingo, República Dominicana</p>
              <p>Email: privacidad@fortexarh.com</p>
              <p>Teléfono: (809) 685-9898</p>
            </div>

            <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-blue-800 text-sm">
                <strong>Nota:</strong> Esta política cumple con la Ley 172-13 sobre Protección de Datos de Carácter Personal de la República Dominicana y sus reglamentos de aplicación.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
