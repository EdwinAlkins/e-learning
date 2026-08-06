import { create } from 'zustand';
import type { Formation } from '../types';
import { apiService } from '../services/api';

interface CatalogState {
  formations: Formation[];
  loading: boolean;
  error: string | null;
  /** @param force recharge même si déjà chargé ; @param silent ne bascule pas `loading` (évite les flashs UI). */
  fetchFormations: (force?: boolean, silent?: boolean) => Promise<void>;
  upsertFormation: (formation: Formation) => void;
  removeFormation: (formationId: string) => void;
  reset: () => void;
}

/** Ignore les réponses obsolètes si plusieurs fetchs se chevauchent. */
let fetchGeneration = 0;

export const useCatalogStore = create<CatalogState>((set, get) => ({
  formations: [],
  loading: false,
  error: null,
  fetchFormations: async (force = false, silent = false) => {
    const { formations, loading } = get();

    if (formations.length > 0 && !force) return;
    if (loading && !silent) return;

    const generation = ++fetchGeneration;

    if (!silent) {
      set({ loading: true, error: null });
    }
    try {
      const fetched = await apiService.getFormations();
      if (generation !== fetchGeneration) return;
      set({ formations: fetched, loading: false, error: null });
    } catch (error) {
      if (generation !== fetchGeneration) return;
      console.error('Error fetching formations:', error);
      if (silent) {
        // Ne pas vider le catalogue pendant un poll : garder l'état affiché.
        set({ loading: false });
        return;
      }
      set({
        formations: [],
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to load formations',
      });
    }
  },
  upsertFormation: (formation) => {
    const { formations } = get();
    const index = formations.findIndex((item) => item.id === formation.id);
    if (index === -1) {
      set({ formations: [...formations, formation] });
      return;
    }
    const next = [...formations];
    next[index] = formation;
    set({ formations: next });
  },

  removeFormation: (formationId) => {
    set({
      formations: get().formations.filter((formation) => formation.id !== formationId),
    });
  },

  reset: () => {
    set({ formations: [], loading: false, error: null });
  },
}));
