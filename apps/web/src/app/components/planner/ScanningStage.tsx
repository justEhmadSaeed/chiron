import { useEffect, useState } from 'react';
import type { ElementType } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Search, Database, CheckCircle2, Loader2, Shield, Network, BookOpen } from 'lucide-react';
import { MolecularCanvas } from './MolecularCanvas';

interface ScanStep {
  id: number;
  icon: ElementType;
  label: string;
  sublabel: string;
  duration: number;
}

const SCAN_STEPS: ScanStep[] = [
  { id: 1, icon: Search, label: 'Parsing research intent', sublabel: 'Extracting entities, targets, model organisms...', duration: 800 },
  { id: 2, icon: Network, label: 'Building semantic query graph', sublabel: 'APOE4 · iPSC · CRISPR-Cas9 · Amyloid-beta · Alzheimer\'s...', duration: 900 },
  { id: 3, icon: Database, label: 'Querying PubMed (35M papers)', sublabel: 'Searching by MeSH terms + semantic similarity...', duration: 1100 },
  { id: 4, icon: BookOpen, label: 'Scanning bioRxiv / medRxiv', sublabel: 'Preprint server cross-reference in progress...', duration: 900 },
  { id: 5, icon: Database, label: 'Cross-referencing Scopus', sublabel: 'Checking 90M+ indexed records...', duration: 800 },
  { id: 6, icon: Shield, label: 'Analyzing protocol novelty', sublabel: 'Comparing experimental designs, endpoints, conditions...', duration: 1200 },
  { id: 7, icon: Shield, label: 'Computing novelty score', sublabel: 'Aggregating signal across all matched references...', duration: 700 },
];

interface ScanningStageProps {
  question: string;
  onComplete: () => void;
}

export function ScanningStage({ question, onComplete }: ScanningStageProps) {
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);
  const [activeStep, setActiveStep] = useState(0);
  const [totalProgress, setTotalProgress] = useState(0);

  useEffect(() => {
    let stepIdx = 0;
    let totalDelay = 0;

    const runStep = (idx: number) => {
      if (idx >= SCAN_STEPS.length) {
        setTimeout(onComplete, 600);
        return;
      }
      setActiveStep(idx);

      setTimeout(() => {
        setCompletedSteps((prev) => [...prev, SCAN_STEPS[idx].id]);
        setTotalProgress(Math.round(((idx + 1) / SCAN_STEPS.length) * 100));
        runStep(idx + 1);
      }, SCAN_STEPS[idx].duration);
    };

    const timer = setTimeout(() => runStep(0), 400);
    return () => clearTimeout(timer);
  }, [onComplete]);

  return (
    <div className="relative w-full h-full flex items-center justify-center overflow-hidden"
      style={{ background: 'linear-gradient(135deg, #020c1b 0%, #050d1e 50%, #0a0618 100%)' }}>
      
      <MolecularCanvas density={40} accentColor="124, 58, 237" secondaryColor="0, 212, 255" />

      <div className="absolute inset-0 pointer-events-none" style={{
        backgroundImage: 'linear-gradient(rgba(0,212,255,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(0,212,255,0.02) 1px, transparent 1px)',
        backgroundSize: '60px 60px',
      }} />

      <div className="relative z-10 w-full max-w-2xl px-6">

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-10"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full mb-4"
            style={{ background: 'rgba(124,58,237,0.1)', border: '1px solid rgba(124,58,237,0.3)' }}>
            <div className="w-2 h-2 rounded-full bg-purple-400 animate-pulse" />
            <span className="text-purple-300" style={{ fontSize: '11px', letterSpacing: '0.12em', fontFamily: 'JetBrains Mono, monospace' }}>
              LITERATURE QC SCAN
            </span>
          </div>
          <h2 className="text-white mb-2" style={{ fontFamily: 'Space Grotesk, sans-serif', fontSize: '1.6rem', fontWeight: 600 }}>
            Checking prior art...
          </h2>
          <p className="text-slate-500" style={{ fontSize: '13px', fontFamily: 'Inter, sans-serif' }}>
            Scanning 125M+ scientific records to assess novelty
          </p>
        </motion.div>

        {/* Question card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          className="rounded-xl p-4 mb-6"
          style={{
            background: 'rgba(13,24,41,0.7)',
            border: '1px solid rgba(0,212,255,0.15)',
            backdropFilter: 'blur(12px)',
          }}
        >
          <div className="flex items-start gap-3">
            <div className="w-6 h-6 rounded flex items-center justify-center shrink-0 mt-0.5"
              style={{ background: 'rgba(0,212,255,0.1)', border: '1px solid rgba(0,212,255,0.2)' }}>
              <BookOpen size={12} className="text-cyan-400" />
            </div>
            <p className="text-slate-300" style={{ fontSize: '13px', lineHeight: 1.6, fontFamily: 'Inter, sans-serif' }}>
              {question}
            </p>
          </div>
        </motion.div>

        {/* Scan steps */}
        <div className="rounded-2xl overflow-hidden mb-6"
          style={{
            background: 'rgba(8, 15, 28, 0.85)',
            border: '1px solid rgba(255,255,255,0.06)',
            backdropFilter: 'blur(20px)',
          }}>
          
          {/* Terminal header */}
          <div className="px-4 py-2.5 flex items-center gap-2"
            style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', background: 'rgba(0,0,0,0.2)' }}>
            <div className="w-2.5 h-2.5 rounded-full bg-red-500/60" />
            <div className="w-2.5 h-2.5 rounded-full bg-amber-500/60" />
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/60" />
            <span className="text-slate-600 ml-2" style={{ fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' }}>
              chiron ~ literature-qc --scan
            </span>
          </div>

          <div className="p-4 space-y-2">
            <AnimatePresence>
              {SCAN_STEPS.map((step, idx) => {
                const isCompleted = completedSteps.includes(step.id);
                const isActive = activeStep === idx && !isCompleted;
                const isPending = idx > activeStep;
                const Icon = step.icon;

                return (
                  <motion.div
                    key={step.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{
                      opacity: isPending ? 0.3 : 1,
                      x: 0,
                    }}
                    transition={{ delay: idx * 0.05 }}
                    className="flex items-start gap-3 py-2 px-3 rounded-lg transition-all"
                    style={{
                      background: isActive ? 'rgba(124,58,237,0.08)' : isCompleted ? 'rgba(16,185,129,0.04)' : 'transparent',
                    }}
                  >
                    <div className="mt-0.5 shrink-0">
                      {isCompleted ? (
                        <CheckCircle2 size={15} className="text-emerald-400" />
                      ) : isActive ? (
                        <Loader2 size={15} className="text-purple-400 animate-spin" />
                      ) : (
                        <div className="w-4 h-4 rounded-full" style={{ border: '1px solid rgba(255,255,255,0.15)' }} />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span
                          className={isCompleted ? 'text-slate-300' : isActive ? 'text-slate-200' : 'text-slate-600'}
                          style={{ fontSize: '13px', fontFamily: 'Inter, sans-serif' }}
                        >
                          {step.label}
                        </span>
                        {isCompleted && (
                          <motion.span
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="text-emerald-600"
                            style={{ fontSize: '10px', fontFamily: 'JetBrains Mono, monospace' }}
                          >
                            ✓ done
                          </motion.span>
                        )}
                      </div>
                      {(isActive || isCompleted) && (
                        <p className={`mt-0.5 ${isCompleted ? 'text-slate-600' : 'text-slate-500'}`}
                          style={{ fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' }}>
                          {step.sublabel}
                        </p>
                      )}
                    </div>
                    {isActive && (
                      <div className="flex gap-0.5 mt-1.5 shrink-0">
                        {[0, 1, 2].map((i) => (
                          <motion.div
                            key={i}
                            className="w-1 h-1 rounded-full bg-purple-500"
                            animate={{ opacity: [0.3, 1, 0.3] }}
                            transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
                          />
                        ))}
                      </div>
                    )}
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        </div>

        {/* Progress bar */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-slate-500" style={{ fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' }}>
              SCAN PROGRESS
            </span>
            <span className="text-cyan-400" style={{ fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' }}>
              {totalProgress}%
            </span>
          </div>
          <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
            <motion.div
              className="h-full rounded-full"
              style={{ background: 'linear-gradient(90deg, #7c3aed, #00d4ff)' }}
              animate={{ width: `${totalProgress}%` }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
            />
          </div>
          <div className="flex justify-between">
            <span className="text-slate-600" style={{ fontSize: '10px', fontFamily: 'JetBrains Mono, monospace' }}>
              125,000,000+ records indexed
            </span>
            <span className="text-slate-600" style={{ fontSize: '10px', fontFamily: 'JetBrains Mono, monospace' }}>
              avg. latency 4.2s
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}