import { ArrowRight, Boxes, Database, RefreshCw, ShoppingBag, Trash2, Wand2 } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';

import { cleanDemoMlTrainingData, getDemoMlTrainingDataStatus, seedDemoMlTrainingData } from '../../api/demoToolsApi.js';
import { getErrorMessage, showApiErrorToast } from '../../api/httpClient.js';
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
  const [demoStatus, setDemoStatus] = useState(null);
  const [demoMessage, setDemoMessage] = useState('');
  const [demoLoading, setDemoLoading] = useState(false);

  const scope = getUserScope(user);
  const modules = getEnabledModulesForUser(user);
  const canManageDemoTools = user?.default_role === 'SUPER_ADMIN';

  const loadDemoStatus = useCallback(async () => {
    if (!canManageDemoTools) return;
    setDemoLoading(true);
    setDemoMessage('');
    try {
      setDemoStatus(await getDemoMlTrainingDataStatus());
    } catch (error) {
      setDemoStatus(null);
      setDemoMessage(getErrorMessage(error));
    } finally {
      setDemoLoading(false);
    }
  }, [canManageDemoTools]);

  useEffect(() => {
    loadDemoStatus();
  }, [loadDemoStatus]);

  if (!user) return <Navigate to="/app/login" replace />;

  if (modules.length === 1 && !canManageDemoTools) {
    return <Navigate to={getModuleHomePath(modules[0].id, scope)} replace />;
  }

  async function runDemoAction(action, successMessage) {
    setDemoLoading(true);
    setDemoMessage('');
    try {
      const result = await action();
      setDemoStatus(result);
      setDemoMessage(successMessage);
    } catch (error) {
      showApiErrorToast(error);
      setDemoMessage(getErrorMessage(error));
    } finally {
      setDemoLoading(false);
    }
  }

  function getDemoToolsMessage(message) {
    if (!message) return '';
    if (message.toLowerCase().includes('not found')) {
      return 'Demo Tools API is not enabled on the backend. Set ENABLE_DEMO_TOOLS=True in backend/.env and restart FastAPI.';
    }
    return message;
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

        <div className="grid gap-4 md:grid-cols-2">
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
          <section className="mt-5 rounded-lg border border-line bg-white p-5 shadow-soft">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-blush text-brand-red">
                    <Database size={20} />
                  </span>
                  <div>
                    <p className="text-sm text-muted">Super admin tools</p>
                    <h2 className="text-xl font-semibold">Demo ML training data</h2>
                  </div>
                </div>
                <p className="mt-3 text-sm text-charcoal">
                  Creates or removes the isolated `DEMO-ML-STORE` dataset used for checkout and trial ML training tests.
                </p>
              </div>
              <button
                type="button"
                onClick={loadDemoStatus}
                disabled={demoLoading}
                className="inline-flex items-center justify-center gap-2 rounded-lg border border-line px-3 py-2 text-sm font-medium text-charcoal disabled:opacity-60"
              >
                <RefreshCw size={16} />
                Refresh
              </button>
            </div>

            <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              <DemoMetric label="Store" value={demoStatus?.exists ? demoStatus.store_number : 'Not present'} />
              <DemoMetric label="Checkout completed" value={demoStatus?.counts?.checkout_completed_tokens ?? '-'} />
              <DemoMetric label="Checkout waiting" value={demoStatus?.counts?.checkout_waiting_tokens ?? '-'} />
              <DemoMetric label="Trial completed" value={demoStatus?.counts?.trial_completed_tokens ?? '-'} />
              <DemoMetric label="Trial waiting" value={demoStatus?.counts?.trial_waiting_tokens ?? '-'} />
              <DemoMetric label="ML metadata" value={demoStatus?.counts?.ml_metadata_rows ?? '-'} />
            </div>

            {demoStatus?.ids?.store_id ? (
              <div className="mt-4 rounded-lg bg-brand-blush px-3 py-2 text-sm text-charcoal">
                Demo store ID: <span className="font-semibold">{demoStatus.ids.store_id}</span>
              </div>
            ) : null}

            {demoMessage ? <p className="mt-4 rounded-lg bg-brand-blush px-3 py-2 text-sm text-charcoal">{getDemoToolsMessage(demoMessage)}</p> : null}

            <div className="mt-4 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => runDemoAction(() => seedDemoMlTrainingData({ replace: false }), 'Demo ML training data created.')}
                disabled={demoLoading}
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-red px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60"
              >
                <Wand2 size={16} />
                Create demo data
              </button>
              <button
                type="button"
                onClick={() => runDemoAction(() => seedDemoMlTrainingData({ replace: true }), 'Demo ML training data recreated.')}
                disabled={demoLoading}
                className="inline-flex items-center justify-center gap-2 rounded-lg border border-line px-4 py-2.5 text-sm font-medium text-charcoal disabled:opacity-60"
              >
                <RefreshCw size={16} />
                Recreate
              </button>
              <button
                type="button"
                onClick={() => {
                  if (window.confirm('Remove the demo ML training store and related demo artifacts?')) {
                    runDemoAction(cleanDemoMlTrainingData, 'Demo ML training data removed.');
                  }
                }}
                disabled={demoLoading}
                className="inline-flex items-center justify-center gap-2 rounded-lg border border-rose-200 px-4 py-2.5 text-sm font-medium text-rose-700 disabled:opacity-60"
              >
                <Trash2 size={16} />
                Clean demo data
              </button>
            </div>
          </section>
        ) : null}
      </section>
    </main>
  );
}

function DemoMetric({ label, value }) {
  return (
    <div className="rounded-lg border border-line p-3">
      <p className="text-xs font-medium uppercase text-muted">{label}</p>
      <p className="mt-1 truncate text-lg font-semibold text-ink" title={String(value)}>
        {value}
      </p>
    </div>
  );
}
