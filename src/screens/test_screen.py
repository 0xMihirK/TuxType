"""Test screen — Monkeytype-style paragraph viewport with continuous flow"""
import time
from textual.screen import Screen
from textual.widgets import Static, Header
from textual.containers import Container, Vertical
from textual.binding import Binding
from textual.timer import Timer
from textual import events
from rich.text import Text
from rich.style import Style
from typing import Optional, Callable, List

from ..core.test_engine import TestEngine, TestMode, Difficulty, TestStatus
from ..widgets.status_bar import StatusBar
from ..constants import MAX_LINE_WIDTH, VIEWPORT_LINES, BAR_FILLED, BAR_EMPTY, BAR_WIDTH


def wrap_words_to_lines(words: list, max_width: int) -> List[List[int]]:
    """Group word indices into lines that fit within max_width characters.
    
    Args:
        words: List of word strings (or WordState objects with .word attribute)
        max_width: Maximum character width per line
        
    Returns:
        List of lists, where each inner list contains word indices for that line
    """
    lines: List[List[int]] = []
    current_line: List[int] = []
    current_width = 0
    
    for i, w in enumerate(words):
        word = w.word if hasattr(w, 'word') else str(w)
        word_len = len(word)
        
        # Check if adding this word (+ space) exceeds line width
        needed = word_len + (1 if current_width > 0 else 0)
        
        if current_width + needed > max_width and current_line:
            # Start a new line
            lines.append(current_line)
            current_line = [i]
            current_width = word_len
        else:
            current_line.append(i)
            current_width += needed
    
    # Don't forget the last line
    if current_line:
        lines.append(current_line)
    
    return lines


class TestScreen(Screen):
    """Typing test screen with paragraph viewport and continuous flow"""
    
    BINDINGS = [
        Binding("tab", "restart", "Restart", show=False),
        Binding("escape", "menu", "Menu", show=False),
    ]
    
    CSS = """
    TestScreen {
        background: $background;
    }
    
    #main-container {
        width: 100%;
        height: 1fr;
        align: center middle;
    }
    
    #content-box {
        width: 100%;
        height: auto;
        padding: 1 0;
    }
    
    #title-row {
        width: 100%;
        height: 1;
        content-align: center middle;
        margin-bottom: 1;
    }
    
    #progress-row {
        width: 100%;
        height: 1;
        content-align: center middle;
        margin-bottom: 1;
    }
    
    #viewport {
        width: 100%;
        height: auto;
        min-height: 5;
        padding: 1 0;
    }
    
    .viewport-line {
        width: 100%;
        height: auto;
        min-height: 1;
    }
    
    #stats-line {
        width: 100%;
        height: 1;
        content-align: center middle;
        margin-top: 1;
    }
    """
    
    def __init__(self,
                 mode: str = "words",
                 mode_value: int = 50,
                 language: str = "english",
                 difficulty: str = "normal",
                 punctuation: bool = False,
                 numbers: bool = False,
                 on_complete: Optional[Callable] = None,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        
        self.mode = TestMode(mode) if isinstance(mode, str) else mode
        self.mode_value = mode_value
        self.language = language
        self.difficulty = Difficulty(difficulty) if isinstance(difficulty, str) else difficulty
        self.punctuation = punctuation
        self.numbers = numbers
        self.on_complete_callback = on_complete
        
        self.engine: Optional[TestEngine] = None
        self.timer: Optional[Timer] = None
        self._test_started = False
        
        # Viewport state
        self._line_groups: List[List[int]] = []   # word indices grouped by line
        self._viewport_top: int = 0                # index of the first visible line
        self._active_line: int = 0                 # index of line containing cursor
    
    @property
    def theme_colors(self):
        """Get current theme colors"""
        return {
            'accent': self.app.get_theme_color('accent'),
            'correct': self.app.get_theme_color('correct'),
            'incorrect': self.app.get_theme_color('incorrect'),
            'extra': self.app.get_theme_color('extra'),
            'cursor_fg': self.app.get_theme_color('background'),
            'cursor_bg': self.app.get_theme_color('cursor'),
            'current': self.app.get_theme_color('foreground'),
            'active': self.app.get_theme_color('foreground'), # or pending?
            'dim': self.app.get_theme_color('pending'),
            'border': self.app.get_theme_color('border'),
        }
    
    def compose(self):
        """Create child widgets"""
        yield Header(show_clock=True)
        
        with Container(id="main-container"):
            with Vertical(id="content-box"):
                yield Static(self._render_title(), id="title-row")
                yield Static(self._render_progress_bar(), id="progress-row")
                
                with Vertical(id="viewport"):
                    # 3 viewport lines: completed, active, upcoming
                    yield Static("", id="vp-line-0", classes="viewport-line")
                    yield Static("", id="vp-line-1", classes="viewport-line")
                    yield Static("", id="vp-line-2", classes="viewport-line")
                
                yield Static(self._render_stats(), id="stats-line")
        
        yield StatusBar(
            context="Waiting to start...",
            hints="tab restart  esc menu"
        )
    
    # ── Helpers ──
    
    def _compute_left_padding(self) -> int:
        """Calculate left padding to center the text block"""
        try:
            terminal_width = self.app.size.width
        except Exception:
            terminal_width = 80
        return max(0, (terminal_width - MAX_LINE_WIDTH) // 2)
    
    def _find_line_for_word(self, word_index: int) -> int:
        """Find which line a given word index belongs to"""
        for line_idx, indices in enumerate(self._line_groups):
            if word_index in indices:
                return line_idx
        return len(self._line_groups) - 1 if self._line_groups else 0
    
    # ── Title / Progress / Stats rendering ──
    
    def _render_title(self) -> Text:
        """Render minimal title in accent color"""
        colors = self.theme_colors
        text = Text(justify="center")
        text.append("🐧 ", Style(color="#89dceb"))
        text.append("tuxtype", Style(color=colors['accent']))
        return text
    
    def _render_progress_bar(self) -> Text:
        """Render Unicode block-character progress bar"""
        text = Text(justify="center")
        
        if not self.engine:
            filled = 0
        elif self.mode == TestMode.WORDS:
            total = len(self.engine.word_states)
            completed = self.engine.current_word_index
            ratio = completed / total if total > 0 else 0
            filled = int(ratio * BAR_WIDTH)
        elif self.mode == TestMode.TIME:
            elapsed = self.engine.elapsed_time
            time_limit = self.engine.time_limit or self.mode_value
            ratio = elapsed / time_limit if time_limit > 0 else 0
            filled = int(min(1.0, ratio) * BAR_WIDTH)
        else:
            filled = 0
        
        empty = BAR_WIDTH - filled
        colors = self.theme_colors
        if filled > 0:
            text.append(BAR_FILLED * filled, Style(color=colors['accent']))
        if empty > 0:
            text.append(BAR_EMPTY * empty, Style(color=colors['border']))
        
        return text
    
    def _render_stats(self) -> Text:
        """Render live WPM + accuracy stats"""
        text = Text(justify="center")
        
        if not self.engine or not self.engine.is_active:
            return text
        
        elapsed = self.engine.elapsed_time
        wpm = self.engine.stats.get_wpm(elapsed) if elapsed > 0 else 0
        accuracy = self.engine.stats.get_accuracy()
        
        colors = self.theme_colors
        
        text.append(f"{wpm:.0f}", Style(color="#89b4fa", bold=True))
        text.append(" wpm", Style(color=colors['dim']))
        text.append("   ", Style(color=colors['border']))
        acc_color = colors['correct'] if accuracy >= 95 else colors['incorrect']
        text.append(f"{accuracy:.1f}%", Style(color=acc_color, bold=True))
        text.append(" acc", Style(color=colors['dim']))
        
        return text
    
    # ── Core viewport rendering ──
    
    def _render_line(self, line_idx: int, is_active: bool, is_completed: bool) -> Text:
        """Render a single line of the viewport.
        
        Args:
            line_idx: Index into self._line_groups
            is_active: Whether this is the line being typed
            is_completed: Whether this line has already been typed
            
        Returns:
            Rich Text object with left padding for centered block alignment
        """
        padding = self._compute_left_padding()
        text = Text()
        
        # Add left padding to center the block
        if padding > 0:
            text.append(" " * padding)
        
        if line_idx < 0 or line_idx >= len(self._line_groups):
            return text
        
        colors = self.theme_colors
        word_indices = self._line_groups[line_idx]
        
        for pos, word_idx in enumerate(word_indices):
            if word_idx >= len(self.engine.word_states):
                break
                
            word_state = self.engine.word_states[word_idx]
            is_current_word = (word_idx == self.engine.current_word_index)
            chars = word_state.get_display_chars()
            
            if is_completed:
                # Completed line: all dimmed
                for char, state in chars:
                    if state == 'correct':
                        style = Style(color=colors['correct'], dim=True)
                    elif state == 'incorrect':
                        style = Style(color=colors['incorrect'], dim=True)
                    else:
                        style = Style(color=colors['dim'])
                    text.append(char, style)
            elif is_active:
                # Active line: full styling with cursor
                for i, (char, state) in enumerate(chars):
                    if state == 'correct':
                        style = Style(color=colors['correct'])
                    elif state == 'incorrect':
                        style = Style(color=colors['cursor_fg'], bgcolor=colors['incorrect'])
                    elif state == 'extra':
                        style = Style(color=colors['extra'], strike=True)
                    elif is_current_word and i == self.engine.current_char_index:
                        # Block cursor
                        style = Style(color=colors['cursor_fg'], bgcolor=colors['cursor_bg'], bold=True)
                    elif is_current_word:
                        style = Style(color=colors['current'], bold=True)
                    else:
                        # Other words on active line
                        style = Style(color=colors['active'])
                    text.append(char, style)
                
                # Cursor at space position (end of word)
                if is_current_word and self.engine.current_char_index >= len(word_state.word):
                    text.append(" ", Style(color=colors['cursor_fg'], bgcolor=colors['cursor_bg']))
                else:
                    text.append(" ")
                continue  # skip the default space append below
            else:
                # Upcoming line: all dark gray
                for char, state in chars:
                    text.append(char, Style(color=colors['dim']))
            
            # Add space between words
            text.append(" ")
        
        return text
    
    def _update_viewport(self) -> None:
        """Update the 3-line viewport display"""
        if not self.engine or not self._line_groups:
            return
        
        # Find which line the current word is on
        current_word = self.engine.current_word_index
        new_active = self._find_line_for_word(current_word)
        
        # Scroll: when active line changes, update viewport top
        if new_active != self._active_line:
            self._active_line = new_active
        
        # Position viewport: active line in the middle slot (index 1)
        # If on first line, show it at slot 0 with nothing above
        if self._active_line == 0:
            self._viewport_top = 0
        else:
            self._viewport_top = self._active_line - 1
        
        # Render the 3 viewport lines
        for slot in range(VIEWPORT_LINES):
            line_idx = self._viewport_top + slot
            widget_id = f"#vp-line-{slot}"
            
            try:
                widget = self.query_one(widget_id, Static)
            except Exception:
                continue
            
            if line_idx < 0 or line_idx >= len(self._line_groups):
                widget.update(Text(""))
                continue
            
            is_active = (line_idx == self._active_line)
            is_completed = (line_idx < self._active_line)
            
            rendered = self._render_line(line_idx, is_active, is_completed)
            widget.update(rendered)
    
    # ── Engine init / lifecycle ──
    
    def on_mount(self) -> None:
        """Initialize"""
        self._init_engine()
        self._rebuild_lines()
        self._update_viewport()
        self.timer = self.set_interval(0.1, self._on_timer)
    
    def on_unmount(self) -> None:
        """Cleanup"""
        if self.timer:
            self.timer.stop()
    
    def on_resize(self, event) -> None:
        """Recalculate padding on terminal resize"""
        self._update_viewport()
    
    def _init_engine(self) -> None:
        """Initialize test engine"""
        self.engine = TestEngine(
            mode=self.mode,
            mode_value=self.mode_value,
            language=self.language,
            difficulty=self.difficulty,
            punctuation=self.punctuation,
            numbers=self.numbers,
            on_update=self._on_engine_update,
            on_complete=self._on_test_complete
        )
        self._test_started = False
    
    def _rebuild_lines(self) -> None:
        """Re-wrap words into lines based on MAX_LINE_WIDTH"""
        if not self.engine:
            return
        self._line_groups = wrap_words_to_lines(self.engine.word_states, MAX_LINE_WIDTH)
        self._active_line = 0
        self._viewport_top = 0
    
    # ── Update callbacks ──
    
    def _update_display(self) -> None:
        """Full display update: viewport + progress + stats"""
        self._update_viewport()
        self._update_progress()
        self._update_stats()
    
    def _update_progress(self) -> None:
        """Update Unicode progress bar"""
        try:
            self.query_one("#progress-row", Static).update(self._render_progress_bar())
        except Exception:
            pass
    
    def _update_stats(self) -> None:
        """Update live stats display"""
        try:
            self.query_one("#stats-line", Static).update(self._render_stats())
        except Exception:
            pass
    
    def _on_timer(self) -> None:
        """Timer callback"""
        if not self.engine or not self.engine.is_active:
            return
        if self.engine.check_time_limit():
            return
        self._update_progress()
        self._update_stats()
    
    def _on_engine_update(self) -> None:
        """Engine update callback — called on every keypress"""
        if not self._test_started and self.engine and self.engine.is_active:
            self._test_started = True
            try:
                status_bar = self.query_one(StatusBar)
                status_bar.set_context("Typing...")
            except Exception:
                pass
        self._update_display()
    
    def _on_test_complete(self, results: dict) -> None:
        """Test complete"""
        if self.timer:
            self.timer.stop()
        if self.on_complete_callback:
            self.on_complete_callback(results)
        self.app.push_screen("results", results)
    
    # ── Key handling ──
    
    def on_key(self, event: events.Key) -> None:
        """Handle key press"""
        if not self.engine:
            return
        
        key = event.key
        
        if key == "tab" or key == "escape":
            return
        elif key == "space":
            self.engine.process_key("space")
        elif key == "backspace":
            self.engine.process_key("backspace")
        elif key == "ctrl+backspace":
            while self.engine.current_word and len(self.engine.current_word.typed) > 0:
                self.engine.process_key("backspace")
        elif len(event.character or "") == 1:
            self.engine.process_key(event.character)
            event.prevent_default()
            event.stop()
        else:
            return
        
        event.prevent_default()
        event.stop()
    
    # ── Actions ──
    
    def action_restart(self) -> None:
        """Restart test"""
        if self.engine:
            self.engine.reset()
        self._rebuild_lines()
        self._test_started = False
        try:
            status_bar = self.query_one(StatusBar)
            status_bar.set_context("Waiting to start...")
        except Exception:
            pass
        self._update_display()
    
    def action_menu(self) -> None:
        """Return to menu"""
        if self.timer:
            self.timer.stop()
        self.app.pop_screen()
