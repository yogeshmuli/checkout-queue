function readBooleanFlag(value, defaultValue) {
  if (value === undefined) return defaultValue;
  return !['false', '0', 'off', 'no'].includes(String(value).toLowerCase());
}

export const moduleFlags = {
  checkout: readBooleanFlag(import.meta.env.VITE_ENABLE_CHECKOUT_QUEUE, true),
  trial: readBooleanFlag(import.meta.env.VITE_ENABLE_TRIAL_QUEUE, true),
};

export const enabledModules = [
  moduleFlags.checkout ? { id: 'checkout', label: 'Queueless Transaction', description: 'Billing counters, customer tokens, and checkout operations.' } : null,
  moduleFlags.trial ? { id: 'trial', label: 'Quick Trial', description: 'Trial zones, studios, and fitting-room style token flow.' } : null,
].filter(Boolean);

export function getEnabledModulesForUser(user) {
  if (user?.assigned_zone_id) {
    return enabledModules.filter((module) => module.id === 'trial');
  }
  if (user?.assigned_counter_id || user?.section_id) {
    return enabledModules.filter((module) => module.id === 'checkout');
  }
  if (user?.default_role === 'TRIAL_ZONE_ASSISTANT') {
    return enabledModules.filter((module) => module.id === 'trial');
  }
  if (user?.default_role === 'CASHIER') {
    return enabledModules.filter((module) => module.id === 'checkout');
  }
  return enabledModules;
}

export function getAssignedModuleId(user) {
  if (user?.assigned_zone_id) return 'trial';
  if (user?.assigned_counter_id || user?.section_id) return 'checkout';
  if (user?.default_role === 'TRIAL_ZONE_ASSISTANT') return 'trial';
  if (user?.default_role === 'CASHIER') return 'checkout';
  return null;
}

export function getDefaultModule() {
  return enabledModules[0]?.id || 'checkout';
}

export function getModuleLoginPath(moduleId) {
  if (moduleId === 'trial') return '/app/trial/login';
  if (moduleId === 'checkout') return '/app/checkout/login';
  return '/app/login';
}

export function getModuleHomePath(moduleId, role = 'admin') {
  if (moduleId === 'checkout') {
    if (role === 'staff') return '/app/checkout/staff';
    if (role === 'customer') return '/app/checkout/customer';
    return '/app/checkout/admin';
  }
  return `/app/${moduleId}/${role}`;
}
