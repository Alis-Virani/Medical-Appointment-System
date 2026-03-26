import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Layout.css';

const NAV = {
  patient: [
    { to: '/app/chat',   icon: '💬', label: 'AI Chat' },
    { to: '/app/health', icon: '📋', label: 'Health History' },
  ],
  doctor: [
    { to: '/app/chat',      icon: '💬', label: 'AI Assistant' },
    { to: '/app/dashboard', icon: '📊', label: 'Dashboard' },
    { to: '/app/notes',     icon: '📝', label: 'Patient Notes' },
    { to: '/app/schedule',  icon: '📅', label: 'My Schedule' },
  ],
  admin: [
    { to: '/app/chat',  icon: '💬', label: 'AI Assistant' },
    { to: '/app/admin', icon: '⚙️',  label: 'Doctor Management' },
  ],
};

const ROLE_BADGE = { patient: 'badge-patient', doctor: 'badge-doctor', admin: 'badge-admin' };

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const links = NAV[user?.role] || NAV.patient;

  const handleLogout = () => { logout(); navigate('/'); };
  const isChat = useLocation().pathname === '/app/chat';
  const fireNewChat = () => {
    if (!isChat) navigate('/app/chat');
    window.dispatchEvent(new CustomEvent('medicare:newChat'));
  };

  return (
    <div className="layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <span className="sidebar-logo">🩺</span>
          <span className="sidebar-title">MediCare AI</span>
        </div>

        <nav className="sidebar-nav">
          {links.map(({ to, icon, label }) => (
            <NavLink
              key={to} to={to}
              className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
            >
              <span className="sidebar-link-icon">{icon}</span>
              <span>{label}</span>
            </NavLink>
          ))}

          {/* New Chat — shown under whichever link points to /app/chat */}
          <button className="sidebar-new-chat" onClick={fireNewChat}>
            <span className="sidebar-link-icon">✏️</span>
            <span>New Chat</span>
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div className="sidebar-avatar">
              {(user?.full_name || 'U').charAt(0).toUpperCase()}
            </div>
            <div className="sidebar-user-info">
              <span className="sidebar-user-name">{user?.full_name || user?.username}</span>
              <span className={`badge ${ROLE_BADGE[user?.role]}`}>{user?.role}</span>
            </div>
          </div>
          <button className="btn-ghost sidebar-logout" onClick={handleLogout} title="Logout">
            ↩
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
