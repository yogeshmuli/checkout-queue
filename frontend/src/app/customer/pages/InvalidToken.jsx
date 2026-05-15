import { EmptyStateCard } from '../../../app/common/FormAndStatePrimitives.jsx';

export function InvalidToken() {
  return (
    <main className="min-h-screen  px-4 py-5 ">
      <section className="mx-auto max-w-md">
        <EmptyStateCard
          message="Invalid or no token present in URL."
          ctaTo="/app/customer/create"
          ctaLabel="Go to create token"
        />
      </section>
    </main>
  );
}
