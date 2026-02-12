"""ASCII performance graph widget"""
from textual.widget import Widget
from rich.text import Text
from rich.style import Style
from rich.console import RenderableType
from typing import List, Tuple


class PerformanceGraph(Widget):
    """Widget for displaying ASCII performance graphs"""
    
    DEFAULT_CSS = """
    PerformanceGraph {
        width: 100%;
        height: 10;
        padding: 0 1;
    }
    """
    
    def __init__(self, 
                 data: List[Tuple[float, float]] = None,
                 width: int = 50,
                 height: int = 8,
                 title: str = "WPM over time",
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self._data = data or []
        self._width = width
        self._height = height
        self._title = title
        
        # Graph characters
        self._chars = {
            'vertical': '│',
            'horizontal': '─',
            'corner_tl': '┌',
            'corner_tr': '┐',
            'corner_bl': '└',
            'corner_br': '┘',
            'point': '●',
            'line_up': '╱',
            'line_down': '╲',
            'dot': '·',
        }
    
    def set_data(self, data: List[Tuple[float, float]]) -> None:
        """Set graph data
        
        Args:
            data: List of (time, value) tuples
        """
        self._data = data
        self.refresh()
    
    def render(self) -> RenderableType:
        """Render the graph"""
        if not self._data:
            return Text("No data to display", style=Style(color='#6c7086'))
        
        return self._render_line_graph()
    
    def _render_line_graph(self) -> Text:
        """Render a simple ASCII line graph"""
        text = Text()
        
        # Get data range
        values = [v for _, v in self._data]
        times = [t for t, _ in self._data]
        
        if not values:
            return Text("No data")
        
        min_val = 0
        max_val = max(values) * 1.1  # Add 10% headroom
        if max_val == 0:
            max_val = 100
        
        min_time = min(times) if times else 0
        max_time = max(times) if times else 60
        
        # Calculate dimensions
        graph_width = min(self._width, 60)
        graph_height = min(self._height, 8)
        
        # Create grid
        grid = [[' ' for _ in range(graph_width + 5)] for _ in range(graph_height + 1)]
        
        # Add Y-axis labels
        for row in range(graph_height + 1):
            val = max_val - (row * max_val / graph_height)
            label = f"{int(val):3d} "
            for i, c in enumerate(label):
                if i < 4:
                    grid[row][i] = c
        
        # Add axis
        for row in range(graph_height):
            grid[row][4] = '│'
        
        for col in range(4, graph_width + 5):
            grid[graph_height][col] = '─'
        
        grid[graph_height][4] = '└'
        
        # Plot data points
        if len(self._data) > 0:
            # Sample data to fit width
            step = max(1, len(self._data) // graph_width)
            sampled = self._data[::step][:graph_width]
            
            prev_row = None
            for i, (t, v) in enumerate(sampled):
                col = 5 + i
                if col >= graph_width + 5:
                    break
                
                # Calculate row (inverted - higher values at top)
                row = int((max_val - v) / max_val * graph_height)
                row = max(0, min(graph_height - 1, row))
                
                # Draw point
                grid[row][col] = '●'
                
                # Draw connecting line
                if prev_row is not None and prev_row != row:
                    # Simple vertical connection
                    start_row, end_row = sorted([prev_row, row])
                    for r in range(start_row + 1, end_row):
                        if grid[r][col - 1] == ' ':
                            grid[r][col - 1] = '·'
                
                prev_row = row
        
        # Add X-axis labels
        time_labels_row = ['0s', '', f'{int(max_time)}s']
        
        # Build output
        text.append(f"  {self._title}\n", Style(color='#cdd6f4'))
        
        for row in range(graph_height + 1):
            line = ''.join(grid[row])
            
            # Color the data points
            styled_line = Text()
            for char in line:
                if char == '●':
                    styled_line.append(char, Style(color='#89b4fa'))
                elif char == '·':
                    styled_line.append(char, Style(color='#45475a'))
                elif char in '│─└':
                    styled_line.append(char, Style(color='#45475a'))
                elif char.isdigit():
                    styled_line.append(char, Style(color='#6c7086'))
                else:
                    styled_line.append(char)
            
            text.append(styled_line)
            text.append('\n')
        
        # X-axis time labels
        text.append(f"     0s", Style(color='#6c7086'))
        padding = graph_width - 10
        text.append(' ' * max(0, padding))
        text.append(f"{int(max_time)}s\n", Style(color='#6c7086'))
        
        return text


class SimpleBarGraph(Widget):
    """Simple horizontal bar graph for stats comparison"""
    
    DEFAULT_CSS = """
    SimpleBarGraph {
        width: 100%;
        height: auto;
        padding: 0 1;
    }
    """
    
    def __init__(self, 
                 data: dict = None,
                 max_value: float = 100,
                 bar_width: int = 30,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self._data = data or {}
        self._max_value = max_value
        self._bar_width = bar_width
    
    def set_data(self, data: dict, max_value: float = None) -> None:
        """Set bar graph data
        
        Args:
            data: Dict of {label: value}
            max_value: Maximum value for scaling
        """
        self._data = data
        if max_value:
            self._max_value = max_value
        self.refresh()
    
    def render(self) -> RenderableType:
        """Render the bar graph"""
        text = Text()
        
        if not self._data:
            return text
        
        colors = ['#89b4fa', '#a6e3a1', '#f9e2af', '#fab387', '#f38ba8']
        
        for i, (label, value) in enumerate(self._data.items()):
            # Label
            text.append(f"{label:12} ", Style(color='#6c7086'))
            
            # Bar
            bar_len = int((value / self._max_value) * self._bar_width)
            bar_len = max(0, min(self._bar_width, bar_len))
            
            color = colors[i % len(colors)]
            text.append('█' * bar_len, Style(color=color))
            text.append('░' * (self._bar_width - bar_len), Style(color='#45475a'))
            
            # Value
            text.append(f" {value:.1f}\n", Style(color='#cdd6f4'))
        
        return text
