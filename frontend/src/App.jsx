import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import LandingPage from './pages/LandingPage';
import AuthPage from './pages/AuthPage';
import Layout from './components/Layout';
import ChatPage from './pages/ChatPage';
import HealthHistoryPage from './pages/HealthHistoryPage';
import DoctorDashboardPage from './pages/DoctorDashboardPage';
import PatientNotesPage from './pages/PatientNotesPage';
import SchedulePage from './pages/SchedulePage';
import AdminPage from './pages/AdminPage';

function ProtectedRoute({ children, roles }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/auth" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/app/chat" replace />;
  return children;
}

function AppRoutes() {
  const { user } = useAuth();
  return (
    <Routes>
      <Route path="/" element={user ? <Navigate to="/app/chat" /> : <LandingPage />} />
      <Route path="/auth" element={user ? <Navigate to="/app/chat" /> : <AuthPage />} />
      <Route path="/app" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route path="chat" element={<ChatPage />} />
        <Route path="health" element={<ProtectedRoute roles={['patient']}><HealthHistoryPage /></ProtectedRoute>} />
        <Route path="dashboard" element={<ProtectedRoute roles={['doctor']}><DoctorDashboardPage /></ProtectedRoute>} />
        <Route path="notes" element={<ProtectedRoute roles={['doctor']}><PatientNotesPage /></ProtectedRoute>} />
        <Route path="schedule" element={<ProtectedRoute roles={['doctor']}><SchedulePage /></ProtectedRoute>} />
        <Route path="admin" element={<ProtectedRoute roles={['admin']}><AdminPage /></ProtectedRoute>} />
        <Route index element={<Navigate to="chat" />} />
      </Route>
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}
