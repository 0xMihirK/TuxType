"""Configuration management"""
import os
import toml
import logging
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class TestSettings:
    """Test-related settings"""
    default_mode: str = "words"
    default_word_count: int = 50
    default_time: int = 60
    default_language: str = "english"
    difficulty: str = "normal"
    punctuation: bool = False
    numbers: bool = False
    quick_restart: bool = True


@dataclass
class DisplaySettings:
    """Display-related settings"""
    theme: str = "dark"
    show_live_wpm: bool = True
    show_live_accuracy: bool = True
    show_live_burst: bool = False
    caret_style: str = "block"  # block, line, underline
    colorblind_mode: bool = False


@dataclass
class BehaviorSettings:
    """Behavior-related settings"""
    quick_end: bool = False
    stop_on_error: bool = False
    confidence_mode: int = 0  # 0=off, 1=no going back, 2=limited backspace
    lazy_mode: bool = False
    sound_on_error: bool = False
    sound_on_complete: bool = False


@dataclass
class StatsSettings:
    """Statistics display settings"""
    show_consistency: bool = True
    show_graph: bool = True
    graph_style: str = "line"
    always_show_decimal: bool = False


@dataclass
class AppConfig:
    """Complete application configuration"""
    test: TestSettings = field(default_factory=TestSettings)
    display: DisplaySettings = field(default_factory=DisplaySettings)
    behavior: BehaviorSettings = field(default_factory=BehaviorSettings)
    stats: StatsSettings = field(default_factory=StatsSettings)


class Config:
    """Configuration manager"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager
        
        Args:
            config_path: Path to config file. If None, uses default location.
        """
        if config_path is None:
            base_dir = Path(__file__).parent.parent.parent
            config_path = base_dir / "data" / "tuxtype.config"
            # Migrate from old config file if it exists
            old_config = base_dir / "data" / "user_config.toml"
            if not Path(config_path).exists() and old_config.exists():
                import shutil
                shutil.copy2(old_config, config_path)
        
        self.config_path = Path(config_path)
        self.config = AppConfig()
        
        # Load configuration if exists
        if self.config_path.exists():
            self.load()
    
    def load(self) -> None:
        """Load configuration from file"""
        try:
            data = toml.load(self.config_path)
            
            # Load test settings
            if 'test' in data:
                for key, value in data['test'].items():
                    if hasattr(self.config.test, key):
                        setattr(self.config.test, key, value)
            
            # Load display settings
            if 'display' in data:
                for key, value in data['display'].items():
                    if hasattr(self.config.display, key):
                        setattr(self.config.display, key, value)
            
            # Load behavior settings
            if 'behavior' in data:
                for key, value in data['behavior'].items():
                    if hasattr(self.config.behavior, key):
                        setattr(self.config.behavior, key, value)
            
            # Load stats settings
            if 'stats' in data:
                for key, value in data['stats'].items():
                    if hasattr(self.config.stats, key):
                        setattr(self.config.stats, key, value)
                        
        except (toml.TomlDecodeError, IOError) as e:
            logger.error(f"Error loading config: {e}")
            # Keep defaults
    
    def save(self) -> None:
        """Save configuration to file"""
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'test': asdict(self.config.test),
                'display': asdict(self.config.display),
                'behavior': asdict(self.config.behavior),
                'stats': asdict(self.config.stats)
            }
            
            with open(self.config_path, 'w') as f:
                toml.dump(data, f)
        except (IOError, OSError) as e:
            logger.error(f"Failed to save config: {e}")
    
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value
        
        Args:
            section: Config section (test, display, behavior, stats)
            key: Key within section
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        section_obj = getattr(self.config, section, None)
        if section_obj:
            return getattr(section_obj, key, default)
        return default
    
    def set(self, section: str, key: str, value: Any) -> None:
        """Set a configuration value
        
        Args:
            section: Config section
            key: Key within section
            value: Value to set
        """
        section_obj = getattr(self.config, section, None)
        if section_obj and hasattr(section_obj, key):
            setattr(section_obj, key, value)
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults"""
        self.config = AppConfig()
    
    @property
    def test(self) -> TestSettings:
        """Get test settings"""
        return self.config.test
    
    @property
    def display(self) -> DisplaySettings:
        """Get display settings"""
        return self.config.display
    
    @property
    def behavior(self) -> BehaviorSettings:
        """Get behavior settings"""
        return self.config.behavior
    
    @property
    def stats(self) -> StatsSettings:
        """Get stats settings"""
        return self.config.stats


# Color schemes for themes
THEMES = {
    'dark': {
        'background': '#1e1e2e',
        'foreground': '#cdd6f4',
        'correct': '#a6e3a1',
        'incorrect': '#f38ba8',
        'extra': '#fab387',
        'pending': '#6c7086',
        'current': '#f5e0dc',
        'cursor': '#f5c2e7',
        'accent': '#89b4fa',
        'warning': '#f9e2af',
        'border': '#45475a',
        'header': '#cba6f7',
    },
    'light': {
        'background': '#eff1f5',
        'foreground': '#4c4f69',
        'correct': '#40a02b',
        'incorrect': '#d20f39',
        'extra': '#fe640b',
        'pending': '#9ca0b0',
        'current': '#dc8a78',
        'cursor': '#ea76cb',
        'accent': '#1e66f5',
        'warning': '#df8e1d',
        'border': '#bcc0cc',
        'header': '#8839ef',
    },
    'monokai': {
        'background': '#272822',
        'foreground': '#f8f8f2',
        'correct': '#a6e22e',
        'incorrect': '#f92672',
        'extra': '#fd971f',
        'pending': '#75715e',
        'current': '#f8f8f2',
        'cursor': '#ae81ff',
        'accent': '#66d9ef',
        'warning': '#e6db74',
        'border': '#49483e',
        'header': '#ae81ff',
    },
    'dracula': {
        'background': '#282a36',
        'foreground': '#f8f8f2',
        'correct': '#50fa7b',
        'incorrect': '#ff5555',
        'extra': '#ffb86c',
        'pending': '#6272a4',
        'current': '#f8f8f2',
        'cursor': '#bd93f9',
        'accent': '#8be9fd',
        'warning': '#f1fa8c',
        'border': '#44475a',
        'header': '#bd93f9',
    },
}


def get_theme(name: str = 'dark') -> dict:
    """Get theme colors by name"""
    return THEMES.get(name, THEMES['dark'])
