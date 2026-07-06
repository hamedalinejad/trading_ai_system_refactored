"""
CLI Module for Trading AI System (v79.2)

Provides command-line interface and interactive menu system.
Thread-safe, production-ready CLI with full module integration.

Usage:
    from trading_ai_system.cli import main, InteractiveMenu
    
    # Command-line interface
    exit_code = main()
    
    # Interactive menu
    menu = InteractiveMenu()
    menu.run()

Commands:
    backtest    - Run backtests
    train       - Train models
    live        - Live trading
    data        - Data management
    config      - Configuration
    analysis    - Analysis and metrics
    strategy    - Strategy management
    risk        - Risk management
    model       - Model management
    feature     - Feature engineering
    portfolio   - Portfolio tracking
"""

__version__ = "0.79.2"

from typing import Optional
import sys
import argparse


def main(argv: Optional[list] = None) -> int:
    """
    Entry point for command-line interface.
    
    Args:
        argv: Command-line arguments (defaults to sys.argv[1:])
    
    Returns:
        Exit code (0=success, 1=error, 2=validation error)
    
    Example:
        >>> exit_code = main(['backtest', '--pair', 'EURUSD'])
        >>> sys.exit(exit_code)
    """
    from trading_ai_system.cli.cli import create_parser, main as cli_main
    
    if argv is None:
        argv = sys.argv[1:]
    
    old_argv = sys.argv
    sys.argv = ['trading_ai_system'] + argv
    
    try:
        return cli_main()
    finally:
        sys.argv = old_argv


def run_interactive_menu() -> None:
    """
    Launch interactive menu system.
    
    Example:
        >>> run_interactive_menu()
    """
    from trading_ai_system.cli.menu_system import InteractiveMenu
    
    menu = InteractiveMenu()
    menu.run()


__all__ = [
    'main',
    'run_interactive_menu',
    '__version__',
]
