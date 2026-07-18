import React, { useState, useEffect, useRef } from 'react';
import { Mic, FileText, ArrowRight, Loader2, X, Trash2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import PhoneInput, { isValidPhoneNumber } from 'react-phone-number-input';
import 'react-phone-number-input/style.css';
import { firService, nlpService } from '../services/api';
import useFirStore from '../store/firStore';
import { toast } from 'react-hot-toast';

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

const InputField = ({ label, placeholder, type = "text", multiline = false, fullWidth = false, value, onChange, maxLength }) => (
  <div className={`flex flex-col gap-4 ${fullWidth ? 'md:col-span-2' : ''}`}>
    <label className="label-mono text-[8px] text-muted-foreground">{label}</label>
    {multiline ? (
      <textarea 
        rows={3}
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        maxLength={maxLength}
        className="bg-muted/50 border-none p-3.5 text-sm font-normal tracking-tight focus:outline-none focus:ring-1 focus:ring-accent/40 transition-all placeholder:text-muted-foreground/10"
        placeholder={placeholder}
      />
    ) : (
      <input 
        type={type}
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        maxLength={maxLength}
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
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [audioError, setAudioError] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationError, setGenerationError] = useState('');
  const [draftNarrative, setDraftNarrative] = useState('');
  const [recommendedSections, setRecommendedSections] = useState([]);
  const [isSaving, setIsSaving] = useState(false);
  const [narrative, setNarrative] = useState('');
  const [inputLang, setInputLang] = useState('en');
  const [isTranslating, setIsTranslating] = useState(false);
  const [liveSections, setLiveSections] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  
  const mediaRecorderRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const audioChunksRef = useRef([]);
  const nlpTimerRef = useRef(null);
  
  const [formData, setFormData] = useState({
    complainant_name: '', complainant_contact: '', complainant_address: '',
    complainant_id: '', complainant_id_type: '', incident_location: '', incident_time: ''
  });
  const [selectedFir, setSelectedFir] = useState(null);

  const localFirs = useFirStore(s => s.localFirs);
  const addFir = useFirStore(s => s.addFir);
  const deleteFir = useFirStore(s => s.deleteFir);
  const getNextFirNumber = useFirStore(s => s.getNextFirNumber);
  const clearAll = useFirStore(s => s.clearAll);

  // Merge backend FIRs with local ones on mount
  useEffect(() => {
    // ONE-TIME FINAL WIPE AS REQUESTED BY USER
    const hasCleared = localStorage.getItem('crimegpt_force_wipe_final');
    if (!hasCleared) {
      clearAll();
      localStorage.setItem('crimegpt_force_wipe_final', 'true');
    }
  }, []);

  // Cleanup media streams on unmount
  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current?.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
      mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  // Debounced live BNS section analysis
  useEffect(() => {
    if (nlpTimerRef.current) clearTimeout(nlpTimerRef.current);
    if (narrative.trim().length < 30) {
      setLiveSections([]);
      setIsAnalyzing(false);
      return;
    }
    setIsAnalyzing(true);
    nlpTimerRef.current = setTimeout(async () => {
      try {
        const response = await firService.generate(narrative);
        if (response.success) {
          const sections = response.data?.recommended_sections || [];
          setLiveSections(sections.slice(0, 5));
        }
      } catch {
        // silently fail — live suggestions are best-effort
      } finally {
        setIsAnalyzing(false);
      }
    }, 800);
    return () => { if (nlpTimerRef.current) clearTimeout(nlpTimerRef.current); };
  }, [narrative]);

  // Format ID if type changes
  useEffect(() => {
    if (!formData.complainant_id) return;
    
    if (formData.complainant_id_type === 'Aadhaar Card') {
      const digits = formData.complainant_id.replace(/\D/g, '').slice(0, 12);
      const groups = digits.match(/.{1,4}/g);
      const formatted = groups ? groups.join(' ') : digits;
      if (formatted !== formData.complainant_id) {
        setFormData(prev => ({ ...prev, complainant_id: formatted }));
      }
    } else {
      const limits = {
        'PAN Card': 10,
        'Voter ID': 10,
        'Passport': 8,
        'Driving Licence': 15
      };
      const limit = limits[formData.complainant_id_type];
      if (limit) {
        const formatted = formData.complainant_id.toUpperCase().slice(0, limit);
        if (formatted !== formData.complainant_id) {
          setFormData(prev => ({ ...prev, complainant_id: formatted }));
        }
      }
    }
  }, [formData.complainant_id_type]);

  const getSupportedMimeType = () => {
    if (typeof MediaRecorder === 'undefined') return '';
    const candidates = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus'];
    return candidates.find((type) => MediaRecorder.isTypeSupported(type)) || '';
  };

  const startRecording = async () => {
    setAudioError('');
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      setAudioError('Voice input is not supported in this browser.');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      audioChunksRef.current = [];
      const mimeType = getSupportedMimeType();
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);

      recorder.ondataavailable = (event) => {
        if (event.data?.size > 0) audioChunksRef.current.push(event.data);
      };

      recorder.onerror = () => {
        setAudioError('Audio recording failed. Please try again.');
      };

      recorder.onstop = async () => {
        const chunks = audioChunksRef.current;
        mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
        mediaStreamRef.current = null;
        setIsRecording(false);

        if (!chunks.length) {
          setAudioError('No audio was captured.');
          return;
        }

        setIsTranscribing(true);
        try {
          const audioBlob = new Blob(chunks, { type: recorder.mimeType || 'audio/webm' });
          const response = await nlpService.transcribe(audioBlob, {
            language: inputLang,
            prompt: 'Indian police FIR incident narration with names, locations, dates, and offence details.',
          });
          const transcript = response.data?.text?.trim();
          if (!transcript) {
            setAudioError('No speech was detected in the recording.');
            return;
          }
          setNarrative((current) => [current.trim(), transcript].filter(Boolean).join('\n'));
        } catch (err) {
          setAudioError(err.response?.data?.detail || 'Transcription failed. Check the Groq API key and try again.');
        } finally {
          setIsTranscribing(false);
          audioChunksRef.current = [];
        }
      };

      mediaRecorderRef.current = recorder;
      recorder.start();
      setIsRecording(true);
    } catch (err) {
      setAudioError(err.name === 'NotAllowedError' ? 'Microphone permission was denied.' : 'Unable to access microphone.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
  };

  const handleVoiceInput = () => {
    if (isRecording) stopRecording();
    else startRecording();
  };

  const handleTranslate = async () => {
    if (!narrative.trim() || inputLang === 'en') return;
    setIsTranslating(true);
    try {
      const response = await nlpService.translate(narrative, inputLang, 'en');
      if (response.success && response.data?.translated) {
        setNarrative(response.data.translated);
        setInputLang('en');
        toast.success('TRANSLATED TO ENGLISH');
      }
    } catch (err) {
      toast.error('TRANSLATION FAILED');
    } finally {
      setIsTranslating(false);
    }
  };

  const handleGenerate = async () => {
    if (!narrative.trim()) return;
    setIsGenerating(true);
    setGenerationError('');
    setDraftNarrative('');
    setRecommendedSections([]);
    try {
      const response = await firService.generate(narrative);
      if (response.success) {
        const draft = response.data || {};
        const entities = draft.extracted_entities || {};
        const complainant = draft.suggested_complainant || {};
        const firstLocation = Array.isArray(entities.locations) ? entities.locations[0] : '';
        
        setDraftNarrative(draft.ai_narrative || '');
        setRecommendedSections(draft.recommended_sections || []);
        
        setFormData((current) => ({
          ...current,
          complainant_name: complainant.name || current.complainant_name,
          complainant_contact: complainant.contact || current.complainant_contact,
          complainant_address: complainant.address || current.complainant_address,
          complainant_id: complainant.id_number || current.complainant_id,
          incident_location: firstLocation || current.incident_location,
        }));
        toast.success('FIR DRAFT GENERATED SUCCESSFULLY');
      }
    } catch (err) { 
      console.error("AI Generation Failed", err);
      let errMsg;
      const data = err.response?.data;
      if (!err.response) {
        // Network error — backend not reachable
        errMsg = "Cannot reach the server. Please ensure the backend is running.";
      } else if (err.response.status === 401) {
        errMsg = "Session expired. Please log in again.";
      } else if (err.response.status === 422) {
        // FastAPI Pydantic validation error — detail is an array of objects
        const detail = data?.detail;
        if (Array.isArray(detail)) {
          errMsg = detail.map(d => d.msg || d.message).filter(Boolean).join('; ');
        } else if (typeof detail === 'string') {
          errMsg = detail;
        } else {
          errMsg = "Validation error. Please check your input.";
        }
      } else {
        // Other server errors
        errMsg = data?.message
          || data?.detail
          || data?.errors?.[0]?.message
          || `Server error (${err.response.status}). Please try again.`;
      }
      setGenerationError(errMsg);
      toast.error('AI GENERATION FAILED');
    } finally { 
      setIsGenerating(false); 
    }
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
          id_type: formData.complainant_id_type || '',
          id_proof: formData.complainant_id || '',
        },
      };

      addFir(localFir);
      setNarrative('');
      setFormData({
        complainant_name: '', complainant_contact: '', complainant_address: '',
        complainant_id: '', complainant_id_type: '', incident_location: '', incident_time: ''
      });
      toast.success(`FIR ${localFir.fir_number} SAVED TO VAULT`);

      /* 
      // Best-effort backend sync — Disabled to prevent unintentional record creation
      firService.submit({
        fir_number: localFir.fir_number,
        incident_description: narrative,
        incident_date: formData.incident_time ? new Date(formData.incident_time).toISOString() : new Date().toISOString(),
        incident_location: localFir.incident_location,
        complainant: { name: formData.complainant_name || 'Unknown', contact: formData.complainant_contact || '', address: formData.complainant_address || '', id_number: formData.complainant_id || '' },
        sections: [],
        ai_narrative: narrative
      }).catch(() => {});
      */

    } catch (err) {
      console.error('Failed to save FIR', err);
    } finally {
      setIsSaving(false);
    }
  };

  const updateField = (field, value) => {
    let finalValue = value;
    if (field === 'complainant_id') {
      const type = formData.complainant_id_type;
      if (type === 'Aadhaar Card') {
        const digits = value.replace(/\D/g, '').slice(0, 12);
        const groups = digits.match(/.{1,4}/g);
        finalValue = groups ? groups.join(' ') : digits;
      } else {
        const limits = {
          'PAN Card': 10,
          'Voter ID': 10,
          'Passport': 8,
          'Driving Licence': 15
        };
        const limit = limits[type];
        if (limit) {
          finalValue = value.toUpperCase().slice(0, limit);
        }
      }
    }
    setFormData(prev => ({ ...prev, [field]: finalValue }));
  };

  return (
    <div className="px-6">
      {/* Header */}
      <header className="py-12 md:py-16 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="max-w-3xl">
          <p className="label-mono mb-2 text-accent/70 text-[10px]">Module 01 • Automation</p>
          <h1 className="text-6xl md:text-7xl font-bold tracking-tighter leading-none uppercase text-foreground/90">FIR Draft</h1>
        </div>
        <div className="flex flex-col items-start gap-4">
          {/* Language toggle */}
          <div className="flex gap-1">
            {[{code:'en',label:'EN'},{code:'hi',label:'हि'},{code:'gu',label:'ગુ'}].map(l => (
              <button
                key={l.code}
                onClick={() => setInputLang(l.code)}
                className={`px-3 py-1.5 label-mono text-[9px] font-bold border transition-all ${
                  inputLang === l.code
                    ? 'bg-accent text-background border-accent'
                    : 'border-border text-muted-foreground hover:border-foreground/30'
                }`}
              >{l.label}</button>
            ))}
          </div>
          <button 
            onClick={handleVoiceInput} disabled={isTranscribing}
            className={`flex items-center gap-2 px-6 py-3 font-bold text-base uppercase tracking-tighter transition-all border-2 ${
              isRecording ? 'bg-accent border-accent text-background animate-pulse' : 'bg-background border-foreground/50 text-foreground/80 hover:bg-foreground hover:text-background'
            }`}
          >
            <Mic size={18} />
            {isTranscribing ? 'Transcribing...' : isRecording ? 'Stop Recording' : `Voice (${inputLang.toUpperCase()})`}
          </button>
          {(audioError || isRecording) && (
            <p className={`label-mono text-[9px] ${audioError ? 'text-accent' : 'text-muted-foreground/50'}`}>
              {audioError || 'Recording incident audio. Click stop when finished.'}
            </p>
          )}
        </div>
      </header>

      {/* Narrative */}
      <div className="border-t-4 border-foreground/10 pt-6 pb-8">
        <div className="flex items-center justify-between mb-2">
          <p className="label-mono text-muted-foreground text-[8px]">Incident Narrative (Natural Language Input)</p>
          {inputLang !== 'en' && (
            <button
              onClick={handleTranslate}
              disabled={isTranslating || !narrative.trim()}
              className="flex items-center gap-1.5 label-mono text-[8px] border border-accent/40 text-accent px-3 py-1 hover:bg-accent hover:text-background transition-all disabled:opacity-50"
            >
              {isTranslating ? <><Loader2 size={10} className="animate-spin" /> Translating...</> : <>↔ Translate to English</>}
            </button>
          )}
        </div>
        <textarea 
          value={narrative} onChange={(e) => setNarrative(e.target.value)}
          className="w-full bg-transparent border border-foreground/10 rounded-md p-3 text-lg md:text-xl font-medium tracking-tight placeholder:text-muted-foreground/10 focus:outline-none focus:border-foreground/30 min-h-[120px] leading-relaxed text-foreground/70"
          placeholder={inputLang === 'hi' ? 'घटना का विवरण यहाँ लिखें...' : inputLang === 'gu' ? 'ઘટનાનું વર્ણન અહીં લખો...' : 'Describe the incident in detail. AI will auto-fill structured fields below.'}
        />
        {/* Live BNS section suggestions */}
        <div className="mt-3 min-h-[28px]">
          {isAnalyzing && narrative.trim().length >= 30 && (
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 bg-accent rounded-full animate-pulse" />
              <span className="label-mono text-[8px] text-muted-foreground/50">ANALYSING NARRATIVE FOR BNS SECTIONS...</span>
            </div>
          )}
          {!isAnalyzing && liveSections.length > 0 && (
            <div className="flex flex-wrap gap-2 items-center">
              <span className="label-mono text-[7px] text-muted-foreground/40 uppercase">Suggested:</span>
              {liveSections.map((section) => (
                <button
                  key={section}
                  onClick={() => {
                    if (!recommendedSections.includes(section)) {
                      setRecommendedSections(prev => [...prev, section]);
                    }
                  }}
                  className="label-mono text-[8px] border border-accent/30 text-accent/80 px-2 py-0.5 hover:bg-accent hover:text-background transition-all"
                  title="Click to add to FIR"
                >
                  + {section}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Form Sections */}
      <FormSection id="01" title="Complainant">
        <InputField label="Full Name" placeholder="ENTER NAME" value={formData.complainant_name} onChange={(v) => updateField('complainant_name', v)} />
        <div className="flex flex-col gap-1">
          <label className="label-mono text-[8px] text-muted-foreground">Contact</label>
          <PhoneInput
            international
            withCountryCallingCode
            defaultCountry="IN"
            placeholder="+91 XXXX-XXXXXX"
            value={formData.complainant_contact}
            onChange={(v) => updateField('complainant_contact', v || '')}
            className={`bg-muted/50 border-none p-3.5 text-sm font-normal tracking-tight focus:outline-none focus:ring-1 transition-all text-foreground/80 [&_.PhoneInputInput]:bg-transparent [&_.PhoneInputInput]:border-none [&_.PhoneInputInput]:focus:outline-none [&_.PhoneInputInput]:min-h-[24px] ${
              formData.complainant_contact
                ? isValidPhoneNumber(formData.complainant_contact)
                  ? 'focus:ring-green-500/40'
                  : 'focus:ring-red-500/40'
                : 'focus:ring-accent/40'
            }`}
          />
          {formData.complainant_contact && (
            <p className={`label-mono text-[8px] mt-1 ${
              isValidPhoneNumber(formData.complainant_contact)
                ? 'text-green-500'
                : 'text-red-400'
            }`}>
              {isValidPhoneNumber(formData.complainant_contact)
                ? '✓ Valid number'
                : '✗ Invalid number for selected country'}
            </p>
          )}
        </div>
        <InputField label="Address" placeholder="FULL RESIDENTIAL ADDRESS" fullWidth value={formData.complainant_address} onChange={(v) => updateField('complainant_address', v)} />
        {/* Identity Type + Number */}
        <div className="flex flex-col gap-4">
          <label className="label-mono text-[8px] text-muted-foreground">ID Type</label>
          <select
            value={formData.complainant_id_type}
            onChange={(e) => updateField('complainant_id_type', e.target.value)}
            className="bg-muted/50 border-none p-3.5 text-sm font-normal tracking-tight focus:outline-none focus:ring-1 focus:ring-accent/40 transition-all text-foreground/80"
          >
            <option value="">SELECT TYPE</option>
            <option value="Aadhaar Card">Aadhaar Card</option>
            <option value="PAN Card">PAN Card</option>
            <option value="Voter ID">Voter ID</option>
            <option value="Passport">Passport</option>
            <option value="Driving Licence">Driving Licence</option>
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <InputField 
            label="ID Number" 
            placeholder={
              formData.complainant_id_type === 'Aadhaar Card' ? "0000 0000 0000" : 
              formData.complainant_id_type === 'PAN Card' ? "ABCDE1234F" : 
              formData.complainant_id_type === 'Voter ID' ? "XYZ1234567" :
              formData.complainant_id_type === 'Passport' ? "Z1234567" :
              formData.complainant_id_type === 'Driving Licence' ? "DL-1420110012345" :
              "ENTER ID NUMBER"
            } 
            value={formData.complainant_id} 
            onChange={(v) => updateField('complainant_id', v)} 
            maxLength={
              formData.complainant_id_type === 'Aadhaar Card' ? 14 : 
              formData.complainant_id_type === 'PAN Card' ? 10 : 
              formData.complainant_id_type === 'Voter ID' ? 10 :
              formData.complainant_id_type === 'Passport' ? 8 :
              formData.complainant_id_type === 'Driving Licence' ? 15 :
              undefined
            }
          />
          {formData.complainant_id && formData.complainant_id_type && (
            <p className={`label-mono text-[8px] mt-1 ${
              (() => {
                const type = formData.complainant_id_type;
                const val = formData.complainant_id;
                if (type === 'Aadhaar Card') return val.replace(/\D/g, '').length === 12;
                if (type === 'PAN Card') return val.length === 10;
                if (type === 'Voter ID') return val.length === 10;
                if (type === 'Passport') return val.length === 8;
                if (type === 'Driving Licence') return val.length === 15;
                return true;
              })() ? 'text-green-500' : 'text-red-400'
            }`}>
              {(() => {
                const type = formData.complainant_id_type;
                const val = formData.complainant_id;
                if (type === 'Aadhaar Card') {
                  return val.replace(/\D/g, '').length === 12 ? '✓ Valid Aadhaar format' : `✗ Need ${12 - val.replace(/\D/g, '').length} more digits`;
                }
                const limits = { 'PAN Card': 10, 'Voter ID': 10, 'Passport': 8, 'Driving Licence': 15 };
                const limit = limits[type];
                if (limit) {
                  return val.length === limit ? `✓ Valid ${type} format` : `✗ Need ${limit - val.length} more characters`;
                }
                return null;
              })()}
            </p>
          )}
        </div>
      </FormSection>

      <FormSection id="02" title="Logistics">
        <InputField label="Exact Location" placeholder="CRIME SCENE / LANDMARK" value={formData.incident_location} onChange={(v) => updateField('incident_location', v)} />
        <InputField label="Date & Time" type="datetime-local" value={formData.incident_time} onChange={(v) => updateField('incident_time', v)} />
      </FormSection>
      {generationError && (
        <div className="border border-accent/30 bg-accent/10 p-4 mb-8">
          <p className="label-mono text-[10px] text-accent">{generationError}</p>
        </div>
      )}

      {(draftNarrative || recommendedSections.length > 0) && (
        <section className="border-t border-border py-8 grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-4">
            <span className="label-mono text-[10px] text-accent/70 mb-2 block">AI Output</span>
            <h3 className="text-3xl font-bold tracking-tighter uppercase leading-none text-foreground/80">Draft Review</h3>
          </div>
          <div className="lg:col-span-8 space-y-5">
            {recommendedSections.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {recommendedSections.map((section) => (
                  <span key={section} className="label-mono text-[9px] border border-accent/40 text-accent px-2 py-1">
                    {section}
                  </span>
                ))}
              </div>
            )}
            {draftNarrative && (
              <textarea
                value={draftNarrative}
                onChange={(event) => setDraftNarrative(event.target.value)}
                className="w-full min-h-[220px] bg-muted/40 border border-border p-4 text-sm leading-relaxed text-foreground/80 focus:outline-none focus:border-accent/50"
              />
            )}
          </div>
        </section>
      )}

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
            onClick={handleGenerate} disabled={isGenerating || isRecording || isTranscribing || !narrative.trim()}
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
                  <h2 className="text-3xl font-bold tracking-tighter uppercase">{selectedFir.fir_number || selectedFir.fir_no || 'UNKNOWN'}</h2>
                </div>
                <button onClick={() => setSelectedFir(null)} className="text-muted-foreground hover:text-foreground transition-colors">
                  <X size={20} />
                </button>
              </div>
              <div className="space-y-4 border-t border-border pt-4">
                <div>
                  <p className="label-mono text-[8px] text-muted-foreground mb-1">Status</p>
                  <StatusBadge status={selectedFir.status} />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="label-mono text-[8px] text-muted-foreground mb-1">Complainant</p>
                    <p className="text-sm font-medium">{selectedFir.complainant?.name || '—'}</p>
                  </div>
                  <div>
                    <p className="label-mono text-[8px] text-muted-foreground mb-1">Contact</p>
                    <p className="text-sm font-medium">{selectedFir.complainant?.contact || selectedFir.complainant?.phone || '—'}</p>
                  </div>
                  <div>
                    <p className="label-mono text-[8px] text-muted-foreground mb-1">Address</p>
                    <p className="text-sm font-medium">{selectedFir.complainant?.address || '—'}</p>
                  </div>
                  <div>
                    <p className="label-mono text-[8px] text-muted-foreground mb-1">Identity Proof</p>
                    <p className="text-sm font-medium">{selectedFir.complainant?.id_proof || selectedFir.complainant?.id_number || '—'}</p>
                  </div>
                </div>
                <div>
                  <p className="label-mono text-[8px] text-muted-foreground mb-1">Location</p>
                  <p className="text-sm font-medium">{selectedFir.incident_location || selectedFir.location || '—'}</p>
                </div>
                <div>
                  <p className="label-mono text-[8px] text-muted-foreground mb-1">Filed</p>
                  <p className="text-sm font-medium">{selectedFir.created_at ? new Date(selectedFir.created_at).toLocaleString() : '—'}</p>
                </div>
                <div>
                  <p className="label-mono text-[8px] text-muted-foreground mb-2">Incident Narrative</p>
                  <div className="bg-background/30 p-4 border border-border/40 rounded-sm">
                    <p className="text-sm leading-relaxed text-foreground/80 whitespace-pre-wrap italic">
                      "{selectedFir?.incident_description || selectedFir?.ai_narrative || 'No statement recorded.'}"
                    </p>
                  </div>
                </div>
              </div>
              
              {selectedFir?.sections?.length > 0 && (
                <div className="mt-6">
                  <p className="label-mono text-[8px] text-muted-foreground mb-2 uppercase">Applied Sections</p>
                  <div className="flex flex-wrap gap-2">
                    {selectedFir.sections.map((s, i) => (
                      <span key={i} className="label-mono text-[9px] bg-accent/5 border border-accent/20 text-accent px-2 py-1 uppercase">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}
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
          <div className="flex items-center gap-6">
            {localFirs.length > 0 && (
              <button 
                onClick={() => {
                  if (window.confirm('Are you sure you want to clear all local drafts?')) {
                    localStorage.removeItem('crimegpt_local_firs');
                    localStorage.setItem('crimegpt_fir_counter', '0');
                    window.location.reload();
                  }
                }}
                className="label-mono text-[9px] text-accent border-b border-accent/30 hover:border-accent transition-all uppercase"
              >
                Clear All Drafts
              </button>
            )}
            <span className="label-mono text-[9px] text-muted-foreground/40">{localFirs.length} records</span>
          </div>
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