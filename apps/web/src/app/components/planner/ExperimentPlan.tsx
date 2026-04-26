import type { ExperimentFeedback } from "@chiron/contracts";
import {
  AlertCircle,
  ArrowLeft,
  Beaker,
  BookOpen,
  CalendarDays,
  CheckSquare,
  ChevronDown,
  ChevronRight,
  ChevronUp,
  Clock,
  DollarSign,
  Download,
  Layers,
  ListOrdered,
  MessageSquareQuote,
  Package,
  Pencil,
  Send,
  Shield,
  Sparkles,
  Star,
  ThumbsUp,
  TrendingUp,
  Users
} from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import type { ElementType, ReactNode } from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { PLANNER_NAV_SECTIONS, REVIEW_TAGS } from "./constants";
import { MolecularCanvas } from "./MolecularCanvas";
import type { ExperimentPlanData, QCResult, SectionReview } from "./types";
import { downloadMarkdownFile, generateMarkdownFromPlan } from "./utils/generateMarkdownFromPlan";

interface ExperimentPlanProps {
  plan: ExperimentPlanData;
  qcResult: QCResult;
  question: string;
  hasPriorFeedback?: boolean;
  feedback?: ExperimentFeedback;
  onNewPlan: () => void;
  onFeedbackSubmit?: (feedback: ExperimentFeedback) => void;
}

function NoveltyBadge({ signal }: { signal: string }) {
  const cfg = {
    similar_work: {
      label: "SIMILAR WORK",
      color: "#f59e0b",
      bg: "rgba(245,158,11,0.1)",
      border: "rgba(245,158,11,0.25)"
    },
    not_found: {
      label: "NOVEL",
      color: "#10b981",
      bg: "rgba(16,185,129,0.1)",
      border: "rgba(16,185,129,0.25)"
    },
    exact_match: {
      label: "PRIOR ART",
      color: "#f43f5e",
      bg: "rgba(244,63,94,0.1)",
      border: "rgba(244,63,94,0.25)"
    }
  }[signal] ?? {
    label: "UNKNOWN",
    color: "#94a3b8",
    bg: "rgba(148,163,184,0.1)",
    border: "rgba(148,163,184,0.25)"
  };

  return (
    <span
      className="px-2 py-0.5 rounded-md"
      style={{
        background: cfg.bg,
        border: `1px solid ${cfg.border}`,
        color: cfg.color,
        fontSize: "10px",
        fontFamily: "JetBrains Mono, monospace",
        letterSpacing: "0.05em"
      }}
    >
      {cfg.label}
    </span>
  );
}

function ComplexityBadge({ level }: { level: string }) {
  const colors: Record<string, string> = {
    Low: "#10b981",
    Medium: "#f59e0b",
    High: "#f97316",
    "Very High": "#f43f5e"
  };
  const color = colors[level] ?? "#94a3b8";
  return (
    <span
      className="px-2 py-0.5 rounded-md"
      style={{
        background: `${color}15`,
        border: `1px solid ${color}30`,
        color,
        fontSize: "10px",
        fontFamily: "JetBrains Mono, monospace"
      }}
    >
      {level.toUpperCase()} COMPLEXITY
    </span>
  );
}

function SectionCard({
  id,
  title,
  icon: Icon,
  reviewMode,
  sectionReview,
  onReviewSave,
  children
}: {
  id: string;
  title: string;
  icon: ElementType;
  reviewMode: boolean;
  sectionReview?: SectionReview;
  onReviewSave: (r: SectionReview) => void;
  children: ReactNode;
}) {
  const [showReview, setShowReview] = useState(false);
  const [rating, setRating] = useState(sectionReview?.rating ?? 0);
  const [hoverRating, setHoverRating] = useState(0);
  const [comment, setComment] = useState(sectionReview?.comment ?? "");
  const [corrections, setCorrections] = useState(sectionReview?.corrections ?? "");
  const [selectedTags, setSelectedTags] = useState<string[]>(sectionReview?.tags ?? []);
  const [submitted, setSubmitted] = useState(!!sectionReview);

  const toggleTag = (tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  const handleSubmit = () => {
    onReviewSave({
      sectionId: id,
      sectionTitle: title,
      rating,
      comment,
      corrections,
      tags: selectedTags,
      timestamp: new Date().toISOString()
    });
    setSubmitted(true);
    setShowReview(false);
  };

  return (
    <section id={id} className="scroll-mt-24">
      <div
        className="rounded-2xl overflow-hidden"
        style={{
          background: "rgba(10,18,32,0.85)",
          border: "1px solid rgba(255,255,255,0.07)",
          backdropFilter: "blur(12px)"
        }}
      >
        {/* Section header */}
        <div
          className="px-6 py-4 flex items-center justify-between"
          style={{
            borderBottom: "1px solid rgba(255,255,255,0.05)",
            background: "rgba(0,0,0,0.2)"
          }}
        >
          <div className="flex items-center gap-3">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{
                background: "rgba(0,212,255,0.08)",
                border: "1px solid rgba(0,212,255,0.15)"
              }}
            >
              <Icon size={15} className="text-cyan-400" />
            </div>
            <h2
              className="text-white"
              style={{ fontFamily: "Space Grotesk, sans-serif", fontSize: "15px", fontWeight: 600 }}
            >
              {title}
            </h2>
          </div>
          {reviewMode && (
            <div className="flex items-center gap-2">
              {submitted && (
                <span
                  className="flex items-center gap-1 text-emerald-400"
                  style={{ fontSize: "11px", fontFamily: "JetBrains Mono, monospace" }}
                >
                  <ThumbsUp size={11} /> Reviewed
                </span>
              )}
              <button
                onClick={() => setShowReview(!showReview)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all"
                style={{
                  background: showReview ? "rgba(124,58,237,0.15)" : "rgba(255,255,255,0.04)",
                  border: showReview
                    ? "1px solid rgba(124,58,237,0.4)"
                    : "1px solid rgba(255,255,255,0.08)",
                  color: showReview ? "#a78bfa" : "#64748b",
                  fontSize: "12px",
                  fontFamily: "Space Grotesk, sans-serif"
                }}
              >
                <Pencil size={12} />
                {showReview ? "Hide" : "Review"}
              </button>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="p-6">{children}</div>

        {/* Review panel */}
        <AnimatePresence>
          {showReview && reviewMode && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div
                className="px-6 pb-6 pt-0"
                style={{
                  borderTop: "1px solid rgba(124,58,237,0.2)",
                  background: "rgba(124,58,237,0.04)"
                }}
              >
                <div className="pt-5 space-y-4">
                  <p
                    className="text-purple-400"
                    style={{
                      fontSize: "12px",
                      fontFamily: "JetBrains Mono, monospace",
                      letterSpacing: "0.08em"
                    }}
                  >
                    ✦ SCIENTIST REVIEW — {title.toUpperCase()}
                  </p>

                  {/* Star rating */}
                  <div>
                    <p className="text-slate-400 mb-2" style={{ fontSize: "12px" }}>
                      Quality Rating
                    </p>
                    <div className="flex gap-1">
                      {[1, 2, 3, 4, 5].map((s) => (
                        <button
                          key={s}
                          onMouseEnter={() => setHoverRating(s)}
                          onMouseLeave={() => setHoverRating(0)}
                          onClick={() => setRating(s)}
                          className="transition-all"
                        >
                          <Star
                            size={22}
                            className={
                              s <= (hoverRating || rating)
                                ? "text-amber-400 fill-amber-400"
                                : "text-slate-700"
                            }
                          />
                        </button>
                      ))}
                      {rating > 0 && (
                        <span
                          className="ml-2 text-slate-400 self-center"
                          style={{ fontSize: "12px" }}
                        >
                          {["", "Poor", "Fair", "Good", "Very Good", "Excellent"][rating]}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Tags */}
                  <div>
                    <p className="text-slate-400 mb-2" style={{ fontSize: "12px" }}>
                      Issue Tags
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {REVIEW_TAGS.map((tag) => (
                        <button
                          key={tag}
                          onClick={() => toggleTag(tag)}
                          className="px-2.5 py-1 rounded-md text-xs transition-all"
                          style={{
                            background: selectedTags.includes(tag)
                              ? "rgba(124,58,237,0.2)"
                              : "rgba(255,255,255,0.04)",
                            border: selectedTags.includes(tag)
                              ? "1px solid rgba(124,58,237,0.5)"
                              : "1px solid rgba(255,255,255,0.08)",
                            color: selectedTags.includes(tag) ? "#a78bfa" : "#64748b",
                            fontFamily: "JetBrains Mono, monospace"
                          }}
                        >
                          {tag}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Comment */}
                  <div>
                    <p className="text-slate-400 mb-2" style={{ fontSize: "12px" }}>
                      Annotation
                    </p>
                    <textarea
                      value={comment}
                      onChange={(e) => setComment(e.target.value)}
                      placeholder="Add contextual notes, observations, or domain expertise..."
                      rows={2}
                      className="w-full rounded-xl px-4 py-3 resize-none outline-none text-slate-300 placeholder-slate-600"
                      style={{
                        background: "rgba(0,0,0,0.3)",
                        border: "1px solid rgba(255,255,255,0.08)",
                        fontSize: "13px",
                        fontFamily: "Inter, sans-serif",
                        lineHeight: 1.6
                      }}
                    />
                  </div>

                  {/* Corrections */}
                  <div>
                    <p className="text-slate-400 mb-2" style={{ fontSize: "12px" }}>
                      Corrections / Suggested Changes
                    </p>
                    <textarea
                      value={corrections}
                      onChange={(e) => setCorrections(e.target.value)}
                      placeholder="e.g. 'Use Synthego sgRNA at 50 nM, not 100 nM. Protocol ref: PMID 34567890'"
                      rows={2}
                      className="w-full rounded-xl px-4 py-3 resize-none outline-none placeholder-slate-600"
                      style={{
                        background: "rgba(0,0,0,0.3)",
                        border: "1px solid rgba(255,255,255,0.08)",
                        fontSize: "13px",
                        fontFamily: "JetBrains Mono, monospace",
                        lineHeight: 1.6,
                        color: "#93c5fd"
                      }}
                    />
                  </div>

                  <button
                    onClick={handleSubmit}
                    disabled={rating === 0}
                    className="flex items-center gap-2 px-4 py-2.5 rounded-xl transition-all disabled:opacity-40"
                    style={{
                      background: "rgba(124,58,237,0.2)",
                      border: "1px solid rgba(124,58,237,0.4)",
                      color: "#a78bfa",
                      fontSize: "13px",
                      fontFamily: "Space Grotesk, sans-serif",
                      fontWeight: 600
                    }}
                  >
                    <Send size={13} /> Submit Review
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </section>
  );
}

export function ExperimentPlan({
  plan,
  qcResult,
  hasPriorFeedback = false,
  feedback,
  onNewPlan,
  onFeedbackSubmit
}: ExperimentPlanProps) {
  const [activeSection, setActiveSection] = useState("overview");
  const [reviewMode, setReviewMode] = useState(!!feedback);
  const [expandedSteps, setExpandedSteps] = useState<number[]>([]);

  // Initialize reviews from dictionary mapping
  const initialReviews = useMemo(() => {
    if (!feedback) return {};
    const parsed: Record<string, SectionReview> = {};

    Object.entries(feedback).forEach(([sectionId, fb]) => {
      const sec = PLANNER_NAV_SECTIONS.find((s) => s.id === sectionId);
      parsed[sectionId] = {
        sectionId,
        sectionTitle: sec ? sec.label : sectionId,
        rating: fb.rating || 0,
        comment: fb.annotation || "",
        corrections: fb.corrections || "",
        tags: fb.issue_tags || [],
        timestamp: new Date().toISOString()
      };
    });

    return parsed;
  }, [feedback]);

  const [reviews, setReviews] = useState<Record<string, SectionReview>>(initialReviews);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [materialSort, setMaterialSort] = useState<"category" | "cost" | "name">("category");
  const [showCoachMark, setShowCoachMark] = useState(() => {
    try {
      return !localStorage.getItem("chiron_review_onboarded");
    } catch {
      return true;
    }
  });
  const [fabHovered, setFabHovered] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);

  const handleExportMarkdown = useCallback(() => {
    setIsExporting(true);
    try {
      const markdown = generateMarkdownFromPlan(plan);
      const slug = plan.title
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/(^-|-$)/g, "");
      downloadMarkdownFile(markdown, `${slug || "experiment-plan"}.md`);
    } finally {
      setIsExporting(false);
    }
  }, [plan]);

  const dismissCoachMark = useCallback(() => {
    setShowCoachMark(false);
    try {
      localStorage.setItem("chiron_review_onboarded", "1");
    } catch {
      console.error("Failed to save coach mark to localStorage");
    }
  }, []);

  const toggleReviewMode = useCallback(() => {
    dismissCoachMark();
    setReviewMode((v) => !v);
  }, [dismissCoachMark]);

  const toggleStep = (id: number) =>
    setExpandedSteps((prev) => (prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]));

  const handleReviewSave = (r: SectionReview) =>
    setReviews((prev) => ({ ...prev, [r.sectionId]: r }));

  const totalReviews = Object.keys(reviews).length;

  const handleFinalSubmit = () => {
    setFeedbackSubmitted(true);

    const payload: ExperimentFeedback = {};
    Object.entries(reviews).forEach(([sectionId, review]) => {
      // Only include sections with actual feedback
      if (review.rating > 0 || review.comment || review.corrections || review.tags.length > 0) {
        payload[sectionId] = {
          rating: review.rating,
          issue_tags: review.tags,
          annotation: review.comment,
          corrections: review.corrections
        };
      }
    });

    onFeedbackSubmit?.(payload);

    setTimeout(() => setFeedbackSubmitted(false), 4000);
  };

  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    setActiveSection(id);
  };

  // Scroll spy
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) setActiveSection(e.target.id);
        });
      },
      { rootMargin: "-30% 0px -60% 0px", threshold: 0 }
    );
    PLANNER_NAV_SECTIONS.forEach(({ id }) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, []);

  const sortedMaterials = [...(plan.materials ?? [])].sort((a, b) => {
    if (materialSort === "cost") return b.total - a.total;
    if (materialSort === "name") return a.name.localeCompare(b.name);
    return a.category.localeCompare(b.category);
  });

  return (
    <div
      className="relative flex h-full overflow-hidden"
      style={{ background: "linear-gradient(160deg, #020c1b 0%, #050d1e 100%)" }}
    >
      {/* Subtle background */}
      <div className="absolute inset-0 pointer-events-none opacity-20">
        <MolecularCanvas density={20} />
      </div>

      {/* ── LEFT SIDEBAR ── */}
      <div
        className="relative z-10 w-56 shrink-0 flex flex-col h-full py-6 px-4"
        style={{
          borderRight: "1px solid rgba(255,255,255,0.05)",
          background: "rgba(5,10,20,0.6)",
          backdropFilter: "blur(20px)"
        }}
      >
        {/* Logo */}
        <div className="flex items-center gap-2 mb-8 px-2">
          <Beaker size={16} className="text-cyan-400" />
          <span
            className="text-white"
            style={{
              fontFamily: "Space Grotesk, sans-serif",
              fontWeight: 600,
              fontSize: "14px",
              letterSpacing: "0.04em"
            }}
          >
            CHI<span className="text-cyan-400">RON</span>
          </span>
        </div>

        {/* Nav */}
        <nav className="space-y-1 flex-1">
          <p
            className="text-slate-600 px-2 mb-2"
            style={{
              fontSize: "10px",
              letterSpacing: "0.1em",
              fontFamily: "JetBrains Mono, monospace"
            }}
          >
            SECTIONS
          </p>
          {PLANNER_NAV_SECTIONS.map(({ id, label, icon: Icon }) => {
            const isActive = activeSection === id;
            const isReviewed = reviews[id];
            return (
              <button
                key={id}
                onClick={() => scrollTo(id)}
                className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-left transition-all group"
                style={{
                  background: isActive ? "rgba(0,212,255,0.1)" : "transparent",
                  border: isActive ? "1px solid rgba(0,212,255,0.2)" : "1px solid transparent"
                }}
              >
                <Icon
                  size={14}
                  className={`transition-colors ${isActive ? "text-cyan-400" : "text-slate-600 group-hover:text-slate-400"}`}
                />
                <span
                  className={`flex-1 transition-colors ${isActive ? "text-cyan-300" : "text-slate-500 group-hover:text-slate-300"}`}
                  style={{ fontSize: "13px", fontFamily: "Inter, sans-serif" }}
                >
                  {label}
                </span>
                {reviewMode && isReviewed && (
                  <div className="w-2 h-2 rounded-full bg-emerald-400" />
                )}
                {isActive && <ChevronRight size={12} className="text-cyan-500" />}
              </button>
            );
          })}
        </nav>

        {/* Plan stats */}
        <div
          className="rounded-xl p-3 mt-4 space-y-2"
          style={{ background: "rgba(0,0,0,0.3)", border: "1px solid rgba(255,255,255,0.05)" }}
        >
          <p
            className="text-slate-600"
            style={{
              fontSize: "10px",
              letterSpacing: "0.1em",
              fontFamily: "JetBrains Mono, monospace"
            }}
          >
            PLAN STATS
          </p>
          {[
            { label: "Cost", value: `$${plan.budget.total.toLocaleString()}`, icon: DollarSign },
            { label: "Duration", value: `${plan.totalWeeks} weeks`, icon: Clock },
            { label: "Team", value: `${plan.teamSize} FTEs`, icon: Users }
          ].map(({ label, value, icon: Icon }) => (
            <div key={label} className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <Icon size={10} className="text-slate-600" />
                <span
                  className="text-slate-600"
                  style={{ fontSize: "11px", fontFamily: "JetBrains Mono, monospace" }}
                >
                  {label}
                </span>
              </div>
              <span
                className="text-cyan-400"
                style={{ fontSize: "11px", fontFamily: "JetBrains Mono, monospace" }}
              >
                {value}
              </span>
            </div>
          ))}
        </div>

        {/* New plan button */}
        <button
          onClick={onNewPlan}
          className="mt-3 w-full flex items-center justify-center gap-2 py-2 rounded-xl transition-all"
          style={{
            background: "rgba(255,255,255,0.03)",
            border: "1px solid rgba(255,255,255,0.07)",
            color: "#4b5563",
            fontSize: "12px",
            fontFamily: "Space Grotesk, sans-serif"
          }}
        >
          <ArrowLeft size={12} /> New Plan
        </button>
      </div>

      {/* ── MAIN CONTENT ── */}
      <div ref={contentRef} className="relative z-10 flex-1 overflow-y-auto">
        {/* Sticky header */}
        <div
          className="sticky top-0 z-20 px-6 py-3 flex items-center justify-between"
          style={{
            background: "rgba(5,10,20,0.9)",
            borderBottom: "1px solid rgba(255,255,255,0.05)",
            backdropFilter: "blur(20px)"
          }}
        >
          <div className="flex items-center gap-3 min-w-0">
            <div className="min-w-0">
              <p
                className="text-white truncate"
                style={{
                  fontFamily: "Space Grotesk, sans-serif",
                  fontSize: "14px",
                  fontWeight: 600,
                  maxWidth: "400px"
                }}
              >
                {plan.title}
              </p>
              <div className="flex items-center gap-2 mt-0.5">
                <NoveltyBadge signal={qcResult?.signal ?? "not_found"} />
                <ComplexityBadge level={plan.complexity} />
                <span
                  className="text-slate-600"
                  style={{ fontSize: "10px", fontFamily: "JetBrains Mono, monospace" }}
                >
                  {plan.createdAt}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {hasPriorFeedback && (
              <div
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-full"
                style={{
                  background: "rgba(124,58,237,0.1)",
                  border: "1px solid rgba(124,58,237,0.25)"
                }}
              >
                <MessageSquareQuote size={11} className="text-purple-400" />
                <span
                  className="text-purple-400"
                  style={{ fontSize: "10px", fontFamily: "JetBrains Mono, monospace" }}
                >
                  Prior corrections applied
                </span>
              </div>
            )}
            <button
              onClick={toggleReviewMode}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all"
              style={{
                background: reviewMode ? "rgba(124,58,237,0.15)" : "rgba(255,255,255,0.04)",
                border: reviewMode
                  ? "1px solid rgba(124,58,237,0.4)"
                  : "1px solid rgba(255,255,255,0.08)",
                color: reviewMode ? "#a78bfa" : "#64748b",
                fontSize: "12px",
                fontFamily: "Space Grotesk, sans-serif"
              }}
            >
              <Pencil size={12} />
              {reviewMode ? "Exit Review" : "Review Mode"}
            </button>
            <button
              onClick={handleExportMarkdown}
              disabled={isExporting}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all disabled:opacity-50 cursor-pointer"
              style={{
                background: "rgba(0,212,255,0.08)",
                border: "1px solid rgba(0,212,255,0.2)",
                color: "#00d4ff",
                fontSize: "12px",
                fontFamily: "Space Grotesk, sans-serif"
              }}
            >
              {isExporting ? (
                <>
                  <div
                    className="w-3 h-3 rounded-full border-2 border-t-transparent animate-spin"
                    style={{ borderColor: "rgba(0,212,255,0.3)", borderTopColor: "#00d4ff" }}
                  />
                  Exporting...
                </>
              ) : (
                <>
                  <Download size={12} /> Export
                </>
              )}
            </button>
          </div>
        </div>

        {/* Review mode banner */}
        <AnimatePresence>
          {reviewMode && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div
                className="px-6 py-3 flex items-center justify-between"
                style={{
                  background: "rgba(124,58,237,0.08)",
                  borderBottom: "1px solid rgba(124,58,237,0.2)"
                }}
              >
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-purple-400 animate-pulse" />
                  <span
                    className="text-purple-300"
                    style={{
                      fontSize: "12px",
                      fontFamily: "Space Grotesk, sans-serif",
                      fontWeight: 600
                    }}
                  >
                    SCIENTIST REVIEW MODE
                  </span>
                  <span
                    className="text-purple-500"
                    style={{ fontSize: "11px", fontFamily: "Inter, sans-serif" }}
                  >
                    Expand each section to rate, annotate, and submit corrections. Your feedback
                    trains the model.
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span
                    className="text-purple-400"
                    style={{ fontSize: "11px", fontFamily: "JetBrains Mono, monospace" }}
                  >
                    {totalReviews}/{PLANNER_NAV_SECTIONS.length} reviewed
                  </span>
                  {totalReviews > 0 && (
                    <button
                      onClick={handleFinalSubmit}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg"
                      style={{
                        background: "rgba(124,58,237,0.2)",
                        border: "1px solid rgba(124,58,237,0.4)",
                        color: "#a78bfa",
                        fontSize: "12px",
                        fontFamily: "Space Grotesk, sans-serif"
                      }}
                    >
                      <Send size={11} /> Submit All Feedback
                    </button>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Feedback success toast */}
        <AnimatePresence>
          {feedbackSubmitted && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="fixed top-20 right-6 z-50 rounded-xl px-5 py-3 flex items-center gap-3"
              style={{
                background: "rgba(16,185,129,0.15)",
                border: "1px solid rgba(16,185,129,0.35)",
                backdropFilter: "blur(20px)",
                boxShadow: "0 0 30px rgba(16,185,129,0.2)"
              }}
            >
              <Sparkles size={16} className="text-emerald-400" />
              <div>
                <p
                  className="text-emerald-300"
                  style={{
                    fontSize: "13px",
                    fontFamily: "Space Grotesk, sans-serif",
                    fontWeight: 600
                  }}
                >
                  Feedback recorded
                </p>
                <p
                  className="text-emerald-600"
                  style={{ fontSize: "11px", fontFamily: "Inter, sans-serif" }}
                >
                  {totalReviews} corrections stored · Will improve next similar plan
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* CONTENT */}
        <div className="px-6 py-6 space-y-5 max-w-4xl">
          {/* ── OVERVIEW ── */}
          <SectionCard
            id="overview"
            title="Overview"
            icon={Layers}
            reviewMode={reviewMode}
            sectionReview={reviews["overview"]}
            onReviewSave={handleReviewSave}
          >
            <div className="space-y-5">
              {/* Key metrics row */}
              <div className="grid grid-cols-4 gap-3">
                {[
                  {
                    label: "Total Budget",
                    value: `$${plan.budget.total.toLocaleString()}`,
                    sub: "Estimated",
                    color: "#00d4ff",
                    icon: DollarSign
                  },
                  {
                    label: "Timeline",
                    value: `${plan.totalWeeks} weeks`,
                    sub: "End-to-end",
                    color: "#7c3aed",
                    icon: CalendarDays
                  },
                  {
                    label: "Team Size",
                    value: `${plan.teamSize} FTEs`,
                    sub: "Required",
                    color: "#10b981",
                    icon: Users
                  },
                  {
                    label: "Complexity",
                    value: plan.complexity,
                    sub: "Assessment",
                    color: "#f43f5e",
                    icon: TrendingUp
                  }
                ].map(({ label, value, sub, color, icon: Icon }) => (
                  <div
                    key={label}
                    className="rounded-xl p-4"
                    style={{
                      background: `${color}08`,
                      border: `1px solid ${color}20`
                    }}
                  >
                    <Icon size={14} style={{ color, marginBottom: 8 }} />
                    <div
                      className="text-white"
                      style={{
                        fontFamily: "Space Grotesk, sans-serif",
                        fontSize: "18px",
                        fontWeight: 700
                      }}
                    >
                      {value}
                    </div>
                    <div className="text-slate-500" style={{ fontSize: "11px" }}>
                      {sub}
                    </div>
                    <div
                      className="text-slate-400 mt-0.5"
                      style={{ fontSize: "11px", fontFamily: "JetBrains Mono, monospace" }}
                    >
                      {label}
                    </div>
                  </div>
                ))}
              </div>

              {/* Hypothesis */}
              <div
                className="rounded-xl p-4"
                style={{
                  background: "rgba(0,212,255,0.04)",
                  border: "1px solid rgba(0,212,255,0.1)"
                }}
              >
                <div className="flex items-center gap-2 mb-2">
                  <BookOpen size={13} className="text-cyan-500" />
                  <span
                    className="text-cyan-500"
                    style={{
                      fontSize: "11px",
                      fontFamily: "JetBrains Mono, monospace",
                      letterSpacing: "0.08em"
                    }}
                  >
                    HYPOTHESIS
                  </span>
                </div>
                <p
                  className="text-slate-300"
                  style={{ fontSize: "14px", lineHeight: 1.7, fontFamily: "Inter, sans-serif" }}
                >
                  {plan.hypothesis}
                </p>
              </div>

              {/* Overview text */}
              <p
                className="text-slate-400"
                style={{ fontSize: "14px", lineHeight: 1.7, fontFamily: "Inter, sans-serif" }}
              >
                {plan.overview}
              </p>
            </div>
          </SectionCard>

          {/* ── PROTOCOL ── */}
          <SectionCard
            id="protocol"
            title="Protocol"
            icon={ListOrdered}
            reviewMode={reviewMode}
            sectionReview={reviews["protocol"]}
            onReviewSave={handleReviewSave}
          >
            <div className="space-y-6">
              {(plan.protocol ?? []).map((phase) => (
                <div key={phase.phase}>
                  <div className="flex items-center gap-3 mb-3">
                    <div className="h-px flex-1" style={{ background: "rgba(255,255,255,0.06)" }} />
                    <span
                      className="text-cyan-400 shrink-0"
                      style={{
                        fontSize: "12px",
                        fontFamily: "JetBrains Mono, monospace",
                        letterSpacing: "0.05em"
                      }}
                    >
                      {phase.phase}
                    </span>
                    <span
                      className="text-slate-600 shrink-0"
                      style={{ fontSize: "11px", fontFamily: "JetBrains Mono, monospace" }}
                    >
                      {phase.weekRange}
                    </span>
                    <div className="h-px flex-1" style={{ background: "rgba(255,255,255,0.06)" }} />
                  </div>

                  <div className="space-y-2">
                    {(phase.steps ?? []).map((step) => {
                      const isExpanded = expandedSteps.includes(step.id);
                      return (
                        <div
                          key={step.id}
                          className="rounded-xl overflow-hidden"
                          style={{
                            background: "rgba(255,255,255,0.02)",
                            border: "1px solid rgba(255,255,255,0.05)"
                          }}
                        >
                          <button
                            onClick={() => toggleStep(step.id)}
                            className="w-full flex items-start gap-3 p-4 text-left hover:bg-white/[0.02] transition-colors"
                          >
                            <div
                              className="w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-0.5"
                              style={{
                                background: "rgba(0,212,255,0.1)",
                                border: "1px solid rgba(0,212,255,0.2)",
                                fontSize: "10px",
                                color: "#00d4ff",
                                fontFamily: "JetBrains Mono, monospace"
                              }}
                            >
                              {step.id}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span
                                  className="text-slate-200"
                                  style={{ fontSize: "14px", fontFamily: "Inter, sans-serif" }}
                                >
                                  {step.title}
                                </span>
                                {step.critical && (
                                  <span
                                    className="flex items-center gap-1 px-1.5 py-0.5 rounded"
                                    style={{
                                      background: "rgba(244,63,94,0.1)",
                                      border: "1px solid rgba(244,63,94,0.2)",
                                      color: "#f43f5e",
                                      fontSize: "10px",
                                      fontFamily: "JetBrains Mono, monospace"
                                    }}
                                  >
                                    <AlertCircle size={9} /> CRITICAL
                                  </span>
                                )}
                                <span
                                  className="text-slate-600"
                                  style={{
                                    fontSize: "11px",
                                    fontFamily: "JetBrains Mono, monospace"
                                  }}
                                >
                                  ⏱ {step.duration}
                                </span>
                              </div>
                            </div>
                            {isExpanded ? (
                              <ChevronUp size={14} className="text-slate-500 shrink-0" />
                            ) : (
                              <ChevronDown size={14} className="text-slate-500 shrink-0" />
                            )}
                          </button>
                          <AnimatePresence>
                            {isExpanded && (
                              <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: "auto", opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                className="overflow-hidden"
                              >
                                <div
                                  className="px-4 pb-4 space-y-2"
                                  style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}
                                >
                                  <p
                                    className="text-slate-400 mt-3"
                                    style={{
                                      fontSize: "13px",
                                      lineHeight: 1.7,
                                      fontFamily: "Inter, sans-serif"
                                    }}
                                  >
                                    {step.detail}
                                  </p>
                                  {step.notes && (
                                    <div
                                      className="flex items-start gap-2 px-3 py-2 rounded-lg"
                                      style={{
                                        background: "rgba(245,158,11,0.06)",
                                        border: "1px solid rgba(245,158,11,0.15)"
                                      }}
                                    >
                                      <AlertCircle
                                        size={12}
                                        className="text-amber-500 mt-0.5 shrink-0"
                                      />
                                      <p
                                        className="text-amber-500/80"
                                        style={{
                                          fontSize: "12px",
                                          fontFamily: "Inter, sans-serif",
                                          lineHeight: 1.6
                                        }}
                                      >
                                        <strong>Note: </strong>
                                        {step.notes}
                                      </p>
                                    </div>
                                  )}
                                </div>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>

          {/* ── MATERIALS ── */}
          <SectionCard
            id="materials"
            title="Materials & Supply Chain"
            icon={Package}
            reviewMode={reviewMode}
            sectionReview={reviews["materials"]}
            onReviewSave={handleReviewSave}
          >
            <div className="space-y-4">
              {/* Sort controls */}
              <div className="flex items-center gap-2">
                <span
                  className="text-slate-600"
                  style={{ fontSize: "11px", fontFamily: "JetBrains Mono, monospace" }}
                >
                  SORT BY:
                </span>
                {(["category", "cost", "name"] as const).map((s) => (
                  <button
                    key={s}
                    onClick={() => setMaterialSort(s)}
                    className="px-2.5 py-1 rounded-md text-xs transition-all"
                    style={{
                      background:
                        materialSort === s ? "rgba(0,212,255,0.1)" : "rgba(255,255,255,0.03)",
                      border:
                        materialSort === s
                          ? "1px solid rgba(0,212,255,0.25)"
                          : "1px solid rgba(255,255,255,0.06)",
                      color: materialSort === s ? "#00d4ff" : "#64748b",
                      fontFamily: "JetBrains Mono, monospace"
                    }}
                  >
                    {s}
                  </button>
                ))}
                <div className="ml-auto">
                  <span
                    className="text-cyan-400"
                    style={{ fontSize: "12px", fontFamily: "JetBrains Mono, monospace" }}
                  >
                    Total: $
                    {(plan.materials ?? []).reduce((s, m) => s + m.total, 0).toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Table */}
              <div
                className="rounded-xl overflow-hidden"
                style={{ border: "1px solid rgba(255,255,255,0.06)" }}
              >
                <table className="w-full">
                  <thead>
                    <tr
                      style={{
                        background: "rgba(0,0,0,0.3)",
                        borderBottom: "1px solid rgba(255,255,255,0.05)"
                      }}
                    >
                      {[
                        "Item",
                        "Catalog #",
                        "Supplier",
                        "Qty",
                        "Unit Cost",
                        "Total",
                        "Lead Time"
                      ].map((h) => (
                        <th
                          key={h}
                          className="px-3 py-2 text-left text-slate-500"
                          style={{
                            fontSize: "10px",
                            fontFamily: "JetBrains Mono, monospace",
                            letterSpacing: "0.06em"
                          }}
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {sortedMaterials.map((mat, idx) => (
                      <tr
                        key={mat.id}
                        style={{
                          background: idx % 2 === 0 ? "transparent" : "rgba(255,255,255,0.01)",
                          borderBottom: "1px solid rgba(255,255,255,0.03)"
                        }}
                      >
                        <td className="px-3 py-2.5">
                          <div>
                            <p
                              className="text-slate-200"
                              style={{ fontSize: "12px", fontFamily: "Inter, sans-serif" }}
                            >
                              {mat.name}
                            </p>
                            <span
                              className="text-slate-600"
                              style={{ fontSize: "10px", fontFamily: "JetBrains Mono, monospace" }}
                            >
                              {mat.category}
                            </span>
                          </div>
                        </td>
                        <td
                          className="px-3 py-2.5 text-cyan-600"
                          style={{ fontSize: "11px", fontFamily: "JetBrains Mono, monospace" }}
                        >
                          {mat.catalog}
                        </td>
                        <td className="px-3 py-2.5 text-slate-400" style={{ fontSize: "12px" }}>
                          {mat.supplier}
                        </td>
                        <td
                          className="px-3 py-2.5 text-slate-300"
                          style={{ fontSize: "12px", fontFamily: "JetBrains Mono, monospace" }}
                        >
                          {mat.qty} {mat.unit}
                        </td>
                        <td
                          className="px-3 py-2.5 text-slate-300"
                          style={{ fontSize: "12px", fontFamily: "JetBrains Mono, monospace" }}
                        >
                          ${mat.unitCost}
                        </td>
                        <td
                          className="px-3 py-2.5 text-white"
                          style={{
                            fontSize: "12px",
                            fontFamily: "JetBrains Mono, monospace",
                            fontWeight: 600
                          }}
                        >
                          ${mat.total.toLocaleString()}
                        </td>
                        <td
                          className="px-3 py-2.5 text-slate-500"
                          style={{ fontSize: "11px", fontFamily: "JetBrains Mono, monospace" }}
                        >
                          {mat.leadTime}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </SectionCard>

          {/* ── BUDGET ── */}
          <SectionCard
            id="budget"
            title="Budget Breakdown"
            icon={DollarSign}
            reviewMode={reviewMode}
            sectionReview={reviews["budget"]}
            onReviewSave={handleReviewSave}
          >
            <div className="space-y-5">
              <div className="grid grid-cols-2 gap-5">
                {/* Bar chart */}
                <div>
                  <p
                    className="text-slate-500 mb-3"
                    style={{ fontSize: "11px", fontFamily: "JetBrains Mono, monospace" }}
                  >
                    BY CATEGORY ($)
                  </p>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart
                      data={plan.budget.categories}
                      layout="vertical"
                      margin={{ left: 0, right: 30, top: 0, bottom: 0 }}
                    >
                      <XAxis
                        type="number"
                        tick={{ fill: "#475569", fontSize: 10, fontFamily: "JetBrains Mono" }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <YAxis
                        type="category"
                        dataKey="name"
                        width={160}
                        tick={{ fill: "#64748b", fontSize: 10, fontFamily: "Inter" }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip
                        contentStyle={{
                          background: "rgba(10,18,32,0.95)",
                          border: "1px solid rgba(255,255,255,0.1)",
                          borderRadius: 8,
                          color: "#e2e8f0",
                          fontSize: 12
                        }}
                        formatter={(v: number) => [`$${v.toLocaleString()}`, ""]}
                      />
                      <Bar dataKey="amount" radius={[0, 4, 4, 0]}>
                        {(plan.budget.categories ?? []).map((cat) => (
                          <Cell key={cat.name} fill={cat.color} opacity={0.85} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Pie / donut */}
                <div>
                  <p
                    className="text-slate-500 mb-3"
                    style={{ fontSize: "11px", fontFamily: "JetBrains Mono, monospace" }}
                  >
                    DISTRIBUTION (%)
                  </p>
                  <div className="flex items-center gap-4">
                    <ResponsiveContainer width={130} height={130}>
                      <PieChart>
                        <Pie
                          data={plan.budget.categories}
                          dataKey="amount"
                          cx="50%"
                          cy="50%"
                          innerRadius={38}
                          outerRadius={60}
                          paddingAngle={2}
                          strokeWidth={0}
                        >
                          {(plan.budget.categories ?? []).map((cat) => (
                            <Cell key={cat.name} fill={cat.color} opacity={0.85} />
                          ))}
                        </Pie>
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="space-y-1.5">
                      {(plan.budget.categories ?? []).map((cat) => (
                        <div key={cat.name} className="flex items-center gap-2">
                          <div
                            className="w-2 h-2 rounded-full shrink-0"
                            style={{ background: cat.color }}
                          />
                          <span
                            className="text-slate-400"
                            style={{ fontSize: "11px", fontFamily: "Inter, sans-serif" }}
                          >
                            {cat.name}
                          </span>
                          <span
                            className="text-slate-500 ml-auto"
                            style={{ fontSize: "10px", fontFamily: "JetBrains Mono, monospace" }}
                          >
                            {cat.percentage}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Total */}
              <div
                className="flex items-center justify-between rounded-xl px-5 py-3"
                style={{
                  background: "rgba(0,212,255,0.06)",
                  border: "1px solid rgba(0,212,255,0.15)"
                }}
              >
                <span
                  className="text-slate-400"
                  style={{ fontSize: "14px", fontFamily: "Space Grotesk, sans-serif" }}
                >
                  Total Estimated Budget
                </span>
                <span
                  className="text-cyan-300"
                  style={{
                    fontSize: "24px",
                    fontFamily: "Space Grotesk, sans-serif",
                    fontWeight: 700
                  }}
                >
                  ${plan.budget.total.toLocaleString()}
                </span>
              </div>
            </div>
          </SectionCard>

          {/* ── TIMELINE ── */}
          <SectionCard
            id="timeline"
            title="Timeline & Phases"
            icon={CalendarDays}
            reviewMode={reviewMode}
            sectionReview={reviews["timeline"]}
            onReviewSave={handleReviewSave}
          >
            <div className="space-y-4">
              {/* Week labels */}
              <div className="relative">
                <div className="flex mb-1 pl-36">
                  {Array.from({ length: plan.totalWeeks + 1 }, (_, i) => (
                    <div
                      key={i}
                      className="flex-1 text-center text-slate-600"
                      style={{ fontSize: "10px", fontFamily: "JetBrains Mono, monospace" }}
                    >
                      {i > 0 && i % 2 === 0 ? `W${i}` : ""}
                    </div>
                  ))}
                </div>

                {/* Phase rows */}
                {(plan.timeline ?? []).map((phase) => (
                  <div key={phase.phase} className="flex items-center mb-2">
                    {/* Phase label */}
                    <div className="w-36 shrink-0 pr-3">
                      <p
                        className="text-slate-300 text-right"
                        style={{ fontSize: "12px", fontFamily: "Inter, sans-serif" }}
                      >
                        {phase.phase}
                      </p>
                    </div>

                    {/* Track */}
                    <div
                      className="relative flex-1 h-7"
                      style={{ background: "rgba(255,255,255,0.03)", borderRadius: 4 }}
                    >
                      <motion.div
                        initial={{ width: 0, opacity: 0 }}
                        whileInView={{
                          width: `${(phase.duration / plan.totalWeeks) * 100}%`,
                          opacity: 1
                        }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.7, delay: 0.1 }}
                        className="absolute top-0 h-full rounded"
                        style={{
                          left: `${(phase.start / plan.totalWeeks) * 100}%`,
                          background: `${phase.color}25`,
                          border: `1px solid ${phase.color}50`
                        }}
                      >
                        <div className="h-full rounded overflow-hidden">
                          <div
                            className="h-1 w-full"
                            style={{ background: phase.color, opacity: 0.8 }}
                          />
                        </div>
                        <div className="px-2 flex items-center h-full">
                          <span
                            style={{
                              fontSize: "10px",
                              fontFamily: "JetBrains Mono, monospace",
                              color: phase.color,
                              whiteSpace: "nowrap",
                              overflow: "hidden",
                              textOverflow: "ellipsis"
                            }}
                          >
                            {phase.duration}w
                          </span>
                        </div>
                      </motion.div>
                    </div>
                  </div>
                ))}

                {/* Grid lines */}
                <div className="absolute inset-0 pl-36 pointer-events-none flex">
                  {Array.from({ length: plan.totalWeeks }, (_, i) => (
                    <div
                      key={i}
                      className="flex-1"
                      style={{ borderRight: "1px solid rgba(255,255,255,0.03)" }}
                    />
                  ))}
                </div>
              </div>

              {/* Phase details */}
              <div className="grid grid-cols-2 gap-3 mt-2">
                {(plan.timeline ?? []).map((phase) => (
                  <div
                    key={phase.phase}
                    className="rounded-xl p-3"
                    style={{ background: `${phase.color}07`, border: `1px solid ${phase.color}20` }}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-2 h-2 rounded-full" style={{ background: phase.color }} />
                      <span
                        style={{
                          fontSize: "12px",
                          fontFamily: "Space Grotesk, sans-serif",
                          color: phase.color,
                          fontWeight: 600
                        }}
                      >
                        {phase.phase}
                      </span>
                      <span
                        className="text-slate-500 ml-auto"
                        style={{ fontSize: "10px", fontFamily: "JetBrains Mono, monospace" }}
                      >
                        Wk {phase.start + 1}–{phase.start + phase.duration}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {(phase.tasks ?? []).map((t) => (
                        <span
                          key={t}
                          className="text-slate-500 px-1.5 py-0.5 rounded"
                          style={{
                            fontSize: "10px",
                            fontFamily: "Inter, sans-serif",
                            background: "rgba(255,255,255,0.04)"
                          }}
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </SectionCard>

          {/* ── VALIDATION ── */}
          <SectionCard
            id="validation"
            title="Validation & Success Criteria"
            icon={CheckSquare}
            reviewMode={reviewMode}
            sectionReview={reviews["validation"]}
            onReviewSave={handleReviewSave}
          >
            <div className="space-y-3">
              {(plan.validation ?? []).map((metric, idx) => (
                <motion.div
                  key={metric.metric}
                  initial={{ opacity: 0, x: -10 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: idx * 0.05 }}
                  className="rounded-xl p-4 flex items-start gap-4"
                  style={{
                    background: metric.critical ? "rgba(244,63,94,0.04)" : "rgba(255,255,255,0.02)",
                    border: metric.critical
                      ? "1px solid rgba(244,63,94,0.15)"
                      : "1px solid rgba(255,255,255,0.05)"
                  }}
                >
                  <div
                    className="w-6 h-6 rounded-full flex items-center justify-center shrink-0"
                    style={{
                      background: metric.critical ? "rgba(244,63,94,0.1)" : "rgba(16,185,129,0.1)",
                      border: `1px solid ${metric.critical ? "rgba(244,63,94,0.25)" : "rgba(16,185,129,0.25)"}`
                    }}
                  >
                    {metric.critical ? (
                      <AlertCircle size={12} className="text-rose-400" />
                    ) : (
                      <Shield size={12} className="text-emerald-400" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <span
                        className="text-white"
                        style={{
                          fontSize: "13px",
                          fontFamily: "Space Grotesk, sans-serif",
                          fontWeight: 600
                        }}
                      >
                        {metric.metric}
                      </span>
                      {metric.critical && (
                        <span
                          className="px-1.5 py-0.5 rounded text-rose-400"
                          style={{
                            fontSize: "9px",
                            fontFamily: "JetBrains Mono, monospace",
                            background: "rgba(244,63,94,0.1)",
                            border: "1px solid rgba(244,63,94,0.2)"
                          }}
                        >
                          CRITICAL
                        </span>
                      )}
                    </div>
                    <p
                      className="text-cyan-400 mb-1"
                      style={{ fontSize: "13px", fontFamily: "JetBrains Mono, monospace" }}
                    >
                      Target: {metric.target}
                    </p>
                    <div className="flex items-center gap-3">
                      <p
                        className="text-slate-500"
                        style={{ fontSize: "11px", fontFamily: "Inter, sans-serif" }}
                      >
                        Method: {metric.method}
                      </p>
                      <span
                        className="text-slate-600"
                        style={{ fontSize: "10px", fontFamily: "JetBrains Mono, monospace" }}
                      >
                        @ {metric.timepoint}
                      </span>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </SectionCard>

          <div className="h-12" />
        </div>
      </div>

      {/* ── COACH MARK OVERLAY (first-time users) ── */}
      <AnimatePresence>
        {showCoachMark && (
          <motion.div
            key="coach-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
            className="absolute inset-0 pointer-events-none"
            style={{ zIndex: 38 }}
          >
            {/* Radial spotlight: transparent circle around FAB, dark everywhere else */}
            <div
              className="absolute inset-0"
              style={{
                background:
                  "radial-gradient(circle 72px at calc(100% - 60px) calc(100% - 60px), transparent 0%, transparent 52px, rgba(2,8,20,0.82) 76%)"
              }}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── COACH MARK TOOLTIP ── */}
      <AnimatePresence>
        {showCoachMark && (
          <motion.div
            key="coach-tooltip"
            initial={{ opacity: 0, y: 12, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.95 }}
            transition={{ duration: 0.35, delay: 0.15 }}
            className="absolute pointer-events-auto"
            style={{ bottom: 132, right: 20, zIndex: 50, width: 280 }}
          >
            <div
              className="rounded-2xl p-5"
              style={{
                background: "rgba(10,6,28,0.96)",
                border: "1px solid rgba(124,58,237,0.45)",
                boxShadow: "0 0 40px rgba(124,58,237,0.25), 0 20px 60px rgba(0,0,0,0.5)",
                backdropFilter: "blur(20px)"
              }}
            >
              {/* Header */}
              <div className="flex items-center gap-2 mb-3">
                <div
                  className="w-7 h-7 rounded-lg flex items-center justify-center"
                  style={{
                    background: "rgba(124,58,237,0.2)",
                    border: "1px solid rgba(124,58,237,0.4)"
                  }}
                >
                  <Pencil size={13} className="text-purple-400" />
                </div>
                <div>
                  <p
                    className="text-purple-300"
                    style={{
                      fontSize: "13px",
                      fontFamily: "Space Grotesk, sans-serif",
                      fontWeight: 700
                    }}
                  >
                    Scientist Review Mode
                  </p>
                  <p
                    className="text-purple-600"
                    style={{ fontSize: "10px", fontFamily: "JetBrains Mono, monospace" }}
                  >
                    KEY FEATURE
                  </p>
                </div>
              </div>

              <p
                className="text-slate-300 mb-4"
                style={{ fontSize: "12px", fontFamily: "Inter, sans-serif", lineHeight: 1.65 }}
              >
                Rate, annotate, and correct each section of the plan. Your feedback is stored and
                used to improve future plans for similar experiments.
              </p>

              {/* Feature bullets */}
              <div className="space-y-1.5 mb-4">
                {[
                  "⭐  Rate each section 1–5",
                  "✏️  Add inline corrections",
                  "🏷️  Tag issues by type",
                  "🔁  Feedback trains future plans"
                ].map((item) => (
                  <p
                    key={item}
                    className="text-slate-400"
                    style={{ fontSize: "11px", fontFamily: "Inter, sans-serif" }}
                  >
                    {item}
                  </p>
                ))}
              </div>

              <button
                onClick={dismissCoachMark}
                className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl transition-all"
                style={{
                  background:
                    "linear-gradient(135deg, rgba(124,58,237,0.3), rgba(124,58,237,0.15))",
                  border: "1px solid rgba(124,58,237,0.5)",
                  color: "#a78bfa",
                  fontSize: "13px",
                  fontFamily: "Space Grotesk, sans-serif",
                  fontWeight: 600
                }}
              >
                Got it — I&apos;ll explore it
              </button>
            </div>

            {/* Arrow pointing down-right to FAB */}
            <div
              className="absolute"
              style={{
                bottom: -10,
                right: 36,
                width: 0,
                height: 0,
                borderLeft: "10px solid transparent",
                borderRight: "10px solid transparent",
                borderTop: "10px solid rgba(124,58,237,0.45)"
              }}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── REVIEW MODE FAB ── */}
      <div className="absolute pointer-events-auto" style={{ bottom: 32, right: 32, zIndex: 50 }}>
        {/* Pulse rings when coach mark is active or review mode is off */}
        {!reviewMode && (
          <>
            <motion.div
              className="absolute inset-0 rounded-full"
              style={{ border: "2px solid rgba(124,58,237,0.4)" }}
              animate={{ scale: [1, 1.55, 1], opacity: [0.7, 0, 0.7] }}
              transition={{ duration: 2.2, repeat: Infinity, ease: "easeOut" }}
            />
            <motion.div
              className="absolute inset-0 rounded-full"
              style={{ border: "2px solid rgba(124,58,237,0.25)" }}
              animate={{ scale: [1, 1.9, 1], opacity: [0.5, 0, 0.5] }}
              transition={{ duration: 2.2, repeat: Infinity, ease: "easeOut", delay: 0.4 }}
            />
          </>
        )}

        <motion.button
          whileHover={{ scale: 1.06 }}
          whileTap={{ scale: 0.94 }}
          onHoverStart={() => setFabHovered(true)}
          onHoverEnd={() => setFabHovered(false)}
          onClick={toggleReviewMode}
          className="relative flex items-center gap-0 rounded-full overflow-hidden transition-all duration-300"
          style={{
            height: 52,
            minWidth: 52,
            paddingLeft: fabHovered || reviewMode ? 18 : 0,
            paddingRight: fabHovered || reviewMode ? 18 : 0,
            justifyContent: fabHovered || reviewMode ? "flex-start" : "center",
            background: reviewMode
              ? "linear-gradient(135deg, #a78bfa, #7c3aed)"
              : "linear-gradient(135deg, #7c3aed, #5b21b6)",
            boxShadow: reviewMode
              ? "0 0 24px rgba(167,139,250,0.5), 0 8px 32px rgba(0,0,0,0.4)"
              : showCoachMark
                ? "0 0 32px rgba(124,58,237,0.7), 0 8px 32px rgba(0,0,0,0.4)"
                : "0 0 20px rgba(124,58,237,0.4), 0 8px 24px rgba(0,0,0,0.3)"
          }}
        >
          <Pencil size={18} className="text-white shrink-0" style={{ marginLeft: 0 }} />
          <AnimatePresence>
            {(fabHovered || reviewMode) && (
              <motion.span
                initial={{ opacity: 0, width: 0, marginLeft: 0 }}
                animate={{ opacity: 1, width: "auto", marginLeft: 8 }}
                exit={{ opacity: 0, width: 0, marginLeft: 0 }}
                transition={{ duration: 0.2 }}
                className="text-white whitespace-nowrap overflow-hidden"
                style={{
                  fontSize: "13px",
                  fontFamily: "Space Grotesk, sans-serif",
                  fontWeight: 600
                }}
              >
                {reviewMode ? "Exit Review" : "Review Mode"}
              </motion.span>
            )}
          </AnimatePresence>
        </motion.button>
      </div>
    </div>
  );
}
