import React, { useState } from 'react';
import { Mic, FileText, ArrowRight, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { firService } from '../services/api';

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

export default function FIRAutomator() {
  const [isRecording, setIsRecording] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [narrative, setNarrative] = useState('');
  const [formData, setFormData] = useState({
    complainant_name: '',
    complainant_contact: '',
    complainant_address: '',
    complainant_id: '',
    incident_location: '',
    incident_time: ''
  });

  const handleGenerate = async () => {
    if (!narrative.trim()) return;
    setIsGenerating(true);
    try {
      const response = await firService.generate(narrative);
      if (response.success) {
        // Auto-fill logic based on backend response schema
        const data = response.data.structured_data || {};
        setFormData({
          complainant_name: data.complainant?.name || '',
          complainant_contact: data.complainant?.contact || '',
          complainant_address: data.complainant?.address || '',
          complainant_id: data.complainant?.id_proof || '',
          incident_location: data.incident?.location || '',
          incident_time: data.incident?.time || ''
        });
      }
    } catch (err) {
      console.error("AI Generation Failed", err);
    } finally {
      setIsGenerating(false);
    }
  };

  const updateField = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="px-6">
      {/* Header */}
      <header className="py-12 md:py-16 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="max-w-3xl">
          <p className="label-mono mb-2 text-accent/70 text-[10px]">Module 01 • Automation</p>
          <h1 className="text-6xl md:text-7xl font-bold tracking-tighter leading-none uppercase text-foreground/90">
            FIR Draft
          </h1>
        </div>
        <div className="flex flex-col items-start gap-4">
          <button 
            onClick={() => setIsRecording(!isRecording)}
            className={`flex items-center gap-2 px-6 py-3 font-bold text-base uppercase tracking-tighter transition-all border-2 ${
              isRecording 
                ? 'bg-accent border-accent text-background animate-pulse' 
                : 'bg-background border-foreground/50 text-foreground/80 hover:bg-foreground hover:text-background'
            }`}
          >
            <Mic size={18} />
            {isRecording ? 'Listening' : 'Voice Input'}
          </button>
        </div>
      </header>

      {/* Main Narrative Area */}
      <div className="border-t-4 border-foreground/10 pt-6 pb-8">
        <p className="label-mono mb-2 text-muted-foreground/40 text-[8px]">Incident Narrative (Natural Language Input)</p>
        <textarea 
          value={narrative}
          onChange={(e) => setNarrative(e.target.value)}
          className="w-full bg-transparent border-none text-lg md:text-xl font-medium tracking-tight placeholder:text-muted-foreground/10 focus:outline-none min-h-[120px] leading-relaxed text-foreground/70"
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
          <button className="label-mono text-base border-b-2 border-border/50 pb-1 hover:border-accent transition-all text-muted-foreground">
            Save Draft
          </button>
          <button 
            onClick={handleGenerate}
            disabled={isGenerating || !narrative}
            className="flex items-center gap-3 px-8 py-4 bg-accent text-background font-bold text-lg uppercase tracking-tighter hover:bg-foreground transition-all disabled:opacity-50"
          >
            {isGenerating ? (
              <>
                Analysing...
                <Loader2 size={20} className="animate-spin" />
              </>
            ) : (
              <>
                Generate FIR
                <ArrowRight size={20} />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
