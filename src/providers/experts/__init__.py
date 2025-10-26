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
from src.providers.experts.rekatochklart import RekatochklartProvider
from src.providers.experts.aftonbladet import AftonbladetProvider
from src.providers.experts.stryktipspodden import StryktipsoddenProvider
from src.providers.experts.generic_blog import (
    GenericBlogProvider,
    ExpressenProvider,
    TipsmedossProvider,
    SpelbloggareProvider,
)

__all__ = [
    "BaseExpertProvider",
    "ExpertPrediction",
    "RekatochklartProvider",
    "AftonbladetProvider",
    "StryktipsoddenProvider",
    "GenericBlogProvider",
    "ExpressenProvider",
    "TipsmedossProvider",
    "SpelbloggareProvider",
]
