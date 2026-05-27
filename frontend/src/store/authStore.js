import { create } from 'zustand';

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
  
  setAuth: (user, token) => {
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
