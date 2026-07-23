import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import LexBot from './components/LexBot';
import FIRAutomator from './components/FIRAutomator';
import Dashboard from './components/Dashboard';
import Vault from './components/Vault';
import CaseLinkage from './components/CaseLinkage';
import DocumentGenerator from './components/DocumentGenerator';
import CaseDiary from './components/CaseDiary';
import Login from './components/Login';
import UserSettings from './components/UserSettings';
import LERSPortal from './components/LERSPortal';
import { motion, AnimatePresence } from 'framer-motion';
import useAuthStore from './store/authStore';
import { authService } from './services/api';
import { Toaster } from 'react-hot-toast';


// RBAC — must match Sidebar.jsx roles config
const TAB_ROLES = {
  dashboard: ['io', 'sho', 'admin'],
  fir:       ['io', 'sho', 'admin'],
  lexbot:    ['io', 'sho', 'admin'],
  vault:     ['io', 'sho', 'admin'],
  linkage:   ['sho', 'admin'],
  documents: ['io', 'sho', 'admin'],
  diary:     ['io', 'sho', 'admin'],
  lers:      ['io', 'sho', 'admin'],
};

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [settingsOpen, setSettingsOpen] = useState(false);
  const { isAuthenticated, user, token, setAuth, logout } = useAuthStore();

  useEffect(() => {
    // ONE-TIME HARD RESET FOR USER (V3)
    const hasCleared = localStorage.getItem('crimegpt_global_wipe_v3');
    if (!hasCleared) {
      localStorage.clear();
      localStorage.setItem('crimegpt_global_wipe_v3', 'true');
      window.location.reload();
    }
  }, []);

  useEffect(() => {
    const checkAuth = async () => {
      if (isAuthenticated && !user) {
        // Skip API call for demo mock tokens — they don't have real backend sessions
        const isDemoToken = token?.startsWith('demo-');
        if (isDemoToken) return;

        try {
          const response = await authService.me();
          if (response.success) {
            setAuth(response.data, localStorage.getItem('token'));
          }
        } catch {
          logout();
        }
      }
    };
    checkAuth();
  }, [isAuthenticated, user, token, logout, setAuth]);

  if (!isAuthenticated) {
    return <Login />;
  }

  // RBAC route guard — resolve the effective tab (avoids setState in useEffect)
  const role = user?.role || 'io';
  const allowedRoles = TAB_ROLES[activeTab];
  const effectiveTab = (allowedRoles && !allowedRoles.includes(role)) ? 'dashboard' : activeTab;

  return (
    <div className="flex bg-background text-foreground min-h-screen">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} onSettingsClick={() => setSettingsOpen(true)} />
      <UserSettings isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
      <Toaster 
        position="top-right"
        toastOptions={{
          style: {
            background: 'var(--color-background)',
            color: 'var(--color-foreground)',
            border: '1px solid var(--color-border)',
            borderRadius: '0px',
            fontSize: '12px',
            fontFamily: 'var(--font-mono)',
          },
          success: {
            iconTheme: {
              primary: '#22C55E',
              secondary: '#FFFFFF',
            },
          },
        }}
      />
      
      <main className="flex-1 h-screen flex flex-col overflow-hidden">
        {/* Header - Minimalist */}
        <header className="h-20 border-b border-border flex items-center justify-between px-12 bg-background/80 backdrop-blur-md z-30 shrink-0">
          <div className="flex items-center gap-4">
            <div className="w-2 h-2 bg-accent" />
            <h2 className="label-mono text-sm tracking-[0.3em] font-bold">
              {activeTab}
            </h2>
          </div>
          <div className="flex items-center gap-8">
            <div className="text-right hidden sm:block">
              <p className="label-mono text-[10px]">Active Officer</p>
              <p className="font-bold uppercase tracking-tighter text-lg">{user?.name || 'Loading...'}</p>
            </div>
            <div 
              onClick={logout}
              className="h-10 w-10 border-2 border-foreground flex items-center justify-center font-black text-sm hover:bg-accent hover:border-accent hover:text-background transition-all cursor-pointer"
            >
              {user?.name?.split(' ').map(n => n[0]).join('') || '??'}
            </div>
          </div>
        </header>

        <AnimatePresence mode="wait">
          <motion.div
            key={effectiveTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3, ease: [0.25, 0, 0, 1] }}
            className="flex-1 overflow-y-auto relative custom-scrollbar"
          >
            {effectiveTab === 'dashboard' && <Dashboard />}
            {effectiveTab === 'fir' && <FIRAutomator />}
            {effectiveTab === 'lexbot' && <LexBot />}
            {effectiveTab === 'vault' && <Vault />}
            {effectiveTab === 'linkage' && <CaseLinkage />}
            {effectiveTab === 'documents' && <DocumentGenerator />}
            {effectiveTab === 'diary' && <CaseDiary />}
            {effectiveTab === 'lers' && <LERSPortal />}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}

