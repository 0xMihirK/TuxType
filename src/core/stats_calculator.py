"""Statistics calculator for typing tests"""
import statistics
import logging
from typing import List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Constants
CHARS_PER_WORD = 5


@dataclass
class CharacterStats:
    """Character-level statistics"""
    correct: int = 0
    incorrect: int = 0
    extra: int = 0
    missed: int = 0
    
    @property
    def total(self) -> int:
        return self.correct + self.incorrect + self.extra
    
    def to_string(self) -> str:
        return f"{self.correct}/{self.incorrect}/{self.extra}/{self.missed}"


class StatsCalculator:
    """Calculate typing test statistics"""
    
    @staticmethod
    def calculate_wpm(correct_chars: int, elapsed_seconds: float) -> float:
        """Calculate Words Per Minute
        
        WPM = (correct_characters / 5) / (time_elapsed / 60)
        
        Args:
            correct_chars: Number of correctly typed characters
            elapsed_seconds: Time elapsed in seconds
            
        Returns:
            WPM value
        """
        if elapsed_seconds <= 0:
            return 0.0
        
        words = correct_chars / CHARS_PER_WORD  # Standard: 5 chars = 1 word
        minutes = elapsed_seconds / 60
        return round(words / minutes, 2)
    
    @staticmethod
    def calculate_raw_wpm(total_chars: int, elapsed_seconds: float) -> float:
        """Calculate Raw WPM (including incorrect characters)
        
        Args:
            total_chars: Total number of typed characters (correct + incorrect)
            elapsed_seconds: Time elapsed in seconds
            
        Returns:
            Raw WPM value
        """
        if elapsed_seconds <= 0:
            return 0.0
        
        words = total_chars / CHARS_PER_WORD
        minutes = elapsed_seconds / 60
        return round(words / minutes, 2)
    
    @staticmethod
    def calculate_accuracy(correct_chars: int, total_chars: int) -> float:
        """Calculate typing accuracy percentage
        
        Args:
            correct_chars: Number of correctly typed characters
            total_chars: Total characters typed
            
        Returns:
            Accuracy percentage (0-100)
        """
        if total_chars <= 0:
            return 100.0
        
        return round((correct_chars / total_chars) * 100, 2)
    
    @staticmethod
    def calculate_consistency(word_speeds: List[float]) -> float:
        """Calculate typing consistency based on speed variation
        
        Consistency = 100 - (std_dev / mean * 100)
        Higher is better (less variation)
        
        Args:
            word_speeds: List of WPM values for each word
            
        Returns:
            Consistency percentage (0-100)
        """
        if len(word_speeds) < 2:
            return 100.0
        
        # Filter out zero speeds
        speeds = [s for s in word_speeds if s > 0]
        
        if len(speeds) < 2:
            return 100.0
        
        try:
            mean = statistics.mean(speeds)
            if mean <= 0:
                return 100.0
            
            std_dev = statistics.stdev(speeds)
            consistency = 100 - (std_dev / mean * 100)
            
            # Clamp to 0-100 range
            return round(max(0, min(100, consistency)), 2)
        except statistics.StatisticsError:
            return 100.0
    
    @staticmethod
    def calculate_burst_speed(chars: int, seconds: float) -> float:
        """Calculate burst speed for current word
        
        Args:
            chars: Characters in current word
            seconds: Time spent on current word
            
        Returns:
            Burst WPM
        """
        if seconds <= 0:
            return 0.0
        
        return StatsCalculator.calculate_wpm(chars, seconds)
    
    @staticmethod
    def get_char_stats(expected: str, typed: str) -> CharacterStats:
        """Compare expected and typed strings to get character stats
        
        Args:
            expected: Expected text
            typed: Actually typed text
            
        Returns:
            CharacterStats with correct/incorrect/extra/missed counts
        """
        stats = CharacterStats()
        
        exp_len = len(expected)
        typ_len = len(typed)
        
        # Compare characters up to the shorter length
        compare_len = min(exp_len, typ_len)
        
        for i in range(compare_len):
            if typed[i] == expected[i]:
                stats.correct += 1
            else:
                stats.incorrect += 1
        
        # Extra characters (typed more than expected)
        if typ_len > exp_len:
            stats.extra = typ_len - exp_len
        
        # Missed characters (typed less than expected)
        if typ_len < exp_len:
            stats.missed = exp_len - typ_len
        
        return stats
    
    @staticmethod
    def format_time(seconds: float) -> str:
        """Format seconds as MM:SS or M:SS
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted time string
        """
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration for display (e.g., "1h 23m" or "45s")
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Human-readable duration string
        """
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            if secs > 0:
                return f"{minutes}m {secs}s"
            return f"{minutes}m"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            if minutes > 0:
                return f"{hours}h {minutes}m"
            return f"{hours}h"


class LiveStats:
    """Track live statistics during a typing test"""
    
    def __init__(self):
        self.reset()
    
    def reset(self) -> None:
        """Reset all stats"""
        self.correct_chars = 0
        self.incorrect_chars = 0
        self.extra_chars = 0
        self.missed_chars = 0
        self.total_keystrokes = 0
        self.word_speeds: List[float] = []
        self.wpm_history: List[Tuple[float, float]] = []  # (time, wpm)
        self.start_time: Optional[float] = None
        self.current_word_start: Optional[float] = None
    
    def add_correct_char(self) -> None:
        """Record a correct character"""
        self.correct_chars += 1
        self.total_keystrokes += 1
    
    def add_incorrect_char(self) -> None:
        """Record an incorrect character"""
        self.incorrect_chars += 1
        self.total_keystrokes += 1
    
    def add_extra_char(self) -> None:
        """Record an extra character"""
        self.extra_chars += 1
        self.total_keystrokes += 1
    
    def remove_char(self, was_correct: bool = True) -> None:
        """Remove a character (backspace)"""
        if was_correct:
            self.correct_chars = max(0, self.correct_chars - 1)
        else:
            self.incorrect_chars = max(0, self.incorrect_chars - 1)
    
    def complete_word(self, word_wpm: float) -> None:
        """Record completion of a word"""
        self.word_speeds.append(word_wpm)
    
    def add_missed_chars(self, count: int) -> None:
        """Add missed characters (word submitted short)"""
        self.missed_chars += count
    
    def record_wpm(self, time: float, wpm: float) -> None:
        """Record WPM at a point in time for graphing"""
        self.wpm_history.append((time, wpm))
    
    @property
    def total_chars(self) -> int:
        """Total characters typed"""
        return self.correct_chars + self.incorrect_chars
    
    def get_wpm(self, elapsed_seconds: float) -> float:
        """Get current WPM"""
        return StatsCalculator.calculate_wpm(self.correct_chars, elapsed_seconds)
    
    def get_raw_wpm(self, elapsed_seconds: float) -> float:
        """Get current raw WPM"""
        return StatsCalculator.calculate_raw_wpm(self.total_chars, elapsed_seconds)
    
    def get_accuracy(self) -> float:
        """Get current accuracy"""
        return StatsCalculator.calculate_accuracy(self.correct_chars, self.total_chars)
    
    def get_consistency(self) -> float:
        """Get current consistency"""
        return StatsCalculator.calculate_consistency(self.word_speeds)
    
    def get_char_stats(self) -> CharacterStats:
        """Get character statistics"""
        return CharacterStats(
            correct=self.correct_chars,
            incorrect=self.incorrect_chars,
            extra=self.extra_chars,
            missed=self.missed_chars
        )
