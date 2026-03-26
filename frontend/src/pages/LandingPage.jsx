import { useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import './LandingPage.css';

// Animated dot-grid particle canvas — mirrors the CompanionAI aesthetic
function ParticleCanvas() {
  const canvasRef = useRef();

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    let animId;
    let w, h, cols, rows, dots;
    let mouse = { x: -9999, y: -9999 };

    const DOT_SPACING = 28;
    const DOT_RADIUS  = 1.6;
    const MAX_DIST    = 160;   // mouse-repel radius
    const BASE_ALPHA  = 0.18;
    const COLOR       = '180,159,249'; // purple

    const buildGrid = () => {
      w = canvas.width  = window.innerWidth;
      h = canvas.height = window.innerHeight;
      cols = Math.ceil(w / DOT_SPACING) + 2;
      rows = Math.ceil(h / DOT_SPACING) + 2;
      dots = [];
      for (let c = 0; c < cols; c++) {
        for (let r = 0; r < rows; r++) {
          dots.push({
            ox: c * DOT_SPACING,
            oy: r * DOT_SPACING,
            x:  c * DOT_SPACING,
            y:  r * DOT_SPACING,
            alpha: BASE_ALPHA + Math.random() * 0.08,
            phase: Math.random() * Math.PI * 2,
            speed: 0.003 + Math.random() * 0.003,
          });
        }
      }
    };

    const onResize = () => { buildGrid(); };
    const onMouse  = (e) => { mouse.x = e.clientX; mouse.y = e.clientY; };
    const onLeave  = ()  => { mouse.x = -9999; mouse.y = -9999; };

    window.addEventListener('resize', onResize);
    window.addEventListener('mousemove', onMouse);
    window.addEventListener('mouseleave', onLeave);
    buildGrid();

    let t = 0;
    const draw = () => {
      ctx.clearRect(0, 0, w, h);
      t++;

      for (const d of dots) {
        d.phase += d.speed;
        const pulse = Math.sin(d.phase) * 0.07;

        // Mouse repel
        const dx = d.ox - mouse.x;
        const dy = d.oy - mouse.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        let alpha = d.alpha + pulse;
        let rx = 0, ry = 0;

        if (dist < MAX_DIST) {
          const force = (1 - dist / MAX_DIST) * 18;
          rx = (dx / dist) * force;
          ry = (dy / dist) * force;
          alpha = Math.min(0.65, alpha + (1 - dist / MAX_DIST) * 0.5);
        }
        d.x += (d.ox + rx - d.x) * 0.08;
        d.y += (d.oy + ry - d.y) * 0.08;

        ctx.beginPath();
        ctx.arc(d.x, d.y, DOT_RADIUS, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${COLOR},${Math.max(0, Math.min(1, alpha))})`;
        ctx.fill();
      }
      animId = requestAnimationFrame(draw);
    };
    draw();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', onResize);
      window.removeEventListener('mousemove', onMouse);
      window.removeEventListener('mouseleave', onLeave);
    };
  }, []);

  return <canvas ref={canvasRef} className="landing-canvas" />;
}

export default function LandingPage() {
  return (
    <div className="landing">
      <ParticleCanvas />

      {/* Header */}
      <header className="landing-header">
        <Link to="/auth" className="btn-outline landing-signin-btn">Sign In</Link>
      </header>

      {/* Vertical label */}
      <div className="landing-vert">// Medical Intelligence Terminal //</div>

      {/* Hero */}
      <main className="landing-hero">
        <div className="landing-project-name">MediCare AI</div>

        <p className="landing-tagline">WHERE MEDICINE MEETS INTELLIGENCE</p>

        <h1 className="landing-h1">
          The Intelligent<br />
          <span className="landing-h1-accent">Medical Assistant</span>
        </h1>

        <p className="landing-desc">
          LangGraph AI · Emergency Detection · Multilingual · 15+ Specialties
        </p>

        <div className="landing-cta">
          <Link to="/auth?mode=register" className="cta-primary">ENTER THE EXPERIENCE</Link>
          <Link to="/auth?mode=login" className="cta-ghost">SIGN IN</Link>
        </div>

        {/* Stats row */}
        <div className="landing-stats">
          {[
            { v: 'LangGraph',  l: 'AI Engine' },
            { v: '15+',        l: 'Specialties' },
            { v: '7+',         l: 'Cities' },
            { v: 'Active',     l: 'Safety Layer' },
          ].map(s => (
            <div key={s.l} className="landing-stat">
              <span className="landing-stat-v">{s.v}</span>
              <span className="landing-stat-l">{s.l}</span>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
