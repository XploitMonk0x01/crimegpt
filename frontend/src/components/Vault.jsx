import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Database, Upload, Shield, CheckCircle, Eye, Loader2, X, Image as ImageIcon, Tag } from 'lucide-react';
import { evidenceService, firService } from '../services/api';

export default function Vault() {
  const [firs, setFirs] = useState([]);
  const [selectedFirId, setSelectedFirId] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState('');
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
  
  // Gallery state
  const [evidenceList, setEvidenceList] = useState([]);
  const [loadingGallery, setLoadingGallery] = useState(false);

  const isUuid = (value) =>
    /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
      String(value || '').trim()
    );

  const filteredFirs = firs.filter(f => 
    (f.fir_number?.toLowerCase().includes(query.toLowerCase())) ||
    (f.id.toLowerCase().includes(query.toLowerCase()))
  ).slice(0, 10);

  useEffect(() => {
    firService.list({ pageSize: 50 }).then(r => {
      if (r.success) setFirs(r.data || []);
    }).catch(() => {});
  }, []);

  const fetchEvidenceList = async (firId) => {
    if (!firId) {
      setEvidenceList([]);
      return;
    }
    setLoadingGallery(true);
    try {
      const res = await evidenceService.listByFir(firId);
      if (res.success) {
        setEvidenceList(res.data || []);
      }
    } catch (err) {
      console.error("Failed to fetch evidence list:", err);
    } finally {
      setLoadingGallery(false);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file || !isUuid(selectedFirId)) {
      setError('Please select a valid FIR from the list');
      return;
    }
    setUploading(true); setError(''); setUploadResult(null);
    try {
      const r = await evidenceService.upload(file, selectedFirId, description, tags);
      if (r.success) { 
        setUploadResult(r.data); 
        setFile(null); 
        setDescription(''); 
        setTags('');
        // Refresh the gallery
        fetchEvidenceList(selectedFirId);
      }
    } catch (err) { setError(err.response?.data?.detail || 'Upload failed'); }
    finally { setUploading(false); }
  };

  const handleCustody = async () => {
    if (!isUuid(evidenceIdInput)) {
      setCustodyData({ error: 'Please enter a valid Evidence UUID' });
      return;
    }
    setLoadingCustody(true); setCustodyData(null);
    try { const r = await evidenceService.getCustody(evidenceIdInput.trim()); if (r.success) setCustodyData(r.data); }
    catch (err) { setCustodyData({ error: err.response?.data?.detail || 'Not found' }); }
    finally { setLoadingCustody(false); }
  };

  const handleVerify = async () => {
    if (!isUuid(evidenceIdInput)) {
      setVerifyData({ error: 'Please enter a valid Evidence UUID' });
      return;
    }
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
                    setSelectedFirId('');
                    setIsOpen(true);
                  }} 
                  placeholder="Type FIR Number or UUID..." 
                  className={`w-full ${inputCls}`} 
                />
                {query && (
                  <button 
                    type="button"
                    onClick={() => { setQuery(''); setSelectedFirId(''); setIsOpen(false); }}
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
                            setSelectedFirId(f.id);
                            fetchEvidenceList(f.id);
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
              {selectedFirId && (
                <p className="label-mono text-[7px] text-accent mt-1">
                  LINKED ID: {selectedFirId}
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
            <div className="flex flex-col gap-2">
              <label className="label-mono text-[8px] text-muted-foreground/50">Tags (Comma Separated)</label>
              <input type="text" value={tags} onChange={e => setTags(e.target.value)} placeholder="e.g. weapon, blood, screenshot" className={inputCls} />
            </div>
            {error && <p className="label-mono text-[8px] text-accent bg-accent/10 py-2 px-3 animate-pulse uppercase">{error}</p>}
            {uploadResult && (
              <motion.div initial={{opacity:0}} animate={{opacity:1}} className="bg-green-500/10 border border-green-500/30 p-4">
                <div className="flex items-center gap-2"><CheckCircle size={14} className="text-green-500" /><p className="label-mono text-[10px] text-green-500">Uploaded</p></div>
              </motion.div>
            )}
            <button type="submit" disabled={uploading || !file || !isUuid(selectedFirId)} className="flex items-center gap-3 px-8 py-4 bg-accent text-background font-bold text-lg uppercase tracking-tighter hover:bg-foreground transition-all disabled:opacity-50">
              {uploading ? <><span>Uploading...</span><Loader2 size={20} className="animate-spin" /></> : <><span>Upload Evidence</span><Upload size={20} /></>}
            </button>
          </form>
        </div>
      </section>

      {/* Image Gallery */}
      <AnimatePresence>
        {selectedFirId && (
          <motion.section 
            initial={{ opacity: 0, height: 0 }} 
            animate={{ opacity: 1, height: 'auto' }} 
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-border py-8 grid grid-cols-1 lg:grid-cols-12 gap-6 overflow-hidden"
          >
            <div className="lg:col-span-4">
              <span className="label-mono text-[10px] text-accent/70 mb-2 block">Section 01-B</span>
              <h3 className="text-3xl font-bold tracking-tighter uppercase leading-none text-foreground/80 flex items-center gap-3">
                <ImageIcon size={28} /> Evidence Gallery
              </h3>
            </div>
            <div className="lg:col-span-8">
              {loadingGallery ? (
                <div className="flex items-center gap-2 text-muted-foreground/50">
                  <Loader2 size={16} className="animate-spin" />
                  <span className="label-mono text-[10px]">Loading Evidence...</span>
                </div>
              ) : evidenceList.length === 0 ? (
                <div className="p-8 border border-dashed border-border/50 text-center">
                  <p className="label-mono text-muted-foreground/50 text-xs">No evidence found for this FIR.</p>
                </div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {evidenceList.map((item) => {
                    const isImage = item.file_type?.startsWith('image/');
                    return (
                      <div key={item.id} className="border border-border/50 bg-muted/20 group relative overflow-hidden flex flex-col">
                        <div className="aspect-square bg-muted/50 flex items-center justify-center p-2">
                          {isImage ? (
                            <img 
                              src={evidenceService.downloadUrl(item.id)} 
                              alt={item.filename}
                              className="w-full h-full object-contain drop-shadow-lg"
                              loading="lazy"
                            />
                          ) : (
                            <div className="flex flex-col items-center opacity-30">
                              <Shield size={32} />
                              <span className="label-mono text-[8px] mt-2 text-center uppercase tracking-tighter break-all">{item.file_type}</span>
                            </div>
                          )}
                        </div>
                        <div className="p-3 border-t border-border/50 bg-background/50 flex flex-col justify-between flex-grow">
                          <div>
                            <p className="font-bold text-[10px] uppercase truncate" title={item.filename}>{item.filename}</p>
                            <p className="label-mono text-[8px] text-muted-foreground mt-1 line-clamp-2" title={item.description}>{item.description || 'No description'}</p>
                          </div>
                          
                          {item.tags && item.tags.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-3">
                              {item.tags.map((tag, i) => (
                                <span key={i} className="label-mono text-[7px] bg-accent/10 text-accent px-1.5 py-0.5 flex items-center gap-1">
                                  <Tag size={8} /> {tag}
                                </span>
                              ))}
                            </div>
                          )}
                          
                          <div className="flex justify-between items-center mt-3 pt-2 border-t border-border/30">
                            <span className="label-mono text-[7px] text-muted-foreground/50" title={item.id}>ID: {item.id.slice(0, 8)}...</span>
                            <button onClick={() => { setEvidenceIdInput(item.id); setQuery(''); setSelectedFirId(''); setIsOpen(false); }} className="label-mono text-[8px] hover:text-accent transition-colors underline decoration-border underline-offset-2">Verify</button>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </motion.section>
        )}
      </AnimatePresence>

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
