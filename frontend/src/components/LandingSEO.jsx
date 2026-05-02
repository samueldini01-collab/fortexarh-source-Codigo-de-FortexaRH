/**
 * LandingSEO — dynamic meta tags, OpenGraph, and hreflang per country/language.
 */
import { Helmet } from "react-helmet-async";

const COUNTRY_SLUGS = {
  DO: "republica-dominicana", CU: "cuba", HT: "haiti", PR: "puerto-rico",
  CR: "costa-rica", SV: "el-salvador", GT: "guatemala", HN: "honduras",
  NI: "nicaragua", PA: "panama", MX: "mexico", US: "estados-unidos", CA: "canada",
  CO: "colombia", AR: "argentina", CL: "chile", PE: "peru", EC: "ecuador",
  VE: "venezuela", BO: "bolivia", PY: "paraguay", UY: "uruguay", GY: "guyana",
  SR: "surinam", BR: "brasil",
  ES: "espana", GB: "reino-unido", FR: "francia", BE: "belgica",
};

export { COUNTRY_SLUGS };

export function slugToCountry(slug) {
  if (!slug) return null;
  const lower = slug.toLowerCase();
  for (const [code, s] of Object.entries(COUNTRY_SLUGS)) {
    if (s === lower) return code;
  }
  // Accept direct codes too (e.g. /country/MX)
  if (lower.length === 2 && COUNTRY_SLUGS[lower.toUpperCase()]) {
    return lower.toUpperCase();
  }
  return null;
}

export default function LandingSEO({ profile, countryCode, lang = "es" }) {
  const baseUrl = typeof window !== "undefined" ? window.location.origin : "https://fortexarh.com";
  const slug = COUNTRY_SLUGS[countryCode];
  const canonical = slug ? `${baseUrl}/pais/${slug}` : baseUrl;
  const countryName = profile?.name || "República Dominicana";

  const titles = {
    es: `FortexaRH · Software de Nómina y RRHH para ${countryName}`,
    en: `FortexaRH · HR & Payroll Software for ${countryName}`,
    fr: `FortexaRH · Logiciel RH & Paie pour ${countryName}`,
    pt: `FortexaRH · Software de RH e Folha para ${countryName}`,
  };

  const descriptions = {
    es: `Automatiza nómina con motor fiscal nativo para ${countryName}. Calcula deducciones, genera reportes oficiales y cumple con todas las leyes locales. Prueba gratis 30 días.`,
    en: `Automate payroll with native fiscal engine for ${countryName}. Calculate deductions, generate official reports and stay compliant with all local laws. Free 30-day trial.`,
    fr: `Automatisez la paie avec le moteur fiscal natif pour ${countryName}. Calculez les déductions, générez des rapports officiels et respectez toutes les lois locales. Essai gratuit de 30 jours.`,
    pt: `Automatize a folha com motor fiscal nativo para ${countryName}. Calcule deduções, gere relatórios oficiais e cumpra todas as leis locais. Teste grátis por 30 dias.`,
  };

  const title = titles[lang] || titles.es;
  const description = descriptions[lang] || descriptions.es;

  return (
    <Helmet>
      <html lang={lang} />
      <title>{title}</title>
      <meta name="description" content={description} />
      <link rel="canonical" href={canonical} />

      {/* Hreflang for all supported country+language combinations */}
      {slug && ["es", "en", "fr", "pt"].map((l) => (
        <link
          key={l}
          rel="alternate"
          hrefLang={l}
          href={`${baseUrl}/pais/${slug}?lang=${l}`}
        />
      ))}
      <link rel="alternate" hrefLang="x-default" href={baseUrl} />

      {/* OpenGraph */}
      <meta property="og:type" content="website" />
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:url" content={canonical} />
      <meta property="og:locale" content={`${lang}_${countryCode || "DO"}`} />

      {/* Twitter */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={title} />
      <meta name="twitter:description" content={description} />

      {/* Structured data (JSON-LD) */}
      <script type="application/ld+json">
        {JSON.stringify({
          "@context": "https://schema.org",
          "@type": "SoftwareApplication",
          name: "FortexaRH",
          applicationCategory: "BusinessApplication",
          operatingSystem: "Web",
          description,
          url: canonical,
          offers: {
            "@type": "Offer",
            priceCurrency: profile?.currency || "USD",
            availability: "https://schema.org/InStock",
          },
          areaServed: {
            "@type": "Country",
            name: countryName,
          },
        })}
      </script>
    </Helmet>
  );
}
