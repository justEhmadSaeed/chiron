import type { ExperimentPlanData } from "../types";

export const generateMarkdownFromPlan = (data: ExperimentPlanData | null | undefined): string => {
  if (!data) return "No data provided.";

  // 1. Header & Overview
  let md = `# ${data.title || "Experiment Plan"}\n\n`;

  md += `**Complexity:** ${data.complexity} | **Team Size:** ${data.teamSize} FTEs | **Duration:** ${data.totalWeeks} Weeks\n\n`;

  if (data.hypothesis) md += `### Hypothesis\n${data.hypothesis}\n\n`;
  if (data.overview) md += `### Overview\n${data.overview}\n\n`;

  // 2. Budget Table
  const categories = data.budget?.categories ?? [];
  if (categories.length > 0) {
    md += `## Budget Breakdown\n\n`;
    md += `| Category | Amount | % of Budget |\n`;
    md += `| :--- | :--- | :--- |\n`;
    categories.forEach((item) => {
      md += `| ${item.name} | $${item.amount.toLocaleString()} | ${item.percentage}% |\n`;
    });
    md += `| **Total** | **$${(data.budget?.total ?? 0).toLocaleString()}** | **100%** |\n\n`;
  }

  // 3. Materials Table
  const materials = data.materials ?? [];
  if (materials.length > 0) {
    md += `## Required Materials\n\n`;
    md += `| Name | Supplier | Catalog | Qty | Total Cost |\n`;
    md += `| :--- | :--- | :--- | :--- | :--- |\n`;
    materials.forEach((m) => {
      // Strip pipe characters to prevent markdown table breaks
      const safeName = m.name.replace(/\|/g, "-");
      const safeSupplier = m.supplier.replace(/\|/g, "-");
      const safeCatalog = m.catalog.replace(/\|/g, "-");
      md += `| ${safeName} | ${safeSupplier} | ${safeCatalog} | ${m.qty} ${m.unit} | $${m.total.toLocaleString()} |\n`;
    });
    md += `\n`;
  }

  // 4. Validation Criteria Table
  const validation = data.validation ?? [];
  if (validation.length > 0) {
    md += `## Validation Metrics\n\n`;
    md += `| Metric | Target | Method | Timepoint | Critical |\n`;
    md += `| :--- | :--- | :--- | :--- | :--- |\n`;
    validation.forEach((v) => {
      md += `| ${v.metric} | ${v.target} | ${v.method} | ${v.timepoint} | ${v.critical ? "Yes" : "No"} |\n`;
    });
    md += `\n`;
  }

  // 5. Protocol Steps (Nested Lists)
  const protocol = data.protocol ?? [];
  if (protocol.length > 0) {
    md += `## Protocol\n\n`;
    protocol.forEach((phase) => {
      md += `### ${phase.phase} (${phase.weekRange})\n`;
      const steps = phase.steps ?? [];
      if (steps.length > 0) {
        steps.forEach((step) => {
          md += `* **[${step.duration}] ${step.title}:** ${step.detail}\n`;
          if (step.notes) md += `  * *Note: ${step.notes}*\n`;
        });
      }
      md += `\n`;
    });
  }

  return md;
};

/**
 * Triggers a browser download of a Markdown file from a string.
 */
export const downloadMarkdownFile = (
  content: string,
  filename: string = "experiment-plan.md"
): void => {
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};
