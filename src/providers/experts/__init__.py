"""Expert prediction providers for Stryktips Bot.

Providers for scraping and parsing expert predictions from various Swedish sources:

Swedish Sources:
- Rekatochklart - Popular betting blog
- Aftonbladet/Sportbladet - Major sports media
- Erik Niva - Renowned football analyst (Sportbladet)
- Olof Lundh - Famous commentator (Fotbollskanalen/TV4)
- Sportbladet - Dedicated Stryktips coverage
- Fotbollskanalen - Leading football media
- Stryktipspodden - Popular Stryktips podcast
- Expressen Tips & Odds - Major sports media
- Tipsmedoss - Betting blog
- Spelbloggare - Betting blog platform
"""

from src.providers.experts.base import BaseExpertProvider, ExpertPrediction
from src.providers.experts.cache import ProviderCache
from src.providers.experts.rekatochklart import RekatochklartProvider
from src.providers.experts.aftonbladet import AftonbladetProvider
from src.providers.experts.stryktipspodden import StryktipsoddenProvider
from src.providers.experts.erik_niva import ErikNivaProvider
from src.providers.experts.olof_lundh import OlofLundhProvider
from src.providers.experts.sportbladet import SportbladetProvider
from src.providers.experts.fotbollskanalen import FotbollskalenProvider
from src.providers.experts.generic_blog import (
    GenericBlogProvider,
    ExpressenProvider,
    TipsmedossProvider,
    SpelbloggareProvider,
)

__all__ = [
    "BaseExpertProvider",
    "ExpertPrediction",
    "ProviderCache",
    # Swedish providers
    "RekatochklartProvider",
    "AftonbladetProvider",
    "ErikNivaProvider",
    "OlofLundhProvider",
    "SportbladetProvider",
    "FotbollskalenProvider",
    "StryktipsoddenProvider",
    "ExpressenProvider",
    "TipsmedossProvider",
    "SpelbloggareProvider",
    # Generic
    "GenericBlogProvider",
]
