const STAFF_ROLES = new Set(['CASHIER', 'TRIAL_ZONE_ASSISTANT']);

export function getUserScope(user) {
  if (!user) return 'guest';
  return STAFF_ROLES.has(user.default_role) ? 'staff' : 'admin';
}
