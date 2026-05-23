import { ArrowRight, Boxes, ShoppingBag } from 'lucide-react';
import { Navigate, useNavigate } from 'react-router-dom';

import brandLogo from '../../assets/images/equilateral_logo.png';
import { useAuthStore } from '../../store/authStore.js';
import { getEnabledModulesForUser, getModuleHomePath } from './moduleConfig.js';
import { getUserScope } from './roleUtils.js';

const moduleIcons = {
  checkout: ShoppingBag,
  trial: Boxes,
};

export function ContextSelector() {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  if (!user) return <Navigate to="/app/login" replace />;

  const scope = getUserScope(user);
  const modules = getEnabledModulesForUser(user);
  if (modules.length === 1) {
    return <Navigate to={getModuleHomePath(modules[0].id, scope)} replace />;
  }

  return (
    <main className="min-h-screen bg-brand-blush px-4 py-6 text-ink">
      <section className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center">
        <header className="mb-5 flex items-center gap-3">
          <img src={brandLogo} alt="Queue logo" className="h-11 w-28 rounded-lg bg-white p-1 object-cover" />
          <div>
            <p className="text-sm text-muted">Choose workspace</p>
            <h1 className="text-2xl font-semibold">Select product context</h1>
          </div>
        </header>

        <div className="grid gap-4 md:grid-cols-2">
          {modules.map((module) => {
            const Icon = moduleIcons[module.id] || ShoppingBag;
            return (
              <button
                key={module.id}
                type="button"
                onClick={() => navigate(getModuleHomePath(module.id, scope))}
                className="rounded-lg border border-line bg-white p-5 text-left shadow-soft transition hover:border-brand-red"
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-brand-blush text-brand-red">
                    <Icon size={22} />
                  </span>
                  <ArrowRight size={18} className="text-brand-red" />
                </div>
                <h2 className="mt-4 text-xl font-semibold">{module.label}</h2>
                <p className="mt-2 text-sm text-muted">{module.description}</p>
              </button>
            );
          })}
        </div>
      </section>
    </main>
  );
}
