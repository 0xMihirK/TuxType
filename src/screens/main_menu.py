"""Main menu screen with keyboard navigation and row highlighting"""
from textual.screen import Screen
from textual.widgets import Static, Header
from textual.containers import Container, Vertical
from textual.binding import Binding
from textual import events
from rich.text import Text
from rich.style import Style
from typing import Optional

from ..widgets.status_bar import StatusBar


class MenuItem(Static):
    """A single menu item with full-width highlight support"""
    
    DEFAULT_CSS = """
    MenuItem {
        width: 100%;
        height: auto;
        min-height: 1;
        padding: 0 2;
    }
    
    MenuItem.selected {
        background: #313244;
    }
    """
    
    def __init__(self, key: str, label: str, color: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.key = key
        self.label = label
        self.color = color
        self.is_selected = False
    
    def render(self) -> Text:
        text = Text()
        # Use theme colors
        foreground = self.app.get_theme_color("foreground")
        pending = self.app.get_theme_color("pending")
        
        if self.is_selected:
            text.append("  ▸ ", Style(color=self.color, bold=True))
        else:
            text.append("    ", Style(color=pending))
        text.append(f"[{self.key}] ", Style(color=self.color, bold=True))
        text.append(self.label, Style(
            color=foreground if self.is_selected else pending
        ))
        return text
    
    def set_selected(self, selected: bool) -> None:
        self.is_selected = selected
        self.set_class(selected, "selected")
        self.refresh()


class MainMenuScreen(Screen):
    """Main menu with keyboard navigation and full-width row highlighting"""
    
    BINDINGS = [
        Binding("enter", "select", "Select", show=False),
        Binding("1", "start_test", "Start Test", show=False),
        Binding("2", "settings", "Settings", show=False),
        Binding("3", "stats", "Statistics", show=False),
        Binding("4", "history", "History", show=False),
        Binding("q", "quit", "Quit", show=False),
    ]
    
    CSS = """
    MainMenuScreen {
        background: $background;
    }
    
    #menu-outer {
        width: 100%;
        height: 100%;
        align: center middle;
    }
    
    #menu-box {
        width: 60;
        max-width: 90;
        height: auto;
        border: round #45475a;
        padding: 2 3;
        background: $surface;
    }
    
    #menu-title {
        text-align: center;
        width: 100%;
        height: 3;
        padding: 0 0 1 0;
    }
    
    #menu-items {
        width: 100%;
        height: auto;
        padding: 1 0;
    }
    
    #current-settings {
        width: 100%;
        height: auto;
        padding: 1 2;
        margin-top: 1;
        border-top: solid #313244;
    }
    
    #stats-summary {
        width: 100%;
        height: auto;
        padding: 0 2;
        color: #585b70;
    }
    """
    
    def __init__(self,
                 current_mode: str = "words",
                 current_value: int = 50,
                 current_language: str = "english",
                 avg_wpm: float = 0,
                 avg_accuracy: float = 0,
                 tests_today: int = 0,
                 streak: int = 0,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self.current_mode = current_mode
        self.current_value = current_value
        self.current_language = current_language
        self.avg_wpm = avg_wpm
        self.avg_accuracy = avg_accuracy
        self.tests_today = tests_today
        self.streak = streak
        self.selected_index = 0
        self.menu_items_data = [
            ("1", "Start Typing Test", "#a6e3a1", "start_test"),
            ("2", "Test Settings", "#89b4fa", "settings"),
            ("3", "View Statistics", "#f9e2af", "stats"),
            ("4", "History", "#cba6f7", "history"),
            ("Q", "Quit", "#f38ba8", "quit"),
        ]
    
    def compose(self):
        """Create child widgets"""
        yield Header(show_clock=True)
        
        with Container(id="menu-outer"):
            with Vertical(id="menu-box"):
                yield Static(self._render_title(), id="menu-title")
                
                with Vertical(id="menu-items"):
                    for i, (key, label, color, _) in enumerate(self.menu_items_data):
                        yield MenuItem(key, label, color, id=f"menu-item-{i}")
                
                yield Static(self._render_current_settings(), id="current-settings")
                yield Static(self._render_stats_summary(), id="stats-summary")
        
        yield StatusBar(context="Main Menu", hints="↑↓ navigate  enter select")
    
    def on_mount(self) -> None:
        """Highlight the first item on mount"""
        self._update_selection()
    
    def _render_title(self) -> Text:
        """Render the title"""
        text = Text(justify="center")
        text.append("🐧 ", style=Style(color="#89dceb"))
        text.append("TUXTYPE", style=Style(color="#89b4fa", bold=True))
        return text
    
    def _render_current_settings(self) -> Text:
        """Render current test settings"""
        text = Text()
        pending = self.app.get_theme_color("pending")
        border = self.app.get_theme_color("border")
        
        text.append("  Mode: ", Style(color=pending))
        text.append(f"{self.current_mode}", Style(color="#89b4fa"))
        text.append("  │  ", Style(color=border))
        text.append(f"{self.current_value}", Style(color="#a6e3a1"))
        text.append("  │  ", Style(color=border))
        text.append(f"{self.current_language}", Style(color="#f9e2af"))
        return text
    
    def _render_stats_summary(self) -> Text:
        """Render quick stats summary"""
        text = Text()
        pending = self.app.get_theme_color("pending")
        border = self.app.get_theme_color("border")
        
        if self.avg_wpm > 0:
            text.append(f"\n  Avg: ", Style(color=pending))
            text.append(f"{self.avg_wpm:.0f} wpm", Style(color="#89b4fa"))
            text.append("  │  ", Style(color=border))
            text.append(f"{self.avg_accuracy:.1f}%", Style(color="#a6e3a1"))
        
        if self.tests_today > 0 or self.streak > 0:
            text.append(f"\n  Today: ", Style(color=pending))
            text.append(f"{self.tests_today} tests", Style(color=pending))
            if self.streak > 0:
                text.append("  │  ", Style(color=border))
                text.append(f"{self.streak}d streak ", Style(color="#f9e2af"))
                text.append("🔥", Style(color="#fab387"))
        
        return text
    
    def _update_selection(self) -> None:
        """Update visual selection of menu items"""
        for i in range(len(self.menu_items_data)):
            try:
                item = self.query_one(f"#menu-item-{i}", MenuItem)
                item.set_selected(i == self.selected_index)
            except Exception:
                pass
    
    def on_key(self, event: events.Key) -> None:
        """Handle keyboard navigation"""
        key = event.key
        
        if key in ("up", "k"):
            self.selected_index = (self.selected_index - 1) % len(self.menu_items_data)
            self._update_selection()
            event.prevent_default()
            event.stop()
        elif key in ("down", "j"):
            self.selected_index = (self.selected_index + 1) % len(self.menu_items_data)
            self._update_selection()
            event.prevent_default()
            event.stop()
    
    def action_select(self) -> None:
        """Execute the currently selected menu action"""
        _, _, _, action = self.menu_items_data[self.selected_index]
        getattr(self, f"action_{action}")()
    
    def update_stats(self, avg_wpm: float, avg_accuracy: float,
                     tests_today: int, streak: int) -> None:
        """Update displayed statistics"""
        self.avg_wpm = avg_wpm
        self.avg_accuracy = avg_accuracy
        self.tests_today = tests_today
        self.streak = streak
        try:
            stats_widget = self.query_one("#stats-summary", Static)
            stats_widget.update(self._render_stats_summary())
        except Exception:
            pass
    
    def action_start_test(self) -> None:
        """Start a typing test"""
        self.app.push_screen("test")
    
    def action_settings(self) -> None:
        """Open settings"""
        self.app.push_screen("settings")
    
    def action_stats(self) -> None:
        """View statistics"""
        self.app.push_screen("stats")
    
    def action_history(self) -> None:
        """View history"""
        self.app.push_screen("history")
    
    def action_quit(self) -> None:
        """Quit the application"""
        self.app.exit()
