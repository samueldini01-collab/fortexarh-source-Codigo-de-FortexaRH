/**
 * Official bank lists per country where FortexaRH operates.
 *
 * For DR we include the SUIR+/Banreservas ACH "bank_code" because the
 * Banreservas TXT/XLSX exports need it. For other countries the code
 * is optional (left blank = free text).
 */

export const DOMINICAN_BANKS = [
  { code: "002", name: "Banco de Reservas (Banreservas)" },
  { code: "014", name: "Banco BHD (BHD León)" },
  { code: "008", name: "Banco Popular Dominicano" },
  { code: "017", name: "Scotiabank República Dominicana" },
  { code: "012", name: "Banco del Progreso" },
  { code: "009", name: "Citibank N.A." },
  { code: "021", name: "Banco Santa Cruz" },
  { code: "025", name: "Banco Caribe" },
  { code: "026", name: "Banco Vimenca" },
  { code: "029", name: "Banco BDI" },
  { code: "069", name: "Banco Promerica" },
  { code: "072", name: "Banesco" },
  { code: "078", name: "Banco Lafise" },
  { code: "086", name: "Banco Activo" },
  { code: "087", name: "Banco LAFISE Bancentro" },
  { code: "010", name: "Banco Múltiple López de Haro" },
  { code: "058", name: "Asociación Popular de Ahorros y Préstamos (APAP)" },
  { code: "060", name: "Asociación Cibao de Ahorros y Préstamos" },
  { code: "061", name: "Asociación La Nacional de Ahorros y Préstamos" },
  { code: "062", name: "Asociación La Vega Real" },
  { code: "063", name: "Asociación Romana de Ahorros y Préstamos" },
  { code: "064", name: "Asociación Mocana de Ahorros y Préstamos" },
  { code: "065", name: "Asociación Peravia de Ahorros y Préstamos" },
  { code: "066", name: "Asociación Bonao de Ahorros y Préstamos" },
  { code: "067", name: "Asociación Duarte de Ahorros y Préstamos" },
  { code: "068", name: "Asociación Maguana de Ahorros y Préstamos" },
  { code: "088", name: "Cooperativa Nacional de Servicios Múltiples Vega Real (COOPCENTRAL)" },
];

export const MEXICAN_BANKS = [
  { code: "002", name: "BANAMEX" },
  { code: "006", name: "BANCOMEXT" },
  { code: "009", name: "BANOBRAS" },
  { code: "012", name: "BBVA México" },
  { code: "014", name: "SANTANDER" },
  { code: "019", name: "BANJERCITO" },
  { code: "021", name: "HSBC" },
  { code: "030", name: "BAJÍO" },
  { code: "036", name: "INBURSA" },
  { code: "037", name: "INTERACCIONES" },
  { code: "042", name: "MIFEL" },
  { code: "044", name: "SCOTIABANK" },
  { code: "058", name: "BANREGIO" },
  { code: "059", name: "INVEX" },
  { code: "060", name: "BANSI" },
  { code: "062", name: "AFIRME" },
  { code: "072", name: "BANORTE" },
  { code: "112", name: "BMONEX" },
  { code: "127", name: "AZTECA" },
  { code: "128", name: "AUTOFIN" },
  { code: "130", name: "COMPARTAMOS" },
  { code: "132", name: "MULTIVA BANCO" },
];

export const COLOMBIAN_BANKS = [
  { code: "01",  name: "Bancolombia" },
  { code: "02",  name: "Banco de Bogotá" },
  { code: "07",  name: "Banco AV Villas" },
  { code: "13",  name: "BBVA Colombia" },
  { code: "23",  name: "Banco Davivienda" },
  { code: "32",  name: "Banco Caja Social" },
  { code: "40",  name: "Banco Agrario" },
  { code: "51",  name: "Banco Popular" },
  { code: "52",  name: "Banco Itaú" },
  { code: "53",  name: "Banco Cooperativo Coopcentral" },
  { code: "58",  name: "Banco Falabella" },
  { code: "62",  name: "Banco Pichincha" },
  { code: "63",  name: "Banco Finandina" },
  { code: "65",  name: "Banco Santander de Negocios" },
  { code: "66",  name: "Banco Serfinanza" },
  { code: "67",  name: "Banco GNB Sudameris" },
];

export const ARGENTINIAN_BANKS = [
  { code: "005", name: "BANCO GALICIA" },
  { code: "011", name: "BANCO NACION" },
  { code: "014", name: "BANCO PROVINCIA" },
  { code: "015", name: "ICBC" },
  { code: "016", name: "CITIBANK" },
  { code: "017", name: "BANCO BBVA" },
  { code: "027", name: "BANCO SUPERVIELLE" },
  { code: "029", name: "BANCO CIUDAD" },
  { code: "034", name: "BANCO PATAGONIA" },
  { code: "044", name: "BANCO HIPOTECARIO" },
  { code: "045", name: "BANCO SAN JUAN" },
  { code: "060", name: "BANCO TUCUMAN" },
  { code: "065", name: "BANCO MUNICIPAL DE ROSARIO" },
  { code: "072", name: "BANCO SANTANDER RIO" },
  { code: "083", name: "BANCO DEL CHUBUT" },
  { code: "086", name: "BANCO DE SANTA CRUZ" },
  { code: "093", name: "BANCO DE LA PAMPA" },
  { code: "094", name: "BANCO CORRIENTES" },
  { code: "143", name: "BRUBANK" },
  { code: "147", name: "BANCO INTERFINANZAS" },
  { code: "150", name: "HSBC" },
  { code: "165", name: "JPMORGAN CHASE BANK" },
  { code: "191", name: "BANCO CREDICOOP" },
  { code: "198", name: "BANCO DE COMERCIO" },
  { code: "247", name: "BANCO RIOJA" },
  { code: "259", name: "BANCO MACRO" },
  { code: "262", name: "BANCO MARIVA" },
  { code: "266", name: "BANCO BIND" },
  { code: "268", name: "BANCO PROVINCIA TIERRA DEL FUEGO" },
  { code: "269", name: "BANCO ROELA" },
  { code: "281", name: "BANCO MERIDIAN" },
  { code: "295", name: "BANCO NACIONAL DE PAGOS" },
  { code: "299", name: "BANCO COMAFI" },
  { code: "300", name: "BANCO DE INVERSIÓN Y COMERCIO EXTERIOR" },
  { code: "301", name: "BANCO PIANO" },
  { code: "305", name: "BANCO JULIO" },
  { code: "309", name: "NUEVO BANCO DE LA RIOJA" },
  { code: "310", name: "BANCO DEL SOL" },
  { code: "311", name: "NUEVO BANCO DEL CHACO" },
  { code: "312", name: "BANCO VOII" },
  { code: "315", name: "BANCO DE FORMOSA" },
  { code: "319", name: "BANCO CMF" },
  { code: "321", name: "BANCO DE SANTIAGO DEL ESTERO" },
  { code: "322", name: "BANCO INDUSTRIAL" },
  { code: "330", name: "NUEVO BANCO DE SANTA FE" },
  { code: "331", name: "BANCO CETELEM" },
  { code: "332", name: "BANCO DE SERVICIOS FINANCIEROS" },
  { code: "336", name: "BANCO BRADESCO" },
  { code: "340", name: "BANCO DE SERVICIOS Y TRANSACCIONES" },
  { code: "341", name: "RCI BANQUE" },
  { code: "384", name: "WILOBANK" },
  { code: "386", name: "NUEVO BANCO DE ENTRE RIOS" },
  { code: "389", name: "BANCO COLUMBIA" },
];

export const PERUVIAN_BANKS = [
  { code: "002", name: "BANCO DE CRÉDITO DEL PERÚ (BCP)" },
  { code: "003", name: "INTERBANK" },
  { code: "009", name: "SCOTIABANK PERÚ" },
  { code: "011", name: "BBVA PERÚ" },
  { code: "018", name: "MIBANCO" },
  { code: "023", name: "BANCO DE LA NACIÓN" },
  { code: "035", name: "BANCO PICHINCHA" },
  { code: "038", name: "BANBIF" },
  { code: "043", name: "BANCO DE COMERCIO" },
  { code: "049", name: "BANCO RIPLEY" },
  { code: "050", name: "BANCO SANTANDER PERÚ" },
  { code: "053", name: "BANCO FALABELLA" },
  { code: "054", name: "BANCO AZTECA PERÚ" },
  { code: "056", name: "BANCO CENCOSUD" },
  { code: "058", name: "BANCO GNB PERÚ" },
];

export const CHILEAN_BANKS = [
  { code: "001", name: "Banco de Chile" },
  { code: "009", name: "Banco Internacional" },
  { code: "012", name: "Banco del Estado de Chile (BancoEstado)" },
  { code: "014", name: "Scotiabank Chile" },
  { code: "016", name: "Banco de Crédito e Inversiones (BCI)" },
  { code: "027", name: "Corpbanca" },
  { code: "028", name: "Banco BICE" },
  { code: "031", name: "HSBC Bank Chile" },
  { code: "037", name: "Banco Santander Chile" },
  { code: "039", name: "Banco Itaú Chile" },
  { code: "049", name: "Banco Security" },
  { code: "051", name: "Banco Falabella" },
  { code: "053", name: "Banco Ripley" },
  { code: "054", name: "Rabobank Chile" },
  { code: "055", name: "Banco Consorcio" },
  { code: "056", name: "Banco Penta" },
  { code: "059", name: "Banco BTG Pactual Chile" },
];

export const PANAMA_BANKS = [
  { code: "001", name: "Banco Nacional de Panamá" },
  { code: "002", name: "Caja de Ahorros" },
  { code: "003", name: "Banistmo" },
  { code: "004", name: "BAC Credomatic" },
  { code: "005", name: "Banco General" },
  { code: "006", name: "Global Bank" },
  { code: "007", name: "Multibank" },
  { code: "008", name: "Banesco Panamá" },
  { code: "009", name: "Banco Aliado" },
  { code: "010", name: "Banco Davivienda Panamá" },
  { code: "011", name: "Banco Pichincha Panamá" },
  { code: "012", name: "Mercantil Banco" },
  { code: "013", name: "Credicorp Bank" },
  { code: "014", name: "St. Georges Bank" },
];

export const ECUADOR_BANKS = [
  { code: "001", name: "Banco del Pichincha" },
  { code: "002", name: "Banco de Guayaquil" },
  { code: "003", name: "Produbanco" },
  { code: "004", name: "Banco Pacífico" },
  { code: "005", name: "Banco Internacional" },
  { code: "006", name: "Banco Bolivariano" },
  { code: "007", name: "Banco ProCredit" },
  { code: "008", name: "Banco General Rumiñahui" },
  { code: "009", name: "Banco del Austro" },
  { code: "010", name: "Banco Solidario" },
  { code: "011", name: "Banco Coopnacional" },
  { code: "012", name: "Banco Amazonas" },
  { code: "013", name: "Banco Capital" },
  { code: "014", name: "Banco D-Miro" },
];

/**
 * Returns the list of banks for the given country code, or empty list
 * (which the UI treats as "free text — type the bank name").
 */
export function getBanksByCountry(countryCode) {
  switch ((countryCode || "").toUpperCase()) {
    case "DO": return DOMINICAN_BANKS;
    case "MX": return MEXICAN_BANKS;
    case "CO": return COLOMBIAN_BANKS;
    case "AR": return ARGENTINIAN_BANKS;
    case "PE": return PERUVIAN_BANKS;
    case "CL": return CHILEAN_BANKS;
    case "PA": return PANAMA_BANKS;
    case "EC": return ECUADOR_BANKS;
    default: return [];
  }
}
