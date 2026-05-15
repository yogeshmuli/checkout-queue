import { useEffect, useState } from 'react';
import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom';

import { fetchCurrentUser } from './api/authApi.js';
import { AdminApp } from './app/admin/AdminApp.jsx';
import { Landing } from './app/common/Landing.jsx';
import { Login } from './app/common/Login.jsx';
import { CustomerApp } from './app/customer/CustomerApp.jsx';
import { StaffApp } from './app/staff/StaffApp.jsx';
import { useAuthStore } from './store/authStore.js';
import { getUserScope } from './app/common/roleUtils.js';

function RequireAuth({ children }) {
  const { accessToken } = useAuthStore();
  if (!accessToken) return <Navigate to="/app/login" replace />;
  return children;
}

function RequireAdmin({ children }) {
  const { user } = useAuthStore();
  if (!user) return <Navigate to="/app/login" replace />;
  if (getUserScope(user) !== 'admin') return <Navigate to="/app/staff" replace />;
  return children;
}

export default function App() {
  const { accessToken, user, setUser, clearSession } = useAuthStore();
  const [bootstrapping, setBootstrapping] = useState(Boolean(accessToken && !user));

  useEffect(() => {
    let cancelled = false;

    if (!accessToken || user) {
      setBootstrapping(false);
      return () => {
        cancelled = true;
      };
    }

    fetchCurrentUser()
      .then((profile) => {
        if (cancelled) return;
        setUser(profile);
      })
      .catch(() => {
        if (cancelled) return;
        clearSession();
      })
      .finally(() => {
        if (!cancelled) setBootstrapping(false);
      });

    return () => {
      cancelled = true;
    };
  }, [accessToken, user, setUser, clearSession]);

  if (bootstrapping) {
    return <div className="min-h-screen bg-brand-blush" />;
  }

  return (
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/app" element={<Landing />} />
        <Route path="/app/login" element={<Login />} />
        <Route
          path="/app/admin/*"
          element={
            <RequireAuth>
              <RequireAdmin>
                <AdminApp />
              </RequireAdmin>
            </RequireAuth>
          }
        />
        <Route
          path="/app/staff/*"
          element={
            <RequireAuth>
              <StaffApp />
            </RequireAuth>
          }
        />
        <Route path="/app/customer/*" element={<CustomerApp />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

