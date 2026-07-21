import { create } from 'zustand';

// Map backend OfficerRole enum values → frontend UI role keys
// Backend: admin, inspector, station_head, constable
// Frontend: admin, io, sho, io (constable treated as io)
const BACKEND_TO_UI_ROLE = {
  admin: 'admin',
  station_head: 'sho',
  inspector: 'io',
  constable: 'io',
};

/**
 * Normalize an officer object from the backend:
 * - Maps backend role string to UI role key (admin/sho/io)
 * - Returns the officer as-is if role is already a UI key
 */
function normalizeOfficer(officer) {
  if (!officer) return null;
  const uiRole = BACKEND_TO_UI_ROLE[officer.role] ?? officer.role;
  return { ...officer, role: uiRole };
}

// Restore user from localStorage if available (needed for demo mock users)
const getSavedUser = () => {
  try {
    const raw = localStorage.getItem('crimegpt_user');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

const useAuthStore = create((set) => ({
  user: getSavedUser(),
  token: localStorage.getItem('token') || null,
  isAuthenticated: !!localStorage.getItem('token'),

  setAuth: (rawUser, token) => {
    const user = normalizeOfficer(rawUser);
    localStorage.setItem('token', token);
    localStorage.setItem('crimegpt_user', JSON.stringify(user));
    set({ user, token, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('crimegpt_user');
    set({ user: null, token: null, isAuthenticated: false });
  },
}));

export default useAuthStore;
