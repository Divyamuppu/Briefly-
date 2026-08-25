import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, Video, Check, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const VideoTypeCard = ({ type, isSelected, onSelect }) => {
  const videoRef = useRef(null);
  const [isHovering, setIsHovering] = useState(false);

  const handleMouseEnter = () => {
    setIsHovering(true);
    if (videoRef.current) {
      videoRef.current.currentTime = 0;
      videoRef.current.play().catch(() => {});
    }
  };

  const handleMouseLeave = () => {
    setIsHovering(false);
    if (videoRef.current) {
      videoRef.current.pause();
      videoRef.current.currentTime = 0;
    }
  };

  return (
    <button
      key={type.id}
      data-testid={`video-type-${type.id}`}
      onClick={() => onSelect(type.id)}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className={`group relative overflow-hidden rounded-3xl transition-all duration-300 border ${
        isSelected
          ? 'ring-2 ring-primary border-primary shadow-[0_0_40px_-10px_rgba(147,112,246,0.5)] scale-[1.02]'
          : 'border-white/10 hover:border-white/25 hover:scale-[1.01]'
      }`}
    >
      <div className="relative aspect-video overflow-hidden bg-black">
        <img
          src={type.image}
          alt={type.title}
          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
        />
        {type.video && (
          <video
            ref={videoRef}
            src={type.video}
            muted
            loop
            playsInline
            preload="metadata"
            className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-300 ${
              isHovering ? 'opacity-100' : 'opacity-0'
            }`}
          />
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-black/10" />

        {isSelected && (
          <div className="absolute top-4 right-4 w-9 h-9 rounded-full bg-primary flex items-center justify-center shadow-lg">
            <Check className="w-5 h-5 text-black" />
          </div>
        )}

        {type.video && (
          <p className={`absolute bottom-2 left-4 text-[10px] font-mono uppercase tracking-wider transition-opacity duration-200 ${isHovering ? 'opacity-0' : 'opacity-70 text-white'}`}>
            Hover to preview
          </p>
        )}
      </div>

      <div className="absolute bottom-0 left-0 right-0 p-6 text-left">
        <h3 className="text-xl font-bold font-display text-white mb-1">{type.title}</h3>
        <p className="text-sm text-white/60">{type.description}</p>
      </div>
    </button>
  );
};

const VideoTypeSelection = () => {
  const navigate = useNavigate();
  const [videoTypes, setVideoTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedType, setSelectedType] = useState(null);
  const [selectedSubOption, setSelectedSubOption] = useState(null);

  useEffect(() => {
    const fetchVideoTypes = async () => {
      try {
        const response = await axios.get(`${API}/video-types`);
        setVideoTypes(response.data);
      } catch (error) {
        console.error('Error fetching video types:', error);
        toast.error('Failed to load video types');
      } finally {
        setLoading(false);
      }
    };
    fetchVideoTypes();
  }, []);

  const handleSelectType = (typeId) => {
    setSelectedType(typeId);
    setSelectedSubOption(null);
  };

  const handleContinue = () => {
    if (!selectedType) {
      toast.error('Please select a video type');
      return;
    }
    navigate('/create', { state: { videoType: selectedType, videoSubOption: selectedSubOption } });
  };

  const activeType = videoTypes.find((t) => t.id === selectedType);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-10 h-10 text-primary animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background px-4 py-12">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-primary/30 bg-primary/5 mb-6">
            <Video className="w-4 h-4 text-primary" />
            <span className="text-xs font-mono uppercase tracking-[0.2em] text-primary">Video Type</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight font-display mb-4 text-foreground">
            What type of video are you <span className="text-primary">creating?</span>
          </h1>
          <p className="text-lg text-muted-foreground">
            Select the style that best matches your project
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {videoTypes.map((type) => (
            <VideoTypeCard
              key={type.id}
              type={type}
              isSelected={selectedType === type.id}
              onSelect={handleSelectType}
            />
          ))}
        </div>

        {/* Dynamic, context-aware sub-options for the selected video type */}
        <AnimatePresence>
          {activeType && activeType.sub_options?.length > 0 && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.35, ease: 'easeOut' }}
              className="mb-12 overflow-hidden"
            >
              <div className="p-8 rounded-3xl bg-card border border-border backdrop-blur-sm">
                <p className="text-xs font-mono uppercase tracking-[0.25em] text-primary mb-4">
                  Refine &middot; {activeType.title}
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                  {activeType.sub_options.map((opt) => (
                    <button
                      key={opt.id}
                      data-testid={`sub-option-${opt.id}`}
                      onClick={() => setSelectedSubOption(opt.id)}
                      className={`text-left p-4 rounded-2xl border transition-all duration-200 ${
                        selectedSubOption === opt.id
                          ? 'border-primary bg-primary/10'
                          : 'border-border bg-secondary/40 hover:border-primary/40'
                      }`}
                    >
                      <p className={`text-sm font-semibold font-display mb-1 ${selectedSubOption === opt.id ? 'text-primary' : 'text-foreground'}`}>
                        {opt.label}
                      </p>
                      <p className="text-xs text-muted-foreground leading-relaxed">{opt.note}</p>
                    </button>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="flex justify-center pb-24">
          <Button
            data-testid="continue-to-swipe-btn"
            onClick={handleContinue}
            disabled={!selectedType}
            className="h-16 px-16 text-lg rounded-full bg-primary text-black font-bold uppercase tracking-wide hover:bg-primary/90 transition-all duration-300 shadow-[0_0_30px_-8px_rgba(147,112,246,0.5)] disabled:opacity-40 disabled:cursor-not-allowed group"
          >
            Continue to Style Selection
            <ArrowRight className="ml-3 w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default VideoTypeSelection;