import React, { useState, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { ArrowRight, Video, Mic, Upload, Link as LinkIcon, X, Square } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CreateProject = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const videoType = location.state?.videoType;
  const videoSubOption = location.state?.videoSubOption;
  const audioRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const fileInputRef = useRef(null);

  const [formData, setFormData] = useState({
    project_name: '',
    video_length: '30s',
    platform: 'Instagram',
    aspect_ratio: '9:16',
    target_audience: '',
    purpose: '',
    business_model: 'B2C',
    narrative_technical: 0,
    brand_tones: {
      fun_serious: 0,
      luxury_casual: 0,
      corporate_playful: 0
    },
    references: [],
    voice_note_url: null,
    video_type: videoType || null,
    video_sub_option: videoSubOption || null,
  });

  const [isRecording, setIsRecording] = useState(false);
  const [audioPreviewUrl, setAudioPreviewUrl] = useState(null);
  const [uploadingVoice, setUploadingVoice] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [referenceInput, setReferenceInput] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Converts a Blob/File to a base64 data URL. We store the recording and any
  // uploaded reference file directly as a data URL in the project record — so it
  // persists with no Supabase Storage bucket, no permissions setup, and no
  // browser-only blob: URL that dies the moment you leave this page (that was why
  // voice notes / files never showed up in the brief before).
  const toDataUrl = (fileOrBlob) =>
    new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = reject;
      reader.readAsDataURL(fileOrBlob);
    });

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      const chunks = [];

      mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        setAudioPreviewUrl(URL.createObjectURL(blob)); // instant local playback
        setUploadingVoice(true);
        try {
          const dataUrl = await toDataUrl(blob); // permanent, self-contained
          setFormData((prev) => ({ ...prev, voice_note_url: dataUrl }));
          toast.success('Voice note saved');
        } catch (error) {
          console.error('Error saving voice note:', error);
          toast.error('Could not save voice note');
          setFormData((prev) => ({ ...prev, voice_note_url: null }));
        } finally {
          setUploadingVoice(false);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
      toast.success('Recording started');
    } catch (error) {
      console.error('Error accessing microphone:', error);
      toast.error('Could not access microphone');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop());
      setIsRecording(false);
    }
  };

  const addReference = () => {
    if (referenceInput.trim()) {
      // A pasted link is already a real URL — normalize it so it's always clickable.
      let value = referenceInput.trim();
      if (!/^https?:\/\//i.test(value)) value = `https://${value}`;
      setFormData((prev) => ({
        ...prev,
        references: [...prev.references, { type: 'url', value }]
      }));
      setReferenceInput('');
      toast.success('Reference added');
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploadingFile(true);
    try {
      const dataUrl = await toDataUrl(file);
      setFormData((prev) => ({
        ...prev,
        references: [...prev.references, { type: 'file', value: dataUrl, name: file.name }],
      }));
      toast.success('File added');
    } catch (error) {
      console.error('Error reading file:', error);
      toast.error('Could not add file');
    } finally {
      setUploadingFile(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const removeReference = (index) => {
    const newReferences = formData.references.filter((_, i) => i !== index);
    setFormData({ ...formData, references: newReferences });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.project_name || !formData.target_audience || !formData.purpose) {
      toast.error('Please fill in all required fields');
      return;
    }

    // Fold any link still sitting in the reference box (that wasn't "added" with the
    // button) into the references list, so a link the user typed always gets saved —
    // even if they forget to click the add button before submitting.
    let references = [...formData.references];
    const pending = referenceInput.trim();
    if (pending) {
      let value = pending;
      if (!/^https?:\/\//i.test(value)) value = `https://${value}`;
      references = [...references, { type: 'url', value }];
    }
    const payload = { ...formData, references };

    setSubmitting(true);
    try {
      const response = await axios.post(`${API}/projects`, payload);
      const projectId = response.data.id;

      toast.success('Project created! Time to swipe.');
      navigate(`/swipe/${projectId}`);
    } catch (error) {
      console.error('Error creating project:', error);
      toast.error('Failed to create project');
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4 py-8">
      <div className="max-w-3xl w-full">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-primary/30 bg-primary/5 mb-4">
            <Video className="w-4 h-4 text-primary" />
            <span className="text-xs font-mono uppercase tracking-[0.2em] text-primary">New Project</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight font-display mb-4 text-foreground">
            Tell us about your <span className="text-primary">video</span>
          </h1>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Basic Info */}
          <div className="space-y-6 p-8 rounded-3xl bg-card border border-border">
            <div className="space-y-3">
              <Label className="text-xs font-mono uppercase tracking-[0.2em] text-muted-foreground">Project Name *</Label>
              <input
                data-testid="project-name-input"
                type="text"
                value={formData.project_name}
                onChange={(e) => setFormData({ ...formData, project_name: e.target.value })}
                className="w-full bg-transparent border-b-2 border-border text-2xl py-4 focus:border-primary focus:outline-none placeholder:text-muted-foreground/60 transition-colors duration-300 font-display text-foreground"
                placeholder="My Awesome Video"
              />
            </div>

            <div className="space-y-3">
              <Label className="text-xs font-mono uppercase tracking-[0.2em] text-muted-foreground">Purpose / Goal *</Label>
              <textarea
                data-testid="purpose-input"
                value={formData.purpose}
                onChange={(e) => setFormData({ ...formData, purpose: e.target.value })}
                className="w-full bg-transparent border-b-2 border-border text-lg py-3 focus:border-primary focus:outline-none placeholder:text-muted-foreground/60 transition-colors duration-300 resize-none text-foreground"
                placeholder="What are you trying to accomplish with this video?"
                rows={2}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-3">
                <Label className="text-xs font-mono uppercase tracking-[0.2em] text-muted-foreground">Video Length</Label>
                <select
                  data-testid="video-length-select"
                  value={formData.video_length}
                  onChange={(e) => setFormData({ ...formData, video_length: e.target.value })}
                  className="w-full bg-transparent border-b-2 border-border text-lg py-3 focus:border-primary focus:outline-none transition-colors duration-300 text-foreground"
                >
                  <option value="15s" className="bg-black">15 seconds</option>
                  <option value="30s" className="bg-black">30 seconds</option>
                  <option value="60s" className="bg-black">60 seconds</option>
                  <option value="90s" className="bg-black">90 seconds</option>
                  <option value="custom" className="bg-black">Custom</option>
                </select>
              </div>

              <div className="space-y-3">
                <Label className="text-xs font-mono uppercase tracking-[0.2em] text-muted-foreground">Platform</Label>
                <select
                  data-testid="platform-select"
                  value={formData.platform}
                  onChange={(e) => setFormData({ ...formData, platform: e.target.value })}
                  className="w-full bg-transparent border-b-2 border-border text-lg py-3 focus:border-primary focus:outline-none transition-colors duration-300 text-foreground"
                >
                  <option value="Instagram" className="bg-black">Instagram</option>
                  <option value="TikTok" className="bg-black">TikTok</option>
                  <option value="YouTube" className="bg-black">YouTube</option>
                  <option value="LinkedIn" className="bg-black">LinkedIn</option>
                  <option value="Website" className="bg-black">Website</option>
                </select>
              </div>

              <div className="space-y-3">
                <Label className="text-xs font-mono uppercase tracking-[0.2em] text-muted-foreground">Aspect Ratio</Label>
                <select
                  data-testid="aspect-ratio-select"
                  value={formData.aspect_ratio}
                  onChange={(e) => setFormData({ ...formData, aspect_ratio: e.target.value })}
                  className="w-full bg-transparent border-b-2 border-border text-lg py-3 focus:border-primary focus:outline-none transition-colors duration-300 text-foreground"
                >
                  <option value="9:16" className="bg-black">9:16 (Vertical)</option>
                  <option value="1:1" className="bg-black">1:1 (Square)</option>
                  <option value="16:9" className="bg-black">16:9 (Widescreen)</option>
                  <option value="4:5" className="bg-black">4:5 (Portrait)</option>
                </select>
              </div>

              <div className="space-y-3">
                <Label className="text-xs font-mono uppercase tracking-[0.2em] text-muted-foreground">Business Model</Label>
                <select
                  data-testid="business-model-select"
                  value={formData.business_model}
                  onChange={(e) => setFormData({ ...formData, business_model: e.target.value })}
                  className="w-full bg-transparent border-b-2 border-border text-lg py-3 focus:border-primary focus:outline-none transition-colors duration-300 text-foreground"
                >
                  <option value="B2C" className="bg-black">B2C (Direct to Consumer)</option>
                  <option value="B2B" className="bg-black">B2B (Business to Business)</option>
                </select>
              </div>
            </div>

            <div className="space-y-3">
              <Label className="text-xs font-mono uppercase tracking-[0.2em] text-muted-foreground">Target Audience *</Label>
              <input
                data-testid="target-audience-input"
                type="text"
                value={formData.target_audience}
                onChange={(e) => setFormData({ ...formData, target_audience: e.target.value })}
                className="w-full bg-transparent border-b-2 border-border text-lg py-3 focus:border-primary focus:outline-none placeholder:text-muted-foreground/60 transition-colors duration-300 text-foreground"
                placeholder="e.g., Young professionals aged 25-35"
              />
            </div>
          </div>

          {/* Style Sliders */}
          <div className="space-y-8 p-8 rounded-3xl bg-card border border-border">
            <h2 className="text-2xl font-semibold font-display text-center text-foreground">Video Style</h2>

            <div className="space-y-8">
              <div className="space-y-4">
                <p className="text-xs text-muted-foreground text-center uppercase tracking-wider">Story-driven vs. Feature-focused</p>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-primary">Narrative</span>
                  <span className="text-xs font-mono text-muted-foreground">{Math.abs(formData.narrative_technical)}%</span>
                  <span className="text-sm text-muted-foreground">Technical/Spec</span>
                </div>
                <Slider
                  data-testid="narrative-technical-slider"
                  value={[formData.narrative_technical]}
                  onValueChange={(value) => setFormData({ ...formData, narrative_technical: value[0] })}
                  min={-100}
                  max={100}
                  step={1}
                />
              </div>

              <div className="space-y-4">
                <p className="text-xs text-muted-foreground text-center uppercase tracking-wider">Tone & Energy</p>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-primary">Fun</span>
                  <span className="text-xs font-mono text-muted-foreground">{Math.abs(formData.brand_tones.fun_serious)}%</span>
                  <span className="text-sm text-muted-foreground">Serious</span>
                </div>
                <Slider
                  data-testid="fun-serious-slider"
                  value={[formData.brand_tones.fun_serious]}
                  onValueChange={(value) => setFormData({ ...formData, brand_tones: { ...formData.brand_tones, fun_serious: value[0] } })}
                  min={-100}
                  max={100}
                  step={1}
                />
              </div>

              <div className="space-y-4">
                <p className="text-xs text-muted-foreground text-center uppercase tracking-wider">Brand Positioning</p>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-primary">Luxury</span>
                  <span className="text-xs font-mono text-muted-foreground">{Math.abs(formData.brand_tones.luxury_casual)}%</span>
                  <span className="text-sm text-muted-foreground">Casual</span>
                </div>
                <Slider
                  data-testid="luxury-casual-slider"
                  value={[formData.brand_tones.luxury_casual]}
                  onValueChange={(value) => setFormData({ ...formData, brand_tones: { ...formData.brand_tones, luxury_casual: value[0] } })}
                  min={-100}
                  max={100}
                  step={1}
                />
              </div>

              <div className="space-y-4">
                <p className="text-xs text-muted-foreground text-center uppercase tracking-wider">Communication Style</p>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Corporate</span>
                  <span className="text-xs font-mono text-muted-foreground">{Math.abs(formData.brand_tones.corporate_playful)}%</span>
                  <span className="text-sm text-primary">Playful</span>
                </div>
                <Slider
                  data-testid="corporate-playful-slider"
                  value={[formData.brand_tones.corporate_playful]}
                  onValueChange={(value) => setFormData({ ...formData, brand_tones: { ...formData.brand_tones, corporate_playful: value[0] } })}
                  min={-100}
                  max={100}
                  step={1}
                />
              </div>
            </div>
          </div>

          {/* References */}
          <div className="space-y-6 p-8 rounded-3xl bg-card border border-border">
            <h2 className="text-xl font-semibold font-display text-foreground">References (Optional)</h2>

            <div className="flex gap-3">
              <input
                type="text"
                value={referenceInput}
                onChange={(e) => setReferenceInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addReference())}
                placeholder="Paste a URL..."
                className="flex-1 bg-transparent border-b-2 border-border text-base py-2 focus:border-primary focus:outline-none placeholder:text-muted-foreground/60 text-foreground"
              />
              <Button type="button" onClick={addReference} size="sm" className="rounded-full bg-primary text-black hover:bg-primary/90">
                <LinkIcon className="w-4 h-4" />
              </Button>
              <Button type="button" onClick={() => fileInputRef.current?.click()} disabled={uploadingFile} size="sm" className="rounded-full bg-primary text-black hover:bg-primary/90 disabled:opacity-60">
                <Upload className="w-4 h-4" />
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                onChange={handleFileUpload}
                className="hidden"
                accept="image/*,video/*,.pdf"
              />
            </div>

            {formData.references.length > 0 && (
              <div className="space-y-2">
                {formData.references.map((ref, idx) => (
                  <div key={idx} className="flex items-center gap-2 p-3 rounded-xl bg-card border border-border">
                    <span className="text-sm flex-1 truncate text-muted-foreground">{ref.name || ref.value}</span>
                    <Button type="button" onClick={() => removeReference(idx)} size="sm" variant="ghost" className="h-6 w-6 p-0 text-muted-foreground hover:text-foreground">
                      <X className="w-3 h-3" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Voice Note */}
          <div className="space-y-4 p-8 rounded-3xl bg-card border border-border">
            <h2 className="text-xl font-semibold font-display text-foreground">Voice Note (Optional)</h2>
            <p className="text-sm text-muted-foreground">Record any additional thoughts or context</p>

            <div className="flex items-center gap-4 flex-wrap">
              {!isRecording ? (
                <Button type="button" onClick={startRecording} disabled={uploadingVoice} className="rounded-full bg-primary text-black hover:bg-primary/90 disabled:opacity-60" size="lg">
                  <Mic className="w-5 h-5 mr-2" />
                  {formData.voice_note_url ? 'Re-record' : 'Start Recording'}
                </Button>
              ) : (
                <Button type="button" onClick={stopRecording} className="rounded-full bg-accent hover:bg-accent/90" size="lg">
                  <Square className="w-5 h-5 mr-2" />
                  Stop Recording
                </Button>
              )}
              {uploadingVoice && (
                <span className="text-sm text-muted-foreground">Saving voice note…</span>
              )}
              {!uploadingVoice && formData.voice_note_url && (
                <span className="text-sm text-primary">&check; Voice note saved</span>
              )}
            </div>

            {audioPreviewUrl && (
              <audio controls className="w-full mt-2" src={audioPreviewUrl}>
                Your browser does not support the audio element.
              </audio>
            )}
          </div>

          <div className="flex justify-center pt-4 pb-24">
            <Button
              data-testid="start-swiping-btn"
              type="submit"
              disabled={submitting || uploadingVoice || uploadingFile}
              className="h-16 px-16 text-lg rounded-full bg-primary text-black font-bold uppercase tracking-wide hover:bg-primary/90 transition-all duration-300 shadow-[0_0_30px_-8px_rgba(147,112,246,0.5)] disabled:opacity-50 group"
            >
              {submitting ? 'Creating Project...' : (uploadingVoice || uploadingFile) ? 'Uploading…' : 'Start Swiping'}
              {!submitting && !uploadingVoice && !uploadingFile && <ArrowRight className="ml-3 w-5 h-5 group-hover:translate-x-1 transition-transform" />}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateProject;
