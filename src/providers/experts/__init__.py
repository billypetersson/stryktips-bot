"""Expert prediction providers for Stryktips Bot.

Providers for scraping and parsing expert predictions from various sources:

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

International Sources:
- The Guardian - Football Weekly podcast & articles
- The Athletic - Premium sports media
- Opta Analyst - Data-driven predictions
- The Totally Football Show - James Richardson's podcast
- Tifo Football - Tactical analysis
- Sky Sports - Neville & Carragher MNF analysis
- BBC Match of the Day - Premier League analysis
- The Coaches' Voice - Professional coaches' analysis
- The Times - Premium sports journalism
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
# International providers
from src.providers.experts.guardian_football import GuardianFootballProvider
from src.providers.experts.the_athletic import TheAthleticProvider
from src.providers.experts.opta_analyst import OptaAnalystProvider
from src.providers.experts.totally_football_show import TotallyFootballShowProvider
from src.providers.experts.tifo_football import TifoFootballProvider
from src.providers.experts.sky_sports import SkySportsProvider
from src.providers.experts.bbc_motd import BBCMatchOfTheDayProvider
from src.providers.experts.coaches_voice import CoachesVoiceProvider
from src.providers.experts.the_times import TheTimesProvider

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
    # International providers
    "GuardianFootballProvider",
    "TheAthleticProvider",
    "OptaAnalystProvider",
    "TotallyFootballShowProvider",
    "TifoFootballProvider",
    "SkySportsProvider",
    "BBCMatchOfTheDayProvider",
    "CoachesVoiceProvider",
    "TheTimesProvider",
]
