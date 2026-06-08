import { useEffect, useState } from "react";
import {
  Navigate,
  Route,
  BrowserRouter as Router,
  Routes,
  useLocation,
} from "react-router-dom";
import { ToastContainer } from "react-toastify";

import { fetchCurrentUser } from "./api/authApi.js";
import { CheckoutApp } from "./app/checkout/CheckoutApp.jsx";
import { ContextSelector } from "./app/common/ContextSelector.jsx";
import { Landing } from "./app/common/Landing.jsx";
import { Login } from "./app/common/Login.jsx";
import { BrandHeader } from "./app/common/BrandHeader.jsx";
import { Footer } from "./app/common/Footer.jsx";
import { PwaRefreshButton } from "./app/common/PwaRefreshButton.jsx";
import { TrialApp } from "./app/trial/TrialApp.jsx";
import { useAuthStore } from "./store/authStore.js";
import DemoToolsFAB from "./app/common/DemoToolsFAB.jsx";

function RequireAuth({ children }) {
  const { accessToken } = useAuthStore();
  if (!accessToken) return <Navigate to="/app/login" replace />;
  return children;
}

export default function App() {
  const { accessToken, user, setUser, clearSession } = useAuthStore();
  const [bootstrapping, setBootstrapping] = useState(
    Boolean(accessToken && !user),
  );
  const canManageDemoTools = user?.default_role === "SUPER_ADMIN";
  useEffect(() => {
    const loader = document.getElementById("app-boot-loader");
    if (!loader) return undefined;

    loader.classList.add("is-hidden");
    const removeLoader = window.setTimeout(() => {
      loader.remove();
    }, 260);

    return () => window.clearTimeout(removeLoader);
  }, []);

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
      <AppRoutes canManageDemoTools={canManageDemoTools} />
    </Router>
  );
}

function AppRoutes({ canManageDemoTools } ) {
  const location = useLocation();
  const showHeader = location.pathname === "/";

  return (
    <>
      {showHeader ? <BrandHeader /> : null}
      <ToastContainer
        position="top-right"
        autoClose={3500}
        newestOnTop
        pauseOnFocusLoss={false}
        theme="colored"
      />
      <PwaRefreshButton />
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
      {showHeader ? <Footer /> : null}
      {canManageDemoTools && <DemoToolsFAB />}
    </>
  );
}
