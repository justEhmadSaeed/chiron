import type { 
  QCResult, 
  Reference, 
  ExperimentPlanData, 
  ProtocolPhase, 
  ProtocolStep, 
  Material, 
  BudgetCategory, 
  TimelinePhase, 
  ValidationMetric 
} from "@chiron/contracts";

export type AppStage = "input" | "scanning" | "qc_results" | "planning" | "plan" | "review";

export type { 
  QCResult, 
  Reference, 
  ExperimentPlanData, 
  ProtocolPhase, 
  ProtocolStep, 
  Material, 
  BudgetCategory, 
  TimelinePhase, 
  ValidationMetric 
};

export type NoveltySignal = "not_found" | "similar_work" | "exact_match";

export interface SectionReview {
  sectionId: string;
  sectionTitle: string;
  rating: number;
  comment: string;
  corrections: string;
  tags: string[];
  timestamp: string;
}

export interface FeedbackStore {
  planId: string;
  question: string;
  reviews: SectionReview[];
  submittedAt: string;
  domain: string;
}
