import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Download, Share2, Home, Loader2, Film, Music, Palette, Type, Link as LinkIcon, Layers } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const BriefDashboard = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [brief, setBrief] = useState(null);
  const [loading, setLoading] = useState(true);
  const [additionalNotes, setAdditionalNotes] = useState('');
  const [notesSaveTimeout, setNotesSaveTimeout] = useState(null);
  const [notesSaving, setNotesSaving] = useState(false);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    fetchBrief();
  }, [projectId]);

  const fetchBrief = async () => {
    try {
      const response = await axios.get(`${API}/brief/${projectId}`);
      setBrief(response.data);
      setAdditionalNotes(response.data?.project_details?.additional_notes || '');
      setLoading(false);
    } catch (error) {
      console.error('Error fetching brief:', error);
      toast.error('Failed to load brief');
      setLoading(false);
    }
  };

  const handleNotesChange = (value) => {
    setAdditionalNotes(value);
    if (notesSaveTimeout) clearTimeout(notesSaveTimeout);
    const timeout = setTimeout(async () => {
      setNotesSaving(true);
      try {
        await axios.patch(`${API}/projects/${projectId}/notes`, { additional_notes: value });
      } catch (error) {
        console.error('Error saving notes:', error);
        toast.error('Failed to save notes');
      } finally {
        setNotesSaving(false);
      }
    }, 800);
    setNotesSaveTimeout(timeout);
  };

  const handleDownloadPDF = async () => {
    try {
      const response = await axios.get(`${API}/brief/${projectId}/pdf`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `brief_${projectId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('PDF downloaded successfully!');
    } catch (error) {
      console.error('Error downloading PDF:', error);
      toast.error('Failed to download PDF');
    }
  };

  const handleDownloadVisualDeck = async () => {
    try {
      const response = await axios.get(`${API}/brief/${projectId}/visual-deck`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `visual_deck_${projectId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Visual deck downloaded successfully!');
    } catch (error) {
      console.error('Error downloading visual deck:', error);
      toast.error('Failed to download visual deck');
    }
  };

  const handleShare = async () => {
    const shareUrl = window.location.href;
    try {
      await navigator.clipboard.writeText(shareUrl);
      toast.success('Link copied to clipboard!');
    } catch (error) {
      toast.error('Failed to copy link');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-12 h-12 text-primary animate-spin" />
      </div>
    );
  }

  if (!brief) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <p className="text-lg text-muted-foreground">Brief not found</p>
          <Button onClick={() => navigate('/home')}>
            <Home className="mr-2 w-4 h-4" />
            Go Home
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background px-4 py-12">
      <div className="max-w-6xl mx-auto space-y-12">
        <div className="text-center space-y-4">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-primary/20 bg-primary/5">
            <Film className="w-4 h-4 text-primary" />
            <span className="text-xs font-mono uppercase tracking-[0.2em] text-primary">Creative Brief</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight font-display">
            <span className="text-primary">{brief.project_name}</span>
          </h1>
          <p className="text-sm text-muted-foreground">
            Based on {brief.total_swipes} preferences
          </p>
        </div>

        {/* AI Summary */}
        <div className="p-8 rounded-2xl bg-gradient-to-br from-primary/5 to-purple-50 border border-primary/20 shadow-md">
          <h2 className="text-2xl font-semibold font-display mb-4 text-primary">Video Overview</h2>
          <p className="text-base leading-relaxed text-foreground">
            {brief.ai_summary}
          </p>
        </div>

        {/* Project Details */}
        <div className="grid grid-cols-1 gap-6">
          <div className="p-8 rounded-2xl bg-card border border-border shadow-md space-y-4">
            <h2 className="text-xl font-semibold font-display text-primary">Project Details</h2>
            <div className="space-y-3 text-sm">
              {brief.project_details.video_type && (
                <div className="pb-3 border-b border-border">
                  <span className="text-muted-foreground block mb-2">Video Type:</span>
                  <span className="font-medium text-foreground capitalize">{brief.project_details.video_type.replace('_', ' ')}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-muted-foreground">Platform:</span>
                <span className="font-medium text-foreground">{brief.project_details.platform}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Video Length:</span>
                <span className="font-medium text-foreground">{brief.project_details.video_length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Aspect Ratio:</span>
                <span className="font-medium text-foreground">{brief.project_details.aspect_ratio}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Business Model:</span>
                <span className="font-medium text-foreground">{brief.project_details.business_model}</span>
              </div>
              <div className="pt-3 border-t border-border">
                <span className="text-muted-foreground block mb-2">Target Audience:</span>
                <span className="font-medium text-foreground">{brief.project_details.target_audience}</span>
              </div>
              <div className="pt-3 border-t border-border">
                <span className="text-muted-foreground block mb-2">Purpose:</span>
                <span className="font-medium text-foreground">{brief.project_details.purpose}</span>
              </div>
            </div>
          </div>

          <div className="p-8 rounded-2xl bg-card border border-border shadow-md space-y-4">
            <h2 className="text-xl font-semibold font-display text-primary">Style Preferences</h2>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-primary">Narrative</span>
                  <span className="text-xs font-mono text-muted-foreground">{Math.abs(brief.project_details.narrative_technical)}%</span>
                  <span className="text-foreground">Technical</span>
                </div>
                <div className="h-2 bg-secondary rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-purple-400 to-primary transition-all"
                    style={{ width: `${(brief.project_details.narrative_technical + 100) / 2}%` }}
                  />
                </div>
              </div>
              
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-primary">Fun</span>
                  <span className="text-xs font-mono text-muted-foreground">{Math.abs(brief.project_details.brand_tones.fun_serious)}%</span>
                  <span className="text-foreground">Serious</span>
                </div>
                <div className="h-2 bg-secondary rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-primary transition-all"
                    style={{ width: `${(100 - brief.project_details.brand_tones.fun_serious) / 2}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-primary">Luxury</span>
                  <span className="text-xs font-mono text-muted-foreground">{Math.abs(brief.project_details.brand_tones.luxury_casual)}%</span>
                  <span className="text-foreground">Casual</span>
                </div>
                <div className="h-2 bg-secondary rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-primary transition-all"
                    style={{ width: `${(100 - brief.project_details.brand_tones.luxury_casual) / 2}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-foreground">Corporate</span>
                  <span className="text-xs font-mono text-muted-foreground">{Math.abs(brief.project_details.brand_tones.corporate_playful)}%</span>
                  <span className="text-primary">Playful</span>
                </div>
                <div className="h-2 bg-secondary rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-primary transition-all"
                    style={{ width: `${(brief.project_details.brand_tones.corporate_playful + 100) / 2}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* References */}
        {brief.project_details.references && brief.project_details.references.length > 0 && (
          <div className="p-8 rounded-2xl bg-card border border-border shadow-md">
            <h2 className="text-xl font-semibold font-display text-primary mb-4">References</h2>
            <div className="space-y-2">
              {brief.project_details.references.map((ref, idx) => (
                <div key={idx} className="flex items-center gap-2 p-3 rounded-lg bg-secondary/60 border border-border">
                  <LinkIcon className="w-4 h-4 text-primary flex-shrink-0" />
                  <a href={ref.value} target="_blank" rel="noopener noreferrer" className="text-sm text-primary hover:underline truncate">
                    {ref.name || ref.value}
                  </a>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Voice Note */}
        {brief.project_details.voice_note_url && (
          <div className="p-8 rounded-2xl bg-card border border-border shadow-md">
            <h2 className="text-xl font-semibold font-display text-primary mb-4">Voice Note</h2>
            <audio controls className="w-full" src={brief.project_details.voice_note_url}>
              Your browser does not support the audio element.
            </audio>
          </div>
        )}

        <div className="grid grid-cols-1 gap-6">
          <div className="p-8 rounded-2xl bg-card border border-border shadow-md space-y-6" data-testid="editing-style-section">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                <Film className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h2 className="text-2xl font-semibold font-display text-foreground">Editing Style</h2>
                <p className="text-xs font-mono text-muted-foreground">{brief.editing_style.count} selections</p>
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-lg leading-relaxed text-foreground">{brief.editing_style.preference}</p>
            </div>
          </div>

          <div className="p-8 rounded-2xl bg-card border border-border shadow-md space-y-6" data-testid="color-direction-section">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-pink-100 flex items-center justify-center">
                <Palette className="w-6 h-6 text-pink-600" />
              </div>
              <div>
                <h2 className="text-2xl font-semibold font-display text-foreground">Color Direction</h2>
                <p className="text-xs font-mono text-muted-foreground">{brief.color_direction.count} selections</p>
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-lg leading-relaxed text-foreground">{brief.color_direction.preference}</p>
            </div>
          </div>

          <div className="p-8 rounded-2xl bg-card border border-border shadow-md space-y-6" data-testid="music-direction-section">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
                <Music className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h2 className="text-2xl font-semibold font-display text-foreground">Music Direction</h2>
                <p className="text-xs font-mono text-muted-foreground">{brief.music_direction.count} selections</p>
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-lg leading-relaxed text-foreground">{brief.music_direction.preference}</p>
            </div>
          </div>

          <div className="p-8 rounded-2xl bg-card border border-border shadow-md space-y-6" data-testid="typography-direction-section">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-secondary flex items-center justify-center">
                <Type className="w-6 h-6 text-foreground" />
              </div>
              <div>
                <h2 className="text-2xl font-semibold font-display text-foreground">Typography</h2>
                <p className="text-xs font-mono text-muted-foreground">{brief.typography_direction.count} selections</p>
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-lg leading-relaxed text-foreground">{brief.typography_direction.preference}</p>
            </div>
          </div>

          <div className="p-8 rounded-2xl bg-card border border-border shadow-md space-y-6" data-testid="motion-graphics-section">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-purple-100 flex items-center justify-center">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
                </svg>
              </div>
              <div>
                <h2 className="text-2xl font-semibold font-display text-foreground">Motion Graphics</h2>
                <p className="text-xs font-mono text-muted-foreground">{brief.motion_graphics.count} selections</p>
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-lg leading-relaxed text-foreground">{brief.motion_graphics.preference}</p>
            </div>
          </div>
        </div>

        {/* Additional Notes Section */}
        <div className="p-8 rounded-2xl bg-card border border-border shadow-md">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold font-display text-primary">Additional Notes</h2>
            {notesSaving && <span className="text-xs text-muted-foreground">Saving...</span>}
          </div>
          <textarea
            value={additionalNotes}
            onChange={(e) => handleNotesChange(e.target.value)}
            placeholder="Add any additional notes, requirements, or feedback here..."
            className="w-full min-h-[120px] bg-card border-2 border-border rounded-2xl p-4 text-base focus:border-primary focus:outline-none placeholder:text-muted-foreground transition-colors duration-300 resize-y text-foreground"
            data-testid="additional-notes-textarea"
          />
          <p className="text-xs text-muted-foreground mt-2">These notes will be included in the PDF export</p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pb-24">
          <Button
            data-testid="download-pdf-btn"
            onClick={handleDownloadPDF}
            className="h-12 px-8 rounded-full bg-primary text-white font-bold uppercase tracking-wide hover:bg-primary/90 transition-all duration-300 shadow-md hover:shadow-lg"
          >
            <Download className="mr-2 w-5 h-5" />
            Download PDF
          </Button>
          <Button
            data-testid="download-visual-deck-btn"
            onClick={handleDownloadVisualDeck}
            variant="outline"
            className="h-12 px-8 rounded-full bg-card border-2 border-primary text-primary font-bold uppercase tracking-wide hover:bg-primary/10 transition-all duration-300 shadow-md hover:shadow-lg"
          >
            <Layers className="mr-2 w-5 h-5" />
            Visual Deck
          </Button>
          <Button
            data-testid="share-btn"
            onClick={handleShare}
            variant="outline"
            className="h-12 px-8 rounded-full bg-card border-2 border-border text-foreground font-medium hover:bg-secondary transition-colors duration-300"
          >
            <Share2 className="mr-2 w-5 h-5" />
            Share Link
          </Button>
          <Button
            data-testid="home-btn"
            onClick={() => navigate('/home')}
            variant="outline"
            className="h-12 px-8 rounded-full bg-card border-2 border-border text-foreground font-medium hover:bg-secondary transition-colors duration-300"
          >
            <Home className="mr-2 w-5 h-5" />
            New Project
          </Button>
        </div>
      </div>
    </div>
  );
};

export default BriefDashboard;