import { Navigate, Route, Routes } from 'react-router-dom';

import { useAuthStore } from '../../store/authStore.js';
import { getAssignedModuleId } from '../common/moduleConfig.js';
import { getUserScope } from '../common/roleUtils.js';
import { AdminApp } from './admin/AdminApp.jsx';
import { CustomerApp } from './customer/CustomerApp.jsx';
import { StaffApp } from './staff/StaffApp.jsx';

function RequireAdmin({ children }) {
  const { user } = useAuthStore();
  if (!user) return <Navigate to="/app/checkout/login" replace />;
  if (getUserScope(user) !== 'admin') return <Navigate to="/app/checkout/staff" replace />;
  return children;
}

function RequireCheckoutStaff({ children }) {
  const { user } = useAuthStore();
  if (!user) return <Navigate to="/app/checkout/login" replace />;
  if (getAssignedModuleId(user) === 'trial') return <Navigate to="/app/trial/staff" replace />;
  return children;
}

export function CheckoutApp() {
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
          <RequireCheckoutStaff>
            <StaffApp />
          </RequireCheckoutStaff>
        }
      />
      <Route path="customer/*" element={<CustomerApp />} />
      <Route path="*" element={<Navigate to={user ? (scope === 'admin' ? '/app/checkout/admin' : '/app/checkout/staff') : '/app/checkout/customer'} replace />} />
    </Routes>
  );
}
