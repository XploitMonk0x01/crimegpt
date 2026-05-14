import { useState } from 'react';
import { motion } from 'framer-motion';
import { Shield, ArrowRight, Lock } from 'lucide-react';
import { authService } from '../services/api';
import useAuthStore from '../store/authStore';

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

        <div className="mt-12 pt-8 border-t border-border/10 flex items-center justify-between opacity-30">
          <p className="label-mono text-[8px]">LOCAL_NODE_AH01</p>
          <p className="label-mono text-[8px]">AES_256_ENCRYPTED</p>
        </div>
      </div>
    </div>
  );
}
