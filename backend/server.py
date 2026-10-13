from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from neon_db import (
    cards_get_all, cards_resync_category,
    video_types_get_all, video_types_resync,
    project_get, project_create, project_update,
    swipe_create, swipes_get_for_project,
)
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as pdf_canvas
import io
import random
import asyncio
import requests
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Pydantic Models
class BrandTones(BaseModel):
    fun_serious: int = Field(ge=-100, le=100)
    luxury_casual: int = Field(ge=-100, le=100)
    corporate_playful: int = Field(ge=-100, le=100)

class Reference(BaseModel):
    type: str
    value: str
    name: Optional[str] = None

class ProjectCreate(BaseModel):
    project_name: str
    video_length: str
    platform: str
    aspect_ratio: str
    target_audience: str
    purpose: str
    business_model: str
    narrative_technical: int
    brand_tones: BrandTones
    references: Optional[List[Reference]] = []
    voice_note_url: Optional[str] = None
    video_type: Optional[str] = None
    video_sub_option: Optional[str] = None
    additional_notes: Optional[str] = None

class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_name: str
    video_length: str
    platform: str
    aspect_ratio: str
    target_audience: str
    purpose: str
    business_model: str
    narrative_technical: int
    brand_tones: BrandTones
    references: Optional[List[Reference]] = []
    voice_note_url: Optional[str] = None
    video_type: Optional[str] = None
    video_sub_option: Optional[str] = None
    additional_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SwipeCard(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: str
    title: str
    description: str
    image_url: str
    metadata: Optional[Dict[str, Any]] = None

class SwipeAction(BaseModel):
    project_id: str
    card_id: str
    action: str

class SwipeResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    card_id: str
    action: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BriefSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")
    project_id: str
    project_name: str
    project_details: Dict[str, Any]
    editing_style: Dict[str, Any]
    color_direction: Dict[str, Any]
    music_direction: Dict[str, Any]
    typography_direction: Dict[str, Any]
    motion_graphics: Dict[str, Any]
    total_swipes: int
    ai_summary: str

# AI-Generated Card Data with Enhanced Media
CARD_SEED_DATA = {
    "editing_style": [
        {"title": "Fast-Paced Social Cuts", "description": "Quick, energetic transitions every 1-2 seconds.", "metadata": {"pace": "fast", "shot_duration": "1-2s"}, "video_url": "/assets/video-types/fast_pace_cut.mp4", "image_url": "https://images.pexels.com/photos/6255898/pexels-photo-6255898.jpeg?auto=compress&cs=tinysrgb&w=800"},
        {"title": "Cinematic Slow Pacing", "description": "Deliberate, measured cuts emphasizing mood.", "metadata": {"pace": "slow", "shot_duration": "5-8s"}, "video_url": "https://assets.mixkit.co/videos/5565/5565-360.mp4", "image_url": "https://picsum.photos/id/24/800/1000"},
        {"title": "Documentary Style", "description": "Natural, interview-based with b-roll overlay.", "metadata": {"pace": "medium", "shot_duration": "3-5s"}, "video_url": "https://assets.mixkit.co/videos/6052/6052-360.mp4", "image_url": "https://picsum.photos/id/31/800/1000", "gallery": ["https://images.pexels.com/photos/10464783/pexels-photo-10464783.jpeg?auto=compress&cs=tinysrgb&w=800", "https://images.pexels.com/photos/10464790/pexels-photo-10464790.jpeg?auto=compress&cs=tinysrgb&w=800", "https://images.pexels.com/photos/10464451/pexels-photo-10464451.jpeg?auto=compress&cs=tinysrgb&w=800", "https://images.pexels.com/photos/10464470/pexels-photo-10464470.jpeg?auto=compress&cs=tinysrgb&w=800", "https://images.pexels.com/photos/10464792/pexels-photo-10464792.jpeg?auto=compress&cs=tinysrgb&w=800"]},
        {"title": "Music Video Style", "description": "Beat-synced editing with creative transitions.", "metadata": {"pace": "fast", "shot_duration": "0.5-2s"}, "video_url": "https://assets.mixkit.co/5tkfgsbokjzfgfu5emasqjkhym86", "image_url": "https://picsum.photos/id/38/800/1000"},
        {"title": "Vlog Aesthetic", "description": "Personal, handheld feel with jump cuts.", "metadata": {"pace": "medium", "shot_duration": "2-4s"}, "video_url": "https://assets.mixkit.co/videos/41272/41272-360.mp4", "image_url": "https://picsum.photos/id/45/800/1000"},
        {"title": "Commercial Polish", "description": "Refined, professional cuts with smooth transitions.", "metadata": {"pace": "medium", "shot_duration": "3-4s"}, "video_url": "https://assets.mixkit.co/videos/4809/4809-720.mp4", "image_url": "https://picsum.photos/id/52/800/1000"},
        {"title": "Action-Packed Montage", "description": "Dynamic, high-energy sequences building excitement.", "metadata": {"pace": "fast", "shot_duration": "0.5-1.5s"}, "video_url": "https://assets.mixkit.co/videos/43483/43483-360.mp4", "image_url": "https://picsum.photos/id/59/800/1000"},
        {"title": "Avant Garde", "description": "Experimental, artistic editing pushing creative boundaries.", "metadata": {"pace": "fast", "shot_duration": "1-3s"}, "video_url": "https://assets.mixkit.co/videos/43434/43434-720.mp4", "image_url": "https://picsum.photos/id/66/800/1000"},
        {"title": "Traditional TVC", "description": "Classic television commercial structure with narrative arc.", "metadata": {"pace": "medium", "shot_duration": "3-5s"}, "video_url": "https://assets.mixkit.co/4uubj0hrt8so60orc1e2bbakh6v4", "image_url": "https://picsum.photos/id/73/800/1000"},
        {"title": "Fast Editorial Cut", "description": "Quick energetic style, exploring places, themes, cities and concepts.", "metadata": {"pace": "fast", "shot_duration": "3s"}, "video_url": "https://assets.mixkit.co/la3a23waeronjzwjlmziqf0acpdq", "image_url": "https://picsum.photos/id/80/800/1000", "gallery": ["https://images.pexels.com/photos/18999437/pexels-photo-18999437.jpeg?auto=compress&cs=tinysrgb&w=800", "https://images.pexels.com/photos/4881146/pexels-photo-4881146.jpeg?auto=compress&cs=tinysrgb&w=800", "https://images.pexels.com/photos/119777/pexels-photo-119777.jpeg?auto=compress&cs=tinysrgb&w=800", "https://images.pexels.com/photos/6793710/pexels-photo-6793710.jpeg?auto=compress&cs=tinysrgb&w=800", "https://images.pexels.com/photos/4238107/pexels-photo-4238107.jpeg?auto=compress&cs=tinysrgb&w=800"]},
        {"title": "Product Edit (High End)", "description": "Artistically showcasing a product with context and juxtaposition.", "metadata": {"pace": "medium", "shot_duration": "6s"}, "video_url": "https://assets.mixkit.co/videos/44070/44070-360.mp4", "image_url": "https://images.pexels.com/photos/2113994/pexels-photo-2113994.jpeg?auto=compress&cs=tinysrgb&w=800"},
    ],
    "color_grading": [
        {"title": "Warm Cinematic Tones", "description": "Golden hour feel with warm oranges and yellows. Inviting and nostalgic.", "metadata": {"palette": "warm", "mood": "nostalgic"}, "color_palette": ["#FF8C42", "#FFD93D", "#FFA500"], "color_overlay": "linear-gradient(135deg, rgba(255,140,66,0.3), rgba(255,217,61,0.3))", "color_filter": "saturate(1.2) contrast(1.1) brightness(1.05)", "image_url": "/assets/color/warm_cinematic_tones.jpg"},
        {"title": "Pastel Palette", "description": "Soft, desaturated colors with gentle pinks and blues. Dreamy and whimsical.", "metadata": {"palette": "pastel", "mood": "dreamy"}, "color_palette": ["#FFB6D9", "#A8D8EA", "#E7BCDE"], "color_overlay": "linear-gradient(135deg, rgba(255,182,217,0.4), rgba(168,216,234,0.4))", "color_filter": "saturate(0.7) brightness(1.1)", "image_url": "/assets/color/pastel_palette.jpg"},
        {"title": "Neon Cyberpunk", "description": "Vibrant purples, blues, and magentas with high contrast. Futuristic and edgy.", "metadata": {"palette": "neon", "mood": "futuristic"}, "color_palette": ["#FF006E", "#8338EC", "#3A86FF"], "color_overlay": "linear-gradient(135deg, rgba(255,0,110,0.3), rgba(131,56,236,0.3))", "color_filter": "saturate(1.5) contrast(1.3)", "image_url": "/assets/color/neon_cyberpunk.png", "gallery": ["https://images.pexels.com/photos/10175091/pexels-photo-10175091.jpeg?auto=compress&cs=tinysrgb&w=800", "https://images.pexels.com/photos/31689562/pexels-photo-31689562.jpeg?auto=compress&cs=tinysrgb&w=800", "https://images.pexels.com/photos/18867525/pexels-photo-18867525.jpeg?auto=compress&cs=tinysrgb&w=800", "https://images.pexels.com/photos/32452320/pexels-photo-32452320.jpeg?auto=compress&cs=tinysrgb&w=800", "https://images.pexels.com/photos/1718758/pexels-photo-1718758.jpeg?auto=compress&cs=tinysrgb&w=800"]},
        {"title": "High Contrast Dramatic", "description": "Deep blacks and bright highlights. Bold and impactful visual style.", "metadata": {"palette": "high-contrast", "mood": "dramatic"}, "color_palette": ["#000000", "#FFFFFF", "#8B0000"], "color_filter": "contrast(1.5) brightness(0.9)", "image_url": "/assets/color/high_contrast_dramatic.png"},
        {"title": "Soft Commercial Look", "description": "Clean, natural colors with slight warmth. Professional and approachable.", "metadata": {"palette": "natural", "mood": "professional"}, "color_palette": ["#F5E6D3", "#C9ADA7", "#9A8C98"], "color_filter": "saturate(0.9) brightness(1.05) sepia(0.1)", "image_url": "/assets/color/soft_commercial_look.jpg"},
        {"title": "Desaturated Moody", "description": "Low saturation with cool tones. Serious and contemplative atmosphere.", "metadata": {"palette": "desaturated", "mood": "moody"}, "color_palette": ["#6C757D", "#495057", "#ADB5BD"], "color_filter": "saturate(0.5) brightness(0.8)", "image_url": "/assets/color/desaturated_moody.png"},
        {"title": "Vibrant Pop Colors", "description": "Saturated, punchy colors with strong primaries. Energetic and youthful.", "metadata": {"palette": "vibrant", "mood": "energetic"}, "color_palette": ["#FF005C", "#FFD500", "#00F5FF"], "color_overlay": "linear-gradient(135deg, rgba(255,0,92,0.2), rgba(0,245,255,0.2))", "color_filter": "saturate(1.6) contrast(1.2)", "image_url": "https://picsum.photos/id/136/800/1000"},
        {"title": "Film Noir", "description": "Black and white with dramatic shadows. Classic and mysterious.", "metadata": {"palette": "monochrome", "mood": "mysterious"}, "color_palette": ["#000000", "#808080", "#FFFFFF"], "color_filter": "grayscale(1) contrast(1.3)", "image_url": "/assets/color/film_noir.png"},
    ],
    "music_style": [
        {"title": "Indie Electronic", "description": "Synth-driven melodies with organic textures. Modern and creative.", "metadata": {"genre": "electronic", "tempo": "110-130 BPM"}, "audio_url": "/assets/music/indie_electronic.mp3", "image_url": "https://images.pexels.com/photos/844928/pexels-photo-844928.jpeg?auto=compress&cs=tinysrgb&w=800"},
        {"title": "Orchestral Cinematic", "description": "Sweeping strings and epic brass. Grand and emotive.", "metadata": {"genre": "orchestral", "tempo": "80-100 BPM"}, "audio_url": "/assets/music/orchestral_cinematic.mp3", "image_url": "https://images.pexels.com/photos/32024630/pexels-photo-32024630.jpeg?auto=compress&cs=tinysrgb&w=800"},
        {"title": "Hip Hop Trap", "description": "Heavy 808s with punchy hi-hats. Urban and confident.", "metadata": {"genre": "hip-hop", "tempo": "140-160 BPM"}, "audio_url": "/assets/music/hip_hop_trap.mp3", "image_url": "https://picsum.photos/id/164/800/1000"},
        {"title": "Lo-fi Chill", "description": "Relaxed beats with vinyl crackle. Mellow and contemplative.", "metadata": {"genre": "lo-fi", "tempo": "70-90 BPM"}, "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3", "image_url": "https://picsum.photos/id/171/800/1000"},
        {"title": "Corporate Uplifting", "description": "Motivational piano with light percussion. Professional and optimistic.", "metadata": {"genre": "corporate", "tempo": "100-120 BPM"}, "audio_url": "/assets/music/corporate_uplifting.mp3", "image_url": "https://picsum.photos/id/178/800/1000"},
        {"title": "Ambient Soundscape", "description": "Atmospheric pads with subtle movements. Ethereal and spacious.", "metadata": {"genre": "ambient", "tempo": "60-80 BPM"}, "audio_url": "/assets/music/ambient_soundscape.mp3", "image_url": "https://picsum.photos/id/185/800/1000", "gallery": ["https://images.pexels.com/photos/14845824/pexels-photo-14845824.jpeg?auto=compress&cs=tinysrgb&w=800", "https://images.pexels.com/photos/13061095/pexels-photo-13061095.jpeg?auto=compress&cs=tinysrgb&w=800", "https://images.pexels.com/photos/14590274/pexels-photo-14590274.jpeg?auto=compress&cs=tinysrgb&w=800", "https://images.pexels.com/photos/16356229/pexels-photo-16356229.jpeg?auto=compress&cs=tinysrgb&w=800", "https://images.pexels.com/photos/13367244/pexels-photo-13367244.jpeg?auto=compress&cs=tinysrgb&w=800"]},
        {"title": "Rock Energetic", "description": "Electric guitars with driving drums. Powerful and rebellious.", "metadata": {"genre": "rock", "tempo": "120-140 BPM"}, "audio_url": "/assets/music/rock_energetic.mp3", "image_url": "https://picsum.photos/id/192/800/1000"},
        {"title": "Jazz Smooth", "description": "Saxophone and upright bass. Sophisticated and timeless.", "metadata": {"genre": "jazz", "tempo": "90-110 BPM"}, "audio_url": "/assets/music/jazz_smooth.mp3", "image_url": "https://picsum.photos/id/199/800/1000"},
        {"title": "Bollywood / Indian Pop", "description": "Vibrant Indian melodies blending traditional and modern sounds.", "metadata": {"genre": "indian-pop", "tempo": "100-140 BPM"}, "audio_url": "/assets/music/bollywood_indian_pop.mp3", "image_url": "https://picsum.photos/id/1011/800/1000"},
        {"title": "Regional / Folk", "description": "Authentic regional folk instruments with earthy, rooted grooves.", "metadata": {"genre": "folk", "tempo": "80-120 BPM"}, "audio_url": "/assets/music/regional_folk.mp3", "image_url": "https://picsum.photos/id/1025/800/1000"},
    ],
    "typography": [
        {"title": "Modern Geometric Sans", "description": "Clean, precise letterforms with geometric construction. Contemporary and minimal.", "metadata": {"style": "sans-serif", "weight": "medium"}, "font_name": "Montserrat", "sample_text": "CREATIVE DIRECTION", "image_url": "https://picsum.photos/id/206/800/1000"},
        {"title": "Elegant Luxury Serif", "description": "Refined serifs with high contrast. Timeless and sophisticated.", "metadata": {"style": "serif", "weight": "light"}, "font_name": "Playfair Display", "sample_text": "Premium Quality", "image_url": "https://picsum.photos/id/213/800/1000"},
        {"title": "Bold Condensed", "description": "Narrow, impactful letters with strong presence. Commanding and direct.", "metadata": {"style": "condensed", "weight": "bold"}, "font_name": "Bebas Neue", "sample_text": "IMPACT", "image_url": "https://picsum.photos/id/220/800/1000"},
        {"title": "Handwritten Style", "description": "Organic, personal letterforms with natural flow. Authentic and warm.", "metadata": {"style": "script", "weight": "regular"}, "font_name": "Dancing Script", "sample_text": "Authentic Stories", "image_url": "https://picsum.photos/id/227/800/1000"},
        {"title": "Retro Display", "description": "Vintage-inspired characters with personality. Nostalgic and playful.", "metadata": {"style": "display", "weight": "bold"}, "font_name": "Righteous", "sample_text": "RETRO VIBES", "image_url": "https://picsum.photos/id/234/800/1000"},
        {"title": "Minimalist Thin", "description": "Delicate, lightweight letterforms. Elegant and modern.", "metadata": {"style": "sans-serif", "weight": "thin"}, "font_name": "Raleway", "sample_text": "Elegance", "image_url": "https://picsum.photos/id/241/800/1000"},
        {"title": "Grunge Textured", "description": "Distressed, edgy typography. Raw and rebellious.", "metadata": {"style": "display", "weight": "bold"}, "font_name": "Bungee", "sample_text": "RAW ENERGY", "image_url": "https://picsum.photos/id/248/800/1000"},
        {"title": "Futuristic Tech", "description": "Angular, digital-inspired letterforms. Innovative and cutting-edge.", "metadata": {"style": "sans-serif", "weight": "medium"}, "font_name": "Orbitron", "sample_text": "FUTURE TECH", "image_url": "https://picsum.photos/id/255/800/1000"},
    ],
    "motion_graphics": [
        {"title": "Minimal Line Art", "description": "Simple, elegant line animations. Clean and professional.", "metadata": {"complexity": "low", "style": "minimal"}, "image_url": "https://picsum.photos/id/262/800/1000", "video_url": "/assets/video-types/line_art_animation.mp4"},
        {"title": "3D Product Showcase", "description": "Rotating 3D elements with depth. Modern and dimensional.", "metadata": {"complexity": "high", "style": "3d"}, "image_url": "https://picsum.photos/id/269/800/1000", "video_url": "https://assets.mixkit.co/videos/42957/42957-720.mp4"},
        {"title": "Kinetic Typography", "description": "Animated text with motion. Dynamic and engaging.", "metadata": {"complexity": "medium", "style": "text"}, "image_url": "https://picsum.photos/id/276/800/1000", "video_url": "https://assets.mixkit.co/video-templates/617/mixkit-617-360.mp4"},
        {"title": "Flat Icon Animation", "description": "Smooth icon transitions. Friendly and accessible.", "metadata": {"complexity": "low", "style": "flat"}, "image_url": "https://picsum.photos/id/283/800/1000", "video_url": "https://assets.mixkit.co/video-templates/571/mixkit-571-360.mp4"},
        {"title": "Particle Effects", "description": "Flowing particles and organic motion. Sophisticated and fluid.", "metadata": {"complexity": "high", "style": "particles"}, "image_url": "https://picsum.photos/id/290/800/1000", "video_url": "https://assets.mixkit.co/videos/18142/18142-360.mp4"},
        {"title": "Infographic Animation", "description": "Data visualization in motion. Clear and informative.", "metadata": {"complexity": "medium", "style": "data"}, "image_url": "https://picsum.photos/id/297/800/1000", "video_url": "https://assets.mixkit.co/videos/5404/5404-720.mp4"},
        {"title": "Liquid Motion", "description": "Smooth, fluid transitions. Organic and premium.", "metadata": {"complexity": "high", "style": "liquid"}, "image_url": "https://picsum.photos/id/304/800/1000", "video_url": "https://assets.mixkit.co/video-templates/608/mixkit-608-360.mp4"},
        {"title": "Geometric Shapes", "description": "Bold geometric animations. Strong and modern.", "metadata": {"complexity": "medium", "style": "geometric"}, "image_url": "https://picsum.photos/id/311/800/1000", "video_url": "https://assets.mixkit.co/video-templates/609/mixkit-609-360.mp4", "gallery": ["https://images.pexels.com/photos/32381944/pexels-photo-32381944.jpeg?auto=compress&cs=tinysrgb&w=800", "https://images.pexels.com/photos/33950026/pexels-photo-33950026.jpeg?auto=compress&cs=tinysrgb&w=800", "https://images.pexels.com/photos/12732215/pexels-photo-12732215.jpeg?auto=compress&cs=tinysrgb&w=800", "https://images.pexels.com/photos/4252167/pexels-photo-4252167.jpeg?auto=compress&cs=tinysrgb&w=800", "https://images.pexels.com/photos/13129478/pexels-photo-13129478.jpeg?auto=compress&cs=tinysrgb&w=800"]},
    ]
}

CATEGORY_ORDER = ["editing_style", "music_style", "color_grading", "typography", "motion_graphics"]

# Image URLs from design guidelines
IMAGE_POOL = [
    "https://images.unsplash.com/photo-1762792668677-29c149b70e9b?crop=entropy&cs=srgb&fm=jpg&q=85",
    "https://images.unsplash.com/photo-1602404454154-a2dc6b0a7223?crop=entropy&cs=srgb&fm=jpg&q=85",
    "https://images.unsplash.com/photo-1762354766808-92f8ad416174?crop=entropy&cs=srgb&fm=jpg&q=85",
    "https://images.unsplash.com/photo-1558707538-c56435bdcdf3?crop=entropy&cs=srgb&fm=jpg&q=85",
    "https://images.unsplash.com/photo-1686061592315-af9342dc8d74?crop=entropy&cs=srgb&fm=jpg&q=85",
    "https://images.unsplash.com/photo-1529257608761-0ef888111001?crop=entropy&cs=srgb&fm=jpg&q=85",
    "https://images.unsplash.com/photo-1574169208507-84376144848b?crop=entropy&cs=srgb&fm=jpg&q=85",
    "https://images.unsplash.com/photo-1611162617474-5b21e879e113?crop=entropy&cs=srgb&fm=jpg&q=85",
]

def _slug(title: str) -> str:
    """A stable, readable identifier for each card, derived from its title.
    (Postgres text columns don't have Firebase's character restrictions, but we
    keep this simple/consistent scheme since the frontend generates matching IDs.)"""
    slug = title.strip().lower().replace(' ', '_')
    for ch in ['$', '#', '[', ']', '/', '.']:
        slug = slug.replace(ch, '')
    return slug

def resync_category_cards(category: str):
    """Always overwrites this category's rows with the current CARD_SEED_DATA list on startup.
    This keeps Neon in sync with the code whenever cards are added, removed, renamed, or
    given new media (safe because this is generated reference content, not user-entered data)."""
    items = CARD_SEED_DATA.get(category, [])
    cards_resync_category(category, items)
    logger.info("Resynced %d %s cards into Neon", len(items), category)

def get_all_cards_from_db() -> Dict[str, List[Dict[str, Any]]]:
    """Returns {category: [card_dict, ...]} read from Neon, each card_dict tagged with its slug id."""
    return cards_get_all()

# --- Video Types: live, context-aware sub-options per video type ---
VIDEO_TYPE_SEED_DATA = {
    "ugc": {
        "title": "UGC / Creator Style",
        "description": "Authentic, relatable content from a creator perspective",
        "image": "https://images.unsplash.com/photo-1611162616475-46b635cb6868?w=800&q=80",
        "video": "/assets/video-types/ugc.mp4",
        "sub_options": [
            {"id": "talking_to_camera", "label": "Talking to Camera", "note": "Direct, personal, phone-shot feel"},
            {"id": "day_in_the_life", "label": "Day in the Life", "note": "Loosely narrated, observational"},
            {"id": "unboxing_review", "label": "Review", "note": "Product-first, hands-on demo"},
            {"id": "before_after", "label": "Before & After", "note": "Transformation-driven hook"},
        ],
    },
    "social_ad": {
        "title": "Social Media Ad",
        "description": "Fast-paced, attention-grabbing advertisement for social platforms",
        "image": "https://images.unsplash.com/photo-1611926653458-09294b3142bf?w=800&q=80",
        "video": "/assets/video-types/social_ad.mp4",
        "sub_options": [
            {"id": "reels", "label": "Instagram Reels", "note": "9:16 · under 30s · trending audio"},
            {"id": "tiktok", "label": "LinkedIn", "note": "1:1 or 16:9 · professional, credibility-first tone"},
            {"id": "youtube_shorts", "label": "YouTube Shorts", "note": "9:16 · loopable hook"},
            {"id": "feed_ad", "label": "Feed / Stories Ad", "note": "1:1 or 9:16 · scroll-stopping first 3s"},
        ],
    },
    "corporate": {
        "title": "Corporate / Brand Film",
        "description": "Professional, polished brand storytelling",
        "image": "https://images.unsplash.com/photo-1553877522-43269d4ea984?w=800&q=80",
        "video": "/assets/video-types/corporate.mp4",
        "sub_options": [
            {"id": "brand_manifesto", "label": "Brand Manifesto", "note": "Cinematic, values-led voiceover"},
            {"id": "company_culture", "label": "Company Culture", "note": "Warm, people-first B-roll"},
            {"id": "product_launch", "label": "Product Launch", "note": "Polished, feature-forward"},
            {"id": "investor_deck", "label": "Investor / Pitch Film", "note": "Data-driven, confident tone"},
        ],
    },
    "documentary": {
        "title": "Documentary",
        "description": "In-depth storytelling with interviews and b-roll",
        "image": "https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?w=800&q=80",
        "video": "/assets/video-types/documentary.mp4",
        "sub_options": [
            {"id": "character_driven", "label": "Character-Driven", "note": "Follows one central subject"},
            {"id": "observational", "label": "Observational", "note": "Fly-on-the-wall, minimal narration"},
            {"id": "investigative", "label": "Investigative", "note": "Question-led, research-heavy"},
            {"id": "archival", "label": "Archival / Historical", "note": "Built around found footage"},
        ],
    },
    "narrative_ad": {
        "title": "Narrative Ad",
        "description": "Story-driven commercial with character and plot",
        "image": "https://images.unsplash.com/photo-1485846234645-a62644f84728?w=800&q=80",
        "video": "/assets/video-types/narrative_ad.mp4",
        "sub_options": [
            {"id": "emotional_arc", "label": "Emotional Arc", "note": "Setup, tension, payoff"},
            {"id": "comedic", "label": "Comedic", "note": "Punchline-driven, quick cuts"},
            {"id": "slice_of_life", "label": "Slice of Life", "note": "Relatable, everyday moment"},
            {"id": "aspirational", "label": "Aspirational", "note": "Lifestyle-forward, cinematic"},
        ],
    },
    "interview": {
        "title": "Talking Head / Interview",
        "description": "Conversation-focused with expert or testimonial",
        "image": "https://images.unsplash.com/photo-1478720568477-152d9b164e26?w=800&q=80",
        "video": "/assets/video-types/interview.mp4",
        "sub_options": [
            {"id": "single_subject", "label": "Single Subject", "note": "One expert, direct address"},
            {"id": "panel", "label": "Panel / Multiple Voices", "note": "Cut between speakers"},
            {"id": "testimonial", "label": "Customer Testimonial", "note": "Trust-building, candid"},
            {"id": "qa_format", "label": "Q&A Format", "note": "Interviewer heard, not seen"},
        ],
    },
}

def resync_video_types():
    """Always overwrites video_types with the current VIDEO_TYPE_SEED_DATA on startup.
    This keeps Neon in sync with the code whenever labels, sub-options, or anything else
    here is edited (safe because this is generated reference content, not user-entered data)."""
    video_types_resync(VIDEO_TYPE_SEED_DATA)
    logger.info("Resynced %d video types into Neon", len(VIDEO_TYPE_SEED_DATA))

def get_all_video_types_from_db() -> Dict[str, Dict[str, Any]]:
    return video_types_get_all()

# --- Suggestion Engine ---
# Rule-based (not an external AI call) so it's instant, free, and fully explainable.
# Two jobs: (1) recommend a sensible starting pick per category for a given video type,
# (2) flag when two already-selected styles pull in contradictory directions.

VIDEO_TYPE_RECOMMENDATIONS = {
    "ugc": {
        "editing_style": ["Vlog Aesthetic", "Fast Editorial Cut"],
        "music_style": ["Lo-fi Chill", "Indie Electronic"],
        "color_grading": ["Soft Commercial Look", "Pastel Palette"],
        "typography": ["Handwritten Style", "Retro Display"],
        "motion_graphics": ["Flat Icon Animation", "Particle Effects"],
    },
    "social_ad": {
        "editing_style": ["Fast-Paced Social Cuts", "Music Video Style"],
        "music_style": ["Hip Hop Trap", "Rock Energetic"],
        "color_grading": ["Vibrant Pop Colors", "Neon Cyberpunk"],
        "typography": ["Bold Condensed", "Futuristic Tech"],
        "motion_graphics": ["Kinetic Typography", "Geometric Shapes"],
    },
    "corporate": {
        "editing_style": ["Commercial Polish", "Traditional TVC"],
        "music_style": ["Corporate Uplifting", "Orchestral Cinematic"],
        "color_grading": ["Soft Commercial Look", "High Contrast Dramatic"],
        "typography": ["Modern Geometric Sans", "Minimalist Thin"],
        "motion_graphics": ["Infographic Animation", "3D Product Showcase"],
    },
    "documentary": {
        "editing_style": ["Documentary Style", "Fast Editorial Cut"],
        "music_style": ["Ambient Soundscape", "Jazz Smooth"],
        "color_grading": ["Desaturated Moody", "Film Noir"],
        "typography": ["Minimalist Thin", "Modern Geometric Sans"],
        "motion_graphics": ["Minimal Line Art", "Infographic Animation"],
    },
    "narrative_ad": {
        "editing_style": ["Cinematic Slow Pacing", "Product Edit (High End)"],
        "music_style": ["Orchestral Cinematic", "Ambient Soundscape"],
        "color_grading": ["Warm Cinematic Tones", "Film Noir"],
        "typography": ["Elegant Luxury Serif", "Retro Display"],
        "motion_graphics": ["Liquid Motion", "3D Product Showcase"],
    },
    "interview": {
        "editing_style": ["Documentary Style", "Commercial Polish"],
        "music_style": ["Ambient Soundscape", "Corporate Uplifting"],
        "color_grading": ["High Contrast Dramatic", "Soft Commercial Look"],
        "typography": ["Modern Geometric Sans", "Minimalist Thin"],
        "motion_graphics": ["Minimal Line Art", "Infographic Animation"],
    },
}

# Each style title is tagged with the "vibes" it carries. A style can carry more than one.
VIBE_TAGS = {
    # Editing Style
    "Fast-Paced Social Cuts": {"energetic", "casual"},
    "Cinematic Slow Pacing": {"calm", "luxury"},
    "Documentary Style": {"calm", "serious"},
    "Music Video Style": {"energetic", "playful"},
    "Vlog Aesthetic": {"casual", "playful"},
    "Commercial Polish": {"corporate", "serious"},
    "Action-Packed Montage": {"energetic"},
    "Avant Garde": {"experimental", "playful"},
    "Traditional TVC": {"corporate", "serious"},
    "Fast Editorial Cut": {"energetic", "casual"},
    "Product Edit (High End)": {"luxury", "serious"},
    # Color Grading
    "Warm Cinematic Tones": {"luxury", "calm"},
    "Pastel Palette": {"playful", "casual"},
    "Neon Cyberpunk": {"energetic", "experimental"},
    "High Contrast Dramatic": {"serious", "luxury"},
    "Soft Commercial Look": {"corporate", "calm"},
    "Desaturated Moody": {"serious", "calm"},
    "Vibrant Pop Colors": {"energetic", "playful"},
    "Film Noir": {"serious", "luxury"},
    # Music Style
    "Indie Electronic": {"energetic", "experimental"},
    "Orchestral Cinematic": {"luxury", "serious"},
    "Hip Hop Trap": {"energetic", "casual"},
    "Lo-fi Chill": {"calm", "casual"},
    "Corporate Uplifting": {"corporate", "serious"},
    "Ambient Soundscape": {"calm"},
    "Rock Energetic": {"energetic"},
    "Jazz Smooth": {"luxury", "calm"},
    # Typography
    "Modern Geometric Sans": {"corporate", "serious"},
    "Elegant Luxury Serif": {"luxury", "serious"},
    "Bold Condensed": {"energetic", "playful"},
    "Handwritten Style": {"casual", "playful"},
    "Retro Display": {"playful", "casual"},
    "Minimalist Thin": {"luxury", "calm"},
    "Grunge Textured": {"energetic", "experimental"},
    "Futuristic Tech": {"experimental", "serious"},
}

# Pairs of vibes that pull a project in genuinely opposite directions.
CONFLICTING_VIBE_PAIRS = [
    ("luxury", "casual"),
    ("energetic", "calm"),
    ("corporate", "experimental"),
    ("serious", "playful"),
]

CATEGORY_LABELS_FOR_CONFLICTS = {
    "editing_style": "Editing Style",
    "music_style": "Music",
    "color_grading": "Color Grading",
    "typography": "Font",
    "motion_graphics": "Motion Graphics",
}

def find_style_conflicts(selections: Dict[str, List[str]]) -> List[Dict[str, str]]:
    """selections: {category: [titles]} \u2014 a category can now have more than one style picked.
    Returns a list of human-readable conflict warnings between any two currently-selected
    styles (from DIFFERENT categories) whose vibes contradict each other. Two styles picked
    within the same category aren't compared against each other \u2014 that's just exploring
    options within one category, not a stylistic contradiction."""
    items = []
    for cat, titles in selections.items():
        for title in (titles or []):
            if title:
                items.append((cat, title))
    conflicts = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            cat_a, title_a = items[i]
            cat_b, title_b = items[j]
            if cat_a == cat_b:
                continue
            vibes_a = VIBE_TAGS.get(title_a, set())
            vibes_b = VIBE_TAGS.get(title_b, set())
            for vibe_x, vibe_y in CONFLICTING_VIBE_PAIRS:
                if (vibe_x in vibes_a and vibe_y in vibes_b) or (vibe_y in vibes_a and vibe_x in vibes_b):
                    conflicts.append({
                        "category_a": CATEGORY_LABELS_FOR_CONFLICTS.get(cat_a, cat_a),
                        "style_a": title_a,
                        "category_b": CATEGORY_LABELS_FOR_CONFLICTS.get(cat_b, cat_b),
                        "style_b": title_b,
                        "message": f"\"{title_a}\" feels {vibe_x if vibe_x in vibes_a else vibe_y}, while \"{title_b}\" feels {vibe_y if vibe_x in vibes_a else vibe_x} \u2014 these can feel inconsistent together.",
                    })
    return conflicts

@api_router.get("/video-types")
async def get_video_types():
    raw = await asyncio.to_thread(get_all_video_types_from_db)
    result = []
    for type_id, data in raw.items():
        result.append({
            "id": type_id,
            "title": data.get("title"),
            "description": data.get("description"),
            "image": data.get("image"),
            "video": data.get("video"),
            "sub_options": data.get("sub_options", []),
        })
    return result

class ConflictCheckRequest(BaseModel):
    selections: Dict[str, List[str]]

@api_router.get("/suggestions/{video_type}")
async def get_suggestions(video_type: str):
    """Returns a recommended starting pick per category for the given video type."""
    return VIDEO_TYPE_RECOMMENDATIONS.get(video_type, {})

@api_router.post("/check-conflicts")
async def check_conflicts(input: ConflictCheckRequest):
    """Given the current selections {category: [titles]}, flags any cross-category pairs whose vibes contradict."""
    conflicts = find_style_conflicts(input.selections)
    return {"conflicts": conflicts}

# Bucket in Neon Storage where voice notes and uploaded reference files live.
# It must exist and be public (create it once in the Neon dashboard, or the code
# will attempt to create it on first use below).
UPLOAD_BUCKET = os.environ.get('SUPABASE_UPLOAD_BUCKET', 'uploads')

def _ensure_bucket():
    """Makes sure the public upload bucket exists. Safe to call repeatedly."""
    try:
        supabase.storage.get_bucket(UPLOAD_BUCKET)
    except Exception:
        try:
            supabase.storage.create_bucket(UPLOAD_BUCKET, options={"public": True})
        except Exception as e:
            logger.warning("Could not create bucket %s: %s", UPLOAD_BUCKET, e)

def _upload_bytes_to_storage(data: bytes, filename: str, content_type: str) -> str:
    """Uploads raw bytes to Neon Storage and returns a permanent public URL.
    This replaces the old approach of storing browser blob: URLs, which only worked
    inside the tab that created them and were dead by the time the brief loaded."""
    _ensure_bucket()
    ext = os.path.splitext(filename)[1] or ''
    object_path = f"{uuid.uuid4().hex}{ext}"
    supabase.storage.from_(UPLOAD_BUCKET).upload(
        object_path,
        data,
        {"content-type": content_type or "application/octet-stream"},
    )
    return supabase.storage.from_(UPLOAD_BUCKET).get_public_url(object_path)

@api_router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Accepts a voice note or reference file, stores it permanently in Neon Storage,
    and returns a real public URL the brief page (and PDF exports) can actually load."""
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")
    try:
        public_url = await asyncio.to_thread(
            _upload_bytes_to_storage, contents, file.filename or "upload", file.content_type
        )
    except Exception as e:
        logger.error("Upload failed: %s", e)
        raise HTTPException(status_code=500, detail="Upload failed")
    return {"url": public_url, "name": file.filename}

@api_router.post("/projects", response_model=Project)
async def create_project(input: ProjectCreate):
    project_dict = input.model_dump()
    project = Project(**project_dict)
    doc = project.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['brand_tones'] = project.brand_tones.model_dump()
    doc.pop('id', None)
    await asyncio.to_thread(project_create, project.id, doc)
    return project

@api_router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    project = await asyncio.to_thread(project_get, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if isinstance(project['created_at'], str):
        project['created_at'] = datetime.fromisoformat(project['created_at'])
    return project

@api_router.patch("/projects/{project_id}/video-type")
async def update_video_type(project_id: str, video_type: dict):
    existing = await asyncio.to_thread(project_get, project_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found")
    update_payload = {"video_type": video_type.get("video_type")}
    if "video_sub_option" in video_type:
        update_payload["video_sub_option"] = video_type.get("video_sub_option")
    await asyncio.to_thread(project_update, project_id, update_payload)
    return {"message": "Video type updated successfully"}

@api_router.patch("/projects/{project_id}/notes")
async def update_additional_notes(project_id: str, payload: dict):
    existing = await asyncio.to_thread(project_get, project_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found")
    await asyncio.to_thread(
        project_update, project_id,
        {"additional_notes": payload.get("additional_notes", "")}
    )
    return {"message": "Notes saved successfully"}

@api_router.get("/cards", response_model=List[SwipeCard])
async def get_cards():
    all_cards = await asyncio.to_thread(get_all_cards_from_db)
    cards = []

    # Build cards in category order
    for category in CATEGORY_ORDER:
        items = all_cards.get(category, [])
        # Shuffle items within each category
        shuffled_items = items.copy()
        random.shuffle(shuffled_items)

        for item in shuffled_items:
            # Use explicit image_url from seed data if set, otherwise a DETERMINISTIC pick
            # from the pool based on the title (not random) so each card's image stays
            # consistent across reloads instead of reshuffling every time.
            fixed_image = item.get("image_url") or IMAGE_POOL[sum(ord(c) for c in item["title"]) % len(IMAGE_POOL)]
            card_data = {
                "category": category,
                "title": item["title"],
                "description": item["description"],
                "image_url": fixed_image,
                "metadata": item.get("metadata", {}) or {}
            }

            # Add audio URL for music cards
            if item.get("audio_url"):
                card_data["metadata"]["audio_url"] = item["audio_url"]

            # Add font info for typography cards
            if item.get("font_name"):
                card_data["metadata"]["font_name"] = item["font_name"]
                card_data["metadata"]["sample_text"] = item.get("sample_text", "Sample Text")

            # Add color info for color grading cards
            if item.get("color_palette"):
                card_data["metadata"]["color_palette"] = item["color_palette"]
            if item.get("color_overlay"):
                card_data["metadata"]["color_overlay"] = item["color_overlay"]
            if item.get("color_filter"):
                card_data["metadata"]["color_filter"] = item["color_filter"]

            # Add hover-preview video for editing style cards
            if item.get("video_url"):
                card_data["metadata"]["video_url"] = item["video_url"]

            # Add hover-preview YouTube embed (for cards using a YouTube reference instead of a direct video file)
            if item.get("youtube_id"):
                card_data["metadata"]["youtube_id"] = item["youtube_id"]

            card = SwipeCard(**card_data)
            cards.append(card)

    return cards

@api_router.post("/swipes", response_model=SwipeResult)
async def save_swipe(input: SwipeAction):
    result = SwipeResult(**input.model_dump())
    await asyncio.to_thread(swipe_create, result.id, result.project_id, result.card_id, result.action)
    return result

@api_router.get("/brief/{project_id}", response_model=BriefSummary)
async def get_brief(project_id: str):
    project = await asyncio.to_thread(project_get, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # These two calls are independent (different tables, no shared data) so we
    # run them concurrently instead of one-after-the-other — this alone cuts
    # the brief endpoint's own latency by roughly a third on top of project_get.
    swipes, all_cards = await asyncio.gather(
        asyncio.to_thread(swipes_get_for_project, project_id),
        asyncio.to_thread(get_all_cards_from_db),
    )

    liked_swipes = [s for s in swipes if s['action'] in ['like', 'love']]
    
    def analyze_category(category_name: str):
        category_swipes = [s for s in liked_swipes if s['card_id'].startswith(category_name)]
        if not category_swipes:
            return {"preference": "Not enough data", "count": 0, "selections": []}
        
        category_cards = all_cards.get(category_name, [])
        liked_titles = []
        selected_card = None
        matched_cards = []
        for swipe in category_swipes:
            for card in category_cards:
                card_id = f"{category_name}_{card['_slug']}"
                if swipe['card_id'] == card_id:
                    liked_titles.append(card['title'])
                    matched_cards.append({
                        "title": card.get("title"),
                        "description": card.get("description"),
                        "metadata": card.get("metadata", {}) or {},
                    })
                    if selected_card is None:
                        selected_card = card
        
        return {
            "preference": ", ".join(liked_titles[:3]) if liked_titles else "Mixed preferences",
            "count": len(category_swipes),
            "percentage": round((len(category_swipes) / len(liked_swipes) * 100), 1) if liked_swipes else 0,
            "image_url": selected_card.get("image_url") if selected_card else None,
            "video_url": selected_card.get("video_url") if selected_card else None,
            "gallery": selected_card.get("gallery") if selected_card else None,
            "selections": matched_cards,
        }
    
    editing = analyze_category("editing_style")
    color = analyze_category("color_grading")
    music = analyze_category("music_style")
    typography = analyze_category("typography")
    motion = analyze_category("motion_graphics")
    
    # Generate AI summary
    def generate_summary():
        narrative_score = project.get('narrative_technical', 0)
        fun_score = project['brand_tones']['fun_serious']
        luxury_score = project['brand_tones']['luxury_casual']
        playful_score = project['brand_tones']['corporate_playful']
        
        # Determine dominant style (0 = center/neutral, negative = left pole, positive = right pole)
        style_desc = "narrative-driven" if narrative_score < 0 else "specification-focused"
        tone_desc = "fun and energetic" if fun_score < 0 else "serious and professional"
        brand_desc = "luxury" if luxury_score < 0 else "casual"
        approach_desc = "playful" if playful_score > 0 else "corporate"
        
        # Get top preferences
        edit_pref = editing['preference'].split(',')[0] if editing['count'] > 0 else "dynamic editing"
        color_pref = color['preference'].split(',')[0] if color['count'] > 0 else "vibrant colors"
        music_pref = music['preference'].split(',')[0] if music['count'] > 0 else "engaging music"
        
        summary = f"This {project.get('video_length', '30s')} video for {project.get('platform', 'social media')} should be {style_desc} with a {tone_desc} tone, targeting {project.get('target_audience', 'the target audience')}. "
        summary += f"The visual approach leans toward {brand_desc} aesthetics with a {approach_desc} communication style. "
        summary += f"The editing style should embrace {edit_pref.lower()}, complemented by {color_pref.lower()}. "
        summary += f"Audio direction favors {music_pref.lower()}, creating an engaging soundscape. "
        
        if motion['count'] > 0:
            motion_pref = motion['preference'].split(',')[0]
            summary += f"Motion graphics should incorporate {motion_pref.lower()} to enhance visual storytelling. "
        
        summary += f"The {project.get('aspect_ratio', '16:9')} format is optimized for {project.get('business_model', 'B2C')} audiences, aiming to {project.get('purpose', 'achieve the project goals')}."
        
        return summary
    
    ai_summary = generate_summary()
    
    # Prepare project details
    project_details = {
        "video_length": project.get('video_length'),
        "platform": project.get('platform'),
        "aspect_ratio": project.get('aspect_ratio'),
        "target_audience": project.get('target_audience'),
        "purpose": project.get('purpose'),
        "business_model": project.get('business_model'),
        "video_type": project.get('video_type'),
        "narrative_technical": project.get('narrative_technical', 0),
        "brand_tones": project.get('brand_tones', {}),
        "references": project.get('references', []),
        "voice_note_url": project.get('voice_note_url'),
        "additional_notes": project.get('additional_notes')
    }
    
    brief = BriefSummary(
        project_id=project_id,
        project_name=project['project_name'],
        project_details=project_details,
        editing_style=editing,
        color_direction=color,
        music_direction=music,
        typography_direction=typography,
        motion_graphics=motion,
        total_swipes=len(swipes),
        ai_summary=ai_summary
    )
    
    return brief

@api_router.get("/brief/{project_id}/pdf")
async def export_pdf(project_id: str):
    project = await asyncio.to_thread(project_get, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    brief_data = await get_brief(project_id)
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.6*inch, bottomMargin=0.6*inch)
    story = []
    
    styles = getSampleStyleSheet()
    ACCENT = HexColor('#2088A0')
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=22, textColor=ACCENT, spaceAfter=6, alignment=TA_CENTER)
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontSize=10, textColor=HexColor('#666666'), spaceAfter=24, alignment=TA_CENTER)
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=15, textColor=ACCENT, spaceBefore=18, spaceAfter=8)
    subheading_style = ParagraphStyle('CustomSubheading', parent=styles['Heading3'], fontSize=11, textColor=HexColor('#222222'), spaceBefore=10, spaceAfter=4)
    body_style = ParagraphStyle('CustomBody', parent=styles['Normal'], fontSize=10, leading=15, textColor=HexColor('#333333'))
    meta_style = ParagraphStyle('CustomMeta', parent=styles['Normal'], fontSize=8.5, textColor=HexColor('#888888'), spaceAfter=8)

    total_selections = sum((brief_data.editing_style.get('count', 0), brief_data.color_direction.get('count', 0),
                             brief_data.music_direction.get('count', 0), brief_data.typography_direction.get('count', 0),
                             brief_data.motion_graphics.get('count', 0)))
    category_count = sum(1 for c in [brief_data.editing_style, brief_data.color_direction, brief_data.music_direction,
                                       brief_data.typography_direction, brief_data.motion_graphics] if c.get('count', 0) > 0)

    story.append(Paragraph("BRIEFLY", title_style))
    story.append(Paragraph(f"Creative Brief &middot; {project.get('project_name', 'Untitled')}", subtitle_style))
    story.append(Paragraph(f"Based on {total_selections} style selections across {category_count} categories", meta_style))

    # 1. Video Overview
    story.append(Paragraph("1. Video Overview", heading_style))
    story.append(Paragraph(brief_data.ai_summary, body_style))

    # 2. Project Details
    story.append(Paragraph("2. Project Details", heading_style))
    details_rows = [
        ["Video Type:", (project.get('video_type') or '-').replace('_', ' ').title()],
        ["Platform:", project.get('platform') or '-'],
        ["Video Length:", project.get('video_length') or '-'],
        ["Aspect Ratio:", project.get('aspect_ratio') or '-'],
        ["Business Model:", project.get('business_model') or '-'],
        ["Target Audience:", project.get('target_audience') or '-'],
        ["Purpose:", project.get('purpose') or '-'],
    ]
    details_table = Table(details_rows, colWidths=[1.6*inch, 4.4*inch])
    details_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), HexColor('#888888')),
        ('TEXTCOLOR', (1, 0), (1, -1), HexColor('#222222')),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, HexColor('#EEEEEE')),
    ]))
    story.append(details_table)

    # Additional Notes and Voice Note, if the user provided either
    additional_notes = (project.get('additional_notes') or '').strip()
    voice_note_url = project.get('voice_note_url')
    if additional_notes or voice_note_url:
        story.append(Spacer(1, 0.15*inch))
        if additional_notes:
            story.append(Paragraph("Additional Notes", ParagraphStyle(
                'NotesHeading', parent=styles['Heading3'], fontSize=11, textColor=HexColor('#222222'), spaceAfter=4
            )))
            story.append(Paragraph(additional_notes, body_style))
        if voice_note_url:
            story.append(Paragraph(
                "\U0001F3A4 A voice note was recorded for this project. Play it back on the live Brief page \u2014 audio can't be embedded in a PDF.",
                meta_style
            ))

    # Reference links / files the client attached \u2014 rendered as real clickable links.
    references = project.get('references') or []
    if references:
        story.append(Spacer(1, 0.15*inch))
        story.append(Paragraph("References", ParagraphStyle(
            'RefHeading', parent=styles['Heading3'], fontSize=11, textColor=HexColor('#222222'), spaceAfter=4
        )))
        link_style = ParagraphStyle('RefLink', parent=body_style, textColor=ACCENT)
        for ref in references:
            url = (ref.get('value') or '').strip()
            if not url:
                continue
            label = ref.get('name') or url
            safe_label = label.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            # Only pasted web links become clickable. Uploaded files are stored inline as
            # data: URLs (huge), so we just list their name instead of embedding the blob.
            if url.lower().startswith(('http://', 'https://')):
                safe_url = url.replace('&', '&amp;')
                story.append(Paragraph(f'&bull; <link href="{safe_url}"><u>{safe_label}</u></link>', link_style))
            else:
                story.append(Paragraph(f'&bull; {safe_label} (attached file)', body_style))

    # 3. Style Preferences (real bipolar tone data, not fake "Balanced 50%")
    story.append(Paragraph("3. Style Preferences", heading_style))
    tone_axes = [
        ("Narrative vs Technical", project.get('narrative_technical', 0), "Narrative", "Technical"),
        ("Fun vs Serious", (project.get('brand_tones') or {}).get('fun_serious', 0), "Fun", "Serious"),
        ("Luxury vs Casual", (project.get('brand_tones') or {}).get('luxury_casual', 0), "Luxury", "Casual"),
        ("Corporate vs Playful", (project.get('brand_tones') or {}).get('corporate_playful', 0), "Corporate", "Playful"),
    ]
    tone_rows = [["Tone Axis", "Value", "Leaning"]]
    for axis_name, value, left_label, right_label in tone_axes:
        if value == 0:
            leaning = "Balanced"
        elif value < 0:
            leaning = left_label
        else:
            leaning = right_label
        tone_rows.append([axis_name, f"{abs(value)}%", leaning])
    tone_table = Table(tone_rows, colWidths=[2.4*inch, 1.2*inch, 2.4*inch])
    tone_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT),
        ('TEXTCOLOR', (0, 1), (-1, -1), HexColor('#333333')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('LINEBELOW', (0, 1), (-1, -2), 0.5, HexColor('#EEEEEE')),
        ('GRID', (0, 0), (-1, 0), 0.5, ACCENT),
    ]))
    story.append(tone_table)

    # 4. Detailed Style Selections
    story.append(Paragraph("4. Detailed Style Selections", heading_style))
    category_defs = [
        ("Editing Style", brief_data.editing_style),
        ("Music Style", brief_data.music_direction),
        ("Color Grading", brief_data.color_direction),
        ("Typography", brief_data.typography_direction),
        ("Motion Graphics", brief_data.motion_graphics),
    ]
    for cat_label, cat_data in category_defs:
        count = cat_data.get('count', 0)
        story.append(Paragraph(f"{cat_label} &mdash; {count} selection{'s' if count != 1 else ''}", subheading_style))
        selections = cat_data.get('selections', [])
        if not selections:
            story.append(Paragraph("No selection made.", body_style))
        for sel in selections:
            meta = sel.get('metadata', {}) or {}
            meta_str = " | ".join(f"{k.replace('_', ' ').title()}: {v}" for k, v in meta.items())
            story.append(Paragraph(f"&bull; <b>{sel.get('title', '')}</b>", body_style))
            if sel.get('description'):
                story.append(Paragraph(sel['description'], meta_style))
            if meta_str:
                story.append(Paragraph(meta_str, meta_style))

    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(f"Generated by Briefly | {datetime.now(timezone.utc).strftime('%B %d, %Y')}", meta_style))
    
    doc.build(story)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=brief_{project_id}.pdf"}
    )

def _download_image_for_pdf(url, timeout=4, cache=None):
    """Downloads an image for embedding in a canvas-based PDF. Returns None on any failure.
    When a `cache` dict is passed (see _prefetch_images_for_pdf below), a pre-fetched
    result is returned instantly instead of making a fresh request."""
    if cache is not None and url in cache:
        return cache[url]
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return ImageReader(io.BytesIO(resp.content))
    except Exception:
        return None

def _prefetch_images_for_pdf(urls, timeout=4, max_workers=8):
    """Downloads several images concurrently instead of one-by-one, which is what made
    Visual Deck generation slow (5 categories x up to 5 gallery images each, all fetched
    sequentially over the network). Returns {url: ImageReader-or-None}."""
    unique_urls = list(dict.fromkeys(u for u in urls if u))
    if not unique_urls:
        return {}
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_download_image_for_pdf, url, timeout): url for url in unique_urls}
        for future in futures:
            url = futures[future]
            try:
                results[url] = future.result()
            except Exception:
                results[url] = None
    return results

def _draw_dark_background(c, width, height):
    c.setFillColor(HexColor('#0A0A0A'))
    c.rect(0, 0, width, height, fill=1, stroke=0)

def _draw_wrapped_text(c, text, x, y, max_width, font_name, font_size, color, leading=16):
    """Basic word-wrapped text drawing for reportlab canvas. Returns the y position after the text block."""
    c.setFont(font_name, font_size)
    c.setFillColor(color)
    words = (text or "").split()
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        if c.stringWidth(test_line, font_name, font_size) <= max_width:
            line = test_line
        else:
            c.drawString(x, y, line)
            y -= leading
            line = word
    if line:
        c.drawString(x, y, line)
    return y - leading

@api_router.get("/brief/{project_id}/visual-deck")
async def export_visual_deck(project_id: str):
    project = await asyncio.to_thread(project_get, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    brief_data = await get_brief(project_id)

    # Building the deck involves several blocking network calls (image downloads) and
    # CPU-bound PDF drawing. Running it in a worker thread keeps the event loop free so
    # this one request doesn't stall every other request the server is handling.
    buffer = await asyncio.to_thread(_build_visual_deck_pdf, project, brief_data)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=visual_deck_{project_id}.pdf"}
    )

def _build_visual_deck_pdf(project: dict, brief_data) -> io.BytesIO:
    width, height = letter
    margin = 60
    ACCENT = HexColor('#5EC8E0')
    WHITE = HexColor('#FAFAFA')
    GRAY = HexColor('#9A9A9A')
    CARD = HexColor('#151515')
    TRACK = HexColor('#262626')

    buffer = io.BytesIO()
    c = pdf_canvas.Canvas(buffer, pagesize=letter)

    category_defs = [
        ("EDITING", brief_data.editing_style),
        ("MUSIC", brief_data.music_direction),
        ("COLOR", brief_data.color_direction),
        ("FONT", brief_data.typography_direction),
        ("MOTION", brief_data.motion_graphics),
    ]
    total_selections = sum((c_data or {}).get('count', 0) for _, c_data in category_defs)

    # Fetch every image this deck will need up front, in parallel, instead of one request
    # at a time inline while drawing each page — this is what was making the deck slow.
    _image_urls_needed = []
    for _, c_data in category_defs:
        c_data = c_data or {}
        if c_data.get('gallery'):
            _image_urls_needed.extend(c_data['gallery'][:5])
        elif c_data.get('image_url'):
            _image_urls_needed.append(c_data['image_url'])
    _image_cache = _prefetch_images_for_pdf(_image_urls_needed)

    # --- Page 1: Cover ---
    _draw_dark_background(c, width, height)
    c.setFont('Helvetica-Bold', 44)
    c.setFillColor(ACCENT)
    c.drawCentredString(width / 2, height / 2 + 70, "BRIEFLY")
    c.setFont('Helvetica', 11)
    c.setFillColor(GRAY)
    c.drawCentredString(width / 2, height / 2 + 42, "C R E A T I V E   B R I E F")
    c.setFont('Helvetica-Bold', 20)
    c.setFillColor(WHITE)
    c.drawCentredString(width / 2, height / 2, project.get('project_name') or 'Untitled Project')
    c.setFont('Helvetica', 10)
    c.setFillColor(GRAY)
    video_type_label = (project.get('video_type') or '').replace('_', ' ').title()
    c.drawCentredString(
        width / 2, height / 2 - 22,
        " · ".join(filter(None, [video_type_label, project.get('platform'), project.get('video_length')]))
    )
    c.showPage()

    # --- Page 2: Overview ---
    _draw_dark_background(c, width, height)
    y = height - 90

    # Plain-language TL;DR so a first-time reader understands the project instantly
    tldr = f"A {project.get('video_length') or ''} {video_type_label} video for {project.get('platform') or 'your platform'}, aimed at {project.get('target_audience') or 'your audience'}."
    c.setFont('Helvetica-Bold', 16)
    c.setFillColor(ACCENT)
    y = _draw_wrapped_text(c, tldr, margin, y, width - 2 * margin, 'Helvetica-Bold', 16, ACCENT, leading=22)
    y -= 20

    c.setFont('Helvetica-Bold', 14)
    c.setFillColor(WHITE)
    c.drawString(margin, y, "The Brief")
    y -= 26
    y = _draw_wrapped_text(c, brief_data.ai_summary, margin, y, width - 2 * margin, 'Helvetica', 10.5, GRAY, leading=15)
    y -= 26

    info_pairs = [
        ("VIDEO TYPE", video_type_label or "-"),
        ("TARGET AUDIENCE", project.get('target_audience') or "-"),
        ("BUSINESS MODEL", project.get('business_model') or "-"),
        ("PURPOSE", (project.get('purpose') or "-")[:60]),
    ]
    col_width = (width - 2 * margin - 20) / 2
    for i, (label, value) in enumerate(info_pairs):
        col = i % 2
        row = i // 2
        bx = margin + col * (col_width + 20)
        by = y - row * 90
        c.setFillColor(CARD)
        c.roundRect(bx, by - 70, col_width, 70, 6, fill=1, stroke=0)
        c.setFont('Helvetica', 8)
        c.setFillColor(GRAY)
        c.drawString(bx + 14, by - 22, label)
        c.setFont('Helvetica-Bold', 12)
        c.setFillColor(WHITE)
        c.drawString(bx + 14, by - 44, value)

    additional_notes = (project.get('additional_notes') or '').strip()
    voice_note_url = project.get('voice_note_url')
    references = project.get('references') or []
    if additional_notes or voice_note_url or references:
        ny = y - ((len(info_pairs) + 1) // 2) * 90 - 30
        if additional_notes:
            c.setFont('Helvetica-Bold', 10)
            c.setFillColor(ACCENT)
            c.drawString(margin, ny, "ADDITIONAL NOTES")
            ny -= 16
            ny = _draw_wrapped_text(c, additional_notes, margin, ny, width - 2 * margin, 'Helvetica', 9.5, GRAY, leading=14)
            ny -= 8
        if references:
            c.setFont('Helvetica-Bold', 10)
            c.setFillColor(ACCENT)
            c.drawString(margin, ny, "REFERENCES")
            ny -= 16
            for ref in references:
                url = (ref.get('value') or '').strip()
                if not url:
                    continue
                is_web = url.lower().startswith(('http://', 'https://'))
                label = ref.get('name') or url
                display = label if len(label) <= 88 else label[:85] + '...'
                if not is_web:
                    display = f"{display} (attached file)"
                c.setFont('Helvetica', 9)
                c.setFillColor(WHITE)
                text_w = c.stringWidth(f"\u2022 {display}", 'Helvetica', 9)
                c.drawString(margin, ny, f"\u2022 {display}")
                # Only real web links become clickable; inline data: URLs are skipped.
                if is_web:
                    c.linkURL(url, (margin, ny - 2, margin + text_w, ny + 10), relative=0)
                ny -= 14
            ny -= 6
        if voice_note_url:
            c.setFont('Helvetica', 8)
            c.setFillColor(GRAY)
            c.drawString(margin, ny, "\U0001F3A4 A voice note was recorded for this project \u2014 play it back on the live Brief page.")
    c.showPage()

    # --- Page 3: Feeling the Vibe (real bipolar tone data) ---
    _draw_dark_background(c, width, height)
    y = height - 90
    c.setFont('Helvetica-Bold', 22)
    c.setFillColor(WHITE)
    c.drawString(margin, y, "Feeling the Vibe")
    y -= 20
    c.setFont('Helvetica', 9.5)
    c.setFillColor(GRAY)
    c.drawString(margin, y, "How this video should come across, based on your choices \u2014 the highlighted side is the stronger lean.")
    y -= 45

    tone_axes = [
        ("Narrative vs Technical", project.get('narrative_technical', 0), "Narrative", "Technical"),
        ("Fun vs Serious", (project.get('brand_tones') or {}).get('fun_serious', 0), "Fun", "Serious"),
        ("Luxury vs Casual", (project.get('brand_tones') or {}).get('luxury_casual', 0), "Luxury", "Casual"),
        ("Corporate vs Playful", (project.get('brand_tones') or {}).get('corporate_playful', 0), "Corporate", "Playful"),
    ]
    bar_width = width - 2 * margin
    for axis_name, value, left_label, right_label in tone_axes:
        left_active = value <= 0
        right_active = value > 0
        c.setFont('Helvetica-Bold', 12)
        c.setFillColor(ACCENT if left_active else GRAY)
        c.drawString(margin, y, left_label)
        c.setFont('Helvetica-Bold', 12)
        c.setFillColor(ACCENT if right_active else GRAY)
        c.drawRightString(margin + bar_width, y, right_label)
        y -= 16
        c.setFont('Helvetica', 8)
        c.setFillColor(GRAY)
        c.drawCentredString(margin + bar_width / 2, y, f"{axis_name} \u00b7 {abs(value)}% lean")
        y -= 18
        c.setFillColor(TRACK)
        c.roundRect(margin, y - 8, bar_width, 8, 4, fill=1, stroke=0)
        fill_ratio = (value + 100) / 200  # 0..1 across the full -100..100 range
        c.setFillColor(ACCENT)
        c.roundRect(margin, y - 8, max(bar_width * fill_ratio, 8), 8, 4, fill=1, stroke=0)
        y -= 40
    c.showPage()

    # --- Style DNA pages: 2 categories per page, each with a real image + one-line description ---
    def draw_category_half(label, item, top):
        """Draws one category in either the top or bottom half of the page.
        Each category type gets its own display: Editing/Color/Motion show a real image,
        Music shows an icon (no stock photo fits 'a genre'), Font shows the style's own
        typeface rendered as large text (matching how the live app displays font picks)."""
        item = item or {}
        name = item.get('preference') or 'Not enough data'
        selections = item.get('selections') or []
        first_selection = selections[0] if selections else {}
        image_url = item.get('image_url')

        half_height = (height - 2 * margin) / 2
        top_y = height - margin if top else height - margin - half_height
        content_height = half_height - 60

        if item.get('gallery'):
            # Moodboard collage takes priority for ANY category, including Music \u2014
            # a mood-representative gallery beats both the icon-only default and a single photo.
            gallery_urls = item['gallery'][:5]
            hero_url, support_urls = gallery_urls[0], gallery_urls[1:]
            gap = 4
            hero_width = (width - 2 * margin) * 0.58
            support_col_width = (width - 2 * margin) - hero_width - gap

            hero_img = _download_image_for_pdf(hero_url, cache=_image_cache)
            if hero_img:
                c.drawImage(hero_img, margin, top_y - content_height, width=hero_width, height=content_height,
                             preserveAspectRatio=True, anchor='c', mask='auto')
            else:
                c.setFillColor(CARD)
                c.rect(margin, top_y - content_height, hero_width, content_height, fill=1, stroke=0)

            if support_urls:
                cell_height = (content_height - gap * (len(support_urls) - 1)) / len(support_urls)
                sx = margin + hero_width + gap
                sy = top_y
                for url in support_urls:
                    img = _download_image_for_pdf(url, cache=_image_cache)
                    if img:
                        c.drawImage(img, sx, sy - cell_height, width=support_col_width, height=cell_height,
                                     preserveAspectRatio=True, anchor='c', mask='auto')
                    else:
                        c.setFillColor(CARD)
                        c.rect(sx, sy - cell_height, support_col_width, cell_height, fill=1, stroke=0)
                    sy -= (cell_height + gap)
            text_y = top_y - content_height - 26

        elif label == 'MUSIC':
            # Icon + name only \u2014 no generic stock photo pretending to represent a genre
            c.setFillColor(CARD)
            c.roundRect(margin, top_y - content_height, width - 2 * margin, content_height, 10, fill=1, stroke=0)
            icon_cx = width / 2
            icon_cy = top_y - content_height / 2
            c.setFillColor(HexColor('#0A0A0A'))
            c.circle(icon_cx, icon_cy, 40, fill=1, stroke=0)
            c.setStrokeColor(ACCENT)
            c.setLineWidth(2)
            c.circle(icon_cx, icon_cy, 40, fill=0, stroke=1)
            # simple speaker glyph
            c.setFillColor(ACCENT)
            c.rect(icon_cx - 14, icon_cy - 8, 8, 16, fill=1, stroke=0)
            p = c.beginPath()
            p.moveTo(icon_cx - 6, icon_cy - 8)
            p.lineTo(icon_cx + 6, icon_cy - 16)
            p.lineTo(icon_cx + 6, icon_cy + 16)
            p.lineTo(icon_cx - 6, icon_cy + 8)
            p.close()
            c.drawPath(p, fill=1, stroke=0)
            text_y = top_y - content_height - 26

        elif label == 'FONT':
            # Show the style's own typeface as large styled text \u2014 the same idea as the
            # live app's font card, not a stock photo standing in for typography.
            c.setFillColor(CARD)
            c.roundRect(margin, top_y - content_height, width - 2 * margin, content_height, 10, fill=1, stroke=0)
            sample_text = (first_selection.get('metadata') or {}).get('sample_text') or name
            c.setFont('Helvetica-Bold', 34)
            c.setFillColor(WHITE)
            c.drawCentredString(width / 2, top_y - content_height / 2 - 12, sample_text[:20])
            text_y = top_y - content_height - 26

        else:
            # EDITING, COLOR, MOTION \u2014 a real representative image
            img = _download_image_for_pdf(image_url, cache=_image_cache) if image_url else None
            if img:
                c.drawImage(img, margin, top_y - content_height, width=width - 2 * margin, height=content_height,
                             preserveAspectRatio=True, anchor='c', mask='auto')
            else:
                c.setFillColor(CARD)
                c.rect(margin, top_y - content_height, width - 2 * margin, content_height, fill=1, stroke=0)
            text_y = top_y - content_height - 26

        c.setFont('Helvetica-Bold', 8)
        c.setFillColor(ACCENT)
        c.drawString(margin, text_y, label)
        c.setFont('Helvetica-Bold', 15)
        c.setFillColor(WHITE)
        c.drawString(margin, text_y - 20, name)

    style_pairs = [category_defs[i:i + 2] for i in range(0, len(category_defs), 2)]
    for page_num, pair in enumerate(style_pairs):
        _draw_dark_background(c, width, height)
        if len(pair) == 2:
            (label_a, item_a), (label_b, item_b) = pair
            draw_category_half(label_a, item_a, top=True)
            c.setStrokeColor(HexColor('#222222'))
            c.line(margin, height / 2, width - margin, height / 2)
            draw_category_half(label_b, item_b, top=False)
        else:
            (label_a, item_a), = pair
            draw_category_half(label_a, item_a, top=True)
        c.setFont('Helvetica', 7.5)
        c.setFillColor(GRAY)
        c.drawRightString(width - margin, margin - 20, f"Style DNA \u00b7 {page_num + 1}/{len(style_pairs)}")
        c.showPage()

    # --- Closing ---
    _draw_dark_background(c, width, height)
    c.setFont('Helvetica-Bold', 18)
    c.setFillColor(WHITE)
    c.drawCentredString(width / 2, height / 2 + 10, "BRIEFLY")
    c.setFont('Helvetica', 10)
    c.setFillColor(GRAY)
    c.drawCentredString(width / 2, height / 2 - 12, "Creative Brief System")
    c.drawCentredString(width / 2, height / 2 - 30, f"Generated {datetime.now(timezone.utc).strftime('%B %d, %Y')}")
    c.showPage()

    c.save()
    buffer.seek(0)
    return buffer

@app.on_event("startup")
async def on_startup():
    await asyncio.to_thread(resync_category_cards, "editing_style")
    await asyncio.to_thread(resync_category_cards, "music_style")
    await asyncio.to_thread(resync_category_cards, "color_grading")
    await asyncio.to_thread(resync_category_cards, "typography")
    await asyncio.to_thread(resync_category_cards, "motion_graphics")
    await asyncio.to_thread(resync_video_types)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)