import { SectionHeader } from '../../../common/SectionHeader.jsx';

export function AdminModulePlaceholder({ title }) {
  return (
    <section className="rounded-lg border border-dashed border-brand-soft bg-white p-6">
      <SectionHeader eyebrow="Admin module" title={title} />
      <p className="mt-4 max-w-2xl text-sm leading-6 text-charcoal">
        This workspace is reserved for the {title.toLowerCase()} management APIs as the backend slices are added.
      </p>
    </section>
  );
}
