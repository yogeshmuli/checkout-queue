export const moduleFlags = {
  checkout: import.meta.env.VITE_ENABLE_CHECKOUT_QUEUE || true,
  trial: import.meta.env.VITE_ENABLE_TRIAL_QUEUE || true,
};

export const enabledModules = [
  moduleFlags.checkout ? { id: 'checkout', label: 'Checkout Queue', description: 'Billing counters, customer tokens, and checkout operations.' } : null,
  moduleFlags.trial ? { id: 'trial', label: 'Trial Queue', description: 'Trial zones, studios, and fitting-room style token flow.' } : null,
].filter(Boolean);

export function getDefaultModule() {
  return enabledModules[0]?.id || 'checkout';
}

export function getModuleHomePath(moduleId, role = 'admin') {
  if (moduleId === 'checkout') {
    if (role === 'staff') return '/app/checkout/staff';
    if (role === 'customer') return '/app/checkout/customer';
    return '/app/checkout/admin';
  }
  return `/app/${moduleId}/${role}`;
}
