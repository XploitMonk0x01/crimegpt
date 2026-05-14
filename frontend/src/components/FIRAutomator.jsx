import React, { useState, useEffect } from 'react';
import { Mic, FileText, ArrowRight, Loader2, X, Trash2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { firService } from '../services/api';
import useFirStore from '../store/firStore';

const FormSection = ({ id, title, children }) => (
  <div className="border-t border-border py-8 grid grid-cols-1 lg:grid-cols-12 gap-6 group">
    <div className="lg:col-span-4">
      <span className="label-mono text-[10px] text-accent/70 mb-2 block">Section {id}</span>
      <h3 className="text-3xl font-bold tracking-tighter uppercase leading-none group-hover:text-accent transition-colors text-foreground/80">
        {title}
      </h3>
    </div>
    <div className="lg:col-span-8 grid grid-cols-1 md:grid-cols-2 gap-12">
      {children}
    </div>
  </div>
);

const InputField = ({ label, placeholder, type = "text", multiline = false, fullWidth = false, value, onChange }) => (
  <div className={`flex flex-col gap-4 ${fullWidth ? 'md:col-span-2' : ''}`}>
    <label className="label-mono text-[8px] text-muted-foreground/50">{label}</label>
    {multiline ? (
      <textarea 
        rows={3}
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        className="bg-muted/50 border-none p-3.5 text-sm font-normal tracking-tight focus:outline-none focus:ring-1 focus:ring-accent/40 transition-all placeholder:text-muted-foreground/10"
        placeholder={placeholder}
      />
    ) : (
      <input 
        type={type}
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        className="bg-muted/50 border-none p-3.5 text-sm font-normal tracking-tight focus:outline-none focus:ring-1 focus:ring-accent/40 transition-all placeholder:text-muted-foreground/10"
        placeholder={placeholder}
      />
    )}
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
      {status || 'draft'}
    </span>
  );
};

function formatTimeAgo(iso) {
  if (!iso) return '';
  const mins = Math.floor((Date.now() - new Date(iso).getTime()) / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function FIRAutomator() {
  const [isRecording, setIsRecording] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [narrative, setNarrative] = useState('');
  const [formData, setFormData] = useState({
    complainant_name: '', complainant_contact: '', complainant_address: '',
    complainant_id: '', incident_location: '', incident_time: ''
  });
  const [loadingFirs, setLoadingFirs] = useState(false);
  const [selectedFir, setSelectedFir] = useState(null);

  const localFirs = useFirStore(s => s.localFirs);
  const addFir = useFirStore(s => s.addFir);
  const deleteFir = useFirStore(s => s.deleteFir);
  const getNextFirNumber = useFirStore(s => s.getNextFirNumber);

  // Merge backend FIRs with local ones on mount
  useEffect(() => {
    const fetchBackend = async () => {
      try {
        const r = await firService.list({ pageSize: 20 });
        if (r.success && r.data?.length > 0) {
          // Backend has real data — could sync here if needed
        }
      } catch { /* backend offline */ }
    };
    fetchBackend();
  }, []);


  const handleGenerate = async () => {
    if (!narrative.trim()) return;
    setIsGenerating(true);
    try {
      const response = await firService.generate(narrative);
      if (response.success) {
        const data = response.data.structured_data || {};
        setFormData({
          complainant_name: data.complainant?.name || '',
          complainant_contact: data.complainant?.contact || '',
          complainant_address: data.complainant?.address || '',
          complainant_id: data.complainant?.id_proof || '',
          incident_location: data.incident?.location || '',
          incident_time: data.incident?.time || ''
        });
        // Refresh list after generation
        firService.list({ pageSize: 10 }).then(r => { if (r.success) setRecentFirs(r.data || []); }).catch(() => {});
      }
    } catch (err) { 
      console.error("AI Generation Failed", err); 
      alert(err.response?.data?.detail?.[0]?.msg || "AI Generation failed. Ensure the narrative is at least 20 characters long.");
    }
    finally { setIsGenerating(false); }
  };

  const handleSave = async () => {
    if (!narrative.trim()) return;
    setIsSaving(true);
    try {
      const localFir = {
        id: `local-${Date.now()}`,
        fir_number: getNextFirNumber(),
        status: 'draft',
        incident_location: formData.incident_location || 'Pending Investigation',
        incident_description: narrative,
        sections: [],
        created_at: new Date().toISOString(),
        complainant: {
          name: formData.complainant_name || 'Unknown',
          contact: formData.complainant_contact || '',
          address: formData.complainant_address || '',
          id_proof: formData.complainant_id || '',
        },
      };

      addFir(localFir);
      setNarrative('');
      setFormData({
        complainant_name: '', complainant_contact: '', complainant_address: '',
        complainant_id: '', incident_location: '', incident_time: ''
      });

      // Best-effort backend sync
      firService.submit({
        fir_number: localFir.fir_number,
        incident_description: narrative,
        incident_date: formData.incident_time ? new Date(formData.incident_time).toISOString() : new Date().toISOString(),
        incident_location: localFir.incident_location,
        complainant: { name: formData.complainant_name || 'Unknown', contact: formData.complainant_contact || '', address: formData.complainant_address || '', id_number: formData.complainant_id || '' },
        sections: [],
        ai_narrative: narrative
      }).catch(() => {});

    } catch (err) {
      console.error('Failed to save FIR', err);
    } finally {
      setIsSaving(false);
    }
  };

  const updateField = (field, value) => setFormData(prev => ({ ...prev, [field]: value }));

  return (
    <div className="px-6">
      {/* Header */}
      <header className="py-12 md:py-16 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="max-w-3xl">
          <p className="label-mono mb-2 text-accent/70 text-[10px]">Module 01 • Automation</p>
          <h1 className="text-6xl md:text-7xl font-bold tracking-tighter leading-none uppercase text-foreground/90">FIR Draft</h1>
        </div>
        <div className="flex flex-col items-start gap-4">
          <button 
            onClick={() => setIsRecording(!isRecording)}
            className={`flex items-center gap-2 px-6 py-3 font-bold text-base uppercase tracking-tighter transition-all border-2 ${
              isRecording ? 'bg-accent border-accent text-background animate-pulse' : 'bg-background border-foreground/50 text-foreground/80 hover:bg-foreground hover:text-background'
            }`}
          >
            <Mic size={18} />
            {isRecording ? 'Listening' : 'Voice Input'}
          </button>
        </div>
      </header>

      {/* Narrative */}
      <div className="border-t-4 border-foreground/10 pt-6 pb-8">
        <p className="label-mono mb-2 text-muted-foreground/40 text-[8px]">Incident Narrative (Natural Language Input)</p>
        <textarea 
          value={narrative} onChange={(e) => setNarrative(e.target.value)}
          className="w-full bg-transparent border border-foreground/10 rounded-md p-3 text-lg md:text-xl font-medium tracking-tight placeholder:text-muted-foreground/10 focus:outline-none focus:border-foreground/30 min-h-[120px] leading-relaxed text-foreground/70"
          placeholder="Describe the incident in detail. AI will auto-fill structured fields below."
        />
      </div>

      {/* Form Sections */}
      <FormSection id="01" title="Complainant">
        <InputField label="Full Name" placeholder="ENTER NAME" value={formData.complainant_name} onChange={(v) => updateField('complainant_name', v)} />
        <InputField label="Contact" placeholder="+91 XXXX-XXXXXX" value={formData.complainant_contact} onChange={(v) => updateField('complainant_contact', v)} />
        <InputField label="Address" placeholder="FULL RESIDENTIAL ADDRESS" fullWidth value={formData.complainant_address} onChange={(v) => updateField('complainant_address', v)} />
        <InputField label="Identity Proof" placeholder="AADHAR / PAN / VOTER ID" value={formData.complainant_id} onChange={(v) => updateField('complainant_id', v)} />
      </FormSection>

      <FormSection id="02" title="Logistics">
        <InputField label="Exact Location" placeholder="CRIME SCENE / LANDMARK" value={formData.incident_location} onChange={(v) => updateField('incident_location', v)} />
        <InputField label="Date & Time" type="datetime-local" value={formData.incident_time} onChange={(v) => updateField('incident_time', v)} />
      </FormSection>

      {/* Actions */}
      <div className="py-16 border-t border-border flex flex-col md:flex-row justify-between items-center gap-12">
        <p className="label-mono max-w-sm text-muted-foreground/40 text-[9px]">
          BY GENERATING THIS DOCUMENT, YOU ACKNOWLEDGE THAT ALL INPUTS ARE VERIFIED PER POLICE PROTOCOL.
        </p>
        <div className="flex gap-8">
          <button 
            onClick={handleSave} 
            disabled={isSaving || !narrative}
            className="label-mono text-base border-b-2 border-border/50 pb-1 hover:border-accent transition-all text-muted-foreground disabled:opacity-50"
          >
            {isSaving ? 'Saving...' : 'Save FIR'}
          </button>
          <button 
            onClick={handleGenerate} disabled={isGenerating || !narrative}
            className="flex items-center gap-3 px-8 py-4 bg-accent text-background font-bold text-lg uppercase tracking-tighter hover:bg-foreground transition-all disabled:opacity-50"
          >
            {isGenerating ? <><span>Analysing...</span><Loader2 size={20} className="animate-spin" /></> : <><span>Generate FIR</span><ArrowRight size={20} /></>}
          </button>
        </div>
      </div>

      {/* FIR Detail Modal */}
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
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              onClick={e => e.stopPropagation()}
              className="bg-muted border border-border w-full max-w-2xl max-h-[80vh] overflow-y-auto p-8"
            >
              <div className="flex items-start justify-between mb-6">
                <div>
                  <p className="label-mono text-[9px] text-accent/70 mb-1">FIR Record</p>
                  <h2 className="text-3xl font-bold tracking-tighter uppercase">{selectedFir.fir_number}</h2>
                </div>
                <button onClick={() => setSelectedFir(null)} className="text-muted-foreground hover:text-foreground transition-colors">
                  <X size={20} />
                </button>
              </div>
              <div className="space-y-4 border-t border-border pt-4">
                <div>
                  <p className="label-mono text-[8px] text-muted-foreground/50 mb-1">Status</p>
                  <StatusBadge status={selectedFir.status} />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="label-mono text-[8px] text-muted-foreground/50 mb-1">Complainant</p>
                    <p className="text-sm font-medium">{selectedFir.complainant?.name || '—'}</p>
                  </div>
                  <div>
                    <p className="label-mono text-[8px] text-muted-foreground/50 mb-1">Contact</p>
                    <p className="text-sm font-medium">{selectedFir.complainant?.contact || '—'}</p>
                  </div>
                  <div>
                    <p className="label-mono text-[8px] text-muted-foreground/50 mb-1">Address</p>
                    <p className="text-sm font-medium">{selectedFir.complainant?.address || '—'}</p>
                  </div>
                  <div>
                    <p className="label-mono text-[8px] text-muted-foreground/50 mb-1">Identity Proof</p>
                    <p className="text-sm font-medium">{selectedFir.complainant?.id_proof || '—'}</p>
                  </div>
                </div>
                <div>
                  <p className="label-mono text-[8px] text-muted-foreground/50 mb-1">Location</p>
                  <p className="text-sm font-medium">{selectedFir.incident_location || '—'}</p>
                </div>
                <div>
                  <p className="label-mono text-[8px] text-muted-foreground/50 mb-1">Filed</p>
                  <p className="text-sm font-medium">{new Date(selectedFir.created_at).toLocaleString()}</p>
                </div>
                <div>
                  <p className="label-mono text-[8px] text-muted-foreground/50 mb-2">Incident Narrative</p>
                  <p className="text-sm leading-relaxed text-foreground/80 whitespace-pre-wrap">{selectedFir.incident_description || selectedFir.ai_narrative || '—'}</p>
                </div>
              </div>
              <div className="mt-8 flex justify-end">
                <button
                  onClick={() => { deleteFir(selectedFir.id); setSelectedFir(null); }}
                  className="flex items-center gap-2 label-mono text-[10px] text-accent border border-accent/40 px-4 py-2 hover:bg-accent hover:text-background transition-all"
                >
                  <Trash2 size={12} /> Delete FIR
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Recent FIRs */}
      <section className="border-t border-border py-8">
        <div className="flex items-end justify-between mb-4">
          <h2 className="text-4xl font-bold tracking-tighter uppercase text-foreground/80">Your FIRs</h2>
          <span className="label-mono text-[9px] text-muted-foreground/40">{localFirs.length} records</span>
        </div>
        <div className="space-y-0 border-t border-border">
          {localFirs.length === 0 ? (
            <div className="py-12 text-center">
              <FileText size={40} strokeWidth={1} className="text-muted-foreground/20 mx-auto mb-3" />
              <p className="label-mono text-muted-foreground/40 text-[10px]">No FIRs yet — generate your first</p>
            </div>
          ) : (
            localFirs.map((fir, i) => (
              <motion.div key={fir.id} initial={{opacity:0}} animate={{opacity:1}} transition={{delay:i*0.04}}
                className="group flex items-center justify-between py-6 border-b border-border hover:bg-muted transition-all px-4 -mx-4"
              >
                <div className="flex items-baseline gap-6 cursor-pointer flex-1" onClick={() => setSelectedFir(fir)}>
                  <span className="label-mono opacity-30 group-hover:opacity-100 group-hover:text-accent">{String(i+1).padStart(2,'0')}</span>
                  <div>
                    <p className="text-base font-bold uppercase tracking-tight">{fir.fir_number || `FIR-${fir.id.slice(0,8)}`}</p>
                    <p className="label-mono mt-0.5 text-muted-foreground text-[8px]">{formatTimeAgo(fir.created_at)}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <StatusBadge status={fir.status} />
                  <button
                    onClick={() => deleteFir(fir.id)}
                    className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-accent transition-all"
                    title="Delete"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </motion.div>
            ))
          )}
        </div>
      </section>
    </div>
  );
}






