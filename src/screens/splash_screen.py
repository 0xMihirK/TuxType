"""Splash screen with app branding"""
from textual.screen import Screen
from textual.widgets import Static
from textual.containers import Container
from rich.text import Text
from rich.style import Style
from rich.align import Align


class SplashScreen(Screen):
    """Splash screen shown on app startup"""
    
    CSS = """
    SplashScreen {
        background: $background;
        align: center middle;
    }
    
    #splash-container {
        width: 100%;
        height: 100%;
        align: center middle;
    }
    
    #splash-logo {
        text-align: center;
        padding: 2;
    }
    
    #splash-subtitle {
        text-align: center;
        color: #6c7086;
        padding: 1;
    }
    """
    
    def compose(self):
        """Create splash screen layout"""
        with Container(id="splash-container"):
            yield Static(self._render_logo(), id="splash-logo")
            yield Static(self._render_subtitle(), id="splash-subtitle")
    
    def _render_logo(self) -> Text:
        """Render the TuxType logo in ASCII art style"""
        text = Text()
        
        # ASCII art style logo — TuxType
        logo_lines = [
            "████████╗██╗   ██╗██╗  ██╗████████╗██╗   ██╗██████╗ ███████╗",
            "╚══██╔══╝██║   ██║╚██╗██╔╝╚══██╔══╝╚██╗ ██╔╝██╔══██╗██╔════╝",
            "   ██║   ██║   ██║ ╚███╔╝    ██║    ╚████╔╝ ██████╔╝█████╗  ",
            "   ██║   ██║   ██║ ██╔██╗    ██║     ╚██╔╝  ██╔═══╝ ██╔══╝  ",
            "   ██║   ╚██████╔╝██╔╝ ██╗   ██║      ██║   ██║     ███████╗",
            "   ╚═╝    ╚═════╝ ╚═╝  ╚═╝   ╚═╝      ╚═╝   ╚═╝     ╚══════╝",
        ]
        
        # Gradient colors from cyan to purple
        colors = ["#89dceb", "#89b4fa", "#b4befe", "#cba6f7", "#f5c2e7", "#f38ba8"]
        
        for i, line in enumerate(logo_lines):
            color = colors[i % len(colors)]
            text.append(line, Style(color=color, bold=True))
            text.append("\n")
        
        return text
    
    def _render_subtitle(self) -> Text:
        """Render subtitle"""
        text = Text()
        text.append("\n🐧 ", Style(color="#89dceb"))
        text.append("Terminal Typing Test", Style(color="#cdd6f4", italic=True))
        text.append(" 🐧", Style(color="#89dceb"))
        text.append("\n\n")
        text.append("Loading...", Style(color="#6c7086"))
        return text
    
    def on_mount(self) -> None:
        """Set timer toclose splash after 2 seconds"""
        self.set_timer(2.0, self._close_splash)
    
    def _close_splash(self) -> None:
        """Close splash and show main menu"""
        self.app.pop_screen()
        self.app.push_screen("menu")
