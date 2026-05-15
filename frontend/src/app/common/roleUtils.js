const STAFF_ROLES = new Set(['CASHIER']);

export function getUserScope(user) {
  if (!user) return 'guest';
  return STAFF_ROLES.has(user.default_role) ? 'staff' : 'admin';
}
