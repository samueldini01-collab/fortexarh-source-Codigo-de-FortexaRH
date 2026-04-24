import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Shield, ArrowLeft } from "lucide-react";

export default function PrivacyPage() {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <img src="/favicon.png" alt="FortexaRH" className="h-8 w-8" />
            <span className="font-bold text-slate-800">{t('privacy.fortexarh')}</span>
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
              <h1 className="text-3xl font-bold text-slate-900">{t('privacy.politicaDePrivacidad')}</h1>
              <p className="text-slate-500">{t('privacy.ultimaActualizacionEnero2025')}</p>
            </div>
          </div>

          <div className="prose prose-slate max-w-none">
            <p className="text-slate-600 mb-6">
              En FortexaRH, operado por Cloudtexa Solutions SRL, nos comprometemos a proteger su privacidad y la de sus empleados. Esta Política de Privacidad describe cómo recopilamos, usamos, almacenamos y protegemos su información personal, en cumplimiento con la Ley 172-13 sobre Protección de Datos de Carácter Personal de la República Dominicana.
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">1. Información que Recopilamos</h2>
            <p className="text-slate-600 mb-4">{t('privacy.recopilamosLosSiguientesTipos')}</p>
            
            <h3 className="text-lg font-medium text-slate-800 mt-4 mb-2">{t('privacy.datosDeLaEmpresa')}</h3>
            <ul className="list-disc pl-6 text-slate-600 mb-4">
              <li>{t('privacy.nombreComercialYRazon')}</li>
              <li>{t('privacy.rncRegistroNacionalDel')}</li>
              <li>{t('privacy.direccionFisicaYDe')}</li>
              <li>{t('privacy.informacionDeContactoEmpresarial')}</li>
              <li>{t('privacy.datosBancariosParaProcesamiento')}</li>
            </ul>

            <h3 className="text-lg font-medium text-slate-800 mt-4 mb-2">{t('privacy.datosDeEmpleados')}</h3>
            <ul className="list-disc pl-6 text-slate-600 mb-4">
              <li>{t('privacy.nombreCompletoYCedula')}</li>
              <li>{t('privacy.fechaDeNacimientoY')}</li>
              <li>{t('privacy.direccionYDatosDe')}</li>
              <li>{t('privacy.informacionLaboralCargoSalario')}</li>
              <li>{t('privacy.numeroDeSeguroSocial')}</li>
              <li>{t('privacy.datosBancariosParaDeposito')}</li>
              <li>{t('privacy.informacionDeDependientesPara')}</li>
            </ul>

            <h3 className="text-lg font-medium text-slate-800 mt-4 mb-2">{t('privacy.datosDeUso')}</h3>
            <ul className="list-disc pl-6 text-slate-600 mb-4">
              <li>{t('privacy.registrosDeAccesoAl')}</li>
              <li>{t('privacy.direccionIpYTipo')}</li>
              <li>{t('privacy.paginasVisitadasYAcciones')}</li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">2. Cómo Usamos la Información</h2>
            <p className="text-slate-600 mb-4">{t('privacy.utilizamosSuInformacionPara')}</p>
            <ul className="list-disc pl-6 text-slate-600 mb-4">
              <li>{t('privacy.proveerYMantenerEl')}</li>
              <li>{t('privacy.calcularYProcesarNominas')}</li>
              <li>{t('privacy.generarArchivosRequeridosPor')}</li>
              <li>{t('privacy.notificarleSobreCambiosEn')}</li>
              <li>{t('privacy.brindarSoporteTecnico')}</li>
              <li>{t('privacy.mejorarYPersonalizarEl')}</li>
              <li>{t('privacy.cumplirConObligacionesLegales')}</li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">3. Base Legal para el Procesamiento</h2>
            <p className="text-slate-600 mb-4">
              Procesamos sus datos personales conforme a la Ley 172-13 bajo las siguientes bases legales:
            </p>
            <ul className="list-disc pl-6 text-slate-600 mb-4">
              <li><strong>{t('privacy.consentimiento')}</strong> Cuando usted nos proporciona sus datos al registrarse</li>
              <li><strong>{t('privacy.ejecucionContractual')}</strong> Para cumplir con nuestras obligaciones del servicio</li>
              <li><strong>{t('privacy.obligacionLegal')}</strong> Para cumplir con requerimientos de TSS, DGII y otras entidades</li>
              <li><strong>{t('privacy.interesLegitimo')}</strong> Para mejorar nuestros servicios y prevenir fraudes</li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">4. Compartir Información</h2>
            <p className="text-slate-600 mb-4">
              Podemos compartir su información únicamente en los siguientes casos:
            </p>
            <ul className="list-disc pl-6 text-slate-600 mb-4">
              <li><strong>{t('privacy.entidadesGubernamentales')}</strong> TSS, DGII, Ministerio de Trabajo cuando sea requerido por ley</li>
              <li><strong>{t('privacy.proveedoresDeServicios')}</strong> Procesadores de pago, servicios de alojamiento en la nube (con acuerdos de confidencialidad)</li>
              <li><strong>{t('privacy.conSuConsentimiento')}</strong> Cuando usted nos autorice expresamente</li>
              <li><strong>{t('privacy.porOrdenJudicial')}</strong> Cuando sea requerido por autoridad competente</li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">5. Seguridad de Datos</h2>
            <p className="text-slate-600 mb-4">
              Implementamos medidas de seguridad técnicas y organizativas para proteger su información:
            </p>
            <ul className="list-disc pl-6 text-slate-600 mb-4">
              <li>{t('privacy.encriptacionSsltlsParaTransmision')}</li>
              <li>{t('privacy.encriptacionDeDatosSensibles')}</li>
              <li>{t('privacy.accesoRestringidoBasadoEn')}</li>
              <li>{t('privacy.auditoriasDeSeguridadPeriodicas')}</li>
              <li>{t('privacy.respaldosAutomaticosDiarios')}</li>
              <li>{t('privacy.autenticacionDeDosFactores')}</li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">6. Derechos del Usuario (ARCO)</h2>
            <p className="text-slate-600 mb-4">
              Conforme a la Ley 172-13, usted tiene los siguientes derechos:
            </p>
            <ul className="list-disc pl-6 text-slate-600 mb-4">
              <li><strong>{t('privacy.acceso')}</strong> Solicitar una copia de sus datos personales</li>
              <li><strong>{t('privacy.rectificacion')}</strong> Corregir datos inexactos o incompletos</li>
              <li><strong>{t('privacy.cancelacion')}</strong> Solicitar la eliminación de sus datos</li>
              <li><strong>{t('privacy.oposicion')}</strong> Oponerse al procesamiento de sus datos</li>
            </ul>
            <p className="text-slate-600 mb-4">
              Para ejercer estos derechos, envíe un correo a: <strong>privacidad@fortexaerp.com</strong>
            </p>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">7. Retención de Datos</h2>
            <p className="text-slate-600 mb-4">
              Conservamos sus datos durante el tiempo necesario para cumplir con los fines descritos en esta política y según lo exija la legislación dominicana:
            </p>
            <ul className="list-disc pl-6 text-slate-600 mb-4">
              <li>{t('privacy.registrosDeNomina10')}</li>
              <li>{t('privacy.documentosFiscales10Anos')}</li>
              <li>{t('privacy.datosDeCuentaDurante')}</li>
            </ul>

            <h2 className="text-xl font-semibold text-slate-900 mt-8 mb-4">8. Cookies y Tecnologías Similares</h2>
            <p className="text-slate-600 mb-4">
              Utilizamos cookies para:
            </p>
            <ul className="list-disc pl-6 text-slate-600 mb-4">
              <li>{t('privacy.mantenerSuSesionActiva')}</li>
              <li>{t('privacy.recordarSusPreferencias')}</li>
              <li>{t('privacy.analizarElUsoDel')}</li>
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
              <p><strong>{t('privacy.oficialDeProteccionDe')}</strong></p>
              <p>{t('privacy.cloudtexaSolutionsSrl')}</p>
              <p>{t('privacy.avWinstonChurchillSanto')}</p>
              <p>{t('privacy.emailPrivacidadfortexarhcom')}</p>
              <p>{t('privacy.telefono8096859898')}</p>
            </div>

            <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-blue-800 text-sm">
                <strong>{t('privacy.nota')}</strong> Esta política cumple con la Ley 172-13 sobre Protección de Datos de Carácter Personal de la República Dominicana y sus reglamentos de aplicación.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
