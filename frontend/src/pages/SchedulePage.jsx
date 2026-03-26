import { useState, useEffect } from 'react';
import client from '../api/client';
import './DashboardPages.css';

export default function SchedulePage() {
  const [schedule, setSchedule] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    client.get('/schedule/').then(r => setSchedule(r.data)).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page-loading"><span className="spinner" /></div>;

  const upcoming = schedule.filter(a => new Date(a.appointment_date) >= new Date());
  const past = schedule.filter(a => new Date(a.appointment_date) < new Date());

  const clearPast = async () => {
    if (!past.length) return;
    const ok = window.confirm('Remove all past appointments from schedule history?');
    if (!ok) return;
    await client.delete('/schedule/past');
    setSchedule(prev => prev.filter(a => new Date(a.appointment_date) >= new Date()));
  };

  return (
    <div className="dash-page">
      <div className="dash-header">
        <h1 className="dash-title">My Schedule</h1>
        <p className="dash-sub">All appointments assigned to you</p>
      </div>

      <div className="dash-grid-2">
        <div>
          <h2 className="section-heading">📅 Upcoming ({upcoming.length})</h2>
          {upcoming.length === 0 ? (
            <div className="card empty-card"><p>No upcoming appointments</p></div>
          ) : upcoming.map(a => (
            <div key={a.id} className="card appt-card fade-up">
              <div className="appt-header">
                <span className="appt-name">{a.patient_name || 'Patient'}</span>
                <span className={`badge ${a.status === 'confirmed' ? 'badge-doctor' : 'badge-patient'}`}>{a.status}</span>
              </div>
              <div className="appt-meta">
                <span>📅 {a.appointment_date}</span>
                <span>🕒 {a.appointment_time}</span>
              </div>
              {a.notes && <div className="note-field">Notes: {a.notes}</div>}
            </div>
          ))}
        </div>

        <div>
          <div className="section-heading-row">
            <h2 className="section-heading">🕐 Past ({past.length})</h2>
            <button
              type="button"
              className="section-clear-btn"
              onClick={clearPast}
              disabled={past.length === 0}
            >
              Remove All
            </button>
          </div>
          {past.length === 0 ? (
            <div className="card empty-card"><p>No past appointments</p></div>
          ) : past.slice(0, 10).map(a => (
            <div key={a.id} className="card appt-card fade-up" style={{opacity:0.6}}>
              <div className="appt-header">
                <span className="appt-name">{a.patient_name || 'Patient'}</span>
                <span className="history-date">{a.appointment_date}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
