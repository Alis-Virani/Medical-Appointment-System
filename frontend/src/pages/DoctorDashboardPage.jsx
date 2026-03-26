import { useState, useEffect } from 'react';
import client from '../api/client';
import { useAuth } from '../context/AuthContext';
import './DashboardPages.css';

export default function DoctorDashboardPage() {
  const { user } = useAuth();
  const [todayAppts, setTodayAppts] = useState([]);
  const [allAppts, setAllAppts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      client.get('/schedule/today'),
      client.get('/schedule/'),
    ]).then(([t, a]) => {
      setTodayAppts(t.data);
      setAllAppts(a.data);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="page-loading"><span className="spinner" /></div>;

  const upcoming = allAppts.filter(a => new Date(a.appointment_date) >= new Date()).slice(0, 5);

  return (
    <div className="dash-page">
      <div className="dash-header">
        <h1 className="dash-title">Doctor Dashboard</h1>
        <p className="dash-sub">Welcome back, Dr. {user?.full_name}</p>
      </div>

      {/* Stats row */}
      <div className="stats-row">
        {[
          { label: "Today's Patients", value: todayAppts.length, icon: '👥' },
          { label: 'Upcoming', value: upcoming.length, icon: '📅' },
          { label: 'Total Appointments', value: allAppts.length, icon: '📊' },
        ].map(s => (
          <div key={s.label} className="stat-card card">
            <span className="stat-icon">{s.icon}</span>
            <span className="stat-value">{s.value}</span>
            <span className="stat-label">{s.label}</span>
          </div>
        ))}
      </div>

      <div className="dash-grid-2">
        {/* Today */}
        <div>
          <h2 className="section-heading">📅 Today's Schedule</h2>
          {todayAppts.length === 0 ? (
            <div className="card empty-card"><p>No appointments today</p></div>
          ) : todayAppts.map(a => (
            <div key={a.id} className="card appt-card fade-up">
              <div className="appt-header">
                <span className="appt-name">{a.patient_name || 'Patient'}</span>
                <span className="appt-time">{a.time}</span>
              </div>
              <span className={`badge ${a.status === 'confirmed' ? 'badge-doctor' : 'badge-patient'}`}>{a.status}</span>
            </div>
          ))}
        </div>

        {/* Upcoming */}
        <div>
          <h2 className="section-heading">🔜 Upcoming Appointments</h2>
          {upcoming.length === 0 ? (
            <div className="card empty-card"><p>No upcoming appointments</p></div>
          ) : upcoming.map(a => (
            <div key={a.id} className="card appt-card fade-up">
              <div className="appt-header">
                <span className="appt-name">{a.patient_name || 'Patient'}</span>
                <span className={`badge ${a.status === 'confirmed' ? 'badge-doctor' : 'badge-patient'}`}>{a.status}</span>
              </div>
              <div className="appt-meta">
                <span>📅 {a.appointment_date} at {a.appointment_time}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
