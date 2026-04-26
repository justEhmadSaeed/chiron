import { Brain, Loader2, MessageSquareQuote, Sparkles } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useEffect, useState } from "react";
import { MolecularCanvas } from "./MolecularCanvas";

interface PlanSection {
  id: string;
  label: string;
  sublabel: string;
  duration: number;
  tokens: number;
}

const PLAN_SECTIONS: PlanSection[] = [
  {
    id: "hypothesis",
    label: "Formalizing hypothesis",
    sublabel: "Structuring testable scientific claim...",
    duration: 700,
    tokens: 312
  },
  {
    id: "protocol",
    label: "Generating protocol",
    sublabel: "Building step-by-step methodology from validated templates...",
    duration: 1400,
    tokens: 2841
  },
  {
    id: "materials",
    label: "Sourcing materials & reagents",
    sublabel: "Matching catalog numbers, suppliers, lead times...",
    duration: 1100,
    tokens: 1290
  },
  {
    id: "budget",
    label: "Estimating budget",
    sublabel: "Computing line-item costs with real reagent prices...",
    duration: 800,
    tokens: 640
  },
  {
    id: "timeline",
    label: "Phasing the timeline",
    sublabel: "Mapping dependencies and critical path analysis...",
    duration: 900,
    tokens: 520
  },
  {
    id: "validation",
    label: "Defining validation criteria",
    sublabel: "Setting measurable success/failure endpoints...",
    duration: 700,
    tokens: 480
  }
];

interface PlanningStageProps {
  question: string;
  hasPriorFeedback?: boolean;
  onComplete: () => void;
  isPlanReady?: boolean;
}

export function PlanningStage({
  hasPriorFeedback = false,
  onComplete,
  isPlanReady = false
}: PlanningStageProps) {
  const [completedSections, setCompletedSections] = useState<string[]>([]);
  const [activeSection, setActiveSection] = useState(-1);
  const [totalTokens, setTotalTokens] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const runSection = (i: number) => {
      if (i >= PLAN_SECTIONS.length) return;

      setActiveSection(i);

      // Don't auto-complete the last step
      if (i === PLAN_SECTIONS.length - 1) return;

      setTimeout(() => {
        setCompletedSections((prev) => [...prev, PLAN_SECTIONS[i].id]);
        setTotalTokens((prev) => prev + PLAN_SECTIONS[i].tokens);
        const nextProgress = Math.min(95, Math.round(((i + 1) / PLAN_SECTIONS.length) * 100));
        setProgress(nextProgress);
        runSection(i + 1);
      }, PLAN_SECTIONS[i].duration);
    };

    const startTimer = setTimeout(() => runSection(0), 500);
    return () => clearTimeout(startTimer);
  }, []);

  useEffect(() => {
    if (isPlanReady && activeSection === PLAN_SECTIONS.length - 1) {
      const timer = setTimeout(() => {
        setCompletedSections((prev) => {
          const lastSectionId = PLAN_SECTIONS[activeSection].id;
          if (prev.includes(lastSectionId)) return prev;
          return [...prev, lastSectionId];
        });
        setTotalTokens((prev) => prev + PLAN_SECTIONS[activeSection].tokens);
        setProgress(100);
      }, 0);

      const completionTimer = setTimeout(onComplete, 1500);

      return () => {
        clearTimeout(timer);
        clearTimeout(completionTimer);
      };
    }
  }, [isPlanReady, activeSection, onComplete]);

  return (
    <div
      className="relative w-full h-full flex items-center justify-center overflow-hidden"
      style={{ background: "linear-gradient(135deg, #020c1b 0%, #050d1e 50%, #0a0618 100%)" }}
    >
      <MolecularCanvas density={45} accentColor="0, 212, 255" secondaryColor="124, 58, 237" />

      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(rgba(0,212,255,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(0,212,255,0.02) 1px, transparent 1px)",
          backgroundSize: "60px 60px"
        }}
      />

      <div className="relative z-10 w-full max-w-xl px-6 space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <div
            className="relative inline-flex items-center justify-center w-14 h-14 rounded-2xl mb-4"
            style={{ background: "rgba(0,212,255,0.08)", border: "1px solid rgba(0,212,255,0.2)" }}
          >
            <Brain size={24} className="text-cyan-400" />
            <motion.div
              className="absolute inset-0 rounded-2xl"
              style={{ border: "1px solid rgba(0,212,255,0.4)" }}
              animate={{ scale: [1, 1.2, 1], opacity: [1, 0, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
            />
          </div>
          <h2
            className="text-white mb-2"
            style={{ fontFamily: "Space Grotesk, sans-serif", fontSize: "1.6rem", fontWeight: 600 }}
          >
            Architecting your plan...
          </h2>
          <p className="text-slate-500" style={{ fontSize: "13px" }}>
            Generating a lab-ready experiment from first principles
          </p>
        </motion.div>

        {/* Prior feedback notice */}
        <AnimatePresence>
          {hasPriorFeedback && (
            <motion.div
              initial={{ opacity: 0, y: -8, height: 0 }}
              animate={{ opacity: 1, y: 0, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="rounded-xl px-4 py-3 flex items-start gap-3"
              style={{
                background: "rgba(124,58,237,0.1)",
                border: "1px solid rgba(124,58,237,0.3)"
              }}
            >
              <MessageSquareQuote size={16} className="text-purple-400 mt-0.5 shrink-0" />
              <div>
                <p
                  className="text-purple-300"
                  style={{
                    fontSize: "13px",
                    fontFamily: "Space Grotesk, sans-serif",
                    fontWeight: 600
                  }}
                >
                  Incorporating prior scientist corrections
                </p>
                <p
                  className="text-purple-500"
                  style={{ fontSize: "12px", fontFamily: "Inter, sans-serif" }}
                >
                  3 expert annotations from similar CRISPR-iPSC experiments applied as few-shot
                  context
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Section progress */}
        <div
          className="rounded-2xl overflow-hidden"
          style={{
            background: "rgba(8,15,28,0.85)",
            border: "1px solid rgba(255,255,255,0.06)",
            backdropFilter: "blur(20px)"
          }}
        >
          <div
            className="px-4 py-2.5 flex items-center justify-between"
            style={{
              borderBottom: "1px solid rgba(255,255,255,0.05)",
              background: "rgba(0,0,0,0.2)"
            }}
          >
            <div className="flex items-center gap-2">
              <Sparkles size={12} className="text-cyan-400" />
              <span
                className="text-slate-400"
                style={{ fontSize: "11px", fontFamily: "JetBrains Mono, monospace" }}
              >
                PLAN GENERATION
              </span>
            </div>
            <span
              className="text-slate-500"
              style={{ fontSize: "10px", fontFamily: "JetBrains Mono, monospace" }}
            >
              ~{totalTokens.toLocaleString()} tokens
            </span>
          </div>

          <div className="p-4 space-y-3">
            {PLAN_SECTIONS.map((section, idx) => {
              const isCompleted = completedSections.includes(section.id);
              const isActive = activeSection === idx && !isCompleted;

              return (
                <motion.div
                  key={section.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: idx <= activeSection ? 1 : 0.25 }}
                  className="flex items-center gap-3"
                >
                  {/* Status icon */}
                  <div
                    className="w-5 h-5 rounded-full flex items-center justify-center shrink-0"
                    style={{
                      background: isCompleted
                        ? "rgba(0,212,255,0.15)"
                        : isActive
                          ? "rgba(124,58,237,0.15)"
                          : "rgba(255,255,255,0.04)",
                      border: isCompleted
                        ? "1px solid rgba(0,212,255,0.4)"
                        : isActive
                          ? "1px solid rgba(124,58,237,0.4)"
                          : "1px solid rgba(255,255,255,0.1)"
                    }}
                  >
                    {isCompleted ? (
                      <div className="w-2 h-2 rounded-full bg-cyan-400" />
                    ) : isActive ? (
                      <Loader2 size={10} className="text-purple-400 animate-spin" />
                    ) : (
                      <div className="w-1.5 h-1.5 rounded-full bg-slate-700" />
                    )}
                  </div>

                  {/* Label */}
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span
                        className={
                          isCompleted
                            ? "text-slate-300"
                            : isActive
                              ? "text-white"
                              : "text-slate-600"
                        }
                        style={{ fontSize: "13px", fontFamily: "Inter, sans-serif" }}
                      >
                        {section.label}
                      </span>
                      {isCompleted && (
                        <span
                          className="text-cyan-600"
                          style={{ fontSize: "10px", fontFamily: "JetBrains Mono, monospace" }}
                        >
                          +{section.tokens.toLocaleString()} tokens
                        </span>
                      )}
                    </div>
                    {isActive && (
                      <motion.p
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="text-purple-500"
                        style={{ fontSize: "11px", fontFamily: "JetBrains Mono, monospace" }}
                      >
                        {section.sublabel}
                      </motion.p>
                    )}
                  </div>

                  {/* Progress dot for active */}
                  {isActive && (
                    <div className="flex gap-0.5">
                      {[0, 1, 2].map((i) => (
                        <motion.div
                          key={i}
                          className="w-1 h-1 rounded-full bg-purple-500"
                          animate={{ opacity: [0.2, 1, 0.2] }}
                          transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.15 }}
                        />
                      ))}
                    </div>
                  )}
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Overall progress */}
        <div className="space-y-2">
          <div className="flex justify-between">
            <span
              className="text-slate-500"
              style={{ fontSize: "11px", fontFamily: "JetBrains Mono, monospace" }}
            >
              GENERATING PLAN
            </span>
            <span
              className="text-cyan-400"
              style={{ fontSize: "11px", fontFamily: "JetBrains Mono, monospace" }}
            >
              {progress}%
            </span>
          </div>
          <div
            className="h-1.5 rounded-full overflow-hidden"
            style={{ background: "rgba(255,255,255,0.06)" }}
          >
            <motion.div
              className="h-full rounded-full"
              style={{ background: "linear-gradient(90deg, #00d4ff, #7c3aed)" }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3, ease: "easeOut" }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
