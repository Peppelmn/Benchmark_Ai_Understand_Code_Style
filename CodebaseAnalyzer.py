from pathlib import Path
from typing import List

class CodebaseAnalyzer:
    """
    Base class for specific codebase analyzers (e.g., Spacing, Naming).
    It handles the initial scanning of the directory, filtering of invalid,
    excessively large, or irrelevant files (tests, migrations), and caches 
    the list of valid Python files to avoid redundant I/O operations.
    """
    _python_files_cache = [] 
    _is_initialized = False
    
    def __init__(self, codebase_path: str, max_token_limit: float = float('inf')):
        """
        Initializes the analyzer by setting up paths and limits.
        If the shared file cache is empty, it triggers a codebase scan.

        Args:
            codebase_path (str): The root path to the directory to analyze.
            max_token_limit (float): The maximum allowed tokens (approx.) per file. 
                                     Files exceeding this are skipped.
        """
        self.codebase_path = Path(codebase_path)
        self.python_files = CodebaseAnalyzer._python_files_cache 
        self.parse_error_count = 0
        self.max_token_limit = max_token_limit
        self.max_char_limit = max_token_limit * 4
        
        if not CodebaseAnalyzer._is_initialized:
            self._scan_codebase()
            CodebaseAnalyzer._is_initialized = True
        else:
            print(f"Analyzer pronto. File caricati dalla cache: {len(self.python_files)}")

    def _is_test_or_generated(self, path: Path) -> bool:
        """
        Helper method to detect test files, migrations, and config files.
        """
        name = path.name.lower()
        parts = [p.lower() for p in path.parts]

        # 1. Skip Test files (spesso contengono mock o codice strano)
        if name.startswith("test_") or name.endswith("_test.py") or name.endswith("test.py"):
            return True
        if "tests" in parts or "test" in parts or "testing" in parts:
            return True

        # 2. Skip Migrations (Django/Flask, spesso auto-generati)
        if "migrations" in parts or "alembic" in parts:
            return True
            
        # 3. Skip Setup/Config files comuni
        if name in ["setup.py", "conftest.py", "manage.py", "wsgi.py", "asgi.py"]:
            return True
            
        return False

    def _scan_codebase(self):
        """
        Private method that performs the actual file system traversal.
        It recursively finds .py files, applies filters (folders, symlinks, size, tests),
        and populates the class-level `_python_files_cache`.
        """
        print(f"Inizializzazione Analyzer: scansione file in {self.codebase_path}...")
        
        token_skipped_count = 0
        exception_skipped_count = 0
        tests_skipped_count = 0 # Nuovo contatore

        CodebaseAnalyzer._python_files_cache.clear()

        # Cartelle tecniche da ignorare sempre
        ignored_folders = {".git", "__pycache__", ".venv", "venv", "env", "node_modules", "build", "dist", "egg-info", ".idea", ".vscode"}

        for path in self.codebase_path.rglob("*.py"):
            
            # 1. Filtro Cartelle Tecniche (Veloce)
            if any(part in ignored_folders for part in path.parts):
                continue
            
            # 2. Filtro Symlinks
            if path.is_symlink():
                continue

            # 3. Filtro Logico (Test, Migrazioni, ecc.) - NUOVO
            if self._is_test_or_generated(path):
                tests_skipped_count += 1
                continue

            try:
                # 4. Filtro Contenuto e Dimensione
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Controllo dimensione (Char limit approx token limit)
                # Utile per non intasare la RAM o bloccare l'AST su file generati enormi
                if len(content) > self.max_char_limit:
                    token_skipped_count += 1
                    continue
                    
                if not content.strip():
                    continue

            except Exception:
                exception_skipped_count += 1
                continue

            # Se passa tutti i controlli, è un file "buono"
            CodebaseAnalyzer._python_files_cache.append(path)
            
        print(f"Scansione completata. File validi caricati: {len(CodebaseAnalyzer._python_files_cache)}")
        print(f"\t-> Scartati (Test/Config/Migrazioni): {tests_skipped_count}")
        print(f"\t-> Scartati (Troppo grandi > {self.max_token_limit} tok): {token_skipped_count}")
        print(f"\t-> Scartati (Errori lettura): {exception_skipped_count}")

    def get_python_files(self) -> List[Path]:
        """
        Returns the list of valid Python files identified during the scan.

        Returns:
            List[Path]: A list of Path objects pointing to valid Python files.
        """
        return self.python_files