"""
CLI Package - Command-line interface for Trading AI System

Exports:
- Interactive menu system
- CLI commands
"""

from cli.menu_system import InteractiveMenu
from cli.commands import (
    BacktestCommand,
    TrainCommand,
    LiveCommand,
    DataCommand,
    ConfigCommand,
    AnalysisCommand,
)

__all__ = [
    'InteractiveMenu',
    'BacktestCommand',
    'TrainCommand',
    'LiveCommand',
    'DataCommand',
    'ConfigCommand',
    'AnalysisCommand',
]
