import { create } from 'zustand';

const STORAGE_KEY = 'crimegpt_local_firs';
const COUNTER_KEY = 'crimegpt_fir_counter';

const loadFromStorage = () => {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); }
  catch { return []; }
};

const getNextCounter = () => {
  const current = parseInt(localStorage.getItem(COUNTER_KEY) || '0', 10);
  const next = current + 1;
  localStorage.setItem(COUNTER_KEY, String(next));
  return next;
};

const useFirStore = create((set, get) => ({
  localFirs: loadFromStorage(),

  getNextFirNumber: () => {
    const n = getNextCounter();
    return `FIR-${String(n).padStart(5, '0')}`;
  },

  addFir: (fir) => {
    const existing = get().localFirs;
    const updated = [fir, ...existing].slice(0, 50);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    set({ localFirs: updated });
  },

  deleteFir: (id) => {
    const updated = get().localFirs.filter(f => f.id !== id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    set({ localFirs: updated });
  },

  clearAll: () => {
    localStorage.removeItem(STORAGE_KEY);
    localStorage.setItem(COUNTER_KEY, '0');
    set({ localFirs: [] });
  },
}));

export default useFirStore;
