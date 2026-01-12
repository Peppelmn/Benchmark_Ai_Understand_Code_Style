from pathlib import Path

class CodebaseAnalyzer:
    """
    Base class for specific codebase analyzers (e.g., Spacing, Naming).
    It handles the initial scanning of the directory, filtering of invalid or
    excessively large files, and caches the list of valid Python files to avoid
    redundant I/O operations across different analyzer instances.
    """
    _python_files_cache = [] 
    _is_initialized = False
    
    def __init__(self, codebase_path: str, max_token_limit, max_results_per_question = 10):
        """
        Initializes the analyzer by setting up paths and limits.
        If the shared file cache is empty, it triggers a codebase scan.

        Args:
            codebase_path (str): The root path to the directory to analyze.
            max_token_limit (int): The maximum allowed tokens (approx.) per file. Files exceeding this are skipped.
            max_results_per_question (int, optional): The target number of samples to find per question type. Defaults to 10.
        """
        self.codebase_path = Path(codebase_path)
        self.python_files = CodebaseAnalyzer._python_files_cache 
        self.parse_error_count = 0
        self.max_results_per_question = max_results_per_question
        self.max_token_limit = max_token_limit
        self.max_char_limit = max_token_limit * 4
        
        if not CodebaseAnalyzer._is_initialized:
            self._scan_codebase()
            CodebaseAnalyzer._is_initialized = True
        else:
            print(f"Analyzer pronto. File caricati dalla cache: {len(self.python_files)}")

    def _scan_codebase(self):
        """
        Private method that performs the actual file system traversal.
        It recursively finds .py files, applies filters (folders, symlinks, size),
        and populates the class-level `_python_files_cache`.
        """
        print(f"Inizializzazione Analyzer: scansione file in {self.codebase_path}...")
        token_skipped_count = 0
        exception_skipped_count = 0

        CodebaseAnalyzer._python_files_cache.clear()

        for path in self.codebase_path.rglob("*.py"):
            
            if any(part in {".git", "__pycache__", ".venv", "venv", "node_modules", "build", "dist"} for part in path.parts):
                continue
            
            if path.is_symlink():
                continue

            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                if len(content) > self.max_char_limit:
                    token_skipped_count += 1
                    continue
                    
                if not content.strip():
                    continue

            except Exception:
                exception_skipped_count += 1
                continue

            CodebaseAnalyzer._python_files_cache.append(path)
            
        print(f"Scansione completata. File validi caricati: {len(CodebaseAnalyzer._python_files_cache)}")
        print(f"\t->Scartati per numero token > {self.max_token_limit}: {token_skipped_count}")
        print(f"\t->Scartati per errori di lettura: {exception_skipped_count}")