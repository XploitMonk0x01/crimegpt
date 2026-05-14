import React, { useState, useCallback, useEffect } from 'react';
import { 
  LayoutDashboard, 
  FileText, 
  MessageSquare, 
  Database, 
  Link2, 
  Settings,
  ChevronLeft,
  ChevronRight,
  Shield,
  GripVertical
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab }) {
  const [width, setWidth] = useState(192); // Default w-48
  const [isResizing, setIsResizing] = useState(false);
  const isCollapsed = width <= 80;

  const menuItems = [
    { id: 'dashboard', label: 'Command', icon: LayoutDashboard },
    { id: 'fir', label: 'Automator', icon: FileText },
    { id: 'lexbot', label: 'LexBot', icon: MessageSquare },
    { id: 'vault', label: 'Vault', icon: Database },
    { id: 'linkage', label: 'Linkage', icon: Link2 },
  ];

  const startResizing = useCallback((e) => {
    setIsResizing(true);
  }, []);

  const stopResizing = useCallback(() => {
    setIsResizing(false);
  }, []);

  const resize = useCallback((e) => {
    if (isResizing) {
      const newWidth = e.clientX;
      if (newWidth > 64 && newWidth < 450) {
        setWidth(newWidth);
      }
    }
  }, [isResizing]);

  useEffect(() => {
    window.addEventListener('mousemove', resize);
    window.addEventListener('mouseup', stopResizing);
    return () => {
      window.removeEventListener('mousemove', resize);
      window.removeEventListener('mouseup', stopResizing);
    };
  }, [resize, stopResizing]);

  const toggleCollapse = () => {
    if (isCollapsed) {
      setWidth(192);
    } else {
      setWidth(64);
    }
  };

  return (
    <div 
      style={{ width: `${width}px` }}
      className={`h-screen border-r border-border flex flex-col bg-background relative shrink-0 transition-[width] duration-75 ${isResizing ? 'transition-none' : ''}`}
    >
      {/* Brand Section */}
      <div className={`p-6 border-b border-border flex items-center justify-between h-20 ${isCollapsed ? 'px-4' : ''}`}>
        {!isCollapsed ? (
          <div className="flex items-center gap-2 overflow-hidden">
            <Shield size={18} className="text-accent shrink-0" />
            <h2 className="text-xl font-bold tracking-tighter uppercase text-foreground/90 whitespace-nowrap">CrimeGPT</h2>
          </div>
        ) : (
          <Shield size={24} className="text-accent mx-auto" />
        )}
        {!isCollapsed && (
          <button 
            onClick={toggleCollapse}
            className="p-1 hover:bg-muted transition-colors rounded text-muted-foreground shrink-0"
          >
            <ChevronLeft size={16} />
          </button>
        )}
      </div>

      {/* Collapse Trigger for Mini Mode */}
      {isCollapsed && (
        <button 
          onClick={toggleCollapse}
          className="absolute -right-3 top-24 bg-accent text-background rounded-full p-1 shadow-lg z-50 border border-background"
        >
          <ChevronRight size={12} />
        </button>
      )}

      {/* Nav Section */}
      <nav className="flex-1 py-6 px-3 flex flex-col gap-1 overflow-hidden">
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={`flex items-center gap-4 px-4 py-3 transition-all duration-200 group overflow-hidden ${
              activeTab === item.id 
                ? 'bg-accent text-background' 
                : 'text-muted-foreground hover:bg-muted hover:text-foreground'
            } ${isCollapsed ? 'justify-center px-0' : ''}`}
          >
            <item.icon size={18} className="shrink-0" />
            {!isCollapsed && (
              <span className="label-mono text-[10px] uppercase font-bold tracking-widest truncate">
                {item.label}
              </span>
            )}
          </button>
        ))}
      </nav>

      {/* Footer / Settings */}
      <div className="p-3 border-t border-border overflow-hidden">
        <button className={`w-full flex items-center gap-4 px-4 py-3 text-muted-foreground hover:bg-muted hover:text-foreground transition-all ${isCollapsed ? 'justify-center px-0' : ''}`}>
          <Settings size={18} className="shrink-0" />
          {!isCollapsed && (
            <span className="label-mono text-[10px] uppercase font-bold tracking-widest truncate">Settings</span>
          )}
        </button>
        
        {!isCollapsed && (
          <div className="mt-4 pt-4 border-t border-border px-2 overflow-hidden">
            <p className="label-mono text-[8px] text-muted-foreground/50">NODE_STATUS</p>
            <p className="font-mono text-[9px] text-foreground mt-1 uppercase tracking-tighter truncate">AHM_SECURE_01</p>
          </div>
        )}
      </div>

      {/* Resize Handle */}
      <div 
        onMouseDown={startResizing}
        className={`absolute top-0 right-0 w-1 h-full cursor-col-resize hover:bg-accent/30 transition-colors z-40 group flex items-center justify-center`}
      >
        <div className="opacity-0 group-hover:opacity-100 bg-accent w-1 h-12 rounded-full" />
      </div>
    </div>
  );
}
