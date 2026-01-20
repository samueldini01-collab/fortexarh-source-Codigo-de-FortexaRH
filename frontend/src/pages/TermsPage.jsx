import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { FileText, ArrowLeft } from "lucide-react";

export default function TermsPage() {
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
            <div className="w-12 h-12 rounded-xl bg-emerald-100 flex items-center justify-center">
              <FileText className="w-6 h-6 text-emerald-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-slate-900">Términos de Servicio</h1>
              <p className="text-slate-500">Última actualización: Enero 2025</p>
            </div>
          </div>

          <div className="prose prose-slate max-w-none">
            <p className="text-slate-600 mb-6">
              Bienvenido a FortexaRH. Estos Términos de Servicio ("Términos") rigen su uso del software de gestión de recursos humanos y nómina FortexaRH ("Servicio"), operado por Cloudtexa Solutions SRL ("Nosotros", "Nuestro" o "la Empresa"), una empresa constituida bajo las leyes de la República Dominicana.
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">1. Aceptación de Términos</h2>
            <p className="text-slate-600 mb-4">
              Al acceder o utilizar nuestro Servicio, usted acepta estar sujeto a estos Términos. Si no está de acuerdo con alguna parte de estos términos, no podrá acceder al Servicio. Estos términos se rigen por las leyes de la República Dominicana, incluyendo pero no limitado a:
            </p>
            <ul className="list-disc pl-6 text-slate-600 mb-4">
              <li>Código de Trabajo de la República Dominicana (Ley 16-92)</li>
              <li>Ley General de Protección de los Derechos del Consumidor o Usuario (Ley 358-05)</li>
              <li>Ley sobre Comercio Electrónico, Documentos y Firmas Digitales (Ley 126-02)</li>
              <li>Ley Orgánica sobre Protección de Datos de Carácter Personal (Ley 172-13)</li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">2. Descripción del Servicio</h2>
            <p className="text-slate-600 mb-4">
              FortexaRH es una plataforma de software como servicio (SaaS) que proporciona:
            </p>
            <ul className="list-disc pl-6 text-slate-600 mb-4">
              <li>Gestión de empleados y expedientes laborales</li>
              <li>Procesamiento y cálculo de nóminas conforme a la legislación dominicana</li>
              <li>Generación de archivos TSS (Tesorería de la Seguridad Social)</li>
              <li>Control de asistencias y vacaciones</li>
              <li>Reportes y formularios requeridos por la DGII</li>
              <li>Organigrama y estructura organizacional</li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">3. Licencia de Uso</h2>
            <p className="text-slate-600 mb-4">
              Sujeto al cumplimiento de estos Términos y al pago de las tarifas aplicables, le otorgamos una licencia limitada, no exclusiva, no transferible y revocable para acceder y utilizar el Servicio únicamente para sus operaciones comerciales internas.
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">4. Restricciones de Uso</h2>
            <p className="text-slate-600 mb-4">Usted se compromete a NO:</p>
            <ul className="list-disc pl-6 text-slate-600 mb-4">
              <li>Copiar, modificar, distribuir, vender o arrendar ninguna parte del Servicio</li>
              <li>Realizar ingeniería inversa o intentar extraer el código fuente</li>
              <li>Usar el Servicio para actividades ilegales o fraudulentas</li>
              <li>Interferir con la seguridad o integridad del Servicio</li>
              <li>Compartir credenciales de acceso con terceros no autorizados</li>
              <li>Procesar datos de nómina que no correspondan a empleados legítimos de su empresa</li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">5. Propiedad Intelectual</h2>
            <p className="text-slate-600 mb-4">
              El Servicio y su contenido original, características y funcionalidad son y seguirán siendo propiedad exclusiva de Cloudtexa Solutions SRL y sus licenciantes. El Servicio está protegido por las leyes de propiedad intelectual de la República Dominicana, tratados internacionales y otras leyes aplicables.
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">6. Datos y Confidencialidad</h2>
            <p className="text-slate-600 mb-4">
              Usted es responsable de la exactitud y legalidad de los datos que ingresa al sistema. Nos comprometemos a mantener la confidencialidad de su información conforme a nuestra Política de Privacidad y la Ley 172-13 sobre Protección de Datos Personales.
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">7. Tarifas y Pagos</h2>
            <p className="text-slate-600 mb-4">
              Las tarifas del Servicio se cobran mensualmente según el plan seleccionado. Los pagos se procesan en Dólares Estadounidenses (USD) o Pesos Dominicanos (DOP) según corresponda. El incumplimiento de pago puede resultar en la suspensión del acceso al Servicio.
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">8. Limitación de Responsabilidad</h2>
            <p className="text-slate-600 mb-4">
              En ningún caso Cloudtexa Solutions SRL, sus directores, empleados o agentes serán responsables por daños indirectos, incidentales, especiales, consecuentes o punitivos que resulten del uso o la imposibilidad de uso del Servicio. Nuestra responsabilidad máxima estará limitada al monto pagado por usted en los últimos 12 meses por el Servicio.
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">9. Indemnización</h2>
            <p className="text-slate-600 mb-4">
              Usted acepta indemnizar y mantener indemne a Cloudtexa Solutions SRL de cualquier reclamo, daño, pérdida, responsabilidad y gastos (incluyendo honorarios de abogados) que surjan de su uso del Servicio o violación de estos Términos.
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">10. Terminación</h2>
            <p className="text-slate-600 mb-4">
              Podemos terminar o suspender su acceso inmediatamente, sin previo aviso, por cualquier razón, incluyendo el incumplimiento de estos Términos. Tras la terminación, su derecho a usar el Servicio cesará inmediatamente. Podrá solicitar una copia de sus datos dentro de los 30 días siguientes a la terminación.
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">11. Cambios en los Términos</h2>
            <p className="text-slate-600 mb-4">
              Nos reservamos el derecho de modificar estos Términos en cualquier momento. Le notificaremos sobre cambios sustanciales mediante correo electrónico o aviso en el Servicio con al menos 30 días de anticipación. Su uso continuado del Servicio después de la entrada en vigor de los cambios constituye su aceptación de los nuevos términos.
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">12. Ley Aplicable y Jurisdicción</h2>
            <p className="text-slate-600 mb-4">
              Estos Términos se regirán e interpretarán de acuerdo con las leyes de la República Dominicana, sin tener en cuenta sus disposiciones sobre conflictos de leyes. Cualquier disputa que surja en relación con estos Términos será sometida a la jurisdicción exclusiva de los tribunales competentes del Distrito Nacional, República Dominicana.
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">13. Contacto</h2>
            <p className="text-slate-600 mb-4">
              Si tiene preguntas sobre estos Términos, contáctenos:
            </p>
            <div className="bg-slate-50 p-4 rounded-lg text-slate-600">
              <p><strong>Cloudtexa Solutions SRL</strong></p>
              <p>Av. Winston Churchill, Santo Domingo, República Dominicana</p>
              <p>Email: info@fortexarh.com</p>
              <p>Teléfono: (809) 685-9898</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
