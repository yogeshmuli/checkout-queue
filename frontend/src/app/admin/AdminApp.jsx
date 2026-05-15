import {
  Activity,
  Bell,
  CalendarDays,
  Gauge,
  LayoutDashboard,
  Plus,
  Settings2,
  Store,
  UsersRound,
} from 'lucide-react';
import { NavLink, Route, Routes } from 'react-router-dom';

import brandLogo from '../../assets/images/equilateral_logo.png';
import { MetricTile } from '../common/MetricTile.jsx';
import { SectionHeader } from '../common/SectionHeader.jsx';
import { AdminStores } from './AdminStores.jsx';

const navItems = [
  { label: 'Dashboard', path: '/app/admin', Icon: LayoutDashboard },
  { label: 'Stores', path: '/app/admin/stores', Icon: Store },
  { label: 'Sections', path: '/app/admin/sections', Icon: Settings2 },
  { label: 'Counters', path: '/app/admin/counters', Icon: Gauge },
  { label: 'Staff', path: '/app/admin/staff', Icon: UsersRound },
  { label: 'Queue', path: '/app/admin/queue', Icon: Activity },
  { label: 'Calendar', path: '/app/admin/calendar', Icon: CalendarDays },
  { label: 'Alerts', path: '/app/admin/alerts', Icon: Bell },
];

export function AdminApp() {
  return (
    <div className="min-h-screen bg-brand-blush text-ink">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-brand-deep bg-brand-red px-4 py-5 text-white lg:block">
        <div className="mb-7 flex items-center gap-3 px-2">
          <img src={brandLogo} alt="Checkout Queue logo" className="h-10 w-24 rounded-lg bg-white p-1 object-contain" />
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
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium ${
                  isActive ? 'bg-white text-brand-red' : 'text-red-50 hover:bg-white/20 hover:text-white'
                }`
              }
            >
              <item.Icon size={18} />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 border-b border-brand-deep bg-brand-red px-4 py-3 text-white backdrop-blur">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <img src={brandLogo} alt="Checkout Queue logo" className="h-9 w-20 rounded-lg bg-white p-1 object-contain lg:hidden" />
              <div>
              <p className="text-sm text-red-100">Retail checkout operations</p>
              <h1 className="text-lg font-semibold">Admin workspace</h1>
              </div>
            </div>
            <NavLink
              to="/app/customer"
              className="rounded-lg border border-white/60 bg-white/10 px-3 py-2 text-sm font-medium text-white hover:bg-white/20"
            >
              Customer view
            </NavLink>
          </div>
          <nav className="mt-3 flex gap-2 overflow-x-auto lg:hidden">
            {navItems.map((item) => (
              <NavLink
                key={item.label}
                to={item.path}
                end={item.path === '/app/admin'}
                className={({ isActive }) =>
                  `flex shrink-0 items-center gap-2 rounded-lg border px-3 py-2 text-sm ${
                    isActive ? 'border-white bg-white text-brand-red' : 'border-white/40 bg-white/10 text-white'
                  }`
                }
              >
                <item.Icon size={16} />
                {item.label}
              </NavLink>
            ))}
          </nav>
        </header>
        <main className="mx-auto max-w-7xl px-4 py-6">
          <Routes>
            <Route index element={<AdminDashboard />} />
            <Route path="stores" element={<AdminStores />} />
            <Route path="sections" element={<AdminPlaceholder title="Sections" />} />
            <Route path="counters" element={<AdminPlaceholder title="Counters" />} />
            <Route path="staff" element={<AdminPlaceholder title="Staff" />} />
            <Route path="queue" element={<AdminPlaceholder title="Queue" />} />
            <Route path="calendar" element={<AdminPlaceholder title="Calendar" />} />
            <Route path="alerts" element={<AdminPlaceholder title="Alerts" />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

function AdminDashboard() {
  const queueRows = [
    ['Regular checkout', 'A104', '18 waiting', '82%'],
    ['Express checkout', 'E044', '7 waiting', '69%'],
    ['Returns desk', 'R012', '3 waiting', '41%'],
  ];

  return (
    <div className="space-y-6">
      <SectionHeader
        eyebrow="Live Store Dashboard"
        title="Store queue overview"
        action={
          <button type="button" className="inline-flex items-center gap-2 rounded-lg bg-brand-red px-4 py-2 text-sm font-medium text-white">
            <Plus size={16} />
            Create store
          </button>
        }
      />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricTile label="Active stores" value="4" tone="mint" />
        <MetricTile label="Waiting tokens" value="28" />
        <MetricTile label="Active counters" value="11" tone="amber" />
        <MetricTile label="Avg wait" value="14m" tone="rose" />
      </div>
      <section className="rounded-lg border border-line bg-white">
        <div className="border-b border-line p-4">
          <h3 className="font-semibold">Section throughput</h3>
        </div>
        <div className="divide-y divide-brand-soft">
          {queueRows.map(([section, token, waiting, utilization]) => (
            <div key={section} className="grid gap-3 p-4 sm:grid-cols-4">
              <div className="font-medium">{section}</div>
              <div className="text-charcoal">Serving {token}</div>
              <div className="text-charcoal">{waiting}</div>
              <div className="text-charcoal">{utilization} utilization</div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function AdminPlaceholder({ title }) {
  return (
    <section className="rounded-lg border border-dashed border-brand-soft bg-white p-6">
      <SectionHeader eyebrow="Admin module" title={title} />
      <p className="mt-4 max-w-2xl text-sm leading-6 text-charcoal">
        This workspace is reserved for the {title.toLowerCase()} management APIs as the backend slices are added.
      </p>
    </section>
  );
}

