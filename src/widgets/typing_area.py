"""Typing area widget for displaying and tracking text"""
from textual.widget import Widget
from textual.reactive import reactive
from textual.message import Message
from rich.text import Text
from rich.style import Style
from typing import List, Tuple, Optional


class TypingArea(Widget):
    """Widget for displaying typing test text with real-time feedback"""
    
    DEFAULT_CSS = """
    TypingArea {
        width: 100%;
        height: auto;
        min-height: 6;
        padding: 1 2;
        background: $surface;
    }
    """
    
    # Reactive properties
    words: reactive[List[str]] = reactive(list)
    typed_chars: reactive[List[List[Tuple[str, str]]]] = reactive(list)
    current_word_index: reactive[int] = reactive(0)
    current_char_index: reactive[int] = reactive(0)
    
    class CharTyped(Message):
        """Message sent when a character is typed"""
        def __init__(self, char: str) -> None:
            self.char = char
            super().__init__()
    
    class WordCompleted(Message):
        """Message sent when a word is completed"""
        def __init__(self, word: str, typed: str, correct: bool) -> None:
            self.word = word
            self.typed = typed
            self.correct = correct
            super().__init__()
    
    def __init__(self, 
                 words: Optional[List[str]] = None,
                 theme: str = "dark",
                 **kwargs) -> None:
        super().__init__(**kwargs)
        self._words = words or []
        self._typed: List[str] = []  # Typed text per word
        self._char_states: List[List[Tuple[str, bool]]] = []  # (char, correct) per word
        self._current_word_idx = 0
        self._current_char_idx = 0
        self._theme = theme
        
        # Color scheme
        self._colors = {
            'correct': '#a6e3a1',
            'incorrect': '#f38ba8',
            'extra': '#fab387',
            'pending': '#6c7086',
            'current': '#cdd6f4',
            'cursor': '#f5c2e7',
        }
    
    def set_words(self, words: List[str]) -> None:
        """Set the words to type"""
        self._words = words
        self._typed = ["" for _ in words]
        self._char_states = [[] for _ in words]
        self._current_word_idx = 0
        self._current_char_idx = 0
        self.refresh()
    
    def reset(self) -> None:
        """Reset typing state"""
        self._typed = ["" for _ in self._words]
        self._char_states = [[] for _ in self._words]
        self._current_word_idx = 0
        self._current_char_idx = 0
        self.refresh()
    
    def add_char(self, char: str) -> Tuple[bool, bool]:
        """Add a typed character
        
        Returns:
            Tuple of (is_correct, is_extra)
        """
        if self._current_word_idx >= len(self._words):
            return False, False
        
        word = self._words[self._current_word_idx]
        
        # Check if this is an extra character
        is_extra = self._current_char_idx >= len(word)
        
        # Check if character is correct
        if is_extra:
            is_correct = False
        else:
            expected = word[self._current_char_idx]
            is_correct = (char == expected)
        
        # Update typed text
        self._typed[self._current_word_idx] += char
        self._char_states[self._current_word_idx].append((char, is_correct))
        self._current_char_idx += 1
        
        self.refresh()
        return is_correct, is_extra
    
    def delete_char(self) -> bool:
        """Delete last character
        
        Returns:
            True if character was deleted
        """
        if self._current_word_idx >= len(self._words):
            return False
        
        typed = self._typed[self._current_word_idx]
        if len(typed) == 0:
            return False
        
        self._typed[self._current_word_idx] = typed[:-1]
        if self._char_states[self._current_word_idx]:
            self._char_states[self._current_word_idx].pop()
        self._current_char_idx = max(0, self._current_char_idx - 1)
        
        self.refresh()
        return True
    
    def submit_word(self) -> Tuple[str, str, bool]:
        """Submit current word and move to next
        
        Returns:
            Tuple of (expected_word, typed_word, was_correct)
        """
        if self._current_word_idx >= len(self._words):
            return "", "", False
        
        word = self._words[self._current_word_idx]
        typed = self._typed[self._current_word_idx]
        correct = (word == typed)
        
        self._current_word_idx += 1
        self._current_char_idx = 0
        
        self.refresh()
        return word, typed, correct
    
    @property
    def current_word(self) -> str:
        """Get current word"""
        if self._current_word_idx < len(self._words):
            return self._words[self._current_word_idx]
        return ""
    
    @property
    def current_typed(self) -> str:
        """Get currently typed text for current word"""
        if self._current_word_idx < len(self._typed):
            return self._typed[self._current_word_idx]
        return ""
    
    @property
    def is_complete(self) -> bool:
        """Check if all words have been typed"""
        return self._current_word_idx >= len(self._words)
    
    def render(self) -> Text:
        """Render the typing area"""
        text = Text()
        
        # Calculate how many words to show (adjust based on width)
        show_before = 2  # Completed words to show
        show_after = 15  # Pending words to show
        
        start_idx = max(0, self._current_word_idx - show_before)
        end_idx = min(len(self._words), self._current_word_idx + show_after + 1)
        
        for word_idx in range(start_idx, end_idx):
            word = self._words[word_idx]
            typed = self._typed[word_idx] if word_idx < len(self._typed) else ""
            char_states = self._char_states[word_idx] if word_idx < len(self._char_states) else []
            
            is_current = (word_idx == self._current_word_idx)
            is_completed = (word_idx < self._current_word_idx)
            
            # Render each character
            self._render_word(text, word, typed, char_states, is_current, is_completed)
            
            # Add space between words
            if word_idx < end_idx - 1:
                text.append(" ")
        
        return text
    
    def _render_word(self, text: Text, word: str, typed: str, 
                     char_states: List[Tuple[str, bool]], 
                     is_current: bool, is_completed: bool) -> None:
        """Render a single word with character coloring"""
        word_len = len(word)
        typed_len = len(typed)
        
        for i in range(max(word_len, typed_len)):
            if i < word_len and i < typed_len:
                # Both expected and typed
                typed_char, is_correct = char_states[i] if i < len(char_states) else (typed[i], typed[i] == word[i])
                
                if is_correct:
                    style = Style(color=self._colors['correct'])
                else:
                    style = Style(color=self._colors['incorrect'], strike=False)
                    # Show the expected character (crossed out) for incorrect
                text.append(word[i], style)
                
            elif i < word_len:
                # Expected but not typed yet
                if is_current and i == self._current_char_idx:
                    # Cursor position
                    style = Style(color=self._colors['current'], underline=True)
                else:
                    style = Style(color=self._colors['pending'])
                text.append(word[i], style)
                
            else:
                # Extra typed characters
                style = Style(color=self._colors['extra'])
                if i < typed_len:
                    text.append(typed[i], style)
        
        # Add cursor at end if we're at end of current word
        if is_current and self._current_char_idx >= word_len:
            text.append("▏", Style(color=self._colors['cursor']))
