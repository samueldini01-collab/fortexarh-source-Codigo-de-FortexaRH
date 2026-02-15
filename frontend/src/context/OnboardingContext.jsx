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
    titleKey: "onboarding.steps.welcome.title",
    descriptionKey: "onboarding.steps.welcome.description",
    image: "/fortexarh-icon-128.png",
  },
  {
    id: "dashboard",
    type: "highlight",
    target: '[data-testid="stat-card-0"]',
    titleKey: "onboarding.steps.dashboard.title",
    descriptionKey: "onboarding.steps.dashboard.description",
    position: "bottom",
  },
  {
    id: "sidebar",
    type: "highlight",
    target: '[data-testid="collapse-sidebar-btn"]',
    titleKey: "onboarding.steps.sidebar.title",
    descriptionKey: "onboarding.steps.sidebar.description",
    position: "right",
  },
  {
    id: "search",
    type: "highlight",
    target: '[data-testid="global-search-trigger"]',
    titleKey: "onboarding.steps.search.title",
    descriptionKey: "onboarding.steps.search.description",
    position: "bottom",
  },
  {
    id: "theme",
    type: "highlight",
    target: '[data-testid="theme-toggle-btn"]',
    titleKey: "onboarding.steps.theme.title",
    descriptionKey: "onboarding.steps.theme.description",
    position: "bottom",
  },
  {
    id: "user-menu",
    type: "highlight",
    target: '[data-testid="user-menu-btn"]',
    titleKey: "onboarding.steps.userMenu.title",
    descriptionKey: "onboarding.steps.userMenu.description",
    position: "bottom",
  },
  {
    id: "employees-nav",
    type: "highlight",
    target: 'a[href="/employees"]',
    titleKey: "onboarding.steps.employees.title",
    descriptionKey: "onboarding.steps.employees.description",
    position: "right",
  },
  {
    id: "payroll-nav",
    type: "highlight",
    target: 'a[href="/payroll"]',
    titleKey: "onboarding.steps.payroll.title",
    descriptionKey: "onboarding.steps.payroll.description",
    position: "right",
  },
  {
    id: "keyboard-shortcuts",
    type: "modal",
    titleKey: "onboarding.steps.keyboard.title",
    descriptionKey: "onboarding.steps.keyboard.description",
    icon: "keyboard",
  },
  {
    id: "complete",
    type: "modal",
    titleKey: "onboarding.steps.complete.title",
    descriptionKey: "onboarding.steps.complete.description",
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
