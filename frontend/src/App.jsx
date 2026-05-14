import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import LexBot from './components/LexBot';
import FIRAutomator from './components/FIRAutomator';
import Login from './components/Login';
import { motion, AnimatePresence } from 'framer-motion';
import { Database, Link2 } from 'lucide-react';
import useAuthStore from './store/authStore';
import { authService } from './services/api';

const Dashboard = () => (
  <div className="flex flex-col">
    {/* Hero Section */}
    <section className="px-6 py-6 border-b border-border">
      <p className="label-mono mb-1 text-accent/80">Active Operations</p>
      <h1 className="text-6xl md:text-7xl font-bold tracking-tighter leading-none uppercase text-foreground/90">
        Live Stats
      </h1>
    </section>

    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
      <StatCard label="Active FIRs" value="124" detail="Since last cycle" />
      <StatCard label="Legal Intelligence" value="45" detail="Queries processed" />
      <StatCard label="System Integrity" value="98%" detail="Operational" />
    </div>

    {/* Recent Activity Section */}
    <section className="px-6 py-8">
      <div className="flex items-end justify-between mb-4">
        <h2 className="text-4xl font-bold tracking-tighter uppercase text-foreground/80">Recent logs</h2>
        <button className="label-mono border-b border-accent/50 pb-0.5 hover:text-accent transition-all text-muted-foreground">View all</button>
      </div>
      
      <div className="space-y-0 border-t border-border">
        {[1, 2, 3].map((i) => (
          <div key={i} className="group flex items-center justify-between py-8 border-b border-border hover:bg-muted transition-all px-4 -mx-4 cursor-pointer">
            <div className="flex items-baseline gap-6">
              <span className="label-mono opacity-30 group-hover:opacity-100 group-hover:text-accent">0{i}</span>
              <div>
                <p className="text-lg font-bold uppercase tracking-tight">FIR #BK-2024-00{i} Generated</p>
                <p className="label-mono mt-0.5 text-muted-foreground text-[9px]">Officer Rahul S. • 24 mins ago</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className="label-mono text-[10px] border border-accent text-accent px-2 py-0.5">Pending</span>
              <span className="text-xl">→</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  </div>
);

const StatCard = ({ label, value, detail }) => (
  <div className="p-5 border-r border-b border-border flex flex-col justify-between min-h-[120px] group hover:bg-muted/30 transition-colors">
    <p className="label-mono text-muted-foreground/60 text-[8px] group-hover:text-accent transition-colors">{label}</p>
    <div>
      <h2 className="text-6xl font-bold tracking-tighter leading-none mb-1 text-foreground/90">{value}</h2>
      <p className="label-mono text-[7px] tracking-widest text-muted-foreground/40">{detail}</p>
    </div>
  </div>
);

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
            {activeTab === 'vault' && (
              <div className="section-py px-12 flex flex-col items-center justify-center text-center">
                <Database size={80} strokeWidth={1} className="text-muted-foreground/30 mb-8" />
                <h2 className="text-5xl font-bold uppercase tracking-tighter mb-4 text-foreground/70">Secure Vault</h2>
                <p className="label-mono text-muted-foreground/50">End-to-End Encryption Enabled</p>
              </div>
            )}
            {activeTab === 'linkage' && (
              <div className="section-py px-12 flex flex-col items-center justify-center text-center">
                <Link2 size={80} strokeWidth={1} className="text-muted-foreground/30 mb-8" />
                <h2 className="text-5xl font-bold uppercase tracking-tighter mb-4 text-foreground/70">Case Linkage</h2>
                <p className="label-mono text-muted-foreground/50">Pattern Detection Initializing</p>
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}
