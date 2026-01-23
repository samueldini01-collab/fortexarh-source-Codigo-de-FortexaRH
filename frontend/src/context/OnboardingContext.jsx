import { createContext, useContext, useState, useEffect, useCallback } from "react";

const OnboardingContext = createContext({
  isOnboarding: false,
  currentStep: 0,
  totalSteps: 0,
  startOnboarding: () => {},
  nextStep: () => {},
  prevStep: () => {},
  skipOnboarding: () => {},
  completeOnboarding: () => {},
  isCompleted: false,
  currentStepData: null,
});

const ONBOARDING_STORAGE_KEY = "fortexarh-onboarding-completed";
const ONBOARDING_VERSION = "1.0"; // Increment to re-show tutorial after updates

// Define the tutorial steps
const ONBOARDING_STEPS = [
  {
    id: "welcome",
    type: "modal",
    title: "¡Bienvenido a FortexaRH! 🎉",
    description: "Te guiaremos por las funciones principales del sistema para que puedas empezar a gestionar tu equipo de forma eficiente.",
    image: "/fortexarh-icon-128.png",
  },
  {
    id: "dashboard",
    type: "highlight",
    target: '[data-testid="stat-card-0"]',
    title: "Panel de Control",
    description: "Aquí verás un resumen rápido de tu gestión: empleados, nóminas pendientes, asistencias y más. Haz clic en cualquier tarjeta para ir directamente a esa sección.",
    position: "bottom",
  },
  {
    id: "sidebar",
    type: "highlight",
    target: '[data-testid="collapse-sidebar-btn"]',
    title: "Menú de Navegación",
    description: "Usa el menú lateral para acceder a todos los módulos. Puedes colapsarlo para tener más espacio de trabajo.",
    position: "right",
  },
  {
    id: "search",
    type: "highlight",
    target: '[data-testid="global-search-trigger"]',
    title: "Búsqueda Global",
    description: "Busca rápidamente empleados, nóminas, vacaciones y más. También puedes usar Ctrl+K como atajo de teclado.",
    position: "bottom",
  },
  {
    id: "theme",
    type: "highlight",
    target: '[data-testid="theme-toggle-btn"]',
    title: "Personaliza tu Experiencia",
    description: "Cambia entre modo claro, oscuro o alto contraste según tu preferencia. El sistema también puede detectar la configuración de tu dispositivo.",
    position: "bottom",
  },
  {
    id: "user-menu",
    type: "highlight",
    target: '[data-testid="user-menu-btn"]',
    title: "Tu Perfil y Configuración",
    description: "Accede a tu perfil, configuración de empresa, facturación y más desde este menú. También encontrarás los atajos de teclado disponibles.",
    position: "bottom",
  },
  {
    id: "employees-nav",
    type: "highlight",
    target: 'a[href="/employees"]',
    title: "Gestión de Empleados",
    description: "El módulo de empleados es el corazón del sistema. Aquí registras, editas y gestionas toda la información de tu equipo.",
    position: "right",
  },
  {
    id: "payroll-nav",
    type: "highlight",
    target: 'a[href="/payroll-v2"]',
    title: "Nómina Avanzada",
    description: "Calcula nóminas con todas las deducciones de ley (TSS, ISR) de forma automática. Genera reportes DGII y comprobantes de pago.",
    position: "right",
  },
  {
    id: "keyboard-shortcuts",
    type: "modal",
    title: "¡Trabaja más Rápido! ⌨️",
    description: "FortexaRH tiene atajos de teclado para navegar rápidamente:\n\n• Presiona ? para ver todos los atajos\n• G + E para ir a Empleados\n• G + N para ir a Nómina\n• Ctrl + K para búsqueda global",
    icon: "keyboard",
  },
  {
    id: "complete",
    type: "modal",
    title: "¡Listo para Empezar! 🚀",
    description: "Ya conoces las funciones principales de FortexaRH. Si necesitas ayuda, puedes:\n\n• Presionar ? para ver atajos de teclado\n• Reiniciar este tutorial desde Configuración\n• Contactar soporte desde el menú de ayuda",
    confetti: true,
  },
];

export function OnboardingProvider({ children }) {
  const [isOnboarding, setIsOnboarding] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [isCompleted, setIsCompleted] = useState(false);

  // Check if onboarding was completed
  useEffect(() => {
    const stored = localStorage.getItem(ONBOARDING_STORAGE_KEY);
    if (stored) {
      try {
        const data = JSON.parse(stored);
        if (data.version === ONBOARDING_VERSION && data.completed) {
          setIsCompleted(true);
        }
      } catch {
        // Invalid data, will show onboarding
      }
    }
  }, []);

  const startOnboarding = useCallback(() => {
    setCurrentStep(0);
    setIsOnboarding(true);
  }, []);

  const nextStep = useCallback(() => {
    if (currentStep < ONBOARDING_STEPS.length - 1) {
      setCurrentStep(prev => prev + 1);
    } else {
      completeOnboarding();
    }
  }, [currentStep]);

  const prevStep = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  }, [currentStep]);

  const skipOnboarding = useCallback(() => {
    setIsOnboarding(false);
    setCurrentStep(0);
    // Mark as completed but skipped
    localStorage.setItem(ONBOARDING_STORAGE_KEY, JSON.stringify({
      version: ONBOARDING_VERSION,
      completed: true,
      skipped: true,
      completedAt: new Date().toISOString(),
    }));
    setIsCompleted(true);
  }, []);

  const completeOnboarding = useCallback(() => {
    setIsOnboarding(false);
    setCurrentStep(0);
    localStorage.setItem(ONBOARDING_STORAGE_KEY, JSON.stringify({
      version: ONBOARDING_VERSION,
      completed: true,
      skipped: false,
      completedAt: new Date().toISOString(),
    }));
    setIsCompleted(true);
  }, []);

  const resetOnboarding = useCallback(() => {
    localStorage.removeItem(ONBOARDING_STORAGE_KEY);
    setIsCompleted(false);
    setCurrentStep(0);
  }, []);

  const value = {
    isOnboarding,
    currentStep,
    totalSteps: ONBOARDING_STEPS.length,
    currentStepData: ONBOARDING_STEPS[currentStep],
    steps: ONBOARDING_STEPS,
    startOnboarding,
    nextStep,
    prevStep,
    skipOnboarding,
    completeOnboarding,
    resetOnboarding,
    isCompleted,
  };

  return (
    <OnboardingContext.Provider value={value}>
      {children}
    </OnboardingContext.Provider>
  );
}

export const useOnboarding = () => {
  const context = useContext(OnboardingContext);
  if (context === undefined) {
    throw new Error("useOnboarding must be used within an OnboardingProvider");
  }
  return context;
};

export { ONBOARDING_STEPS };
