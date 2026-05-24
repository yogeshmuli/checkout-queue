import { useEffect, useState } from 'react';
import { Navigate, Route, BrowserRouter as Router, Routes, useLocation } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';

import { fetchCurrentUser } from './api/authApi.js';
import { CheckoutApp } from './app/checkout/CheckoutApp.jsx';
import { ContextSelector } from './app/common/ContextSelector.jsx';
import { Landing } from './app/common/Landing.jsx';
import { Login } from './app/common/Login.jsx';
import { BrandHeader } from './app/common/BrandHeader.jsx';
import { TrialApp } from './app/trial/TrialApp.jsx';
import { useAuthStore } from './store/authStore.js';

function RequireAuth({ children }) {
  const { accessToken } = useAuthStore();
  if (!accessToken) return <Navigate to="/app/login" replace />;
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
      <AppRoutes />
    </Router>
  );
}

function AppRoutes() {
  const location = useLocation();
  const showHeader = location.pathname === '/';

  return (
    <>
      {showHeader ? <BrandHeader /> : null}
      <ToastContainer position="top-right" autoClose={3500} newestOnTop pauseOnFocusLoss={false} theme="colored" />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route
          path="/app"
          element={
            <RequireAuth>
              <ContextSelector />
            </RequireAuth>
          }
        />
        <Route path="/app/login" element={<Login />} />
        <Route path="/app/checkout/*" element={<CheckoutApp />} />
        <Route path="/app/trial/*" element={<TrialApp />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
