import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Beaker, Sparkles, ArrowRight, ChevronRight, Dna, Microscope, FlaskConical, Brain, Atom } from 'lucide-react';
import { MolecularCanvas } from './MolecularCanvas';
import { EXAMPLE_QUESTIONS } from './mockData';

interface InputStageProps {
  onSubmit: (question: string) => void;
}

const DOMAIN_CHIPS = [
  { label: 'Genomics', icon: Dna, color: 'text-cyan-400 bg-cyan-950/60 border-cyan-800/50' },
  { label: 'Neuroscience', icon: Brain, color: 'text-purple-400 bg-purple-950/60 border-purple-800/50' },
  { label: 'Cell Biology', icon: Microscope, color: 'text-emerald-400 bg-emerald-950/60 border-emerald-800/50' },
  { label: 'Biochemistry', icon: FlaskConical, color: 'text-amber-400 bg-amber-950/60 border-amber-800/50' },
  { label: 'Biophysics', icon: Atom, color: 'text-pink-400 bg-pink-950/60 border-pink-800/50' },
];

export function InputStage({ onSubmit }: InputStageProps) {
  const [question, setQuestion] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [activeExample, setActiveExample] = useState<number | null>(null);

  const handleExampleClick = (q: string, idx: number) => {
    setActiveExample(idx);
    setQuestion(q);
  };

  const handleSubmit = () => {
    if (question.trim().length > 10) onSubmit(question.trim());
  };

  const charCount = question.length;
  const isReady = question.trim().length > 10;

  return (
    <div className="relative w-full h-full flex flex-col items-center justify-center overflow-hidden"
      style={{ background: 'linear-gradient(135deg, #020c1b 0%, #050d1e 40%, #0a0618 100%)' }}>
      
      <MolecularCanvas density={60} />

      {/* Top grid overlay */}
      <div className="absolute inset-0 pointer-events-none" style={{
        backgroundImage: 'linear-gradient(rgba(0,212,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,212,255,0.03) 1px, transparent 1px)',
        backgroundSize: '60px 60px',
      }} />

      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: 'easeOut' }}
        className="absolute top-8 left-8 flex items-center gap-3"
      >
        <div className="relative">
          <div className="w-9 h-9 rounded-lg flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #00d4ff22, #7c3aed33)', border: '1px solid rgba(0,212,255,0.3)' }}>
            <Beaker size={18} className="text-cyan-400" />
          </div>
          <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
        </div>
        <div>
          <div className="text-white" style={{ fontFamily: 'Space Grotesk, sans-serif', fontWeight: 600, fontSize: '15px', letterSpacing: '0.05em' }}>
            CHI<span className="text-cyan-400">RON</span>
          </div>
          <div className="text-slate-500" style={{ fontSize: '10px', letterSpacing: '0.12em', fontFamily: 'JetBrains Mono, monospace' }}>
            AI EXPERIMENT ARCHITECT
          </div>
        </div>
      </motion.div>

      {/* Domain chips top right */}
      <motion.div
        initial={{ opacity: 0, x: 30 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.8, delay: 0.3 }}
        className="absolute top-8 right-8 flex gap-2"
      >
        {DOMAIN_CHIPS.map(({ label, icon: Icon, color }) => (
          <div key={label} className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs ${color}`}
            style={{ fontFamily: 'JetBrains Mono, monospace' }}>
            <Icon size={10} />
            {label}
          </div>
        ))}
      </motion.div>

      {/* Main content */}
      <div className="relative z-10 w-full max-w-3xl px-6 flex flex-col items-center gap-8">

        {/* Hero headline */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.1 }}
          className="text-center"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full mb-5"
            style={{ background: 'rgba(0,212,255,0.08)', border: '1px solid rgba(0,212,255,0.2)' }}>
            <Sparkles size={12} className="text-cyan-400" />
            <span className="text-cyan-400" style={{ fontSize: '11px', letterSpacing: '0.15em', fontFamily: 'JetBrains Mono, monospace' }}>
              HYPOTHESIS → EXECUTABLE PROTOCOL IN MINUTES
            </span>
          </div>

          <h1 className="text-white mb-3" style={{
            fontFamily: 'Space Grotesk, sans-serif',
            fontSize: '2.8rem',
            fontWeight: 700,
            lineHeight: 1.15,
            letterSpacing: '-0.02em',
          }}>
            Turn a scientific question
            <br />
            <span style={{
              background: 'linear-gradient(135deg, #00d4ff, #7c3aed)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}>
              into a lab-ready plan
            </span>
          </h1>

          <p className="text-slate-400 max-w-lg mx-auto" style={{ fontSize: '15px', lineHeight: 1.6 }}>
            Enter any research question. Chiron validates novelty against 40M+ papers,
            then generates a complete protocol — materials, budget, timeline, and validation.
          </p>
        </motion.div>

        {/* Input box */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="w-full"
        >
          <div
            className="relative rounded-2xl transition-all duration-300"
            style={{
              background: 'rgba(13, 24, 41, 0.85)',
              border: isFocused
                ? '1px solid rgba(0, 212, 255, 0.5)'
                : '1px solid rgba(255,255,255,0.08)',
              boxShadow: isFocused
                ? '0 0 0 3px rgba(0,212,255,0.08), 0 20px 60px rgba(0,0,0,0.4)'
                : '0 20px 60px rgba(0,0,0,0.3)',
              backdropFilter: 'blur(20px)',
            }}
          >
            {/* Input label */}
            <div className="px-5 pt-4 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-cyan-400" style={{ boxShadow: '0 0 6px #00d4ff' }} />
              <span className="text-slate-500" style={{ fontSize: '11px', letterSpacing: '0.12em', fontFamily: 'JetBrains Mono, monospace' }}>
                RESEARCH QUESTION
              </span>
            </div>

            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              onKeyDown={(e) => { if (e.key === 'Enter' && e.metaKey) handleSubmit(); }}
              placeholder="e.g. What is the effect of CRISPR-Cas9 targeting of APOE4 on amyloid-beta accumulation in iPSC-derived Alzheimer's neurons?"
              rows={4}
              className="w-full resize-none bg-transparent px-5 py-4 outline-none placeholder-slate-600"
              style={{
                color: '#e2e8f0',
                fontFamily: 'Inter, sans-serif',
                fontSize: '15px',
                lineHeight: 1.7,
              }}
            />

            {/* Bottom bar */}
            <div className="px-5 pb-4 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <span className="text-slate-600" style={{ fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' }}>
                  {charCount} chars
                </span>
                <span className="text-slate-600" style={{ fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' }}>
                  ⌘ + Enter to submit
                </span>
              </div>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleSubmit}
                disabled={!isReady}
                className="flex items-center gap-2.5 px-5 py-2.5 rounded-xl transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed"
                style={{
                  background: isReady
                    ? 'linear-gradient(135deg, #00d4ff, #0ea5e9)'
                    : 'rgba(0,212,255,0.1)',
                  boxShadow: isReady ? '0 0 20px rgba(0,212,255,0.3)' : 'none',
                  color: isReady ? '#000' : '#4b5563',
                  fontFamily: 'Space Grotesk, sans-serif',
                  fontWeight: 600,
                  fontSize: '14px',
                }}
              >
                Initiate Analysis
                <ArrowRight size={15} />
              </motion.button>
            </div>
          </div>
        </motion.div>

        {/* Example questions */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="w-full"
        >
          <p className="text-slate-600 text-center mb-3" style={{ fontSize: '11px', letterSpacing: '0.1em', fontFamily: 'JetBrains Mono, monospace' }}>
            — EXAMPLE QUESTIONS —
          </p>
          <div className="flex flex-col gap-2">
            {EXAMPLE_QUESTIONS.slice(0, 3).map((q, idx) => (
              <motion.button
                key={idx}
                whileHover={{ x: 4 }}
                onClick={() => handleExampleClick(q, idx)}
                className="group flex items-start gap-3 px-4 py-3 rounded-xl text-left transition-all duration-200"
                style={{
                  background: activeExample === idx
                    ? 'rgba(0,212,255,0.08)'
                    : 'rgba(255,255,255,0.02)',
                  border: activeExample === idx
                    ? '1px solid rgba(0,212,255,0.25)'
                    : '1px solid rgba(255,255,255,0.05)',
                }}
              >
                <ChevronRight size={14} className="text-cyan-600 mt-0.5 shrink-0 group-hover:text-cyan-400 transition-colors" />
                <span className="text-slate-400 group-hover:text-slate-300 transition-colors"
                  style={{ fontSize: '13px', lineHeight: 1.5, fontFamily: 'Inter, sans-serif' }}>
                  {q}
                </span>
              </motion.button>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Bottom status bar */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        className="absolute bottom-6 flex items-center gap-6"
      >
        {['PubMed · 35M+ papers', 'bioRxiv · 220K+ preprints', 'Scopus · 90M+ records', 'ClinicalTrials.gov'].map((db) => (
          <div key={db} className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" style={{ boxShadow: '0 0 4px #10b981' }} />
            <span className="text-slate-600" style={{ fontSize: '10px', fontFamily: 'JetBrains Mono, monospace' }}>{db}</span>
          </div>
        ))}
      </motion.div>
    </div>
  );
}
