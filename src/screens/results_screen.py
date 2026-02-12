"""Results screen for displaying test results"""
from textual.screen import Screen
from textual.widgets import Static, Header
from textual.containers import Container, Vertical
from textual.binding import Binding
from rich.text import Text
from rich.style import Style
from typing import Optional

from ..widgets.stats_display import ResultsDisplay
from ..widgets.graph import PerformanceGraph
from ..widgets.status_bar import StatusBar


class ResultsScreen(Screen):
    """Screen for displaying typing test results"""
    
    BINDINGS = [
        Binding("tab", "continue", "Continue", show=True),
        Binding("r", "retry", "Retry", show=True),
        Binding("m", "menu", "Menu", show=True),
        Binding("h", "history", "History", show=True),
    ]
    
    CSS = """
    ResultsScreen {
        background: $background;
    }
    
    #results-container {
        width: 100%;
        height: 100%;
        align: center middle;
    }
    
    #results-box {
        width: 80;
        max-width: 90;
        height: auto;
        border: round #45475a;
        padding: 2 3;
        background: $surface;
    }
    
    #title {
        text-align: center;
        padding: 0 0 1 0;
    }
    
    #main-stats {
        padding: 1 0;
        border-bottom: solid #45475a;
    }
    
    #graph-area {
        padding: 1 0;
    }
    
    #details {
        padding: 1 0;
        border-top: solid #45475a;
    }
    
    #hint {
        text-align: center;
        color: #6c7086;
        padding: 1 0 0 0;
    }
    """
    
    def __init__(self, results: Optional[dict] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.results = results or {}
    
    @property
    def theme_colors(self):
        """Get current theme colors"""
        return {
            'accent': self.app.get_theme_color('accent'),
            'correct': self.app.get_theme_color('correct'),
            'incorrect': self.app.get_theme_color('incorrect'),
            'extra': self.app.get_theme_color('extra'),
            'foreground': self.app.get_theme_color('foreground'),
            'pending': self.app.get_theme_color('pending'),
            'border': self.app.get_theme_color('border'),
            'warning': self.app.get_theme_color('warning'),
        }
    
    def compose(self):
        """Create child widgets"""
        yield Header(show_clock=True)
        
        with Container(id="results-container"):
            with Vertical(id="results-box"):
                yield Static(self._render_title(), id="title")
                yield Static(self._render_main_stats(), id="main-stats")
                yield PerformanceGraph(
                    data=self.results.get('wpm_history', []),
                    id="graph-area"
                )
                yield Static(self._render_details(), id="details")
                yield Static(self._render_hint(), id="hint")
        
        yield StatusBar(context="Results", hints="tab continue  r retry  m menu")
    
    def _render_title(self) -> Text:
        """Render title"""
        text = Text()
        colors = self.theme_colors
        
        status = self.results.get('status', 'completed')
        if status == 'completed':
            text.append("✓ ", Style(color=colors['correct']))
            text.append("TEST COMPLETED", Style(color=colors['foreground'], bold=True))
        elif status == 'failed':
            text.append("✗ ", Style(color=colors['incorrect']))
            text.append("TEST FAILED", Style(color=colors['incorrect'], bold=True))
        else:
            text.append("TEST RESULTS", Style(color=colors['foreground'], bold=True))
        
        return text
    
    def _render_main_stats(self) -> Text:
        """Render main statistics"""
        text = Text()
        colors = self.theme_colors
        
        wpm = self.results.get('wpm', 0)
        raw_wpm = self.results.get('raw_wpm', 0)
        accuracy = self.results.get('accuracy', 0)
        consistency = self.results.get('consistency', 0)
        
        # Big WPM display
        text.append("\n")
        text.append("  WPM: ", Style(color=colors['pending']))
        text.append(f"{wpm:.0f}", Style(color=colors['accent'], bold=True)) # Blue/Accent
        
        text.append("    Raw: ", Style(color=colors['pending']))
        text.append(f"{raw_wpm:.0f}", Style(color=colors['foreground']))
        
        text.append("    Accuracy: ", Style(color=colors['pending']))
        acc_color = colors['correct'] if accuracy >= 95 else colors['incorrect']
        text.append(f"{accuracy:.1f}%", Style(color=acc_color))
        
        text.append("    Consistency: ", Style(color=colors['pending']))
        text.append(f"{consistency:.0f}%", Style(color=colors['foreground']))
        
        text.append("\n")
        
        # Character breakdown
        correct = self.results.get('characters_correct', 0)
        incorrect = self.results.get('characters_incorrect', 0)
        extra = self.results.get('characters_extra', 0)
        missed = self.results.get('characters_missed', 0)
        
        text.append("\n  Characters: ", Style(color=colors['pending']))
        text.append(f"{correct}", Style(color=colors['correct']))
        text.append(" / ", Style(color=colors['border']))
        text.append(f"{incorrect}", Style(color=colors['incorrect']))
        text.append(" / ", Style(color=colors['border']))
        text.append(f"{extra}", Style(color=colors['extra']))
        text.append(" / ", Style(color=colors['border']))
        text.append(f"{missed}", Style(color=colors['pending']))
        text.append("  (correct/incorrect/extra/missed)", Style(color=colors['border']))
        
        # Personal best indicator
        if self.results.get('is_personal_best'):
            text.append("\n\n  ")
            text.append("★ NEW PERSONAL BEST! ★", Style(color=colors['accent'], bold=True))
        
        text.append("\n")
        
        return text
    
    def _render_details(self) -> Text:
        """Render test details"""
        text = Text()
        colors = self.theme_colors
        
        mode = self.results.get('mode', 'words')
        mode_value = self.results.get('mode_value', 50)
        duration = self.results.get('duration', 0)
        language = self.results.get('language', 'english')
        difficulty = self.results.get('difficulty', 'normal')
        
        text.append("\n  Test Details:\n", Style(color=colors['pending']))
        
        # Mode
        text.append("  • Mode: ", Style(color=colors['pending']))
        if mode == 'words':
            text.append(f"{mode_value} words", Style(color=colors['correct']))
        elif mode == 'time':
            text.append(f"{mode_value} seconds", Style(color=colors['accent']))
        else:
            text.append(mode, Style(color=colors['foreground']))
        
        # Duration
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        text.append(f"\n  • Time: ", Style(color=colors['pending']))
        text.append(f"{minutes}:{seconds:02d}", Style(color=colors['accent']))
        
        # Language
        text.append(f"\n  • Language: ", Style(color=colors['pending']))
        text.append(f"{language.capitalize()}", Style(color=colors['foreground']))
        
        # Difficulty
        if difficulty != 'normal':
            text.append(f"\n  • Difficulty: ", Style(color=colors['pending']))
            text.append(f"{difficulty.capitalize()}", Style(color=colors['incorrect']))
        
        text.append("\n")
        
        return text
    
    def _render_hint(self) -> Text:
        """Render navigation hint"""
        text = Text()
        colors = self.theme_colors
        text.append("[Tab] ", Style(color=colors['correct']))
        text.append("Continue  ", Style(color=colors['pending']))
        text.append("[R] ", Style(color=colors['accent'])) # Blue/Accent used for Retry? Or standard accent
        text.append("Retry  ", Style(color=colors['pending']))
        text.append("[H] ", Style(color=colors['warning'])) # Yellow/Warning
        text.append("History  ", Style(color=colors['pending']))
        text.append("[M] ", Style(color=colors['incorrect'])) # Red/Menu
        text.append("Menu", Style(color=colors['pending']))
        return text
    
    def on_mount(self) -> None:
        """Update graph when mounted"""
        graph = self.query_one("#graph-area", PerformanceGraph)
        graph.set_data(self.results.get('wpm_history', []))
    
    def action_continue(self) -> None:
        """Continue to next test"""
        # Stack: Menu → Test → Results → pop both, push new Test
        self.app.pop_screen()  # pop Results
        self.app.pop_screen()  # pop old Test
        self.app.push_screen("test")
    
    def action_retry(self) -> None:
        """Retry with same settings"""
        # Stack: Menu → Test → Results → pop both, push new Test
        self.app.pop_screen()  # pop Results
        self.app.pop_screen()  # pop old Test
        self.app.push_screen("test")
    
    def action_menu(self) -> None:
        """Return to main menu"""
        # Stack: Menu → Test → Results → pop both to land on Menu
        self.app.pop_screen()  # pop Results
        self.app.pop_screen()  # pop Test
    
    def action_history(self) -> None:
        """View test history"""
        # Stack: Menu → Test → Results → pop both, push History
        self.app.pop_screen()  # pop Results
        self.app.pop_screen()  # pop Test
        self.app.push_screen("history")
