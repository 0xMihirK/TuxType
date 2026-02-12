"""Database manager for SQLite operations"""
import sqlite3
import os
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional, List, Tuple
from .models import TestResult, PersonalBest, DailyStats, Quote
from ..constants import MINIMUM_ACCURACY_FOR_PB, CHARS_PER_WORD, DEFAULT_SPARKLINE_LIMIT

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database operations for the typing test application"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager
        
        Args:
            db_path: Path to database file. If None, uses default in data directory.
        """
        if db_path is None:
            # Default to data directory in project root
            base_dir = Path(__file__).parent.parent.parent
            data_dir = base_dir / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "database.db")
        
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def _init_database(self) -> None:
        """Initialize database with schema"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Create tests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                mode TEXT NOT NULL,
                mode_value INTEGER,
                language TEXT NOT NULL,
                difficulty TEXT DEFAULT 'normal',
                wpm REAL NOT NULL,
                raw_wpm REAL NOT NULL,
                accuracy REAL NOT NULL,
                consistency REAL,
                characters_correct INTEGER,
                characters_incorrect INTEGER,
                characters_extra INTEGER,
                characters_missed INTEGER,
                test_duration REAL,
                punctuation BOOLEAN DEFAULT 0,
                numbers BOOLEAN DEFAULT 0,
                is_personal_best BOOLEAN DEFAULT 0,
                quote_id INTEGER,
                FOREIGN KEY (quote_id) REFERENCES quotes(id)
            )
        ''')
        
        # Create quotes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                author TEXT,
                source TEXT,
                length INTEGER,
                category TEXT,
                language TEXT DEFAULT 'english'
            )
        ''')
        
        # Create settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create personal_bests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS personal_bests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mode TEXT NOT NULL,
                mode_value INTEGER,
                language TEXT NOT NULL,
                difficulty TEXT DEFAULT 'normal',
                wpm REAL NOT NULL,
                accuracy REAL NOT NULL,
                test_id INTEGER,
                achieved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (test_id) REFERENCES tests(id),
                UNIQUE(mode, mode_value, language, difficulty)
            )
        ''')
        
        # Create daily_stats table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_stats (
                date DATE PRIMARY KEY,
                tests_completed INTEGER DEFAULT 0,
                time_typed INTEGER DEFAULT 0,
                words_typed INTEGER DEFAULT 0,
                avg_wpm REAL,
                avg_accuracy REAL,
                best_wpm REAL
            )
        ''')
        
        # Create indexes for common queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tests_timestamp ON tests(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tests_mode ON tests(mode, mode_value)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pb_mode ON personal_bests(mode, mode_value, language)')
        
        conn.commit()
    
    def close(self) -> None:
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    # Test Results CRUD
    def save_test_result(self, result: TestResult) -> int:
        """Save a test result and return its ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO tests (
                    timestamp, mode, mode_value, language, difficulty,
                    wpm, raw_wpm, accuracy, consistency,
                    characters_correct, characters_incorrect, characters_extra, characters_missed,
                    test_duration, punctuation, numbers, is_personal_best, quote_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.timestamp.isoformat(),
                result.mode,
                result.mode_value,
                result.language,
                result.difficulty,
                result.wpm,
                result.raw_wpm,
                result.accuracy,
                result.consistency,
                result.characters_correct,
                result.characters_incorrect,
                result.characters_extra,
                result.characters_missed,
                result.test_duration,
                result.punctuation,
                result.numbers,
                result.is_personal_best,
                result.quote_id
            ))
            
            test_id = cursor.lastrowid
            
            # Update daily stats
            self._update_daily_stats(result)
            
            # Check and update personal best
            if result.accuracy >= MINIMUM_ACCURACY_FOR_PB:  # Only consider for PB if accuracy >= 95%
                self._check_personal_best(result, test_id)
            
            conn.commit()
            return test_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to save test result: {e}")
            raise
    
    def get_test_results(self, limit: int = 50, offset: int = 0,
                         mode: Optional[str] = None,
                         language: Optional[str] = None) -> List[TestResult]:
        """Get test results with optional filters"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM tests WHERE 1=1'
        params = []
        
        if mode:
            query += ' AND mode = ?'
            params.append(mode)
        if language:
            query += ' AND language = ?'
            params.append(language)
        
        query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append(TestResult(
                id=row['id'],
                timestamp=datetime.fromisoformat(row['timestamp']),
                mode=row['mode'],
                mode_value=row['mode_value'],
                language=row['language'],
                difficulty=row['difficulty'],
                wpm=row['wpm'],
                raw_wpm=row['raw_wpm'],
                accuracy=row['accuracy'],
                consistency=row['consistency'] or 0,
                characters_correct=row['characters_correct'] or 0,
                characters_incorrect=row['characters_incorrect'] or 0,
                characters_extra=row['characters_extra'] or 0,
                characters_missed=row['characters_missed'] or 0,
                test_duration=row['test_duration'] or 0,
                punctuation=bool(row['punctuation']),
                numbers=bool(row['numbers']),
                is_personal_best=bool(row['is_personal_best'])
            ))
        
        return results
    
    def get_test_count(self) -> int:
        """Get total number of tests"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM tests')
        return cursor.fetchone()[0]
    
    def delete_test(self, test_id: int) -> bool:
        """Delete a test result"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM tests WHERE id = ?', (test_id,))
        conn.commit()
        return cursor.rowcount > 0
    
    def clear_history(self) -> None:
        """Clear all test history and statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Clear all related tables
        cursor.execute('DELETE FROM tests')
        cursor.execute('DELETE FROM personal_bests')
        cursor.execute('DELETE FROM daily_stats')
        
        # Reset auto-increment counters (optional, but good for clean slate)
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('tests', 'personal_bests')")
        
        conn.commit()
    
    # Personal Bests
    def _check_personal_best(self, result: TestResult, test_id: int) -> bool:
        """Check if result is a new personal best and update if so"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Check existing PB
        cursor.execute('''
            SELECT wpm FROM personal_bests 
            WHERE mode = ? AND mode_value = ? AND language = ? AND difficulty = ?
        ''', (result.mode, result.mode_value, result.language, result.difficulty))
        
        row = cursor.fetchone()
        
        if row is None or result.wpm > row['wpm']:
            # New personal best
            cursor.execute('''
                INSERT OR REPLACE INTO personal_bests 
                (mode, mode_value, language, difficulty, wpm, accuracy, test_id, achieved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.mode, result.mode_value, result.language, result.difficulty,
                result.wpm, result.accuracy, test_id, datetime.now().isoformat()
            ))
            
            # Mark test as personal best
            cursor.execute('UPDATE tests SET is_personal_best = 1 WHERE id = ?', (test_id,))
            conn.commit()
            return True
        
        return False
    
    def get_personal_bests(self) -> List[PersonalBest]:
        """Get all personal bests"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM personal_bests ORDER BY wpm DESC')
        
        results = []
        for row in cursor.fetchall():
            results.append(PersonalBest(
                id=row['id'],
                mode=row['mode'],
                mode_value=row['mode_value'],
                language=row['language'],
                difficulty=row['difficulty'],
                wpm=row['wpm'],
                accuracy=row['accuracy'],
                test_id=row['test_id'],
                achieved_at=datetime.fromisoformat(row['achieved_at'])
            ))
        return results
    
    def get_personal_best(self, mode: str, mode_value: int, 
                          language: str = "english",
                          difficulty: str = "normal") -> Optional[PersonalBest]:
        """Get personal best for specific mode/settings"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM personal_bests 
            WHERE mode = ? AND mode_value = ? AND language = ? AND difficulty = ?
        ''', (mode, mode_value, language, difficulty))
        
        row = cursor.fetchone()
        if row:
            return PersonalBest(
                id=row['id'],
                mode=row['mode'],
                mode_value=row['mode_value'],
                language=row['language'],
                difficulty=row['difficulty'],
                wpm=row['wpm'],
                accuracy=row['accuracy'],
                test_id=row['test_id'],
                achieved_at=datetime.fromisoformat(row['achieved_at'])
            )
        return None
    
    # Daily Stats
    def _update_daily_stats(self, result: TestResult) -> None:
        """Update daily statistics with new test result"""
        conn = self._get_connection()
        cursor = conn.cursor()
        today = date.today().isoformat()
        
        # Get existing stats
        cursor.execute('SELECT * FROM daily_stats WHERE date = ?', (today,))
        row = cursor.fetchone()
        
        words_typed = result.characters_correct // CHARS_PER_WORD  # Approximate words
        
        if row:
            # Update existing
            new_count = row['tests_completed'] + 1
            new_time = row['time_typed'] + int(result.test_duration)
            new_words = row['words_typed'] + words_typed
            new_avg_wpm = ((row['avg_wpm'] * row['tests_completed']) + result.wpm) / new_count
            new_avg_acc = ((row['avg_accuracy'] * row['tests_completed']) + result.accuracy) / new_count
            new_best = max(row['best_wpm'], result.wpm)
            
            cursor.execute('''
                UPDATE daily_stats 
                SET tests_completed = ?, time_typed = ?, words_typed = ?,
                    avg_wpm = ?, avg_accuracy = ?, best_wpm = ?
                WHERE date = ?
            ''', (new_count, new_time, new_words, new_avg_wpm, new_avg_acc, new_best, today))
        else:
            # Insert new
            cursor.execute('''
                INSERT INTO daily_stats 
                (date, tests_completed, time_typed, words_typed, avg_wpm, avg_accuracy, best_wpm)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (today, 1, int(result.test_duration), words_typed, 
                  result.wpm, result.accuracy, result.wpm))
        
        conn.commit()
    
    def get_daily_stats(self, date_str: Optional[str] = None) -> Optional[DailyStats]:
        """Get stats for a specific date (default today)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if date_str is None:
            date_str = date.today().isoformat()
        
        cursor.execute('SELECT * FROM daily_stats WHERE date = ?', (date_str,))
        row = cursor.fetchone()
        
        if row:
            return DailyStats(
                date=row['date'],
                tests_completed=row['tests_completed'],
                time_typed=row['time_typed'],
                words_typed=row['words_typed'],
                avg_wpm=row['avg_wpm'] or 0,
                avg_accuracy=row['avg_accuracy'] or 0,
                best_wpm=row['best_wpm'] or 0
            )
        return None
    
    # Aggregate Statistics
    def get_average_stats(self, limit: Optional[int] = None) -> dict:
        """Get average statistics across tests
        
        Args:
            limit: If provided, only consider last N tests
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if limit:
            cursor.execute('''
                SELECT AVG(wpm) as avg_wpm, AVG(accuracy) as avg_accuracy,
                       AVG(consistency) as avg_consistency, COUNT(*) as count
                FROM (SELECT wpm, accuracy, consistency FROM tests ORDER BY timestamp DESC LIMIT ?)
            ''', (limit,))
        else:
            cursor.execute('''
                SELECT AVG(wpm) as avg_wpm, AVG(accuracy) as avg_accuracy,
                       AVG(consistency) as avg_consistency, COUNT(*) as count
                FROM tests
            ''')
        
        row = cursor.fetchone()
        return {
            'avg_wpm': row['avg_wpm'] or 0,
            'avg_accuracy': row['avg_accuracy'] or 0,
            'avg_consistency': row['avg_consistency'] or 0,
            'count': row['count'] or 0
        }
    
    def get_total_stats(self) -> dict:
        """Get total cumulative statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_tests,
                SUM(test_duration) as total_time,
                SUM(characters_correct) as total_chars,
                MAX(wpm) as best_wpm
            FROM tests
        ''')
        
        row = cursor.fetchone()
        total_words = (row['total_chars'] or 0) // CHARS_PER_WORD
        
        return {
            'total_tests': row['total_tests'] or 0,
            'total_time': row['total_time'] or 0,
            'total_words': total_words,
            'total_chars': row['total_chars'] or 0,
            'best_wpm': row['best_wpm'] or 0
        }
    
    def get_streak(self) -> Tuple[int, int]:
        """Get current and best streak
        
        Returns:
            Tuple of (current_streak, best_streak)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT date FROM daily_stats ORDER BY date DESC')
        dates = [row['date'] for row in cursor.fetchall()]
        
        if not dates:
            return 0, 0
        
        # Calculate current streak
        current_streak = 0
        today = date.today()
        check_date = today
        
        for d in dates:
            if d == check_date.isoformat():
                current_streak += 1
                check_date = check_date - timedelta(days=1)  # Fixed: use timedelta instead of replace
            elif d == (today - timedelta(days=1)).isoformat() and current_streak == 0:
                # Started counting from yesterday
                current_streak = 1
                check_date = date.fromisoformat(d) - timedelta(days=1)  # Fixed: use timedelta
            else:
                break
        
        # Calculate best streak by checking all consecutive sequences
        best_streak = current_streak
        if len(dates) > 1:
            temp_streak = 1
            for i in range(len(dates) - 1):
                date1 = date.fromisoformat(dates[i])
                date2 = date.fromisoformat(dates[i + 1])
                if (date1 - date2).days == 1:
                    temp_streak += 1
                    best_streak = max(best_streak, temp_streak)
                else:
                    temp_streak = 1
        
        return current_streak, best_streak
    
    def get_recent_sparkline_data(self, limit: int = DEFAULT_SPARKLINE_LIMIT) -> Tuple[List[float], List[float]]:
        """Get WPM and accuracy data for recent tests for sparklines
        
        Args:
            limit: Number of recent tests to retrieve
            
        Returns:
            Tuple of (wpm_values, accuracy_values) lists
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT wpm, accuracy FROM (
                SELECT wpm, accuracy, timestamp FROM tests 
                ORDER BY timestamp DESC 
                LIMIT ?
            ) sub ORDER BY timestamp ASC
        ''', (limit,))
        
        rows = cursor.fetchall()
        wpm_values = [row['wpm'] for row in rows]
        accuracy_values = [row['accuracy'] for row in rows]
        
        return wpm_values, accuracy_values
    
    # Settings
    def get_setting(self, key: str, default: str = "") -> str:
        """Get a setting value"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        return row['value'] if row else default
    
    def set_setting(self, key: str, value: str) -> None:
        """Set a setting value"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
        ''', (key, value, datetime.now().isoformat()))
        conn.commit()
