export type AppStage =
  | 'input'
  | 'scanning'
  | 'qc_results'
  | 'planning'
  | 'plan'
  | 'review';

export type NoveltySignal = 'not_found' | 'similar_work' | 'exact_match';

export interface Reference {
  id: string;
  title: string;
  authors: string;
  journal: string;
  year: number;
  doi: string;
  similarity: number;
  type: 'preprint' | 'journal' | 'review';
}

export interface QCResult {
  signal: NoveltySignal;
  noveltyScore: number;
  references: Reference[];
  scanDuration: number;
  databases: string[];
}

export interface ProtocolStep {
  id: number;
  title: string;
  detail: string;
  duration: string;
  critical: boolean;
  notes?: string;
}

export interface ProtocolPhase {
  phase: string;
  weekRange: string;
  steps: ProtocolStep[];
}

export interface Material {
  id: number;
  name: string;
  catalog: string;
  supplier: string;
  unitCost: number;
  qty: number;
  unit: string;
  total: number;
  category: string;
  leadTime: string;
}

export interface BudgetCategory {
  name: string;
  amount: number;
  color: string;
  percentage: number;
}

export interface TimelinePhase {
  phase: string;
  start: number;
  duration: number;
  tasks: string[];
  color: string;
  dependencies?: string[];
}

export interface ValidationMetric {
  metric: string;
  target: string;
  method: string;
  critical: boolean;
  timepoint: string;
}

export interface ExperimentPlanData {
  title: string;
  question: string;
  createdAt: string;
  complexity: 'Low' | 'Medium' | 'High' | 'Very High';
  teamSize: number;
  totalWeeks: number;
  overview: string;
  hypothesis: string;
  protocol: ProtocolPhase[];
  materials: Material[];
  budget: {
    total: number;
    categories: BudgetCategory[];
  };
  timeline: TimelinePhase[];
  validation: ValidationMetric[];
}

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
