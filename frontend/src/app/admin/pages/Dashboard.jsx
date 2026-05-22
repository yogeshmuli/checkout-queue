import { Plus } from 'lucide-react';

import { MetricTile } from '../../common/MetricTile.jsx';
import { SectionHeader } from '../../common/SectionHeader.jsx';

export function Dashboard() {
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
        <MetricTile label="Active stores" value="4"  />
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
