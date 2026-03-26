import { useState, useEffect } from 'react';
import client from '../api/client';
import './DashboardPages.css';

export default function PatientNotesPage() {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ patient_id: '', patient_name: '', content: '', diagnosis: '', prescription: '' });
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  useEffect(() => { loadNotes(); }, []);

  const loadNotes = async () => {
    try { const { data } = await client.get('/notes/'); setNotes(data); }
    finally { setLoading(false); }
  };

  const set = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  const saveNote = async (e) => {
    e.preventDefault(); setSaving(true); setMsg('');
    try {
      await client.post(`/notes/?patient_id=${form.patient_id}&patient_name=${encodeURIComponent(form.patient_name)}&content=${encodeURIComponent(form.content)}&diagnosis=${encodeURIComponent(form.diagnosis)}&prescription=${encodeURIComponent(form.prescription)}`);
      setMsg('Note saved!');
      setForm({ patient_id: '', patient_name: '', content: '', diagnosis: '', prescription: '' });
      loadNotes();
    } catch { setMsg('Failed to save note.'); }
    finally { setSaving(false); }
  };

  if (loading) return <div className="page-loading"><span className="spinner" /></div>;

  return (
    <div className="dash-page">
      <div className="dash-header">
        <h1 className="dash-title">Patient Notes</h1>
        <p className="dash-sub">Write and manage clinical notes for your patients</p>
      </div>

      <div className="dash-grid-2">
        {/* New note form */}
        <div>
          <h2 className="section-heading">✏️ New Note</h2>
          <div className="card">
            {msg && <div className={msg.includes('saved') ? 'alert-success' : 'alert-error'} style={{marginBottom:'16px'}}>{msg}</div>}
            <form onSubmit={saveNote} className="notes-form">
              <div className="auth-field">
                <label className="input-label">[ Patient Name ]</label>
                <input className="input-field" placeholder="John Doe" value={form.patient_name} onChange={set('patient_name')} required />
              </div>
              <div className="auth-field">
                <label className="input-label">[ Patient ID ]</label>
                <input className="input-field" placeholder="User ID (number)" type="number" value={form.patient_id} onChange={set('patient_id')} required />
              </div>
              <div className="auth-field">
                <label className="input-label">[ Clinical Notes ]</label>
                <textarea className="input-field notes-textarea" placeholder="Examination findings..." value={form.content} onChange={set('content')} required />
              </div>
              <div className="auth-field">
                <label className="input-label">[ Diagnosis ]</label>
                <input className="input-field" placeholder="Diagnosis..." value={form.diagnosis} onChange={set('diagnosis')} />
              </div>
              <div className="auth-field">
                <label className="input-label">[ Prescription ]</label>
                <input className="input-field" placeholder="Medication / dosage..." value={form.prescription} onChange={set('prescription')} />
              </div>
              <button type="submit" className="btn-primary" style={{width:'100%', marginTop:'8px'}} disabled={saving}>
                {saving ? <span className="spinner" /> : 'Save Note'}
              </button>
            </form>
          </div>
        </div>

        {/* Notes list */}
        <div>
          <h2 className="section-heading">📋 Previous Notes</h2>
          {notes.length === 0 ? (
            <div className="card empty-card"><p>No notes yet</p></div>
          ) : notes.map(n => (
            <div key={n.id} className="card note-card fade-up">
              <div className="appt-header">
                <span className="appt-name">{n.patient_name}</span>
                <span className="history-date">{new Date(n.created_at).toLocaleDateString()}</span>
              </div>
              {n.diagnosis && <div className="note-field"><strong>Diagnosis:</strong> {n.diagnosis}</div>}
              {n.prescription && <div className="note-field"><strong>Rx:</strong> {n.prescription}</div>}
              <div className="note-content">{n.content}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
