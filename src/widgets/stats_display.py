"""Stats display widget for real-time statistics"""
from textual.widget import Widget
from textual.reactive import reactive
from rich.text import Text
from rich.style import Style
from rich.table import Table
from rich.console import RenderableType
from typing import Optional


class StatsDisplay(Widget):
    """Widget for displaying real-time typing statistics"""
    
    DEFAULT_CSS = """
    StatsDisplay {
        width: 100%;
        height: auto;
        min-height: 3;
        padding: 0 1;
    }
    """
    
    # Reactive properties for auto-refresh
    wpm: reactive[float] = reactive(0.0)
    raw_wpm: reactive[float] = reactive(0.0)
    accuracy: reactive[float] = reactive(100.0)
    time_elapsed: reactive[float] = reactive(0.0)
    time_remaining: reactive[Optional[float]] = reactive(None)
    mode: reactive[str] = reactive("words")
    mode_value: reactive[int] = reactive(50)
    
    def __init__(self,
                 show_raw_wpm: bool = False,
                 show_time: bool = True,
                 compact: bool = False,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self._show_raw_wpm = show_raw_wpm
        self._show_time = show_time
        self._compact = compact
        
        # Colors
        self._colors = {
            'wpm': '#89b4fa',
            'accuracy': '#a6e3a1',
            'time': '#f9e2af',
            'label': '#6c7086',
            'value': '#cdd6f4',
        }
    
    def update_stats(self, wpm: float, accuracy: float, 
                     time_elapsed: float, raw_wpm: float = 0,
                     time_remaining: Optional[float] = None) -> None:
        """Update all statistics at once"""
        self.wpm = wpm
        self.raw_wpm = raw_wpm
        self.accuracy = accuracy
        self.time_elapsed = time_elapsed
        self.time_remaining = time_remaining
        self.refresh()
    
    def set_mode(self, mode: str, mode_value: int) -> None:
        """Set test mode display"""
        self.mode = mode
        self.mode_value = mode_value
        self.refresh()
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds as M:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
    
    def render(self) -> RenderableType:
        """Render the stats display"""
        if self._compact:
            return self._render_compact()
        return self._render_full()
    
    def _render_compact(self) -> Text:
        """Render compact single-line stats"""
        text = Text()
        
        # WPM
        text.append("WPM: ", Style(color=self._colors['label']))
        text.append(f"{self.wpm:.0f}", Style(color=self._colors['wpm'], bold=True))
        
        text.append("  │  ")
        
        # Accuracy
        text.append("Acc: ", Style(color=self._colors['label']))
        acc_color = self._colors['accuracy'] if self.accuracy >= 95 else '#f38ba8'
        text.append(f"{self.accuracy:.1f}%", Style(color=acc_color))
        
        if self._show_time:
            text.append("  │  ")
            
            if self.time_remaining is not None:
                text.append("Time: ", Style(color=self._colors['label']))
                text.append(self._format_time(self.time_remaining), 
                           Style(color=self._colors['time']))
            else:
                text.append("Time: ", Style(color=self._colors['label']))
                text.append(self._format_time(self.time_elapsed),
                           Style(color=self._colors['time']))
        
        return text
    
    def _render_full(self) -> Text:
        """Render full stats display"""
        text = Text()
        
        # Mode info
        mode_str = f"{self.mode_value} {self.mode}" if self.mode == "words" else f"{self.mode_value}s"
        text.append(f"Mode: {mode_str}", Style(color=self._colors['label']))
        text.append("  │  ")
        
        # WPM
        text.append("WPM: ", Style(color=self._colors['label']))
        text.append(f"{self.wpm:.1f}", Style(color=self._colors['wpm'], bold=True))
        
        # Raw WPM
        if self._show_raw_wpm:
            text.append("  │  ")
            text.append("Raw: ", Style(color=self._colors['label']))
            text.append(f"{self.raw_wpm:.1f}", Style(color=self._colors['value']))
        
        text.append("  │  ")
        
        # Accuracy
        text.append("Accuracy: ", Style(color=self._colors['label']))
        acc_color = self._colors['accuracy'] if self.accuracy >= 95 else '#f38ba8'
        text.append(f"{self.accuracy:.1f}%", Style(color=acc_color))
        
        if self._show_time:
            text.append("  │  ")
            
            if self.time_remaining is not None:
                text.append("Remaining: ", Style(color=self._colors['label']))
                time_color = '#f38ba8' if self.time_remaining <= 10 else self._colors['time']
                text.append(self._format_time(self.time_remaining),
                           Style(color=time_color))
            else:
                text.append("Time: ", Style(color=self._colors['label']))
                text.append(self._format_time(self.time_elapsed),
                           Style(color=self._colors['time']))
        
        return text


class ResultsDisplay(Widget):
    """Widget for displaying final test results"""
    
    DEFAULT_CSS = """
    ResultsDisplay {
        width: 100%;
        height: auto;
        padding: 1 2;
    }
    """
    
    def __init__(self, results: Optional[dict] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._results = results or {}
    
    def set_results(self, results: dict) -> None:
        """Set the results to display"""
        self._results = results
        self.refresh()
    
    def render(self) -> RenderableType:
        """Render the results"""
        if not self._results:
            return Text("No results to display")
        
        text = Text()
        
        # Main stats line
        wpm = self._results.get('wpm', 0)
        raw_wpm = self._results.get('raw_wpm', 0)
        accuracy = self._results.get('accuracy', 0)
        consistency = self._results.get('consistency', 0)
        
        # WPM in large style
        text.append("WPM: ", Style(color='#6c7086'))
        text.append(f"{wpm:.1f}", Style(color='#89b4fa', bold=True))
        
        text.append("    ")
        
        text.append("Raw: ", Style(color='#6c7086'))
        text.append(f"{raw_wpm:.1f}", Style(color='#cdd6f4'))
        
        text.append("    ")
        
        text.append("Accuracy: ", Style(color='#6c7086'))
        acc_color = '#a6e3a1' if accuracy >= 95 else '#f38ba8'
        text.append(f"{accuracy:.1f}%", Style(color=acc_color))
        
        text.append("    ")
        
        text.append("Consistency: ", Style(color='#6c7086'))
        text.append(f"{consistency:.1f}%", Style(color='#cdd6f4'))
        
        text.append("\n\n")
        
        # Character stats
        correct = self._results.get('characters_correct', 0)
        incorrect = self._results.get('characters_incorrect', 0)
        extra = self._results.get('characters_extra', 0)
        missed = self._results.get('characters_missed', 0)
        
        text.append("Characters: ", Style(color='#6c7086'))
        text.append(f"{correct}", Style(color='#a6e3a1'))
        text.append("/", Style(color='#6c7086'))
        text.append(f"{incorrect}", Style(color='#f38ba8'))
        text.append("/", Style(color='#6c7086'))
        text.append(f"{extra}", Style(color='#fab387'))
        text.append("/", Style(color='#6c7086'))
        text.append(f"{missed}", Style(color='#6c7086'))
        text.append("  (correct/incorrect/extra/missed)", Style(color='#45475a'))
        
        text.append("\n")
        
        # Duration
        duration = self._results.get('duration', 0)
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        text.append("Time: ", Style(color='#6c7086'))
        text.append(f"{minutes}:{seconds:02d}", Style(color='#f9e2af'))
        
        # Personal best indicator
        if self._results.get('is_personal_best'):
            text.append("  ")
            text.append("★ NEW PERSONAL BEST!", Style(color='#f9e2af', bold=True))
        
        return text
