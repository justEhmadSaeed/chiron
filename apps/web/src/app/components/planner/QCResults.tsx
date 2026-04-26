import {
  AlertTriangle,
  ArrowRight,
  BookMarked,
  BookOpen,
  Calendar,
  CheckCircle,
  Columns2,
  ExternalLink,
  FileText,
  RefreshCw,
  ShieldCheck,
  TrendingUp,
  XCircle
} from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import type { ElementType } from "react";
import { useState } from "react";
import { MolecularCanvas } from "./MolecularCanvas";
import type { NoveltySignal, QCResult, Reference } from "./types";

interface QCResultsProps {
  question: string;
  result: QCResult;
  onGenerate: () => void;
  onRedo: () => void;
}

const SIGNAL_CONFIG: Record<
  NoveltySignal,
  {
    label: string;
    sublabel: string;
    color: string;
    bg: string;
    border: string;
    icon: ElementType;
    badgeBg: string;
  }
> = {
  not_found: {
    label: "NOT FOUND",
    sublabel: "No matching experiments detected. High novelty confirmed.",
    color: "#10b981",
    bg: "rgba(16,185,129,0.06)",
    border: "rgba(16,185,129,0.3)",
    icon: CheckCircle,
    badgeBg: "rgba(16,185,129,0.12)"
  },
  similar_work: {
    label: "SIMILAR WORK EXISTS",
    sublabel: "Related experiments found. Your specific approach appears novel.",
    color: "#f59e0b",
    bg: "rgba(245,158,11,0.06)",
    border: "rgba(245,158,11,0.3)",
    icon: AlertTriangle,
    badgeBg: "rgba(245,158,11,0.12)"
  },
  exact_match: {
    label: "EXACT MATCH FOUND",
    sublabel: "This protocol has been published. Consider modifying your approach.",
    color: "#f43f5e",
    bg: "rgba(244,63,94,0.06)",
    border: "rgba(244,63,94,0.3)",
    icon: XCircle,
    badgeBg: "rgba(244,63,94,0.12)"
  }
};

const TYPE_CONFIG = {
  journal: { label: "Journal", color: "#00d4ff", bg: "rgba(0,212,255,0.08)" },
  preprint: { label: "Preprint", color: "#f59e0b", bg: "rgba(245,158,11,0.08)" },
  review: { label: "Review", color: "#7c3aed", bg: "rgba(124,58,237,0.08)" }
};

function NoveltyGauge({ score, color }: { score: number; color: string }) {
  const angle = (score / 100) * 180 - 90;
  const radians = (angle * Math.PI) / 180;
  const cx = 80,
    cy = 80;
  const needleX = cx + 42 * Math.cos(radians);
  const needleY = cy + 42 * Math.sin(radians);

  return (
    <svg width="160" height="105" viewBox="0 0 160 105">
      <path
        d="M 20 80 A 60 60 0 0 1 140 80"
        fill="none"
        stroke="rgba(255,255,255,0.06)"
        strokeWidth="8"
        strokeLinecap="round"
      />
      <defs>
        <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#10b981" />
          <stop offset="50%" stopColor="#f59e0b" />
          <stop offset="100%" stopColor="#f43f5e" />
        </linearGradient>
      </defs>
      <path
        d="M 20 80 A 60 60 0 0 1 140 80"
        fill="none"
        stroke="url(#gaugeGrad)"
        strokeWidth="8"
        strokeLinecap="round"
        strokeDasharray="190"
        strokeDashoffset={190 - (score / 100) * 190}
      />
      <motion.line
        x1={cx}
        y1={cy}
        x2={needleX}
        y2={needleY}
        stroke={color}
        strokeWidth="2.5"
        strokeLinecap="round"
        initial={{ x2: cx, y2: cy }}
        animate={{ x2: needleX, y2: needleY }}
        transition={{ duration: 1.2, delay: 0.3, ease: "easeOut" }}
        style={{ filter: `drop-shadow(0 0 4px ${color})` }}
      />
      <circle
        cx={cx}
        cy={cy}
        r="4"
        fill={color}
        style={{ filter: `drop-shadow(0 0 4px ${color})` }}
      />
      <text
        x={cx}
        y={cy + 22}
        textAnchor="middle"
        fill={color}
        style={{ fontSize: "22px", fontFamily: "Space Grotesk, sans-serif", fontWeight: 700 }}
      >
        {score}
      </text>
      <text
        x={cx}
        y={cy + 35}
        textAnchor="middle"
        fill="rgba(148,163,184,0.5)"
        style={{ fontSize: "9px", fontFamily: "JetBrains Mono, monospace" }}
      >
        NOVELTY / 100
      </text>
    </svg>
  );
}

type ViewMode = "split" | "summary" | "references";

function InlineCitation({
  num,
  hovered,
  onEnter,
  onLeave
}: {
  num: number;
  refId: string;
  hovered: boolean;
  onEnter: () => void;
  onLeave: () => void;
}) {
  return (
    <span
      onMouseEnter={onEnter}
      onMouseLeave={onLeave}
      className="inline-flex items-center justify-center cursor-pointer select-none transition-all duration-200"
      style={{
        width: 20,
        height: 20,
        borderRadius: 5,
        background: hovered ? "rgba(0,212,255,0.22)" : "rgba(0,212,255,0.1)",
        border: `1px solid ${hovered ? "rgba(0,212,255,0.7)" : "rgba(0,212,255,0.3)"}`,
        color: "#00d4ff",
        fontSize: 10,
        fontFamily: "JetBrains Mono, monospace",
        fontWeight: 700,
        margin: "0 3px",
        verticalAlign: "middle",
        boxShadow: hovered ? "0 0 10px rgba(0,212,255,0.45)" : "none"
      }}
    >
      {num}
    </span>
  );
}

function ReferenceCard({
  reference,
  idx,
  highlighted
}: {
  reference: Reference;
  idx: number;
  highlighted: boolean;
}) {
  const typeConf = TYPE_CONFIG[reference.type];
  return (
    <motion.div
      animate={{
        boxShadow: highlighted
          ? "0 0 0 1.5px rgba(0,212,255,0.6), 0 0 20px rgba(0,212,255,0.15)"
          : "0 0 0 1px rgba(255,255,255,0.06)",
        background: highlighted ? "rgba(0,212,255,0.07)" : "rgba(13,24,41,0.7)"
      }}
      transition={{ duration: 0.2 }}
      className="rounded-xl p-3"
      style={{ backdropFilter: "blur(12px)" }}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          {/* Top meta row */}
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <span
              className="flex items-center justify-center w-5 h-5 rounded shrink-0"
              style={{
                background: "rgba(0,212,255,0.1)",
                border: "1px solid rgba(0,212,255,0.25)",
                color: "#00d4ff",
                fontSize: 10,
                fontFamily: "JetBrains Mono, monospace",
                fontWeight: 700
              }}
            >
              {idx + 1}
            </span>
            <span
              className="px-1.5 py-0.5 rounded"
              style={{
                background: typeConf.bg,
                color: typeConf.color,
                fontFamily: "JetBrains Mono, monospace",
                fontSize: "10px"
              }}
            >
              {typeConf.label}
            </span>
            <span
              className="text-slate-500"
              style={{ fontSize: "10px", fontFamily: "JetBrains Mono, monospace" }}
            >
              {reference.year}
            </span>
            <div className="flex items-center gap-1.5 ml-auto">
              <div
                className="w-14 h-1 rounded-full overflow-hidden"
                style={{ background: "rgba(255,255,255,0.08)" }}
              >
                <motion.div
                  className="h-full rounded-full"
                  style={{
                    background:
                      reference.similarity > 60
                        ? "#f43f5e"
                        : reference.similarity > 40
                          ? "#f59e0b"
                          : "#10b981"
                  }}
                  initial={{ width: 0 }}
                  animate={{ width: `${reference.similarity}%` }}
                  transition={{ delay: 0.3 + idx * 0.1, duration: 0.6 }}
                />
              </div>
              <span
                className="text-slate-600"
                style={{ fontSize: "10px", fontFamily: "JetBrains Mono, monospace" }}
              >
                {reference.similarity}%
              </span>
            </div>
          </div>
          <p
            className="text-slate-200 mb-1 leading-snug"
            style={{ fontSize: "12px", fontFamily: "Inter, sans-serif" }}
          >
            {reference.title}
          </p>
          <p
            className="text-slate-500"
            style={{ fontSize: "11px", fontFamily: "Inter, sans-serif" }}
          >
            {reference.authors.split(",").slice(0, 2).join(",")}{" "}
            {reference.authors.split(",").length > 2 ? "et al." : ""} ·{" "}
            <span className="italic">{reference.journal}</span>
          </p>
        </div>
        <a
          href={`https://doi.org/${reference.doi}`}
          target="_blank"
          rel="noopener noreferrer"
          className="shrink-0 text-slate-600 hover:text-cyan-400 transition-colors mt-1"
        >
          <ExternalLink size={12} />
        </a>
      </div>
    </motion.div>
  );
}

export function QCResults({ result, onGenerate, onRedo }: QCResultsProps) {
  const config = SIGNAL_CONFIG[result.signal];
  const Icon = config.icon;
  const [hoveredRef, setHoveredRef] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("split");

  const getRefId = (num: number) => result.references[num - 1]?.id ?? null;

  const VIEW_MODES: { id: ViewMode; label: string; icon: ElementType }[] = [
    { id: "split", label: "Split", icon: Columns2 },
    { id: "summary", label: "Summary", icon: FileText },
    { id: "references", label: "References", icon: BookOpen }
  ];

  return (
    <div
      className="relative w-full h-full flex items-center justify-center overflow-auto py-8"
      style={{ background: "linear-gradient(135deg, #020c1b 0%, #050d1e 50%, #0a0618 100%)" }}
    >
      <MolecularCanvas density={28} accentColor="245, 158, 11" secondaryColor="0, 212, 255" />
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(rgba(0,212,255,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(0,212,255,0.02) 1px, transparent 1px)",
          backgroundSize: "60px 60px"
        }}
      />

      <div className="relative z-10 w-full max-w-4xl px-6 space-y-4">
        {/* Stage badge */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <div
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full"
            style={{ background: "rgba(0,212,255,0.07)", border: "1px solid rgba(0,212,255,0.15)" }}
          >
            <ShieldCheck size={12} className="text-cyan-400" />
            <span
              className="text-cyan-400"
              style={{
                fontSize: "11px",
                letterSpacing: "0.12em",
                fontFamily: "JetBrains Mono, monospace"
              }}
            >
              LITERATURE QC COMPLETE
            </span>
          </div>
        </motion.div>

        {/* Novelty card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="rounded-2xl p-5"
          style={{
            background: config.bg,
            border: `1px solid ${config.border}`,
            backdropFilter: "blur(20px)"
          }}
        >
          <div className="flex items-start gap-5">
            <div className="shrink-0">
              <NoveltyGauge score={result.noveltyScore} color={config.color} />
            </div>
            <div className="flex-1 pt-2">
              <div className="flex items-center gap-2.5 mb-1.5">
                <Icon size={17} style={{ color: config.color }} />
                <span
                  style={{
                    fontFamily: "JetBrains Mono, monospace",
                    fontSize: "14px",
                    fontWeight: 600,
                    color: config.color,
                    letterSpacing: "0.05em"
                  }}
                >
                  {config.label}
                </span>
              </div>
              <p
                className="text-slate-300 mb-3"
                style={{ fontSize: "13px", lineHeight: 1.6, fontFamily: "Inter, sans-serif" }}
              >
                {config.sublabel}
              </p>
              <div className="flex gap-4 flex-wrap">
                {[
                  { icon: BookMarked, text: `${result.references.length} references found` },
                  { icon: TrendingUp, text: `${result.databases.length} databases scanned` },
                  { icon: Calendar, text: `${result.scanDuration}s elapsed` }
                ].map(({ icon: Ic, text }) => (
                  <div key={text} className="flex items-center gap-1.5">
                    <Ic size={11} className="text-slate-600" />
                    <span
                      className="text-slate-400"
                      style={{ fontSize: "11px", fontFamily: "JetBrains Mono, monospace" }}
                    >
                      {text}
                    </span>
                  </div>
                ))}
              </div>
              {/* Database chips */}
              <div className="flex gap-1.5 flex-wrap mt-3">
                {result.databases.map((db) => (
                  <span
                    key={db}
                    className="px-2 py-0.5 rounded text-slate-500"
                    style={{
                      fontSize: "10px",
                      fontFamily: "JetBrains Mono, monospace",
                      background: "rgba(255,255,255,0.04)",
                      border: "1px solid rgba(255,255,255,0.06)"
                    }}
                  >
                    ✓ {db}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </motion.div>

        {/* ── QC INTELLIGENCE BRIEF ── */}
        {result.references.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
            className="rounded-2xl overflow-hidden"
            style={{
              background: "rgba(8,15,30,0.85)",
              border: "1px solid rgba(255,255,255,0.07)",
              backdropFilter: "blur(20px)"
            }}
          >
            {/* Brief header with view toggle */}
            <div
              className="flex items-center justify-between px-5 py-3"
              style={{
                borderBottom: "1px solid rgba(255,255,255,0.05)",
                background: "rgba(0,0,0,0.25)"
              }}
            >
              <div className="flex items-center gap-2">
                <div
                  className="w-1.5 h-1.5 rounded-full bg-amber-400"
                  style={{ boxShadow: "0 0 6px #f59e0b" }}
                />
                <span
                  className="text-slate-300"
                  style={{
                    fontSize: "12px",
                    fontFamily: "Space Grotesk, sans-serif",
                    fontWeight: 600,
                    letterSpacing: "0.04em"
                  }}
                >
                  QC Intelligence Brief
                </span>
                <span
                  className="text-slate-600"
                  style={{ fontSize: "10px", fontFamily: "JetBrains Mono, monospace" }}
                >
                  · AI-generated · {result.references.length} citations
                </span>
              </div>

              {/* View mode toggle */}
              <div
                className="flex items-center gap-0.5 rounded-lg p-0.5"
                style={{
                  background: "rgba(0,0,0,0.3)",
                  border: "1px solid rgba(255,255,255,0.06)"
                }}
              >
                {VIEW_MODES.map(({ id, label, icon: ModeIcon }) => (
                  <button
                    key={id}
                    onClick={() => setViewMode(id)}
                    className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md transition-all"
                    style={{
                      background: viewMode === id ? "rgba(0,212,255,0.1)" : "transparent",
                      border:
                        viewMode === id ? "1px solid rgba(0,212,255,0.2)" : "1px solid transparent",
                      color: viewMode === id ? "#00d4ff" : "#475569",
                      fontSize: "11px",
                      fontFamily: "JetBrains Mono, monospace"
                    }}
                  >
                    <ModeIcon size={11} />
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Brief content */}
            <AnimatePresence mode="wait">
              {viewMode === "split" && (
                <motion.div
                  key="split"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="grid grid-cols-[1fr_0.8fr]"
                  style={{ minHeight: 280 }}
                >
                  {/* Left: Summary */}
                  <div
                    className="p-5 overflow-y-auto"
                    style={{ borderRight: "1px solid rgba(255,255,255,0.05)", maxHeight: 340 }}
                  >
                    <p
                      className="text-slate-600 mb-3"
                      style={{
                        fontSize: "10px",
                        letterSpacing: "0.1em",
                        fontFamily: "JetBrains Mono, monospace"
                      }}
                    >
                      AI SUMMARY — hover citations to highlight references
                    </p>
                    <div className="space-y-3">
                      {(result.summary || []).map((para, pIdx) => (
                        <p
                          key={pIdx}
                          className="text-slate-400 leading-relaxed"
                          style={{ fontSize: "13px", fontFamily: "Inter, sans-serif" }}
                        >
                          {para.text}
                          {para.citations.map((num) => {
                            const refId = getRefId(num);
                            return refId ? (
                              <InlineCitation
                                key={num}
                                num={num}
                                refId={refId}
                                hovered={hoveredRef === refId}
                                onEnter={() => setHoveredRef(refId)}
                                onLeave={() => setHoveredRef(null)}
                              />
                            ) : null;
                          })}
                          {"continuation" in para && <span>{para.continuation as string}</span>}
                        </p>
                      ))}
                    </div>
                  </div>

                  {/* Right: References */}
                  <div className="p-4 overflow-y-auto space-y-2.5" style={{ maxHeight: 340 }}>
                    <p
                      className="text-slate-600 mb-3"
                      style={{
                        fontSize: "10px",
                        letterSpacing: "0.1em",
                        fontFamily: "JetBrains Mono, monospace"
                      }}
                    >
                      CLOSEST REFERENCES
                    </p>
                    {result.references.map((ref, idx) => (
                      <ReferenceCard
                        key={ref.id}
                        reference={ref}
                        idx={idx}
                        highlighted={hoveredRef === ref.id}
                      />
                    ))}
                  </div>
                </motion.div>
              )}

              {viewMode === "summary" && (
                <motion.div
                  key="summary"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="p-6"
                >
                  <p
                    className="text-slate-600 mb-4"
                    style={{
                      fontSize: "10px",
                      letterSpacing: "0.1em",
                      fontFamily: "JetBrains Mono, monospace"
                    }}
                  >
                    AI SUMMARY — click citations to view reference details
                  </p>
                  <div className="space-y-4 max-w-2xl">
                    {(result.summary || []).map((para, pIdx) => (
                      <p
                        key={pIdx}
                        className="text-slate-300 leading-relaxed"
                        style={{ fontSize: "14px", fontFamily: "Inter, sans-serif" }}
                      >
                        {para.text}
                        {para.citations.map((num) => {
                          const refId = getRefId(num);
                          return refId ? (
                            <InlineCitation
                              key={num}
                              num={num}
                              refId={refId}
                              hovered={hoveredRef === refId}
                              onEnter={() => setHoveredRef(refId)}
                              onLeave={() => setHoveredRef(null)}
                            />
                          ) : null;
                        })}
                        {"continuation" in para && <span>{para.continuation as string}</span>}
                      </p>
                    ))}
                  </div>

                  {/* Floating reference tooltip when citation hovered */}
                  <AnimatePresence>
                    {hoveredRef && (
                      <motion.div
                        initial={{ opacity: 0, y: 8, scale: 0.97 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 8, scale: 0.97 }}
                        transition={{ duration: 0.15 }}
                        className="mt-4 rounded-xl p-4"
                        style={{
                          background: "rgba(0,212,255,0.06)",
                          border: "1px solid rgba(0,212,255,0.3)",
                          maxWidth: 520
                        }}
                      >
                        {(() => {
                          const ref = result.references.find((r) => r.id === hoveredRef);
                          if (!ref) return null;
                          const typeConf = TYPE_CONFIG[ref.type];
                          return (
                            <div className="flex items-start gap-3">
                              <div
                                className="flex items-center justify-center w-6 h-6 rounded shrink-0"
                                style={{
                                  background: "rgba(0,212,255,0.1)",
                                  border: "1px solid rgba(0,212,255,0.3)",
                                  color: "#00d4ff",
                                  fontSize: 11,
                                  fontFamily: "JetBrains Mono, monospace",
                                  fontWeight: 700
                                }}
                              >
                                {result.references.indexOf(ref) + 1}
                              </div>
                              <div>
                                <p
                                  className="text-slate-200 mb-1"
                                  style={{
                                    fontSize: "13px",
                                    fontFamily: "Inter, sans-serif",
                                    lineHeight: 1.5
                                  }}
                                >
                                  {ref.title}
                                </p>
                                <p className="text-slate-500" style={{ fontSize: "11px" }}>
                                  {ref.authors} · <em>{ref.journal}</em> · {ref.year}
                                </p>
                                <div className="flex items-center gap-2 mt-1.5">
                                  <span
                                    className="px-1.5 py-0.5 rounded"
                                    style={{
                                      background: typeConf.bg,
                                      color: typeConf.color,
                                      fontSize: 10,
                                      fontFamily: "JetBrains Mono, monospace"
                                    }}
                                  >
                                    {typeConf.label}
                                  </span>
                                  <span
                                    className="text-slate-600"
                                    style={{
                                      fontSize: 10,
                                      fontFamily: "JetBrains Mono, monospace"
                                    }}
                                  >
                                    {ref.similarity}% similarity
                                  </span>
                                </div>
                              </div>
                            </div>
                          );
                        })()}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              )}

              {viewMode === "references" && (
                <motion.div
                  key="references"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="p-5 space-y-3"
                >
                  <p
                    className="text-slate-600"
                    style={{
                      fontSize: "10px",
                      letterSpacing: "0.1em",
                      fontFamily: "JetBrains Mono, monospace"
                    }}
                  >
                    CLOSEST REFERENCES — {result.references.length} found
                  </p>
                  {result.references.map((ref, idx) => (
                    <ReferenceCard key={ref.id} reference={ref} idx={idx} highlighted={false} />
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}

        {/* CTAs */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.45 }}
          className="flex gap-3"
        >
          <button
            onClick={onRedo}
            className="flex items-center gap-2 px-4 py-3 rounded-xl transition-all"
            style={{
              background: "rgba(255,255,255,0.03)",
              border: "1px solid rgba(255,255,255,0.08)",
              color: "#94a3b8",
              fontFamily: "Space Grotesk, sans-serif",
              fontSize: "14px"
            }}
          >
            <RefreshCw size={14} /> Revise Question
          </button>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onGenerate}
            className="flex-1 flex items-center justify-center gap-2.5 px-6 py-3 rounded-xl"
            style={{
              background: "linear-gradient(135deg, #00d4ff 0%, #0ea5e9 50%, #7c3aed 100%)",
              boxShadow: "0 0 30px rgba(0,212,255,0.22)",
              color: "#fff",
              fontFamily: "Space Grotesk, sans-serif",
              fontWeight: 600,
              fontSize: "15px"
            }}
          >
            Generate Full Experiment Plan
            <ArrowRight size={16} />
          </motion.button>
        </motion.div>
      </div>
    </div>
  );
}
