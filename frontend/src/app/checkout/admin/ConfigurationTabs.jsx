import { NavLink, useLocation } from 'react-router-dom';

import { configurationPaths } from './configurationNavigation.js';

const tabs = [
  { label: 'Stores', path: configurationPaths[0], preserveStoreId: false },
  { label: 'Store Config', path: configurationPaths[1], preserveStoreId: true },
  { label: 'Sections', path: configurationPaths[2], preserveStoreId: true },
  { label: 'Counters', path: configurationPaths[3], preserveStoreId: true },
  { label: 'Staff', path: configurationPaths[4], preserveStoreId: true },
  { label: 'Calendar', path: configurationPaths[5], preserveStoreId: true },
];

function isConfigurationPath(pathname) {
  return configurationPaths.includes(pathname);
}

export function ConfigurationTabs() {
  const location = useLocation();
  const storeId = new URLSearchParams(location.search).get('store_id');

  if (!isConfigurationPath(location.pathname)) return null;

  return (
    <nav className="mb-6 overflow-x-auto rounded-lg border border-line bg-white" aria-label="Checkout configuration">
      <div className="flex min-w-max px-2">
        {tabs.map((tab) => {
          const to = tab.preserveStoreId && storeId ? `${tab.path}?store_id=${encodeURIComponent(storeId)}` : tab.path;

          return (
            <NavLink
              key={tab.path}
              to={to}
              className={({ isActive }) =>
                `whitespace-nowrap border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
                  isActive ? 'border-brand-red text-brand-red' : 'border-transparent text-charcoal hover:text-brand-red'
                }`
              }
            >
              {tab.label}
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
}
