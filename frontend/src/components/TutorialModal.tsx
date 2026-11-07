import { useState } from 'react';

export interface TutorialModalProps {
  onComplete: () => void;
}

interface StepInfo {
  icon: string;
  stepNum: number;
  title: string;
  text: string;
  hint: string;
}

const STEPS: StepInfo[] = [
  {
    icon: '🌾',
    stepNum: 1,
    title: 'Granja y Recursos',
    text: '¡Bienvenido! Recolecta tu Grano aquí para empezar.',
    hint: 'El grano te servirá para mejorar tus edificios y fortalecer tu economía.',
  },
  {
    icon: '🔄',
    stepNum: 2,
    title: 'Fusión de Tropas',
    text: "Ve a 'Merge' y fusiona 3 unidades iguales para hacerlas más fuertes.",
    hint: 'Al unir 3 copias idénticas, aumentas su nivel, daño y supervivencia.',
  },
  {
    icon: '⚔️',
    stepNum: 3,
    title: 'Estrategia y Combate',
    text: "Forma tu equipo en 'Formación' y ¡a la batalla!",
    hint: 'Coloca tus unidades en la cuadrícula 3x3 y desafía las oleadas.',
  },
];

export function TutorialModal({ onComplete }: TutorialModalProps) {
  const [currentStep, setCurrentStep] = useState<number>(1);

  const stepData = STEPS[currentStep - 1] ?? STEPS[0];
  const isLastStep = currentStep === STEPS.length;

  const handleNext = () => {
    if (isLastStep) {
      onComplete();
    } else {
      setCurrentStep((prev) => prev + 1);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 select-none">
      <div className="w-full max-w-sm bg-gradient-to-b from-stone-900 to-stone-950 border border-stone-800 rounded-3xl p-6 shadow-2xl flex flex-col items-center text-center gap-4">
        {/* Indicadores de paso */}
        <div className="flex items-center gap-2">
          {STEPS.map((s) => (
            <div
              key={s.stepNum}
              className={`h-1.5 rounded-full transition-all duration-300 ${
                s.stepNum === currentStep
                  ? 'w-7 bg-amber-400'
                  : s.stepNum < currentStep
                  ? 'w-4 bg-amber-600/60'
                  : 'w-4 bg-stone-800'
              }`}
            />
          ))}
        </div>

        {/* Badge paso actual */}
        <span className="text-[11px] font-mono font-bold tracking-wider uppercase text-amber-400 bg-amber-500/10 border border-amber-500/20 px-3 py-0.5 rounded-full">
          Paso {currentStep} de 3
        </span>

        {/* Icono central */}
        <div className="w-16 h-16 rounded-2xl bg-stone-800/90 border border-stone-700/80 flex items-center justify-center text-3xl shadow-inner">
          <span className="filter drop-shadow">{stepData.icon}</span>
        </div>

        {/* Título y texto del paso */}
        <div className="flex flex-col gap-1.5 px-2">
          <h3 className="text-base font-black text-stone-100 tracking-tight">
            {stepData.title}
          </h3>
          <p className="text-sm font-semibold text-amber-200/90 leading-snug">
            {stepData.text}
          </p>
          <p className="text-xs text-stone-400 mt-1">
            {stepData.hint}
          </p>
        </div>

        {/* Botones de acción */}
        <div className="w-full flex flex-col gap-2 mt-2">
          <button
            type="button"
            onClick={handleNext}
            className="w-full py-3 px-4 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-stone-950 font-black text-sm rounded-xl shadow-lg shadow-amber-900/40 active:scale-95 transition"
          >
            {isLastStep ? '¡Entendido!' : 'Siguiente'}
          </button>

          <button
            type="button"
            onClick={onComplete}
            className="text-xs text-stone-500 hover:text-stone-300 transition underline underline-offset-4 py-1"
          >
            Omitir
          </button>
        </div>
      </div>
    </div>
  );
}

export default TutorialModal;
