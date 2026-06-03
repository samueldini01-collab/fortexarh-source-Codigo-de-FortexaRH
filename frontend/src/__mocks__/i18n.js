// Minimal i18n stub for component tests.
// Provides ``t()`` as identity-on-fallback so test queries can match by visible text.
jest.mock("react-i18next", () => ({
  __esModule: true,
  useTranslation: () => ({
    t: (key, opts) => (opts && opts.defaultValue) || key,
    i18n: { changeLanguage: () => Promise.resolve() },
  }),
  initReactI18next: { type: "3rdParty", init: () => {} },
  Trans: ({ children }) => children,
}));
