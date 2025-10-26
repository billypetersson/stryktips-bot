"""Expert prediction providers for Stryktips Bot.

Providers for scraping and parsing expert predictions from various Swedish sources:
- Rekatochklart
- Aftonbladet Sportbladet
- Stryktipspodden
- Expressen Tips & Odds
- Tipsmedoss
- Spelbloggare
"""

from src.providers.experts.base import BaseExpertProvider, ExpertPrediction

__all__ = [
    "BaseExpertProvider",
    "ExpertPrediction",
]
