import {
  Activity,
  ArrowLeftRight,
  Bell,
  BrainCircuit,
  CalendarDays,
  Gauge,
  LayoutDashboard,
  LogOut,
  Menu,
  SlidersHorizontal,
  Settings2,
  Store,
  UsersRound,
  X,
} from 'lucide-react';
import { useState } from 'react';
import { NavLink, Route, Routes, useNavigate } from 'react-router-dom';

import brandLogo from '../../../assets/images/equilateral_logo.png';
import { useAuthStore } from '../../../store/authStore.js';
import { enabledModules } from '../../common/moduleConfig.js';
import { Alerts } from './pages/Alerts.jsx';
import { Calendar } from './pages/Calendar.jsx';
import { Counters } from './pages/Counters.jsx';
import { Dashboard } from './pages/Dashboard.jsx';
import { MachineLearning } from './pages/MachineLearning.jsx';
import { Queue } from './pages/Queue.jsx';
import { Sections } from './pages/Sections.jsx';
import { Staff } from './pages/Staff.jsx';
import { StoreConfig } from './pages/StoreConfig.jsx';
import { Stores } from './pages/Stores.jsx';

const navItems = [
  { label: 'Dashboard', path: '/app/checkout/admin', Icon: LayoutDashboard },
  { label: 'Stores', path: '/app/checkout/admin/stores', Icon: Store },
  { label: 'Store Config', path: '/app/checkout/admin/store-config', Icon: SlidersHorizontal },
  { label: 'Sections', path: '/app/checkout/admin/sections', Icon: Settings2 },
  { label: 'Counters', path: '/app/checkout/admin/counters', Icon: Gauge },
  { label: 'Staff', path: '/app/checkout/admin/staff', Icon: UsersRound },
  { label: 'Queue', path: '/app/checkout/admin/queue', Icon: Activity },
  { label: 'Calendar', path: '/app/checkout/admin/calendar', Icon: CalendarDays },
  { label: 'ML', path: '/app/checkout/admin/ml', Icon: BrainCircuit },
  { label: 'Alerts', path: '/app/checkout/admin/alerts', Icon: Bell },
];

const canChangeContext = enabledModules.length > 1;

function getNavItemClass(isActive) {
  return `admin-sidebar-link relative flex h-11 items-center gap-3 overflow-hidden rounded-lg px-3 text-sm font-medium ${
    isActive ? 'bg-white text-brand-red hover:text-brand-red' : 'text-red-50'
  }`;
}

export function AdminApp() {
  const navigate = useNavigate();
  const { clearSession, user } = useAuthStore();
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);

  function logout() {
    clearSession();
    navigate('/app/login', { replace: true });
  }

  return (
    <div className="min-h-screen bg-brand-blush text-ink">
      <aside className="fixed inset-y-0 left-0 hidden w-64 flex-col border-r border-brand-deep bg-brand-red px-4 py-5 text-white lg:flex">
        <div className="mb-7 flex items-start gap-3 px-2 flex-col justify-center">
          <img src={brandLogo} alt="Checkout Queue logo" className="h-10 w-24 rounded-lg bg-white p-1 object-cover" />
          <div>
            <p className="font-semibold">Admin Portal</p>
            <p className="text-xs text-red-100">Checkout Queue</p>
          </div>
        </div>
        <nav className="flex-1 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.label}
              to={item.path}
              end={item.path === '/app/checkout/admin'}
              className={({ isActive }) => getNavItemClass(isActive)}
            >
              <item.Icon size={18} className="shrink-0" />
              <span className="truncate">{item.label}</span>
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
                onClick={() => setIsMobileNavOpen(true)}
                className="inline-flex items-center justify-center rounded-lg border border-line p-2 text-charcoal lg:hidden"
                aria-label="Open admin navigation"
              >
                <Menu size={18} />
              </button>
              <img src={brandLogo} alt="Checkout Queue logo" className="h-8 w-16 shrink-0 rounded-lg bg-white p-1 object-cover sm:h-9 sm:w-20 lg:hidden" />
              <div className="min-w-0">
                <p className="truncate text-xs sm:text-sm">Retail checkout operations</p>
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
                to="/app/checkout/customer"
                className="max-w-[38vw] shrink-0 truncate whitespace-nowrap rounded-lg border border-brand-red/30 bg-brand-blush px-2.5 py-2 text-xs font-medium text-brand-red hover:bg-white sm:max-w-none sm:px-3 sm:text-sm"
              >
                Customer view
              </NavLink>
            </div>
          </div>
        </header>

        <div
          className={`fixed inset-0 z-40 bg-black/40 transition-opacity lg:hidden ${
            isMobileNavOpen ? 'opacity-100' : 'pointer-events-none opacity-0'
          }`}
          onClick={() => setIsMobileNavOpen(false)}
          aria-hidden="true"
        />

        <aside
          className={`fixed inset-y-0 left-0 z-50 flex w-72 flex-col overflow-y-auto bg-brand-red p-4 text-white shadow-2xl transition-transform lg:hidden ${
            isMobileNavOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
          aria-label="Admin mobile navigation drawer"
        >
          <div className="mb-5 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <img src={brandLogo} alt="Checkout Queue logo" className="h-10 w-24 rounded-lg bg-white p-1 object-cover" />
              <div>
                <p className="font-semibold">Admin Portal</p>
                <p className="text-xs text-red-100">Checkout Queue</p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setIsMobileNavOpen(false)}
              className="rounded-lg border border-white/30 p-2 text-white"
              aria-label="Close admin navigation"
            >
              <X size={18} />
            </button>
          </div>

          <nav className="flex-1 space-y-1">
            {navItems.map((item) => (
              <NavLink
                key={item.label}
                to={item.path}
                end={item.path === '/app/checkout/admin'}
                onClick={() => setIsMobileNavOpen(false)}
                className={({ isActive }) => getNavItemClass(isActive)}
              >
                <item.Icon size={18} className="shrink-0" />
                <span className="truncate">{item.label}</span>
              </NavLink>
            ))}
          </nav>
          <SidebarAccount email={user?.email} onLogout={logout} />
        </aside>

        <main className="mx-auto max-w-7xl px-4 py-6">
          <Routes>
            <Route index element={<Dashboard />} />
            <Route path="stores" element={<Stores />} />
            <Route path="store-config" element={<StoreConfig />} />
            <Route path="sections" element={<Sections />} />
            <Route path="counters" element={<Counters />} />
            <Route path="staff" element={<Staff />} />
            <Route path="queue" element={<Queue />} />
            <Route path="calendar" element={<Calendar />} />
            <Route path="ml" element={<MachineLearning />} />
            <Route path="alerts" element={<Alerts />} />
          </Routes>
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
