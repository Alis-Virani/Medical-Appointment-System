import { useState, useEffect } from 'react';
import client from '../api/client';
import './DashboardPages.css';

export default function HealthHistoryPage() {
  const [history, setHistory] = useState([]);
  const [upcoming, setUpcoming] = useState([]);
  const [loading, setLoading] = useState(true);

  const clearHistory = async () => {
    if (!history.length) return;
    const ok = window.confirm('Remove all symptom history? This action cannot be undone.');
    if (!ok) return;
    await client.delete('/health/history');
    setHistory([]);
  };

  useEffect(() => {
    Promise.all([
      client.get('/health/history'),
      client.get('/appointments/upcoming'),
    ]).then(([h, u]) => {
      setHistory(h.data);
      setUpcoming(u.data);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page-loading"><span className="spinner" /></div>;

  return (
    <div className="dash-page">
      <div className="dash-header">
        <h1 className="dash-title">Health History</h1>
        <p className="dash-sub">Your recorded symptoms, conditions, and upcoming appointments</p>
      </div>

      <div className="dash-grid-2">
        {/* Upcoming appointments */}
        <div>
          <h2 className="section-heading">📅 Upcoming Appointments</h2>
          {upcoming.length === 0 ? (
            <div className="card empty-card">
              <p>No upcoming appointments</p>
              <small>Use the AI Chat to book one</small>
            </div>
          ) : upcoming.map(a => (
            <div key={a.id} className="card appt-card fade-up">
              <div className="appt-header">
                <span className="appt-name">{a.doctor_name}</span>
                <span className={`badge ${a.status === 'confirmed' ? 'badge-doctor' : 'badge-patient'}`}>{a.status}</span>
              </div>
              <div className="appt-meta">
                <span>🏥 {a.specialty}</span>
                <span>📍 {a.city}</span>
                <span>📅 {a.appointment_date} {a.appointment_time}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Symptom history */}
        <div>
          <div className="section-heading-row">
            <h2 className="section-heading">🩺 Symptom History</h2>
            <button
              type="button"
              className="section-clear-btn"
              onClick={clearHistory}
              disabled={history.length === 0}
            >
              Remove All
            </button>
          </div>
          {history.length === 0 ? (
            <div className="card empty-card">
              <p>No health records yet</p>
              <small>Chat with the AI to start building your health profile</small>
            </div>
          ) : (
            <div className="history-list">
              {history.map((h, i) => (
                <div key={i} className="card history-card fade-up" style={{animationDelay:`${i*0.04}s`}}>
                  <div className="history-symptom">{h.symptom}</div>
                  {h.condition && <div className="history-condition">Condition: {h.condition}</div>}
                  {h.specialist && <div className="history-specialist">Specialist: {h.specialist}</div>}
                  <div className="history-date">{new Date(h.recorded_at).toLocaleDateString()}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
