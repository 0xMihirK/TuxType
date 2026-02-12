"""History screen for viewing past test results"""
import csv
import os
from pathlib import Path
from textual.screen import Screen
from textual.widgets import Static, Header, DataTable
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding
from rich.text import Text
from rich.style import Style
from typing import List, Optional
from datetime import datetime

from ..database.models import TestResult
from ..widgets.status_bar import StatusBar


class HistoryScreen(Screen):
    """Screen for viewing test history"""
    
    BINDINGS = [
        Binding("escape", "back", "Back", show=True),
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("delete", "delete", "Delete", show=True),
        Binding("c", "clear_history", "Clear All", show=True),
        Binding("e", "export", "Export CSV", show=True),
    ]
    
    CSS = """
    HistoryScreen {
        background: $background;
    }
    
    #history-container {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }
    
    #header-row {
        height: auto;
        width: 100%;
        align-vertical: middle;
        padding: 0 0 1 0;
    }
    
    #title {
        width: 1fr;
        text-align: center;
    }
    
    #clear-hint {
        width: auto;
        dock: right;
    }
    
    #table-container {
        height: 100%;
        border: round #45475a;
        padding: 0;
    }
    
    DataTable {
        height: 100%;
    }
    
    DataTable > .datatable--header {
        background: #313244;
        color: #cdd6f4;
    }
    
    DataTable > .datatable--cursor {
        background: #45475a;
    }
    
    #summary {
        padding: 1 0 0 0;
        color: #6c7086;
    }
    
    #hint {
        text-align: center;
        color: #6c7086;
        padding: 1 0 0 0;
    }
    """
    
    def __init__(self, results: Optional[List[TestResult]] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.results = results or []
    
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
        
        with Container(id="history-container"):
            with Horizontal(id="header-row"):
                yield Static(self._render_title(), id="title")
                yield Static(self._render_clear_hint(), id="clear-hint")
            
            with Vertical(id="table-container"):
                yield DataTable(id="history-table")
            
            yield Static(self._render_summary(), id="summary")
            yield Static(self._render_hint(), id="hint")
        
        yield StatusBar(context="History", hints="esc back")
    
    def on_mount(self) -> None:
        """Initialize table when mounted"""
        table = self.query_one("#history-table", DataTable)
        
        # Add columns
        table.add_column("Date/Time", key="datetime", width=18)
        table.add_column("Mode", key="mode", width=8)
        table.add_column("WPM", key="wpm", width=6)
        table.add_column("Acc", key="accuracy", width=7)
        table.add_column("Cons", key="consistency", width=6)
        table.add_column("PB", key="pb", width=3)
        
        # Load data from database
        self._load_data()
    
    def _load_data(self) -> None:
        """Load test history from database"""
        table = self.query_one("#history-table", DataTable)
        table.clear()
        
        # Get results from app's database
        if hasattr(self.app, 'db'):
            self.results = self.app.db.get_test_results(limit=100)
        
        # Add rows
        for result in self.results:
            # Format datetime
            dt_str = result.timestamp.strftime("%Y-%m-%d %H:%M")
            
            # Format mode
            if result.mode == "words":
                mode_str = f"{result.mode_value}w"
            elif result.mode == "time":
                mode_str = f"{result.mode_value}s"
            else:
                mode_str = result.mode
            
            # Format accuracy with color indicator
            acc_str = f"{result.accuracy:.1f}%"
            
            # Format consistency
            cons_str = f"{result.consistency:.0f}%"
            
            # Personal best indicator
            pb_str = "⭐" if result.is_personal_best else ""
            
            table.add_row(
                dt_str,
                mode_str,
                f"{result.wpm:.0f}",
                acc_str,
                cons_str,
                pb_str,
                key=str(result.id)
            )
        
        # Update summary
        summary = self.query_one("#summary", Static)
        summary.update(self._render_summary())
    
    def _render_title(self) -> Text:
        """Render title"""
        text = Text()
        colors = self.theme_colors
        text.append("📊 ", Style(color=colors['accent']))
        text.append("TEST HISTORY", Style(color=colors['foreground'], bold=True))
        return text
    
    def _render_clear_hint(self) -> Text:
        """Render clear history hint"""
        text = Text()
        colors = self.theme_colors
        text.append("[C] ", Style(color=colors['incorrect']))
        text.append("Clear History", Style(color=colors['pending']))
        return text
    
    def _render_summary(self, extra_message: str = "") -> Text:
        """Render summary"""
        text = Text()
        colors = self.theme_colors
        text.append(f"Showing {len(self.results)} tests", Style(color=colors['pending']))
        
        if self.results:
            # Calculate averages
            avg_wpm = sum(r.wpm for r in self.results) / len(self.results)
            avg_acc = sum(r.accuracy for r in self.results) / len(self.results)
            
            text.append("  •  ", Style(color=colors['border']))
            text.append(f"Avg: {avg_wpm:.0f} WPM, {avg_acc:.1f}% accuracy", 
                       Style(color=colors['pending']))
        
        if extra_message:
            text.append("  •  ", Style(color=colors['border']))
            text.append(extra_message, Style(color=colors['correct']))
        
        return text
    
    def _render_hint(self) -> Text:
        """Render navigation hint"""
        text = Text()
        colors = self.theme_colors
        text.append("[↑/↓] ", Style(color=colors['accent']))
        text.append("Navigate  ", Style(color=colors['pending']))
        text.append("[E] ", Style(color=colors['correct']))
        text.append("Export  ", Style(color=colors['pending']))
        text.append("[Del] ", Style(color=colors['incorrect']))
        text.append("Delete  ", Style(color=colors['pending']))
        text.append("[C] ", Style(color=colors['incorrect']))
        text.append("Clear All  ", Style(color=colors['pending']))
        text.append("[Esc] ", Style(color=colors['pending']))
        text.append("Back", Style(color=colors['pending']))
        return text
    
    def action_back(self) -> None:
        """Return to previous screen"""
        self.app.pop_screen()
    
    def action_delete(self) -> None:
        """Delete selected test"""
        table = self.query_one("#history-table", DataTable)
        if table.row_count == 0:
            return
        try:
            row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
            test_id = int(row_key.value)
            if hasattr(self.app, 'db'):
                self.app.db.delete_test(test_id)
                self._load_data()
        except Exception:
            pass
            
    def action_clear_history(self) -> None:
        """Clear all history"""
        if hasattr(self.app, 'db'):
            self.app.db.clear_history()
            self._load_data()
            
            # Show feedback
            summary = self.query_one("#summary", Static)
            summary.update(self._render_summary(
                extra_message="✓ History cleared"
            ))
    
    def action_export(self) -> None:
        """Export history to CSV"""
        if not self.results:
            return
        
        # Create exports directory
        base_dir = Path(__file__).parent.parent.parent
        export_dir = base_dir / "data" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = export_dir / f"tuxtype_history_{timestamp}.csv"
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Header row
                writer.writerow([
                    "Date", "Time", "Mode", "Value", "Language",
                    "WPM", "Raw WPM", "Accuracy", "Consistency",
                    "Correct", "Incorrect", "Extra", "Missed",
                    "Duration (s)", "Punctuation", "Numbers", "PB"
                ])
                # Data rows
                for r in self.results:
                    writer.writerow([
                        r.timestamp.strftime("%Y-%m-%d"),
                        r.timestamp.strftime("%H:%M:%S"),
                        r.mode,
                        r.mode_value,
                        r.language,
                        f"{r.wpm:.1f}",
                        f"{r.raw_wpm:.1f}",
                        f"{r.accuracy:.1f}",
                        f"{r.consistency:.1f}",
                        r.characters_correct,
                        r.characters_incorrect,
                        r.characters_extra,
                        r.characters_missed,
                        f"{r.test_duration:.1f}",
                        "Yes" if r.punctuation else "No",
                        "Yes" if r.numbers else "No",
                        "Yes" if r.is_personal_best else "No",
                    ])
            
            # Show success feedback
            summary = self.query_one("#summary", Static)
            summary.update(self._render_summary(
                extra_message=f"✓ Exported to {filepath.name}"
            ))
        except Exception as e:
            summary = self.query_one("#summary", Static)
            summary.update(self._render_summary(
                extra_message=f"✗ Export failed: {e}"
            ))
