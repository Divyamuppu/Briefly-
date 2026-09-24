import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, ArrowRight, ArrowLeft, Loader2, Sparkles, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { toast } from 'sonner';
import {
  EditingCard,
  MusicCard,
  TypographyCard,
  ColorCard,
  MotionGraphicsCard,
} from '@/components/SwipeCard';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CATEGORY_ORDER = ['editing_style', 'music_style', 'color_grading', 'typography', 'motion_graphics'];

// Clients see every option in a category but can select at most this many per category.
const MAX_PICKS_PER_CATEGORY = 3;

const CATEGORY_META = {
  editing_style: { label: 'Editing Style', hint: 'How should the video be cut and paced?' },
  music_style: { label: 'Music', hint: 'What should the soundtrack feel like?' },
  color_grading: { label: 'Color & Shades', hint: 'What color treatment fits your brand?' },
  typography: { label: 'Font', hint: 'Which typeface should carry your message?' },
  motion_graphics: { label: 'Motion Graphics', hint: 'How much visual complexity do you want?' },
};

const CARD_RENDERERS = {
  editing_style: EditingCard,
  music_style: MusicCard,
  color_grading: ColorCard,
  typography: TypographyCard,
  motion_graphics: MotionGraphicsCard,
};

const SwipeInterface = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();

  const [cardsByCategory, setCardsByCategory] = useState({});
  const [loading, setLoading] = useState(true);
  const [categoryStep, setCategoryStep] = useState(0);
  const [selections, setSelections] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [recommendations, setRecommendations] = useState({});
  const [videoTypeLabel, setVideoTypeLabel] = useState('');
  const [activeConflicts, setActiveConflicts] = useState([]);

  useEffect(() => {
    const fetchCards = async () => {
      try {
        const response = await axios.get(`${API}/cards`);
        const grouped = {};
        response.data.forEach((card) => {
          if (!grouped[card.category]) grouped[card.category] = [];
          if (!grouped[card.category].some((c) => c.title === card.title)) {
            grouped[card.category].push(card);
          }
        });
        setCardsByCategory(grouped);
      } catch (error) {
        console.error('Error fetching cards:', error);
        toast.error('Failed to load style options');
      } finally {
        setLoading(false);
      }
    };
    fetchCards();
  }, []);

  // Load AI-style suggestions based on the project's video type, so a first-time
  // user gets a sensible recommended pick per category instead of a blank slate.
  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        const projectRes = await axios.get(`${API}/projects/${projectId}`);
        const videoType = projectRes.data.video_type;
        if (!videoType) return;
        setVideoTypeLabel(videoType.replace(/_/g, ' '));
        const suggestionsRes = await axios.get(`${API}/suggestions/${videoType}`);
        setRecommendations(suggestionsRes.data || {});
      } catch (error) {
        // Non-critical — the flow works fine without recommendations, so fail silently.
        console.error('Error fetching recommendations:', error);
      }
    };
    if (projectId) fetchRecommendations();
  }, [projectId]);

  const currentCategory = CATEGORY_ORDER[categoryStep];
  const currentCards = cardsByCategory[currentCategory] || [];
  const CardRenderer = CARD_RENDERERS[currentCategory];
  const isLastStep = categoryStep === CATEGORY_ORDER.length - 1;
  const currentSelections = selections[currentCategory] || [];
  const hasSelectionForStep = currentSelections.length > 0;
  const rawRecommendation = recommendations[currentCategory];
  const recommendedTitles = Array.isArray(rawRecommendation)
    ? rawRecommendation
    : rawRecommendation
    ? [rawRecommendation]
    : [];

  const checkConflicts = async (nextSelections) => {
    const selectionTitles = {};
    Object.entries(nextSelections).forEach(([category, cards]) => {
      if (cards && cards.length) selectionTitles[category] = cards.map((c) => c.title);
    });
    const totalPicks = Object.values(selectionTitles).reduce((sum, titles) => sum + titles.length, 0);
    if (totalPicks < 2) {
      setActiveConflicts([]);
      return;
    }
    try {
      const res = await axios.post(`${API}/check-conflicts`, { selections: selectionTitles });
      setActiveConflicts(res.data.conflicts || []);
    } catch (error) {
      console.error('Error checking conflicts:', error);
    }
  };

  // Multi-select with a cap: a client can pick up to MAX_PICKS_PER_CATEGORY options
  // in a single category. Tapping a selected card removes it; tapping a new one adds it,
  // unless the cap is already reached (then we nudge them to deselect one first).
  const toggleCard = (card) => {
    const existing = selections[currentCategory] || [];
    const alreadySelected = existing.some((c) => c.title === card.title);
    if (!alreadySelected && existing.length >= MAX_PICKS_PER_CATEGORY) {
      toast.error(`You can select up to ${MAX_PICKS_PER_CATEGORY} options in this category`);
      return;
    }
    const nextForCategory = alreadySelected
      ? existing.filter((c) => c.title !== card.title)
      : [...existing, card];
    const next = { ...selections, [currentCategory]: nextForCategory };
    setSelections(next);
    checkConflicts(next);
  };

  const goBack = () => {
    if (categoryStep > 0) setCategoryStep((s) => s - 1);
  };

  const goNext = async () => {
    if (!hasSelectionForStep) {
      toast.error('Pick an option to continue');
      return;
    }
    if (!isLastStep) {
      setCategoryStep((s) => s + 1);
      return;
    }
    await finishAndSubmit();
  };

  const finishAndSubmit = async () => {
    setSubmitting(true);
    try {
      const swipeRequests = [];
      CATEGORY_ORDER.forEach((category) => {
        const cards = selections[category] || [];
        cards.forEach((card) => {
          const cardId = `${category}_${card.title.replace(/\s+/g, '_').toLowerCase()}`;
          swipeRequests.push(
            axios.post(`${API}/swipes`, {
              project_id: projectId,
              card_id: cardId,
              action: 'love',
            })
          );
        });
      });
      await Promise.all(swipeRequests);
      navigate(`/brief/${projectId}`);
    } catch (error) {
      console.error('Error saving selections:', error);
      toast.error('Failed to save your selections');
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-12 h-12 text-primary animate-spin" />
      </div>
    );
  }

  const progress = ((categoryStep + 1) / CATEGORY_ORDER.length) * 100;

  return (
    <div className="min-h-screen bg-background px-4 py-12">
      <div className="max-w-5xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <p className="text-xs font-mono uppercase tracking-[0.25em] text-primary">
            Category {categoryStep + 1} of {CATEGORY_ORDER.length}
          </p>
          <h1 className="text-3xl md:text-4xl font-bold font-display text-foreground">
            {CATEGORY_META[currentCategory]?.label}
          </h1>
          <p className="text-sm text-muted-foreground">{CATEGORY_META[currentCategory]?.hint}</p>
          <p className="text-xs text-muted-foreground/80">
            Tap to select — up to {MAX_PICKS_PER_CATEGORY} per category
            {` · ${currentSelections.length}/${MAX_PICKS_PER_CATEGORY} selected`}
          </p>
        </div>

        <Progress value={progress} className="h-1.5 bg-secondary" data-testid="category-progress" />

        {/* AI suggestion hint for this category, based on the project's video type */}
        {recommendedTitles.length > 0 && !hasSelectionForStep && (
          <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-primary/10 border border-primary/25 text-sm text-primary/90" data-testid="recommendation-hint">
            <Sparkles className="w-4 h-4 shrink-0" />
            <span>
              For a {videoTypeLabel} video, we'd suggest{' '}
              <strong>{recommendedTitles.join(' and ')}</strong> here.
            </span>
          </div>
        )}

        {/* Conflict warnings between current selections */}
        {activeConflicts.length > 0 && (
          <div className="space-y-2" data-testid="conflict-warnings">
            {activeConflicts.map((conflict, idx) => (
              <div key={idx} className="flex items-start gap-2 px-4 py-2.5 rounded-xl bg-accent/10 border border-accent/25 text-sm text-accent/90">
                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{conflict.message}</span>
              </div>
            ))}
          </div>
        )}

        {/* Grid of tappable options for this category */}
        <AnimatePresence mode="wait">
          <motion.div
            key={currentCategory}
            initial={{ opacity: 0, x: 24 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -24 }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            {currentCards.map((card) => {
              const isSelected = currentSelections.some((c) => c.title === card.title);
              const isRecommended = recommendedTitles.includes(card.title);
              return (
                <button
                  key={card.title}
                  type="button"
                  data-testid={`option-${currentCategory}-${card.title.replace(/\s+/g, '_').toLowerCase()}`}
                  onClick={() => toggleCard(card)}
                  className={`relative text-left rounded-3xl overflow-hidden aspect-[3/4] border transition-all duration-300 ${
                    isSelected
                      ? 'ring-2 ring-primary border-primary shadow-[0_0_40px_-10px_rgba(147,112,246,0.5)] scale-[1.02]'
                      : 'border-border hover:border-primary/40 hover:scale-[1.01]'
                  }`}
                >
                  <CardRenderer card={card} />
                  {isSelected && (
                    <div className="absolute top-4 right-4 w-9 h-9 rounded-full bg-primary flex items-center justify-center shadow-lg z-10">
                      <Check className="w-5 h-5 text-black" />
                    </div>
                  )}
                  {isRecommended && !isSelected && (
                    <div className="absolute top-4 left-4 inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-black/70 border border-primary/50 backdrop-blur-md z-10">
                      <Sparkles className="w-3 h-3 text-primary" />
                      <span className="text-[9px] font-mono uppercase tracking-wider text-primary">Suggested</span>
                    </div>
                  )}
                </button>
              );
            })}
          </motion.div>
        </AnimatePresence>

        {/* Navigation */}
        <div className="flex items-center justify-between pt-4 pb-16">
          <Button
            type="button"
            onClick={goBack}
            disabled={categoryStep === 0}
            variant="outline"
            className="h-14 px-8 rounded-full border-2 border-border bg-secondary/40 hover:border-primary/40 disabled:opacity-30"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>

          <Button
            data-testid="next-category-btn"
            type="button"
            onClick={goNext}
            disabled={submitting}
            className="h-14 px-10 rounded-full bg-primary text-black font-bold uppercase tracking-wide hover:bg-primary/90 shadow-[0_0_30px_-8px_rgba(147,112,246,0.5)] disabled:opacity-60"
          >
            {submitting ? 'Generating Brief...' : isLastStep ? 'Generate Brief' : 'Next Category'}
            {!submitting && <ArrowRight className="w-4 h-4 ml-2" />}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default SwipeInterface;