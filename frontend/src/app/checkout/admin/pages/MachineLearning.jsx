import { BrainCircuit, Download, RefreshCw, Upload, Wand2 } from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { getErrorMessage, showApiErrorToast } from '../../../../api/httpClient.js';
import { downloadStoreTrainingTemplate, getStoreModelMetadata, trainStoreModel, trainStoreModelFromUpload } from '../../../../api/checkout/mlApi.js';
import { listStores } from '../../../../api/checkout/storeApi.js';
import { Select } from '../../../common/FormAndStatePrimitives.jsx';
import { SectionHeader } from '../../../common/SectionHeader.jsx';

export function MachineLearning() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [stores, setStores] = useState([]);
  const [metadata, setMetadata] = useState(null);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [storesLoaded, setStoresLoaded] = useState(false);
  const [trainingFile, setTrainingFile] = useState(null);
  const [validationErrors, setValidationErrors] = useState([]);
  const storeId = searchParams.get('store_id') || '';

  const storeOptions = useMemo(
    () =>
      stores.length
        ? stores.map((store) => ({
        label: `${store.name} (${store.store_number})`,
        value: String(store.id),
      }))
        : [{ label: 'No stores found', value: '' }],
    [stores]
  );

  useEffect(() => {
    async function loadStores() {
      try {
        setStores(await listStores({ include_inactive: true }));
      } catch (error) {
        showApiErrorToast(error);
        setMessage(getErrorMessage(error));
      } finally {
        setStoresLoaded(true);
      }
    }

    loadStores();
  }, []);

  useEffect(() => {
    if (!stores.length) return;
    if (stores.some((store) => String(store.id) === String(storeId))) return;
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set('store_id', String(stores[0].id));
      return next;
    });
  }, [setSearchParams, storeId, stores]);

  const loadMetadata = useCallback(async () => {
    if (!storeId) return;
    setLoading(true);
    setMessage('');
    try {
      setMetadata(await getStoreModelMetadata(storeId));
    } catch (error) {
      setMetadata(null);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }, [storeId]);

  useEffect(() => {
    if (!storeId) {
      setMetadata(null);
      return;
    }

    loadMetadata();
  }, [loadMetadata, storeId]);

  function selectStore(value) {
    setTrainingFile(null);
    setValidationErrors([]);
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (value) {
        next.set('store_id', value);
      } else {
        next.delete('store_id');
      }
      return next;
    });
  }

  async function trainModel() {
    if (!storeId) {
      setMessage('Select a store before training.');
      return;
    }

    setLoading(true);
    setMessage('');
    try {
      setMetadata(await trainStoreModel(storeId));
      setMessage('Model trained from database records.');
    } catch (error) {
      showApiErrorToast(error);
      setMessage(getErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function downloadTemplate() {
    if (!storeId) return;
    setLoading(true);
    try {
      const blob = await downloadStoreTrainingTemplate(storeId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `checkout-store-${storeId}-ml-training.xlsx`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      showApiErrorToast(error);
    } finally { setLoading(false); }
  }

  async function uploadAndTrain() {
    if (!storeId || !trainingFile) return;
    setLoading(true); setMessage(''); setValidationErrors([]);
    try {
      setMetadata(await trainStoreModelFromUpload(storeId, trainingFile));
      setMessage('Uploaded model trained and activated for this store.');
      setTrainingFile(null);
    } catch (error) {
      const errors = error?.detail?.errors;
      setValidationErrors(Array.isArray(errors) ? errors : []);
      setMessage(getErrorMessage(error));
    } finally { setLoading(false); }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[2fr_1fr]">
      <section className="rounded-lg border border-line bg-white p-5">
        <SectionHeader eyebrow="Intelligence hub" title="Service-time prediction" />
        <div className="mt-5 grid gap-3 md:grid-cols-[1fr_auto_auto_auto] md:items-end">
          <Select label="Store" value={storeId} options={storeOptions} onChange={selectStore} disabled={!stores.length} />
          <button
            type="button"
            onClick={trainModel}
            disabled={loading || !storeId}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-red px-4 py-3 text-sm font-semibold text-white disabled:opacity-60"
          >
            <Wand2 size={17} />
            Train from database
          </button>
          <button type="button" onClick={downloadTemplate} disabled={loading || !storeId} className="inline-flex items-center justify-center gap-2 rounded-lg border border-line px-4 py-3 text-sm font-medium text-charcoal disabled:opacity-60">
            <Download size={17} /> Excel template
          </button>
          <button
            type="button"
            onClick={loadMetadata}
            disabled={loading || !storeId}
            className="inline-flex items-center justify-center gap-2 rounded-lg border border-line px-4 py-3 text-sm font-medium text-charcoal disabled:opacity-60"
          >
            <RefreshCw size={17} />
            Refresh
          </button>
        </div>

        <div className="mt-5 rounded-lg border border-line bg-slate-50 p-4">
          <p className="text-sm font-semibold text-ink">Train from a specific Excel dataset</p>
          <p className="mt-1 text-sm text-muted">The uploaded rows train and activate a new model only for the selected store.</p>
          <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center">
            <input type="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" onChange={(event) => { setTrainingFile(event.target.files?.[0] || null); setValidationErrors([]); }} disabled={loading || !storeId} className="block w-full text-sm text-charcoal file:mr-3 file:rounded-lg file:border-0 file:bg-white file:px-3 file:py-2 file:font-medium" />
            <button type="button" onClick={uploadAndTrain} disabled={loading || !storeId || !trainingFile} className="inline-flex shrink-0 items-center justify-center gap-2 rounded-lg bg-brand-red px-4 py-3 text-sm font-semibold text-white disabled:opacity-60"><Upload size={17} /> Upload and train</button>
          </div>
          {trainingFile ? <p className="mt-2 text-xs text-muted">Selected: {trainingFile.name}</p> : null}
          {validationErrors.length ? <ul className="mt-3 max-h-48 overflow-auto rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">{validationErrors.map((error, index) => <li key={`${error.row}-${error.column}-${index}`}>Row {error.row ?? '-'}, {error.column || 'workbook'}: {error.message}</li>)}</ul> : null}
        </div>

        {message ? <p className="mt-4 rounded-lg bg-brand-blush px-3 py-2 text-sm text-charcoal">{message}</p> : null}
        {storesLoaded && !stores.length ? (
          <p className="mt-5 rounded-lg border border-dashed border-line p-4 text-sm text-muted">Create a store first, then ML training and metadata will appear here.</p>
        ) : null}

        {stores.length ? (
        <>
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Metric label="Status" value={metadata?.status || 'Not trained'} />
          <Metric label="Samples" value={metadata?.sample_size ?? '-'} />
          <Metric label="MAE" value={metadata?.mae != null ? metadata.mae.toFixed(2) : '-'} />
          <Metric label="R2" value={metadata?.r2_score != null ? metadata.r2_score.toFixed(2) : '-'} />
        </div>

        {metadata ? (
          <div className="mt-5 rounded-lg border border-line p-4">
            <div className="flex items-center gap-2">
              <BrainCircuit size={19} className="text-brand-red" />
              <h3 className="font-semibold">Latest model</h3>
            </div>
            <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
              <MetadataItem label="Type" value={metadata.model_type} />
              <MetadataItem label="Version" value={metadata.model_version} />
              <MetadataItem label="Accuracy" value={metadata.accuracy_score != null ? `${Math.round(metadata.accuracy_score * 100)}%` : '-'} />
              <MetadataItem label="Data quality" value={metadata.data_quality_score != null ? `${Math.round(metadata.data_quality_score * 100)}%` : '-'} />
              <MetadataItem label="Training source" value={metadata.training_source === 'EXCEL_UPLOAD' ? 'Excel upload' : 'Database'} />
              <MetadataItem label="Source file" value={metadata.original_filename} />
              <MetadataItem label="Uploaded by user" value={metadata.uploaded_by_user_id ? `User ${metadata.uploaded_by_user_id}` : '-'} />
              <MetadataItem label="Trained at" value={metadata.trained_at ? new Date(metadata.trained_at).toLocaleString() : '-'} />
            </dl>
          </div>
        ) : null}
        </>
        ) : null}
      </section>

      {stores.length ? (
      <section className="rounded-lg border border-line bg-white p-5">
        <SectionHeader eyebrow="Fallback" title="Queue behavior" />
        <p className="mt-4 text-sm leading-6 text-charcoal">
          Queue estimates use ML only when a trained model is ready for the selected store. Otherwise, token creation falls back to the store rule-based service-time configuration.
        </p>
      </section>
      ) : null}
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded-lg border border-line p-4">
      <p className="text-xs font-medium uppercase text-muted">{label}</p>
      <p className="mt-1 text-xl font-semibold text-ink">{value}</p>
    </div>
  );
}

function MetadataItem({ label, value }) {
  return (
    <div>
      <dt className="text-muted">{label}</dt>
      <dd className="mt-1 font-medium text-charcoal">{value || '-'}</dd>
    </div>
  );
}
