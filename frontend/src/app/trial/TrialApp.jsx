import { Activity, Boxes, Building2, LayoutDashboard, Menu, Settings, X } from 'lucide-react';
import { useState } from 'react';
import { NavLink, Navigate, Route, Routes } from 'react-router-dom';

import brandLogo from '../../assets/images/equilateral_logo.png';
import { getUserScope } from '../common/roleUtils.js';
import { useAuthStore } from '../../store/authStore.js';
import { TrialAdmin } from './admin/TrialAdmin.jsx';
import { TrialCustomer } from './customer/TrialCustomer.jsx';
import { TrialStaff } from './staff/TrialStaff.jsx';

const navItems = [
  { label: 'Overview', path: '/app/trial/admin', Icon: LayoutDashboard },
  { label: 'Zones', path: '/app/trial/admin/zones', Icon: Boxes },
  { label: 'Studios', path: '/app/trial/admin/studios', Icon: Building2 },
  { label: 'Config', path: '/app/trial/admin/config', Icon: Settings },
  { label: 'Queue', path: '/app/trial/admin/queue', Icon: Activity },
];

function navClass(isActive) {
  return `flex h-11 items-center gap-3 rounded-lg px-3 text-sm font-medium ${
    isActive ? 'bg-white text-brand-red' : 'text-red-50 hover:bg-white/10'
  }`;
}

function TrialAdminShell() {
  const [isOpen, setIsOpen] = useState(false);
  return (
    <div className="min-h-screen bg-brand-blush text-ink">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-brand-deep bg-brand-red px-4 py-5 text-white lg:block">
        <div className="mb-7 flex flex-col gap-3 px-2">
          <img src={brandLogo} alt="Trial Queue logo" className="h-10 w-24 rounded-lg bg-white p-1 object-cover" />
          <div>
            <p className="font-semibold">Trial Admin</p>
            <p className="text-xs text-red-100">Trial Queue</p>
          </div>
        </div>
        <nav className="space-y-1">
          {navItems.map((item) => (
            <NavLink key={item.label} to={item.path} end={item.path === '/app/trial/admin'} className={({ isActive }) => navClass(isActive)}>
              <item.Icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 bg-white px-4 py-3">
          <div className="flex items-center justify-between gap-3">
            <button type="button" onClick={() => setIsOpen(true)} className="rounded-lg border border-line p-2 lg:hidden" aria-label="Open trial navigation">
              <Menu size={18} />
            </button>
            <div>
              <p className="text-sm text-muted">Trial Queue</p>
              <h1 className="text-lg font-semibold">Admin workspace</h1>
            </div>
            <NavLink to="/app" className="rounded-lg border border-brand-red/30 bg-brand-blush px-3 py-2 text-sm font-medium text-brand-red">
              Switch context
            </NavLink>
          </div>
        </header>
        <aside className={`fixed inset-y-0 left-0 z-50 w-72 bg-brand-red p-4 text-white transition-transform lg:hidden ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
          <div className="mb-5 flex items-center justify-between">
            <span className="font-semibold">Trial Admin</span>
            <button type="button" onClick={() => setIsOpen(false)} className="rounded-lg border border-white/30 p-2" aria-label="Close trial navigation">
              <X size={18} />
            </button>
          </div>
          <nav className="space-y-1">
            {navItems.map((item) => (
              <NavLink key={item.label} to={item.path} end={item.path === '/app/trial/admin'} onClick={() => setIsOpen(false)} className={({ isActive }) => navClass(isActive)}>
                <item.Icon size={18} />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </nav>
        </aside>
        <main className="mx-auto max-w-7xl px-4 py-6">
          <TrialAdmin />
        </main>
      </div>
    </div>
  );
}

export function TrialApp() {
  const { user } = useAuthStore();
  const scope = user ? getUserScope(user) : 'customer';
  return (
    <Routes>
      <Route path="admin/*" element={scope === 'admin' ? <TrialAdminShell /> : <Navigate to="/app/trial/staff" replace />} />
      <Route path="staff/*" element={<TrialStaff />} />
      <Route path="customer/*" element={<TrialCustomer />} />
      <Route path="*" element={<Navigate to={scope === 'admin' ? '/app/trial/admin' : '/app/trial/staff'} replace />} />
    </Routes>
  );
}
