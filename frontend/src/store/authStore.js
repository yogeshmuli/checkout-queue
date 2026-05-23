import { create } from 'zustand';

function getPreferredRole(user) {
  return ['CASHIER', 'TRIAL_ZONE_ASSISTANT'].includes(user?.default_role) ? 'staff' : 'admin';
}

export const useAuthStore = create((set) => ({
  accessToken: localStorage.getItem('checkout_queue_access_token') || '',
  refreshToken: localStorage.getItem('checkout_queue_refresh_token') || '',
  user: (() => {
    const raw = localStorage.getItem('checkout_queue_user');
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  })(),
  preferredRole: localStorage.getItem('checkout_queue_role') || 'customer',
  setSession: ({ user, tokens }) => {
    localStorage.setItem('checkout_queue_access_token', tokens.access_token);
    localStorage.setItem('checkout_queue_refresh_token', tokens.refresh_token);
    localStorage.setItem('checkout_queue_user', JSON.stringify(user || null));
    set({
      user,
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
      preferredRole: getPreferredRole(user),
    });
  },
  setUser: (user) => {
    localStorage.setItem('checkout_queue_user', JSON.stringify(user || null));
    set({ user, preferredRole: getPreferredRole(user) });
  },
  setPreferredRole: (role) => {
    localStorage.setItem('checkout_queue_role', role);
    set({ preferredRole: role });
  },
  clearSession: () => {
    localStorage.removeItem('checkout_queue_access_token');
    localStorage.removeItem('checkout_queue_refresh_token');
    localStorage.removeItem('checkout_queue_user');
    set({ accessToken: '', refreshToken: '', user: null });
  },
}));
