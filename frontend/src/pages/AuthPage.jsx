import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../api/client';
import './AuthPage.css';

export default function AuthPage() {
  const [mode, setMode] = useState(() => {
    const p = new URLSearchParams(window.location.search);
    return p.get('mode') === 'register' ? 'register' : 'login';
  });
  const [form, setForm] = useState({ username:'', password:'', full_name:'', email:'', phone:'', role:'patient' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // ── Forgot password modal ────────────────────────────────────────────────────
  const [fpOpen,    setFpOpen]    = useState(false);
  const [fpStep,    setFpStep]    = useState(1);      // 1=email, 2=code+newpw
  const [fpEmail,   setFpEmail]   = useState('');
  const [fpOtp,     setFpOtp]     = useState('');
  const [fpDevOtp,  setFpDevOtp]  = useState('');    // shown when email not configured
  const [fpNewPw,   setFpNewPw]   = useState('');
  const [fpMsg,     setFpMsg]     = useState('');
  const [fpErr,     setFpErr]     = useState('');
  const [fpLoading, setFpLoading] = useState(false);
  const [fpDone,    setFpDone]    = useState(false);

  const { login, register } = useAuth();
  const navigate = useNavigate();

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  const handleLogin = async (e) => {
    e.preventDefault(); setError(''); setLoading(true);
    try { await login(form.username, form.password); navigate('/app/chat'); }
    catch { setError('Invalid username or password.'); }
    finally { setLoading(false); }
  };

  const handleRegister = async (e) => {
    e.preventDefault(); setError(''); setLoading(true);
    try { await register(form); setMode('login'); alert('Account created! Please sign in.'); }
    catch (err) { setError(err.response?.data?.detail || 'Registration failed.'); }
    finally { setLoading(false); }
  };

  const handleSendOtp = async (e) => {
    e.preventDefault(); setFpErr(''); setFpLoading(true);
    try {
      const res = await api.post('/auth/forgot-password', { email: fpEmail });
      setFpMsg(res.data.message);
      if (res.data.dev_otp) setFpDevOtp(res.data.dev_otp);
      setFpStep(2);
    } catch (err) {
      setFpErr(err.response?.data?.detail || 'Something went wrong.');
    } finally { setFpLoading(false); }
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault(); setFpErr(''); setFpLoading(true);
    try {
      await api.post('/auth/verify-otp', { email: fpEmail, otp: fpOtp, new_password: fpNewPw });
      setFpDone(true);
    } catch (err) {
      setFpErr(err.response?.data?.detail || 'Invalid or expired code.');
    } finally { setFpLoading(false); }
  };

  const resetFpModal = () => {
    setFpOpen(false); setFpStep(1); setFpEmail(''); setFpOtp('');
    setFpNewPw(''); setFpMsg(''); setFpErr(''); setFpDevOtp(''); setFpDone(false);
  };

  const quotes = [
    { q: 'This AI caught a pattern in my symptoms my GP missed.' },
    { q: 'Managing my schedule and patient notes in one place has been a game-changer.' },
    { q: 'The multilingual support means my parents can use it in Gujarati.' },
  ];
  const quote = quotes[Math.floor(Date.now() / 10000) % quotes.length];

  return (
    <div className="auth-wrap">
      {/* ── Forgot password modal ── */}
      {fpOpen && (
        <div className="fp-overlay" onClick={resetFpModal}>
          <div className="fp-modal" onClick={e => e.stopPropagation()}>
            <button className="fp-close" onClick={resetFpModal}>✕</button>

            {fpDone ? (
              <div className="fp-done">
                <span className="fp-done-icon">✅</span>
                <h3>Password updated!</h3>
                <p>You can now sign in with your new password.</p>
                <button className="auth-submit-btn" style={{marginTop:'20px'}} onClick={resetFpModal}>
                  Back to Sign In
                </button>
              </div>
            ) : fpStep === 1 ? (
              <>
                <h3 className="fp-title">Reset Password</h3>
                <p className="fp-sub">Enter the email you registered with. We'll send a 6-digit code.</p>
                {fpErr && <div className="alert-error auth-error">{fpErr}</div>}
                <form onSubmit={handleSendOtp}>
                  <div className="af">
                    <label className="input-label">[ Registered Email ]</label>
                    <input className="input-field" type="email" placeholder="jane@email.com"
                      value={fpEmail} onChange={e => setFpEmail(e.target.value)} required />
                  </div>
                  <button type="submit" className="auth-submit-btn" disabled={fpLoading}>
                    {fpLoading ? <span className="spinner" /> : 'SEND RESET CODE'}
                  </button>
                </form>
              </>
            ) : (
              <>
                <h3 className="fp-title">Enter Reset Code</h3>
                <p className="fp-sub">{fpMsg}</p>
                {fpDevOtp && (
                  <div className="fp-dev-otp">
                    🛠 Dev mode — your code: <strong>{fpDevOtp}</strong>
                  </div>
                )}
                {fpErr && <div className="alert-error auth-error">{fpErr}</div>}
                <form onSubmit={handleVerifyOtp}>
                  <div className="af">
                    <label className="input-label">[ 6-Digit Code ]</label>
                    <input className="input-field" placeholder="000000" maxLength={6}
                      value={fpOtp} onChange={e => setFpOtp(e.target.value)} required />
                  </div>
                  <div className="af">
                    <label className="input-label">[ New Password ]</label>
                    <input className="input-field" type="password" placeholder="••••••••"
                      value={fpNewPw} onChange={e => setFpNewPw(e.target.value)} required minLength={6} />
                  </div>
                  <button type="submit" className="auth-submit-btn" disabled={fpLoading}>
                    {fpLoading ? <span className="spinner" /> : 'RESET PASSWORD'}
                  </button>
                </form>
              </>
            )}
          </div>
        </div>
      )}

      {/* ── Left panel: form ── */}
      <div className="auth-panel auth-form-panel">
        <Link to="/" className="auth-back">← Back</Link>

        <div className="auth-brand-row">
          <span className="auth-brand-dot">🩺</span>
        </div>
        <h2 className="auth-brand-hero">MediCare AI</h2>

        <div className="auth-form-box fade-up">
          <h1 className="auth-heading">
            {mode === 'login' ? 'Sign in' : 'Create account'}
          </h1>
          <p className="auth-sub">
            {mode === 'login' ? "Don't have an account? " : 'Already have one? '}
            <button className="auth-toggle-link"
              onClick={() => { setMode(m => m === 'login' ? 'register' : 'login'); setError(''); }}>
              {mode === 'login' ? 'Sign up' : 'Sign in'}
            </button>
          </p>

          {error && <div className="alert-error auth-error">{error}</div>}

          <form onSubmit={mode === 'login' ? handleLogin : handleRegister} className="auth-form">
            {mode === 'register' && (
              <div className="af">
                <label className="input-label">[ Full Name ]</label>
                <input className="input-field" placeholder="Jane Doe" value={form.full_name} onChange={set('full_name')} required />
              </div>
            )}
            <div className="af">
              <label className="input-label">[ Username ]</label>
              <input className="input-field" placeholder="your_username" value={form.username} onChange={set('username')} required />
            </div>
            <div className="af">
              <label className="input-label">[ Password ]</label>
              <input className="input-field" type="password" placeholder="••••••••" value={form.password} onChange={set('password')} required />
              {mode === 'login' && (
                <button type="button" className="auth-forgot-link" onClick={() => setFpOpen(true)}>
                  Forgot password?
                </button>
              )}
            </div>
            {mode === 'register' && <>
              <div className="af">
                <label className="input-label">[ Email ]</label>
                <input className="input-field" type="email" placeholder="jane@email.com" value={form.email} onChange={set('email')} />
              </div>
              <div className="af">
                <label className="input-label">[ Phone ]</label>
                <input className="input-field" placeholder="+91XXXXXXXXXX" value={form.phone} onChange={set('phone')} />
              </div>
              <div className="af">
                <label className="input-label">[ I am a ]</label>
                <select className="input-field" value={form.role} onChange={set('role')}>
                  <option value="patient">Patient</option>
                  <option value="doctor">Doctor</option>
                </select>
              </div>
            </>}
            <button type="submit" className="auth-submit-btn" disabled={loading}>
              {loading
                ? <span className="spinner" />
                : mode === 'login' ? 'ENTER THE EXPERIENCE' : 'CREATE ACCOUNT'
              }
            </button>
          </form>
        </div>

        <p className="auth-secure">🔒 Secured with PBKDF2-SHA256 encryption</p>
      </div>

      {/* ── Right panel: cinematic quote ── */}
      <div className="auth-panel auth-quote-panel">
        <div className="auth-dots" />
        <div className="auth-glow" />
        <div className="auth-quote-box fade-up">
          <span className="auth-qt">"</span>
          <blockquote className="auth-quote-text">{quote.q}</blockquote>
          {quote.by && <cite className="auth-quote-by">{quote.by}</cite>}
        </div>
        <div className="auth-pills">
          {['LangGraph AI', 'Emergency Detection', 'Multilingual', 'Secure Auth'].map(p => (
            <span key={p} className="auth-pill">{p}</span>
          ))}
        </div>
      </div>
    </div>
  );
}
