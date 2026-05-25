import { Activity, ArrowLeftRight, Bell, Boxes, BrainCircuit, Building2, CalendarDays, LayoutDashboard, LogOut, Menu, Settings, Store, Users, X } from 'lucide-react';
import { useState } from 'react';
import { NavLink, Navigate, Route, Routes, useNavigate } from 'react-router-dom';

import brandLogo from '../../assets/images/equilateral_logo.png';
import { enabledModules, getAssignedModuleId } from '../common/moduleConfig.js';
import { getUserScope } from '../common/roleUtils.js';
import { useAuthStore } from '../../store/authStore.js';
import { TrialAdmin } from './admin/TrialAdmin.jsx';
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

const navItems = [
  { label: 'Dashboard', path: '/app/trial/admin', Icon: LayoutDashboard },
  { label: 'Stores', path: '/app/trial/admin/stores', Icon: Store },
  { label: 'Zones', path: '/app/trial/admin/zones', Icon: Boxes },
  { label: 'Studios', path: '/app/trial/admin/studios', Icon: Building2 },
  { label: 'Staff', path: '/app/trial/admin/staff', Icon: Users },
  { label: 'Config', path: '/app/trial/admin/config', Icon: Settings },
  { label: 'Calendar', path: '/app/trial/admin/calendar', Icon: CalendarDays },
  { label: 'ML', path: '/app/trial/admin/ml', Icon: BrainCircuit },
  { label: 'Notifications', path: '/app/trial/admin/notifications', Icon: Bell },
  { label: 'Queue', path: '/app/trial/admin/queue', Icon: Activity },
];

const canChangeContext = enabledModules.length > 1;

function navClass(isActive) {
  return `admin-sidebar-link relative flex h-11 items-center gap-3 overflow-hidden rounded-lg px-3 text-sm font-medium ${
    isActive ? 'bg-white text-brand-red hover:text-brand-red' : 'text-red-50'
  }`;
}

function TrialAdminShell() {
  const navigate = useNavigate();
  const { clearSession, user } = useAuthStore();
  const [isOpen, setIsOpen] = useState(false);

  function logout() {
    clearSession();
    navigate('/app/login', { replace: true });
  }

  return (
    <div className="min-h-screen bg-brand-blush text-ink">
      <aside className="fixed inset-y-0 left-0 hidden w-64 flex-col border-r border-brand-deep bg-brand-red px-4 py-5 text-white lg:flex">
        <div className="mb-7 flex items-start gap-3 px-2 flex-col justify-center">
          <img src={brandLogo} alt="Trial Queue logo" className="h-10 w-24 rounded-lg bg-white p-1 object-cover" />
          <div>
            <p className="font-semibold">Admin Portal</p>
            <p className="text-xs text-red-100">Trial Queue</p>
          </div>
        </div>
        <nav className="flex-1 space-y-1">
          {navItems.map((item) => (
            <NavLink key={item.label} to={item.path} end={item.path === '/app/trial/admin'} className={({ isActive }) => navClass(isActive)}>
              <item.Icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <SidebarAccount email={user?.email} onLogout={logout} />
      </aside>
      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 bg-white px-4 py-3 ">
          <div className="flex items-center justify-between gap-3">
            <div className="flex min-w-0 items-center gap-2 sm:gap-3">
              <button
                type="button"
                onClick={() => setIsOpen(true)}
                className="inline-flex items-center justify-center rounded-lg border border-line p-2 text-charcoal lg:hidden"
                aria-label="Open trial navigation"
              >
                <Menu size={18} />
              </button>
              <img src={brandLogo} alt="Trial Queue logo" className="h-8 w-16 shrink-0 rounded-lg bg-white p-1 object-cover sm:h-9 sm:w-20 lg:hidden" />
              <div className="min-w-0">
                <p className="truncate text-xs sm:text-sm">Retail trial operations</p>
                <h1 className="truncate text-sm font-semibold sm:text-lg">Admin workspace</h1>
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              {canChangeContext ? (
                <NavLink
                  to="/app"
                  className="inline-flex items-center justify-center gap-2 rounded-lg border border-line px-2.5 py-2 text-xs font-medium text-charcoal hover:border-brand-red hover:text-brand-red sm:px-3 sm:text-sm"
                  title="Change product context"
                >
                  <ArrowLeftRight size={16} />
                  <span className="hidden sm:inline">Change context</span>
                </NavLink>
              ) : null}
              <NavLink
                to="/app/trial/customer"
                className="max-w-[38vw] shrink-0 truncate whitespace-nowrap rounded-lg border border-brand-red/30 bg-brand-blush px-2.5 py-2 text-xs font-medium text-brand-red hover:bg-white sm:max-w-none sm:px-3 sm:text-sm"
              >
                Customer view
              </NavLink>
            </div>
          </div>
        </header>

        <div
          className={`fixed inset-0 z-40 bg-black/40 transition-opacity lg:hidden ${
            isOpen ? 'opacity-100' : 'pointer-events-none opacity-0'
          }`}
          onClick={() => setIsOpen(false)}
          aria-hidden="true"
        />

        <aside
          className={`fixed inset-y-0 left-0 z-50 flex w-72 flex-col overflow-y-auto bg-brand-red p-4 text-white shadow-2xl transition-transform lg:hidden ${
            isOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
          aria-label="Trial admin mobile navigation drawer"
        >
          <div className="mb-5 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <img src={brandLogo} alt="Trial Queue logo" className="h-10 w-24 rounded-lg bg-white p-1 object-cover" />
              <div>
                <p className="font-semibold">Admin Portal</p>
                <p className="text-xs text-red-100">Trial Queue</p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="rounded-lg border border-white/30 p-2 text-white"
              aria-label="Close trial navigation"
            >
              <X size={18} />
            </button>
          </div>
          <nav className="flex-1 space-y-1">
            {navItems.map((item) => (
              <NavLink key={item.label} to={item.path} end={item.path === '/app/trial/admin'} onClick={() => setIsOpen(false)} className={({ isActive }) => navClass(isActive)}>
                <item.Icon size={18} />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </nav>
          <SidebarAccount email={user?.email} onLogout={logout} />
        </aside>
        <main className="mx-auto max-w-7xl px-4 py-6">
          <TrialAdmin />
        </main>
      </div>
    </div>
  );
}

function SidebarAccount({ email, onLogout }) {
  return (
    <div className="mt-auto border-t border-white/20 pt-4">
      <p className="truncate px-2 text-xs text-red-100" title={email || 'Signed in'}>
        {email || 'Signed in'}
      </p>
      <button
        type="button"
        onClick={onLogout}
        className="mt-2 flex h-11 w-full items-center gap-3 rounded-lg px-3 text-sm font-medium text-red-50 hover:bg-white hover:text-brand-red"
      >
        <LogOut size={18} className="shrink-0" />
        <span>Logout</span>
      </button>
    </div>
  );
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
            <TrialAdminShell />
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
