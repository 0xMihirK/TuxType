"""Settings screen for test configuration"""
from textual.screen import Screen
from textual.widgets import Static, Button, Header, RadioButton, RadioSet, Switch
from textual.containers import Container, Vertical, Horizontal, Grid
from textual.binding import Binding
from rich.text import Text
from rich.style import Style
from typing import Optional, Callable

from ..widgets.status_bar import StatusBar


class SettingsScreen(Screen):
    """Screen for configuring test settings"""
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("s", "save_start", "Save & Start", show=True),
        Binding("d", "defaults", "Reset Defaults", show=True),
    ]
    
    CSS = """
    SettingsScreen {
        background: $background;
    }
    
    #settings-container {
        width: 100%;
        height: 1fr;
        align: center top;
        overflow-y: auto;
    }
    
    #settings-box {
        width: 75;
        max-width: 90;
        height: auto;
        padding: 2 3;
        margin: 1 0;
        background: $surface;
    }
    
    #title {
        text-align: center;
        padding: 0 0 1 0;
        border-bottom: solid #45475a;
    }
    
    .setting-group {
        padding: 1 0;
    }
    
    .setting-label {
        color: #6c7086;
        padding: 0 0 0 0;
    }
    
    RadioSet {
        height: auto;
        padding: 0 0 0 2;
    }
    
    RadioButton {
        padding: 0 1;
    }
    
    .option-row {
        height: auto;
        padding: 0 0 0 2;
    }
    
    Switch {
        padding: 0 1;
    }
    
    #actions {
        padding: 1 0 0 0;
        border-top: solid #45475a;
        text-align: center;
    }
    
    Button {
        margin: 0 1;
    }
    """
    
    def __init__(self,
                 mode: str = "words",
                 word_count: int = 50,
                 time_value: int = 60,
                 language: str = "english",
                 difficulty: str = "normal",
                 punctuation: bool = False,
                 numbers: bool = False,
                 theme: str = "dark",
                 on_save: Optional[Callable] = None,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        
        self.current_mode = mode
        self.current_word_count = word_count
        self.current_time = time_value
        self.current_language = language
        self.current_difficulty = difficulty
        self.punctuation = punctuation
        self.numbers = numbers
        self.current_theme = theme
        self.on_save_callback = on_save
    
    def compose(self):
        """Create child widgets"""
        yield Header(show_clock=True)
        
        with Container(id="settings-container"):
            with Vertical(id="settings-box"):
                yield Static(self._render_title(), id="title")
                
                # Mode selection (Words / Time only, no Quote)
                yield Static("Mode:", classes="setting-label")
                with RadioSet(id="mode-select"):
                    yield RadioButton("Words", id="mode-words", value=self.current_mode=="words")
                    yield RadioButton("Time", id="mode-time", value=self.current_mode=="time")
                
                # Word count (for word mode)
                yield Static("\nWord Count:", classes="setting-label", id="word-count-label")
                with RadioSet(id="word-count-select"):
                    for count in [10, 25, 50, 100]:
                        yield RadioButton(str(count), id=f"count-{count}", 
                                         value=self.current_word_count==count)
                
                # Time duration (for time mode)
                yield Static("\nTime Duration:", classes="setting-label", id="time-label")
                with RadioSet(id="time-select"):
                    for seconds in [15, 30, 60, 120]:
                        label = f"{seconds}s"
                        yield RadioButton(label, id=f"time-{seconds}",
                                         value=self.current_time==seconds)
                
                # Language
                yield Static("\nLanguage:", classes="setting-label")
                with RadioSet(id="language-select"):
                    yield RadioButton("English", id="lang-english",
                                     value=self.current_language=="english")
                    yield RadioButton("Programming", id="lang-programming",
                                     value=self.current_language=="programming")
                
                
                # Theme
                yield Static("\nTheme:", classes="setting-label")
                with RadioSet(id="theme-select"):
                    yield RadioButton("🌙 Dark", id="theme-dark",
                                     value=self.current_theme=="dark")
                    yield RadioButton("☀️ Light", id="theme-light",
                                     value=self.current_theme=="light")
                    yield RadioButton("🧛 Dracula", id="theme-dracula",
                                     value=self.current_theme=="dracula")
                
                # Options
                yield Static("\nOptions:", classes="setting-label")
                with Horizontal(classes="option-row"):
                    yield Switch(value=self.punctuation, id="punctuation-switch")
                    yield Static(" Punctuation", classes="setting-label")
                with Horizontal(classes="option-row"):
                    yield Switch(value=self.numbers, id="numbers-switch")
                    yield Static(" Numbers", classes="setting-label")
                
                # Actions
                yield Static(self._render_actions(), id="actions")
        
        yield StatusBar(context="Settings", hints="s save & start  d defaults  esc cancel")
    
    def _render_title(self) -> Text:
        """Render title"""
        text = Text()
        text.append("⚙️  ", Style(color="#89b4fa"))
        text.append("TEST SETTINGS", Style(color="#cdd6f4", bold=True))
        return text
    
    def _render_actions(self) -> Text:
        """Render action hints"""
        text = Text()
        text.append("\n[S] ", Style(color="#a6e3a1"))
        text.append("Save & Start  ", Style(color="#6c7086"))
        text.append("[D] ", Style(color="#f9e2af"))
        text.append("Reset Defaults  ", Style(color="#6c7086"))
        text.append("[Esc] ", Style(color="#f38ba8"))
        text.append("Cancel", Style(color="#6c7086"))
        return text
    
    def _get_selected_settings(self) -> dict:
        """Get currently selected settings"""
        settings = {
            'mode': 'words',
            'word_count': 50,
            'time_value': 60,
            'language': 'english',
            'difficulty': 'normal',
            'punctuation': False,
            'numbers': False,
            'theme': 'dark'
        }
        
        # Get mode
        mode_set = self.query_one("#mode-select", RadioSet)
        if mode_set.pressed_button:
            if mode_set.pressed_button.id == "mode-time":
                settings['mode'] = 'time'
        
        # Get word count
        count_set = self.query_one("#word-count-select", RadioSet)
        if count_set.pressed_button:
            count = count_set.pressed_button.id.replace("count-", "")
            settings['word_count'] = int(count)
        
        # Get time
        time_set = self.query_one("#time-select", RadioSet)
        if time_set.pressed_button:
            time_val = time_set.pressed_button.id.replace("time-", "")
            settings['time_value'] = int(time_val)
        
        # Get language
        lang_set = self.query_one("#language-select", RadioSet)
        if lang_set.pressed_button:
            settings['language'] = lang_set.pressed_button.id.replace("lang-", "")
        
        # Get theme
        theme_set = self.query_one("#theme-select", RadioSet)
        if theme_set.pressed_button:
            settings['theme'] = theme_set.pressed_button.id.replace("theme-", "")
        
        # Get switches
        settings['punctuation'] = self.query_one("#punctuation-switch", Switch).value
        settings['numbers'] = self.query_one("#numbers-switch", Switch).value
        
        return settings
    
    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Handle radio set changes"""
        # Immediate theme application
        if event.radio_set.id == "theme-select" and event.pressed:
            theme = event.pressed.id.replace("theme-", "")
            self.current_theme = theme
            self.app._apply_theme(theme)
    
    def action_save_start(self) -> None:
        """Save settings and start test"""
        settings = self._get_selected_settings()
        
        if self.on_save_callback:
            self.on_save_callback(settings)
        
        # Update app state
        self.app.test_mode = settings['mode']
        self.app.test_word_count = settings['word_count']
        self.app.test_time = settings['time_value']
        self.app.test_language = settings['language']
        self.app.test_difficulty = settings['difficulty']
        self.app.test_punctuation = settings['punctuation']
        self.app.test_numbers = settings['numbers']
        
        # Apply theme
        theme = settings.get('theme', 'dark')
        self.app._apply_theme(theme)
        
        # Go to test screen
        self.app.pop_screen()
        self.app.push_screen("test")
    
    def action_defaults(self) -> None:
        """Reset to default settings"""
        # This would reset all radio buttons and switches
        # For simplicity, just pop and re-push the screen
        self.app.pop_screen()
        self.app.push_screen("settings")
    
    def action_cancel(self) -> None:
        """Cancel and return to menu"""
        self.app.pop_screen()
