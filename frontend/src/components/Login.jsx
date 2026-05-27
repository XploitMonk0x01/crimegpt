import { useState } from 'react';
import { motion } from 'framer-motion';
import { Shield, ArrowRight, Lock } from 'lucide-react';
import { authService } from '../services/api';
import useAuthStore from '../store/authStore';

const DEMO_USERS = {
  admin: { badge: 'PN-2024-ADMIN', pin: '1234', role: 'admin' },
  sho: { badge: 'PN-2024-SHO', pin: '5678', role: 'sho' },
  io: { badge: 'PN-2024-IO', pin: '5678', role: 'io' },
};

const MOCK_USERS = {
  sho: {
    user: { id: '00000000-0000-0000-0000-000000000001', name: 'SHO Officer (Demo)', badge_no: 'PN-2024-SHO', role: 'sho', is_active: true },
    token: 'demo-sho-token',
  },
  io: {
    user: { id: '00000000-0000-0000-0000-000000000002', name: 'IO Officer (Demo)', badge_no: 'PN-2024-IO', role: 'io', is_active: true },
    token: 'demo-io-token',
  },
};

const ROLE_DOT = {
  admin: 'bg-green-400',
  sho: 'bg-yellow-400',
  io: 'bg-blue-400',
};

const ROLE_LABEL = {
  admin: 'Admin Officer',
  sho: 'SHO Officer',
  io: 'IO Officer',
};

export default function Login() {
  const [badgeNo, setBadgeNo] = useState('');
  const [pin, setPin] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const setAuth = useAuthStore((state) => state.setAuth);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const response = await authService.login(badgeNo, pin);
      if (response.success) {
        setAuth(response.data.officer, response.data.access_token);
      } else {
        setError('INVALID_CREDENTIALS');
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'CONNECTION_ERROR');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async (roleKey) => {
    setLoading(true);
    setError('');
    const { badge, pin: demoPin, role } = DEMO_USERS[roleKey];

    try {
      const response = await authService.login(badge, demoPin);
      if (response.success) {
        setAuth(response.data.officer, response.data.access_token);
        return;
      }
    } catch (_err) {
      // Backend doesn't have this demo user — fall through to mock
    }

    // Fallback: mock auth for SHO / IO
    if (MOCK_USERS[role]) {
      const { user, token } = MOCK_USERS[role];
      setAuth(user, token);
    } else {
      setError('DEMO_LOGIN_FAILED');
    }

    setLoading(false);
  };

  return (
    <div className="h-screen w-full flex items-center justify-center bg-background p-6">
      <div className="w-full max-w-md">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col items-center mb-10 text-center"
        >
          <div className="w-12 h-12 bg-accent flex items-center justify-center mb-4 shadow-2xl">
            <Shield size={24} className="text-background" />
          </div>
          <p className="label-mono text-accent text-[9px] tracking-[0.5em] uppercase mb-2">Secure Node Access</p>
          <h1 className="text-4xl font-bold tracking-tighter uppercase leading-none text-foreground/90">
            CrimeGPT
          </h1>
        </motion.div>

        <motion.form 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          onSubmit={handleSubmit}
          className="space-y-4"
        >
          <div className="space-y-1.5">
            <label className="label-mono text-[8px] text-muted-foreground/50 uppercase">Badge Number</label>
            <div className="relative">
              <input
                type="text"
                value={badgeNo}
                onChange={(e) => setBadgeNo(e.target.value)}
                placeholder="PN-XXXXX"
                required
                className="w-full bg-muted/50 border-none p-3.5 text-base font-bold tracking-tight placeholder:text-muted-foreground/10 focus:outline-none focus:ring-1 focus:ring-accent/50 transition-all text-foreground/80"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="label-mono text-[8px] text-muted-foreground/50 uppercase">Security PIN</label>
            <div className="relative">
              <input
                type="password"
                value={pin}
                onChange={(e) => setPin(e.target.value)}
                placeholder="••••"
                required
                className="w-full bg-muted/50 border-none p-3.5 text-base font-bold tracking-tight placeholder:text-muted-foreground/10 focus:outline-none focus:ring-1 focus:ring-accent/50 transition-all text-foreground/80"
              />
              <Lock size={14} className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground/20" />
            </div>
          </div>

          {error && (
            <p className="label-mono text-[8px] text-accent text-center bg-accent/10 py-2 animate-pulse uppercase tracking-widest">
              Error: {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-accent text-background p-4 font-bold text-lg uppercase tracking-tighter flex items-center justify-between group hover:bg-foreground transition-all disabled:opacity-50"
          >
            {loading ? 'Authenticating...' : 'Access System'}
            <ArrowRight size={20} className="group-hover:translate-x-2 transition-transform" />
          </button>
        </motion.form>

        {/* DEMO ACCESS */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mt-8"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="flex-1 h-px bg-border/20" />
            <p className="label-mono text-[8px] text-muted-foreground/30 uppercase tracking-widest">Demo Access</p>
            <div className="flex-1 h-px bg-border/20" />
          </div>
          <div className="flex gap-2">
            {(['admin', 'sho', 'io']).map((roleKey) => (
              <button
                key={roleKey}
                type="button"
                disabled={loading}
                onClick={() => handleDemoLogin(roleKey)}
                className="flex-1 flex items-center gap-1.5 px-3 py-2.5 bg-muted/30 hover:bg-muted/60 border border-border/20 hover:border-border/40 transition-all group disabled:opacity-40"
              >
                <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${ROLE_DOT[roleKey]}`} />
                <span className="label-mono text-[8px] uppercase tracking-wider text-muted-foreground group-hover:text-foreground transition-colors truncate">
                  {ROLE_LABEL[roleKey]}
                </span>
              </button>
            ))}
          </div>
        </motion.div>

        <div className="mt-8 pt-8 border-t border-border/10 flex items-center justify-between opacity-30">
          <p className="label-mono text-[8px]">LOCAL_NODE_AH01</p>
          <p className="label-mono text-[8px]">AES_256_ENCRYPTED</p>
        </div>
      </div>
    </div>
  );
}
