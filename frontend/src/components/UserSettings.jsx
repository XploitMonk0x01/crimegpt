import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, User, Shield, Bell, Lock, Moon, Sun, LogOut, ChevronRight } from 'lucide-react';
import useAuthStore from '../store/authStore';

const SettingRow = ({ icon: Icon, label, children }) => (
  <div className="flex items-center justify-between py-4 border-b border-border group">
    <div className="flex items-center gap-3">
      <Icon size={14} className="text-muted-foreground group-hover:text-accent transition-colors shrink-0" />
      <span className="label-mono text-[10px] text-muted-foreground group-hover:text-foreground transition-colors">{label}</span>
    </div>
    <div className="text-sm font-medium">{children}</div>
  </div>
);

const Toggle = ({ value, onChange }) => (
  <button
    onClick={() => onChange(!value)}
    className={`relative w-10 h-5 rounded-full transition-colors ${value ? 'bg-accent' : 'bg-muted'}`}
  >
    <span className={`absolute top-0.5 left-0.5 w-4 h-4 bg-background rounded-full shadow transition-transform ${value ? 'translate-x-5' : 'translate-x-0'}`} />
  </button>
);

export default function UserSettings({ isOpen, onClose }) {
  const { user, logout } = useAuthStore();
  const [notifications, setNotifications] = useState(true);
  
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('crimegpt_dark_mode');
    return saved !== null ? saved === 'true' : true;
  });

  useEffect(() => {
    localStorage.setItem('crimegpt_dark_mode', darkMode);
    if (darkMode) {
      document.documentElement.classList.remove('light');
    } else {
      document.documentElement.classList.add('light');
    }
  }, [darkMode]);
  const [autoSave, setAutoSave] = useState(true);
  const [name, setName] = useState(user?.name || '');
  const [badge, setBadge] = useState(user?.badge_number || 'DM-0001');
  const [station, setStation] = useState(user?.station || 'Central HQ');
  const [editing, setEditing] = useState(false);

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-40 bg-background/60 backdrop-blur-sm"
          />

          {/* Panel */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed right-0 top-0 h-full w-full max-w-md z-50 bg-background border-l border-border flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-border shrink-0">
              <div>
                <p className="label-mono text-[9px] text-accent/70 mb-1">Configuration</p>
                <h2 className="text-2xl font-bold tracking-tighter uppercase">User Settings</h2>
              </div>
              <button onClick={onClose} className="p-2 hover:bg-muted transition-colors text-muted-foreground hover:text-foreground">
                <X size={18} />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-8">

              {/* Profile Section */}
              <div>
                <p className="label-mono text-[8px] text-accent mb-4 tracking-widest">— PROFILE</p>

                {/* Avatar */}
                <div className="flex items-center gap-4 mb-6">
                  <div className="h-14 w-14 border-2 border-accent flex items-center justify-center font-black text-lg bg-accent/10 text-accent">
                    {name.split(' ').map(n => n[0]).join('').slice(0, 2) || '??'}
                  </div>
                  <div>
                    <p className="font-bold uppercase tracking-tighter">{name || 'Officer'}</p>
                    <p className="label-mono text-[9px] text-muted-foreground mt-0.5">{badge} • {station}</p>
                  </div>
                </div>

                {/* Editable fields */}
                {editing ? (
                  <div className="space-y-3">
                    {[
                      { label: 'Full Name', value: name, setter: setName, placeholder: 'OFFICER NAME' },
                      { label: 'Badge Number', value: badge, setter: setBadge, placeholder: 'XX-0000' },
                      { label: 'Station', value: station, setter: setStation, placeholder: 'STATION NAME' },
                    ].map(({ label, value, setter, placeholder }) => (
                      <div key={label} className="flex flex-col gap-1.5">
                        <label className="label-mono text-[8px] text-muted-foreground">{label}</label>
                        <input
                          value={value}
                          onChange={e => setter(e.target.value)}
                          placeholder={placeholder}
                          className="bg-muted/50 border-none p-3 text-sm font-normal tracking-tight focus:outline-none focus:ring-1 focus:ring-accent/40 transition-all"
                        />
                      </div>
                    ))}
                    <div className="flex gap-3 pt-2">
                      <button
                        onClick={() => setEditing(false)}
                        className="flex-1 py-2.5 bg-accent text-background font-bold label-mono text-[10px] tracking-widest hover:bg-foreground transition-all"
                      >
                        SAVE
                      </button>
                      <button
                        onClick={() => setEditing(false)}
                        className="flex-1 py-2.5 border border-border text-muted-foreground font-bold label-mono text-[10px] tracking-widest hover:bg-muted transition-all"
                      >
                        CANCEL
                      </button>
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={() => setEditing(true)}
                    className="w-full flex items-center justify-between py-3 px-4 border border-border hover:bg-muted transition-all group"
                  >
                    <div className="flex items-center gap-2">
                      <User size={13} className="text-muted-foreground" />
                      <span className="label-mono text-[10px] text-muted-foreground group-hover:text-foreground">Edit Profile</span>
                    </div>
                    <ChevronRight size={14} className="text-muted-foreground group-hover:text-accent transition-colors" />
                  </button>
                )}
              </div>

              {/* Preferences */}
              <div>
                <p className="label-mono text-[8px] text-accent mb-4 tracking-widest">— PREFERENCES</p>
                <SettingRow icon={Bell} label="Notifications">
                  <Toggle value={notifications} onChange={setNotifications} />
                </SettingRow>
                <SettingRow icon={Moon} label="Dark Mode">
                  <Toggle value={darkMode} onChange={setDarkMode} />
                </SettingRow>
                <SettingRow icon={Shield} label="Auto-Save Drafts">
                  <Toggle value={autoSave} onChange={setAutoSave} />
                </SettingRow>
              </div>

              {/* Security */}
              <div>
                <p className="label-mono text-[8px] text-accent mb-4 tracking-widest">— SECURITY</p>
                <SettingRow icon={Lock} label="Role">
                  <span className="label-mono text-[10px] border border-accent/40 text-accent px-2 py-0.5">
                    {user?.role?.toUpperCase() || 'OFFICER'}
                  </span>
                </SettingRow>
                <SettingRow icon={Shield} label="Session">
                  <span className="label-mono text-[10px] text-green-400">ACTIVE</span>
                </SettingRow>
              </div>

              {/* App Info */}
              <div>
                <p className="label-mono text-[8px] text-accent mb-4 tracking-widest">— SYSTEM</p>
                <SettingRow icon={Shield} label="Version">
                  <span className="label-mono text-[10px] text-muted-foreground">CrimeGPT v1.0.0</span>
                </SettingRow>
                <SettingRow icon={Shield} label="Node">
                  <span className="label-mono text-[10px] text-muted-foreground">AHM_SECURE_01</span>
                </SettingRow>
              </div>
            </div>

            {/* Footer */}
            <div className="p-6 border-t border-border shrink-0">
              <button
                onClick={() => { logout(); onClose(); }}
                className="w-full flex items-center justify-center gap-3 py-3 border border-accent/40 text-accent hover:bg-accent hover:text-background transition-all group"
              >
                <LogOut size={14} />
                <span className="label-mono text-[10px] font-bold tracking-widest">SIGN OUT</span>
              </button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
