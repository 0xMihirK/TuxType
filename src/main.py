#!/usr/bin/env python3
"""
Terminal Typing Test - Entry Point

A terminal-based typing speed test application inspired by monkeytype.com.
Built with Python, Textual, and Rich.

Usage:
    python -m src.main              # Start with GUI
    python -m src.main --help       # Show help
    python -m src.main --mode words --count 50   # Quick start with settings
"""
import sys
import click
from pathlib import Path

# Add src to path for imports
src_dir = Path(__file__).parent
if str(src_dir.parent) not in sys.path:
    sys.path.insert(0, str(src_dir.parent))


@click.command()
@click.option('--mode', '-m', type=click.Choice(['words', 'time']), default='words',
              help='Test mode: words or time')
@click.option('--count', '-c', type=click.IntRange(10, 1000), default=50,
              help='Word count for word mode (10-1000)')
@click.option('--time', '-t', 'time_limit', type=click.IntRange(15, 600), default=60,
              help='Time limit in seconds for time mode (15-600)')
@click.option('--language', '-l', type=click.Choice(['english', 'english_uk', 'programming']), 
              default='english', help='Language/word list to use')
@click.option('--difficulty', '-d', type=click.Choice(['normal', 'expert', 'master']),
              default='normal', help='Difficulty level')
@click.option('--punctuation', '-p', is_flag=True, default=False,
              help='Include punctuation in words')
@click.option('--numbers', '-n', is_flag=True, default=False,
              help='Include numbers in words')
@click.option('--debug', is_flag=True, default=False,
              help='Enable debug logging')
@click.option('--version', '-v', is_flag=True, default=False,
              help='Show version and exit')
def main(mode: str, count: int, time_limit: int, language: str,
         difficulty: str, punctuation: bool, numbers: bool, debug: bool, version: bool):
    """Terminal Typing Test - Practice your typing speed in the terminal!
    
    A monkeytype-inspired typing test that runs completely offline.
    Features multiple test modes, detailed statistics, and personal best tracking.
    
    Examples:
    
        typing-test                    # Start with defaults (50 words)
        typing-test -m time -t 60      # 60 second time trial
        typing-test -c 100 -p          # 100 words with punctuation
        typing-test -l programming     # Practice programming keywords
    """
    if version:
        from . import __version__
        click.echo(f"Terminal Typing Test v{__version__}")
        click.echo("Python + Textual + Rich")
        click.echo("https://github.com/0xMihirK/TuxType")
        return
    
    # Setup logging
    from .utils.logging_config import setup_logging
    log_level = "DEBUG" if debug else "INFO"
    log_file = Path(__file__).parent.parent / "data" / "tuxtype.log" if debug else None
    setup_logging(log_level=log_level, log_file=log_file)
    
    # Import app here to avoid slow startup for --help
    from .app import TypingTestApp
    
    # Create app instance
    app = TypingTestApp()
    
    # Apply CLI settings
    app.test_mode = mode
    app.test_word_count = count
    app.test_time = time_limit
    app.test_language = language
    app.test_difficulty = difficulty
    app.test_punctuation = punctuation
    app.test_numbers = numbers
    
    # Run the app
    app.run()


if __name__ == "__main__":
    main()
