"""Application-wide constants"""

# ── Test Settings ──
CHARS_PER_WORD = 5
MINIMUM_ACCURACY_FOR_PB = 95.0
TIME_MODE_WORD_BUFFER = 500
TIME_MODE_WORD_BATCH = 100

# ── Display Settings ──
MAX_LINE_WIDTH = 60
VIEWPORT_LINES = 3
BAR_WIDTH = 40
BAR_FILLED = "━"
BAR_EMPTY = "━"

# ── Statistics ──
DEFAULT_SPARKLINE_LIMIT = 20
DEFAULT_HISTORY_LIMIT = 50
DEFAULT_STATS_LIMIT = 10

# ── Test Modes ──
VALID_TEST_MODES = ['words', 'time', 'quote', 'custom']
VALID_DIFFICULTIES = ['normal', 'expert', 'master']
VALID_LANGUAGES = ['english', 'english_uk', 'programming']

# ── Word Count Options ──
WORD_COUNT_OPTIONS = [10, 25, 50, 100]
TIME_OPTIONS = [15, 30, 60, 120]  # seconds

# ── Database ──
DEFAULT_DB_NAME = "database.db"
DEFAULT_DATA_DIR = "data"

# ── File Paths ──
WORDLISTS_SUBDIR = "wordlists"
QUOTES_SUBDIR = "quotes"
CONFIG_FILENAME = "tuxtype.config"
LOG_FILENAME = "tuxtype.log"
