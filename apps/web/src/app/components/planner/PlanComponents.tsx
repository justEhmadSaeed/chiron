import type { ReactNode, ElementType } from 'react';
import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Pencil, Star, Send, ThumbsUp } from 'lucide-react';
import type { SectionReview } from './types';
import { REVIEW_TAGS } from './constants';

// ──────────────────────────────────────────
// NoveltyBadge
// ──────────────────────────────────────────
export function NoveltyBadge({ signal }: { signal: string }) {
  const cfg =
    ({
      similar_work: {
        label: 'SIMILAR WORK',
        color: '#f59e0b',
        bg: 'rgba(245,158,11,0.1)',
        border: 'rgba(245,158,11,0.25)',
      },
      not_found: {
        label: 'NOVEL',
        color: '#10b981',
        bg: 'rgba(16,185,129,0.1)',
        border: 'rgba(16,185,129,0.25)',
      },
      exact_match: {
        label: 'PRIOR ART',
        color: '#f43f5e',
        bg: 'rgba(244,63,94,0.1)',
        border: 'rgba(244,63,94,0.25)',
      },
    } as Record<string, { label: string; color: string; bg: string; border: string }>)[signal] ?? {
      label: 'UNKNOWN',
      color: '#94a3b8',
      bg: 'rgba(148,163,184,0.1)',
      border: 'rgba(148,163,184,0.25)',
    };

  return (
    <span
      className="px-2 py-0.5 rounded-md"
      style={{
        background: cfg.bg,
        border: `1px solid ${cfg.border}`,
        color: cfg.color,
        fontSize: '10px',
        fontFamily: 'JetBrains Mono, monospace',
        letterSpacing: '0.05em',
      }}
    >
      {cfg.label}
    </span>
  );
}

// ──────────────────────────────────────────
// ComplexityBadge
// ──────────────────────────────────────────
export function ComplexityBadge({ level }: { level: string }) {
  const colors: Record<string, string> = {
    Low: '#10b981',
    Medium: '#f59e0b',
    High: '#f97316',
    'Very High': '#f43f5e',
  };
  const color = colors[level] ?? '#94a3b8';
  return (
    <span
      className="px-2 py-0.5 rounded-md"
      style={{
        background: `${color}15`,
        border: `1px solid ${color}30`,
        color,
        fontSize: '10px',
        fontFamily: 'JetBrains Mono, monospace',
      }}
    >
      {level.toUpperCase()} COMPLEXITY
    </span>
  );
}

// ──────────────────────────────────────────
// SectionCard
// ──────────────────────────────────────────
interface SectionCardProps {
  id: string;
  title: string;
  icon: ElementType;
  reviewMode: boolean;
  sectionReview?: SectionReview;
  onReviewSave: (r: SectionReview) => void;
  children: ReactNode;
}

export function SectionCard({
  id,
  title,
  icon: Icon,
  reviewMode,
  sectionReview,
  onReviewSave,
  children,
}: SectionCardProps) {
  const [showReview, setShowReview] = useState(false);
  const [rating, setRating] = useState(sectionReview?.rating ?? 0);
  const [hoverRating, setHoverRating] = useState(0);
  const [comment, setComment] = useState(sectionReview?.comment ?? '');
  const [corrections, setCorrections] = useState(sectionReview?.corrections ?? '');
  const [selectedTags, setSelectedTags] = useState<string[]>(sectionReview?.tags ?? []);
  const [submitted, setSubmitted] = useState(!!sectionReview);

  const toggleTag = (tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag],
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
      timestamp: new Date().toISOString(),
    });
    setSubmitted(true);
    setShowReview(false);
  };

  return (
    <section id={id} className="scroll-mt-24">
      <div
        className="rounded-2xl overflow-hidden"
        style={{
          background: 'rgba(10,18,32,0.85)',
          border: '1px solid rgba(255,255,255,0.07)',
          backdropFilter: 'blur(12px)',
        }}
      >
        {/* Section header */}
        <div
          className="px-6 py-4 flex items-center justify-between"
          style={{
            borderBottom: '1px solid rgba(255,255,255,0.05)',
            background: 'rgba(0,0,0,0.2)',
          }}
        >
          <div className="flex items-center gap-3">
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center"
              style={{
                background: 'rgba(0,212,255,0.08)',
                border: '1px solid rgba(0,212,255,0.15)',
              }}
            >
              <Icon size={15} className="text-cyan-400" />
            </div>
            <h2
              className="text-white"
              style={{
                fontFamily: 'Space Grotesk, sans-serif',
                fontSize: '15px',
                fontWeight: 600,
              }}
            >
              {title}
            </h2>
          </div>
          {reviewMode && (
            <div className="flex items-center gap-2">
              {submitted && (
                <span
                  className="flex items-center gap-1 text-emerald-400"
                  style={{ fontSize: '11px', fontFamily: 'JetBrains Mono, monospace' }}
                >
                  <ThumbsUp size={11} /> Reviewed
                </span>
              )}
              <button
                onClick={() => setShowReview(!showReview)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-all cursor-pointer"
                style={{
                  background: showReview ? 'rgba(124,58,237,0.15)' : 'rgba(255,255,255,0.04)',
                  border: showReview
                    ? '1px solid rgba(124,58,237,0.4)'
                    : '1px solid rgba(255,255,255,0.08)',
                  color: showReview ? '#a78bfa' : '#64748b',
                  fontSize: '12px',
                  fontFamily: 'Space Grotesk, sans-serif',
                }}
              >
                <Pencil size={12} />
                {showReview ? 'Hide' : 'Review'}
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
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div
                className="px-6 pb-6 pt-0"
                style={{
                  borderTop: '1px solid rgba(124,58,237,0.2)',
                  background: 'rgba(124,58,237,0.04)',
                }}
              >
                <div className="pt-5 space-y-4">
                  <p
                    className="text-purple-400"
                    style={{
                      fontSize: '12px',
                      fontFamily: 'JetBrains Mono, monospace',
                      letterSpacing: '0.08em',
                    }}
                  >
                    ✦ SCIENTIST REVIEW — {title.toUpperCase()}
                  </p>

                  {/* Star rating */}
                  <div>
                    <p className="text-slate-400 mb-2" style={{ fontSize: '12px' }}>
                      Quality Rating
                    </p>
                    <div className="flex gap-1">
                      {[1, 2, 3, 4, 5].map((s) => (
                        <button
                          key={s}
                          onMouseEnter={() => setHoverRating(s)}
                          onMouseLeave={() => setHoverRating(0)}
                          onClick={() => setRating(s)}
                          className="transition-all cursor-pointer"
                        >
                          <Star
                            size={22}
                            className={
                              s <= (hoverRating || rating)
                                ? 'text-amber-400 fill-amber-400'
                                : 'text-slate-700'
                            }
                          />
                        </button>
                      ))}
                      {rating > 0 && (
                        <span
                          className="ml-2 text-slate-400 self-center"
                          style={{ fontSize: '12px' }}
                        >
                          {['', 'Poor', 'Fair', 'Good', 'Very Good', 'Excellent'][rating]}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Tags */}
                  <div>
                    <p className="text-slate-400 mb-2" style={{ fontSize: '12px' }}>
                      Issue Tags
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {REVIEW_TAGS.map((tag) => (
                        <button
                          key={tag}
                          onClick={() => toggleTag(tag)}
                          className="px-2.5 py-1 rounded-md text-xs transition-all cursor-pointer"
                          style={{
                            background: selectedTags.includes(tag)
                              ? 'rgba(124,58,237,0.2)'
                              : 'rgba(255,255,255,0.04)',
                            border: selectedTags.includes(tag)
                              ? '1px solid rgba(124,58,237,0.5)'
                              : '1px solid rgba(255,255,255,0.08)',
                            color: selectedTags.includes(tag) ? '#a78bfa' : '#64748b',
                            fontFamily: 'JetBrains Mono, monospace',
                          }}
                        >
                          {tag}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Comment */}
                  <div>
                    <p className="text-slate-400 mb-2" style={{ fontSize: '12px' }}>
                      Annotation
                    </p>
                    <textarea
                      value={comment}
                      onChange={(e) => setComment(e.target.value)}
                      placeholder="Add contextual notes, observations, or domain expertise..."
                      rows={2}
                      className="w-full rounded-xl px-4 py-3 resize-none outline-none text-slate-300 placeholder-slate-600"
                      style={{
                        background: 'rgba(0,0,0,0.3)',
                        border: '1px solid rgba(255,255,255,0.08)',
                        fontSize: '13px',
                        fontFamily: 'Inter, sans-serif',
                        lineHeight: 1.6,
                      }}
                    />
                  </div>

                  {/* Corrections */}
                  <div>
                    <p className="text-slate-400 mb-2" style={{ fontSize: '12px' }}>
                      Corrections / Suggested Changes
                    </p>
                    <textarea
                      value={corrections}
                      onChange={(e) => setCorrections(e.target.value)}
                      placeholder="e.g. 'Use Synthego sgRNA at 50 nM, not 100 nM. Protocol ref: PMID 34567890'"
                      rows={2}
                      className="w-full rounded-xl px-4 py-3 resize-none outline-none placeholder-slate-600"
                      style={{
                        background: 'rgba(0,0,0,0.3)',
                        border: '1px solid rgba(255,255,255,0.08)',
                        fontSize: '13px',
                        fontFamily: 'JetBrains Mono, monospace',
                        lineHeight: 1.6,
                        color: '#93c5fd',
                      }}
                    />
                  </div>

                  <button
                    onClick={handleSubmit}
                    disabled={rating === 0}
                    className="flex items-center gap-2 px-4 py-2.5 rounded-xl transition-all disabled:opacity-40 cursor-pointer"
                    style={{
                      background: 'rgba(124,58,237,0.2)',
                      border: '1px solid rgba(124,58,237,0.4)',
                      color: '#a78bfa',
                      fontSize: '13px',
                      fontFamily: 'Space Grotesk, sans-serif',
                      fontWeight: 600,
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
