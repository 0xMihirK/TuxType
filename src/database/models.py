"""Data models for typing test application"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Tuple


@dataclass
class TestResult:
    """Represents a completed typing test result"""
    id: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)
    mode: str = "words"  # 'words', 'time', 'quote', 'custom'
    mode_value: int = 50  # word count or time in seconds
    language: str = "english"
    difficulty: str = "normal"  # 'normal', 'expert', 'master'
    wpm: float = 0.0
    raw_wpm: float = 0.0
    accuracy: float = 0.0
    consistency: float = 0.0
    characters_correct: int = 0
    characters_incorrect: int = 0
    characters_extra: int = 0
    characters_missed: int = 0
    test_duration: float = 0.0
    punctuation: bool = False
    numbers: bool = False
    is_personal_best: bool = False
    quote_id: Optional[int] = None
    
    @property
    def char_stats(self) -> str:
        """Format character stats as string"""
        return f"{self.characters_correct}/{self.characters_incorrect}/{self.characters_extra}/{self.characters_missed}"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for database storage"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'mode': self.mode,
            'mode_value': self.mode_value,
            'language': self.language,
            'difficulty': self.difficulty,
            'wpm': self.wpm,
            'raw_wpm': self.raw_wpm,
            'accuracy': self.accuracy,
            'consistency': self.consistency,
            'characters_correct': self.characters_correct,
            'characters_incorrect': self.characters_incorrect,
            'characters_extra': self.characters_extra,
            'characters_missed': self.characters_missed,
            'test_duration': self.test_duration,
            'punctuation': self.punctuation,
            'numbers': self.numbers,
            'is_personal_best': self.is_personal_best,
            'quote_id': self.quote_id
        }


@dataclass
class PersonalBest:
    """Represents a personal best record"""
    id: Optional[int] = None
    mode: str = "words"
    mode_value: int = 50
    language: str = "english"
    difficulty: str = "normal"
    wpm: float = 0.0
    accuracy: float = 0.0
    test_id: Optional[int] = None
    achieved_at: datetime = field(default_factory=datetime.now)


@dataclass
class DailyStats:
    """Daily aggregated statistics"""
    date: str = ""  # YYYY-MM-DD format
    tests_completed: int = 0
    time_typed: int = 0  # seconds
    words_typed: int = 0
    avg_wpm: float = 0.0
    avg_accuracy: float = 0.0
    best_wpm: float = 0.0


@dataclass 
class Quote:
    """Represents a typing quote"""
    id: Optional[int] = None
    text: str = ""
    author: Optional[str] = None
    source: Optional[str] = None
    length: int = 0
    category: str = "random"
    language: str = "english"


@dataclass
class WordState:
    """State of a single word during typing"""
    word: str
    typed: str = ""
    chars: List[Tuple[str, str, bool]] = field(default_factory=list)  # (expected, typed, correct)
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
                chars = len(self.word)
                return (chars / 5) / (duration / 60)
        return 0.0


@dataclass
class TestState:
    """Current state of an active typing test"""
    mode: str = "words"
    mode_value: int = 50
    language: str = "english"
    difficulty: str = "normal"
    words: List[str] = field(default_factory=list)
    word_states: List[WordState] = field(default_factory=list)
    current_word_index: int = 0
    current_char_index: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    is_active: bool = False
    is_complete: bool = False
    time_limit: Optional[int] = None  # For time mode
    
    # Live stats
    correct_chars: int = 0
    incorrect_chars: int = 0
    extra_chars: int = 0
    missed_chars: int = 0
    total_keystrokes: int = 0
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds"""
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time else datetime.now().timestamp()
        return end - self.start_time
    
    @property
    def current_word(self) -> Optional[WordState]:
        """Get current word state"""
        if 0 <= self.current_word_index < len(self.word_states):
            return self.word_states[self.current_word_index]
        return None
