import type { PropsWithChildren } from "react";

export function Panel({ children, title }: PropsWithChildren<{ title: string }>) {
  return (
    <section
      style={{
        border: "1px solid rgba(255,255,255,0.08)",
        borderRadius: 24,
        background: "rgba(255,255,255,0.04)",
        padding: 24,
        backdropFilter: "blur(16px)"
      }}
    >
      <h2 style={{ marginTop: 0 }}>{title}</h2>
      {children}
    </section>
  );
}
