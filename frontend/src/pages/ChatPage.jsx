import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import client from '../api/client';
import './ChatPage.css';

function Message({ msg }) {
  const isUser = msg.role === 'user';
  return (
    <div className={`msg-row ${isUser ? 'msg-row-user' : 'msg-row-ai'}`}>
      {!isUser && <div className="msg-avatar">🩺</div>}
      <div className={`msg-bubble ${isUser ? 'msg-bubble-user' : 'msg-bubble-ai'}`}>
        <p>{msg.content}</p>
      </div>
      {isUser && <div className="msg-avatar msg-avatar-user">U</div>}
    </div>
  );
}

export default function ChatPage() {
  const { user } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [typing, setTyping] = useState(false);
  const [banner, setBanner] = useState(null); // {type, text}
  const [listening, setListening] = useState(false);
  const [micError, setMicError] = useState('');
  const bottomRef = useRef();
  const fileRef = useRef();
  const recognitionRef = useRef(null);

  // Web Speech API — voice to text
  const toggleMic = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setMicError('Voice not supported in this browser. Try Chrome.');
      setTimeout(() => setMicError(''), 3000);
      return;
    }
    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }
    const rec = new SpeechRecognition();
    rec.lang = 'en-IN';
    rec.interimResults = true;
    rec.continuous = false;
    rec.onstart = () => setListening(true);
    rec.onresult = (e) => {
      const transcript = Array.from(e.results).map(r => r[0].transcript).join('');
      setInput(transcript);
    };
    rec.onerror = () => { setListening(false); setMicError('Mic access denied.'); setTimeout(() => setMicError(''), 3000); };
    rec.onend = () => setListening(false);
    recognitionRef.current = rec;
    rec.start();
  };

  useEffect(() => { loadSessions(); }, []);
  useEffect(() => { if (activeSession) loadHistory(activeSession); }, [activeSession]);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, typing]);

  // Listen for New Chat fired from the main sidebar
  useEffect(() => {
    const handler = () => newSession();
    window.addEventListener('medicare:newChat', handler);
    return () => window.removeEventListener('medicare:newChat', handler);
  }, []);

  const loadSessions = async () => {
    try {
      const { data } = await client.get('/chat/sessions');
      setSessions(data);
    } catch {}
  };

  const loadHistory = async (sid) => {
    try {
      const { data } = await client.get(`/chat/history/${sid}`);
      setMessages(data);
    } catch {}
  };

  const newSession = async () => {
    const { data } = await client.post('/chat/sessions');
    setSessions(s => [data, ...s]);
    setActiveSession(data.id);
    setMessages([]);
    setBanner(null);
  };

  const deleteSession = async (sid, e) => {
    e.stopPropagation();
    const ok = window.confirm('Delete this chat? This action cannot be undone.');
    if (!ok) return;
    await client.delete(`/chat/sessions/${sid}`);
    setSessions(s => s.filter(x => x.id !== sid));
    if (activeSession === sid) { setActiveSession(null); setMessages([]); }
  };

  const deleteAllSessions = async () => {
    if (!sessions.length) return;
    const ok = window.confirm('Delete all chats? This action cannot be undone.');
    if (!ok) return;
    await client.delete('/chat/sessions');
    setSessions([]);
    setActiveSession(null);
    setMessages([]);
    setBanner(null);
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const userMsg = { role: 'user', content: input };
    setMessages(m => [...m, userMsg]);
    setInput('');
    setTyping(true);
    setBanner(null);
    try {
      const { data } = await client.post('/chat/message', {
        message: userMsg.content,
        session_id: activeSession,
      });
      setTyping(false);
      setMessages(m => [...m, { role: 'assistant', content: data.response }]);
      if (!activeSession) setActiveSession(data.session_id);
      if (data.is_emergency) setBanner({ type: 'emergency', text: '🚨 Emergency detected! Please call 112 or visit the nearest emergency room immediately.' });
      else if (data.is_clinical_report) setBanner({ type: 'clinical', text: '📄 Clinical report detected. This is informational only — always follow your doctor\'s advice.' });
      await loadSessions();
    } catch {
      setTyping(false);
      setMessages(m => [...m, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }]);
    }
  };

  const handleFile = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setMessages(m => [...m, { role: 'user', content: `📎 Uploaded: ${file.name}` }]);
    setTyping(true);
    try {
      const form = new FormData();
      form.append('file', file);
      const { data } = await client.post('/health/report', form, { headers: { 'Content-Type': 'multipart/form-data' } });
      setTyping(false);
      setMessages(m => [...m, { role: 'assistant', content: data.analysis }]);
      setBanner({ type: 'clinical', text: '📄 Medical report analyzed. Review the findings with your doctor.' });
    } catch {
      setTyping(false);
      setMessages(m => [...m, { role: 'assistant', content: 'Could not analyze the file. Please try again.' }]);
    }
    fileRef.current.value = '';
  };

  const welcome = messages.length === 0;

  return (
    <div className="chat-layout">
      {/* Sessions sidebar — title only, no duplicate button */}
      <aside className="chat-sidebar">
        <div className="chat-sidebar-header">
          <span className="chat-sidebar-title">Recent Chats</span>
          <button
            type="button"
            className="chat-clear-all"
            onClick={deleteAllSessions}
            disabled={sessions.length === 0}
            title="Remove all chats"
          >
            Remove All
          </button>
        </div>
        <div className="chat-session-list">
          {sessions.map(s => (
            <div
              key={s.id}
              className={`chat-session-item ${activeSession === s.id ? 'active' : ''}`}
              onClick={() => setActiveSession(s.id)}
            >
              <span className="chat-session-title">{s.title}</span>
              <button className="chat-session-del" onClick={(e) => deleteSession(s.id, e)}>×</button>
            </div>
          ))}
          {sessions.length === 0 && <p className="chat-empty-hint">No chats yet. Start a new one!</p>}
        </div>
      </aside>

      {/* Main chat area */}
      <div className="chat-main">
        {/* Alert banner */}
        {banner && (
          <div className={banner.type === 'emergency' ? 'alert-emergency' : 'alert-clinical'} style={{margin:'16px 16px 0'}}>
            {banner.text}
          </div>
        )}

        {/* Messages */}
        <div className="chat-messages">
          {welcome && (
            <div className="chat-welcome fade-up">
              <div className="chat-welcome-icon">🩺</div>
              <h2>MediCare AI Assistant</h2>
              <p>Ask me about symptoms, medications, appointments, or anything health-related.</p>
              <div className="chat-suggestions">
                {['I have a headache and fever', 'Find a cardiologist in Ahmedabad', 'Book an appointment', 'What are side effects of Paracetamol?'].map(q => (
                  <button key={q} className="chat-suggestion" onClick={() => { setInput(q); }}>
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m, i) => <Message key={i} msg={m} />)}
          {typing && (
            <div className="msg-row msg-row-ai">
              <div className="msg-avatar">🩺</div>
              <div className="msg-bubble msg-bubble-ai msg-typing">
                <span className="typing-dot" /><span className="typing-dot" /><span className="typing-dot" />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input bar */}
        <form className="chat-input-bar" onSubmit={sendMessage}>
          <input
            className="chat-input"
            placeholder={listening ? '🎤 Listening... speak now' : 'Ask me anything about your health...'}
            value={input}
            onChange={e => setInput(e.target.value)}
            disabled={loading}
          />

          {/* Toolbar buttons */}
          <div className="chat-toolbar">
            {/* Upload button */}
            <button
              type="button"
              className={`chat-tool-btn`}
              onClick={() => fileRef.current.click()}
              title="Upload medical report (image or PDF)"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              <span className="chat-tool-label">Upload</span>
            </button>
            <input ref={fileRef} type="file" accept="image/*,.pdf" style={{display:'none'}} onChange={handleFile} />

            {/* Mic button */}
            <button
              type="button"
              className={`chat-tool-btn ${listening ? 'chat-tool-btn--active' : ''}`}
              onClick={toggleMic}
              title={listening ? 'Stop recording' : 'Voice input'}
            >
              {listening ? (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                  <rect x="6" y="6" width="12" height="12" rx="2"/>
                </svg>
              ) : (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"/>
                  <path d="M19 10v2a7 7 0 01-14 0v-2"/>
                  <line x1="12" y1="19" x2="12" y2="23"/>
                  <line x1="8" y1="23" x2="16" y2="23"/>
                </svg>
              )}
              <span className="chat-tool-label">{listening ? 'Stop' : 'Mic'}</span>
            </button>
          </div>

          {micError && <div className="chat-mic-error">{micError}</div>}

          <button type="submit" className="btn-primary chat-send" disabled={!input.trim() || loading}>
            {loading ? <span className="spinner" /> : (
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
