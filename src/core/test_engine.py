"""Core typing test engine"""
import time
import logging
from typing import List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum

from .stats_calculator import StatsCalculator, LiveStats, CharacterStats
from .word_generator import WordGenerator

logger = logging.getLogger(__name__)

# Constants
MINIMUM_ACCURACY_FOR_PB = 95.0
TIME_MODE_WORD_BUFFER = 500
TIME_MODE_WORD_BATCH = 100


class TestMode(Enum):
    """Test mode types"""
    WORDS = "words"
    TIME = "time"
    QUOTE = "quote"
    CUSTOM = "custom"


class Difficulty(Enum):
    """Difficulty levels"""
    NORMAL = "normal"
    EXPERT = "expert"
    MASTER = "master"


class TestStatus(Enum):
    """Current test status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WordState:
    """State of a single word during typing"""
    word: str
    typed: str = ""
    char_states: List[Tuple[str, str, bool]] = field(default_factory=list)
    completed: bool = False
    correct: bool = True
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    @property
    def wpm(self) -> float:
        """Calculate WPM for this word"""
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            if duration > 0:
                return StatsCalculator.calculate_wpm(len(self.word), duration)
        return 0.0
    
    def get_display_chars(self) -> List[Tuple[str, str]]:
        """Get characters with their display state
        
        Returns:
            List of (character, state) where state is 'correct', 'incorrect', 'extra', 'pending'
        """
        result = []
        word_len = len(self.word)
        typed_len = len(self.typed)
        
        for i in range(max(word_len, typed_len)):
            if i < word_len and i < typed_len:
                # Both expected and typed exist
                if self.typed[i] == self.word[i]:
                    result.append((self.word[i], 'correct'))
                else:
                    result.append((self.word[i], 'incorrect'))
            elif i < word_len:
                # Expected exists but not typed (pending)
                result.append((self.word[i], 'pending'))
            else:
                # Extra typed characters
                result.append((self.typed[i], 'extra'))
        
        return result


class TestEngine:
    """Core typing test engine managing test state and input processing"""
    
    def __init__(self, 
                 mode: TestMode = TestMode.WORDS,
                 mode_value: int = 50,
                 language: str = "english",
                 difficulty: Difficulty = Difficulty.NORMAL,
                 punctuation: bool = False,
                 numbers: bool = False,
                 on_update: Optional[Callable] = None,
                 on_complete: Optional[Callable] = None):
        """Initialize test engine
        
        Args:
            mode: Test mode (words, time, quote)
            mode_value: Word count or time in seconds
            language: Language for word generation
            difficulty: Difficulty level
            punctuation: Include punctuation
            numbers: Include numbers
            on_update: Callback for state updates
            on_complete: Callback when test completes
        """
        self.mode = mode
        self.mode_value = mode_value
        self.language = language
        self.difficulty = difficulty
        self.punctuation = punctuation
        self.numbers = numbers
        self.on_update = on_update
        self.on_complete = on_complete
        
        self.word_generator = WordGenerator()
        self.stats = LiveStats()
        
        # Test state
        self.words: List[str] = []
        self.word_states: List[WordState] = []
        self.current_word_index: int = 0
        self.current_char_index: int = 0
        self.status: TestStatus = TestStatus.NOT_STARTED
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.time_limit: Optional[float] = None
        
        # Initialize test
        self.reset()
    
    def reset(self) -> None:
        """Reset test to initial state with new words"""
        self.stats.reset()
        
        # Generate words based on mode
        if self.mode == TestMode.WORDS:
            self.words = self.word_generator.generate_words(
                count=self.mode_value,
                language=self.language,
                punctuation=self.punctuation,
                numbers=self.numbers
            )
            self.time_limit = None
        elif self.mode == TestMode.TIME:
            # Generate more words than needed for time mode
            self.words = self.word_generator.generate_words(
                count=TIME_MODE_WORD_BUFFER,  # Should be enough for any time limit
                language=self.language,
                punctuation=self.punctuation,
                numbers=self.numbers
            )
            self.time_limit = self.mode_value
        elif self.mode == TestMode.QUOTE:
            quote = self.word_generator.get_random_quote()
            if quote:
                self.words = self.word_generator.get_quote_words(quote)
            else:
                self.words = ["No", "quotes", "available"]
            self.time_limit = None
        else:
            self.words = self.word_generator.generate_words(count=50)
            self.time_limit = None
        
        # Initialize word states
        self.word_states = [WordState(word=w) for w in self.words]
        self.current_word_index = 0
        self.current_char_index = 0
        self.status = TestStatus.NOT_STARTED
        self.start_time = None
        self.end_time = None
    
    @property
    def current_word(self) -> Optional[WordState]:
        """Get current word state"""
        if 0 <= self.current_word_index < len(self.word_states):
            return self.word_states[self.current_word_index]
        return None
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds"""
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time
    
    @property
    def remaining_time(self) -> Optional[float]:
        """Get remaining time for time mode"""
        if self.time_limit is None:
            return None
        remaining = self.time_limit - self.elapsed_time
        return max(0, remaining)
    
    @property
    def progress(self) -> float:
        """Get test progress as percentage"""
        if self.mode == TestMode.TIME:
            if self.time_limit:
                return min(100, (self.elapsed_time / self.time_limit) * 100)
        else:
            if len(self.word_states) > 0:
                return (self.current_word_index / len(self.word_states)) * 100
        return 0
    
    @property
    def is_active(self) -> bool:
        """Check if test is in progress"""
        return self.status == TestStatus.IN_PROGRESS
    
    @property
    def is_complete(self) -> bool:
        """Check if test is complete"""
        return self.status in (TestStatus.COMPLETED, TestStatus.FAILED)
    
    def start(self) -> None:
        """Start the test"""
        if self.status == TestStatus.NOT_STARTED:
            self.start_time = time.time()
            self.status = TestStatus.IN_PROGRESS
            if self.current_word:
                self.current_word.start_time = self.start_time
    
    def process_key(self, key: str) -> dict:
        """Process a key press
        
        Args:
            key: The key pressed (single character, 'backspace', 'space', etc.)
            
        Returns:
            dict with update information
        """
        # Auto-start on first keypress
        if self.status == TestStatus.NOT_STARTED and key not in ('backspace', 'escape', 'tab'):
            self.start()
        
        if not self.is_active:
            return {'action': 'ignored', 'reason': 'test not active'}
        
        # Check time limit
        if self.time_limit and self.elapsed_time >= self.time_limit:
            return self._complete_test()
        
        word = self.current_word
        if word is None:
            return self._complete_test()
        
        # Handle different key types
        if key == 'space':
            return self._submit_word()
        elif key == 'backspace':
            return self._handle_backspace()
        elif len(key) == 1:  # Single character
            return self._handle_char(key)
        
        return {'action': 'ignored', 'reason': 'unknown key'}
    
    def _handle_char(self, char: str) -> dict:
        """Handle a character input"""
        word = self.current_word
        if word is None:
            return {'action': 'ignored'}
        
        expected_char = word.word[self.current_char_index] if self.current_char_index < len(word.word) else None
        
        is_correct = (char == expected_char)
        is_extra = (self.current_char_index >= len(word.word))
        
        # Add to typed text
        word.typed += char
        word.char_states.append((expected_char or '', char, is_correct))
        
        # Update stats
        if is_extra:
            self.stats.add_extra_char()
            word.correct = False
        elif is_correct:
            self.stats.add_correct_char()
        else:
            self.stats.add_incorrect_char()
            word.correct = False
            
            # Check difficulty
            if self.difficulty == Difficulty.MASTER:
                return self._fail_test("Incorrect character in Master mode")
        
        self.current_char_index += 1
        
        # Record WPM periodically
        if self.stats.total_chars % 20 == 0:
            self.stats.record_wpm(self.elapsed_time, self.stats.get_wpm(self.elapsed_time))
        
        if self.on_update:
            self.on_update()
        
        return {
            'action': 'char_added',
            'char': char,
            'correct': is_correct,
            'extra': is_extra
        }
    
    def _handle_backspace(self) -> dict:
        """Handle backspace key"""
        word = self.current_word
        if word is None or len(word.typed) == 0:
            return {'action': 'ignored', 'reason': 'nothing to delete'}
        
        # Get the character being deleted
        deleted = word.typed[-1]
        word.typed = word.typed[:-1]
        
        # Update stats
        if word.char_states:
            _, typed_char, was_correct = word.char_states.pop()
            if self.current_char_index > len(word.word):
                self.stats.extra_chars = max(0, self.stats.extra_chars - 1)
            elif was_correct:
                self.stats.correct_chars = max(0, self.stats.correct_chars - 1)
            else:
                self.stats.incorrect_chars = max(0, self.stats.incorrect_chars - 1)
        
        self.current_char_index = max(0, self.current_char_index - 1)
        
        # Re-check if word is correct after backspace
        word.correct = all(
            typed == exp for exp, typed, _ in word.char_states
        ) if word.char_states else True
        
        if self.on_update:
            self.on_update()
        
        return {'action': 'char_deleted', 'char': deleted}
    
    def _submit_word(self) -> dict:
        """Submit current word (space pressed)"""
        word = self.current_word
        if word is None:
            return {'action': 'ignored'}
        
        # Prevent skipping words — must type at least one character
        if len(word.typed) == 0:
            return {'action': 'ignored', 'reason': 'must type before advancing'}
        
        # Mark word as completed
        word.completed = True
        word.end_time = time.time()
        
        # Calculate missed characters
        if len(word.typed) < len(word.word):
            missed = len(word.word) - len(word.typed)
            self.stats.add_missed_chars(missed)
            word.correct = False
        
        # Record word WPM
        self.stats.complete_word(word.wpm)
        
        # Check expert mode
        if self.difficulty == Difficulty.EXPERT and not word.correct:
            return self._fail_test("Incorrect word in Expert mode")
        
        # Move to next word
        self.current_word_index += 1
        self.current_char_index = 0
        
        # Start timing for next word
        if self.current_word:
            self.current_word.start_time = time.time()
        
        # Check if test is complete (word mode)
        if self.mode == TestMode.WORDS and self.current_word_index >= len(self.word_states):
            return self._complete_test()
        
        # Check if we need more words (time mode)
        if self.mode == TestMode.TIME and self.current_word_index >= len(self.word_states) - 10:
            # Generate more words
            try:
                new_words = self.word_generator.generate_words(
                    count=TIME_MODE_WORD_BATCH,
                    language=self.language,
                    punctuation=self.punctuation,
                    numbers=self.numbers
                )
                for w in new_words:
                    self.words.append(w)
                    self.word_states.append(WordState(word=w))
            except Exception as e:
                logger.error(f"Failed to generate more words: {e}")
                # Continue with existing words
        
        if self.on_update:
            self.on_update()
        
        return {
            'action': 'word_submitted',
            'word': word.word,
            'correct': word.correct,
            'wpm': word.wpm
        }
    
    def _complete_test(self) -> dict:
        """Complete the test successfully"""
        self.end_time = time.time()
        self.status = TestStatus.COMPLETED
        
        # Final WPM record
        self.stats.record_wpm(self.elapsed_time, self.stats.get_wpm(self.elapsed_time))
        
        if self.on_complete:
            self.on_complete(self.get_results())
        
        return {'action': 'test_completed', 'results': self.get_results()}
    
    def _fail_test(self, reason: str) -> dict:
        """Fail the test"""
        self.end_time = time.time()
        self.status = TestStatus.FAILED
        
        if self.on_complete:
            self.on_complete(self.get_results())
        
        return {'action': 'test_failed', 'reason': reason, 'results': self.get_results()}
    
    def check_time_limit(self) -> bool:
        """Check if time limit has been reached (for time mode)
        
        Returns:
            True if test should end
        """
        if self.time_limit and self.is_active:
            if self.elapsed_time >= self.time_limit:
                self._complete_test()
                return True
        return False
    
    def get_results(self) -> dict:
        """Get final test results"""
        elapsed = self.elapsed_time
        
        return {
            'mode': self.mode.value,
            'mode_value': self.mode_value,
            'language': self.language,
            'difficulty': self.difficulty.value,
            'wpm': self.stats.get_wpm(elapsed),
            'raw_wpm': self.stats.get_raw_wpm(elapsed),
            'accuracy': self.stats.get_accuracy(),
            'consistency': self.stats.get_consistency(),
            'duration': elapsed,
            'characters_correct': self.stats.correct_chars,
            'characters_incorrect': self.stats.incorrect_chars,
            'characters_extra': self.stats.extra_chars,
            'characters_missed': self.stats.missed_chars,
            'words_completed': self.current_word_index,
            'total_words': len(self.word_states),
            'punctuation': self.punctuation,
            'numbers': self.numbers,
            'status': self.status.value,
            'wpm_history': self.stats.wpm_history,
            'word_speeds': self.stats.word_speeds
        }
    
    def get_display_words(self, before: int = 2, after: int = 10) -> List[Tuple[WordState, bool]]:
        """Get words for display
        
        Args:
            before: Number of completed words to show before current
            after: Number of pending words to show after current
            
        Returns:
            List of (WordState, is_current) tuples
        """
        start = max(0, self.current_word_index - before)
        end = min(len(self.word_states), self.current_word_index + after + 1)
        
        result = []
        for i in range(start, end):
            is_current = (i == self.current_word_index)
            result.append((self.word_states[i], is_current))
        
        return result
