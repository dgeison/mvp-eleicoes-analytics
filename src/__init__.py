"""
MVP Eleições Analytics 2026
Plataforma de análise de dados eleitorais com foco em candidaturas femininas
"""

__version__ = "1.0.0"
__author__ = "Equipe MVP Eleições Analytics"
__description__ = "Plataforma robusta de análise de dados eleitorais brasileiros"

# Imports principais
from .config import settings
from .utils.helpers import setup_logging, DataQualityChecker, ProgressTracker

__all__ = [
    "settings",
    "setup_logging", 
    "DataQualityChecker",
    "ProgressTracker"
]