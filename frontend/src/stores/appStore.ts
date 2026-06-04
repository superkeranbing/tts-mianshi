import { create } from "zustand";

interface AppState {
  user: { id: string; username: string } | null;
  token: string;
  setAuth: (user: { id: string; username: string }, token: string) => void;
  logout: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  user: null,
  token: "",
  setAuth: (user, token) => set({ user, token }),
  logout: () => set({ user: null, token: "" }),
}));
