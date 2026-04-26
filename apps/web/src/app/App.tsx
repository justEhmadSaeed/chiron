import type { ExperimentPlanData, QCResult, ExperimentFeedback } from "@chiron/contracts";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Route, Routes, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { agentEventsWebSocketUrl, apiUrl } from "../lib/backendUrl";
import { ExperimentPlan } from "./components/planner/ExperimentPlan";
import { InputStage } from "./components/planner/InputStage";
import { PlanningStage } from "./components/planner/PlanningStage";
import { QCResults } from "./components/planner/QCResults";
import { ScanningStage } from "./components/planner/ScanningStage";
import type { AppStage, FeedbackStore } from "./components/planner/types";

// Stage progress indicator at top
const STAGE_META = [
  { id: "input", label: "Question" },
  { id: "scanning", label: "Literature QC" },
  { id: "qc_results", label: "QC Results" },
  { id: "planning", label: "Generating" },
  { id: "plan", label: "Experiment Plan" }
];

function StageIndicator({ current }: { current: AppStage }) {
  const currentIdx = STAGE_META.findIndex((s) => s.id === current);
  const displayStages = STAGE_META.filter((s) => s.id !== "review");

  if (current === "input") return null;

  return (
    <div
      className="fixed top-0 left-0 right-0 z-50 flex items-center justify-center py-2 gap-1"
      style={{
        background: "rgba(2, 10, 25, 0.85)",
        backdropFilter: "blur(20px)",
        borderBottom: "1px solid rgba(255,255,255,0.04)"
      }}
    >
      {displayStages.map((stage, idx) => {
        const stageIdx = STAGE_META.findIndex((s) => s.id === stage.id);
        const isCompleted = currentIdx > stageIdx;
        const isActive =
          stageIdx === currentIdx ||
          (current === "review" && stageIdx === displayStages.length - 1);

        return (
          <div key={stage.id} className="flex items-center gap-1">
            <div className="flex items-center gap-1.5">
              <div
                className="w-5 h-5 rounded-full flex items-center justify-center transition-all duration-300"
                style={{
                  background:
                    isCompleted || isActive
                      ? isActive
                        ? "rgba(0,212,255,0.15)"
                        : "rgba(0,212,255,0.08)"
                      : "rgba(255,255,255,0.04)",
                  border:
                    isCompleted || isActive
                      ? `1px solid ${isActive ? "rgba(0,212,255,0.5)" : "rgba(0,212,255,0.2)"}`
                      : "1px solid rgba(255,255,255,0.08)"
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
                  fontSize: "11px",
                  fontFamily: "JetBrains Mono, monospace",
                  color: isActive ? "#00d4ff" : isCompleted ? "#475569" : "#2d3748",
                  letterSpacing: "0.04em",
                  transition: "color 0.3s"
                }}
              >
                {stage.label}
              </span>
            </div>
            {idx < displayStages.length - 1 && (
              <div
                className="w-8 h-px mx-1"
                style={{
                  background: isCompleted ? "rgba(0,212,255,0.25)" : "rgba(255,255,255,0.06)"
                }}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

function ExperimentViewer() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  // Track whether the backend has signalled completion via WebSocket
  const [isLQCReady, setIsLQCReady] = useState(false);
  const [isPlanReady, setIsPlanReady] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const {
    data: experiment,
    isError,
    isLoading
  } = useQuery({
    queryKey: ["experiment", id],
    queryFn: async () => {
      const res = await fetch(apiUrl(`/api/experiments/${id}`));
      if (!res.ok) throw new Error("Failed to fetch");
      return res.json();
    },
    // Keep a slow poll as a silent fallback in case WS is unavailable
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "lqc_completed" || status === "completed") return false;
      return 5000;
    }
  });

  // Open WebSocket while we are in the scanning or planning stage and close it once done
  useEffect(() => {
    if (!id) return;
    // If the experiment is already past scanning/planning, skip WS
    if (experiment?.status && !["running", "planning"].includes(experiment.status)) return;

    const ws = new WebSocket(agentEventsWebSocketUrl());
    wsRef.current = ws;

    ws.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data as string) as {
          event_type: string;
          payload: { experiment_id?: string };
        };
        if (data.event_type === "LQC_COMPLETED" && data.payload.experiment_id === id) {
          setIsLQCReady(true);
          // Invalidate after the ScanningStage animation completes (~1.5 s)
          setTimeout(() => {
            queryClient.invalidateQueries({ queryKey: ["experiment", id] });
          }, 2000);
          ws.close();
        } else if (data.event_type === "PLAN_COMPLETED" && data.payload.experiment_id === id) {
          setIsPlanReady(true);
          // Invalidate after the PlanningStage animation completes
          setTimeout(() => {
            queryClient.invalidateQueries({ queryKey: ["experiment", id] });
          }, 2000);
          ws.close();
        }
      } catch {
        // ignore malformed messages
      }
    };

    ws.onerror = () => {
      // Silently ignore – polling fallback will still work
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
    // Re-run only when the experiment id or its status changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, experiment?.status]);

  const startPlanMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(apiUrl(`/api/experiments/${id}/start-plan`), { method: "POST" });
      if (!res.ok) throw new Error("Failed to start plan");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["experiment", id] });
    }
  });

  const submitFeedbackMutation = useMutation({
    mutationFn: async (feedback: ExperimentFeedback) => {
      const res = await fetch(apiUrl(`/api/experiments/${id}/feedback`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(feedback)
      });
      if (!res.ok) throw new Error("Failed to submit feedback");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["experiment", id] });
    }
  });

  const [feedbackHistory, setFeedbackHistory] = useState<FeedbackStore[]>([]);
  const hasPriorFeedback = feedbackHistory.length > 0;

  // Map backend status to AppStage
  let stage: AppStage = "scanning";
  if (experiment) {
    if (experiment.status === "running") stage = "scanning";
    else if (experiment.status === "lqc_completed") stage = "qc_results";
    else if (experiment.status === "planning") stage = "planning";
    else if (experiment.status === "completed") stage = "plan";
  }

  const handleScanComplete = useCallback(() => {
    // Stage transition is driven by WS / polling, not the animation itself
  }, []);

  const handleGenerate = useCallback(() => {
    startPlanMutation.mutate();
  }, [startPlanMutation]);

  const handleNewPlan = useCallback(() => {
    navigate("/");
  }, [navigate]);

  const handleRedo = useCallback(() => {
    const question = experiment?.question || "";
    navigate(`/?q=${encodeURIComponent(question)}`);
  }, [navigate, experiment]);

  const handleFeedbackSubmit = useCallback((feedback: ExperimentFeedback) => {
    submitFeedbackMutation.mutate(feedback);
  }, [submitFeedbackMutation]);

  if (isError) {
    return (
      <div
        className="flex items-center justify-center h-screen w-full text-white"
        style={{ background: "#020c1b" }}
      >
        Error loading experiment
      </div>
    );
  }

  if (isLoading) {
    return (
      <div
        className="flex flex-col items-center justify-center h-screen w-full text-white space-y-4"
        style={{ background: "#020c1b" }}
      >
        <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
        <span className="font-mono text-sm text-cyan-400/80">Loading Experiment...</span>
      </div>
    );
  }

  return (
    <div
      className="w-full h-screen overflow-hidden flex flex-col"
      style={{ background: "#020c1b", fontFamily: "Inter, sans-serif" }}
    >
      <StageIndicator current={stage} />

      <div className="flex-1 overflow-hidden pt-8">
        <AnimatePresence mode="wait">
          {stage === "scanning" && (
            <motion.div
              key="scanning"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4 }}
              className="w-full h-full"
            >
              <ScanningStage
                question={experiment?.question || ""}
                onComplete={handleScanComplete}
                isLQCReady={isLQCReady}
              />
            </motion.div>
          )}

          {stage === "qc_results" && experiment?.LQC && (
            <motion.div
              key="qc_results"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4 }}
              className="w-full h-full"
            >
              <QCResults
                question={experiment.question || ""}
                result={experiment.LQC as QCResult}
                onGenerate={handleGenerate}
                onRedo={handleRedo}
              />
            </motion.div>
          )}

          {stage === "planning" && (
            <motion.div
              key="planning"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4 }}
              className="w-full h-full"
            >
              <PlanningStage
                question={experiment?.question || ""}
                hasPriorFeedback={hasPriorFeedback}
                onComplete={() => {}}
                isPlanReady={isPlanReady}
              />
            </motion.div>
          )}

          {stage === "plan" && experiment?.plan && experiment?.LQC && (
            <motion.div
              key="plan"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.4 }}
              className="w-full h-full"
            >
              <ExperimentPlan
                plan={experiment.plan as ExperimentPlanData}
                qcResult={experiment.LQC as QCResult}
                question={experiment.question || ""}
                hasPriorFeedback={hasPriorFeedback}
                feedback={experiment.feedback || undefined}
                onNewPlan={handleNewPlan}
                onFeedbackSubmit={(feedback: ExperimentFeedback) => {
                  setFeedbackHistory((prev) => [
                    ...prev,
                    {
                      planId: Date.now().toString(),
                      question: experiment?.question || "",
                      reviews: [],
                      submittedAt: new Date().toISOString(),
                      domain: "Genomics"
                    }
                  ]);
                  handleFeedbackSubmit(feedback);
                }}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function Home() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialQuestion = searchParams.get("q") || undefined;

  const [isGenerating, setIsGenerating] = useState(false);

  const generateMutation = useMutation({
    mutationFn: async (question: string) => {
      const res = await fetch(apiUrl("/api/experiments/generate"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question })
      });
      if (!res.ok) throw new Error("Failed to generate");
      return res.json();
    },
    onSuccess: (data) => {
      navigate(`/experiment/${data.experiment_id}`);
    },
    onSettled: () => {
      setIsGenerating(false);
    }
  });

  const handleQuestionSubmit = useCallback(
    (q: string) => {
      setIsGenerating(true);
      generateMutation.mutate(q);
    },
    [generateMutation]
  );

  return (
    <div
      className="w-full h-screen overflow-hidden flex flex-col"
      style={{ background: "#020c1b", fontFamily: "Inter, sans-serif" }}
    >
      <AnimatePresence mode="wait">
        <motion.div
          key="input"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0, scale: 0.98 }}
          transition={{ duration: 0.35 }}
          className="w-full h-full relative"
        >
          <InputStage initialValue={initialQuestion} onSubmit={handleQuestionSubmit} />
          {isGenerating && (
            <div className="absolute inset-0 bg-black/50 z-50 flex flex-col items-center justify-center backdrop-blur-sm space-y-4">
              <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
              <div className="text-cyan-400 font-mono text-sm animate-pulse">
                Initializing Experiment...
              </div>
            </div>
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/experiment/:id" element={<ExperimentViewer />} />
    </Routes>
  );
}
