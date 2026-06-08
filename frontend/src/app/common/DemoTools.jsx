import { Database, RefreshCw, Trash2, Wand2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import {
  cleanDemoMlTrainingData,
  getDemoMlTrainingDataStatus,
  seedDemoMlTrainingData,
} from "../../api/demoToolsApi.js";
import { getErrorMessage, showApiErrorToast } from "../../api/httpClient.js";
import { useAuthStore } from "../../store/authStore.js";

function DemoMetric({ label, value }) {
  return (
    <div className="rounded-lg border border-line p-3">
      <p className="text-xs font-medium uppercase text-muted">{label}</p>
      <p
        className="mt-1 truncate text-lg font-semibold text-ink"
        title={String(value)}
      >
        {value}
      </p>
    </div>
  );
}

const DemoTools = () => {
  const [demoStatus, setDemoStatus] = useState(null);
  const [demoMessage, setDemoMessage] = useState("");
  const [demoLoading, setDemoLoading] = useState(false);
  const { user } = useAuthStore();
  const canManageDemoTools = user?.default_role === "SUPER_ADMIN";

  const loadDemoStatus = useCallback(async () => {
    if (!canManageDemoTools) return;
    setDemoLoading(true);
    setDemoMessage("");
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

  async function runDemoAction(action, successMessage) {
    setDemoLoading(true);
    setDemoMessage("");
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
    if (!message) return "";
    if (message.toLowerCase().includes("not found")) {
      return "Demo Tools API is not enabled on the backend. Set ENABLE_DEMO_TOOLS=True in backend/.env and restart FastAPI.";
    }
    return message;
  }

  return (
      <section className="rounded-lg border border-line bg-white p-4 shadow-soft sm:p-5">
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
          Creates or removes the isolated `DEMO-ML-STORE` dataset used for
          checkout and trial ML training tests.
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
      <DemoMetric
        label="Store"
        value={demoStatus?.exists ? demoStatus.store_number : "Not present"}
      />
      <DemoMetric
        label="Checkout completed"
        value={demoStatus?.counts?.checkout_completed_tokens ?? "-"}
      />
      <DemoMetric
        label="Checkout waiting"
        value={demoStatus?.counts?.checkout_waiting_tokens ?? "-"}
      />
      <DemoMetric
        label="Trial completed"
        value={demoStatus?.counts?.trial_completed_tokens ?? "-"}
      />
      <DemoMetric
        label="Trial waiting"
        value={demoStatus?.counts?.trial_waiting_tokens ?? "-"}
      />
      <DemoMetric
        label="ML metadata"
        value={demoStatus?.counts?.ml_metadata_rows ?? "-"}
      />
    </div>

    {demoStatus?.ids?.store_id ? (
      <div className="mt-4 rounded-lg bg-brand-blush px-3 py-2 text-sm text-charcoal">
        Demo store ID:{" "}
        <span className="font-semibold">{demoStatus.ids.store_id}</span>
      </div>
    ) : null}

    {demoMessage ? (
      <p className="mt-4 rounded-lg bg-brand-blush px-3 py-2 text-sm text-charcoal">
        {getDemoToolsMessage(demoMessage)}
      </p>
    ) : null}

    <div className="mt-4 flex flex-wrap gap-2">
      <button
        type="button"
        onClick={() =>
          runDemoAction(
            () => seedDemoMlTrainingData({ replace: false }),
            "Demo ML training data created.",
          )
        }
        disabled={demoLoading}
        className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-red px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60"
      >
        <Wand2 size={16} />
        Create demo data
      </button>
      <button
        type="button"
        onClick={() =>
          runDemoAction(
            () => seedDemoMlTrainingData({ replace: true }),
            "Demo ML training data recreated.",
          )
        }
        disabled={demoLoading}
        className="inline-flex items-center justify-center gap-2 rounded-lg border border-line px-4 py-2.5 text-sm font-medium text-charcoal disabled:opacity-60"
      >
        <RefreshCw size={16} />
        Recreate
      </button>
      <button
        type="button"
        onClick={() => {
          if (
            window.confirm(
              "Remove the demo ML training store and related demo artifacts?",
            )
          ) {
            runDemoAction(
              cleanDemoMlTrainingData,
              "Demo ML training data removed.",
            );
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
  )


};

export default DemoTools;
