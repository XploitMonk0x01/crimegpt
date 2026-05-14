import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link2, Search, Loader2, GitBranch, ArrowRight } from 'lucide-react';
import { caseService, firService } from '../services/api';

export default function CaseLinkage() {
  const [firs, setFirs] = useState([]);
  const [selectedFirId, setSelectedFirId] = useState('');
  const [threshold, setThreshold] = useState(0.7);
  const [similarResults, setSimilarResults] = useState(null);
  const [clusters, setClusters] = useState(null);
  const [loadingSimilar, setLoadingSimilar] = useState(false);
  const [loadingClusters, setLoadingClusters] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    firService.list({ pageSize: 50 }).then(r => {
      if (r.success) setFirs(r.data || []);
    }).catch(() => {});
  }, []);

  const handleFindSimilar = async () => {
    if (!selectedFirId) return;
    setLoadingSimilar(true); setSimilarResults(null); setError('');
    try {
      const r = await caseService.findSimilar(selectedFirId, threshold);
      if (r.success) setSimilarResults(r.data);
    } catch (err) { setError(err.response?.data?.detail || 'Search failed'); }
    finally { setLoadingSimilar(false); }
  };

  const handleGetClusters = async () => {
    setLoadingClusters(true); setClusters(null); setError('');
    try {
      const r = await caseService.getClusters();
      if (r.success) setClusters(r.data);
    } catch (err) { setError(err.response?.data?.detail || 'Cluster fetch failed'); }
    finally { setLoadingClusters(false); }
  };

  const inputCls = "bg-muted/50 border-none p-3.5 text-sm font-normal tracking-tight focus:outline-none focus:ring-1 focus:ring-accent/40 transition-all placeholder:text-muted-foreground/10 text-foreground/80";

  return (
    <div className="px-6">
      <header className="py-12 md:py-16">
        <p className="label-mono mb-2 text-accent/70 text-[10px]">Module 04 • Pattern Detection</p>
        <h1 className="text-6xl md:text-7xl font-bold tracking-tighter leading-none uppercase text-foreground/90">Case Linkage</h1>
      </header>

      {error && (
        <motion.div initial={{opacity:0}} animate={{opacity:1}} className="mb-4 bg-accent/10 border border-accent/30 px-4 py-3">
          <p className="label-mono text-[10px] text-accent">{error}</p>
        </motion.div>
      )}

      {/* Find Similar Cases */}
      <section className="border-t border-border py-8 grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-4">
          <span className="label-mono text-[10px] text-accent/70 mb-2 block">Section 01</span>
          <h3 className="text-3xl font-bold tracking-tighter uppercase leading-none text-foreground/80">Similar Cases</h3>
          <p className="label-mono text-[8px] text-muted-foreground/40 mt-2">AI-powered MO pattern matching across all recorded FIRs</p>
        </div>
        <div className="lg:col-span-8 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex flex-col gap-2">
              <label className="label-mono text-[8px] text-muted-foreground/50">Source FIR</label>
              {firs.length > 0 ? (
                <select value={selectedFirId} onChange={e => setSelectedFirId(e.target.value)} className={inputCls}>
                  <option value="">Select FIR...</option>
                  {firs.map(f => <option key={f.id} value={f.id}>{f.fir_number || f.id.slice(0,8)}</option>)}
                </select>
              ) : (
                <input type="text" value={selectedFirId} onChange={e => setSelectedFirId(e.target.value)} placeholder="Enter FIR UUID" className={inputCls} />
              )}
            </div>
            <div className="flex flex-col gap-2">
              <label className="label-mono text-[8px] text-muted-foreground/50">Threshold ({(threshold * 100).toFixed(0)}%)</label>
              <input type="range" min="0" max="1" step="0.05" value={threshold} onChange={e => setThreshold(parseFloat(e.target.value))} className="w-full accent-accent mt-3" />
            </div>
          </div>
          <button onClick={handleFindSimilar} disabled={!selectedFirId || loadingSimilar} className="flex items-center gap-3 px-8 py-4 bg-accent text-background font-bold text-lg uppercase tracking-tighter hover:bg-foreground transition-all disabled:opacity-50">
            {loadingSimilar ? <><span>Searching...</span><Loader2 size={20} className="animate-spin" /></> : <><span>Find Similar</span><Search size={20} /></>}
          </button>

          <AnimatePresence>
            {similarResults && (
              <motion.div initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} exit={{opacity:0}} className="border border-border p-4">
                <p className="label-mono text-[10px] text-accent mb-3">Results</p>
                {Array.isArray(similarResults) && similarResults.length > 0 ? (
                  <div className="space-y-3">
                    {similarResults.map((item, i) => (
                      <div key={i} className="flex items-center justify-between py-3 border-b border-border/50 last:border-0">
                        <div>
                          <p className="text-sm font-bold uppercase tracking-tight">{item.fir_number || item.id?.slice(0,8)}</p>
                          <p className="label-mono text-[8px] text-muted-foreground">{item.similarity ? `${(item.similarity * 100).toFixed(1)}% match` : ''}</p>
                        </div>
                        <ArrowRight size={14} className="text-muted-foreground" />
                      </div>
                    ))}
                  </div>
                ) : (
                  <pre className="text-xs text-muted-foreground overflow-auto max-h-40 font-mono">{JSON.stringify(similarResults, null, 2)}</pre>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </section>

      {/* MO Clusters */}
      <section className="border-t border-border py-8 grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-4">
          <span className="label-mono text-[10px] text-accent/70 mb-2 block">Section 02</span>
          <h3 className="text-3xl font-bold tracking-tighter uppercase leading-none text-foreground/80">MO Clusters</h3>
          <p className="label-mono text-[8px] text-muted-foreground/40 mt-2">Modus Operandi cluster analysis across linked cases</p>
        </div>
        <div className="lg:col-span-8 space-y-6">
          <button onClick={handleGetClusters} disabled={loadingClusters} className="flex items-center gap-3 px-8 py-4 border-2 border-foreground/50 text-foreground/80 font-bold text-lg uppercase tracking-tighter hover:bg-foreground hover:text-background transition-all disabled:opacity-50">
            {loadingClusters ? <><span>Analysing...</span><Loader2 size={20} className="animate-spin" /></> : <><span>Load Clusters</span><GitBranch size={20} /></>}
          </button>
          <AnimatePresence>
            {clusters && (
              <motion.div initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} exit={{opacity:0}} className="border border-border p-4">
                <p className="label-mono text-[10px] text-accent mb-3">Cluster Data</p>
                <pre className="text-xs text-muted-foreground overflow-auto max-h-60 font-mono">{JSON.stringify(clusters, null, 2)}</pre>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </section>

      <div className="py-16 border-t border-border flex items-center justify-center gap-4 text-center">
        <Link2 size={20} strokeWidth={1} className="text-muted-foreground/30" />
        <p className="label-mono text-muted-foreground/40 text-[9px]">VECTOR SIMILARITY • EMBEDDING-BASED MO ANALYSIS • CROSS-STATION LINKAGE</p>
      </div>
    </div>
  );
}
