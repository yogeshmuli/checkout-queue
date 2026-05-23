import {
  Activity,
  Bell,
  BrainCircuit,
  CalendarDays,
  Gauge,
  LayoutDashboard,
  Menu,
  SlidersHorizontal,
  Settings2,
  Store,
  UsersRound,
  X,
} from 'lucide-react';
import { useState } from 'react';
import { NavLink, Route, Routes } from 'react-router-dom';

import brandLogo from '../../assets/images/equilateral_logo.png';
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
  { label: 'Dashboard', path: '/app/admin', Icon: LayoutDashboard },
  { label: 'Stores', path: '/app/admin/stores', Icon: Store },
  { label: 'Store Config', path: '/app/admin/store-config', Icon: SlidersHorizontal },
  { label: 'Sections', path: '/app/admin/sections', Icon: Settings2 },
  { label: 'Counters', path: '/app/admin/counters', Icon: Gauge },
  { label: 'Staff', path: '/app/admin/staff', Icon: UsersRound },
  { label: 'Queue', path: '/app/admin/queue', Icon: Activity },
  { label: 'Calendar', path: '/app/admin/calendar', Icon: CalendarDays },
  { label: 'ML', path: '/app/admin/ml', Icon: BrainCircuit },
  { label: 'Alerts', path: '/app/admin/alerts', Icon: Bell },
];

function getNavItemClass(isActive) {
  return `admin-sidebar-link relative flex h-11 items-center gap-3 overflow-hidden rounded-lg px-3 text-sm font-medium ${
    isActive ? 'bg-white text-brand-red hover:text-brand-red' : 'text-red-50'
  }`;
}

export function AdminApp() {
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);
console.log('AdminApp rendered');
  return (
    <div className="min-h-screen bg-brand-blush text-ink">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-brand-deep bg-brand-red px-4 py-5 text-white lg:block">
        <div className="mb-7 flex items-start gap-3 px-2 flex-col justify-center">
          <img src={brandLogo} alt="Checkout Queue logo" className="h-10 w-24 rounded-lg bg-white p-1 object-cover" />
          <div>
            <p className="font-semibold">Admin Portal</p>
            <p className="text-xs text-red-100">Checkout Queue</p>
          </div>
        </div>
        <nav className="space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.label}
              to={item.path}
              end={item.path === '/app/admin'}
              className={({ isActive }) => getNavItemClass(isActive)}
            >
              <item.Icon size={18} className="shrink-0" />
              <span className="truncate">{item.label}</span>
            </NavLink>
          ))}
        </nav>
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
            <NavLink
              to="/app/customer"
              className="max-w-[42vw] shrink-0 truncate whitespace-nowrap rounded-lg border border-brand-red/30 bg-brand-blush px-2.5 py-2 text-xs font-medium text-brand-red hover:bg-white sm:max-w-none sm:px-3 sm:text-sm"
            >
              Customer view
            </NavLink>
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
          className={`fixed inset-y-0 left-0 z-50 w-72 overflow-y-auto bg-brand-red p-4 text-white shadow-2xl transition-transform lg:hidden ${
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

          <nav className="space-y-1">
            {navItems.map((item) => (
              <NavLink
                key={item.label}
                to={item.path}
                end={item.path === '/app/admin'}
                onClick={() => setIsMobileNavOpen(false)}
                className={({ isActive }) => getNavItemClass(isActive)}
              >
                <item.Icon size={18} className="shrink-0" />
                <span className="truncate">{item.label}</span>
              </NavLink>
            ))}
          </nav>
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
