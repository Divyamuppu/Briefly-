import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';

const SplashScreen = () => {
  const navigate = useNavigate();

  return (
    <div
      data-testid="splash-screen"
      onClick={() => navigate('/home')}
      className="relative min-h-screen bg-background flex flex-col items-center justify-center px-4 cursor-pointer select-none overflow-hidden"
    >
      {/* Blurred background image */}
      <div
        className="absolute inset-0 bg-cover bg-center scale-110"
        style={{
          backgroundImage: "url('/assets/splash-camera.jpg')",
          filter: 'blur(18px) brightness(0.45)',
        }}
      />
      <div className="absolute inset-0 bg-background/60" />

      {/* Foreground content, kept sharp and legible */}
      <motion.h1
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.9, ease: 'easeOut' }}
        className="relative z-10 text-7xl md:text-9xl font-bold tracking-tight leading-none font-display text-primary drop-shadow-[0_4px_24px_rgba(0,0,0,0.6)]"
      >
        BRIEFLY
      </motion.h1>

      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.9, delay: 0.35, ease: 'easeOut' }}
        className="relative z-10 text-sm md:text-base font-mono uppercase tracking-[0.4em] text-white/80 mt-6 drop-shadow-[0_2px_12px_rgba(0,0,0,0.6)]"
      >
        Frames that speak
      </motion.p>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8, delay: 1.4 }}
        className="absolute z-10 bottom-12 text-xs font-mono uppercase tracking-[0.25em] text-white/50"
      >
        Tap anywhere to continue
      </motion.p>
    </div>
  );
};

export default SplashScreen;
