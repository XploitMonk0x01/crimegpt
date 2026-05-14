import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import LexBot from './components/LexBot';
import FIRAutomator from './components/FIRAutomator';
import Dashboard from './components/Dashboard';
import Vault from './components/Vault';
import CaseLinkage from './components/CaseLinkage';
import Login from './components/Login';
import { motion, AnimatePresence } from 'framer-motion';
import useAuthStore from './store/authStore';
import { authService } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const { isAuthenticated, user, setAuth, logout } = useAuthStore();

  useEffect(() => {
    const checkAuth = async () => {
      if (isAuthenticated && !user) {
        try {
          const response = await authService.me();
          if (response.success) {
            setAuth(response.data, localStorage.getItem('token'));
          }
        } catch (err) {
          logout();
        }
      }
    };
    checkAuth();
  }, [isAuthenticated, user, logout, setAuth]);

  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <div className="flex bg-background text-foreground min-h-screen">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      
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
            key={activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3, ease: [0.25, 0, 0, 1] }}
            className="flex-1 overflow-y-auto relative custom-scrollbar"
          >
            {activeTab === 'dashboard' && <Dashboard />}
            {activeTab === 'fir' && <FIRAutomator />}
            {activeTab === 'lexbot' && <LexBot />}
            {activeTab === 'vault' && <Vault />}
            {activeTab === 'linkage' && <CaseLinkage />}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}
