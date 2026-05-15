import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Database, Upload, Shield, CheckCircle, Eye, Loader2, X } from 'lucide-react';
import { evidenceService, firService } from '../services/api';

export default function Vault() {
  const [firs, setFirs] = useState([]);
  const [selectedFir, setSelectedFir] = useState('');
  const [description, setDescription] = useState('');
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState('');
  const [evidenceIdInput, setEvidenceIdInput] = useState('');
  const [custodyData, setCustodyData] = useState(null);
  const [verifyData, setVerifyData] = useState(null);
  const [loadingCustody, setLoadingCustody] = useState(false);
  const [loadingVerify, setLoadingVerify] = useState(false);
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);

  const filteredFirs = firs.filter(f => 
    (f.fir_number?.toLowerCase().includes(query.toLowerCase())) ||
    (f.id.toLowerCase().includes(query.toLowerCase()))
  ).slice(0, 10);

  useEffect(() => {
    firService.list({ pageSize: 50 }).then(r => {
      if (r.success) setFirs(r.data || []);
    }).catch(() => {});
  }, []);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file || !selectedFir) return;
    setUploading(true); setError(''); setUploadResult(null);
    try {
      const r = await evidenceService.upload(file, selectedFir, description);
      if (r.success) { setUploadResult(r.data); setFile(null); setDescription(''); }
    } catch (err) { setError(err.response?.data?.detail || 'Upload failed'); }
    finally { setUploading(false); }
  };

  const handleCustody = async () => {
    if (!evidenceIdInput.trim()) return;
    setLoadingCustody(true); setCustodyData(null);
    try { const r = await evidenceService.getCustody(evidenceIdInput.trim()); if (r.success) setCustodyData(r.data); }
    catch (err) { setCustodyData({ error: err.response?.data?.detail || 'Not found' }); }
    finally { setLoadingCustody(false); }
  };

  const handleVerify = async () => {
    if (!evidenceIdInput.trim()) return;
    setLoadingVerify(true); setVerifyData(null);
    try { const r = await evidenceService.verifyIntegrity(evidenceIdInput.trim()); if (r.success) setVerifyData(r.data); }
    catch (err) { setVerifyData({ error: err.response?.data?.detail || 'Verification failed' }); }
    finally { setLoadingVerify(false); }
  };

  const inputCls = "bg-muted/50 border-none p-3.5 text-sm font-normal tracking-tight focus:outline-none focus:ring-1 focus:ring-accent/40 transition-all placeholder:text-muted-foreground/10 text-foreground/80";

  return (
    <div className="px-6">
      <header className="py-12 md:py-16">
        <p className="label-mono mb-2 text-accent/70 text-[10px]">Module 03 • Secure Storage</p>
        <h1 className="text-6xl md:text-7xl font-bold tracking-tighter leading-none uppercase text-foreground/90">Evidence Vault</h1>
      </header>

      {/* Upload */}
      <section className="border-t border-border py-8 grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-4">
          <span className="label-mono text-[10px] text-accent/70 mb-2 block">Section 01</span>
          <h3 className="text-3xl font-bold tracking-tighter uppercase leading-none text-foreground/80">Upload</h3>
        </div>
        <div className="lg:col-span-8">
          <form onSubmit={handleUpload} className="space-y-6">
            <div className="flex flex-col gap-2 relative">
              <label className="label-mono text-[8px] text-muted-foreground/50">Linked FIR</label>
              <div className="relative">
                <input 
                  type="text" 
                  value={query} 
                  onFocus={() => setIsOpen(true)}
                  onBlur={() => setTimeout(() => setIsOpen(false), 200)}
                  onChange={e => {
                    setQuery(e.target.value);
                    setSelectedFir(e.target.value); 
                    setIsOpen(true);
                  }} 
                  placeholder="Type FIR Number or UUID..." 
                  className={`w-full ${inputCls}`} 
                />
                {query && (
                  <button 
                    type="button"
                    onClick={() => { setQuery(''); setSelectedFir(''); setIsOpen(false); }}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground/30 hover:text-accent transition-colors"
                  >
                    <X size={14} />
                  </button>
                )}
                <AnimatePresence>
                  {isOpen && filteredFirs.length > 0 && (
                    <motion.div 
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="absolute left-0 right-0 top-full mt-1 bg-background border border-border z-50 shadow-2xl max-h-48 overflow-y-auto custom-scrollbar"
                    >
                      {filteredFirs.map(f => (
                        <button
                          key={f.id}
                          type="button"
                          onClick={() => {
                            setQuery(f.fir_number || f.id.slice(0, 8));
                            setSelectedFir(f.id);
                            setIsOpen(false);
                          }}
                          className="w-full text-left px-4 py-3 hover:bg-muted transition-colors border-b border-border/50 last:border-none flex justify-between items-center group"
                        >
                          <div>
                            <p className="font-bold text-xs uppercase tracking-tighter group-hover:text-accent transition-colors">
                              {f.fir_number || 'UNNAMED FIR'}
                            </p>
                            <p className="label-mono text-[8px] text-muted-foreground">
                              {f.id.slice(0, 18)}...
                            </p>
                          </div>
                          <p className="label-mono text-[7px] border border-border px-1.5 py-0.5 opacity-50 group-hover:border-accent group-hover:text-accent transition-all">
                            SELECT
                          </p>
                        </button>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
              {selectedFir && selectedFir !== query && (
                <p className="label-mono text-[7px] text-accent mt-1">
                  LINKED ID: {selectedFir}
                </p>
              )}
            </div>
            <div className="flex flex-col gap-2">
              <label className="label-mono text-[8px] text-muted-foreground/50">Evidence File</label>
              <input type="file" onChange={e => setFile(e.target.files?.[0] || null)} className={`w-full ${inputCls} file:mr-4 file:py-1 file:px-4 file:border-0 file:bg-accent file:text-background file:text-xs file:font-bold file:uppercase file:tracking-wider file:cursor-pointer`} />
            </div>
            <div className="flex flex-col gap-2">
              <label className="label-mono text-[8px] text-muted-foreground/50">Description</label>
              <textarea rows={2} value={description} onChange={e => setDescription(e.target.value)} placeholder="Brief description..." className={inputCls} />
            </div>
            {error && <p className="label-mono text-[8px] text-accent bg-accent/10 py-2 px-3 animate-pulse uppercase">{error}</p>}
            {uploadResult && (
              <motion.div initial={{opacity:0}} animate={{opacity:1}} className="bg-green-500/10 border border-green-500/30 p-4">
                <div className="flex items-center gap-2"><CheckCircle size={14} className="text-green-500" /><p className="label-mono text-[10px] text-green-500">Uploaded</p></div>
              </motion.div>
            )}
            <button type="submit" disabled={uploading || !file || !selectedFir} className="flex items-center gap-3 px-8 py-4 bg-accent text-background font-bold text-lg uppercase tracking-tighter hover:bg-foreground transition-all disabled:opacity-50">
              {uploading ? <><span>Uploading...</span><Loader2 size={20} className="animate-spin" /></> : <><span>Upload Evidence</span><Upload size={20} /></>}
            </button>
          </form>
        </div>
      </section>

      {/* Verify & Track */}
      <section className="border-t border-border py-8 grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-4">
          <span className="label-mono text-[10px] text-accent/70 mb-2 block">Section 02</span>
          <h3 className="text-3xl font-bold tracking-tighter uppercase leading-none text-foreground/80">Verify & Track</h3>
        </div>
        <div className="lg:col-span-8 space-y-6">
          <div className="flex flex-col gap-2">
            <label className="label-mono text-[8px] text-muted-foreground/50">Evidence ID</label>
            <input type="text" value={evidenceIdInput} onChange={e => setEvidenceIdInput(e.target.value)} placeholder="Enter Evidence UUID" className={inputCls} />
          </div>
          <div className="flex gap-4">
            <button onClick={handleCustody} disabled={!evidenceIdInput.trim() || loadingCustody} className="flex items-center gap-2 px-6 py-3 font-bold text-base uppercase tracking-tighter border-2 border-foreground/50 text-foreground/80 hover:bg-foreground hover:text-background transition-all disabled:opacity-50">
              {loadingCustody ? <Loader2 size={16} className="animate-spin" /> : <Eye size={16} />} Custody Chain
            </button>
            <button onClick={handleVerify} disabled={!evidenceIdInput.trim() || loadingVerify} className="flex items-center gap-2 px-6 py-3 font-bold text-base uppercase tracking-tighter border-2 border-foreground/50 text-foreground/80 hover:bg-foreground hover:text-background transition-all disabled:opacity-50">
              {loadingVerify ? <Loader2 size={16} className="animate-spin" /> : <Shield size={16} />} Verify Integrity
            </button>
          </div>
          <AnimatePresence>
            {custodyData && (
              <motion.div initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} exit={{opacity:0}} className="border border-border p-4">
                <p className="label-mono text-[10px] text-accent mb-2">Custody Chain</p>
                {custodyData.error ? <p className="label-mono text-[9px] text-accent/80">{custodyData.error}</p> : <pre className="text-xs text-muted-foreground overflow-auto max-h-40 font-mono">{JSON.stringify(custodyData, null, 2)}</pre>}
              </motion.div>
            )}
          </AnimatePresence>
          <AnimatePresence>
            {verifyData && (
              <motion.div initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} exit={{opacity:0}} className="border border-border p-4">
                <p className="label-mono text-[10px] text-accent mb-2">Integrity Verification</p>
                {verifyData.error ? <p className="label-mono text-[9px] text-accent/80">{verifyData.error}</p> : <pre className="text-xs text-muted-foreground overflow-auto max-h-40 font-mono">{JSON.stringify(verifyData, null, 2)}</pre>}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </section>

      <div className="py-16 border-t border-border flex items-center justify-center gap-4 text-center">
        <Database size={20} strokeWidth={1} className="text-muted-foreground/30" />
        <p className="label-mono text-muted-foreground/40 text-[9px]">ALL EVIDENCE ENCRYPTED AT REST • SHA-256 INTEGRITY HASH • TAMPER-PROOF CUSTODY CHAIN</p>
      </div>
    </div>
  );
}
