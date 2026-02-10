import { useEffect, useState, useRef } from "react";
import { useTranslation } from "react-i18next";
import { useOnboarding } from "@/context/OnboardingContext";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { 
  X, 
  ChevronLeft, 
  ChevronRight, 
  Keyboard, 
  Sparkles,
  PartyPopper,
  SkipForward
} from "lucide-react";

// Spotlight overlay component
function SpotlightOverlay({ targetRect, onClick }) {
  if (!targetRect) return null;

  const padding = 8;
  const borderRadius = 12;

  return (
    <div 
      className="fixed inset-0 z-[9998] pointer-events-auto"
      onClick={onClick}
    >
      <svg className="absolute inset-0 w-full h-full">
        <defs>
          <mask id="spotlight-mask">
            <rect x="0" y="0" width="100%" height="100%" fill="white" />
            <rect 
              x={targetRect.left - padding}
              y={targetRect.top - padding}
              width={targetRect.width + padding * 2}
              height={targetRect.height + padding * 2}
              rx={borderRadius}
              fill="black"
            />
          </mask>
        </defs>
        <rect 
          x="0" 
          y="0" 
          width="100%" 
          height="100%" 
          fill="rgba(0, 0, 0, 0.75)" 
          mask="url(#spotlight-mask)"
        />
      </svg>
      
      {/* Animated border around target */}
      <div 
        className="absolute border-2 border-primary rounded-xl animate-pulse pointer-events-none"
        style={{
          left: targetRect.left - padding,
          top: targetRect.top - padding,
          width: targetRect.width + padding * 2,
          height: targetRect.height + padding * 2,
          boxShadow: "0 0 0 4px rgba(16, 185, 129, 0.3), 0 0 20px rgba(16, 185, 129, 0.5)",
        }}
      />
    </div>
  );
}

// Tooltip component for highlighted elements
function OnboardingTooltip({ step, targetRect, onNext, onPrev, onSkip, currentStep, totalSteps }) {
  const { t } = useTranslation();
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const tooltipRef = useRef(null);

  useEffect(() => {
    if (!targetRect || !tooltipRef.current) return;

    const tooltip = tooltipRef.current;
    const tooltipRect = tooltip.getBoundingClientRect();
    const padding = 16;
    
    let top, left;
    const preferredPosition = step.position || "bottom";

    switch (preferredPosition) {
      case "top":
        top = targetRect.top - tooltipRect.height - padding;
        left = targetRect.left + (targetRect.width - tooltipRect.width) / 2;
        break;
      case "bottom":
        top = targetRect.bottom + padding;
        left = targetRect.left + (targetRect.width - tooltipRect.width) / 2;
        break;
      case "left":
        top = targetRect.top + (targetRect.height - tooltipRect.height) / 2;
        left = targetRect.left - tooltipRect.width - padding;
        break;
      case "right":
        top = targetRect.top + (targetRect.height - tooltipRect.height) / 2;
        left = targetRect.right + padding;
        break;
      default:
        top = targetRect.bottom + padding;
        left = targetRect.left;
    }

    // Keep tooltip within viewport
    const viewportPadding = 20;
    left = Math.max(viewportPadding, Math.min(left, window.innerWidth - tooltipRect.width - viewportPadding));
    top = Math.max(viewportPadding, Math.min(top, window.innerHeight - tooltipRect.height - viewportPadding));

    setPosition({ top, left });
  }, [targetRect, step.position]);

  return (
    <div 
      ref={tooltipRef}
      className="fixed z-[9999] w-80 bg-white dark:bg-slate-900 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-700 overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-300"
      style={{ top: position.top, left: position.left }}
    >
      {/* Progress bar */}
      <div className="h-1 bg-slate-100 dark:bg-slate-800">
        <div 
          className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 transition-all duration-500"
          style={{ width: `${((currentStep + 1) / totalSteps) * 100}%` }}
        />
      </div>

      <div className="p-4">
        {/* Step counter */}
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/30 px-2 py-0.5 rounded-full">
            {t('onboarding.step')} {currentStep + 1} {t('onboarding.of')} {totalSteps}
          </span>
          <button 
            onClick={onSkip}
            className="text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 flex items-center gap-1"
          >
            <SkipForward className="w-3 h-3" />
            {t('onboarding.skip')}
          </button>
        </div>

        {/* Content */}
        <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-2">
          {step.titleKey ? t(step.titleKey) : step.title}
        </h3>
        <p className="text-sm text-slate-600 dark:text-slate-400 mb-4 whitespace-pre-line">
          {step.descriptionKey ? t(step.descriptionKey) : step.description}
        </p>

        {/* Navigation */}
        <div className="flex items-center justify-between">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={onPrev}
            disabled={currentStep === 0}
            className="text-slate-500"
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            {t('onboarding.previous')}
          </Button>
          <Button 
            size="sm" 
            onClick={onNext}
            className="bg-emerald-600 hover:bg-emerald-700"
          >
            {currentStep === totalSteps - 1 ? t('onboarding.finish') : t('onboarding.next')}
            {currentStep < totalSteps - 1 && <ChevronRight className="w-4 h-4 ml-1" />}
          </Button>
        </div>
      </div>
    </div>
  );
}

// Modal for welcome/completion steps
function OnboardingModal({ step, onNext, onSkip, currentStep, totalSteps }) {
  const { t } = useTranslation();
  const [showConfetti, setShowConfetti] = useState(false);

  useEffect(() => {
    if (step.confetti) {
      setShowConfetti(true);
      const timer = setTimeout(() => setShowConfetti(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [step.confetti]);

  const getIcon = () => {
    if (step.icon === "keyboard") return <Keyboard className="w-12 h-12 text-emerald-500" />;
    if (step.confetti) return <PartyPopper className="w-12 h-12 text-emerald-500" />;
    if (step.image) return <img src={step.image} alt="" className="w-16 h-16" />;
    return <Sparkles className="w-12 h-12 text-emerald-500" />;
  };

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 z-[9998] bg-black/60 backdrop-blur-sm" />
      
      {/* Confetti effect */}
      {showConfetti && (
        <div className="fixed inset-0 z-[10000] pointer-events-none overflow-hidden">
          {[...Array(50)].map((_, i) => (
            <div
              key={i}
              className="absolute w-2 h-2 animate-confetti"
              style={{
                left: `${Math.random() * 100}%`,
                top: "-10px",
                backgroundColor: ["#10b981", "#f59e0b", "#3b82f6", "#ec4899", "#8b5cf6"][i % 5],
                animationDelay: `${Math.random() * 2}s`,
                animationDuration: `${2 + Math.random() * 2}s`,
              }}
            />
          ))}
        </div>
      )}

      {/* Modal */}
      <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
        <div className="w-full max-w-md bg-white dark:bg-slate-900 rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 fade-in duration-300">
          {/* Progress */}
          <Progress value={((currentStep + 1) / totalSteps) * 100} className="h-1 rounded-none" />
          
          <div className="p-6 text-center">
            {/* Icon */}
            <div className="w-20 h-20 mx-auto mb-4 bg-emerald-50 dark:bg-emerald-900/30 rounded-full flex items-center justify-center">
              {getIcon()}
            </div>

            {/* Content */}
            <h2 className="text-2xl font-bold text-slate-800 dark:text-slate-100 mb-3">
              {step.titleKey ? t(step.titleKey) : step.title}
            </h2>
            <p className="text-slate-600 dark:text-slate-400 mb-6 whitespace-pre-line">
              {step.descriptionKey ? t(step.descriptionKey) : step.description}
            </p>

            {/* Step indicator */}
            <div className="flex justify-center gap-1.5 mb-6">
              {[...Array(totalSteps)].map((_, i) => (
                <div 
                  key={i}
                  className={`w-2 h-2 rounded-full transition-all ${
                    i === currentStep 
                      ? "w-6 bg-emerald-500" 
                      : i < currentStep 
                        ? "bg-emerald-300 dark:bg-emerald-700" 
                        : "bg-slate-200 dark:bg-slate-700"
                  }`}
                />
              ))}
            </div>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              {currentStep === 0 && (
                <Button variant="outline" onClick={onSkip} className="order-2 sm:order-1">
                  {t('onboarding.skipTutorial')}
                </Button>
              )}
              <Button 
                onClick={onNext} 
                className="bg-emerald-600 hover:bg-emerald-700 order-1 sm:order-2"
                size="lg"
              >
                {currentStep === 0 ? t('onboarding.startTour') : currentStep === totalSteps - 1 ? t('onboarding.startUsing') : t('onboarding.continue')}
                {currentStep < totalSteps - 1 && <ChevronRight className="w-4 h-4 ml-1" />}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

// Main Onboarding component
export default function OnboardingTutorial() {
  const { 
    isOnboarding, 
    currentStep, 
    totalSteps, 
    currentStepData, 
    nextStep, 
    prevStep, 
    skipOnboarding 
  } = useOnboarding();
  
  const [targetRect, setTargetRect] = useState(null);

  // Find and track target element
  useEffect(() => {
    if (!isOnboarding || !currentStepData || currentStepData.type !== "highlight") {
      setTargetRect(null);
      return;
    }

    const findTarget = () => {
      const target = document.querySelector(currentStepData.target);
      if (target) {
        const rect = target.getBoundingClientRect();
        setTargetRect(rect);
        
        // Scroll element into view if needed
        target.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    };

    // Initial find
    findTarget();

    // Re-find on resize/scroll
    const handleResize = () => findTarget();
    window.addEventListener("resize", handleResize);
    window.addEventListener("scroll", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("scroll", handleResize);
    };
  }, [isOnboarding, currentStepData]);

  if (!isOnboarding || !currentStepData) return null;

  // Render modal for modal-type steps
  if (currentStepData.type === "modal") {
    return (
      <OnboardingModal 
        step={currentStepData}
        onNext={nextStep}
        onSkip={skipOnboarding}
        currentStep={currentStep}
        totalSteps={totalSteps}
      />
    );
  }

  // Render highlight + tooltip for highlight-type steps
  return (
    <>
      <SpotlightOverlay 
        targetRect={targetRect} 
        onClick={(e) => {
          // Only advance if clicking outside the tooltip
          if (!e.target.closest('[data-onboarding-tooltip]')) {
            // Don't auto-advance, let user use buttons
          }
        }}
      />
      {targetRect && (
        <div data-onboarding-tooltip>
          <OnboardingTooltip 
            step={currentStepData}
            targetRect={targetRect}
            onNext={nextStep}
            onPrev={prevStep}
            onSkip={skipOnboarding}
            currentStep={currentStep}
            totalSteps={totalSteps}
          />
        </div>
      )}
    </>
  );
}

// Button to start onboarding from anywhere
export function StartTutorialButton({ variant = "default" }) {
  const { startOnboarding, isCompleted } = useOnboarding();

  return (
    <Button 
      variant={variant}
      onClick={startOnboarding}
      className="gap-2"
    >
      <Sparkles className="w-4 h-4" />
      {isCompleted ? "Repetir Tutorial" : "Iniciar Tutorial"}
    </Button>
  );
}
