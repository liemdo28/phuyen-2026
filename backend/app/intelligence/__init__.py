"""
Vietnamese Human Communication & Travel Intelligence Graph

A living knowledge graph that understands how Vietnamese humans ACTUALLY communicate:
- slang, no-accent typing, typos, Gen Z internet language
- emotional signals, fatigue, social energy
- travel behavior, movement resistance, crowd tolerance
- regional dialects, sarcasm, indirect requests
- food culture, nightlife, recovery language
"""
from app.intelligence.analyzer import VietnameseMessageAnalysis, analyze_message

__all__ = ["analyze_message", "VietnameseMessageAnalysis"]
