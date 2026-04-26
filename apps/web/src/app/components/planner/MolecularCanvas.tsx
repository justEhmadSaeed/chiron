import { useEffect, useRef } from 'react';

const ELEMENT_LABELS = ['H', 'C', 'N', 'O', 'P', 'S', 'Fe', 'Mg', 'Ca', 'K', 'Na', 'Cl', 'Zn', 'ATP', 'DNA', 'mRNA', 'GTP'];

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  label: string;
  opacity: number;
  pulseOffset: number;
  isLarge: boolean;
}

interface MolecularCanvasProps {
  density?: number;
  accentColor?: string;
  secondaryColor?: string;
}

export function MolecularCanvas({
  density = 55,
  accentColor = '0, 212, 255',
  secondaryColor = '124, 58, 237',
}: MolecularCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resize = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    };
    resize();

    const getW = () => canvas.offsetWidth;
    const getH = () => canvas.offsetHeight;

    const particles: Particle[] = Array.from({ length: density }, (_, i) => {
      const isLarge = i < density * 0.2;
      return {
        x: Math.random() * getW(),
        y: Math.random() * getH(),
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        radius: isLarge ? Math.random() * 4 + 3 : Math.random() * 2 + 1,
        label: isLarge ? ELEMENT_LABELS[Math.floor(Math.random() * ELEMENT_LABELS.length)] : '',
        opacity: Math.random() * 0.5 + 0.15,
        pulseOffset: Math.random() * Math.PI * 2,
        isLarge,
      };
    });

    let animId: number;
    let frame = 0;

    const draw = () => {
      frame++;
      const W = getW();
      const H = getH();
      ctx.clearRect(0, 0, W, H);

      // Draw connections
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const maxDist = 130;

          if (dist < maxDist) {
            const alpha = (1 - dist / maxDist) * 0.25;
            const useSecondary = (i + j) % 5 === 0;
            const color = useSecondary ? secondaryColor : accentColor;
            ctx.beginPath();
            ctx.strokeStyle = `rgba(${color}, ${alpha})`;
            ctx.lineWidth = 0.6;
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.stroke();
          }
        }
      }

      // Draw particles
      particles.forEach((p) => {
        const pulse = Math.sin(frame * 0.03 + p.pulseOffset) * 0.3 + 0.7;
        const useSecondary = p.isLarge && ELEMENT_LABELS.indexOf(p.label) % 3 === 0;
        const color = useSecondary ? secondaryColor : accentColor;

        // Outer glow
        const glow = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.radius * 6);
        glow.addColorStop(0, `rgba(${color}, ${p.opacity * pulse * 0.4})`);
        glow.addColorStop(1, `rgba(${color}, 0)`);
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius * 6, 0, Math.PI * 2);
        ctx.fillStyle = glow;
        ctx.fill();

        // Core dot
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius * pulse, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${color}, ${p.opacity * pulse})`;
        ctx.fill();

        // Label
        if (p.label) {
          ctx.fillStyle = `rgba(148, 163, 184, ${p.opacity * 0.7 * pulse})`;
          ctx.font = `${p.radius < 4 ? 9 : 10}px "JetBrains Mono", monospace`;
          ctx.textAlign = 'center';
          ctx.fillText(p.label, p.x, p.y - p.radius - 5);
        }

        // Update
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < -20) p.x = W + 20;
        if (p.x > W + 20) p.x = -20;
        if (p.y < -20) p.y = H + 20;
        if (p.y > H + 20) p.y = -20;
      });

      animId = requestAnimationFrame(draw);
    };

    draw();
    window.addEventListener('resize', resize);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', resize);
    };
  }, [density, accentColor, secondaryColor]);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full pointer-events-none"
      style={{ opacity: 0.45 }}
    />
  );
}