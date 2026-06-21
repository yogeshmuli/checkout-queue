import { ArrowRight, Boxes, ShoppingBag } from 'lucide-react';

import { Navigate, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore.js';
import { showApiErrorToast } from '../../api/httpClient.js';


import brandLogo from '../../assets/images/equilateral_logo.png';

import { getEnabledModulesForUser, getModuleHomePath } from './moduleConfig.js';
import { getUserScope } from './roleUtils.js';
import DemoTools from './DemoTools.jsx';

const moduleIcons = {
  checkout: ShoppingBag,
  trial: Boxes,
};

export function ContextSelector() {
  const navigate = useNavigate();
  const { user } = useAuthStore();


  const scope = getUserScope(user);
  const modules = getEnabledModulesForUser(user);
  
const canManageDemoTools = user?.default_role === 'SUPER_ADMIN';
  

  if (!user) return <Navigate to="/app/login" replace />;

  if (modules.length === 1) {
    return <Navigate to={getModuleHomePath(modules[0].id, scope)} replace />;
  }

 

  function onClickModule(module) {

    let enabledModules = getEnabledModulesForUser(user);
    if (!enabledModules.find((m) => m.id === module.id)) {
      showApiErrorToast(new Error('You do not have access to this module.'));
      return;
    }

    navigate(getModuleHomePath(module.id, scope));
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

        <div className="grid gap-4 md:grid-cols-2 mb-5">
          {modules.map((module) => {
            const Icon = moduleIcons[module.id] || ShoppingBag;
            return (
              <button
                key={module.id}
                type="button"
                onClick={() => onClickModule(module)}
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

        {canManageDemoTools ? (
        <DemoTools />
        ) : null}
      </section>
    </main>
  );
}

