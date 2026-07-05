"""
CLI Package - Command-line interface for Trading AI System

v79.1 Exports:
- Interactive menu system
- CLI commands
- Command routing
"""

from .menu_system import InteractiveMenu, MenuOption
from .commands import (
    BaseCommand,
    BacktestCommand,
    TrainCommand,
    LiveCommand,
    DataCommand,
    ConfigCommand,
    AnalysisCommand,
)

__all__ = [
    # Menu
    "InteractiveMenu",
    "MenuOption",
    
    # Base
    "BaseCommand",
    
    # Commands
    "BacktestCommand",
    "TrainCommand",
    "LiveCommand",
    "DataCommand",
    "ConfigCommand",
    "AnalysisCommand",
]

__version__ = "0.79.1"
