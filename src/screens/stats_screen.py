"""Statistics screen for viewing overall statistics"""
from textual.screen import Screen
from textual.widgets import Static, Header
from textual.containers import Container, Vertical
from textual.binding import Binding
from rich.text import Text
from rich.style import Style
from typing import Optional

from ..widgets.status_bar import StatusBar
from ..constants import DEFAULT_SPARKLINE_LIMIT

# Block characters for bar graph (from thin to full)
BAR_CHARS = " ▁▂▃▄▅▆▇█"


class StatsScreen(Screen):
    """Screen for viewing overall statistics"""
    
    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        Binding("h", "history", "History", show=True),
        Binding("p", "personal_bests", "Personal Bests", show=True),
    ]
    
    CSS = """
    StatsScreen {
        background: $background;
    }
    
    #stats-container {
        width: 100%;
        height: 100%;
        align: center middle;
        overflow-y: auto;
    }
    
    #stats-box {
        width: 80;
        height: auto;
        border: round #f9e2af;
        padding: 1 2;
        background: $surface;
    }
    
    #title {
        text-align: center;
        padding: 0 0 1 0;
        border-bottom: solid #45475a;
    }
    
    .stats-section {
        padding: 1 0;
    }
    
    #hint {
        text-align: center;
        color: #6c7086;
        padding: 1 0 0 0;
        border-top: solid #45475a;
    }
    """
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.stats = {'total_tests': 0, 'total_time': 0, 'total_words': 0, 'total_chars': 0}
        self.personal_bests = []
        self.avg_last10 = {'avg_wpm': 0, 'avg_accuracy': 0, 'avg_consistency': 0}
        self.avg_all = {'avg_wpm': 0, 'avg_accuracy': 0, 'avg_consistency': 0}
        self.current_streak = 0
        self.best_streak = 0
        self.wpm_sparkline_data = []
        self.accuracy_sparkline_data = []
        self._show_all_pbs = False
    
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
        
        with Container(id="stats-container"):
            with Vertical(id="stats-box"):
                yield Static(self._render_title(), id="title")
                yield Static(self._render_overall_stats(), id="overall-stats", classes="stats-section")
                
                # Performance trends with text-based bar graphs
                yield Static(self._render_performance_graphs(), id="perf-graphs", classes="stats-section")
                
                yield Static(self._render_averages(), id="averages-text", classes="stats-section")
                yield Static(self._render_personal_bests(), id="pb-section", classes="stats-section")
                yield Static(self._render_hint(), id="hint")
        
        yield StatusBar(context="Statistics", hints="esc back")
    
    def on_mount(self) -> None:
        """Load stats when mounted"""
        self._load_stats()
    
    def _load_stats(self) -> None:
        """Load statistics from database"""
        if hasattr(self.app, 'db'):
            self.stats = self.app.db.get_total_stats()
            self.avg_last10 = self.app.db.get_average_stats(limit=10)
            self.avg_all = self.app.db.get_average_stats()
            self.personal_bests = self.app.db.get_personal_bests()
            current_streak, best_streak = self.app.db.get_streak()
            self.current_streak = current_streak
            self.best_streak = best_streak
            
            # Load sparkline data
            wpm_data, accuracy_data = self.app.db.get_recent_sparkline_data(limit=DEFAULT_SPARKLINE_LIMIT)
            self.wpm_sparkline_data = wpm_data
            self.accuracy_sparkline_data = accuracy_data
        else:
            self.stats = {'total_tests': 0, 'total_time': 0, 'total_words': 0, 'total_chars': 0}
            self.avg_last10 = {'avg_wpm': 0, 'avg_accuracy': 0, 'avg_consistency': 0}
            self.avg_all = {'avg_wpm': 0, 'avg_accuracy': 0, 'avg_consistency': 0}
            self.current_streak = 0
            self.best_streak = 0
            self.wpm_sparkline_data = []
            self.accuracy_sparkline_data = []
        
        # Update displays
        try:
            self.query_one("#overall-stats", Static).update(self._render_overall_stats())
            self.query_one("#perf-graphs", Static).update(self._render_performance_graphs())
            self.query_one("#averages-text", Static).update(self._render_averages())
            self.query_one("#pb-section", Static).update(self._render_personal_bests())
        except Exception:
            pass
    
    def _render_bar_graph(self, data: list, width: int = 60, color_low: str = "#89b4fa",
                          color_high: str = "#a6e3a1", label: str = "",
                          unit: str = "") -> Text:
        """Render a text-based bar graph using Unicode block characters."""
        text = Text()
        colors = self.theme_colors
        
        if not data or all(v == 0 for v in data):
            text.append(f"  {label}: ", Style(color=colors['pending']))
            text.append("No data yet\n", Style(color=colors['pending']))
            return text
        
        # Title line with min/max
        text.append(f"  {label}", Style(color=colors['pending']))
        text.append(f"  (min: ", Style(color=colors['pending']))
        text.append(f"{min(data):.0f}", Style(color=color_low))
        text.append(f"  max: ", Style(color=colors['pending']))
        text.append(f"{max(data):.0f}", Style(color=color_high))
        text.append(f"  latest: ", Style(color=colors['pending']))
        text.append(f"{data[-1]:.0f}{unit}", Style(color=color_high, bold=True))
        text.append(")\n", Style(color=colors['pending']))
        
        # Truncate to width
        display_data = data[-width:]
        
        min_val = min(display_data)
        max_val = max(display_data)
        val_range = max_val - min_val if max_val > min_val else 1
        
        # Render bars
        text.append("  ", Style())
        for i, val in enumerate(display_data):
            # Normalize to 0-8 range for block character selection
            normalized = int(((val - min_val) / val_range) * 8)
            normalized = max(1, min(8, normalized))  # at least ▁
            bar_char = BAR_CHARS[normalized]
            
            # Interpolate color from low to high
            t = (val - min_val) / val_range if val_range > 0 else 0.5
            if t < 0.5:
                color = color_low
            else:
                color = color_high
            
            text.append(bar_char, Style(color=color))
        
        text.append("\n")
        return text

    def _render_title(self) -> Text:
        """Render title"""
        text = Text()
        colors = self.theme_colors
        text.append("📈 ", Style(color=colors['accent']))
        text.append("STATISTICS DASHBOARD", Style(color=colors['foreground'], bold=True))
        return text
    
    def _render_performance_graphs(self) -> Text:
        """Render performance trends with text-based bar graphs"""
        text = Text()
        colors = self.theme_colors
        text.append("\n  📊 Performance Trends\n", Style(color=colors['foreground'], bold=True))
        text.append("  ─" * 30 + "\n", Style(color=colors['border']))
        
        # WPM bar graph
        wpm_graph = self._render_bar_graph(
            self.wpm_sparkline_data,
            width=60,
            color_low=colors['accent'],
            color_high=colors['correct'],
            label="WPM Trend (Last 20 Tests)",
            unit=" wpm"
        )
        text.append_text(wpm_graph)
        
        # Accuracy bar graph
        acc_graph = self._render_bar_graph(
            self.accuracy_sparkline_data,
            width=60,
            color_low=colors['incorrect'],
            color_high=colors['correct'],
            label="Accuracy Trend (Last 20 Tests)",
            unit="%"
        )
        text.append_text(acc_graph)
        
        return text
    
    def _render_overall_stats(self) -> Text:
        """Render overall statistics"""
        text = Text()
        colors = self.theme_colors
        text.append("\n  Overall Statistics\n", Style(color=colors['foreground'], bold=True))
        text.append("  ─" * 30 + "\n", Style(color=colors['border']))
        
        total_tests = self.stats.get('total_tests', 0)
        total_time = self.stats.get('total_time', 0)
        total_words = self.stats.get('total_words', 0)
        total_chars = self.stats.get('total_chars', 0)
        
        # Format time
        hours = int(total_time // 3600)
        minutes = int((total_time % 3600) // 60)
        time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        
        # Row 1
        text.append("  Tests Completed: ", Style(color=colors['pending']))
        text.append(f"{total_tests:,}", Style(color=colors['accent']))
        text.append("      Time Typed: ", Style(color=colors['pending']))
        text.append(f"{time_str}", Style(color=colors['warning']))
        text.append("\n")
        
        # Row 2
        text.append("  Words Typed: ", Style(color=colors['pending']))
        text.append(f"{total_words:,}", Style(color=colors['correct']))
        text.append("         Chars Typed: ", Style(color=colors['pending']))
        text.append(f"{total_chars:,}", Style(color=colors['foreground']))
        text.append("\n")
        
        # Row 3 - Streaks
        text.append("  Current Streak: ", Style(color=colors['pending']))
        if self.current_streak > 0:
            text.append(f"{self.current_streak}d ", Style(color=colors['warning']))
            text.append("🔥", Style(color=colors['extra']))
        else:
            text.append("0d", Style(color=colors['pending']))
        text.append("      Best Streak: ", Style(color=colors['pending']))
        text.append(f"{self.best_streak}d", Style(color=colors['foreground']))
        text.append("\n")
        
        return text
    
    def _render_averages(self) -> Text:
        """Render performance averages"""
        text = Text()
        colors = self.theme_colors
        text.append("\n  Performance Averages\n", Style(color=colors['foreground'], bold=True))
        text.append("  ─" * 30 + "\n", Style(color=colors['border']))
        
        # Table header
        text.append("                  Last 10        All Time\n", Style(color=colors['pending']))
        text.append("  ─" * 30 + "\n", Style(color=colors['border']))
        
        # WPM
        text.append("  WPM:            ", Style(color=colors['pending']))
        text.append(f"{self.avg_last10.get('avg_wpm', 0):>6.1f}", Style(color=colors['accent']))
        text.append("          ", Style(color=colors['pending']))
        text.append(f"{self.avg_all.get('avg_wpm', 0):>6.1f}", Style(color=colors['accent']))
        text.append("\n")
        
        # Accuracy
        text.append("  Accuracy:       ", Style(color=colors['pending']))
        text.append(f"{self.avg_last10.get('avg_accuracy', 0):>5.1f}%", Style(color=colors['correct']))
        text.append("          ", Style(color=colors['pending']))
        text.append(f"{self.avg_all.get('avg_accuracy', 0):>5.1f}%", Style(color=colors['correct']))
        text.append("\n")
        
        # Consistency
        text.append("  Consistency:    ", Style(color=colors['pending']))
        text.append(f"{self.avg_last10.get('avg_consistency', 0):>5.1f}%", Style(color=colors['foreground']))
        text.append("          ", Style(color=colors['pending']))
        text.append(f"{self.avg_all.get('avg_consistency', 0):>5.1f}%", Style(color=colors['foreground']))
        text.append("\n")
        
        return text
    
    def _render_personal_bests(self) -> Text:
        """Render personal bests"""
        text = Text()
        colors = self.theme_colors
        text.append("\n  Personal Bests\n", Style(color=colors['foreground'], bold=True))
        text.append("  ─" * 30 + "\n", Style(color=colors['border']))
        
        if not self.personal_bests:
            text.append("  No personal bests yet. Start typing!\n", Style(color=colors['pending']))
            return text
        
        # Show top 5 or all PBs based on toggle
        display_count = len(self.personal_bests) if self._show_all_pbs else min(5, len(self.personal_bests))
        for pb in self.personal_bests[:display_count]:
            # Format mode
            if pb.mode == "words":
                mode_str = f"{pb.mode_value}w"
            elif pb.mode == "time":
                mode_str = f"{pb.mode_value}s"
            else:
                mode_str = pb.mode
            
            text.append(f"  {mode_str:8}", Style(color=colors['accent']))
            text.append(f"  {pb.wpm:>5.1f} WPM", Style(color=colors['warning'], bold=True))
            text.append(f"  ({pb.accuracy:.1f}%)", Style(color=colors['correct']))
            text.append(f"  {pb.achieved_at.strftime('%Y-%m-%d')}", Style(color=colors['pending']))
            text.append("\n")
        
        return text
    
    def _render_hint(self) -> Text:
        """Render navigation hint"""
        text = Text()
        colors = self.theme_colors
        text.append("\n[H] ", Style(color=colors['extra'])) # Purple/Extra
        text.append("History  ", Style(color=colors['pending']))
        text.append("[P] ", Style(color=colors['warning']))
        pb_label = "Show Less" if self._show_all_pbs else "Show All PBs"
        text.append(f"{pb_label}  ", Style(color=colors['pending']))
        text.append("[Esc] ", Style(color=colors['incorrect']))
        text.append("Back", Style(color=colors['pending']))
        return text
    
    def action_back(self) -> None:
        """Return to previous screen"""
        self.app.pop_screen()
    
    def action_history(self) -> None:
        """Go to history screen"""
        self.app.pop_screen()
        self.app.push_screen("history")
    
    def action_personal_bests(self) -> None:
        """Toggle showing all personal bests"""
        self._show_all_pbs = not self._show_all_pbs
        try:
            self.query_one("#pb-section", Static).update(self._render_personal_bests())
        except Exception:
            pass
