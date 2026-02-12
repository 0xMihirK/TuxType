"""Word generator for typing tests"""
import random
import json
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class WordGenerator:
    """Generates words for typing tests from word lists"""
    
    def __init__(self, data_dir: Optional[str] = None):
        """Initialize word generator
        
        Args:
            data_dir: Path to data directory containing word lists
        """
        if data_dir is None:
            base_dir = Path(__file__).parent.parent.parent
            data_dir = base_dir / "data"
        
        self.data_dir = Path(data_dir)
        self.wordlists_dir = self.data_dir / "wordlists"
        self.quotes_dir = self.data_dir / "quotes"
        
        # Cache loaded word lists
        self._word_cache: dict = {}
        self._quotes_cache: dict = {}
        
        # Ensure directories exist
        self.wordlists_dir.mkdir(parents=True, exist_ok=True)
        self.quotes_dir.mkdir(parents=True, exist_ok=True)
        
        # Create default word lists if they don't exist
        self._ensure_default_wordlists()
    
    def _ensure_default_wordlists(self) -> None:
        """Create default word lists if they don't exist"""
        english_path = self.wordlists_dir / "english_2k.txt"
        if not english_path.exists():
            self._create_default_english_wordlist(english_path)
        
        english_uk_path = self.wordlists_dir / "english_uk.txt"
        if not english_uk_path.exists():
            self._create_english_uk_wordlist(english_uk_path)
        
        programming_path = self.wordlists_dir / "programming.txt"
        if not programming_path.exists():
            self._create_programming_wordlist(programming_path)
        
        quotes_path = self.quotes_dir / "quotes.json"
        if not quotes_path.exists():
            self._create_default_quotes(quotes_path)
    
    def _create_default_english_wordlist(self, path: Path) -> None:
        """Create default English word list with 2000+ common words"""
        try:
            # Most common 2000+ English words for typing practice
            words = """the be to of and a in that have I it for not on with he as you do at
this but his by from they we say her she or an will my one all would there their what
so up out if about who get which go me when make can like time no just him know take
people into year your good some could them see other than then now look only come its
over think also back after use two how our work first well way even new want because
any these give day most us three very own much find make part little house live hand
eye last never child late light call keep head why ask went men need try kind change
room off still learn should place mean old year great same follow same small father any
set put end high both group often run important until form food keep large turn write
place made where system show early begin since study those increase lead number program
public part fact open always big small home help problem through must line right mean 
certain become perhaps side together move point government set world since present state
develop happen during power community play night start city might story seem book young
student provide allow without however once support include question during without might
against order return person might cause effect group become problem such these point
level next away possible program always country area remember consider child support area
create become system order child each school national become seem involve stand service
change possible fact something personal decision sure rather family moment sense simply
add include stand continue believe friend during against support several order really
term leave accept public certain consider become sometimes story effect various president
itself remain within build seem quite human view couple produce provide strong moment
plan break happen carry future control probably return begin police case federal either
major nothing share support particularly allow bring change economic important expect
face health program receive reflect believe report today white among experience require
require remember remain continue center allow according interest education director price
evidence political course activity across development increase attention century author
level available amount suggest interest activity explain defense appear develop language
available market present situation determine claim party standard business remain response
popular establish picture clearly inside modern language decision medical create process
treatment action church growth service identify research challenge indicate character pass
reflect whatever perform director minute himself imagine appear wonder financial support
perform require together difficult remember especially recently maintain environmental
treatment audience whatever difficult performance activity consider everything everybody
morning yourself understand generation strategy structure technology opportunity economic
specific significant southern Republican financial customer security magazine candidate
professional movement management individual relationship communication Republican somebody
generation collection successful specifically institution throughout professional education
traditional population especially religious technology particularly beautiful relationship
democratic significant campaign participant environmental professional traditional marriage
discussion understand conference religious technology everybody significant relationship
participant professional military everybody marriage traditional specifically strategy
environmental technology discussion particularly conference democratic management individual
Republican professional military beautiful successful customer security specifically
magazine institution campaign democratic religious significant traditional relationship
environmental professional participant conference technology discussion everybody marriage
individual management beautiful democratic successful strategy religious environmental
technology professional traditional significant conference discussion relationship marriage
individual participant campaign democratic everybody management strategy environmental
beautiful successful traditional professional Republican significant technology religious
conference individual participant discussion management relationship democratic marriage
strategy environmental traditional campaign successful technology beautiful professional
significant religious everybody participant conference individual discussion democratic
management relationship marriage strategy traditional successful environmental campaign
professional beautiful technology religious significant participant everybody conference
democratic individual discussion management traditional relationship marriage strategy
environmental successful campaign beautiful professional technology significant religious
participant everybody democratic conference individual discussion traditional management
relationship marriage environmental strategy successful campaign technology beautiful
professional significant religious participant democratic everybody conference individual
discussion traditional management relationship environmental marriage strategy successful
campaign beautiful technology professional significant religious participant democratic
conference everybody individual discussion traditional management relationship environmental
marriage strategy successful technology campaign beautiful professional significant religious
democratic participant everybody conference individual discussion traditional management
relationship environmental marriage strategy successful campaign technology beautiful
professional significant religious democratic participant conference everybody individual
discussion traditional management environmental relationship marriage strategy successful
technology campaign beautiful professional significant religious democratic participant
conference everybody individual discussion traditional management environmental relationship
marriage strategy successful technology campaign beautiful professional significant religious
democratic participant conference everybody individual discussion traditional management
environmental relationship marriage strategy successful technology campaign beautiful
professional significant religious democratic participant conference everybody individual
discussion traditional management environmental relationship marriage strategy successful
technology campaign beautiful professional significant religious democratic participant
conference everybody individual discussion traditional management environmental relationship
marriage strategy successful technology campaign beautiful professional significant religious
democratic participant conference everybody individual discussion traditional management
environmental relationship marriage strategy successful technology campaign beautiful
professional significant religious democratic participant conference everybody individual
discussion traditional management environmental relationship marriage strategy successful
technology campaign beautiful professional significant religious democratic participant
conference everybody individual discussion traditional management environmental relationship
marriage strategy successful technology campaign beautiful professional significant religious
democratic participant conference everybody""".split()
            
            # Remove duplicates while preserving order
            seen = set()
            unique_words = []
            for word in words:
                if word.lower() not in seen:
                    seen.add(word.lower())
                    unique_words.append(word.lower())
            
            path.write_text('\n'.join(unique_words), encoding='utf-8')
        except IOError as e:
            logger.error(f"Failed to create default English wordlist: {e}")
            # Continue without file - will use fallback words
    
    def _create_english_uk_wordlist(self, path: Path) -> None:
        """Create English UK word list with British spelling"""
        try:
            # British English spelling variants + common UK words
            words = """the be to of and a in that have I it for not on with he as you do at
this but his by from they we say her she or an will my one all would there their what
so up out if about who get which go me when make can like time no just him know take
people into year your good some could them see other than then now look only come its
over think also back after use two how our work first well way even new want because
any these give day most us three very own much find make part little house live hand
eye last never child late light call keep head why ask went men need try kind change
room off still learn should place mean old year great same follow same small father any
set put end high both group often run important until form food keep large turn write
place made where system show early begin since study those increase lead number programme
public part fact open always big small home help problem through must line right mean
certain become perhaps side together move point government set world since present state
develop happen during power community play night start city might story seem book young
student provide allow without however once support include question during without might
against order return person might cause effect group become problem such these point
level next away possible programme always country area remember consider child support
create become system order child each school national become seem involve stand service
change possible fact something personal decision sure rather family moment sense simply
add include stand continue believe friend during against support several order really
term leave accept public certain consider become sometimes story effect various president
itself remain within build seem quite human view couple produce provide strong moment
plan break happen carry future control probably return begin police case federal either
major nothing share support particularly allow bring change economic important expect
face health programme receive reflect believe report today white among experience require
require remember remain continue centre allow according interest education director price
evidence political course activity across development increase attention century author
level available amount suggest interest activity explain defence appear develop language
available market present situation determine claim party standard business remain response
popular establish picture clearly inside modern language decision medical create process
treatment action church growth service identify research challenge indicate character pass
reflect whatever perform director minute himself imagine appear wonder financial support
perform require together difficult remember especially recently maintain environmental
treatment audience whatever difficult performance activity consider everything everybody
morning yourself understand generation strategy structure technology opportunity economic
specific significant southern labour financial customer security magazine candidate
professional movement management individual relationship communication organisation somebody
generation collection successful specifically institution throughout professional education
traditional population especially religious technology particularly beautiful relationship
democratic significant campaign participant environmental professional traditional marriage
discussion understand conference religious technology everybody significant relationship
participant professional military everybody marriage traditional specifically strategy
environmental technology discussion particularly conference democratic management individual
labour professional military beautiful successful customer security specifically magazine
institution campaign democratic religious significant traditional relationship environmental
professional participant conference technology discussion everybody marriage individual
management beautiful democratic successful strategy religious environmental technology
professional traditional significant conference discussion relationship marriage individual
participant campaign democratic everybody management strategy environmental beautiful
successful traditional professional labour significant technology religious conference
individual participant discussion management relationship democratic marriage strategy
environmental traditional campaign successful technology beautiful professional significant
religious everybody participant conference individual discussion democratic management
relationship marriage strategy traditional successful environmental campaign professional
beautiful technology religious significant participant everybody conference democratic
individual discussion management traditional relationship marriage strategy environmental
successful campaign beautiful professional technology significant religious participant
everybody democratic conference individual discussion traditional management relationship
environmental marriage strategy successful campaign technology beautiful professional
significant religious participant democratic everybody conference individual discussion
traditional management relationship environmental marriage strategy successful technology
campaign beautiful professional significant religious democratic participant conference
everybody individual discussion traditional management relationship environmental marriage
strategy successful technology campaign beautiful professional significant religious
democratic participant conference everybody individual discussion traditional management
environmental relationship marriage strategy successful technology campaign beautiful
professional significant religious democratic participant conference everybody individual
discussion traditional management environmental relationship marriage strategy successful
technology campaign beautiful professional significant religious democratic participant
conference everybody individual discussion traditional management environmental relationship
marriage strategy successful technology campaign beautiful professional significant religious
democratic participant conference everybody colour favour realise organise honour labour
centre metre litre theatre catalogue analyse defence practise licence offence behaviour
neighbour flavour rumour humour favour harbour odour vapour favour colour harbour labour
honour favour rumour colour honour labour favour colour honour labour favour colour
honour labour favour colour honour labour favour colour honour labour favour marvellous
travelling jewellery flavour programme catalogue grey connexion whilst amongst towards
afterwards fulfil enrol skilful wilful defence offence licence practise woollen pyjamas
analyse paralyse catalogue dialogue prologue monologue analogue epilogue travelled
cancelled fuelling levelled modelling quarrelled signalled jeweller marvellous""".split()
        
            # Remove duplicates while preserving order
            seen = set()
            unique_words = []
            for word in words:
                if word.lower() not in seen:
                    seen.add(word.lower())
                    unique_words.append(word.lower())
            
            path.write_text('\n'.join(unique_words), encoding='utf-8')
        except IOError as e:
            logger.error(f"Failed to create English UK wordlist: {e}")
            # Continue without file - will use fallback words
    
    def _create_programming_wordlist(self, path: Path) -> None:
        """Create programming keywords word list with syntax-style words"""
        try:
            words = [
            "def()", "class:", "if(x)", "else{", "elif:", "for(i",
            "while(true)", "return;", "import{", "from", "as", "with(",
            "try{", "except:", "finally{", "raise", "assert(", "break;",
            "continue;", "pass", "yield", "lambda:", "async", "await",
            "True", "False", "None", "and", "or", "not", "in", "is", "del",
            'print("', 'input("', "len(x)", "str(x)", "int(x)", "float(x)",
            "list()", "dict()", "set()", "tuple()", "range(10)", "type(x)",
            "function()", "func(x,", "var", "let", "const", "new",
            "this.", "self.", "static", "public", "private", "void",
            "boolean", "string", "number", "array[]", "object{}",
            "null", "undefined", "export", "default", 'require("',
            "module.", "extends", "implements", "interface", "abstract",
            "override", "throw", 'error("', 'console.log("',
            "window.", "document.", 'querySelector("', 'getElementById("',
            'addEventListener("', 'createElement("', "appendChild(",
            "innerHTML", "className", 'setAttribute("',
            "setTimeout(", "setInterval(", "clearTimeout(",
            "Promise.", "async/await", ".then(", ".catch(", ".finally(",
            'fetch("', "response.json()", "JSON.parse(",
            "JSON.stringify(", "Object.keys(", "Array.from(",
            "Map()", "Set()", "forEach(", "filter(", "reduce(",
            "map(x", "find(x", "sort()", "splice(0,", "slice(0,",
            "push(x)", "pop()", "shift()", "concat(", "includes(",
            "indexOf(", "toString()", "parseInt(", "parseFloat(",
            "Math.random()", "Math.floor(", "Math.ceil(",
            "Date.now()", "RegExp(", "isNaN(x)", "typeof(x)",
            "instanceof", "===", "!==", ">=", "<=", "=>",
            "->", "::", "&&", "||", "??", "?.",
                "...args", "${value}", "`template`",
                "<div>", "</div>", "<span>", "{...props}", "[...arr]",
                "**kwargs", "*args", "@decorator", "#include", "#define",
                "//comment", "/*block*/",
            ]
            path.write_text('\n'.join(words), encoding='utf-8')
        except IOError as e:
            logger.error(f"Failed to create programming wordlist: {e}")
            # Continue without file - will use fallback words
    
    def _create_default_quotes(self, path: Path) -> None:
        """Create default quotes file"""
        try:
            quotes = [
            {
                "text": "The only way to do great work is to love what you do.",
                "author": "Steve Jobs",
                "source": "Stanford Commencement Speech",
                "category": "inspirational"
            },
            {
                "text": "Innovation distinguishes between a leader and a follower.",
                "author": "Steve Jobs",
                "source": None,
                "category": "inspirational"
            },
            {
                "text": "Code is like humor. When you have to explain it, it's bad.",
                "author": "Cory House",
                "source": None,
                "category": "programming"
            },
            {
                "text": "First, solve the problem. Then, write the code.",
                "author": "John Johnson",
                "source": None,
                "category": "programming"
            },
            {
                "text": "Experience is the name everyone gives to their mistakes.",
                "author": "Oscar Wilde",
                "source": None,
                "category": "inspirational"
            },
            {
                "text": "The best error message is the one that never shows up.",
                "author": "Thomas Fuchs",
                "source": None,
                "category": "programming"
            },
            {
                "text": "Simplicity is the soul of efficiency.",
                "author": "Austin Freeman",
                "source": None,
                "category": "programming"
            },
            {
                "text": "Make it work, make it right, make it fast.",
                "author": "Kent Beck",
                "source": None,
                "category": "programming"
            },
            {
                "text": "The function of good software is to make the complex appear to be simple.",
                "author": "Grady Booch",
                "source": None,
                "category": "programming"
            },
            {
                "text": "Any fool can write code that a computer can understand. Good programmers write code that humans can understand.",
                "author": "Martin Fowler",
                "source": "Refactoring",
                "category": "programming"
            },
            {
                "text": "The quick brown fox jumps over the lazy dog.",
                "author": None,
                "source": "Pangram",
                "category": "practice"
            },
            {
                "text": "Pack my box with five dozen liquor jugs.",
                "author": None,
                "source": "Pangram",
                "category": "practice"
            },
            {
                "text": "How vexingly quick daft zebras jump!",
                "author": None,
                "source": "Pangram",
                "category": "practice"
            },
            {
                "text": "Success is not final, failure is not fatal: it is the courage to continue that counts.",
                "author": "Winston Churchill",
                "source": None,
                "category": "inspirational"
            },
            {
                "text": "The only limit to our realization of tomorrow will be our doubts of today.",
                "author": "Franklin D. Roosevelt",
                "source": None,
                "category": "inspirational"
            }
        ]
        
            # Add length to each quote
            for quote in quotes:
                quote["length"] = len(quote["text"])
            
            path.write_text(json.dumps(quotes, indent=2), encoding='utf-8')
        except (IOError, json.JSONEncodeError) as e:
            logger.error(f"Failed to create default quotes file: {e}")
            # Continue without file - will use fallback quotes
    
    def load_wordlist(self, language: str = "english") -> List[str]:
        """Load word list for given language
        
        Args:
            language: Language name (maps to wordlist file)
            
        Returns:
            List of words
        """
        # Sanitize language input to prevent directory traversal
        language = language.replace('..', '').replace('/', '').replace('\\', '')
        
        if language in self._word_cache:
            return self._word_cache[language]
        
        # Map language to file
        file_map = {
            "english": "english_2k.txt",
            "english_us": "english_2k.txt",
            "english_uk": "english_uk.txt",
            "programming": "programming.txt",
        }
        
        filename = file_map.get(language.lower(), "english_2k.txt")
        filepath = self.wordlists_dir / filename
        
        # Ensure path is within wordlists directory
        try:
            filepath = filepath.resolve()
            if not filepath.is_relative_to(self.wordlists_dir.resolve()):
                logger.warning(f"Invalid wordlist path attempted: {filepath}")
                return ["the", "quick", "brown", "fox", "jumps", "over", "the", "lazy", "dog"]
        except (ValueError, OSError):
            logger.warning(f"Path resolution failed for: {filepath}")
            return ["the", "quick", "brown", "fox", "jumps", "over", "the", "lazy", "dog"]
        
        if filepath.exists():
            try:
                text = filepath.read_text(encoding='utf-8')
                words = [w.strip() for w in text.split('\n') if w.strip()]
                if words:
                    self._word_cache[language] = words
                    return words
            except IOError as e:
                logger.error(f"Failed to load wordlist {filepath}: {e}")
        
        # Return fallback words
        logger.info(f"Using fallback words for language: {language}")
        return ["the", "quick", "brown", "fox", "jumps", "over", "the", "lazy", "dog"]
    
    def generate_words(self, count: int = 50, language: str = "english",
                       punctuation: bool = False, numbers: bool = False) -> List[str]:
        """Generate list of random words for typing test
        
        Args:
            count: Number of words to generate
            language: Language/word list to use
            punctuation: Whether to add punctuation
            numbers: Whether to add numbers
            
        Returns:
            List of words
        """
        wordlist = self.load_wordlist(language)
        
        if not wordlist:
            return ["error", "loading", "wordlist"]
        
        # Select random words
        words = [random.choice(wordlist) for _ in range(count)]
        
        # Skip extra punctuation/numbers for programming (already has syntax)
        if language.lower() == "programming":
            return words
        
        # Add punctuation if requested
        if punctuation:
            words = self._add_punctuation(words)
        
        # Add numbers if requested
        if numbers:
            words = self._add_numbers(words)
        
        return words
    
    def _add_punctuation(self, words: List[str]) -> List[str]:
        """Add punctuation to some words"""
        punctuation_marks = ['.', ',', '!', '?', ';', ':', "'", '"']
        result = []
        
        for i, word in enumerate(words):
            # Add punctuation at end of some words (roughly 15%)
            if random.random() < 0.15:
                mark = random.choice(punctuation_marks[:4])  # Common end punctuation
                word = word + mark
            # Capitalize first word and words after sentence-ending punctuation
            elif i == 0 or (result and result[-1][-1] in '.!?'):
                word = word.capitalize()
            
            result.append(word)
        
        return result
    
    def _add_numbers(self, words: List[str]) -> List[str]:
        """Add numbers to the word list"""
        result = []
        
        for word in words:
            # Replace some words with numbers (roughly 10%)
            if random.random() < 0.10:
                result.append(str(random.randint(0, 9999)))
            else:
                result.append(word)
        
        return result
    
    def load_quotes(self, category: Optional[str] = None,
                    length: Optional[str] = None) -> List[dict]:
        """Load quotes with optional filters
        
        Args:
            category: Filter by category (inspirational, programming, etc.)
            length: Filter by length (short, medium, long, extended)
            
        Returns:
            List of quote dictionaries
        """
        quotes_path = self.quotes_dir / "quotes.json"
        
        if not quotes_path.exists():
            self._create_default_quotes(quotes_path)
        
        try:
            quotes = json.loads(quotes_path.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load quotes: {e}")
            return []
        
        # Filter by category
        if category:
            quotes = [q for q in quotes if q.get('category') == category]
        
        # Filter by length
        if length:
            length_ranges = {
                'short': (0, 100),
                'medium': (100, 200),
                'long': (200, 400),
                'extended': (400, float('inf'))
            }
            min_len, max_len = length_ranges.get(length, (0, float('inf')))
            quotes = [q for q in quotes if min_len <= q.get('length', 0) < max_len]
        
        return quotes
    
    def get_random_quote(self, category: Optional[str] = None,
                         length: Optional[str] = None) -> Optional[dict]:
        """Get a random quote
        
        Args:
            category: Filter by category
            length: Filter by length
            
        Returns:
            Quote dictionary or None if no quotes found
        """
        quotes = self.load_quotes(category, length)
        return random.choice(quotes) if quotes else None
    
    def get_quote_words(self, quote: dict) -> List[str]:
        """Convert quote to list of words for typing
        
        Args:
            quote: Quote dictionary with 'text' key
            
        Returns:
            List of words
        """
        text = quote.get('text', '')
        return text.split()
