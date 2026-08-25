import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Film, Sparkles, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import ThemeToggle, { useTheme } from '@/components/ThemeToggle';

const Landing = () => {
  const navigate = useNavigate();
  const [theme, setTheme] = useTheme();

  return (
    <div className="relative min-h-screen bg-background flex items-center justify-center px-4 py-6">
      {/* Compact badge + theme toggle, tucked in the top-right corner */}
      <div className="absolute top-6 right-6 flex items-center gap-3">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border border-primary/20 bg-primary/5">
          <Sparkles className="w-3 h-3 text-primary" />
          <span className="text-[10px] font-mono uppercase tracking-[0.15em] text-primary">Creative Brief Generator</span>
        </div>
        <ThemeToggle theme={theme} setTheme={setTheme} />
      </div>

      <div className="max-w-4xl w-full text-center space-y-10">
        <div className="space-y-6">
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight leading-tight font-display text-foreground">
            Let's build your <span className="text-primary italic">creative brief</span>
          </h1>

          <p className="text-lg md:text-xl leading-relaxed text-muted-foreground max-w-2xl mx-auto">
            Create professional video production briefs in minutes. Streamline your
            pre-production workflow with a fast, intuitive brief generator.
          </p>
        </div>

        <Button
          data-testid="create-project-btn"
          onClick={() => navigate('/video-type')}
          className="h-16 px-14 text-lg rounded-full bg-primary text-primary-foreground font-bold uppercase tracking-wide hover:bg-primary/90 transition-all duration-300 shadow-[0_0_30px_-8px_rgba(147,112,246,0.5)]"
        >
          Create New Project
        </Button>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl mx-auto pt-8">
          <div className="p-6 rounded-xl bg-card border border-border hover:border-primary/30 transition-colors space-y-3 text-left">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
              <Zap className="w-5 h-5 text-primary" />
            </div>
            <h3 className="text-base font-semibold font-display text-foreground">Quick Setup</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">Start in under a minute. No complex forms.</p>
          </div>

          <div className="p-6 rounded-xl bg-card border border-border hover:border-primary/30 transition-colors space-y-3 text-left">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
              <Film className="w-5 h-5 text-primary" />
            </div>
            <h3 className="text-base font-semibold font-display text-foreground">Smart Analysis</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">Preference tracking builds your creative direction.</p>
          </div>

          <div className="p-6 rounded-xl bg-card border border-border hover:border-primary/30 transition-colors space-y-3 text-left">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-primary" />
            </div>
            <h3 className="text-base font-semibold font-display text-foreground">Export Ready</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">Get a professional PDF brief instantly.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Landing;