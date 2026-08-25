import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Play, Pause, Volume2, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

const CategoryTag = ({ label }) => (
  <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/15 backdrop-blur-md">
    <span className="w-1.5 h-1.5 rounded-full bg-primary" />
    <span className="text-[10px] font-mono uppercase tracking-[0.25em] text-white/70">{label}</span>
  </div>
);

const MusicCard = ({ card }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef(null);

  const togglePlay = (e) => {
    e.stopPropagation();
    if (isPlaying) {
      audioRef.current?.pause();
    } else {
      // Stop every other playing audio sample on the page before starting this one,
      // so only one Music card can ever play at a time.
      document.querySelectorAll('audio').forEach((el) => {
        if (el !== audioRef.current && !el.paused) {
          el.pause();
        }
      });
      audioRef.current?.play().catch((err) => {
        console.error('Audio play blocked or failed:', err);
        toast.error('Could not play this sample \u2014 the audio source may be temporarily unavailable.');
      });
    }
  };

  return (
    <div className="relative w-full h-full overflow-hidden bg-[#121212] flex flex-col">
      <div className="relative flex-1 min-h-0 overflow-hidden bg-[#0A0A0A] flex items-center justify-center">
        <motion.div
          animate={{ scale: isPlaying ? [1, 1.08, 1] : 1 }}
          transition={{ duration: 1.4, repeat: isPlaying ? Infinity : 0, ease: 'easeInOut' }}
          className="w-32 h-32 rounded-full bg-black/40 border border-primary/40 backdrop-blur-md flex items-center justify-center shadow-[0_0_60px_-10px_rgba(147,112,246,0.5)]"
        >
          <Volume2 className="w-14 h-14 text-primary/80" strokeWidth={1.25} />
        </motion.div>
      </div>

      <div className="shrink-0 bg-[#121212] border-t border-white/10 p-5 space-y-2">
        <CategoryTag label="Music Style" />
        <h3 className="text-xl font-bold font-display text-white tracking-tight leading-snug">{card.title}</h3>
        <p className="text-sm text-white/60 leading-relaxed line-clamp-2">{card.description}</p>

        {card.metadata && (
          <div className="flex gap-4 text-[11px] text-white/40 font-mono uppercase tracking-wider pt-1">
            <span>Genre / {card.metadata.genre}</span>
            <span>Tempo / {card.metadata.tempo}</span>
          </div>
        )}

        {card.metadata?.audio_url && (
          <div className="pt-2">
            <Button
              onClick={togglePlay}
              size="sm"
              className="h-9 px-5 rounded-full bg-primary text-black font-bold uppercase tracking-wide text-xs hover:bg-primary/90 shadow-[0_0_20px_rgba(147,112,246,0.35)]"
            >
              {isPlaying ? <Pause className="w-3.5 h-3.5 mr-2" /> : <Play className="w-3.5 h-3.5 mr-2" />}
              {isPlaying ? 'Pause Sample' : 'Play Sample'}
            </Button>
            <audio
              ref={audioRef}
              src={card.metadata.audio_url}
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              onEnded={() => setIsPlaying(false)}
            />
          </div>
        )}
      </div>
    </div>
  );
};

const TypographyCard = ({ card }) => {
  const fontFamily = card.metadata?.font_name || 'Inter';
  const sampleText = card.metadata?.sample_text || card.title;

  return (
    <div className="relative w-full h-full overflow-hidden bg-white">
      <style>
        {`@import url('https://fonts.googleapis.com/css2?family=${fontFamily.replace(' ', '+')}:wght@100;200;300;400;500;600;700;800;900&display=swap');`}
      </style>

      <div className="absolute inset-0 flex flex-col items-center justify-center px-10 text-center">
        <p className="text-5xl font-bold text-black" style={{ fontFamily: `'${fontFamily}', sans-serif` }}>
          {sampleText}
        </p>
      </div>

      <div className="absolute bottom-0 left-0 right-0 p-8 flex justify-center">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-black/5 border border-black/15 backdrop-blur-md">
          <span className="w-1.5 h-1.5 rounded-full bg-primary" />
          <span className="text-[10px] font-mono uppercase tracking-[0.25em] text-black/70">Typography</span>
        </div>
      </div>
    </div>
  );
};

const ColorCard = ({ card }) => {
  return (
    <div className="relative w-full h-full overflow-hidden bg-[#0A0A0A]">
      <div className="relative w-full h-full flex">
        <div className="w-1/2 h-full relative overflow-hidden">
          <div
            className="absolute inset-0 card-image-drift"
            style={{
              backgroundImage: `url(${card.image_url})`,
              backgroundSize: 'cover',
              backgroundPosition: 'center',
              filter: 'grayscale(0.3) brightness(0.85)',
            }}
          />
          <div className="absolute top-4 left-4 px-3 py-1 rounded-full bg-black/60 border border-white/15 backdrop-blur-md">
            <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-white/70 font-bold">Before</span>
          </div>
        </div>

        <div className="w-1/2 h-full relative overflow-hidden">
          <div
            className="absolute inset-0 card-image-drift"
            style={{
              backgroundImage: `url(${card.image_url})`,
              backgroundSize: 'cover',
              backgroundPosition: 'center',
              filter: card.metadata?.color_filter || 'none',
            }}
          />
          {card.metadata?.color_overlay && (
            <div
              className="absolute inset-0"
              style={{
                background: card.metadata.color_overlay,
                mixBlendMode: 'multiply',
                opacity: 0.6,
              }}
            />
          )}
          <div className="absolute top-4 right-4 px-3 py-1 rounded-full bg-primary/90 backdrop-blur-md border border-primary">
            <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-black font-bold">After</span>
          </div>
        </div>

        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[2px] h-full bg-white/70 shadow-[0_0_20px_rgba(255,255,255,0.4)]" />
      </div>

      <div className="absolute inset-0 bg-gradient-to-t from-black via-black/30 to-transparent pointer-events-none" />

      <div className="absolute bottom-0 left-0 right-0 p-8 space-y-3">
        <CategoryTag label="Color Grading" />
        <h3 className="text-3xl font-bold font-display text-white tracking-tight">{card.title}</h3>
        <p className="text-sm text-white/60 leading-relaxed">{card.description}</p>
        {card.metadata?.color_palette && (
          <div className="flex gap-2 pt-2">
            {card.metadata.color_palette.map((color, idx) => (
              <div
                key={idx}
                className="w-8 h-8 rounded-full border-2 border-white/30 shadow-lg"
                style={{ backgroundColor: color }}
                title={color}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const EditingCard = ({ card }) => {
  const videoRef = useRef(null);
  const [isHovering, setIsHovering] = useState(false);
  const [isMuted, setIsMuted] = useState(true);
  const videoUrl = card.metadata?.video_url;

  const handleMouseEnter = () => {
    setIsHovering(true);
    if (videoRef.current) {
      videoRef.current.currentTime = 0;
      videoRef.current.muted = isMuted;
      videoRef.current.play().catch((err) => {
        console.error('Video play blocked:', err);
      });
    }
  };

  const handleMouseLeave = () => {
    setIsHovering(false);
    if (videoRef.current) {
      videoRef.current.pause();
      videoRef.current.currentTime = 0;
    }
  };

  const toggleMute = (e) => {
    e.stopPropagation();
    const next = !isMuted;
    setIsMuted(next);
    if (videoRef.current) {
      videoRef.current.muted = next;
      if (!next) {
        videoRef.current.play().catch((err) => console.error('Unmuted play blocked:', err));
      }
    }
  };

  return (
    <div
      className="relative w-full h-full overflow-hidden bg-[#121212] flex flex-col"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* Media zone — video only, top ~70% of the card */}
      <div className="relative flex-1 min-h-0 overflow-hidden bg-[#0A0A0A]">
        {videoUrl ? (
          <video
            ref={videoRef}
            src={videoUrl}
            muted={isMuted}
            loop
            playsInline
            preload="auto"
            className="absolute inset-0 w-full h-full object-cover"
          />
        ) : (
          <div className="absolute inset-0 bg-[#0A0A0A]" />
        )}

        {videoUrl && isHovering && (
          <button
            type="button"
            onClick={toggleMute}
            className="absolute top-4 right-4 z-10 w-9 h-9 rounded-full bg-black/60 border border-white/20 backdrop-blur-md flex items-center justify-center hover:bg-black/80 transition-colors"
          >
            {isMuted ? (
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2M9 9v6h4l5 5V4L13 9H9z" />
              </svg>
            ) : (
              <svg className="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.536 8.464a5 5 0 010 7.072M9 9v6h4l5 5V4L13 9H9z" />
              </svg>
            )}
          </button>
        )}

        {videoUrl && (
          <p className={`absolute bottom-3 left-4 text-[10px] font-mono uppercase tracking-wider transition-opacity duration-200 ${isHovering ? 'opacity-0' : 'opacity-80 text-white'} drop-shadow`}>
            Hover to preview
          </p>
        )}
      </div>

      {/* Text zone — solid panel, always legible regardless of what's playing above */}
      <div className="shrink-0 bg-[#121212] border-t border-white/10 p-5 space-y-2">
        <CategoryTag label="Editing Style" />
        <h3 className="text-xl font-bold font-display text-white tracking-tight leading-snug">{card.title}</h3>
        <p className="text-sm text-white/60 leading-relaxed line-clamp-2">{card.description}</p>
        {card.metadata && (
          <div className="flex gap-4 text-[11px] text-white/40 font-mono uppercase tracking-wider pt-1">
            <span>Pace / {card.metadata.pace}</span>
            <span>Duration / {card.metadata.shot_duration}</span>
          </div>
        )}
      </div>
    </div>
  );
};

const MotionGraphicsCard = ({ card }) => {
  const videoRef = useRef(null);
  const [isHovering, setIsHovering] = useState(false);
  const [isMuted, setIsMuted] = useState(true);
  const videoUrl = card.metadata?.video_url;

  const handleMouseEnter = () => {
    setIsHovering(true);
    if (videoRef.current) {
      videoRef.current.currentTime = 0;
      videoRef.current.muted = isMuted;
      videoRef.current.play().catch((err) => {
        console.error('Video play blocked:', err);
      });
    }
  };

  const handleMouseLeave = () => {
    setIsHovering(false);
    if (videoRef.current) {
      videoRef.current.pause();
      videoRef.current.currentTime = 0;
    }
  };

  const toggleMute = (e) => {
    e.stopPropagation();
    const next = !isMuted;
    setIsMuted(next);
    if (videoRef.current) {
      videoRef.current.muted = next;
      if (!next) {
        videoRef.current.play().catch((err) => console.error('Unmuted play blocked:', err));
      }
    }
  };

  return (
    <div
      className="relative w-full h-full overflow-hidden bg-[#121212] flex flex-col"
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* Media zone — video only, top ~70% of the card */}
      <div className="relative flex-1 min-h-0 overflow-hidden bg-[#0A0A0A]">
        {videoUrl ? (
          <video
            ref={videoRef}
            src={videoUrl}
            muted={isMuted}
            loop
            playsInline
            preload="auto"
            className="absolute inset-0 w-full h-full object-cover"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-32 h-32 rounded-2xl bg-black/40 border border-primary/30 backdrop-blur-md flex items-center justify-center relative overflow-hidden shadow-[0_0_60px_-10px_rgba(147,112,246,0.4)]">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 6, repeat: Infinity, ease: 'linear' }}
                className="absolute"
              >
                <Sparkles className="w-16 h-16 text-primary/50" strokeWidth={1} />
              </motion.div>
            </div>
          </div>
        )}

        {videoUrl && isHovering && (
          <button
            type="button"
            onClick={toggleMute}
            className="absolute top-4 right-4 z-10 w-9 h-9 rounded-full bg-black/60 border border-white/20 backdrop-blur-md flex items-center justify-center hover:bg-black/80 transition-colors"
          >
            {isMuted ? (
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2M9 9v6h4l5 5V4L13 9H9z" />
              </svg>
            ) : (
              <svg className="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.536 8.464a5 5 0 010 7.072M9 9v6h4l5 5V4L13 9H9z" />
              </svg>
            )}
          </button>
        )}

        {videoUrl && (
          <p className={`absolute bottom-3 left-4 text-[10px] font-mono uppercase tracking-wider transition-opacity duration-200 ${isHovering ? 'opacity-0' : 'opacity-80 text-white'} drop-shadow`}>
            Hover to preview
          </p>
        )}
      </div>

      {/* Text zone — solid panel, always legible regardless of what's playing above */}
      <div className="shrink-0 bg-[#121212] border-t border-white/10 p-5 space-y-2">
        <CategoryTag label="Motion Graphics" />
        <h3 className="text-xl font-bold font-display text-white tracking-tight leading-snug">{card.title}</h3>
        <p className="text-sm text-white/60 leading-relaxed line-clamp-2">{card.description}</p>
        {card.metadata && (
          <div className="flex gap-4 text-[11px] text-white/40 font-mono uppercase tracking-wider pt-1">
            <span>Complexity / {card.metadata.complexity}</span>
            <span>Style / {card.metadata.style}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export { EditingCard, MusicCard, TypographyCard, ColorCard, MotionGraphicsCard };

export const SwipeCard = ({ card, stackIndex = 0 }) => {
  const renderCardContent = () => {
    switch (card.category) {
      case 'music_style':
        return <MusicCard card={card} />;
      case 'typography':
        return <TypographyCard card={card} />;
      case 'color_grading':
        return <ColorCard card={card} />;
      case 'motion_graphics':
        return <MotionGraphicsCard card={card} />;
      case 'editing_style':
      default:
        return <EditingCard card={card} />;
    }
  };

  const isTop = stackIndex === 0;

  return (
    <motion.div
      data-testid={`swipe-card-${card.category}`}
      className="swipe-card absolute w-full max-w-md aspect-[3/4] rounded-3xl overflow-hidden shadow-2xl border border-white/10 select-none"
      initial={isTop ? { scale: 0.94, opacity: 0, y: 12 } : false}
      animate={isTop ? { scale: 1, opacity: 1, y: 0 } : { scale: 1 - stackIndex * 0.04, y: stackIndex * 14, opacity: 1 - stackIndex * 0.35 }}
      exit={{ scale: 0.9, opacity: 0, transition: { duration: 0.2 } }}
      transition={{ type: 'spring', stiffness: 260, damping: 26 }}
    >
      {renderCardContent()}
    </motion.div>
  );
};

export default SwipeCard;