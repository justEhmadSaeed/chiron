import { CalendarDays, CheckSquare, DollarSign, Layers, ListOrdered, Package } from "lucide-react";

export const PLANNER_NAV_SECTIONS = [
  { id: "overview", label: "Overview", icon: Layers },
  { id: "protocol", label: "Protocol", icon: ListOrdered },
  { id: "materials", label: "Materials", icon: Package },
  { id: "budget", label: "Budget", icon: DollarSign },
  { id: "timeline", label: "Timeline", icon: CalendarDays },
  { id: "validation", label: "Validation", icon: CheckSquare }
];

export const REVIEW_TAGS = [
  "Correct",
  "Needs Clarification",
  "Outdated Protocol",
  "Wrong Reagent",
  "Timeline Off",
  "Budget Inaccurate",
  "Missing Step",
  "Excellent"
];
