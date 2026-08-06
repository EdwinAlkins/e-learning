import { create } from 'zustand';
import { getUID, setUID as setUIDStorage, clearUID as clearUIDStorage } from '../services/auth';

interface AuthState {
  uid: string | null;
  isAuthenticated: boolean;
  setUID: (uid: string) => void;
  clearUID: () => void;
  checkAuth: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  uid: null,
  isAuthenticated: false,
  setUID: (uid: string) => {
    setUIDStorage(uid);
    set({ uid, isAuthenticated: true });
  },
  clearUID: () => {
    clearUIDStorage();
    set({ uid: null, isAuthenticated: false });
  },
  checkAuth: () => {
    const uid = getUID();
    set({ uid, isAuthenticated: uid !== null });
  },
}));
