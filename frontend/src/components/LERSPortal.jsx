import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Globe, Shield, AlertTriangle, CheckCircle, Copy, Download,
  ChevronDown, Loader2, Send, Wifi, FileText, Clock, RefreshCw,
  MessageCircle, Camera, Hash, Users, Radio, X
} from 'lucide-react';
import toast from 'react-hot-toast';
import { lersService, firService } from '../services/api';

// ─── Platform Config ─────────────────────────────────────────────────────────

const PLATFORMS = [
  {
    id: 'meta',
    label: 'Meta / Facebook',
    color: '#1877F2',
    bg: 'bg-[#1877F2]/10',
    border: 'border-[#1877F2]/30',
    text: 'text-[#1877F2]',
    icon: Users,
    identifierLabel: 'Facebook UID / Profile URL / Email',
  },
  {
    id: 'instagram',
    label: 'Instagram',
    color: '#E1306C',
    bg: 'bg-[#E1306C]/10',
    border: 'border-[#E1306C]/30',
    text: 'text-[#E1306C]',
    icon: Camera,
    identifierLabel: 'Instagram Handle / UID / Email',
  },
  {
    id: 'whatsapp',
    label: 'WhatsApp',
    color: '#25D366',
    bg: 'bg-[#25D366]/10',
    border: 'border-[#25D366]/30',
    text: 'text-[#25D366]',
    icon: MessageCircle,
    identifierLabel: 'WhatsApp Phone Number (with country code)',
  },
  {
    id: 'telegram',
    label: 'Telegram',
    color: '#229ED9',
    bg: 'bg-[#229ED9]/10',
    border: 'border-[#229ED9]/30',
    text: 'text-[#229ED9]',
    icon: Radio,
    identifierLabel: 'Telegram Username / Phone / UID',
  },
  {
    id: 'x',
    label: 'X (Twitter)',
    color: '#ffffff',
    bg: 'bg-white/5',
    border: 'border-white/20',
    text: 'text-white',
    icon: Hash,
    identifierLabel: 'X Handle (@username) / Email / UID',
  },
];

const REQUEST_TYPES = [
  {
    id: 'emergency_disclosure',
    label: 'Emergency Disclosure (EDR)',
    description: 'Imminent threat to life/safety — fastest SLA',
    icon: AlertTriangle,
    urgency: 'emergency',
    color: 'text-red-400',
    border: 'border-red-500/30',
    bg: 'bg-red-500/5',
  },
  {
    id: 'preservation',
    label: 'Account Preservation (APR)',
    description: 'Preserve account data for 90 days pending court order',
    icon: Shield,
    urgency: 'urgent',
    color: 'text-yellow-400',
    border: 'border-yellow-500/30',
    bg: 'bg-yellow-500/5',
  },
  {
    id: 'subscriber_ip',
    label: 'Subscriber & IP Log Request',
    description: 'Subscriber identity & IP access history',
    icon: Globe,
    urgency: 'standard',
    color: 'text-blue-400',
    border: 'border-blue-500/30',
    bg: 'bg-blue-500/5',
  },
];

const IDENTIFIER_TYPES = [
  { id: 'phone', label: 'Phone Number' },
  { id: 'email', label: 'Email Address' },
  { id: 'username', label: 'Username / Handle' },
  { id: 'uid', label: 'Platform UID' },
  { id: 'ip', label: 'IP Address' },
];

const DEFAULT_DATA_BY_TYPE = {
  emergency_disclosure: [
    'Account registration info (name, phone, email)',
    'Real-time IP address and geolocation',
    'Last known login activity',
    'Device identifiers (IMEI, IMSI, MSISDN)',
  ],
  preservation: [
    'All account records (registration, activity, communications metadata)',
    'Preserved for 90 days',
  ],
  subscriber_ip: [
    'Subscriber name and profile details',
    'Registered phone number and email',
    'IP login history (last 90 days)',
    'Device information',
    'Account creation details',
  ],
};

// ─── Sub-Components ───────────────────────────────────────────────────────────

function SelectCard({ items, selected, onSelect, columns = 3 }) {
  return (
    <div className={`grid grid-cols-${columns} gap-3`}>
      {items.map((item) => (
        <button
          key={item.id}
          onClick={() => onSelect(item.id)}
          className={`flex flex-col items-start gap-2 p-4 border transition-all text-left ${
            selected === item.id
              ? `${item.border || 'border-accent'} ${item.bg || 'bg-accent/10'}`
              : 'border-border hover:border-border/80 hover:bg-muted/40'
          }`}
        >
          <div className="flex items-center gap-2 w-full">
            {item.icon && <item.icon size={16} className={selected === item.id ? (item.color || 'text-accent') : 'text-muted-foreground'} />}
            <span className={`label-mono text-[10px] uppercase font-bold tracking-wider ${selected === item.id ? (item.color || 'text-accent') : 'text-foreground'}`}>
              {item.label}
            </span>
            {selected === item.id && <CheckCircle size={12} className={`ml-auto ${item.color || 'text-accent'}`} />}
          </div>
          {item.description && (
            <p className="label-mono text-[8px] text-muted-foreground/60 leading-relaxed">
              {item.description}
            </p>
          )}
        </button>
      ))}
    </div>
  );
}

function PlatformCard({ platform, selected, onSelect }) {
  const Icon = platform.icon;
  return (
    <button
      onClick={() => onSelect(platform.id)}
      className={`flex flex-col items-center gap-3 p-5 border transition-all ${
        selected === platform.id
          ? `${platform.border} ${platform.bg}`
          : 'border-border hover:bg-muted/30'
      }`}
    >
      <Icon size={24} className={selected === platform.id ? platform.text : 'text-muted-foreground'} />
      <span className={`label-mono text-[9px] uppercase font-bold tracking-widest ${selected === platform.id ? platform.text : 'text-muted-foreground'}`}>
        {platform.label}
      </span>
    </button>
  );
}

function TemplateViewer({ result }) {
  const [copied, setCopied] = useState(false);
  const textRef = useRef(null);

  const handleCopy = () => {
    navigator.clipboard.writeText(result.template);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast.success('Template copied to clipboard');
  };

  const handleDownload = () => {
    const blob = new Blob([result.template], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${result.reference_id}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('LERS template downloaded');
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="mt-8 space-y-5"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <p className="label-mono text-[8px] text-muted-foreground/50 uppercase tracking-widest">Generated Request</p>
          <p className="font-bold tracking-tighter text-green-400">{result.reference_id}</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleCopy}
            className="flex items-center gap-2 px-4 py-2 border border-border hover:bg-muted transition-all label-mono text-[9px] uppercase"
          >
            {copied ? <CheckCircle size={12} className="text-green-400" /> : <Copy size={12} />}
            {copied ? 'Copied' : 'Copy'}
          </button>
          <button
            onClick={handleDownload}
            className="flex items-center gap-2 px-4 py-2 border border-accent/40 bg-accent/10 text-accent hover:bg-accent/20 transition-all label-mono text-[9px] uppercase"
          >
            <Download size={12} />
            Download
          </button>
        </div>
      </div>

      {/* Meta Info */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Platform', value: result.platform_info?.full_name },
          { label: 'Request Type', value: result.request_type_label },
          { label: 'SLA', value: result.urgency === 'emergency' ? result.platform_info?.response_sla_emergency : result.platform_info?.response_sla_standard },
        ].map(({ label, value }) => (
          <div key={label} className="border border-border p-3">
            <p className="label-mono text-[8px] text-muted-foreground/50 uppercase">{label}</p>
            <p className="label-mono text-[10px] font-bold mt-1 truncate">{value}</p>
          </div>
        ))}
      </div>

      {/* LERS Portal Link */}
      <div className="flex items-center gap-3 p-3 border border-green-500/20 bg-green-500/5">
        <Wifi size={14} className="text-green-400 shrink-0" />
        <div>
          <p className="label-mono text-[8px] text-muted-foreground/50 uppercase">LERS Portal</p>
          <a
            href={result.platform_info?.lers_portal}
            target="_blank"
            rel="noopener noreferrer"
            className="label-mono text-[10px] text-green-400 hover:underline"
          >
            {result.platform_info?.lers_portal}
          </a>
        </div>
        <div className="ml-auto">
          <span className="label-mono text-[8px] border border-green-500/30 text-green-400 px-2 py-0.5 uppercase">
            Filed — Mock
          </span>
        </div>
      </div>

      {/* Template Text */}
      <div className="border border-border bg-muted/20 relative">
        <div className="flex items-center gap-2 px-4 py-2 border-b border-border">
          <FileText size={12} className="text-muted-foreground/40" />
          <span className="label-mono text-[8px] text-muted-foreground/40 uppercase tracking-widest">LERS Compliant Legal Notice</span>
        </div>
        <pre
          ref={textRef}
          className="p-5 text-[11px] font-mono text-foreground/80 whitespace-pre-wrap break-words leading-relaxed overflow-auto max-h-[500px] custom-scrollbar"
        >
          {result.template}
        </pre>
      </div>
    </motion.div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function LERSPortal() {
  const [step, setStep] = useState(1); // 1: platform, 2: type, 3: details, 4: result
  const [selectedPlatform, setSelectedPlatform] = useState(null);
  const [selectedType, setSelectedType] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const [form, setForm] = useState({
    fir_reference: '',
    target_identifier: '',
    target_identifier_type: 'phone',
    description_of_crime: '',
    section_of_law: 'Section 94 BNSS / Section 91 CrPC',
    station_name: '',
    data_requested: [],
    urgency: 'standard',
  });

  // FIR autocomplete state
  const [firs, setFirs] = useState([]);
  const [firQuery, setFirQuery] = useState('');
  const [firDropdownOpen, setFirDropdownOpen] = useState(false);
  const [selectedFirId, setSelectedFirId] = useState('');

  // Fetch FIRs on mount
  useEffect(() => {
    firService.list({ pageSize: 50 }).then(r => {
      if (r.success) setFirs(r.data || []);
    }).catch(() => {});
  }, []);

  const filteredFirs = firs.filter(f =>
    (f.fir_number?.toLowerCase().includes(firQuery.toLowerCase())) ||
    (f.id.toLowerCase().includes(firQuery.toLowerCase()))
  ).slice(0, 10);

  // Auto-set urgency from request type
  useEffect(() => {
    if (selectedType) {
      const rt = REQUEST_TYPES.find(r => r.id === selectedType);
      if (rt) {
        setForm(f => ({ ...f, urgency: rt.urgency, data_requested: DEFAULT_DATA_BY_TYPE[selectedType] || [] }));
      }
    }
  }, [selectedType]);

  const handleGenerate = async () => {
    if (!selectedPlatform || !selectedType || !form.target_identifier.trim()) {
      toast.error('Please complete all required fields');
      return;
    }

    setLoading(true);
    try {
      const res = await lersService.generate({
        platform: selectedPlatform,
        request_type: selectedType,
        fir_reference: selectedFirId || form.fir_reference || null,
        section_of_law: form.section_of_law,
        target_identifier: form.target_identifier,
        target_identifier_type: form.target_identifier_type,
        description_of_crime: form.description_of_crime,
        data_requested: form.data_requested,
        urgency: form.urgency,
        station_name: form.station_name || null,
      });

      if (res.success) {
        setResult(res.data);
        setStep(4);
        toast.success(`LERS ${res.data.reference_id} generated`);
      }
    } catch (err) {
      toast.error(err.response?.data?.message || 'Failed to generate LERS request');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setStep(1);
    setSelectedPlatform(null);
    setSelectedType(null);
    setResult(null);
    setFirQuery('');
    setSelectedFirId('');
    setFirDropdownOpen(false);
    setForm({
      fir_reference: '',
      target_identifier: '',
      target_identifier_type: 'phone',
      description_of_crime: '',
      section_of_law: 'Section 94 BNSS / Section 91 CrPC',
      station_name: '',
      data_requested: [],
      urgency: 'standard',
    });
  };

  const platInfo = PLATFORMS.find(p => p.id === selectedPlatform);

  return (
    <div className="max-w-4xl mx-auto px-8 py-12 space-y-10">
      {/* Page Header */}
      <div>
        <div className="flex items-center gap-3 mb-2">
          <div className="w-2 h-2 bg-accent" />
          <p className="label-mono text-[9px] tracking-widest text-muted-foreground/50 uppercase">Cyber Crime Wing</p>
        </div>
        <h1 className="text-3xl font-bold tracking-tighter uppercase">LERS Cyber Portal</h1>
        <p className="label-mono text-[10px] text-muted-foreground/60 mt-2 max-w-lg">
          Generate Law Enforcement Request System (LERS) compliant legal notices for Meta, WhatsApp, Instagram, Telegram & X — under Section 94 BNSS / Section 91 CrPC.
        </p>
      </div>

      {/* Legal Disclaimer Banner */}
      <div className="flex items-start gap-3 p-4 border border-yellow-500/20 bg-yellow-500/5">
        <AlertTriangle size={14} className="text-yellow-500 shrink-0 mt-0.5" />
        <p className="label-mono text-[9px] text-yellow-500/70 leading-relaxed">
          This module generates <strong>LERS-compliant mock request templates</strong> for training and demonstration purposes.
          In a live deployment, these requests are submitted through the official LERS portal or via the respective platform's law enforcement portal after proper judicial/supervisory authorization.
        </p>
      </div>

      {/* Progress Stepper */}
      <div className="flex items-center gap-0">
        {['Platform', 'Request Type', 'Target Details', 'Generated Notice'].map((label, i) => (
          <div key={label} className="flex items-center flex-1 last:flex-none">
            <div
              className={`flex items-center gap-2 cursor-pointer ${i + 1 <= step ? 'opacity-100' : 'opacity-30'}`}
              onClick={() => step > i + 1 && setStep(i + 1)}
            >
              <div className={`w-6 h-6 flex items-center justify-center text-[10px] font-bold label-mono border ${i + 1 < step ? 'border-green-500 bg-green-500 text-background' : i + 1 === step ? 'border-accent text-accent' : 'border-border text-muted-foreground'}`}>
                {i + 1 < step ? <CheckCircle size={12} /> : i + 1}
              </div>
              <span className={`label-mono text-[9px] uppercase tracking-widest hidden sm:block ${i + 1 === step ? 'text-foreground' : 'text-muted-foreground/50'}`}>
                {label}
              </span>
            </div>
            {i < 3 && <div className={`flex-1 h-px mx-3 ${i + 1 < step ? 'bg-green-500/40' : 'bg-border'}`} />}
          </div>
        ))}
      </div>

      {/* Step Content */}
      <AnimatePresence mode="wait">
        {/* Step 1: Platform Selection */}
        {step === 1 && (
          <motion.div
            key="step1"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div>
              <p className="label-mono text-[10px] text-muted-foreground/50 uppercase mb-4">Step 1 — Select Target Platform</p>
              <div className="grid grid-cols-5 gap-3">
                {PLATFORMS.map(p => (
                  <PlatformCard key={p.id} platform={p} selected={selectedPlatform} onSelect={setSelectedPlatform} />
                ))}
              </div>
            </div>
            <div className="flex justify-end">
              <button
                disabled={!selectedPlatform}
                onClick={() => setStep(2)}
                className="px-8 py-3 bg-accent text-background label-mono text-[10px] uppercase font-bold hover:opacity-90 transition-all disabled:opacity-30"
              >
                Continue →
              </button>
            </div>
          </motion.div>
        )}

        {/* Step 2: Request Type */}
        {step === 2 && (
          <motion.div
            key="step2"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <p className="label-mono text-[10px] text-muted-foreground/50 uppercase">Step 2 — Select Request Type</p>
            <div className="space-y-3">
              {REQUEST_TYPES.map(rt => (
                <button
                  key={rt.id}
                  onClick={() => setSelectedType(rt.id)}
                  className={`w-full flex items-center gap-4 p-5 border transition-all text-left ${
                    selectedType === rt.id ? `${rt.border} ${rt.bg}` : 'border-border hover:bg-muted/30'
                  }`}
                >
                  <rt.icon size={20} className={selectedType === rt.id ? rt.color : 'text-muted-foreground/40'} />
                  <div className="flex-1">
                    <p className={`label-mono text-[11px] font-bold uppercase tracking-wide ${selectedType === rt.id ? rt.color : 'text-foreground'}`}>
                      {rt.label}
                    </p>
                    <p className="label-mono text-[9px] text-muted-foreground/50 mt-0.5">{rt.description}</p>
                  </div>
                  {selectedType === rt.id && <CheckCircle size={16} className={rt.color} />}
                </button>
              ))}
            </div>
            <div className="flex justify-between">
              <button onClick={() => setStep(1)} className="px-8 py-3 border border-border label-mono text-[10px] uppercase hover:bg-muted transition-all">
                ← Back
              </button>
              <button
                disabled={!selectedType}
                onClick={() => setStep(3)}
                className="px-8 py-3 bg-accent text-background label-mono text-[10px] uppercase font-bold hover:opacity-90 transition-all disabled:opacity-30"
              >
                Continue →
              </button>
            </div>
          </motion.div>
        )}

        {/* Step 3: Target Details */}
        {step === 3 && (
          <motion.div
            key="step3"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <p className="label-mono text-[10px] text-muted-foreground/50 uppercase">Step 3 — Target & Case Details</p>

            <div className="grid grid-cols-2 gap-5">
              {/* Target Identifier */}
              <div className="space-y-2 col-span-2">
                <label className="label-mono text-[9px] text-muted-foreground/50 uppercase">
                  Target Identifier <span className="text-accent">*</span>
                  <span className="ml-2 text-muted-foreground/30 normal-case">{platInfo?.identifierLabel}</span>
                </label>
                <input
                  type="text"
                  value={form.target_identifier}
                  onChange={e => setForm(f => ({ ...f, target_identifier: e.target.value }))}
                  placeholder={platInfo?.identifierLabel || 'Enter identifier...'}
                  className="w-full bg-muted/50 border-none p-3.5 text-sm focus:outline-none focus:ring-1 focus:ring-accent/40 font-mono"
                />
              </div>

              {/* Identifier Type */}
              <div className="space-y-2">
                <label className="label-mono text-[9px] text-muted-foreground/50 uppercase">Identifier Type</label>
                <select
                  value={form.target_identifier_type}
                  onChange={e => setForm(f => ({ ...f, target_identifier_type: e.target.value }))}
                  className="w-full bg-muted/50 border-none p-3.5 text-sm focus:outline-none focus:ring-1 focus:ring-accent/40"
                >
                  {IDENTIFIER_TYPES.map(t => (
                    <option key={t.id} value={t.id}>{t.label}</option>
                  ))}
                </select>
              </div>

              {/* FIR Reference with Autocomplete */}
              <div className="space-y-2 relative">
                <label className="label-mono text-[9px] text-muted-foreground/50 uppercase">FIR Reference No.</label>
                <div className="relative">
                  <input
                    type="text"
                    value={firQuery}
                    onFocus={() => setFirDropdownOpen(true)}
                    onBlur={() => setTimeout(() => setFirDropdownOpen(false), 200)}
                    onChange={e => {
                      setFirQuery(e.target.value);
                      setSelectedFirId('');
                      setForm(f => ({ ...f, fir_reference: '' }));
                      setFirDropdownOpen(true);
                    }}
                    placeholder="Type FIR Number or UUID..."
                    className="w-full bg-muted/50 border-none p-3.5 text-sm focus:outline-none focus:ring-1 focus:ring-accent/40 font-mono"
                  />
                  {firQuery && (
                    <button
                      type="button"
                      onClick={() => { setFirQuery(''); setSelectedFirId(''); setForm(f => ({ ...f, fir_reference: '' })); setFirDropdownOpen(false); }}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground/30 hover:text-accent transition-colors"
                    >
                      <X size={14} />
                    </button>
                  )}
                  <AnimatePresence>
                    {firDropdownOpen && filteredFirs.length > 0 && (
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
                              setForm(fm => ({ ...fm, fir_reference: f.fir_number || f.id }));
                              setFirDropdownOpen(false);
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
                    LINKED: {selectedFirId}
                  </p>
                )}
              </div>

              {/* Station Name */}
              <div className="space-y-2">
                <label className="label-mono text-[9px] text-muted-foreground/50 uppercase">Police Station</label>
                <input
                  type="text"
                  value={form.station_name}
                  onChange={e => setForm(f => ({ ...f, station_name: e.target.value }))}
                  placeholder="e.g. Indore Cyber Crime Cell"
                  className="w-full bg-muted/50 border-none p-3.5 text-sm focus:outline-none focus:ring-1 focus:ring-accent/40 font-mono"
                />
              </div>

              {/* Section of Law */}
              <div className="space-y-2">
                <label className="label-mono text-[9px] text-muted-foreground/50 uppercase">Section of Law</label>
                <input
                  type="text"
                  value={form.section_of_law}
                  onChange={e => setForm(f => ({ ...f, section_of_law: e.target.value }))}
                  className="w-full bg-muted/50 border-none p-3.5 text-sm focus:outline-none focus:ring-1 focus:ring-accent/40 font-mono"
                />
              </div>

              {/* Description */}
              <div className="space-y-2 col-span-2">
                <label className="label-mono text-[9px] text-muted-foreground/50 uppercase">Brief Description of Offence</label>
                <textarea
                  value={form.description_of_crime}
                  onChange={e => setForm(f => ({ ...f, description_of_crime: e.target.value }))}
                  rows={4}
                  placeholder="Briefly describe the cognizable offence under investigation..."
                  className="w-full bg-muted/50 border-none p-3.5 text-sm focus:outline-none focus:ring-1 focus:ring-accent/40 resize-none font-mono"
                />
              </div>

              {/* Data Requested */}
              <div className="space-y-2 col-span-2">
                <label className="label-mono text-[9px] text-muted-foreground/50 uppercase">Data Requested</label>
                <div className="space-y-2">
                  {form.data_requested.map((item, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <span className="label-mono text-[9px] text-accent/60 w-4">{i + 1}.</span>
                      <input
                        value={item}
                        onChange={e => {
                          const updated = [...form.data_requested];
                          updated[i] = e.target.value;
                          setForm(f => ({ ...f, data_requested: updated }));
                        }}
                        className="flex-1 bg-muted/30 border-none p-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-accent/30 font-mono text-[12px]"
                      />
                      <button
                        onClick={() => setForm(f => ({ ...f, data_requested: f.data_requested.filter((_, idx) => idx !== i) }))}
                        className="label-mono text-[9px] text-muted-foreground/40 hover:text-accent transition-colors px-2"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                  <button
                    onClick={() => setForm(f => ({ ...f, data_requested: [...f.data_requested, ''] }))}
                    className="label-mono text-[9px] text-muted-foreground/50 hover:text-accent transition-colors uppercase flex items-center gap-1"
                  >
                    + Add data item
                  </button>
                </div>
              </div>
            </div>

            <div className="flex justify-between">
              <button onClick={() => setStep(2)} className="px-8 py-3 border border-border label-mono text-[10px] uppercase hover:bg-muted transition-all">
                ← Back
              </button>
              <button
                onClick={handleGenerate}
                disabled={loading || !form.target_identifier.trim()}
                className="px-8 py-3 bg-accent text-background label-mono text-[10px] uppercase font-bold hover:opacity-90 transition-all disabled:opacity-30 flex items-center gap-2"
              >
                {loading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
                {loading ? 'Generating...' : 'Generate LERS Notice'}
              </button>
            </div>
          </motion.div>
        )}

        {/* Step 4: Result */}
        {step === 4 && result && (
          <motion.div
            key="step4"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
          >
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <CheckCircle size={18} className="text-green-400" />
                <p className="label-mono text-[11px] text-green-400 uppercase font-bold">LERS Request Generated</p>
              </div>
              <button
                onClick={handleReset}
                className="flex items-center gap-2 px-4 py-2 border border-border label-mono text-[9px] uppercase hover:bg-muted transition-all"
              >
                <RefreshCw size={12} />
                New Request
              </button>
            </div>
            <TemplateViewer result={result} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
