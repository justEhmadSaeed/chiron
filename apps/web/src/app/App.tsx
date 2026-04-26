import { useState, useCallback } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { AppStage, QCResult, ExperimentPlanData, FeedbackStore } from './components/planner/types';
import { InputStage } from './components/planner/InputStage';
import { ScanningStage } from './components/planner/ScanningStage';
import { QCResults } from './components/planner/QCResults';
import { PlanningStage } from './components/planner/PlanningStage';
import { ExperimentPlan } from './components/planner/ExperimentPlan';
import { MOCK_QC_RESULT, MOCK_PLAN } from './components/planner/mockData';

// Stage progress indicator at top
const STAGE_META = [
  { id: 'input', label: 'Question' },
  { id: 'scanning', label: 'Literature QC' },
  { id: 'qc_results', label: 'QC Results' },
  { id: 'planning', label: 'Generating' },
  { id: 'plan', label: 'Experiment Plan' },
];

const STAGE_ORDER = ['input', 'scanning', 'qc_results', 'planning', 'plan', 'review'] as AppStage[];

function StageIndicator({ current }: { current: AppStage }) {
  const currentIdx = STAGE_META.findIndex((s) => s.id === current);
  const displayStages = STAGE_META.filter((s) => s.id !== 'review');

  if (current === 'input') return null;

  return (
    <div
      className="fixed top-0 left-0 right-0 z-50 flex items-center justify-center py-2 gap-1"
      style={{ background: 'rgba(2, 10, 25, 0.85)', backdropFilter: 'blur(20px)', borderBottom: '1px solid rgba(255,255,255,0.04)' }}
    >
      {displayStages.map((stage, idx) => {
        const stageIdx = STAGE_META.findIndex((s) => s.id === stage.id);
        const isCompleted = currentIdx > stageIdx;
        const isActive = stageIdx === currentIdx || (current === 'review' && stageIdx === displayStages.length - 1);

        return (
          <div key={stage.id} className="flex items-center gap-1">
            <div className="flex items-center gap-1.5">
              <div
                className="w-5 h-5 rounded-full flex items-center justify-center transition-all duration-300"
                style={{
                  background: isCompleted || isActive
                    ? isActive ? 'rgba(0,212,255,0.15)' : 'rgba(0,212,255,0.08)'
                    : 'rgba(255,255,255,0.04)',
                  border: isCompleted || isActive
                    ? `1px solid ${isActive ? 'rgba(0,212,255,0.5)' : 'rgba(0,212,255,0.2)'}`
                    : '1px solid rgba(255,255,255,0.08)',
                }}
              >
                {isCompleted ? (
                  <div className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                ) : isActive ? (
                  <motion.div
                    className="w-1.5 h-1.5 rounded-full bg-cyan-400"
                    animate={{ scale: [1, 1.4, 1] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                  />
                ) : (
                  <div className="w-1.5 h-1.5 rounded-full bg-slate-700" />
                )}
              </div>
              <span
                style={{
                  fontSize: '11px',
                  fontFamily: 'JetBrains Mono, monospace',
                  color: isActive ? '#00d4ff' : isCompleted ? '#475569' : '#2d3748',
                  letterSpacing: '0.04em',
                  transition: 'color 0.3s',
                }}
              >
                {stage.label}
              </span>
            </div>
            {idx < displayStages.length - 1 && (
              <div className="w-8 h-px mx-1"
                style={{ background: isCompleted ? 'rgba(0,212,255,0.25)' : 'rgba(255,255,255,0.06)' }} />
            )}
          </div>
        );
      })}
    </div>
  );
}

export default function App() {
  const [stage, setStage] = useState<AppStage>('input');
  const [question, setQuestion] = useState('');
  const [qcResult, setQcResult] = useState<QCResult | null>(null);
  const [plan, setPlan] = useState<ExperimentPlanData | null>(null);
  const [feedbackHistory, setFeedbackHistory] = useState<FeedbackStore[]>([]);

  const hasPriorFeedback = feedbackHistory.length > 0;

  const handleQuestionSubmit = useCallback((q: string) => {
    setQuestion(q);
    setStage('scanning');
  }, []);

  const handleScanComplete = useCallback(() => {
    setQcResult(MOCK_QC_RESULT);
    setStage('qc_results');
  }, []);

  const handleGenerate = useCallback(() => {
    setStage('planning');
  }, []);

  const handlePlanComplete = useCallback(() => {
    setPlan(MOCK_PLAN);
    setStage('plan');
  }, []);

  const handleNewPlan = useCallback(() => {
    setStage('input');
    setQuestion('');
    setQcResult(null);
    setPlan(null);
  }, []);

  const handleRedo = useCallback(() => {
    setStage('input');
    setQcResult(null);
  }, []);

  const showTopBar = stage !== 'input';
  const topPadding = showTopBar ? 'pt-8' : '';

  return (
    <div className="w-full h-screen overflow-hidden flex flex-col"
      style={{ background: '#020c1b', fontFamily: 'Inter, sans-serif' }}>

      <StageIndicator current={stage} />

      <div className={`flex-1 overflow-hidden ${topPadding}`}>
        <AnimatePresence mode="wait">
          {stage === 'input' && (
            <motion.div
              key="input"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0, scale: 0.98 }}
              transition={{ duration: 0.35 }}
              className="w-full h-full"
            >
              <InputStage onSubmit={handleQuestionSubmit} />
            </motion.div>
          )}

          {stage === 'scanning' && (
            <motion.div
              key="scanning"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4 }}
              className="w-full h-full"
            >
              <ScanningStage question={question} onComplete={handleScanComplete} />
            </motion.div>
          )}

          {stage === 'qc_results' && qcResult && (
            <motion.div
              key="qc_results"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4 }}
              className="w-full h-full"
            >
              <QCResults
                question={question}
                result={qcResult}
                onGenerate={handleGenerate}
                onRedo={handleRedo}
              />
            </motion.div>
          )}

          {stage === 'planning' && (
            <motion.div
              key="planning"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4 }}
              className="w-full h-full"
            >
              <PlanningStage
                question={question}
                hasPriorFeedback={hasPriorFeedback}
                onComplete={handlePlanComplete}
              />
            </motion.div>
          )}

          {(stage === 'plan' || stage === 'review') && plan && qcResult && (
            <motion.div
              key="plan"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.4 }}
              className="w-full h-full"
            >
              <ExperimentPlan
                plan={plan}
                qcResult={qcResult}
                question={question}
                hasPriorFeedback={hasPriorFeedback}
                onNewPlan={handleNewPlan}
                onFeedbackSubmit={() => setFeedbackHistory((prev) => [...prev, { planId: Date.now().toString(), question, reviews: [], submittedAt: new Date().toISOString(), domain: 'Genomics' }])}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}