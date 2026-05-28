import { Navigate, Route, Routes } from 'react-router-dom';

import { useAuthStore } from '../../store/authStore.js';
import { getAssignedModuleId } from '../common/moduleConfig.js';
import { getUserScope } from '../common/roleUtils.js';
import { AdminApp } from './admin/AdminApp.jsx';
import { TrialCustomer } from './customer/TrialCustomer.jsx';
import { TrialStaff } from './staff/TrialStaff.jsx';

function RequireAdmin({ children }) {
  const { user } = useAuthStore();
  if (!user) return <Navigate to="/app/login" replace />;
  if (getUserScope(user) !== 'admin') return <Navigate to="/app/trial/staff" replace />;
  return children;
}

function RequireTrialStaff({ children }) {
  const { user } = useAuthStore();
  if (!user) return <Navigate to="/app/login" replace />;
  if (getAssignedModuleId(user) === 'checkout') return <Navigate to="/app/checkout/staff" replace />;
  return children;
}

export function TrialApp() {
  const { user } = useAuthStore();
  const scope = user ? getUserScope(user) : 'customer';
  return (
    <Routes>
      <Route
        path="admin/*"
        element={
          <RequireAdmin>
            <AdminApp />
          </RequireAdmin>
        }
      />
      <Route
        path="staff/*"
        element={
          <RequireTrialStaff>
            <TrialStaff />
          </RequireTrialStaff>
        }
      />
      <Route path="customer/*" element={<TrialCustomer />} />
      <Route path="*" element={<Navigate to={user ? (scope === 'admin' ? '/app/trial/admin' : '/app/trial/staff') : '/app/trial/customer'} replace />} />
    </Routes>
  );
}
