import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FileText, AlertTriangle } from 'lucide-react';
import { dashboardService } from '../services/api';

const StatCard = ({ label, value, detail, loading }) => (
  <div className="p-5 border-r border-b border-border flex flex-col justify-between min-h-[120px] group hover:bg-muted/30 transition-colors">
    <p className="label-mono text-muted-foreground/60 text-[8px] group-hover:text-accent transition-colors">{label}</p>
    <div>
      {loading ? (
        <div className="h-14 flex items-end">
          <div className="w-20 h-10 bg-muted animate-pulse" />
        </div>
      ) : (
        <>
          <h2 className="text-6xl font-bold tracking-tighter leading-none mb-1 text-foreground/90">{value}</h2>
          <p className="label-mono text-[7px] tracking-widest text-muted-foreground/40">{detail}</p>
        </>
      )}
    </div>
  </div>
);

const StatusBadge = ({ status }) => {
  const styles = {
    draft: 'border-muted-foreground text-muted-foreground',
    submitted: 'border-yellow-500 text-yellow-500',
    approved: 'border-green-500 text-green-500',
    rejected: 'border-accent text-accent',
  };

  return (
    <span className={`label-mono text-[10px] border px-2 py-0.5 uppercase ${styles[status] || styles.draft}`}>
      {status || 'Unknown'}
    </span>
  );
};

function formatTimeAgo(isoString) {
  if (!isoString) return '';
  const timestamp = new Date(isoString).getTime();
  if (Number.isNaN(timestamp)) return '';
  const diff = Date.now() - timestamp;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins} min ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await dashboardService.getOfficerDashboard();
      if (response.success) {
        setData(response.data);
      }
    } catch (err) {
      console.error('Dashboard fetch failed:', err);
      setError(err.response?.data?.detail || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    queueMicrotask(fetchDashboard);
  }, []);

  const stats = data?.fir_stats || {};
  const recentFirs = data?.recent_firs || [];

  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="px-6 py-6 border-b border-border">
        <p className="label-mono mb-1 text-accent/80">Active Operations</p>
        <h1 className="text-6xl md:text-7xl font-bold tracking-tighter leading-none uppercase text-foreground/90">
          Live Stats
        </h1>
      </section>

      {/* Error Banner */}
      {error && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="mx-6 mt-4 bg-accent/10 border border-accent/30 px-4 py-3 flex items-center gap-3"
        >
          <AlertTriangle size={16} className="text-accent shrink-0" />
          <p className="label-mono text-[10px] text-accent">{error}</p>
        </motion.div>
      )}

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total FIRs"
          value={loading ? '—' : stats.total ?? 0}
          detail="All records"
          loading={loading}
        />
        <StatCard
          label="Submitted"
          value={loading ? '—' : stats.submitted ?? 0}
          detail="Pending review"
          loading={loading}
        />
        <StatCard
          label="Approved"
          value={loading ? '—' : stats.approved ?? 0}
          detail="Cleared"
          loading={loading}
        />
        <StatCard
          label="Evidence Files"
          value={loading ? '—' : data?.evidence_count ?? 0}
          detail="In vault"
          loading={loading}
        />
      </div>

      {/* Draft & Rejected Row */}
      <div className="grid grid-cols-1 md:grid-cols-2">
        <StatCard
          label="Drafts"
          value={loading ? '—' : stats.draft ?? 0}
          detail="In progress"
          loading={loading}
        />
        <StatCard
          label="Rejected"
          value={loading ? '—' : stats.rejected ?? 0}
          detail="Needs revision"
          loading={loading}
        />
      </div>

      {/* Recent FIRs Section */}
      <section className="px-6 py-8">
        <div className="flex items-end justify-between mb-4">
          <h2 className="text-4xl font-bold tracking-tighter uppercase text-foreground/80">Recent FIRs</h2>
          {error && (
            <button
              onClick={fetchDashboard}
              className="label-mono border-b border-accent/50 pb-0.5 hover:text-accent transition-all text-muted-foreground"
            >
              Retry
            </button>
          )}
        </div>

        <div className="space-y-0 border-t border-border">
          {loading ? (
            // Skeleton loaders
            [...Array(3)].map((_, i) => (
              <div key={i} className="flex items-center justify-between py-8 border-b border-border px-4 -mx-4">
                <div className="flex items-baseline gap-6">
                  <div className="w-6 h-4 bg-muted animate-pulse" />
                  <div>
                    <div className="w-48 h-5 bg-muted animate-pulse mb-2" />
                    <div className="w-32 h-3 bg-muted/50 animate-pulse" />
                  </div>
                </div>
                <div className="w-16 h-5 bg-muted animate-pulse" />
              </div>
            ))
          ) : recentFirs.length === 0 ? (
            <div className="py-16 text-center">
              <FileText size={48} strokeWidth={1} className="text-muted-foreground/20 mx-auto mb-4" />
              <p className="label-mono text-muted-foreground/40 text-[10px]">No FIRs recorded yet</p>
            </div>
          ) : (
            recentFirs.map((fir, i) => (
              <motion.div
                key={fir.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="group flex items-center justify-between py-8 border-b border-border hover:bg-muted transition-all px-4 -mx-4 cursor-pointer"
              >
                <div className="flex items-baseline gap-6">
                  <span className="label-mono opacity-30 group-hover:opacity-100 group-hover:text-accent">
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <div>
                    <p className="text-lg font-bold uppercase tracking-tight">
                      {fir.fir_number || `FIR-${fir.id.slice(0, 8)}`}
                    </p>
                    <p className="label-mono mt-0.5 text-muted-foreground text-[9px]">
                      {formatTimeAgo(fir.created_at)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <StatusBadge status={fir.status} />
                  <span className="text-xl group-hover:translate-x-1 transition-transform">→</span>
                </div>
              </motion.div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}
