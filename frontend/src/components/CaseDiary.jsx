import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BookOpen, Plus, Trash2, Loader2, X, Clock, ChevronDown } from 'lucide-react';
import { caseDiaryService, firService } from '../services/api';
import useFirStore from '../store/firStore';
import { toast } from 'react-hot-toast';

const ENTRY_ICONS = {
  complaint_received: '📝',
  fir_registered: '📋',
  investigation_started: '🔍',
  witness_examined: '👥',
  evidence_seized: '📦',
  spot_visit: '📍',
  arrest_made: '🔒',
  remand_requested: '⚖️',
  chargesheet_filed: '📑',
  court_hearing: '🏛️',
  other: '📌',
};

const ENTRY_COLORS = {
  complaint_received: 'border-blue-500/40 bg-blue-500/5',
  fir_registered: 'border-accent/40 bg-accent/5',
  investigation_started: 'border-yellow-500/40 bg-yellow-500/5',
  witness_examined: 'border-purple-500/40 bg-purple-500/5',
  evidence_seized: 'border-green-500/40 bg-green-500/5',
  spot_visit: 'border-cyan-500/40 bg-cyan-500/5',
  arrest_made: 'border-red-500/40 bg-red-500/5',
  remand_requested: 'border-orange-500/40 bg-orange-500/5',
  chargesheet_filed: 'border-emerald-500/40 bg-emerald-500/5',
  court_hearing: 'border-indigo-500/40 bg-indigo-500/5',
  other: 'border-border bg-muted/20',
};

function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

function formatTime(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
}

export default function CaseDiary() {
  const [entryTypes, setEntryTypes] = useState([]);
  const [firs, setFirs] = useState([]);
  const [selectedFirId, setSelectedFirId] = useState('');
  const [firQuery, setFirQuery] = useState('');
  const [showFirDropdown, setShowFirDropdown] = useState(false);
  const [diary, setDiary] = useState(null);
  const [loadingDiary, setLoadingDiary] = useState(false);
  const [error, setError] = useState('');

  // New entry form
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    entry_type: 'other',
    title: '',
    description: '',
    entry_date: '',
  });
  const [submitting, setSubmitting] = useState(false);

  const localFirs = useFirStore(s => s.localFirs);

  // Load entry types + FIRs
  useEffect(() => {
    caseDiaryService.getEntryTypes().then(r => {
      if (r.success) setEntryTypes(r.data);
    }).catch(() => {
      // Fallback
      setEntryTypes([
        { type: 'complaint_received', label: 'Complaint Received' },
        { type: 'fir_registered', label: 'FIR Registered' },
        { type: 'investigation_started', label: 'Investigation Started' },
        { type: 'witness_examined', label: 'Witness Examined' },
        { type: 'evidence_seized', label: 'Evidence Seized' },
        { type: 'spot_visit', label: 'Spot Visit / Scene Inspection' },
        { type: 'arrest_made', label: 'Arrest Made' },
        { type: 'remand_requested', label: 'Remand Requested' },
        { type: 'chargesheet_filed', label: 'Chargesheet Filed' },
        { type: 'court_hearing', label: 'Court Hearing' },
        { type: 'other', label: 'Other' },
      ]);
    });

    firService.list({ pageSize: 50 }).then(r => {
      if (r.success) setFirs(r.data || []);
    }).catch(() => {});
  }, []);

  const allFirs = [
    ...firs,
    ...localFirs.filter(lf => !firs.some(f => f.id === lf.id)),
  ];

  const filteredFirs = allFirs.filter(f =>
    (f.fir_number?.toLowerCase().includes(firQuery.toLowerCase())) ||
    (f.id?.toLowerCase().includes(firQuery.toLowerCase()))
  ).slice(0, 10);

  const loadDiary = async (firId) => {
    if (!firId) return;
    setLoadingDiary(true);
    setError('');
    setDiary(null);
    try {
      const r = await caseDiaryService.getDiary(firId);
      if (r.success) setDiary(r.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load case diary');
    } finally {
      setLoadingDiary(false);
    }
  };

  const handleSelectFir = (f) => {
    setFirQuery(f.fir_number || f.id.slice(0, 8));
    setSelectedFirId(f.id);
    setShowFirDropdown(false);
    loadDiary(f.id);
  };

  const handleAddEntry = async (e) => {
    e.preventDefault();
    if (!formData.title.trim() || !selectedFirId) return;
    setSubmitting(true);

    try {
      const payload = {
        entry_type: formData.entry_type,
        title: formData.title,
        description: formData.description || null,
        entry_date: formData.entry_date ? new Date(formData.entry_date).toISOString() : null,
      };
      const r = await caseDiaryService.addEntry(selectedFirId, payload);
      if (r.success) {
        toast.success('DIARY ENTRY ADDED');
        setFormData({ entry_type: 'other', title: '', description: '', entry_date: '' });
        setShowForm(false);
        await loadDiary(selectedFirId);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to add entry');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteEntry = async (entryId) => {
    if (!window.confirm('Delete this diary entry?')) return;
    try {
      await caseDiaryService.deleteEntry(entryId);
      toast.success('ENTRY DELETED');
      await loadDiary(selectedFirId);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete');
    }
  };

  const inputCls = "bg-muted/50 border-none p-3.5 text-sm font-normal tracking-tight focus:outline-none focus:ring-1 focus:ring-accent/40 transition-all placeholder:text-muted-foreground/10 text-foreground/80";

  return (
    <div className="px-6">
      {/* Header */}
      <header className="py-12 md:py-16">
        <p className="label-mono mb-2 text-accent/70 text-[10px]">Module 06 • Investigation Log</p>
        <h1 className="text-6xl md:text-7xl font-bold tracking-tighter leading-none uppercase text-foreground/90">
          Case Diary
        </h1>
        <p className="label-mono text-[9px] text-muted-foreground/40 mt-4 max-w-lg">
          Maintain a timeline-based case diary from initial complaint to arrest. Track every investigative step with structured entries.
        </p>
      </header>

      {/* FIR Selector */}
      <section className="border-t border-border py-8 grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-4">
          <span className="label-mono text-[10px] text-accent/70 mb-2 block">Section 01</span>
          <h3 className="text-3xl font-bold tracking-tighter uppercase leading-none text-foreground/80">Select FIR</h3>
        </div>
        <div className="lg:col-span-8">
          <div className="flex flex-col gap-2 relative">
            <label className="label-mono text-[8px] text-muted-foreground/50">Case FIR</label>
            <div className="relative">
              <input
                type="text"
                value={firQuery}
                onFocus={() => setShowFirDropdown(true)}
                onBlur={() => setTimeout(() => setShowFirDropdown(false), 200)}
                onChange={e => { setFirQuery(e.target.value); setSelectedFirId(''); setShowFirDropdown(true); }}
                placeholder="Type FIR Number or UUID..."
                className={`w-full ${inputCls}`}
              />
              {firQuery && (
                <button
                  type="button"
                  onClick={() => { setFirQuery(''); setSelectedFirId(''); setShowFirDropdown(false); setDiary(null); }}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground/30 hover:text-accent transition-colors"
                >
                  <X size={14} />
                </button>
              )}
              <AnimatePresence>
                {showFirDropdown && filteredFirs.length > 0 && (
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
                        onClick={() => handleSelectFir(f)}
                        className="w-full text-left px-4 py-3 hover:bg-muted transition-colors border-b border-border/50 last:border-none flex justify-between items-center group"
                      >
                        <div>
                          <p className="font-bold text-xs uppercase tracking-tighter group-hover:text-accent transition-colors">
                            {f.fir_number || 'UNNAMED FIR'}
                          </p>
                          <p className="label-mono text-[8px] text-muted-foreground">{f.id.slice(0, 18)}...</p>
                        </div>
                        <p className="label-mono text-[7px] border border-border px-1.5 py-0.5 opacity-50 group-hover:border-accent group-hover:text-accent transition-all">SELECT</p>
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
            {selectedFirId && (
              <p className="label-mono text-[7px] text-accent mt-1">LINKED: {selectedFirId}</p>
            )}
          </div>
        </div>
      </section>

      {error && (
        <div className="border border-accent/30 bg-accent/10 p-4 mb-4">
          <p className="label-mono text-[10px] text-accent">{error}</p>
        </div>
      )}

      {/* Timeline */}
      {selectedFirId && (
        <section className="border-t border-border py-8">
          <div className="flex items-end justify-between mb-6">
            <div>
              <span className="label-mono text-[10px] text-accent/70 mb-2 block">Section 02</span>
              <h3 className="text-3xl font-bold tracking-tighter uppercase leading-none text-foreground/80">
                Timeline
              </h3>
              {diary && (
                <p className="label-mono text-[9px] text-muted-foreground/40 mt-2">
                  {diary.fir_number} • {diary.total_entries} entries
                </p>
              )}
            </div>
            <button
              onClick={() => setShowForm(!showForm)}
              className="flex items-center gap-2 px-6 py-3 font-bold text-base uppercase tracking-tighter border-2 border-foreground/50 text-foreground/80 hover:bg-foreground hover:text-background transition-all"
            >
              <Plus size={16} />
              Add Entry
            </button>
          </div>

          {/* Add Entry Form */}
          <AnimatePresence>
            {showForm && (
              <motion.form
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                onSubmit={handleAddEntry}
                className="border border-accent/30 bg-accent/5 p-6 mb-8 space-y-4 overflow-hidden"
              >
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex flex-col gap-2">
                    <label className="label-mono text-[8px] text-muted-foreground/50">Entry Type</label>
                    <select
                      value={formData.entry_type}
                      onChange={e => setFormData(prev => ({ ...prev, entry_type: e.target.value }))}
                      className={inputCls}
                    >
                      {entryTypes.map(t => (
                        <option key={t.type} value={t.type}>{t.label}</option>
                      ))}
                    </select>
                  </div>
                  <div className="flex flex-col gap-2">
                    <label className="label-mono text-[8px] text-muted-foreground/50">Date & Time</label>
                    <input
                      type="datetime-local"
                      value={formData.entry_date}
                      onChange={e => setFormData(prev => ({ ...prev, entry_date: e.target.value }))}
                      className={inputCls}
                    />
                  </div>
                </div>
                <div className="flex flex-col gap-2">
                  <label className="label-mono text-[8px] text-muted-foreground/50">Title</label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={e => setFormData(prev => ({ ...prev, title: e.target.value }))}
                    placeholder="Brief summary of the action taken..."
                    className={inputCls}
                    required
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <label className="label-mono text-[8px] text-muted-foreground/50">Description (Optional)</label>
                  <textarea
                    rows={3}
                    value={formData.description}
                    onChange={e => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="Detailed notes about the investigative action..."
                    className={inputCls}
                  />
                </div>
                <div className="flex gap-4">
                  <button
                    type="submit"
                    disabled={submitting || !formData.title.trim()}
                    className="flex items-center gap-3 px-8 py-3 bg-accent text-background font-bold text-base uppercase tracking-tighter hover:bg-foreground transition-all disabled:opacity-50"
                  >
                    {submitting ? <><span>Saving...</span><Loader2 size={16} className="animate-spin" /></> : <><span>Save Entry</span><Plus size={16} /></>}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowForm(false)}
                    className="label-mono text-[10px] text-muted-foreground hover:text-foreground transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </motion.form>
            )}
          </AnimatePresence>

          {/* Loading */}
          {loadingDiary && (
            <div className="py-12 text-center">
              <Loader2 size={24} className="animate-spin text-accent mx-auto mb-3" />
              <p className="label-mono text-[10px] text-muted-foreground/40">Loading case diary...</p>
            </div>
          )}

          {/* Empty state */}
          {diary && diary.entries?.length === 0 && !loadingDiary && (
            <div className="py-16 text-center">
              <BookOpen size={40} strokeWidth={1} className="text-muted-foreground/20 mx-auto mb-3" />
              <p className="label-mono text-muted-foreground/40 text-[10px]">No diary entries yet — add the first entry above</p>
            </div>
          )}

          {/* Timeline entries */}
          {diary && diary.entries?.length > 0 && (
            <div className="relative pl-8">
              {/* Vertical line */}
              <div className="absolute left-3 top-0 bottom-0 w-px bg-border" />

              <div className="space-y-0">
                {diary.entries.map((entry, i) => (
                  <motion.div
                    key={entry.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="relative group"
                  >
                    {/* Dot on timeline */}
                    <div className="absolute -left-8 top-5 w-6 h-6 flex items-center justify-center z-10">
                      <div className="w-3 h-3 bg-accent border-2 border-background group-hover:scale-125 transition-transform" />
                    </div>

                    <div className={`border-l-2 ml-0 p-5 mb-4 transition-all hover:bg-muted/30 ${ENTRY_COLORS[entry.entry_type] || ENTRY_COLORS.other}`}>
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3">
                          <span className="text-lg">{ENTRY_ICONS[entry.entry_type] || '📌'}</span>
                          <div>
                            <p className="text-sm font-bold uppercase tracking-tight text-foreground/90">
                              {entry.title}
                            </p>
                            <div className="flex items-center gap-3 mt-1">
                              <span className="label-mono text-[8px] text-accent/70">
                                {entryTypes.find(t => t.type === entry.entry_type)?.label || entry.entry_type}
                              </span>
                              <span className="label-mono text-[8px] text-muted-foreground/40 flex items-center gap-1">
                                <Clock size={9} />
                                {formatDate(entry.entry_date)} {formatTime(entry.entry_date)}
                              </span>
                            </div>
                          </div>
                        </div>
                        <button
                          onClick={() => handleDeleteEntry(entry.id)}
                          className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-accent transition-all p-1"
                          title="Delete entry"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                      {entry.description && (
                        <p className="mt-3 text-sm leading-relaxed text-foreground/70 pl-9">
                          {entry.description}
                        </p>
                      )}
                      {entry.officer_badge && (
                        <p className="label-mono text-[7px] text-muted-foreground/30 mt-2 pl-9">
                          Logged by: {entry.officer_name || entry.officer_badge}
                        </p>
                      )}
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      {/* Footer */}
      <div className="py-16 border-t border-border flex items-center justify-center gap-4 text-center">
        <BookOpen size={20} strokeWidth={1} className="text-muted-foreground/30" />
        <p className="label-mono text-muted-foreground/40 text-[9px]">
          TIMELINE-BASED DIARY • FIR TO ARREST • 11 ENTRY TYPES • AUDIT LOGGED
        </p>
      </div>
    </div>
  );
}
