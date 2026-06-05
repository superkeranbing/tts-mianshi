import { create } from "zustand";

function loadStoredAuth() {
  try {
    const token = localStorage.getItem("auth_token");
    const userStr = localStorage.getItem("auth_user");
    if (token && userStr) {
      return { token, user: JSON.parse(userStr) };
    }
  } catch {}
  return null;
}

interface AppState {
  user: { id: string; username: string } | null;
  token: string;
  setAuth: (user: { id: string; username: string }, token: string) => void;
  logout: () => void;
}

const stored = loadStoredAuth();

export const useAppStore = create<AppState>((set) => ({
  user: stored?.user ?? null,
  token: stored?.token ?? "",
  setAuth: (user, token) => {
    localStorage.setItem("auth_token", token);
    localStorage.setItem("auth_user", JSON.stringify(user));
    set({ user, token });
  },
  logout: () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_user");
    set({ user: null, token: "" });
  },
}));