import { create } from 'zustand';

export const useQueueStore = create((set) => ({
  lastToken: null,
  activeCounterId: '1',
  setLastToken: (token) => set({ lastToken: token }),
  setActiveCounterId: (counterId) => set({ activeCounterId: counterId }),
}));
