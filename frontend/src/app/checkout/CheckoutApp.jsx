import { Navigate, Route, Routes } from 'react-router-dom';

import { useAuthStore } from '../../store/authStore.js';
import { getUserScope } from '../common/roleUtils.js';
import { AdminApp } from './admin/AdminApp.jsx';
import { CustomerApp } from './customer/CustomerApp.jsx';
import { StaffApp } from './staff/StaffApp.jsx';

function RequireAdmin({ children }) {
  const { user } = useAuthStore();
  if (!user) return <Navigate to="/app/login" replace />;
  if (getUserScope(user) !== 'admin') return <Navigate to="/app/checkout/staff" replace />;
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
      <Route path="staff/*" element={<StaffApp />} />
      <Route path="customer/*" element={<CustomerApp />} />
      <Route path="*" element={<Navigate to={scope === 'admin' ? '/app/checkout/admin' : '/app/checkout/staff'} replace />} />
    </Routes>
  );
}
