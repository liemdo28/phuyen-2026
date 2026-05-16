"""Vietnamese Human Language Intelligence Package.

This package provides comprehensive Vietnamese language understanding:
- Slang and internet language resolution
- Regional dialect normalization
- No-accent typing inference
- Typo and fuzzy matching
- Emotional language detection
- Pronoun/address detection
- Contextual short phrase resolution
- Social energy analysis
"""
from app.vietnamese.normalizer import VietnameseNormalizer
from app.vietnamese.pronouns import PronounResolver
from app.vietnamese.slang import SlangResolver
from app.vietnamese.emotional import EmotionalAnalyzer
from app.vietnamese.contextual import ContextualResolver
from app.vietnamese.social_energy import SocialEnergyDetector
from app.vietnamese.money_parser import MoneyParser

__all__ = [
    "VietnameseNormalizer",
    "PronounResolver", 
    "SlangResolver",
    "EmotionalAnalyzer",
    "ContextualResolver",
    "SocialEnergyDetector",
    "MoneyParser",
]