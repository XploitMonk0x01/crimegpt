import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FileText, AlertTriangle, X, Search, Loader2 } from 'lucide-react';
import { dashboardService, searchService } from '../services/api';
import useFirStore from '../store/firStore';

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
  const [selectedFir, setSelectedFir] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);
  const [auditLogs, setAuditLogs] = useState([]);
  
  const localFirs = useFirStore(s => s.localFirs);
  const localDraftCount = localFirs.filter(f => f.status === 'draft').length;

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
    dashboardService.getAuditLogs({ limit: 10 }).then(r => {
      if (r.success) setAuditLogs(r.data || []);
    }).catch(() => {});
  }, []);

  const handleSearch = async (e) => {
    e?.preventDefault();
    if (!searchQuery.trim()) return;
    setSearching(true);
    try {
      const r = await searchService.searchFirs(searchQuery);
      if (r.success) setSearchResults(r);
    } catch { setSearchResults({ data: [], total: 0 }); }
    finally { setSearching(false); }
  };

  const stats = data?.fir_stats || {};
  const recentFirs = data?.recent_firs || [];

  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="px-6 py-6 border-b border-border flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <p className="label-mono mb-1 text-accent/80">Active Operations</p>
          <h1 className="text-6xl md:text-7xl font-bold tracking-tighter leading-none uppercase text-foreground/90">
            Live Stats
          </h1>
        </div>
        <button 
          onClick={fetchDashboard}
          className="label-mono text-[10px] border-2 border-foreground px-4 py-2 hover:bg-accent hover:border-accent hover:text-background transition-all uppercase font-bold"
        >
          Sync System
        </button>
      </section>

      {/* Search Bar */}
      <section className="px-6 py-4 border-b border-border">
        <form onSubmit={handleSearch} className="flex gap-3 items-center">
          <div className="relative flex-1">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground/40" />
            <input
              type="text" value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="Search FIRs by keyword, case number, or location..."
              className="w-full bg-muted/50 border-none pl-9 pr-4 py-3 text-sm tracking-tight focus:outline-none focus:ring-1 focus:ring-accent/40 placeholder:text-muted-foreground/20 text-foreground/80"
            />
          </div>
          <button type="submit" disabled={searching || !searchQuery.trim()}
            className="px-6 py-3 bg-accent text-background font-bold text-sm uppercase tracking-tighter hover:bg-foreground transition-all disabled:opacity-50 flex items-center gap-2">
            {searching ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />} Search
          </button>
        </form>
        {searchResults && (
          <div className="mt-4 border border-border p-4">
            <div className="flex justify-between items-center mb-3">
              <p className="label-mono text-[10px] text-accent">{searchResults.total} results for "{searchResults.query}"</p>
              <button onClick={() => { setSearchResults(null); setSearchQuery(''); }} className="text-muted-foreground hover:text-accent"><X size={14} /></button>
            </div>
            {searchResults.data?.length > 0 ? searchResults.data.map((f, i) => (
              <div key={f.id} onClick={() => setSelectedFir(f)}
                className="flex items-center justify-between py-3 border-b border-border/50 last:border-0 hover:bg-muted/30 px-2 cursor-pointer group">
                <div><p className="text-sm font-bold uppercase tracking-tight group-hover:text-accent">{f.fir_number}</p>
                  <p className="label-mono text-[8px] text-muted-foreground truncate max-w-md">{f.incident_description}</p></div>
                <StatusBadge status={f.status} />
              </div>
            )) : <p className="label-mono text-[9px] text-muted-foreground/40 py-4 text-center">No matching FIRs found</p>}
          </div>
        )}
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
          value={loading ? localDraftCount : (stats.draft ?? 0) + localDraftCount}
          detail="In progress"
          loading={false}
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
                onClick={() => setSelectedFir(fir)}
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

      {/* Detail Modal */}
      <AnimatePresence>
        {selectedFir && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4"
            onClick={() => setSelectedFir(null)}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              onClick={e => e.stopPropagation()}
              className="bg-muted border border-border w-full max-w-2xl max-h-[85vh] overflow-y-auto p-8 shadow-2xl relative"
            >
              <button 
                onClick={() => setSelectedFir(null)}
                className="absolute top-6 right-6 p-2 text-muted-foreground hover:text-foreground transition-colors hover:bg-background/50 rounded-full"
              >
                <X size={20} />
              </button>

              <div className="mb-10">
                <p className="label-mono text-[10px] text-accent/70 mb-2 uppercase tracking-widest">Case Profile</p>
                <h2 className="text-5xl font-bold tracking-tighter uppercase leading-none truncate">
                  {selectedFir.fir_number}
                </h2>
                <div className="mt-4 flex items-center gap-4">
                  <StatusBadge status={selectedFir.status} />
                  <span className="label-mono text-[9px] text-muted-foreground/40 italic">
                    ID: {selectedFir.id}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-12 py-8 border-y border-border/50">
                <div className="space-y-6">
                  <div>
                    <p className="label-mono text-[9px] text-muted-foreground uppercase mb-2">Complainant</p>
                    <p className="text-xl font-bold tracking-tight uppercase">{selectedFir.complainant?.name || 'NOT SPECIFIED'}</p>
                  </div>
                  <div>
                    <p className="label-mono text-[9px] text-muted-foreground uppercase mb-2">Contact Details</p>
                    <p className="text-base font-medium text-foreground/80">{selectedFir.complainant?.contact || selectedFir.complainant?.phone || '—'}</p>
                  </div>
                  <div>
                    <p className="label-mono text-[9px] text-muted-foreground uppercase mb-2">Identity Proof</p>
                    <p className="text-sm font-medium text-foreground/70">{selectedFir.complainant?.id_proof || selectedFir.complainant?.id_number || 'PENDING VERIFICATION'}</p>
                  </div>
                </div>

                <div className="space-y-6">
                  <div>
                    <p className="label-mono text-[9px] text-muted-foreground uppercase mb-2">Location of Incident</p>
                    <p className="text-xl font-bold tracking-tight uppercase">{selectedFir.incident_location || selectedFir.location || 'UNDEFINED'}</p>
                  </div>
                  <div>
                    <p className="label-mono text-[9px] text-muted-foreground uppercase mb-2">Occurrence Date</p>
                    <p className="text-base font-medium text-foreground/80">
                      {selectedFir.incident_date || selectedFir.created_at ? new Date(selectedFir.incident_date || selectedFir.created_at).toLocaleString() : '—'}
                    </p>
                  </div>
                  <div>
                    <p className="label-mono text-[9px] text-muted-foreground uppercase mb-2">Reported At</p>
                    <p className="text-sm font-medium text-foreground/70">
                      {selectedFir.created_at ? new Date(selectedFir.created_at).toLocaleString() : '—'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-10">
                <div className="flex items-center justify-between mb-4">
                  <p className="label-mono text-[9px] text-muted-foreground uppercase">Narrative Statement</p>
                  <FileText size={14} className="text-muted-foreground/20" />
                </div>
                <div className="bg-background/30 p-6 border border-border/40 rounded-sm">
                  <p className="text-sm leading-relaxed text-foreground/80 whitespace-pre-wrap italic">
                    "{selectedFir.incident_description || selectedFir.ai_narrative || 'No statement provided.'}"
                  </p>
                </div>
              </div>

              {selectedFir.sections?.length > 0 && (
                <div className="mt-8">
                  <p className="label-mono text-[9px] text-muted-foreground uppercase mb-3">Legal Provisions</p>
                  <div className="flex flex-wrap gap-2">
                    {selectedFir.sections?.map((section, idx) => (
                      <span key={idx} className="label-mono text-[9px] bg-accent/5 border border-accent/20 text-accent px-3 py-1 uppercase">
                        {section}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="mt-12 flex justify-end">
                <button 
                  onClick={() => setSelectedFir(null)}
                  className="px-8 py-3 bg-foreground text-background font-bold text-sm uppercase tracking-widest hover:bg-accent transition-colors"
                >
                  Close Record
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
