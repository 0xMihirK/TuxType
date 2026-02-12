"""Main Textual application for Terminal Typing Test"""
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from datetime import datetime
from typing import Optional

from .screens.main_menu import MainMenuScreen
from .screens.test_screen import TestScreen
from .screens.results_screen import ResultsScreen
from .screens.settings_screen import SettingsScreen
from .screens.history_screen import HistoryScreen
from .screens.stats_screen import StatsScreen
from .screens.splash_screen import SplashScreen
from .database.db_manager import DatabaseManager
from .database.models import TestResult
from .utils.config import Config


class TypingTestApp(App):
    """Terminal Typing Test Application"""
    
    TITLE = "TuxType"
    SUB_TITLE = "Terminal Typing Test"
    
    CSS = """
    Screen {
        background: $background;
    }
    
    /* Dracula theme overrides */
    .dracula-theme Screen {
        background: #282a36;
    }
    
    /* ── Light-theme color overrides ── */
    .light-theme Screen {
        background: #eff1f5;
    }
    .light-theme #stats-box,
    .light-theme #settings-box,
    .light-theme #results-box,
    .light-theme #history-box,
    .light-theme #menu-box,
    .light-theme #table-container {
        background: #e6e9ef;
        border: round #9ca0b0;
    }
    .light-theme Static {
        color: #4c4f69;
    }
    .light-theme .setting-label {
        color: #6c6f85;
    }
    .light-theme Header,
    .light-theme HeaderClock,
    .light-theme HeaderTitle,
    .light-theme HeaderIcon {
        background: #dce0e8;
        color: #4c4f69;
    }
    .light-theme #hint {
        border-top: solid #bcc0cc;
        color: #6c6f85;
    }
    .light-theme #title {
        border-bottom: solid #bcc0cc;
    }
    .light-theme MenuItem.selected {
        background: #bcc0cc;
        color: #4c4f69;
    }
    .light-theme DataTable > .datatable--header {
        background: #ccd0da;
        color: #4c4f69;
    }
    .light-theme DataTable > .datatable--cursor {
        background: #bcc0cc;
        color: #4c4f69;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=False, priority=True),
        Binding("ctrl+q", "quit", "Quit", show=False),
    ]
    
    # Screen registry
    SCREENS = {
        "menu": MainMenuScreen,
        "test": TestScreen,
        "results": ResultsScreen,
        "settings": SettingsScreen,
        "history": HistoryScreen,
        "stats": StatsScreen,
    }
    
    def get_theme_color(self, key: str) -> str:
        """Get color validation from current theme"""
        # Default fallback colors (Dark theme)
        defaults = {
            'background': '#1e1e2e',
            'foreground': '#cdd6f4', 
            'correct': '#a6e3a1',
            'incorrect': '#f38ba8',
            'extra': '#fab387',
            'pending': '#585b70',       # dim
            'current': '#cdd6f4',       # active word 
            'cursor': '#f5e0dc',
            'accent': '#f9e2af',
            'warning': '#fab387',
            'border': '#45475a',
            'header': '#1e1e2e'
        }
        
        # Get current theme dict
        if hasattr(self, 'config') and self.config:
            from .utils.config import THEMES
            theme_dict = THEMES.get(self.test_theme, THEMES['dark'])
            return theme_dict.get(key, defaults.get(key, '#ffffff'))
        
        return defaults.get(key, '#ffffff')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize database
        self.db = DatabaseManager()
        
        # Initialize config
        self.config = Config()
        
        # Test settings (can be modified by settings screen)
        self.test_mode = self.config.test.default_mode
        self.test_word_count = self.config.test.default_word_count
        self.test_time = self.config.test.default_time
        self.test_language = self.config.test.default_language
        self.test_difficulty = self.config.test.difficulty
        self.test_punctuation = self.config.test.punctuation
        self.test_numbers = self.config.test.numbers
        self.test_theme = self.config.display.theme
        
        # Apply theme on startup
        self._apply_theme(self.test_theme)
    
    def _remove_all_theme_classes(self) -> None:
        """Remove all custom theme CSS classes"""
        for cls in ("dracula-theme", "light-theme"):
            self.remove_class(cls)
    
    def _apply_theme(self, theme: str) -> None:
        """Apply the given theme to the app"""
        self.test_theme = theme
        self._remove_all_theme_classes()
        
        if theme == 'light':
            self.dark = False
            self.add_class("light-theme")
        elif theme == 'dracula':
            self.dark = True
            self.add_class("dracula-theme")
        else:  # dark (default)
            self.dark = True
    
    def on_mount(self) -> None:
        """Called when app starts"""
        # Re-apply theme after mount (constructor sets may be overridden)
        self._apply_theme(self.test_theme)

        # Show splash screen first
        splash = SplashScreen()
        super().push_screen(splash)
    
    def _create_menu_screen(self) -> MainMenuScreen:
        """Create main menu screen with current stats"""
        # Get stats for display
        avg_stats = self.db.get_average_stats(limit=10)
        daily = self.db.get_daily_stats()
        current_streak, _ = self.db.get_streak()
        
        return MainMenuScreen(
            current_mode=self.test_mode,
            current_value=self.test_word_count if self.test_mode == "words" else self.test_time,
            current_language=self.test_language,
            avg_wpm=avg_stats.get('avg_wpm', 0),
            avg_accuracy=avg_stats.get('avg_accuracy', 0),
            tests_today=daily.tests_completed if daily else 0,
            streak=current_streak
        )
    
    def _create_test_screen(self) -> TestScreen:
        """Create test screen with current settings"""
        mode_value = self.test_word_count if self.test_mode == "words" else self.test_time
        
        return TestScreen(
            mode=self.test_mode,
            mode_value=mode_value,
            language=self.test_language,
            difficulty=self.test_difficulty,
            punctuation=self.test_punctuation,
            numbers=self.test_numbers,
            on_complete=self._on_test_complete
        )
    
    def _create_settings_screen(self) -> SettingsScreen:
        """Create settings screen with current settings"""
        return SettingsScreen(
            mode=self.test_mode,
            word_count=self.test_word_count,
            time_value=self.test_time,
            language=self.test_language,
            difficulty=self.test_difficulty,
            punctuation=self.test_punctuation,
            numbers=self.test_numbers,
            theme=self.test_theme,
            on_save=self._on_settings_save
        )
    
    def push_screen(self, screen_name: str, *args, **kwargs) -> None:
        """Push a screen by name, creating it with current settings"""
        if screen_name == "menu":
            screen = self._create_menu_screen()
        elif screen_name == "test":
            screen = self._create_test_screen()
        elif screen_name == "settings":
            screen = self._create_settings_screen()
        elif screen_name == "results":
            results = args[0] if args else kwargs.get('results', {})
            screen = ResultsScreen(results=results)
        elif screen_name == "history":
            screen = HistoryScreen()
        elif screen_name == "stats":
            screen = StatsScreen()
        else:
            return
        
        return super().push_screen(screen)
    
    def _on_test_complete(self, results: dict) -> None:
        """Called when a test is completed"""
        # Save to database
        test_result = TestResult(
            timestamp=datetime.now(),
            mode=results.get('mode', 'words'),
            mode_value=results.get('mode_value', 50),
            language=results.get('language', 'english'),
            difficulty=results.get('difficulty', 'normal'),
            wpm=results.get('wpm', 0),
            raw_wpm=results.get('raw_wpm', 0),
            accuracy=results.get('accuracy', 0),
            consistency=results.get('consistency', 0),
            characters_correct=results.get('characters_correct', 0),
            characters_incorrect=results.get('characters_incorrect', 0),
            characters_extra=results.get('characters_extra', 0),
            characters_missed=results.get('characters_missed', 0),
            test_duration=results.get('duration', 0),
            punctuation=results.get('punctuation', False),
            numbers=results.get('numbers', False)
        )
        
        test_id = self.db.save_test_result(test_result)
        
        # Check if it was a personal best
        pb = self.db.get_personal_best(
            test_result.mode, 
            test_result.mode_value,
            test_result.language,
            test_result.difficulty
        )
        
        if pb and pb.test_id == test_id:
            results['is_personal_best'] = True
    
    def _on_settings_save(self, settings: dict) -> None:
        """Called when settings are saved"""
        self.test_mode = settings.get('mode', 'words')
        self.test_word_count = settings.get('word_count', 50)
        self.test_time = settings.get('time_value', 60)
        self.test_language = settings.get('language', 'english')
        self.test_difficulty = settings.get('difficulty', 'normal')
        self.test_punctuation = settings.get('punctuation', False)
        self.test_numbers = settings.get('numbers', False)
        self.test_theme = settings.get('theme', 'dark')
        
        # Apply theme
        self._apply_theme(self.test_theme)
        
        # Update config
        self.config.test.default_mode = self.test_mode
        self.config.test.default_word_count = self.test_word_count
        self.config.test.default_time = self.test_time
        self.config.test.default_language = self.test_language
        self.config.test.difficulty = self.test_difficulty
        self.config.test.punctuation = self.test_punctuation
        self.config.test.numbers = self.test_numbers
        self.config.display.theme = self.test_theme
        
        # Save config
        self.config.save()
    
    def action_quit(self) -> None:
        """Quit the application"""
        self.db.close()
        self.exit()


def create_app() -> TypingTestApp:
    """Create and return the application instance"""
    return TypingTestApp()
