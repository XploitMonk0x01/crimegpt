import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FileText, AlertTriangle, X, Search, Loader2, CheckCircle, XCircle, Shield, ClipboardList, BarChart2, Globe, Database, UserCheck } from 'lucide-react';
import { dashboardService, searchService, firService, cctnsService } from '../services/api';
import useFirStore from '../store/firStore';
import useAuthStore from '../store/authStore';
import toast from 'react-hot-toast';

const StatCard = ({ label, value, detail, loading, accent }) => (
  <div className={`p-5 border-r border-b border-border flex flex-col justify-between min-h-[120px] group hover:bg-muted/30 transition-colors ${accent ? 'border-l-2 border-l-accent' : ''}`}>
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
    <span className={`label-mono text-[10px] border px-2 py-0.5 uppercase ${styles[typeof status === 'object' ? 'draft' : status] || styles.draft}`}>
      {typeof status === 'object' ? 'draft' : (status || 'Unknown')}
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
  return `${Math.floor(hours / 24)}d ago`;
}

function safeStr(val) {
  if (val === null || val === undefined) return '—';
  if (typeof val === 'object') return JSON.stringify(val);
  return String(val);
}

// ─── Pending Approvals Panel (Admin only) ─────────────────────────────────────
function PendingApprovalsPanel({ firs, onAction }) {
  const [actingId, setActingId] = useState(null);

  const handleAction = async (fir, action) => {
    setActingId(fir.id);
    await onAction(fir, action);
    setActingId(null);
  };

  const pendingFirs = firs.filter(f => {
    const status = typeof f.status === 'object' ? f.status?.value : f.status;
    return status === 'submitted';
  });

  if (pendingFirs.length === 0) {
    return (
      <div className="py-10 text-center">
        <CheckCircle size={32} strokeWidth={1} className="text-green-500/30 mx-auto mb-3" />
        <p className="label-mono text-[9px] text-muted-foreground/40">No pending approvals</p>
      </div>
    );
  }

  return (
    <div className="space-y-0 border-t border-border">
      {pendingFirs.map((fir, i) => (
        <motion.div
          key={fir.id}
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.05 }}
          className="flex items-center justify-between py-5 border-b border-border px-4 -mx-4 hover:bg-muted/30 transition-colors"
        >
          <div className="flex items-baseline gap-4">
            <span className="label-mono text-accent/50 text-[9px]">{String(i + 1).padStart(2, '0')}</span>
            <div>
              <p className="font-bold uppercase tracking-tight">{fir.fir_number || `FIR-${fir.id?.slice(0, 8)}`}</p>
              <p className="label-mono text-[8px] text-muted-foreground mt-0.5 truncate max-w-xs">
                {safeStr(fir.incident_description || fir.ai_narrative)?.slice(0, 80)}...
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              disabled={actingId === fir.id}
              onClick={() => handleAction(fir, 'approve')}
              className="flex items-center gap-1.5 px-4 py-2 bg-green-500/10 border border-green-500/40 text-green-400 hover:bg-green-500/20 transition-all label-mono text-[9px] uppercase disabled:opacity-50"
            >
              {actingId === fir.id ? <Loader2 size={12} className="animate-spin" /> : <CheckCircle size={12} />}
              Approve
            </button>
            <button
              disabled={actingId === fir.id}
              onClick={() => handleAction(fir, 'reject')}
              className="flex items-center gap-1.5 px-4 py-2 bg-accent/10 border border-accent/40 text-accent hover:bg-accent/20 transition-all label-mono text-[9px] uppercase disabled:opacity-50"
            >
              {actingId === fir.id ? <Loader2 size={12} className="animate-spin" /> : <XCircle size={12} />}
              Reject
            </button>
          </div>
        </motion.div>
      ))}
    </div>
  );
}

// ─── Audit Log Panel (SHO + Admin) ────────────────────────────────────────────
function AuditLogPanel({ logs }) {
  if (!logs || logs.length === 0) {
    return <p className="label-mono text-[9px] text-muted-foreground/40 py-4 text-center">No audit events recorded</p>;
  }
  const formatAction = (action) => {
    if (!action) return 'UNKNOWN';
    return String(action).replace(/_/g, ' ').toUpperCase();
  };

  return (
    <div className="space-y-0 border-t border-border max-h-64 overflow-y-auto custom-scrollbar">
      {logs.map((log, i) => (
        <div key={log.id || i} className="flex items-center justify-between py-3 border-b border-border/50 last:border-0 px-1 hover:bg-muted/30 transition-colors group">
          <div className="flex items-center gap-3">
            <span className="label-mono text-[7px] text-accent/50 w-5 text-right group-hover:text-accent transition-colors">{i + 1}</span>
            <div>
              <p className="label-mono text-[9px] text-foreground/80 font-bold">{formatAction(log.action)}</p>
              <p className="label-mono text-[7px] text-muted-foreground/60 mt-0.5">
                <span className="text-accent/70">{safeStr(log.resource_type).toUpperCase()}</span>
                <span className="mx-1.5 opacity-30">|</span>
                By: <span className="text-foreground/70">{log.officer_badge || 'SYSTEM'}</span>
              </p>
            </div>
          </div>
          <p className="label-mono text-[7px] text-muted-foreground/40 shrink-0">{formatTimeAgo(log.created_at)}</p>
        </div>
      ))}
    </div>
  );
}

// ─── FIR Detail Modal ─────────────────────────────────────────────────────────
function FIRDetailModal({ fir, onClose, role, onApprove, onReject, onSyncLocal }) {
  const [acting, setActing] = useState(false);
  const [syncingCctns, setSyncingCctns] = useState(false);
  const [cctnsData, setCctnsData] = useState(null);

  useEffect(() => {
    if (fir?.id && !fir.id.startsWith('local-')) {
      cctnsService.getStatus(fir.id)
        .then(res => {
          if (res.success && res.is_synced) {
            setCctnsData({
              cctns_national_id: res.cctns_national_id,
              verification_hash: 'VERIFIED_ON_GRID',
              national_grid_node: 'NCRB_CENTRAL_NODE_DELHI_01',
              synced_at: res.last_sync
            });
          }
        })
        .catch(() => {});
    }
  }, [fir?.id]);

  const handleCctnsSync = async () => {
    try {
      setSyncingCctns(true);
      const res = await cctnsService.syncFir(fir.id);
      if (res.success) {
        setCctnsData(res);
        toast.success(`FIR synced to CCTNS! Ref: ${res.cctns_national_id}`);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'CCTNS Sync failed');
    } finally {
      setSyncingCctns(false);
    }
  };

  const handleApprove = async () => {
    setActing(true);
    await onApprove(fir);
    setActing(false);
    onClose();
  };

  const handleReject = async () => {
    try {
      setActing(true);
      await onReject(fir);
    } finally {
      setActing(false);
    }
  };

  const handleSyncLocalAction = async () => {
    try {
      setActing(true);
      await onSyncLocal(fir);
    } finally {
      setActing(false);
    }
  };

  const firStatus = typeof fir.status === 'object' ? fir.status?.value : fir.status;
  const isSubmitted = firStatus === 'submitted';

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        onClick={e => e.stopPropagation()}
        className="bg-muted border border-border w-full max-w-2xl max-h-[85vh] overflow-y-auto p-8 shadow-2xl relative"
      >
        <button onClick={onClose} className="absolute top-6 right-6 p-2 text-muted-foreground hover:text-foreground transition-colors hover:bg-background/50 rounded-full">
          <X size={20} />
        </button>

        <div className="mb-10">
          <p className="label-mono text-[10px] text-accent/70 mb-2 uppercase tracking-widest">Case Profile</p>
          <h2 className="text-5xl font-bold tracking-tighter uppercase leading-none truncate">{fir.fir_number}</h2>
          <div className="mt-4 flex items-center gap-4">
            <StatusBadge status={fir.status} />
            {fir.id && !fir.id.startsWith('local-') && (
              <span className="label-mono text-[9px] text-muted-foreground/40 italic">ID: {fir.id}</span>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 py-8 border-y border-border/50">
          <div className="space-y-6">
            <div>
              <p className="label-mono text-[9px] text-muted-foreground uppercase mb-2">Complainant</p>
              <p className="text-xl font-bold tracking-tight uppercase">{safeStr(fir.complainant?.name) || 'NOT SPECIFIED'}</p>
            </div>
            <div>
              <p className="label-mono text-[9px] text-muted-foreground uppercase mb-2">Contact Details</p>
              <p className="text-base font-medium text-foreground/80">{safeStr(fir.complainant?.contact || fir.complainant?.phone) || '—'}</p>
            </div>
            <div>
              <p className="label-mono text-[9px] text-muted-foreground uppercase mb-2">Address</p>
              <p className="text-sm font-medium text-foreground/70">{safeStr(fir.complainant?.address) || '—'}</p>
            </div>
            <div>
              <p className="label-mono text-[9px] text-muted-foreground uppercase mb-2">Identity Proof</p>
              <p className="text-sm font-medium text-foreground/70">{safeStr(fir.complainant?.id_proof || fir.complainant?.id_number) || 'PENDING VERIFICATION'}</p>
            </div>
          </div>
          <div className="space-y-6">
            <div>
              <p className="label-mono text-[9px] text-muted-foreground uppercase mb-2">Location of Incident</p>
              <p className="text-xl font-bold tracking-tight uppercase">
                {(() => {
                  const loc = fir.incident_location || fir.location;
                  if (!loc) return 'UNDEFINED';
                  if (typeof loc === 'object') {
                    return loc.name
                      ? `${loc.name}${loc.description ? ' — ' + loc.description : ''}`
                      : JSON.stringify(loc);
                  }
                  return loc;
                })()}
              </p>
            </div>
            <div>
              <p className="label-mono text-[9px] text-muted-foreground uppercase mb-2">Occurrence Date</p>
              <p className="text-base font-medium text-foreground/80">
                {fir.incident_date || fir.created_at ? new Date(fir.incident_date || fir.created_at).toLocaleString() : '—'}
              </p>
            </div>
            <div>
              <p className="label-mono text-[9px] text-muted-foreground uppercase mb-2">Reported At</p>
              <p className="text-sm font-medium text-foreground/70">{fir.created_at ? new Date(fir.created_at).toLocaleString() : '—'}</p>
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
              "{safeStr(fir.incident_description || fir.ai_narrative) || 'No statement provided.'}"
            </p>
          </div>
        </div>

        {fir.sections?.length > 0 && (
          <div className="mt-8">
            <p className="label-mono text-[9px] text-muted-foreground uppercase mb-3">Legal Provisions</p>
            <div className="flex flex-wrap gap-2">
              {fir.sections?.map((section, idx) => (
                <span key={idx} className="label-mono text-[9px] bg-accent/5 border border-accent/20 text-accent px-3 py-1 uppercase">
                  {typeof section === 'object' ? (section.section || section.type || JSON.stringify(section)) : section}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* CCTNS & BharatPol National Grid Sync */}
        <div className="mt-8 p-4 border border-blue-500/30 bg-blue-500/5 rounded-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Globe size={14} className="text-blue-400" />
              <div>
                <p className="label-mono text-[9px] font-bold text-blue-400 uppercase tracking-wider">CCTNS National Grid & BharatPol Linkage</p>
                <p className="label-mono text-[8px] text-muted-foreground mt-0.5">Sync FIR record with NCRB Central Database Grid</p>
              </div>
            </div>
            <button
              disabled={syncingCctns || (fir.id && fir.id.startsWith('local-'))}
              onClick={handleCctnsSync}
              className="px-4 py-2 bg-blue-500/10 border border-blue-500/40 text-blue-400 hover:bg-blue-500/20 transition-all label-mono text-[9px] font-bold uppercase tracking-wider disabled:opacity-40 flex items-center gap-1.5"
            >
              {syncingCctns ? <Loader2 size={12} className="animate-spin" /> : <Database size={12} />}
              {cctnsData ? 'Re-Sync CCTNS' : 'Push to CCTNS'}
            </button>
          </div>
          {cctnsData && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="mt-3 pt-3 border-t border-blue-500/20 space-y-1">
              <div className="flex justify-between items-center text-[9px] label-mono">
                <span className="text-muted-foreground">National Ref ID:</span>
                <span className="font-bold text-green-400">{cctnsData.cctns_national_id}</span>
              </div>
              <div className="flex justify-between items-center text-[8px] label-mono">
                <span className="text-muted-foreground">Verification Hash:</span>
                <span className="text-blue-300 font-mono">{cctnsData.verification_hash}</span>
              </div>
              <div className="flex justify-between items-center text-[8px] label-mono">
                <span className="text-muted-foreground">National Grid Node:</span>
                <span className="text-muted-foreground">{cctnsData.national_grid_node}</span>
              </div>
            </motion.div>
          )}
        </div>

        {/* Admin Approve/Reject Controls */}
        {role === 'admin' && isSubmitted && (
          <div className="mt-10 p-5 border border-yellow-500/30 bg-yellow-500/5">
            {fir?.id?.toString().startsWith('local-') ? (
              <div className="flex flex-col gap-3">
                <p className="label-mono text-[10px] text-yellow-500 uppercase flex items-center gap-2">
                  <AlertTriangle size={14} /> This FIR is saved locally and must be synced to the server before review.
                </p>
                <button
                  onClick={handleSyncLocalAction}
                  disabled={acting}
                  className="px-4 py-2 bg-yellow-500/20 border border-yellow-500/40 text-yellow-400 hover:bg-yellow-500/30 transition-all label-mono text-[9px] uppercase font-bold self-start flex items-center gap-2"
                >
                  {acting ? <Loader2 size={12} className="animate-spin" /> : <Database size={12} />}
                  Sync to Server Now
                </button>
              </div>
            ) : (
              <>
                <p className="label-mono text-[8px] text-yellow-500/70 uppercase mb-4 flex items-center gap-2">
                  <Shield size={10} /> Admin Action Required — This FIR is pending review
                </p>
                <div className="flex gap-3">
                  <button
                    disabled={acting}
                    onClick={handleApprove}
                    className="flex-1 flex items-center justify-center gap-2 py-3 bg-green-500/10 border border-green-500/40 text-green-400 hover:bg-green-500/20 transition-all label-mono text-[10px] uppercase font-bold disabled:opacity-50"
                  >
                    {acting ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle size={14} />}
                    Approve FIR
                  </button>
                  <button
                    disabled={acting}
                    onClick={handleReject}
                    className="flex-1 flex items-center justify-center gap-2 py-3 bg-accent/10 border border-accent/40 text-accent hover:bg-accent/20 transition-all label-mono text-[10px] uppercase font-bold disabled:opacity-50"
                  >
                    {acting ? <Loader2 size={14} className="animate-spin" /> : <XCircle size={14} />}
                    Reject FIR
                  </button>
                </div>
              </>
            )}
          </div>
        )}

        {/* SHO read-only notice */}
        {role === 'sho' && isSubmitted && (
          <div className="mt-10 p-4 border border-yellow-500/20 bg-yellow-500/5">
            <p className="label-mono text-[8px] text-yellow-500/60 uppercase">
              ⚠ This FIR awaits Admin Officer approval. SHO role has read-only access.
            </p>
          </div>
        )}

        <div className="mt-8 flex justify-end">
          <button onClick={onClose} className="px-8 py-3 bg-foreground text-background font-bold text-sm uppercase tracking-widest hover:bg-accent transition-colors">
            Close Record
          </button>
        </div>
      </motion.div>
    </motion.div>
  );
}

// ─── Main Dashboard ────────────────────────────────────────────────────────────
export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedFir, setSelectedFir] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);
  const [auditLogs, setAuditLogs] = useState([]);
  const [activeSection, setActiveSection] = useState('firs'); // 'firs' | 'pending' | 'audit'

  const localFirs = useFirStore(s => s.localFirs);
  const deleteFir = useFirStore(s => s.deleteFir);
  const localDraftCount = localFirs.filter(f => f.status === 'draft').length;

  const user = useAuthStore(s => s.user);
  const role = user?.role || 'io';
  const isAdmin = role === 'admin';
  const isShoOrAdmin = role === 'sho' || role === 'admin';

  const fetchDashboard = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const dashboardReq = dashboardService.getOfficerDashboard();
      const requests = [dashboardReq];
      
      if (isShoOrAdmin) {
        requests.push(dashboardService.getAuditLogs({ limit: 20 }));
      }
      
      const results = await Promise.allSettled(requests);
      
      const dashboardRes = results[0];
      if (dashboardRes.status === 'fulfilled' && dashboardRes.value?.success) {
        setData(dashboardRes.value.data);
      } else {
        throw new Error(dashboardRes.reason?.response?.data?.detail || 'Failed to load dashboard');
      }
      
      if (isShoOrAdmin && results[1]?.status === 'fulfilled' && results[1].value?.success) {
        setAuditLogs(results[1].value.data?.logs || []);
      }
    } catch (err) {
      console.error('Dashboard fetch failed:', err);
      setError(err.message || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }, [isShoOrAdmin]);

  useEffect(() => {
    queueMicrotask(fetchDashboard);
  }, [fetchDashboard]);

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

  const handleApprove = async (fir) => {
    if (fir.id?.toString().startsWith('local-')) {
      toast.error('This FIR is saved locally and must be synced to the server before review.');
      return;
    }
    try {
      await firService.review(fir.id, { action: 'approve' });
      toast.success(`FIR ${fir.fir_number} approved`);
      fetchDashboard();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to approve FIR');
    }
  };

  const handleReject = async (fir) => {
    if (fir.id?.toString().startsWith('local-')) {
      toast.error('This FIR is saved locally and must be synced to the server before review.');
      return;
    }
    try {
      await firService.review(fir.id, { action: 'reject', remarks: 'Rejected by Admin Officer' });
      toast.success(`FIR ${fir.fir_number} rejected`);
      fetchDashboard();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to reject FIR');
    }
  };

  const handleSyncLocal = async (fir) => {
    try {
      const dateVal = fir.incident_date || fir.incident_time;
      let parsedIsoDate = new Date().toISOString();
      if (dateVal) {
        const d = new Date(dateVal);
        if (!isNaN(d.getTime())) {
          parsedIsoDate = d.toISOString();
        }
      }

      const res = await firService.submit({
        fir_number: safeStr(fir.fir_number) || `FIR-${Date.now()}`,
        incident_description: safeStr(fir.incident_description || fir.ai_narrative || 'No description provided.'),
        incident_date: parsedIsoDate,
        incident_location: safeStr(fir.incident_location) || 'Pending Location',
        complainant: {
          name: safeStr(fir.complainant?.name) || 'Unknown Complainant',
          contact: safeStr(fir.complainant?.contact || ''),
          address: safeStr(fir.complainant?.address || ''),
          id_number: safeStr(fir.complainant?.id_number || fir.complainant?.id_proof || '')
        },
        sections: (Array.isArray(fir.sections) ? fir.sections : []).map(s => {
          if (!s) return '';
          if (typeof s === 'string') return s;
          if (typeof s === 'object') {
            return s.bns_section || s.section || s.code || s.title || JSON.stringify(s);
          }
          return String(s);
        }).filter(Boolean),
        ai_narrative: fir.ai_narrative || fir.incident_description || ''
      });

      if (res.success) {
        toast.success(`Local FIR ${fir.fir_number} synced to server successfully`);
        deleteFir(fir.id);
        setSelectedFir(null);
        fetchDashboard();
      }
    } catch (err) {
      console.error('Failed to sync local FIR:', err.response?.data || err);
      const detail = err.response?.data?.errors?.[0]?.message || err.response?.data?.message || err.response?.data?.detail || 'Failed to sync local FIR to server';
      toast.error(detail);
    }
  };

  const stats = data?.fir_stats || {};
  const recentFirs = data?.recent_firs || [];
  const pendingApprovals = data?.pending_approvals || [];

  // Merge local submitted FIRs into the dashboard list so they appear immediately
  const localSubmitted = localFirs.filter(f => f.status === 'submitted');
  const mergedRecentFirs = [
    ...localSubmitted,
    ...recentFirs.filter(rf => !localSubmitted.some(lf => lf.fir_number === rf.fir_number))
  ];
  
  const allPendingApprovals = [
    ...localSubmitted,
    ...pendingApprovals.filter(pa => !localSubmitted.some(lf => lf.fir_number === pa.fir_number))
  ];
  const pendingCount = allPendingApprovals.length || stats.submitted || 0;

  // Role label for hero
  const ROLE_LABEL = { admin: 'Admin Officer', sho: 'SHO Officer', io: 'IO Officer' };
  const ROLE_COLOR = { admin: 'text-red-400', sho: 'text-yellow-400', io: 'text-blue-400' };

  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="px-6 py-6 border-b border-border flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <p className={`label-mono mb-1 text-[9px] uppercase tracking-widest ${ROLE_COLOR[role]}`}>
            {ROLE_LABEL[role]} · Active Operations
          </p>
          <h1 className="text-6xl md:text-7xl font-bold tracking-tighter leading-none uppercase text-foreground/90">
            {isAdmin ? 'Command' : isShoOrAdmin ? 'Station HQ' : 'Live Stats'}
          </h1>
        </div>
        <div className="flex items-center gap-3">
          {isAdmin && pendingCount > 0 && (
            <div className="flex items-center gap-2 px-4 py-2 bg-yellow-500/10 border border-yellow-500/30">
              <Shield size={14} className="text-yellow-500" />
              <span className="label-mono text-[9px] text-yellow-500 uppercase font-bold">{pendingCount} pending approval{pendingCount > 1 ? 's' : ''}</span>
            </div>
          )}
          <button
            onClick={fetchDashboard}
            className="label-mono text-[10px] border-2 border-foreground px-4 py-2 hover:bg-accent hover:border-accent hover:text-background transition-all uppercase font-bold"
          >
            Sync System
          </button>
        </div>
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

      {/* Stat Cards — always shown */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total FIRs" value={loading ? '—' : stats.total ?? 0} detail="All records" loading={loading} />
        <StatCard label="Submitted" value={loading ? '—' : stats.submitted ?? 0} detail="Pending review" loading={loading} accent={isAdmin && (stats.submitted ?? 0) > 0} />
        <StatCard label="Approved" value={loading ? '—' : stats.approved ?? 0} detail="Cleared" loading={loading} />
        <StatCard label="Evidence Files" value={loading ? '—' : data?.evidence_count ?? 0} detail="In vault" loading={loading} />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2">
        <StatCard label="Drafts" value={loading ? localDraftCount : (stats.draft ?? 0) + localDraftCount} detail="In progress" loading={false} />
        <StatCard label="Rejected" value={loading ? '—' : stats.rejected ?? 0} detail="Needs revision" loading={loading} />
      </div>

      {/* Role-based Content Tabs (SHO / Admin only) */}
      {isShoOrAdmin && (
        <section className="px-6 pt-8 pb-2 border-b border-border">
          <div className="flex gap-6">
            {[
              { id: 'firs', label: 'Recent FIRs', icon: FileText },
              ...(isAdmin ? [{ id: 'pending', label: `Pending Approval${pendingCount ? ` (${pendingCount})` : ''}`, icon: Shield }] : []),
              { id: 'audit', label: 'Audit Log', icon: ClipboardList },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveSection(tab.id)}
                className={`flex items-center gap-2 pb-3 border-b-2 label-mono text-[10px] uppercase transition-all ${activeSection === tab.id ? 'border-accent text-accent' : 'border-transparent text-muted-foreground hover:text-foreground'}`}
              >
                <tab.icon size={12} />
                {tab.label}
              </button>
            ))}
          </div>
        </section>
      )}

      {/* Main Content Area */}
      <section className="px-6 py-8">
        {/* IO: always shows Recent FIRs */}
        {/* SHO/Admin: tabs switch between views */}
        {(activeSection === 'firs' || !isShoOrAdmin) && (
          <>
            {!isShoOrAdmin && (
              <div className="flex items-end justify-between mb-4">
                <h2 className="text-4xl font-bold tracking-tighter uppercase text-foreground/80">Recent FIRs</h2>
                {error && (
                  <button onClick={fetchDashboard} className="label-mono border-b border-accent/50 pb-0.5 hover:text-accent transition-all text-muted-foreground">Retry</button>
                )}
              </div>
            )}
            {isShoOrAdmin && (
              <div className="flex items-end justify-between mb-4">
                <h2 className="text-3xl font-bold tracking-tighter uppercase text-foreground/80">Station FIR Queue</h2>
              </div>
            )}
            <div className="space-y-0 border-t border-border">
              {loading ? (
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
              ) : mergedRecentFirs.length === 0 ? (
                <div className="py-16 text-center">
                  <FileText size={48} strokeWidth={1} className="text-muted-foreground/20 mx-auto mb-4" />
                  <p className="label-mono text-muted-foreground/40 text-[10px]">No FIRs recorded yet</p>
                </div>
              ) : (
                mergedRecentFirs.map((fir, i) => (
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
                        <p className="text-lg font-bold uppercase tracking-tight">{fir.fir_number || `FIR-${fir.id.slice(0, 8)}`}</p>
                        <p className="label-mono mt-0.5 text-muted-foreground text-[9px]">
                          {fir.complainant?.name ? `${fir.complainant.name} · ` : ''}{formatTimeAgo(fir.created_at)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <StatusBadge status={fir.status} />
                      {isAdmin && (typeof fir.status === 'object' ? fir.status?.value : fir.status) === 'submitted' && (
                        <span className="label-mono text-[7px] text-yellow-500 bg-yellow-500/10 border border-yellow-500/30 px-2 py-0.5 uppercase">Needs Review</span>
                      )}
                      <span className="text-xl group-hover:translate-x-1 transition-transform">→</span>
                    </div>
                  </motion.div>
                ))
              )}
            </div>
          </>
        )}

        {/* Pending Approvals — Admin only */}
        {activeSection === 'pending' && isAdmin && (
          <>
            <div className="flex items-end justify-between mb-4">
              <h2 className="text-3xl font-bold tracking-tighter uppercase text-foreground/80">Pending Approvals</h2>
              <span className="label-mono text-[9px] text-accent">{pendingCount} FIR{pendingCount !== 1 ? 's' : ''} awaiting decision</span>
            </div>
            <PendingApprovalsPanel
              firs={allPendingApprovals}
              onAction={async (fir, action) => {
                if (action === 'approve') await handleApprove(fir);
                else await handleReject(fir);
              }}
            />
          </>
        )}

        {/* Audit Log — SHO + Admin */}
        {activeSection === 'audit' && isShoOrAdmin && (
          <>
            <div className="flex items-end justify-between mb-4">
              <h2 className="text-3xl font-bold tracking-tighter uppercase text-foreground/80">Audit Trail</h2>
              <span className="label-mono text-[9px] text-muted-foreground/50 uppercase">Last 20 events</span>
            </div>
            <AuditLogPanel logs={auditLogs} />
          </>
        )}
      </section>

      {/* FIR Detail Modal */}
      <AnimatePresence>
        {selectedFir && (
          <FIRDetailModal
            fir={selectedFir}
            role={role}
            onClose={() => setSelectedFir(null)}
            onApprove={handleApprove}
            onReject={handleReject}
            onSyncLocal={handleSyncLocal}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
