import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FileText, Download, Loader2, ChevronDown, X, ArrowRight, Languages } from 'lucide-react';
import { documentService, firService } from '../services/api';
import useFirStore from '../store/firStore';
import { toast } from 'react-hot-toast';

const DOC_ICONS = {
  chargesheet: '📋',
  medical_letter: '🏥',
  remand_request: '⚖️',
  seizure_receipt: '📦',
  court_custody_letter: '🏛️',
  accused_panchanama: '🔒',
  face_id_form: '👤',
};

export default function DocumentGenerator() {
  const [docTypes, setDocTypes] = useState([]);
  const [selectedType, setSelectedType] = useState('');
  const [selectedFirId, setSelectedFirId] = useState('');
  const [language, setLanguage] = useState('en');
  const [additionalContext, setAdditionalContext] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedDoc, setGeneratedDoc] = useState(null);
  const [error, setError] = useState('');
  const [firs, setFirs] = useState([]);
  const [firQuery, setFirQuery] = useState('');
  const [showFirDropdown, setShowFirDropdown] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const localFirs = useFirStore(s => s.localFirs);

  // Load document types
  useEffect(() => {
    documentService.getTypes().then(r => {
      if (r.success) setDocTypes(r.data);
    }).catch(() => {
      // Fallback types when backend is unavailable
      setDocTypes([
        { type: 'chargesheet', label: 'Purvani Chargesheet', description: 'Preliminary chargesheet compiling all case data', icon: '📋' },
        { type: 'medical_letter', label: 'Medical Treatment Letter', description: 'Referral letter for victim medical examination', icon: '🏥' },
        { type: 'remand_request', label: 'Remand Request Letter', description: 'Police custody remand application to Magistrate', icon: '⚖️' },
        { type: 'seizure_receipt', label: 'Seizure Receipt', description: 'Receipt for seized evidence items', icon: '📦' },
        { type: 'court_custody_letter', label: 'Court Custody Letter', description: 'Judicial custody transfer application', icon: '🏛️' },
        { type: 'accused_panchanama', label: 'Accused Arrest Panchanama', description: 'Formal arrest documentation', icon: '🔒' },
        { type: 'face_id_form', label: 'Face Identification Form', description: 'TIP form for accused identification', icon: '👤' },
      ]);
    });
  }, []);

  // Load FIRs from backend
  useEffect(() => {
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

  const isUuid = (value) =>
    /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
      String(value || '').trim()
    );

  const handleGenerate = async () => {
    if (!selectedFirId || !selectedType) return;
    setIsGenerating(true);
    setError('');
    setGeneratedDoc(null);

    try {
      const response = await documentService.generate(selectedFirId, selectedType, {
        language,
        additionalContext: additionalContext || undefined,
      });
      if (response.success) {
        setGeneratedDoc(response.data);
        toast.success(`${response.data.title} GENERATED`);
      }
    } catch (err) {
      const msg = err.response?.data?.detail || 'Document generation failed';
      setError(msg);
      toast.error('GENERATION FAILED');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleExportPdf = async () => {
    if (!generatedDoc) return;
    setIsExporting(true);
    try {
      const blob = await documentService.exportPdf({
        document_type: generatedDoc.document_type,
        title: generatedDoc.title,
        content: generatedDoc.content,
        metadata: generatedDoc.metadata || {},
        fir_number: generatedDoc.fir_number,
      });
      const url = URL.createObjectURL(new Blob([blob], { type: 'application/pdf' }));
      const a = document.createElement('a');
      a.href = url;
      a.download = `${generatedDoc.document_type}_${generatedDoc.fir_number || 'doc'}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success('PDF EXPORTED');
    } catch {
      toast.error('PDF EXPORT FAILED');
    } finally {
      setIsExporting(false);
    }
  };

  const inputCls = "bg-muted/50 border-none p-3.5 text-sm font-normal tracking-tight focus:outline-none focus:ring-1 focus:ring-accent/40 transition-all placeholder:text-muted-foreground/10 text-foreground/80";

  return (
    <div className="px-6">
      {/* Header */}
      <header className="py-12 md:py-16">
        <p className="label-mono mb-2 text-accent/70 text-[10px]">Module 05 • Document Engine</p>
        <h1 className="text-6xl md:text-7xl font-bold tracking-tighter leading-none uppercase text-foreground/90">
          Doc Generator
        </h1>
        <p className="label-mono text-[9px] text-muted-foreground/40 mt-4 max-w-lg">
          Auto-generate 7 types of legal documents from existing FIR data using AI. Each document follows Indian criminal procedure standards (BNS/BNSS/BSA 2023).
        </p>
      </header>

      {/* Document Type Selector */}
      <section className="border-t border-border py-8 grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-4">
          <span className="label-mono text-[10px] text-accent/70 mb-2 block">Section 01</span>
          <h3 className="text-3xl font-bold tracking-tighter uppercase leading-none text-foreground/80">Select Document</h3>
        </div>
        <div className="lg:col-span-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {docTypes.map((dt) => (
              <button
                key={dt.type}
                onClick={() => setSelectedType(dt.type)}
                className={`text-left p-4 border transition-all group ${
                  selectedType === dt.type
                    ? 'border-accent bg-accent/10'
                    : 'border-border hover:border-foreground/30 hover:bg-muted/30'
                }`}
              >
                <div className="flex items-start gap-3">
                  <span className="text-xl">{DOC_ICONS[dt.type] || '📄'}</span>
                  <div>
                    <p className={`text-sm font-bold uppercase tracking-tight ${
                      selectedType === dt.type ? 'text-accent' : 'text-foreground/80 group-hover:text-foreground'
                    }`}>
                      {dt.label}
                    </p>
                    <p className="label-mono text-[7px] text-muted-foreground/50 mt-1">
                      {dt.description}
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* FIR Selector + Options */}
      <section className="border-t border-border py-8 grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-4">
          <span className="label-mono text-[10px] text-accent/70 mb-2 block">Section 02</span>
          <h3 className="text-3xl font-bold tracking-tighter uppercase leading-none text-foreground/80">Configuration</h3>
        </div>
        <div className="lg:col-span-8 space-y-6">
          {/* FIR Selector */}
          <div className="flex flex-col gap-2 relative">
            <label className="label-mono text-[8px] text-muted-foreground/50">Source FIR</label>
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
                  onClick={() => { setFirQuery(''); setSelectedFirId(''); setShowFirDropdown(false); }}
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
                        onClick={() => {
                          setFirQuery(f.fir_number || f.id.slice(0, 8));
                          setSelectedFirId(f.id);
                          setShowFirDropdown(false);
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
              <p className="label-mono text-[7px] text-accent mt-1">LINKED ID: {selectedFirId}</p>
            )}
          </div>

          {/* Language */}
          <div className="flex flex-col gap-2">
            <label className="label-mono text-[8px] text-muted-foreground/50">Output Language</label>
            <div className="flex gap-3">
              {[
                { code: 'en', label: 'English' },
                { code: 'hi', label: 'हिन्दी' },
                { code: 'gu', label: 'ગુજરાતી' },
              ].map(lang => (
                <button
                  key={lang.code}
                  onClick={() => setLanguage(lang.code)}
                  className={`px-4 py-2 text-sm font-bold uppercase tracking-tight border transition-all flex items-center gap-2 ${
                    language === lang.code
                      ? 'border-accent bg-accent/10 text-accent'
                      : 'border-border text-muted-foreground hover:border-foreground/30'
                  }`}
                >
                  <Languages size={14} />
                  {lang.label}
                </button>
              ))}
            </div>
          </div>

          {/* Additional context */}
          <div className="flex flex-col gap-2">
            <label className="label-mono text-[8px] text-muted-foreground/50">Additional Context (Optional)</label>
            <textarea
              rows={3}
              value={additionalContext}
              onChange={e => setAdditionalContext(e.target.value)}
              placeholder="Any officer notes, additional details, or context for the document..."
              className={inputCls}
            />
          </div>
        </div>
      </section>

      {/* Error */}
      {error && (
        <div className="border border-accent/30 bg-accent/10 p-4 mb-8">
          <p className="label-mono text-[10px] text-accent">{error}</p>
        </div>
      )}

      {/* Generate Button */}
      <div className="py-8 border-t border-border flex flex-col md:flex-row justify-between items-center gap-12">
        <p className="label-mono max-w-sm text-muted-foreground/40 text-[9px]">
          DOCUMENTS ARE AI-GENERATED AND MUST BE REVIEWED BY THE INVESTIGATING OFFICER BEFORE OFFICIAL USE.
        </p>
        <button
          onClick={handleGenerate}
          disabled={isGenerating || !selectedType || !selectedFirId}
          className="flex items-center gap-3 px-8 py-4 bg-accent text-background font-bold text-lg uppercase tracking-tighter hover:bg-foreground transition-all disabled:opacity-50"
        >
          {isGenerating ? (
            <><span>Generating...</span><Loader2 size={20} className="animate-spin" /></>
          ) : (
            <><span>Generate Document</span><ArrowRight size={20} /></>
          )}
        </button>
      </div>

      {/* Generated Document Preview */}
      <AnimatePresence>
        {generatedDoc && (
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="border-t-4 border-accent py-8"
          >
            <div className="flex items-start justify-between mb-6">
              <div>
                <span className="label-mono text-[10px] text-accent/70 mb-2 block">Generated Output</span>
                <h3 className="text-3xl font-bold tracking-tighter uppercase leading-none text-foreground/80">
                  {generatedDoc.title}
                </h3>
                <div className="flex items-center gap-4 mt-2">
                  {generatedDoc.fir_number && (
                    <span className="label-mono text-[9px] border border-border px-2 py-0.5">
                      FIR: {generatedDoc.fir_number}
                    </span>
                  )}
                  <span className="label-mono text-[9px] text-muted-foreground/40">
                    {generatedDoc.language === 'hi' ? 'हिन्दी' : generatedDoc.language === 'gu' ? 'ગુજરાતી' : 'English'}
                  </span>
                </div>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={handleExportPdf}
                  disabled={isExporting}
                  className="flex items-center gap-2 px-6 py-3 font-bold text-base uppercase tracking-tighter border-2 border-foreground/50 text-foreground/80 hover:bg-foreground hover:text-background transition-all disabled:opacity-50"
                >
                  {isExporting ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
                  Export PDF
                </button>
                <button
                  onClick={() => setGeneratedDoc(null)}
                  className="p-3 text-muted-foreground hover:text-accent transition-colors"
                >
                  <X size={20} />
                </button>
              </div>
            </div>

            {/* Legal sections used */}
            {generatedDoc.sections_used?.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-4">
                {generatedDoc.sections_used.map((section, i) => (
                  <span key={i} className="label-mono text-[9px] border border-accent/40 text-accent px-2 py-1">
                    {section}
                  </span>
                ))}
              </div>
            )}

            {/* Document Content */}
            <div className="bg-muted/40 border border-border p-6 max-h-[60vh] overflow-y-auto custom-scrollbar">
              <pre className="whitespace-pre-wrap text-sm leading-relaxed text-foreground/80 font-sans">
                {generatedDoc.content}
              </pre>
            </div>
          </motion.section>
        )}
      </AnimatePresence>

      {/* Footer */}
      <div className="py-16 border-t border-border flex items-center justify-center gap-4 text-center">
        <FileText size={20} strokeWidth={1} className="text-muted-foreground/30" />
        <p className="label-mono text-muted-foreground/40 text-[9px]">
          7 DOCUMENT TYPES • AI-POWERED DRAFTING • BNS/BNSS/BSA 2023 COMPLIANT • PDF EXPORT
        </p>
      </div>
    </div>
  );
}
