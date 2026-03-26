import { useState, useEffect } from 'react';
import client from '../api/client';
import './DashboardPages.css';

const EMPTY_FORM = { name:'', specialty:'', city:'', years_experience:0, contact:'', fees:500, availability:'Mon-Sat 9am-6pm', qualifications:'' };

export default function AdminPage() {
  const [doctors, setDoctors] = useState([]);
  const [stats, setStats] = useState({});
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [adding, setAdding] = useState(false);
  const [tab, setTab] = useState('doctors');
  const [msg, setMsg] = useState('');

  useEffect(() => { load(); }, []);

  const load = async () => {
    const [d, s, u] = await Promise.all([
      client.get('/admin/doctors'),
      client.get('/admin/stats'),
      client.get('/admin/users'),
    ]);
    setDoctors(d.data); setStats(s.data); setUsers(u.data);
  };

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  const addDoctor = async (e) => {
    e.preventDefault(); setAdding(true); setMsg('');
    try {
      await client.post('/admin/doctors', { ...form, years_experience: Number(form.years_experience), fees: Number(form.fees) });
      setMsg('Doctor added!'); setForm(EMPTY_FORM); load();
    } catch { setMsg('Failed to add doctor.'); }
    finally { setAdding(false); }
  };

  const removeDoctor = async (id) => {
    if (!confirm('Remove this doctor?')) return;
    await client.delete(`/admin/doctors/${id}`); load();
  };

  return (
    <div className="dash-page">
      <div className="dash-header">
        <h1 className="dash-title">Admin Panel</h1>
        <p className="dash-sub">Doctor and user management</p>
      </div>

      {/* Stats */}
      <div className="stats-row">
        {[
          { label: 'Patients', value: stats.total_patients ?? '-', icon: '🧑‍🤝‍🧑' },
          { label: 'Doctors', value: stats.total_doctors ?? '-', icon: '👨‍⚕️' },
          { label: 'Bookings', value: stats.total_bookings ?? '-', icon: '📅' },
          { label: 'Confirmed', value: stats.confirmed_bookings ?? '-', icon: '✅' },
        ].map(s => (
          <div key={s.label} className="stat-card card">
            <span className="stat-icon">{s.icon}</span>
            <span className="stat-value">{s.value}</span>
            <span className="stat-label">{s.label}</span>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="admin-tabs">
        {['doctors','add','users'].map(t => (
          <button key={t} className={`admin-tab ${tab===t?'active':''}`} onClick={() => setTab(t)}>
            {t === 'doctors' ? '👨‍⚕️ Doctor List' : t === 'add' ? '➕ Add Doctor' : '👥 Users'}
          </button>
        ))}
      </div>

      {tab === 'doctors' && (
        <div className="admin-table-wrap card">
          <table className="admin-table">
            <thead><tr><th>Name</th><th>Specialty</th><th>City</th><th>Rating</th><th>Fees</th><th></th></tr></thead>
            <tbody>
              {doctors.map(d => (
                <tr key={d.id}>
                  <td>{d.name}</td><td>{d.specialty}</td><td>{d.city}</td>
                  <td>⭐ {d.rating}</td><td>₹{d.fees}</td>
                  <td><button className="btn-ghost" style={{color:'var(--error)'}} onClick={() => removeDoctor(d.id)}>Remove</button></td>
                </tr>
              ))}
              {doctors.length === 0 && <tr><td colSpan="6" style={{textAlign:'center',color:'var(--text-muted)'}}>No doctors found</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'add' && (
        <div className="card" style={{maxWidth:600}}>
          {msg && <div className={msg.includes('added') ? 'alert-success' : 'alert-error'} style={{marginBottom:'16px'}}>{msg}</div>}
          <form onSubmit={addDoctor} className="notes-form">
            {[['name','Name'],['specialty','Specialty'],['city','City'],['contact','Contact'],['qualifications','Qualifications'],['availability','Availability']].map(([k,l]) => (
              <div key={k} className="auth-field">
                <label className="input-label">[ {l} ]</label>
                <input className="input-field" value={form[k]} onChange={set(k)} required={['name','specialty','city'].includes(k)} />
              </div>
            ))}
            <div style={{display:'flex',gap:'16px'}}>
              <div className="auth-field" style={{flex:1}}>
                <label className="input-label">[ Years Exp ]</label>
                <input className="input-field" type="number" value={form.years_experience} onChange={set('years_experience')} />
              </div>
              <div className="auth-field" style={{flex:1}}>
                <label className="input-label">[ Fees (₹) ]</label>
                <input className="input-field" type="number" value={form.fees} onChange={set('fees')} />
              </div>
            </div>
            <button type="submit" className="btn-primary" style={{width:'100%'}} disabled={adding}>
              {adding ? <span className="spinner" /> : 'Add Doctor'}
            </button>
          </form>
        </div>
      )}

      {tab === 'users' && (
        <div className="admin-table-wrap card">
          <table className="admin-table">
            <thead><tr><th>Username</th><th>Name</th><th>Email</th><th>Role</th><th>Joined</th></tr></thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id}>
                  <td>{u.username}</td><td>{u.full_name}</td><td>{u.email}</td>
                  <td><span className={`badge badge-${u.role}`}>{u.role}</span></td>
                  <td>{new Date(u.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
