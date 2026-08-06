import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type ThemeMode = 'light' | 'dark' | 'system';

interface ThemeState {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
  getEffectiveMode: () => 'light' | 'dark';
}

// Helper function to detect system theme preference
const getSystemTheme = (): 'light' | 'dark' => {
  if (globalThis.window?.matchMedia) {
    return globalThis.window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  return 'light';
};

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      mode: 'system',
      setMode: (mode: ThemeMode) => {
        set({ mode });
      },
      getEffectiveMode: () => {
        const { mode } = get();
        if (mode === 'system') {
          return getSystemTheme();
        }
        return mode;
      },
    }),
    {
      name: 'theme-storage',
    }
  )
);
