"""Custom status bar widget for TuxType"""
from textual.widgets import Static
from textual.containers import Horizontal
from textual.widget import Widget
from textual.reactive import reactive
from rich.text import Text
from rich.style import Style


class StatusBar(Static):
    """Full-width status bar anchored to the bottom of the screen.
    
    Provides a visually distinct footer with app branding and contextual hints.
    """
    
    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        width: 100%;
        height: 1;
        background: #181825;
        color: #6c7086;
        padding: 0 2;
    }
    """
    
    context: reactive[str] = reactive("")
    hints: reactive[str] = reactive("")
    
    def __init__(self, context: str = "", hints: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self.context = context
        self.hints = hints
    
    def render(self) -> Text:
        """Render the status bar content"""
        text = Text()
        
        # Left: app branding
        text.append(" 🐧 ", Style(color="#89dceb"))
        text.append("TuxType", Style(color="#585b70"))
        
        # Center: context info
        if self.context:
            text.append("  │  ", Style(color="#313244"))
            text.append(self.context, Style(color="#6c7086"))
        
        # Right side: key hints — pad to fill width
        if self.hints:
            # Calculate remaining space
            current_len = len(text.plain)
            try:
                width = self.size.width
            except Exception:
                width = 80
            remaining = max(2, width - current_len - len(self.hints) - 1)
            text.append(" " * remaining)
            text.append(self.hints, Style(color="#585b70"))
        
        return text
    
    def set_context(self, context: str) -> None:
        """Update the context text"""
        self.context = context
        self.refresh()
    
    def set_hints(self, hints: str) -> None:
        """Update the hints text"""
        self.hints = hints
        self.refresh()
