import { create } from 'zustand';

export const useQueueStore = create((set) => ({
  lastToken: null,
  activeCounterId: "",
  setLastToken: (token) => set({ lastToken: token }),
  setActiveCounterId: (counterId) => set({ activeCounterId: counterId }),
}));
